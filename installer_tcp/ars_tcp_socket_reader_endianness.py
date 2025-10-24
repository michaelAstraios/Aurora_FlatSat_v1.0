#!/usr/bin/env python3
"""
ARS TCP Socket Reader with Automatic Endianness Detection

This TCP version includes automatic detection of big vs little endian data format
by analyzing the incoming data patterns and attempting both formats.
"""

import socket
import struct
import threading
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Deque
from dataclasses import dataclass, asdict
from collections import deque
import argparse
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EndiannessDetection:
    """Endianness detection results"""
    is_big_endian: bool
    confidence: float  # 0.0 to 1.0
    detection_method: str
    samples_tested: int
    last_updated: float

@dataclass
class ARSData:
    """Enhanced data structure with endianness info"""
    # Prime angular rates
    prime_x: float = 0.0
    prime_y: float = 0.0
    prime_z: float = 0.0
    
    # Redundant angular rates
    redundant_x: float = 0.0
    redundant_y: float = 0.0
    redundant_z: float = 0.0
    
    # Prime summed incremental angles
    prime_angle_x: float = 0.0
    prime_angle_y: float = 0.0
    prime_angle_z: float = 0.0
    
    # Redundant summed incremental angles
    redundant_angle_x: float = 0.0
    redundant_angle_y: float = 0.0
    redundant_angle_z: float = 0.0
    
    # Metadata
    timestamp: float = 0.0
    port_data_count: Dict[int, int] = None
    endianness_info: Dict[int, EndiannessDetection] = None
    
    def __post_init__(self):
        if self.port_data_count is None:
            self.port_data_count = {i: 0 for i in range(12)}
        if self.endianness_info is None:
            self.endianness_info = {}

