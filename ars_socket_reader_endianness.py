#!/usr/bin/env python3
"""
ARS Socket Reader with Automatic Endianness Detection

This version includes automatic detection of big vs little endian data format
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
                le_value = struct.unpack('<d', sample)[0]
                be_value = struct.unpack('>d', sample)[0]
                
                little_endian_values.append(le_value)
                big_endian_values.append(be_value)
            except:
                continue
        
        if not little_endian_values or not big_endian_values:
            return {'is_big_endian': False, 'confidence': 0.0}
        
        # Analyze ranges - rate sensor data should be in reasonable ranges
        le_range = max(little_endian_values) - min(little_endian_values)
        be_range = max(big_endian_values) - min(big_endian_values)
        
        # Check for reasonable angular rate ranges (±1000 rad/s is reasonable)
        le_reasonable = all(abs(v) < 1000 for v in little_endian_values)
        be_reasonable = all(abs(v) < 1000 for v in big_endian_values)
        
        # Check for NaN/infinity
        le_valid = all(v == v and abs(v) != float('inf') for v in little_endian_values)
        be_valid = all(v == v and abs(v) != float('inf') for v in big_endian_values)
        
        # Score based on reasonableness and validity
        le_score = (1.0 if le_reasonable else 0.5) * (1.0 if le_valid else 0.0)
        be_score = (1.0 if be_reasonable else 0.5) * (1.0 if be_valid else 0.0)
        
        if le_score > be_score:
            return {'is_big_endian': False, 'confidence': le_score}
        else:
            return {'is_big_endian': True, 'confidence': be_score}
    
    def _detect_by_pattern(self, samples: List[bytes]) -> Dict:
        """Detect endianness by analyzing byte patterns"""
        little_endian_patterns = 0
        big_endian_patterns = 0
        
        for sample in samples:
            # Check for common patterns in rate sensor data
            # Little endian: LSB first, MSB last
            # Big endian: MSB first, LSB last
            
            # Look for patterns that suggest reasonable float values
            le_bytes = struct.unpack('<BBBBBBBB', sample)
            be_bytes = struct.unpack('>BBBBBBBB', sample)
            
            # Check for patterns that suggest valid IEEE 754 doubles
            le_pattern_score = self._analyze_byte_pattern(le_bytes)
            be_pattern_score = self._analyze_byte_pattern(be_bytes)
            
            if le_pattern_score > be_pattern_score:
                little_endian_patterns += 1
            else:
                big_endian_patterns += 1
        
        total_patterns = little_endian_patterns + big_endian_patterns
        if total_patterns == 0:
            return {'is_big_endian': False, 'confidence': 0.0}
        
        confidence = max(little_endian_patterns, big_endian_patterns) / total_patterns
        is_big_endian = big_endian_patterns > little_endian_patterns
        
        return {'is_big_endian': is_big_endian, 'confidence': confidence}
    
    def _analyze_byte_pattern(self, bytes_tuple: Tuple) -> float:
        """Analyze byte pattern for IEEE 754 double validity"""
        # IEEE 754 double: 1 sign bit, 11 exponent bits, 52 mantissa bits
        # Check for reasonable exponent values (not all 0s or all 1s)
        
        # Convert to binary representation
        byte1, byte2, byte3, byte4, byte5, byte6, byte7, byte8 = bytes_tuple
        
        # Check exponent field (bits 1-11 in IEEE 754)
        # For little endian: bytes 6-7 contain exponent
        # For big endian: bytes 1-2 contain exponent
        
        # This is a simplified check - in practice, you'd need to properly extract the exponent
        # For now, just check for reasonable byte values
        score = 0.0
        
        # Check for reasonable byte values (not all 0s or all 0xFF)
        for byte_val in bytes_tuple:
            if byte_val == 0:
                score -= 0.1  # Too many zeros might indicate wrong endianness
            elif byte_val == 0xFF:
                score -= 0.1  # Too many 0xFF might indicate wrong endianness
            else:
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _detect_by_consistency(self, samples: List[bytes]) -> Dict:
        """Detect endianness by checking consistency over time"""
        if len(samples) < 5:
            return {'is_big_endian': False, 'confidence': 0.0}
        
        little_endian_values = []
        big_endian_values = []
        
        for sample in samples:
            try:
                le_value = struct.unpack('<d', sample)[0]
                be_value = struct.unpack('>d', sample)[0]
                
                if le_value == le_value and abs(le_value) != float('inf'):  # Not NaN or inf
                    little_endian_values.append(le_value)
                if be_value == be_value and abs(be_value) != float('inf'):  # Not NaN or inf
                    big_endian_values.append(be_value)
            except:
                continue
        
        if len(little_endian_values) < 3 or len(big_endian_values) < 3:
            return {'is_big_endian': False, 'confidence': 0.0}
        
        # Check for reasonable variation (rate sensor data should vary smoothly)
        le_variation = self._calculate_variation(little_endian_values)
        be_variation = self._calculate_variation(big_endian_values)
        
        # Lower variation suggests more consistent (and likely correct) data
        if le_variation < be_variation:
            return {'is_big_endian': False, 'confidence': 1.0 - le_variation}
        else:
            return {'is_big_endian': True, 'confidence': 1.0 - be_variation}
    
    def _calculate_variation(self, values: List[float]) -> float:
        """Calculate variation coefficient for consistency check"""
        if len(values) < 2:
            return 1.0
        
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 1.0
        
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        # Variation coefficient (std dev / mean)
        return abs(std_dev / mean_val) if mean_val != 0 else 1.0
    
    def get_endianness(self, port_index: int) -> Optional[EndiannessDetection]:
        """Get endianness detection result for a port"""
        with self.detection_lock:
            return self.detection_results.get(port_index)
    
    def get_all_detections(self) -> Dict[int, EndiannessDetection]:
        """Get all endianness detection results"""
        with self.detection_lock:
            return dict(self.detection_results)

class EnhancedSocketReaderWithEndianness:
    """Enhanced socket reader with automatic endianness detection"""
    
    def __init__(self, ip_address: str, start_port: int, num_ports: int = 12):
        self.ip_address = ip_address
        self.start_port = start_port
        self.num_ports = num_ports
        self.sockets: List[socket.socket] = []
        self.is_running = False
        self.threads: List[threading.Thread] = []
        self.data_lock = threading.Lock()
        self.latest_data = ARSData()
        
        # Endianness detection
        self.endianness_detector = EndiannessDetector()
        
        # Data handling
        self.packet_counts: Dict[int, int] = {}
        self.last_packet_times: Dict[int, float] = {}
        self.expected_packet_size = 8
        
        # Quality monitoring
        self.quality_stats = {
            'total_packets_received': 0,
            'valid_packets': 0,
            'endianness_detections': 0,
            'parse_errors': 0
        }
        
    def _create_socket(self, port: int) -> Optional[socket.socket]:
        """Create and configure a socket for the given port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            sock.bind((self.ip_address, port))
            sock.settimeout(1.0)
            logger.info(f"Socket created for port {port}")
            return sock
        except Exception as e:
            logger.error(f"Failed to create socket for port {port}: {e}")
            return None
    
    def _parse_float_data_with_endianness(self, data: bytes, port_index: int) -> Optional[float]:
        """Parse float data using detected endianness"""
        if len(data) != 8:
            logger.warning(f"Expected 8 bytes, got {len(data)}")
            return None
        
        # Get endianness detection result
        detection = self.endianness_detector.get_endianness(port_index)
        
        if detection and detection.confidence > 0.7:
            # Use detected endianness
            is_big_endian = detection.is_big_endian
            logger.debug(f"Port {port_index}: Using detected endianness (big_endian={is_big_endian}, confidence={detection.confidence:.2f})")
        else:
            # Fallback: try both and pick the more reasonable one
            try:
                le_value = struct.unpack('<d', data)[0]
                be_value = struct.unpack('>d', data)[0]
                
                # Choose the more reasonable value
                le_reasonable = abs(le_value) < 1000 and le_value == le_value and abs(le_value) != float('inf')
                be_reasonable = abs(be_value) < 1000 and be_value == be_value and abs(be_value) != float('inf')
                
                if le_reasonable and not be_reasonable:
                    is_big_endian = False
                elif be_reasonable and not le_reasonable:
                    is_big_endian = True
                else:
                    # Default to little endian if both are reasonable
                    is_big_endian = False
                
                logger.debug(f"Port {port_index}: Fallback endianness detection (big_endian={is_big_endian})")
            except:
                logger.error(f"Port {port_index}: Failed to parse float data")
                return None
        
        try:
            if is_big_endian:
                value = struct.unpack('>d', data)[0]
            else:
                value = struct.unpack('<d', data)[0]
            
            # Validate the result
            if not (value == value) or abs(value) == float('inf'):
                logger.warning(f"Port {port_index}: Invalid float value")
                return None
            
            return value
        except struct.error as e:
            logger.error(f"Port {port_index}: Failed to parse float data: {e}")
            return None
    
    def _socket_listener(self, sock: socket.socket, port: int, port_index: int):
        """Enhanced listener with endianness detection"""
        logger.info(f"Starting listener with endianness detection for port {port} (index {port_index})")
        
        while self.is_running:
            try:
                data, addr = sock.recvfrom(1024)
                timestamp = time.time()
                
                self.quality_stats['total_packets_received'] += 1
                
                if len(data) == self.expected_packet_size:
                    # Add sample for endianness detection
                    self.endianness_detector.add_sample(port_index, data)
                    
                    # Parse the float value
                    float_value = self._parse_float_data_with_endianness(data, port_index)
                    
                    if float_value is not None:
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
                            
                            # Update metadata
                            self.latest_data.timestamp = timestamp
                            self.latest_data.port_data_count[port_index] += 1
                            
                            # Update endianness info
                            detection = self.endianness_detector.get_endianness(port_index)
                            if detection:
                                self.latest_data.endianness_info[port_index] = detection
                            
                            logger.debug(f"Port {port}: {float_value:.6f} (packet #{self.packet_counts.get(port_index, 0) + 1})")
                        
                        self.quality_stats['valid_packets'] += 1
                        self.packet_counts[port_index] = self.packet_counts.get(port_index, 0) + 1
                    else:
                        self.quality_stats['parse_errors'] += 1
                else:
                    logger.warning(f"Port {port}: Unexpected packet size {len(data)} bytes")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error in socket listener for port {port}: {e}")
                break
        
        logger.info(f"Socket listener for port {port} stopped")
    
    def start_listening(self) -> bool:
        """Start listening on all configured ports"""
        logger.info(f"Starting socket readers with endianness detection for {self.ip_address}:{self.start_port}-{self.start_port + self.num_ports - 1}")
        
        self.is_running = True
        
        # Initialize tracking
        for i in range(self.num_ports):
            self.packet_counts[i] = 0
            self.last_packet_times[i] = 0
        
        # Create sockets for all ports
        for i in range(self.num_ports):
            port = self.start_port + i
            sock = self._create_socket(port)
            
            if sock:
                self.sockets.append(sock)
                thread = threading.Thread(
                    target=self._socket_listener,
                    args=(sock, port, i),
                    daemon=True
                )
                thread.start()
                self.threads.append(thread)
            else:
                logger.error(f"Failed to create socket for port {port}")
                return False
        
        logger.info(f"Started {len(self.sockets)} socket listeners with endianness detection")
        return True
    
    def stop_listening(self):
        """Stop all socket listeners"""
        logger.info("Stopping socket listeners...")
        
        self.is_running = False
        
        for sock in self.sockets:
            try:
                sock.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
        
        for thread in self.threads:
            thread.join(timeout=2.0)
        
        logger.info("Socket listeners stopped")
    
    def get_latest_data(self) -> ARSData:
        """Get the latest ARS data"""
        with self.data_lock:
            return self.latest_data
    
    def get_endianness_report(self) -> Dict:
        """Get endianness detection report"""
        detections = self.endianness_detector.get_all_detections()
        
        report = {
            'total_ports': self.num_ports,
            'detected_ports': len(detections),
            'detections': {}
        }
        
        for port_index, detection in detections.items():
            report['detections'][port_index] = {
                'is_big_endian': detection.is_big_endian,
                'confidence': detection.confidence,
                'detection_method': detection.detection_method,
                'samples_tested': detection.samples_tested,
                'last_updated': detection.last_updated
            }
        
        return report
    
    def get_data_summary(self) -> Dict:
        """Get comprehensive data summary"""
        with self.data_lock:
            total_packets = sum(self.latest_data.port_data_count.values())
            
            return {
                'total_packets': total_packets,
                'port_counts': dict(self.latest_data.port_data_count),
                'quality_stats': dict(self.quality_stats),
                'latest_timestamp': self.latest_data.timestamp,
                'data_age_seconds': time.time() - self.latest_data.timestamp if self.latest_data.timestamp > 0 else None,
                'endianness_report': self.get_endianness_report()
            }

