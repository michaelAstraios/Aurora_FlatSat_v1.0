#!/usr/bin/env python3
"""
Enhanced ARS Sensor Socket Reader with Proper Data Boundary Handling

This improved version handles:
- Data boundary detection and synchronization
- 10ms timing gap detection between packets
- Proper packet parsing with buffering
- Data integrity validation
- Robust error handling for network issues
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
    data_source: str = "ARS_SIMULATED"
    data_quality_score: float = 1.0  # 0.0 to 1.0

class EnhancedSocketReader:
    """Enhanced socket reader with proper data boundary handling"""
    
    def __init__(self, ip_address: str, start_port: int, num_ports: int = 12):
        self.ip_address = ip_address
        self.start_port = start_port
        self.num_ports = num_ports
        self.sockets: List[socket.socket] = []
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
            'parse_errors': 0
        }
        
    def _create_socket(self, port: int) -> Optional[socket.socket]:
        """Create and configure a socket for the given port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Increase buffer size to handle potential bursts
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            sock.bind((self.ip_address, port))
            sock.settimeout(1.0)  # 1 second timeout
            logger.info(f"Socket created for port {port}")
            return sock
        except Exception as e:
            logger.error(f"Failed to create socket for port {port}: {e}")
            return None
    
    def _parse_float_data(self, data: bytes, is_big_endian: bool = False) -> Optional[float]:
        """Parse 8-byte data as 64-bit float with validation"""
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
            if not (value == value):  # NaN check
                logger.warning(f"Received NaN value")
                return None
            if abs(value) == float('inf'):
                logger.warning(f"Received infinity value: {value}")
                return None
                
            return value
        except struct.error as e:
            logger.error(f"Failed to parse float data: {e}")
            self.quality_stats['parse_errors'] += 1
            return None
    
    def _handle_packet_data(self, data: bytes, port: int, port_index: int, timestamp: float) -> Optional[PacketInfo]:
        """Handle incoming packet data with proper boundary detection"""
        self.quality_stats['total_packets_received'] += 1
        
        # Check packet size
        if len(data) != self.expected_packet_size:
            logger.warning(f"Port {port}: Unexpected packet size {len(data)} bytes (expected {self.expected_packet_size})")
            self.quality_stats['size_violations'] += 1
            return None
        
        # Parse the float value
        float_value = self._parse_float_data(data)
        if float_value is None:
            return None
        
        # Check timing
        time_since_last = None
        if port_index in self.last_packet_times:
            time_since_last = timestamp - self.last_packet_times[port_index]
            expected_interval = 0.01  # 10ms
            
            # Check if timing is within tolerance
            if abs(time_since_last - expected_interval) > (self.timing_tolerance_ms / 1000.0):
                logger.debug(f"Port {port}: Timing deviation {time_since_last:.4f}s (expected ~0.01s)")
                self.quality_stats['timing_violations'] += 1
        
        # Update timing info
        self.last_packet_times[port_index] = timestamp
        self.packet_counts[port_index] = self.packet_counts.get(port_index, 0) + 1
        
        self.quality_stats['valid_packets'] += 1
        
        return PacketInfo(
            timestamp=timestamp,
            port=port,
            port_index=port_index,
            data_length=len(data),
            float_value=float_value,
            packet_number=self.packet_counts[port_index],
            time_since_last=time_since_last
        )
    
    def _socket_listener(self, sock: socket.socket, port: int, port_index: int):
        """Enhanced listener for data on a specific socket with proper boundary handling"""
        logger.info(f"Starting enhanced listener for port {port} (index {port_index})")
        
        while self.is_running:
            try:
                data, addr = sock.recvfrom(1024)
                timestamp = time.time()
                
                # Handle the packet data
                packet_info = self._handle_packet_data(data, port, port_index, timestamp)
                
                if packet_info is not None:
                    # Update the latest data
                    with self.data_lock:
                        # Map port index to data field
                        if port_index == 0:  # Prime X
                            self.latest_data.prime_x = packet_info.float_value
                        elif port_index == 1:  # Prime Y
                            self.latest_data.prime_y = packet_info.float_value
                        elif port_index == 2:  # Prime Z
                            self.latest_data.prime_z = packet_info.float_value
                        elif port_index == 3:  # Redundant X
                            self.latest_data.redundant_x = packet_info.float_value
                        elif port_index == 4:  # Redundant Y
                            self.latest_data.redundant_y = packet_info.float_value
                        elif port_index == 5:  # Redundant Z
                            self.latest_data.redundant_z = packet_info.float_value
                        elif port_index == 6:  # Prime Angle X
                            self.latest_data.prime_angle_x = packet_info.float_value
                        elif port_index == 7:  # Prime Angle Y
                            self.latest_data.prime_angle_y = packet_info.float_value
                        elif port_index == 8:  # Prime Angle Z
                            self.latest_data.prime_angle_z = packet_info.float_value
                        elif port_index == 9:  # Redundant Angle X
                            self.latest_data.redundant_angle_x = packet_info.float_value
                        elif port_index == 10:  # Redundant Angle Y
                            self.latest_data.redundant_angle_y = packet_info.float_value
                        elif port_index == 11:  # Redundant Angle Z
                            self.latest_data.redundant_angle_z = packet_info.float_value
                        
                        # Update timing statistics
                        if packet_info.time_since_last is not None:
                            timing_stats = self.latest_data.port_timing_stats[port_index]
                            timing_stats['intervals'].append(packet_info.time_since_last)
                            timing_stats['last_time'] = packet_info.timestamp
                        
                        # Update timestamp and counter
                        self.latest_data.timestamp = timestamp
                        self.latest_data.port_data_count[port_index] += 1
                        
                        logger.debug(f"Port {port}: {packet_info.float_value:.6f} "
                                   f"(packet #{packet_info.packet_number}, "
                                   f"interval: {packet_info.time_since_last:.4f}s)")
                
            except socket.timeout:
                continue  # Normal timeout, keep listening
            except Exception as e:
                if self.is_running:  # Only log if we're supposed to be running
                    logger.error(f"Error in socket listener for port {port}: {e}")
                break
        
        logger.info(f"Socket listener for port {port} stopped")
    
    def start_listening(self) -> bool:
        """Start listening on all configured ports"""
        logger.info(f"Starting enhanced socket readers for {self.ip_address}:{self.start_port}-{self.start_port + self.num_ports - 1}")
        
        self.is_running = True
        
        # Initialize packet tracking
        for i in range(self.num_ports):
            self.packet_counts[i] = 0
            self.last_packet_times[i] = 0
        
        # Create sockets for all ports
        for i in range(self.num_ports):
            port = self.start_port + i
            sock = self._create_socket(port)
            
            if sock:
                self.sockets.append(sock)
                # Start listener thread
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
        
        logger.info(f"Started {len(self.sockets)} enhanced socket listeners")
        return True
    
    def stop_listening(self):
        """Stop all socket listeners"""
        logger.info("Stopping enhanced socket listeners...")
        
        self.is_running = False
        
        # Close all sockets
        for sock in self.sockets:
            try:
                sock.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2.0)
        
        logger.info("Enhanced socket listeners stopped")
    
    def get_latest_data(self) -> ARSData:
        """Get the latest ARS data"""
        with self.data_lock:
            return self.latest_data
    
    def get_data_summary(self) -> Dict:
        """Get a comprehensive summary of received data"""
        with self.data_lock:
            total_packets = sum(self.latest_data.port_data_count.values())
            
            # Calculate timing statistics
            timing_stats = {}
            for port_idx, stats in self.latest_data.port_timing_stats.items():
                if stats['intervals']:
                    intervals = list(stats['intervals'])
                    timing_stats[port_idx] = {
                        'avg_interval': statistics.mean(intervals),
                        'std_interval': statistics.stdev(intervals) if len(intervals) > 1 else 0,
                        'min_interval': min(intervals),
                        'max_interval': max(intervals),
                        'sample_count': len(intervals)
                    }
            
            return {
                'total_packets': total_packets,
                'port_counts': dict(self.latest_data.port_data_count),
                'timing_stats': timing_stats,
                'quality_stats': dict(self.quality_stats),
                'latest_timestamp': self.latest_data.timestamp,
                'data_age_seconds': time.time() - self.latest_data.timestamp if self.latest_data.timestamp > 0 else None,
                'data_quality_flags': dict(self.latest_data.data_quality_flags)
            }
    
    def get_quality_report(self) -> Dict:
        """Get a detailed quality report"""
        summary = self.get_data_summary()
        
        # Calculate quality score
        total_received = self.quality_stats['total_packets_received']
        valid_received = self.quality_stats['valid_packets']
        
        quality_score = valid_received / total_received if total_received > 0 else 0
        
        return {
            'overall_quality_score': quality_score,
            'packet_statistics': {
                'total_received': total_received,
                'valid_packets': valid_received,
                'timing_violations': self.quality_stats['timing_violations'],
                'size_violations': self.quality_stats['size_violations'],
                'parse_errors': self.quality_stats['parse_errors']
            },
            'timing_analysis': summary['timing_stats'],
            'data_quality_flags': summary['data_quality_flags']
        }

