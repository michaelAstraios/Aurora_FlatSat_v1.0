#!/usr/bin/env python3
"""
MATLAB Simulator Data Sender

Simulates MATLAB data generation and sends it to the FlatSat Device Simulator.
This script can be used for testing the simulator without MATLAB.
"""

import socket
import time
import struct
import random
import math
import argparse
import threading
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MATLABDataSender:
    """Simulates MATLAB data generation and transmission"""
    
    def __init__(self, target_ip: str = "127.0.0.1", target_port: int = 5000):
        self.target_ip = target_ip
        self.target_port = target_port
        self.socket: socket.socket = None
        self.running = False
        
    def connect(self) -> bool:
        """Connect to the simulator"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.target_ip, self.target_port))
            logger.info(f"Connected to simulator at {self.target_ip}:{self.target_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the simulator"""
        if self.socket:
            self.socket.close()
            logger.info("Disconnected from simulator")
    
    def send_float_data(self, port: int, value: float):
        """Send a single float value to a specific port"""
        try:
            # Pack as 8-byte (64-bit) float
            data = struct.pack('<d', value)  # Little-endian double
            self.socket.send(data)
            logger.debug(f"Sent {value:.6f} to port {port}")
        except Exception as e:
            logger.error(f"Failed to send data to port {port}: {e}")
    
    def generate_ars_data(self) -> List[float]:
        """Generate ARS data (12 floats)"""
        # Simulate realistic angular rates and angles
        base_time = time.time()
        
        # Prime angular rates (rad/sec)
        prime_x = 0.1 * math.sin(base_time * 0.5)
        prime_y = -0.05 * math.cos(base_time * 0.3)
        prime_z = 0.02 * math.sin(base_time * 0.7)
        
        # Redundant angular rates (slightly different)
        redundant_x = prime_x + random.uniform(-0.001, 0.001)
        redundant_y = prime_y + random.uniform(-0.001, 0.001)
        redundant_z = prime_z + random.uniform(-0.001, 0.001)
        
        # Prime summed incremental angles (rad)
        prime_angle_x = 1.0 * math.sin(base_time * 0.2)
        prime_angle_y = -0.5 * math.cos(base_time * 0.4)
        prime_angle_z = 0.2 * math.sin(base_time * 0.6)
        
        # Redundant summed incremental angles
        redundant_angle_x = prime_angle_x + random.uniform(-0.01, 0.01)
        redundant_angle_y = prime_angle_y + random.uniform(-0.01, 0.01)
        redundant_angle_z = prime_angle_z + random.uniform(-0.01, 0.01)
        
        return [
            prime_x, prime_y, prime_z,
            redundant_x, redundant_y, redundant_z,
            prime_angle_x, prime_angle_y, prime_angle_z,
            redundant_angle_x, redundant_angle_y, redundant_angle_z
        ]
    
    def generate_magnetometer_data(self) -> List[float]:
        """Generate magnetometer data (3 floats)"""
        # Simulate Earth's magnetic field (nT)
        base_time = time.time()
        
        # Typical Earth magnetic field components
        x_field = 25000.0 + 1000.0 * math.sin(base_time * 0.1)
        y_field = -5000.0 + 500.0 * math.cos(base_time * 0.15)
        z_field = 40000.0 + 800.0 * math.sin(base_time * 0.08)
        
        return [x_field, y_field, z_field]
    
    def generate_reaction_wheel_data(self) -> List[float]:
        """Generate reaction wheel data (4 floats)"""
        # Simulate RWA telemetry
        base_time = time.time()
        
        # Wheel speed (RPM)
        wheel_speed = 1500.0 + 100.0 * math.sin(base_time * 0.2)
        
        # Motor current (A)
        motor_current = 2.5 + 0.5 * math.cos(base_time * 0.3)
        
        # Temperature (°C)
        temperature = 35.0 + 5.0 * math.sin(base_time * 0.05)
        
        # Bus voltage (V)
        bus_voltage = 28.5 + 0.5 * math.cos(base_time * 0.1)
        
        return [wheel_speed, motor_current, temperature, bus_voltage]
    
    def send_ars_data(self, ports: List[int]):
        """Send ARS data to specified ports"""
        data = self.generate_ars_data()
        for i, port in enumerate(ports):
            if i < len(data):
                self.send_float_data(port, data[i])
    
    def send_magnetometer_data(self, ports: List[int]):
        """Send magnetometer data to specified ports"""
        data = self.generate_magnetometer_data()
        for i, port in enumerate(ports):
            if i < len(data):
                self.send_float_data(port, data[i])
    
    def send_reaction_wheel_data(self, ports: List[int]):
        """Send reaction wheel data to specified ports"""
        data = self.generate_reaction_wheel_data()
        for i, port in enumerate(ports):
            if i < len(data):
                self.send_float_data(port, data[i])
    
    def run_simulation(self, duration: float = 60.0, ars_enabled: bool = True, 
                      mag_enabled: bool = True, rw_enabled: bool = False):
        """Run the simulation"""
        logger.info(f"Starting simulation for {duration} seconds")
        
        # Port mappings
        ars_ports = list(range(5000, 5012))  # 12 ports
        mag_ports = [6000, 6001, 6002]      # 3 ports
        rw_ports = [7000, 7001, 7002, 7003] # 4 ports
        
        start_time = time.time()
        self.running = True
        
        try:
            while self.running and (time.time() - start_time) < duration:
                current_time = time.time()
                
                # Send ARS data (600 Hz)
                if ars_enabled:
                    self.send_ars_data(ars_ports)
                
                # Send magnetometer data (10 Hz)
                if mag_enabled and int(current_time * 10) % 10 == 0:
                    self.send_magnetometer_data(mag_ports)
                
                # Send reaction wheel data (1 Hz)
                if rw_enabled and int(current_time) % 1 == 0:
                    self.send_reaction_wheel_data(rw_ports)
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        finally:
            self.running = False
            logger.info("Simulation completed")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='MATLAB Data Sender')
    parser.add_argument('--target-ip', default='127.0.0.1', help='Target IP address')
    parser.add_argument('--target-port', type=int, default=5000, help='Target port')
    parser.add_argument('--duration', type=float, default=60.0, help='Simulation duration (seconds)')
    parser.add_argument('--enable-ars', action='store_true', help='Enable ARS data')
    parser.add_argument('--enable-mag', action='store_true', help='Enable magnetometer data')
    parser.add_argument('--enable-rw', action='store_true', help='Enable reaction wheel data')
    parser.add_argument('--all-devices', action='store_true', help='Enable all devices')
    
    args = parser.parse_args()
    
    # Determine which devices to enable
    ars_enabled = args.enable_ars or args.all_devices
    mag_enabled = args.enable_mag or args.all_devices
    rw_enabled = args.enable_rw or args.all_devices
    
    if not (ars_enabled or mag_enabled or rw_enabled):
        logger.info("No devices enabled, enabling ARS by default")
        ars_enabled = True
    
    # Create and run sender
    sender = MATLABDataSender(args.target_ip, args.target_port)
    
    if sender.connect():
        try:
            sender.run_simulation(
                duration=args.duration,
                ars_enabled=ars_enabled,
                mag_enabled=mag_enabled,
                rw_enabled=rw_enabled
            )
        finally:
            sender.disconnect()
    else:
        logger.error("Failed to connect to simulator")

if __name__ == '__main__':
    main()