class EndiannessDetector:
    """Automatic endianness detection for float data"""
    
    def __init__(self, detection_samples: int = 50):
        self.detection_samples = detection_samples
        self.samples_per_port: Dict[int, List[bytes]] = {}
        self.detection_results: Dict[int, EndiannessDetection] = {}
        self.detection_lock = threading.Lock()
        
    def add_sample(self, port_index: int, data: bytes):
        """Add a data sample for endianness detection"""
        with self.detection_lock:
            if port_index not in self.samples_per_port:
                self.samples_per_port[port_index] = []
            
            self.samples_per_port[port_index].append(data)
            
            # Keep only the most recent samples
            if len(self.samples_per_port[port_index]) > self.detection_samples:
                self.samples_per_port[port_index] = self.samples_per_port[port_index][-self.detection_samples:]
            
            # Try detection if we have enough samples
            if len(self.samples_per_port[port_index]) >= 10:
                self._detect_endianness(port_index)
    
    def _detect_endianness(self, port_index: int) -> EndiannessDetection:
        """Detect endianness using multiple methods"""
        samples = self.samples_per_port[port_index]
        
        # Method 1: Range-based detection
        range_result = self._detect_by_range(samples)
        
        # Method 2: Pattern-based detection
        pattern_result = self._detect_by_pattern(samples)
        
        # Method 3: Consistency-based detection
        consistency_result = self._detect_by_consistency(samples)
        
        # Combine results
        big_endian_votes = 0
        little_endian_votes = 0
        total_confidence = 0.0
        
        for result in [range_result, pattern_result, consistency_result]:
            if result['is_big_endian']:
                big_endian_votes += 1
            else:
                little_endian_votes += 1
            total_confidence += result['confidence']
        
        # Determine final result
        is_big_endian = big_endian_votes > little_endian_votes
        confidence = total_confidence / 3.0
        
        # Determine detection method
        if range_result['confidence'] > pattern_result['confidence'] and range_result['confidence'] > consistency_result['confidence']:
            method = "range_analysis"
        elif pattern_result['confidence'] > consistency_result['confidence']:
            method = "pattern_analysis"
        else:
            method = "consistency_analysis"
        
        detection = EndiannessDetection(
            is_big_endian=is_big_endian,
            confidence=confidence,
            detection_method=method,
            samples_tested=len(samples),
            last_updated=time.time()
        )
        
        self.detection_results[port_index] = detection
        return detection
    
    def _detect_by_range(self, samples: List[bytes]) -> Dict:
        """Detect endianness by analyzing value ranges"""
        little_endian_values = []
        big_endian_values = []
        
        for sample in samples:
            try:
                le_val = struct.unpack('<d', sample)[0]
                be_val = struct.unpack('>d', sample)[0]
                
                if abs(le_val) < 1e6 and abs(le_val) > 1e-6:  # Reasonable range
                    little_endian_values.append(le_val)
                if abs(be_val) < 1e6 and abs(be_val) > 1e-6:  # Reasonable range
                    big_endian_values.append(be_val)
            except:
                continue
        
        # Analyze ranges
        le_range_score = self._analyze_range_score(little_endian_values)
        be_range_score = self._analyze_range_score(big_endian_values)
        
        is_big_endian = be_range_score > le_range_score
        confidence = abs(be_range_score - le_range_score)
        
        return {
            'is_big_endian': is_big_endian,
            'confidence': min(confidence, 1.0)
        }
    
    def _detect_by_pattern(self, samples: List[bytes]) -> Dict:
        """Detect endianness by analyzing byte patterns"""
        le_pattern_score = 0
        be_pattern_score = 0
        
        for sample in samples:
            # Check for common patterns
            if sample[0] == 0 and sample[1] == 0:  # Common in little endian
                le_pattern_score += 1
            if sample[6] == 0 and sample[7] == 0:  # Common in big endian
                be_pattern_score += 1
        
        is_big_endian = be_pattern_score > le_pattern_score
        total_samples = len(samples)
        confidence = abs(be_pattern_score - le_pattern_score) / max(total_samples, 1)
        
        return {
            'is_big_endian': is_big_endian,
            'confidence': min(confidence, 1.0)
        }
    
    def _detect_by_consistency(self, samples: List[bytes]) -> Dict:
        """Detect endianness by checking consistency of values"""
        le_values = []
        be_values = []
        
        for sample in samples:
            try:
                le_val = struct.unpack('<d', sample)[0]
                be_val = struct.unpack('>d', sample)[0]
                
                if not (float('-inf') < le_val < float('inf')):
                    le_val = 0
                if not (float('-inf') < be_val < float('inf')):
                    be_val = 0
                
                le_values.append(le_val)
                be_values.append(be_val)
            except:
                le_values.append(0)
                be_values.append(0)
        
        # Check consistency (lower variance is better)
        le_variance = statistics.variance(le_values) if len(le_values) > 1 else 0
        be_variance = statistics.variance(be_values) if len(be_values) > 1 else 0
        
        is_big_endian = be_variance < le_variance
        confidence = abs(le_variance - be_variance) / max(le_variance + be_variance, 1e-10)
        
        return {
            'is_big_endian': is_big_endian,
            'confidence': min(confidence, 1.0)
        }
    
    def _analyze_range_score(self, values: List[float]) -> float:
        """Analyze the range score for a set of values"""
        if not values:
            return 0.0
        
        # Check for reasonable ranges (typical sensor values)
        reasonable_count = 0
        for val in values:
            if -1000 < val < 1000:  # Reasonable sensor range
                reasonable_count += 1
        
        return reasonable_count / len(values)
    
    def get_detection_result(self, port_index: int) -> Optional[EndiannessDetection]:
        """Get the detection result for a specific port"""
        with self.detection_lock:
            return self.detection_results.get(port_index)
    
    def get_all_results(self) -> Dict[int, EndiannessDetection]:
        """Get all detection results"""
        with self.detection_lock:
            return dict(self.detection_results)