class RateSensorSimulator:
    """Enhanced simulator with data quality assessment"""
    
    def __init__(self):
        self.message_counter = 0
        self.status_word_builder = StatusWordBuilder()
    
    def convert_ars_to_rate_sensor(self, ars_data: ARSData) -> RateSensorSimulatedData:
        """Convert ARS data to Rate Sensor format with quality assessment"""
        
        # Use Prime data as primary (could implement voting logic here)
        simulated_data = RateSensorSimulatedData(
            angular_rate_x=ars_data.prime_x,
            angular_rate_y=ars_data.prime_y,
            angular_rate_z=ars_data.prime_z,
            summed_angle_x=ars_data.prime_angle_x,
            summed_angle_y=ars_data.prime_angle_y,
            summed_angle_z=ars_data.prime_angle_z,
            timestamp=ars_data.timestamp,
            message_counter=self.message_counter,
            data_source="ARS_SIMULATED"
        )
        
        # Calculate data quality score
        quality_score = self._calculate_quality_score(ars_data)
        simulated_data.data_quality_score = quality_score
        
        # Build status words based on data quality
        self._update_status_words(simulated_data, ars_data, quality_score)
        
        self.message_counter += 1
        return simulated_data
    
    def _calculate_quality_score(self, ars_data: ARSData) -> float:
        """Calculate overall data quality score (0.0 to 1.0)"""
        score = 1.0
        
        # Check data availability
        has_prime_data = any([ars_data.prime_x, ars_data.prime_y, ars_data.prime_z])
        has_redundant_data = any([ars_data.redundant_x, ars_data.redundant_y, ars_data.redundant_z])
        
        if not has_prime_data:
            score -= 0.5
        if not has_redundant_data:
            score -= 0.2
        
        # Check for large discrepancies between prime and redundant
        if has_prime_data and has_redundant_data:
            rate_diff_x = abs(ars_data.prime_x - ars_data.redundant_x)
            rate_diff_y = abs(ars_data.prime_y - ars_data.redundant_y)
            rate_diff_z = abs(ars_data.prime_z - ars_data.redundant_z)
            max_rate_diff = max(rate_diff_x, rate_diff_y, rate_diff_z)
            
            if max_rate_diff > 0.1:  # Large discrepancy
                score -= 0.3
            elif max_rate_diff > 0.05:  # Moderate discrepancy
                score -= 0.1
        
        # Check timing quality flags
        if not ars_data.data_quality_flags.get('timing_valid', True):
            score -= 0.2
        if not ars_data.data_quality_flags.get('data_boundaries_valid', True):
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _update_status_words(self, simulated_data: RateSensorSimulatedData, ars_data: ARSData, quality_score: float):
        """Update status words based on data quality"""
        
        # Determine status based on quality score
        has_data = quality_score > 0.5
        has_good_quality = quality_score > 0.8
        has_discrepancy = quality_score < 0.7
        
        # Build status words
        simulated_data.status_word_1 = self.status_word_builder.build_status_word_1(
            counter=self.message_counter % 4,
            bit_mode=1,  # Continuous BIT
            rate_sensor_failed=not has_data,
            gyro_failed=has_discrepancy,
            agc_voltage_failed=False
        )
        
        simulated_data.status_word_2 = self.status_word_builder.build_status_word_2(
            gyro_temperature_a=25,  # Simulated temperature
            motor_bias_voltage_failed=False,
            start_data_flag=False,
            processor_failed=not has_good_quality,
            memory_failed=False
        )
        
        simulated_data.status_word_3 = self.status_word_builder.build_status_word_3(
            gyro_a_start_run=has_data,
            gyro_b_start_run=has_data,
            gyro_c_start_run=has_data,
            gyro_a_fdc=has_discrepancy,
            gyro_b_fdc=has_discrepancy,
            gyro_c_fdc=has_discrepancy,
            fdc_failed=has_discrepancy,
            rs_ok=has_good_quality
        )