def main():
    """Main function with endianness detection"""
    parser = argparse.ArgumentParser(description='ARS Socket Reader with Automatic Endianness Detection')
    parser.add_argument('--ip', default='0.0.0.0', help='IP address to listen on (default: 0.0.0.0)')
    parser.add_argument('--start-port', type=int, default=5000, help='Starting port number (default: 5000)')
    parser.add_argument('--num-ports', type=int, default=12, help='Number of ports to listen on (default: 12)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--detection-samples', type=int, default=50, help='Samples for endianness detection (default: 50)')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create enhanced reader
    reader = EnhancedSocketReaderWithEndianness(args.ip, args.start_port, args.num_ports)
    reader.endianness_detector.detection_samples = args.detection_samples
    
    try:
        if reader.start_listening():
            print(f"ARS Socket Reader with Endianness Detection running...")
            print(f"Listening on {args.ip}:{args.start_port}-{args.start_port + args.num_ports - 1}")
            print(f"Detection samples: {args.detection_samples}")
            print("Press Ctrl+C to stop")
            print("-" * 60)
            
            # Monitor and display results
            last_report_time = 0
            while True:
                time.sleep(1.0)
                
                current_time = time.time()
                if current_time - last_report_time >= 10:  # Report every 10 seconds
                    summary = reader.get_data_summary()
                    print(f"\n=== Data Summary ===")
                    print(f"Total packets: {summary['total_packets']}")
                    print(f"Valid packets: {summary['quality_stats']['valid_packets']}")
                    print(f"Parse errors: {summary['quality_stats']['parse_errors']}")
                    
                    endianness_report = summary['endianness_report']
                    print(f"\n=== Endianness Detection ===")
                    print(f"Detected ports: {endianness_report['detected_ports']}/{endianness_report['total_ports']}")
                    
                    for port_idx, detection in endianness_report['detections'].items():
                        endian_str = "Big Endian" if detection['is_big_endian'] else "Little Endian"
                        print(f"Port {port_idx}: {endian_str} (confidence: {detection['confidence']:.2f}, method: {detection['detection_method']})")
                    
                    last_report_time = current_time
        else:
            print("Failed to start socket reader")
            return 1
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        reader.stop_listening()
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        reader.stop_listening()
        return 1

if __name__ == '__main__':
    exit(main())