class EnhancedTCPSocketReaderWithEndianness:
    """Enhanced TCP socket reader with automatic endianness detection"""
    
    def __init__(self, ip_address: str, start_port: int, num_ports: int = 12):
        self.ip_address = ip_address
        self.start_port = start_port
        self.num_ports = num_ports
        self.servers: List[socket.socket] = []
        self.clients: Dict[int, socket.socket] = {}  # Track client connections per port
        self.is_running = False
        self.threads: List[threading.Thread] = []
        self.data_lock = threading.Lock()
        self.latest_data = ARSData()
        self.data_history = deque(maxlen=100)
        
        # Endianness detection
        self.endianness_detector = EndiannessDetector()
        
        # Enhanced data handling
        self.packet_buffers: Dict[int, bytearray] = {}  # Buffer for each port
        self.last_packet_times: Dict[int, float] = {}  # Last packet time per port
        self.packet_counts: Dict[int, int] = {}  # Packet count per port
        self.expected_packet_size = 8  # Expected 8-byte float
        
        # TCP-specific settings
        self.max_clients_per_port = 1  # Only allow one client per port
        self.client_timeout = 30.0  # 30 second timeout for client connections
        
    def _create_tcp_server(self, port: int) -> Optional[socket.socket]:
        """Create and configure a TCP server socket for the given port"""
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Increase buffer size to handle potential bursts
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            server_sock.bind((self.ip_address, port))
            server_sock.listen(1)  # Allow one pending connection
            server_sock.settimeout(1.0)  # 1 second timeout for accept
            logger.info(f"TCP server with endianness detection created for port {port}")
            return server_sock
        except Exception as e:
            logger.error(f"Failed to create TCP server for port {port}: {e}")
            return None
    
    def _parse_float_data_with_endianness(self, data: bytes, port_index: int) -> Optional[float]:
        """Parse 8-byte data as 64-bit float with automatic endianness detection"""
        if len(data) != 8:
            logger.warning(f"Expected 8 bytes, got {len(data)}")
            return None
        
        # Add sample for endianness detection
        self.endianness_detector.add_sample(port_index, data)
        
        # Get detection result
        detection = self.endianness_detector.get_detection_result(port_index)
        
        if detection and detection.confidence > 0.5:
            # Use detected endianness
            try:
                if detection.is_big_endian:
                    value = struct.unpack('>d', data)[0]  # Big endian double
                else:
                    value = struct.unpack('<d', data)[0]  # Little endian double
                
                # Validate float value
                if not (float('-inf') < value < float('inf')):
                    logger.warning(f"Invalid float value: {value}")
                    return None
                    
                return value
            except struct.error as e:
                logger.error(f"Failed to parse float data: {e}")
                return None
        else:
            # Try both endianness formats and pick the more reasonable one
            try:
                le_value = struct.unpack('<d', data)[0]
                be_value = struct.unpack('>d', data)[0]
                
                # Check which value is more reasonable
                le_reasonable = abs(le_value) < 1e6 and abs(le_value) > 1e-6
                be_reasonable = abs(be_value) < 1e6 and abs(be_value) > 1e-6
                
                if le_reasonable and not be_reasonable:
                    return le_value
                elif be_reasonable and not le_reasonable:
                    return be_value
                elif le_reasonable and be_reasonable:
                    # Both reasonable, prefer little endian (more common)
                    return le_value
                else:
                    # Neither reasonable, return little endian as default
                    return le_value
                    
            except struct.error as e:
                logger.error(f"Failed to parse float data: {e}")
                return None
    
    def _process_packet_data(self, data: bytes, port: int, port_index: int, timestamp: float) -> bool:
        """Process packet data with endianness detection"""
        # Initialize buffer for this port if needed
        if port not in self.packet_buffers:
            self.packet_buffers[port] = bytearray()
            self.last_packet_times[port] = 0
            self.packet_counts[port] = 0
        
        # Add data to buffer
        self.packet_buffers[port].extend(data)
        
        # Process complete packets from buffer
        packets_processed = 0
        while len(self.packet_buffers[port]) >= self.expected_packet_size:
            packet_data = bytes(self.packet_buffers[port][:self.expected_packet_size])
            self.packet_buffers[port] = self.packet_buffers[port][self.expected_packet_size:]
            
            # Parse the float value with endianness detection
            float_value = self._parse_float_data_with_endianness(packet_data, port_index)
            
            if float_value is not None:
                self.packet_counts[port] += 1
                
                # Update the latest data
                with self.data_lock:
                    # Map port index to data field
                    if port_index == 0:  # Prime X
                        self.latest_data.prime_x = float_value
                    elif port_index == 1:  # Prime Y
                        self.latest_data.prime_y = float_value
                    elif port_index == 2:  # Prime Z
                        self.latest_data.prime_z = float_value
                    elif port_index == 3:  # Redundant X
                        self.latest_data.redundant_x = float_value
                    elif port_index == 4:  # Redundant Y
                        self.latest_data.redundant_y = float_value
                    elif port_index == 5:  # Redundant Z
                        self.latest_data.redundant_z = float_value
                    elif port_index == 6:  # Prime Angle X
                        self.latest_data.prime_angle_x = float_value
                    elif port_index == 7:  # Prime Angle Y
                        self.latest_data.prime_angle_y = float_value
                    elif port_index == 8:  # Prime Angle Z
                        self.latest_data.prime_angle_z = float_value
                    elif port_index == 9:  # Redundant Angle X
                        self.latest_data.redundant_angle_x = float_value
                    elif port_index == 10:  # Redundant Angle Y
                        self.latest_data.redundant_angle_y = float_value
                    elif port_index == 11:  # Redundant Angle Z
                        self.latest_data.redundant_angle_z = float_value
                    
                    # Update timestamp and counter
                    self.latest_data.timestamp = timestamp
                    self.latest_data.port_data_count[port_index] += 1
                    
                    # Update endianness info
                    detection = self.endianness_detector.get_detection_result(port_index)
                    if detection:
                        self.latest_data.endianness_info[port_index] = detection
                    
                    logger.debug(f"Port {port}: {float_value:.6f} (count: {self.latest_data.port_data_count[port_index]})")
                
                packets_processed += 1
        
        return packets_processed > 0
    
    def _handle_client_connection(self, client_sock: socket.socket, client_addr: Tuple[str, int], port: int, port_index: int):
        """Handle data from a connected TCP client with endianness detection"""
        logger.info(f"Client with endianness detection connected from {client_addr[0]}:{client_addr[1]} on port {port}")
        
        try:
            client_sock.settimeout(1.0)  # 1 second timeout for recv
            
            while self.is_running:
                try:
                    # Receive data from client
                    data = client_sock.recv(4096)  # Larger buffer for TCP
                    
                    if not data:
                        logger.info(f"Client {client_addr[0]}:{client_addr[1]} disconnected from port {port}")
                        break
                    
                    # Process packet data with endianness detection
                    timestamp = time.time()
                    self._process_packet_data(data, port, port_index, timestamp)
                    
                except socket.timeout:
                    continue  # Normal timeout, keep listening
                except Exception as e:
                    if self.is_running:  # Only log if we're supposed to be running
                        logger.error(f"Error handling client {client_addr} on port {port}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in client handler for port {port}: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass
            
            # Remove client from tracking
            with self.data_lock:
                if port in self.clients:
                    del self.clients[port]
            
            logger.info(f"Client handler for port {port} stopped")
    
    def _tcp_server_listener(self, server_sock: socket.socket, port: int, port_index: int):
        """Listen for TCP connections on a specific port with endianness detection"""
        logger.info(f"Starting TCP server listener with endianness detection for port {port} (index {port_index})")
        
        while self.is_running:
            try:
                # Accept client connection
                client_sock, client_addr = server_sock.accept()
                
                # Check if we already have a client for this port
                with self.data_lock:
                    if port in self.clients:
                        logger.warning(f"Port {port} already has a client, rejecting new connection from {client_addr}")
                        client_sock.close()
                        continue
                    
                    # Track the client
                    self.clients[port] = client_sock
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self._handle_client_connection,
                    args=(client_sock, client_addr, port, port_index),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                continue  # Normal timeout, keep listening
            except Exception as e:
                if self.is_running:  # Only log if we're supposed to be running
                    logger.error(f"Error in TCP server listener for port {port}: {e}")
                break
        
        logger.info(f"TCP server listener for port {port} stopped")
    
    def start_listening(self) -> bool:
        """Start listening on all configured TCP ports"""
        logger.info(f"Starting TCP server readers with endianness detection for {self.ip_address}:{self.start_port}-{self.start_port + self.num_ports - 1}")
        
        self.is_running = True
        
        # Create TCP servers for all ports
        for i in range(self.num_ports):
            port = self.start_port + i
            server_sock = self._create_tcp_server(port)
            
            if server_sock:
                self.servers.append(server_sock)
                # Start server listener thread
                thread = threading.Thread(
                    target=self._tcp_server_listener,
                    args=(server_sock, port, i),
                    daemon=True
                )
                thread.start()
                self.threads.append(thread)
                logger.info(f"TCP server with endianness detection started for port {port}")
            else:
                logger.error(f"Failed to start TCP server for port {port}")
                return False
        
        logger.info(f"All TCP servers with endianness detection started successfully")
        return True
    
    def stop_listening(self):
        """Stop listening on all ports"""
        logger.info("Stopping TCP servers with endianness detection...")
        self.is_running = False
        
        # Close all client connections
        with self.data_lock:
            for port, client_sock in self.clients.items():
                try:
                    client_sock.close()
                except:
                    pass
            self.clients.clear()
        
        # Close all server sockets
        for server_sock in self.servers:
            try:
                server_sock.close()
            except:
                pass
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2.0)
        
        logger.info("All TCP servers with endianness detection stopped")
    
    def get_latest_data(self) -> ARSData:
        """Get the latest ARS data"""
        with self.data_lock:
            return self.latest_data
    
    def get_data_history(self) -> List[ARSData]:
        """Get the data history"""
        with self.data_lock:
            return list(self.data_history)
    
    def get_client_status(self) -> Dict[int, bool]:
        """Get status of client connections per port"""
        with self.data_lock:
            return {port: port in self.clients for port in range(self.start_port, self.start_port + self.num_ports)}
    
    def get_endianness_report(self) -> Dict:
        """Get endianness detection report"""
        results = self.endianness_detector.get_all_results()
        report = {}
        
        for port_index, detection in results.items():
            port = self.start_port + port_index
            report[port] = {
                'is_big_endian': detection.is_big_endian,
                'confidence': detection.confidence,
                'detection_method': detection.detection_method,
                'samples_tested': detection.samples_tested,
                'last_updated': detection.last_updated
            }
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='ARS TCP Socket Reader with Automatic Endianness Detection')
    parser.add_argument('--ip', default='127.0.0.1', help='IP address to listen on')
    parser.add_argument('--start-port', type=int, default=5000, help='Starting port number')
    parser.add_argument('--num-ports', type=int, default=12, help='Number of ports to listen on')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Load configuration if provided
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            return 1
    
    # Override with config if available
    ip_address = config.get('ip_address', args.ip)
    start_port = config.get('start_port', args.start_port)
    num_ports = config.get('num_ports', args.num_ports)
    
    logger.info(f"Starting ARS TCP Socket Reader with Endianness Detection")
    logger.info(f"IP: {ip_address}, Ports: {start_port}-{start_port + num_ports - 1}")
    
    # Create socket reader
    socket_reader = EnhancedTCPSocketReaderWithEndianness(ip_address, start_port, num_ports)
    
    try:
        # Start listening
        if not socket_reader.start_listening():
            logger.error("Failed to start TCP servers")
            return 1
        
        logger.info("ARS TCP Socket Reader with Endianness Detection started successfully")
        logger.info("Press Ctrl+C to stop")
        
        # Main loop - display status periodically
        while True:
            time.sleep(10)  # Update every 10 seconds
            
            # Get status
            latest_data = socket_reader.get_latest_data()
            client_status = socket_reader.get_client_status()
            endianness_report = socket_reader.get_endianness_report()
            
            connected_clients = sum(client_status.values())
            total_packets = sum(latest_data.port_data_count.values())
            
            logger.info(f"Status: {total_packets} packets, "
                       f"Connected clients: {connected_clients}/{num_ports}")
            
            # Log endianness detection results
            if endianness_report:
                logger.info("Endianness Detection Results:")
                for port, info in endianness_report.items():
                    endian = "Big" if info['is_big_endian'] else "Little"
                    logger.info(f"  Port {port}: {endian} Endian (confidence: {info['confidence']:.3f}, "
                              f"method: {info['detection_method']}, samples: {info['samples_tested']})")
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        socket_reader.stop_listening()
        logger.info("ARS TCP Socket Reader with Endianness Detection stopped")
    
    return 0

if __name__ == "__main__":
    exit(main())