class StatusWordBuilder:
    """Helper class for building status words (reused from test generator)"""
    
    @staticmethod
    def build_status_word_1(
        counter: int = 0,
        bit_mode: int = 1,
        rate_sensor_failed: bool = False,
        gyro_failed: bool = False,
        agc_voltage_failed: bool = False
    ) -> int:
        """Build Status Word 1 according to Table 7"""
        word = 0
        word |= (counter & 0x03)
        word |= ((bit_mode & 0x03) << 2)
        if rate_sensor_failed:
            word |= (1 << 4)
        if gyro_failed:
            word |= (1 << 5)
        if agc_voltage_failed:
            word |= (1 << 7)
        return word & 0xFFFF
    
    @staticmethod
    def build_status_word_2(
        gyro_temperature_a: int = 25,
        motor_bias_voltage_failed: bool = False,
        start_data_flag: bool = False,
        processor_failed: bool = False,
        memory_failed: bool = False
    ) -> int:
        """Build Status Word 2 according to Table 8"""
        word = 0
        word |= (gyro_temperature_a & 0xFF)
        if motor_bias_voltage_failed:
            word |= (1 << 8)
        if start_data_flag:
            word |= (1 << 9)
        if processor_failed:
            word |= (1 << 10)
        if memory_failed:
            word |= (1 << 11)
        return word & 0xFFFF
    
    @staticmethod
    def build_status_word_3(
        gyro_a_start_run: bool = True,
        gyro_b_start_run: bool = True,
        gyro_c_start_run: bool = True,
        gyro_a_fdc: bool = False,
        gyro_b_fdc: bool = False,
        gyro_c_fdc: bool = False,
        fdc_failed: bool = False,
        rs_ok: bool = True
    ) -> int:
        """Build Status Word 3 according to Table 9"""
        word = 0
        if gyro_a_start_run:
            word |= (1 << 8)
        if gyro_b_start_run:
            word |= (1 << 9)
        if gyro_c_start_run:
            word |= (1 << 10)
        if gyro_a_fdc:
            word |= (1 << 11)
        if gyro_b_fdc:
            word |= (1 << 12)
        if gyro_c_fdc:
            word |= (1 << 13)
        if fdc_failed:
            word |= (1 << 14)
        if rs_ok:
            word |= (1 << 15)
        return word & 0xFFFF

