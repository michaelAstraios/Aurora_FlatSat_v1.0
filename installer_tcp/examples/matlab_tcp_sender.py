#!/usr/bin/env python3
"""
MATLAB TCP Sender - Comprehensive Test Program

Simulates MATLAB's TCP/IP output behavior, sending 8-byte floats with 10ms spacing.
This program can be used to test the FlatSat Device Simulator locally without MATLAB.
"""

import socket
import struct
import time
import math
import random
import argparse
import logging
import sys
from typing import List, Optional
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SenderConfig:
    """Configuration for MATLAB TCP sender"""
    target_ip: str = "127.0.0.1"
    target_port: int = 5000
    endianness: str = "little"  # little or big
    ars_enabled: bool = False
    mag_enabled: bool = False
    rw_enabled: bool = False
    duration: float = 0  # 0 = continuous
    log_level: str = "INFO"

class MATLABTCPSender:
    """Simulates MATLAB TCP/IP data transmission"""
    
    def __init__(self, config: SenderConfig):
        self.config = config
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.packets_sent = 0
        self.bytes_sent = 0
        self.start_time = 0
        
    def connect(self) -> bool:
        """Connect to the simulator"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Disable Nagle's algorithm to ensure immediate transmission
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.socket.connect((self.config.target_ip, self.config.target_port))
            self.connected = True
            logger.info(f"Connected to {self.config.target_ip}:{self.config.target_port} (TCP_NODELAY enabled)")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the simulator"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.connected = False
            logger.info("Disconnected from simulator")
    
    def send_float(self, value: float):
        """
        Send a single 8-byte float value
        
        Args:
            value: Float value to send
        """
        try:
            # Pack as 8-byte (64-bit) double
            if self.config.endianness == "big":
                data = struct.pack('>d', value)
            else:
                data = struct.pack('<d', value)
            
            self.socket.send(data)
            self.packets_sent += 1
            self.bytes_sent += len(data)
            
            logger.debug(f"Sent float: {value:.6f}")
            
            # Wait 10ms between floats
            time.sleep(0.010)
            
        except Exception as e:
            logger.error(f"Failed to send float: {e}")
            self.connected = False
    
    def generate_ars_primary_data(self, simulation_time: float) -> List[float]:
        """
        Generate ARS primary data (6 floats)
        
        Returns:
            [prime_x, prime_y, prime_z, prime_angle_x, prime_angle_y, prime_angle_z]
        """
        # Simulate realistic angular rates (rad/sec)
        prime_x = 0.1 * math.sin(simulation_time * 0.5) + random.uniform(-0.001, 0.001)
        prime_y = -0.05 * math.cos(simulation_time * 0.3) + random.uniform(-0.001, 0.001)
        prime_z = 0.02 * math.sin(simulation_time * 0.7) + random.uniform(-0.001, 0.001)
        
        # Simulate summed incremental angles (rad)
        prime_angle_x = 1.0 * math.sin(simulation_time * 0.2)
        prime_angle_y = -0.5 * math.cos(simulation_time * 0.4)
        prime_angle_z = 0.2 * math.sin(simulation_time * 0.6)
        
        return [prime_x, prime_y, prime_z, prime_angle_x, prime_angle_y, prime_angle_z]
    
    def generate_magnetometer_data(self, simulation_time: float) -> List[float]:
        """
        Generate magnetometer data (3 floats)
        
        Returns:
            [x_field, y_field, z_field] in nanoTesla
        """
        # Simulate Earth's magnetic field (nT)
        x_field = 25000.0 + 1000.0 * math.sin(simulation_time * 0.1)
        y_field = -5000.0 + 500.0 * math.cos(simulation_time * 0.15)
        z_field = 40000.0 + 800.0 * math.sin(simulation_time * 0.08)
        
        return [x_field, y_field, z_field]
    
    def generate_reaction_wheel_data(self, simulation_time: float) -> List[float]:
        """
        Generate reaction wheel data (4 floats)
        
        Returns:
            [wheel_speed, motor_current, temperature, bus_voltage]
        """
        # Wheel speed (RPM)
        wheel_speed = 1500.0 + 100.0 * math.sin(simulation_time * 0.2)
        
        # Motor current (A)
        motor_current = 2.5 + 0.5 * math.cos(simulation_time * 0.3)
        
        # Temperature (°C)
        temperature = 35.0 + 5.0 * math.sin(simulation_time * 0.05)
        
        # Bus voltage (V)
        bus_voltage = 28.5 + 0.5 * math.cos(simulation_time * 0.1)
        
        return [wheel_speed, motor_current, temperature, bus_voltage]
    
    def run_simulation(self):
        """Run the continuous data generation simulation"""
        logger.info("Starting MATLAB TCP sender simulation")
        logger.info(f"ARS: {self.config.ars_enabled}, Mag: {self.config.mag_enabled}, RW: {self.config.rw_enabled}")
        logger.info(f"Endianness: {self.config.endianness}")
        logger.info(f"Duration: {'continuous' if self.config.duration == 0 else f'{self.config.duration}s'}")
        
        self.start_time = time.time()
        last_stats_time = self.start_time
        
        try:
            while self.connected:
                # Check duration
                if self.config.duration > 0:
                    elapsed = time.time() - self.start_time
                    if elapsed >= self.config.duration:
                        logger.info(f"Reached duration limit of {self.config.duration}s")
                        break
                
                simulation_time = time.time() - self.start_time
                
                # Send ARS data (6 floats with 10ms spacing between each)
                if self.config.ars_enabled:
                    ars_data = self.generate_ars_primary_data(simulation_time)
                    for value in ars_data:
                        self.send_float(value)
                
                # Send magnetometer data (3 floats with 10ms spacing between each)
                if self.config.mag_enabled:
                    mag_data = self.generate_magnetometer_data(simulation_time)
                    for value in mag_data:
                        self.send_float(value)
                
                # Send reaction wheel data (4 floats with 10ms spacing between each)
                if self.config.rw_enabled:
                    rw_data = self.generate_reaction_wheel_data(simulation_time)
                    for value in rw_data:
                        self.send_float(value)
                
                # Print statistics every 10 seconds
                current_time = time.time()
                if current_time - last_stats_time >= 10.0:
                    self._print_statistics()
                    last_stats_time = current_time
                
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            self._print_final_statistics()
    
    def _print_statistics(self):
        """Print current statistics"""
        elapsed = time.time() - self.start_time
        rate = self.packets_sent / elapsed if elapsed > 0 else 0
        throughput = self.bytes_sent / elapsed if elapsed > 0 else 0
        
        logger.info(f"Statistics: {self.packets_sent} packets, "
                   f"{self.bytes_sent} bytes, "
                   f"{rate:.1f} packets/sec, "
                   f"{throughput:.1f} bytes/sec")
    
    def _print_final_statistics(self):
        """Print final statistics"""
        elapsed = time.time() - self.start_time
        rate = self.packets_sent / elapsed if elapsed > 0 else 0
        throughput = self.bytes_sent / elapsed if elapsed > 0 else 0
        
        logger.info("=== Final Statistics ===")
        logger.info(f"Duration: {elapsed:.2f}s")
        logger.info(f"Packets sent: {self.packets_sent}")
        logger.info(f"Bytes sent: {self.bytes_sent}")
        logger.info(f"Average rate: {rate:.1f} packets/sec")
        logger.info(f"Average throughput: {throughput:.1f} bytes/sec")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='MATLAB TCP Sender - Test program for FlatSat Device Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Send ARS data only
  %(prog)s --enable-ars
  
  # Send all device data
  %(prog)s --enable-ars --enable-mag --enable-rw
  
  # Send for 60 seconds
  %(prog)s --enable-ars --duration 60
  
  # Use big-endian format
  %(prog)s --enable-ars --endianness big
  
  # Connect to remote simulator
  %(prog)s --target-ip 192.168.1.100 --target-port 5000 --enable-ars
        '''
    )
    
    parser.add_argument('--target-ip', default='127.0.0.1',
                       help='Target IP address (default: 127.0.0.1)')
    parser.add_argument('--target-port', type=int, default=5000,
                       help='Target port (default: 5000)')
    parser.add_argument('--endianness', choices=['little', 'big'], default='little',
                       help='Float endianness (default: little)')
    parser.add_argument('--enable-ars', action='store_true',
                       help='Enable ARS data generation')
    parser.add_argument('--enable-mag', action='store_true',
                       help='Enable magnetometer data generation')
    parser.add_argument('--enable-rw', action='store_true',
                       help='Enable reaction wheel data generation')
    parser.add_argument('--all-devices', action='store_true',
                       help='Enable all devices')
    parser.add_argument('--duration', type=float, default=0,
                       help='Test duration in seconds (0 = continuous, default: 0)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Determine which devices to enable
    config = SenderConfig(
        target_ip=args.target_ip,
        target_port=args.target_port,
        endianness=args.endianness,
        ars_enabled=args.enable_ars or args.all_devices,
        mag_enabled=args.enable_mag or args.all_devices,
        rw_enabled=args.enable_rw or args.all_devices,
        duration=args.duration,
        log_level=args.log_level
    )
    
    # Check if at least one device is enabled
    if not (config.ars_enabled or config.mag_enabled or config.rw_enabled):
        logger.error("No devices enabled. Use --enable-ars, --enable-mag, --enable-rw, or --all-devices")
        sys.exit(1)
    
    # Create sender and connect
    sender = MATLABTCPSender(config)
    
    if sender.connect():
        try:
            sender.run_simulation()
        finally:
            sender.disconnect()
    else:
        logger.error("Failed to connect to simulator")
        sys.exit(1)

if __name__ == '__main__':
    main()

