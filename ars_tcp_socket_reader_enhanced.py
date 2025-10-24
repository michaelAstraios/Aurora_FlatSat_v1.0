#!/usr/bin/env python3
"""
Enhanced ARS Sensor TCP Socket Reader with Proper Data Boundary Handling

This improved TCP version handles:
- Data boundary detection and synchronization
- 10ms timing gap detection between packets
- Proper packet parsing with buffering
- Data integrity validation
- Robust error handling for network issues
- TCP connection management
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
class PacketInfo:
    """Information about a received packet"""
    timestamp: float
    port: int
    port_index: int
    data_length: int
    float_value: float
    packet_number: int
    time_since_last: Optional[float] = None

@dataclass
class ARSData:
    """Enhanced data structure for ARS sensor readings with timing info"""
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
    port_timing_stats: Dict[int, Dict[str, float]] = None
    data_quality_flags: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.port_data_count is None:
            self.port_data_count = {i: 0 for i in range(12)}
        if self.port_timing_stats is None:
            self.port_timing_stats = {i: {'last_time': 0, 'intervals': deque(maxlen=100)} for i in range(12)}
        if self.data_quality_flags is None:
            self.data_quality_flags = {
                'timing_valid': True,
                'data_boundaries_valid': True,
                'packet_sizes_valid': True,
                'float_values_valid': True
            }

@dataclass
class RateSensorSimulatedData:
    """Simulated Rate Sensor data structure matching Honeywell format"""
    # Angular rates (using Prime data as primary)
    angular_rate_x: float = 0.0
    angular_rate_y: float = 0.0
    angular_rate_z: float = 0.0
    
    # Summed incremental angles (using Prime data)
    summed_angle_x: float = 0.0
    summed_angle_y: float = 0.0
    summed_angle_z: float = 0.0
    
    # Status words (simulated)
    status_word_1: int = 0x0000
    status_word_2: int = 0x0019  # Temperature ~25°C
    status_word_3: int = 0xE000  # All gyros running
    
    # Additional metadata
    timestamp: float = 0.0
    message_counter: int = 0
    data_source: str = "ARS_TCP_ENHANCED"
    
    # Enhanced quality metrics
    data_quality_score: float = 1.0  # 0.0 to 1.0

class EnhancedTCPSocketReader:
    """Enhanced TCP socket reader with proper data boundary handling"""
    
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
        
        # Enhanced data handling
        self.packet_buffers: Dict[int, bytearray] = {}  # Buffer for each port
        self.last_packet_times: Dict[int, float] = {}  # Last packet time per port
        self.packet_counts: Dict[int, int] = {}  # Packet count per port
        self.expected_packet_size = 8  # Expected 8-byte float
        self.timing_tolerance_ms = 15  # Allow 15ms tolerance for 10ms expected interval
        
        # Data quality monitoring
        self.quality_stats = {
            'total_packets_received': 0,
            'valid_packets': 0,
            'timing_violations': 0,
            'size_violations': 0,
            'parse_errors': 0,
            'tcp_connection_errors': 0
        }
        
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
            logger.info(f"Enhanced TCP server created for port {port}")
            return server_sock
        except Exception as e:
            logger.error(f"Failed to create enhanced TCP server for port {port}: {e}")
            return None
    
    def _parse_float_data(self, data: bytes, is_big_endian: bool = False) -> Optional[float]:
        """Parse 8-byte data as 64-bit float with enhanced error handling"""
        if len(data) != 8:
            logger.warning(f"Expected 8 bytes, got {len(data)}")
            self.quality_stats['size_violations'] += 1
            return None
            
        try:
            if is_big_endian:
                value = struct.unpack('>d', data)[0]  # Big endian double
            else:
                value = struct.unpack('<d', data)[0]  # Little endian double
            
            # Validate float value (check for NaN, infinity)
            if not (float('-inf') < value < float('inf')):
                logger.warning(f"Invalid float value: {value}")
                self.quality_stats['parse_errors'] += 1
                return None
                
            return value
        except struct.error as e:
            logger.error(f"Failed to parse float data: {e}")
            self.quality_stats['parse_errors'] += 1
            return None
    
    def _process_packet_data(self, data: bytes, port: int, port_index: int, timestamp: float) -> bool:
        """Process packet data with enhanced boundary detection"""
        self.quality_stats['total_packets_received'] += 1
        
        # Initialize buffer for this port if needed
        if port not in self.packet_buffers:
            self.packet_buffers[port] = bytearray()
            self.last_packet_times[port] = 0
            self.packet_counts[port] = 0
        
        # Add data to buffer
        self.packet_buffers[port].extend(data)
        
        # Check timing
        time_since_last = timestamp - self.last_packet_times[port] if self.last_packet_times[port] > 0 else 0
        if time_since_last > 0:
            expected_interval = 0.01  # 10ms
            timing_error = abs(time_since_last - expected_interval)
            if timing_error > self.timing_tolerance_ms / 1000.0:
                self.quality_stats['timing_violations'] += 1
                logger.debug(f"Port {port}: Timing violation - {time_since_last*1000:.1f}ms (expected ~10ms)")
        
        # Process complete packets from buffer
        packets_processed = 0
        while len(self.packet_buffers[port]) >= self.expected_packet_size:
            packet_data = bytes(self.packet_buffers[port][:self.expected_packet_size])
            self.packet_buffers[port] = self.packet_buffers[port][self.expected_packet_size:]
            
            # Parse the float value
            float_value = self._parse_float_data(packet_data)
            
            if float_value is not None:
                self.quality_stats['valid_packets'] += 1
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
                    
                    # Update timing stats
                    if self.last_packet_times[port] > 0:
                        interval = timestamp - self.last_packet_times[port]
                        self.latest_data.port_timing_stats[port_index]['intervals'].append(interval)
                    
                    self.last_packet_times[port] = timestamp
                    
                    logger.debug(f"Port {port}: {float_value:.6f} (count: {self.latest_data.port_data_count[port_index]})")
                
                packets_processed += 1
        
        return packets_processed > 0
    
    def _handle_client_connection(self, client_sock: socket.socket, client_addr: Tuple[str, int], port: int, port_index: int):
        """Handle data from a connected TCP client with enhanced processing"""
        logger.info(f"Enhanced client connected from {client_addr[0]}:{client_addr[1]} on port {port}")
        
        try:
            client_sock.settimeout(1.0)  # 1 second timeout for recv
            
            while self.is_running:
                try:
                    # Receive data from client
                    data = client_sock.recv(4096)  # Larger buffer for TCP
                    
                    if not data:
                        logger.info(f"Client {client_addr[0]}:{client_addr[1]} disconnected from port {port}")
                        break
                    
                    # Process packet data with enhanced boundary detection
                    timestamp = time.time()
                    self._process_packet_data(data, port, port_index, timestamp)
                    
                except socket.timeout:
                    continue  # Normal timeout, keep listening
                except Exception as e:
                    if self.is_running:  # Only log if we're supposed to be running
                        logger.error(f"Error handling enhanced client {client_addr} on port {port}: {e}")
                        self.quality_stats['tcp_connection_errors'] += 1
                    break
                    
        except Exception as e:
            logger.error(f"Error in enhanced client handler for port {port}: {e}")
            self.quality_stats['tcp_connection_errors'] += 1
        finally:
            try:
                client_sock.close()
            except:
                pass
            
            # Remove client from tracking
            with self.data_lock:
                if port in self.clients:
                    del self.clients[port]
            
            logger.info(f"Enhanced client handler for port {port} stopped")
    
    def _tcp_server_listener(self, server_sock: socket.socket, port: int, port_index: int):
        """Listen for TCP connections on a specific port with enhanced monitoring"""
        logger.info(f"Starting enhanced TCP server listener for port {port} (index {port_index})")
        
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
                    logger.error(f"Error in enhanced TCP server listener for port {port}: {e}")
                    self.quality_stats['tcp_connection_errors'] += 1
                break
        
        logger.info(f"Enhanced TCP server listener for port {port} stopped")
    
    def start_listening(self) -> bool:
        """Start listening on all configured TCP ports"""
        logger.info(f"Starting enhanced TCP server readers for {self.ip_address}:{self.start_port}-{self.start_port + self.num_ports - 1}")
        
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
                logger.info(f"Enhanced TCP server started for port {port}")
            else:
                logger.error(f"Failed to start enhanced TCP server for port {port}")
                return False
        
        logger.info(f"All enhanced TCP servers started successfully")
        return True
    
    def stop_listening(self):
        """Stop listening on all ports"""
        logger.info("Stopping enhanced TCP servers...")
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
        
        logger.info("All enhanced TCP servers stopped")
    
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
    
    def get_quality_stats(self) -> Dict:
        """Get data quality statistics"""
        stats = dict(self.quality_stats)
        
        # Calculate quality score
        if stats['total_packets_received'] > 0:
            stats['quality_score'] = stats['valid_packets'] / stats['total_packets_received']
        else:
            stats['quality_score'] = 0.0
        
        # Add timing statistics
        stats['timing_stats'] = {}
        for port_index in range(self.num_ports):
            port = self.start_port + port_index
            if port in self.latest_data.port_timing_stats:
                intervals = list(self.latest_data.port_timing_stats[port_index]['intervals'])
                if intervals:
                    stats['timing_stats'][port] = {
                        'mean_interval': statistics.mean(intervals),
                        'std_interval': statistics.stdev(intervals) if len(intervals) > 1 else 0,
                        'min_interval': min(intervals),
                        'max_interval': max(intervals)
                    }
        
        return stats

class EnhancedRateSensorSimulator:
    """Enhanced simulator with quality monitoring"""
    
    def __init__(self, socket_reader: EnhancedTCPSocketReader):
        self.socket_reader = socket_reader
        self.message_counter = 0
        
    def generate_simulated_data(self) -> RateSensorSimulatedData:
        """Generate simulated rate sensor data with quality metrics"""
        ars_data = self.socket_reader.get_latest_data()
        quality_stats = self.socket_reader.get_quality_stats()
        
        # Calculate quality score
        quality_score = quality_stats.get('quality_score', 1.0)
        
        simulated_data = RateSensorSimulatedData(
            # Use prime data as primary angular rates
            angular_rate_x=ars_data.prime_x,
            angular_rate_y=ars_data.prime_y,
            angular_rate_z=ars_data.prime_z,
            
            # Use prime data as primary summed angles
            summed_angle_x=ars_data.prime_angle_x,
            summed_angle_y=ars_data.prime_angle_y,
            summed_angle_z=ars_data.prime_angle_z,
            
            # Status words (simulated)
            status_word_1=0x0000,  # Normal operation
            status_word_2=0x0019,  # Temperature ~25°C
            status_word_3=0xE000,  # All gyros running
            
            # Metadata
            timestamp=ars_data.timestamp,
            message_counter=self.message_counter,
            data_source="ARS_TCP_ENHANCED",
            data_quality_score=quality_score
        )
        
        self.message_counter += 1
        return simulated_data
    
    def get_status_report(self) -> Dict:
        """Get a comprehensive status report"""
        ars_data = self.socket_reader.get_latest_data()
        client_status = self.socket_reader.get_client_status()
        quality_stats = self.socket_reader.get_quality_stats()
        
        return {
            "timestamp": time.time(),
            "message_counter": self.message_counter,
            "data_source": "ARS_TCP_ENHANCED",
            "client_connections": client_status,
            "port_data_counts": ars_data.port_data_count,
            "quality_stats": quality_stats,
            "data_quality_flags": ars_data.data_quality_flags,
            "latest_data": {
                "prime_rates": [ars_data.prime_x, ars_data.prime_y, ars_data.prime_z],
                "redundant_rates": [ars_data.redundant_x, ars_data.redundant_y, ars_data.redundant_z],
                "prime_angles": [ars_data.prime_angle_x, ars_data.prime_angle_y, ars_data.prime_angle_z],
                "redundant_angles": [ars_data.redundant_angle_x, ars_data.redundant_angle_y, ars_data.redundant_angle_z]
            }
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enhanced ARS TCP Socket Reader and Rate Sensor Simulator')
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
    
    logger.info(f"Starting Enhanced ARS TCP Socket Reader")
    logger.info(f"IP: {ip_address}, Ports: {start_port}-{start_port + num_ports - 1}")
    
    # Create socket reader
    socket_reader = EnhancedTCPSocketReader(ip_address, start_port, num_ports)
    
    # Create simulator
    simulator = EnhancedRateSensorSimulator(socket_reader)
    
    try:
        # Start listening
        if not socket_reader.start_listening():
            logger.error("Failed to start enhanced TCP servers")
            return 1
        
        logger.info("Enhanced ARS TCP Socket Reader started successfully")
        logger.info("Press Ctrl+C to stop")
        
        # Main loop - display status periodically
        while True:
            time.sleep(10)  # Update every 10 seconds
            
            status = simulator.get_status_report()
            quality_score = status['quality_stats'].get('quality_score', 0.0)
            connected_clients = sum(status['client_connections'].values())
            
            logger.info(f"Status: {status['message_counter']} messages, "
                       f"Connected clients: {connected_clients}/{num_ports}, "
                       f"Quality: {quality_score:.3f}")
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        socket_reader.stop_listening()
        logger.info("Enhanced ARS TCP Socket Reader stopped")
    
    return 0

if __name__ == "__main__":
    exit(main())