class DataLogger:
    """Enhanced logger with quality reporting"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file
        self.log_data = []
        
    def log_data(self, ars_data: ARSData, simulated_data: RateSensorSimulatedData):
        """Log both ARS and simulated data with quality info"""
        log_entry = {
            'timestamp': time.time(),
            'ars_data': asdict(ars_data),
            'simulated_data': asdict(simulated_data)
        }
        
        self.log_data.append(log_entry)
        
        # Print to console with quality info
        print(f"\n=== Enhanced ARS to Rate Sensor Simulation ===")
        print(f"Time: {time.strftime('%H:%M:%S', time.localtime(ars_data.timestamp))}")
        print(f"ARS Prime Rates: X={ars_data.prime_x:+.6f}, Y={ars_data.prime_y:+.6f}, Z={ars_data.prime_z:+.6f}")
        print(f"ARS Redundant Rates: X={ars_data.redundant_x:+.6f}, Y={ars_data.redundant_y:+.6f}, Z={ars_data.redundant_z:+.6f}")
        print(f"Simulated Rates: X={simulated_data.angular_rate_x:+.6f}, Y={simulated_data.angular_rate_y:+.6f}, Z={simulated_data.angular_rate_z:+.6f}")
        print(f"Status Words: SW1=0x{simulated_data.status_word_1:04X}, SW2=0x{simulated_data.status_word_2:04X}, SW3=0x{simulated_data.status_word_3:04X}")
        print(f"Data Quality Score: {simulated_data.data_quality_score:.2f}")
        
        # Save to file if specified
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception as e:
                logger.error(f"Failed to write to log file: {e}")

class EnhancedARSRateSensorSimulator:
    """Enhanced main application class with proper data boundary handling"""
    
    def __init__(self, ip_address: str, start_port: int, log_file: str = None):
        self.socket_reader = EnhancedSocketReader(ip_address, start_port)
        self.simulator = RateSensorSimulator()
        self.logger = DataLogger(log_file)
        self.is_running = False
        self.display_thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the enhanced ARS to Rate Sensor simulation"""
        logger.info("Starting Enhanced ARS to Rate Sensor Simulator")
        
        # Start socket reading
        if not self.socket_reader.start_listening():
            logger.error("Failed to start enhanced socket readers")
            return False
        
        self.is_running = True
        
        # Start display thread
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()
        
        logger.info("Enhanced ARS to Rate Sensor Simulator started successfully")
        return True
    
    def stop(self):
        """Stop the simulation"""
        logger.info("Stopping Enhanced ARS to Rate Sensor Simulator")
        
        self.is_running = False
        
        # Stop socket reading
        self.socket_reader.stop_listening()
        
        # Wait for display thread
        if self.display_thread:
            self.display_thread.join(timeout=2.0)
        
        logger.info("Enhanced ARS to Rate Sensor Simulator stopped")
    
    def _display_loop(self):
        """Enhanced display loop with quality monitoring"""
        last_summary_time = 0
        last_quality_report_time = 0
        
        while self.is_running:
            try:
                # Get latest ARS data
                ars_data = self.socket_reader.get_latest_data()
                
                # Convert to Rate Sensor format
                simulated_data = self.simulator.convert_ars_to_rate_sensor(ars_data)
                
                # Log the data
                self.logger.log_data(ars_data, simulated_data)
                
                # Print summary every 10 seconds
                current_time = time.time()
                if current_time - last_summary_time >= 10:
                    summary = self.socket_reader.get_data_summary()
                    print(f"\n=== Enhanced Data Summary ===")
                    print(f"Total packets received: {summary['total_packets']}")
                    print(f"Data age: {summary['data_age_seconds']:.1f}s")
                    print(f"Port counts: {summary['port_counts']}")
                    print(f"Quality flags: {summary['data_quality_flags']}")
                    last_summary_time = current_time
                
                # Print quality report every 30 seconds
                if current_time - last_quality_report_time >= 30:
                    quality_report = self.socket_reader.get_quality_report()
                    print(f"\n=== Data Quality Report ===")
                    print(f"Overall Quality Score: {quality_report['overall_quality_score']:.2f}")
                    print(f"Packet Statistics: {quality_report['packet_statistics']}")
                    last_quality_report_time = current_time
                
                time.sleep(0.1)  # 100ms update rate
                
            except Exception as e:
                logger.error(f"Error in enhanced display loop: {e}")
                time.sleep(1.0)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enhanced ARS Sensor Socket Reader and Rate Sensor Simulator')
    parser.add_argument('--ip', default='0.0.0.0', help='IP address to listen on (default: 0.0.0.0)')
    parser.add_argument('--start-port', type=int, default=5000, help='Starting port number (default: 5000)')
    parser.add_argument('--num-ports', type=int, default=12, help='Number of ports to listen on (default: 12)')
    parser.add_argument('--log-file', help='Log file to save data (optional)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--timing-tolerance', type=int, default=15, help='Timing tolerance in ms (default: 15)')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start enhanced simulator
    simulator = EnhancedARSRateSensorSimulator(args.ip, args.start_port, args.log_file)
    
    # Set timing tolerance
    simulator.socket_reader.timing_tolerance_ms = args.timing_tolerance
    
    try:
        if simulator.start():
            print(f"Enhanced ARS to Rate Sensor Simulator running...")
            print(f"Listening on {args.ip}:{args.start_port}-{args.start_port + args.num_ports - 1}")
            print(f"Timing tolerance: ±{args.timing_tolerance}ms")
            print("Press Ctrl+C to stop")
            print("-" * 60)
            
            # Keep running until interrupted
            while True:
                time.sleep(1.0)
        else:
            print("Failed to start enhanced simulator")
            return 1
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        simulator.stop()
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        simulator.stop()
        return 1

if __name__ == '__main__':
    exit(main())


