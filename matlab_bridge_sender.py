#!/usr/bin/env python3
"""
MATLAB Bridge - Direct Port Sender
Sends simulated MATLAB data directly to all ARS ports (50038-50049)
"""

import socket
import time
import struct
import threading
import random
import math
import logging
from datetime import datetime
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MATLABBridgeSender:
    """Sends simulated MATLAB data to all ARS ports"""
    
    def __init__(self, ports: List[int], host: str = "127.0.0.1"):
        self.ports = ports
        self.host = host
        self.sockets = {}
        self.running = False
        self.start_time = None
        
    def connect_to_ports(self):
        """Connect to all specified ports"""
        logger.info(f"Connecting to {len(self.ports)} ports: {self.ports}")
        
        for port in self.ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, port))
                self.sockets[port] = sock
                logger.info(f"✅ Connected to port {port}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to port {port}: {e}")
        
        if not self.sockets:
            logger.error("No connections established. Exiting.")
            return False
        return True
    
    def generate_realistic_attitude_data(self, port_index: int, time_offset: float) -> float:
        """Generate realistic attitude data based on port index and time"""
        # Base values for different types of attitude data
        # Ports 50038-50043: Angular rates (rad/s)
        # Ports 50044-50049: Angular positions (rad)
        
        if 50038 <= self.ports[port_index] <= 50043:
            # Angular rates - small values typical for satellite attitude rates
            base_rate = 0.0001  # 0.1 mrad/s
            # Add sinusoidal variation for realism
            variation = base_rate * 0.5 * (random.random() - 0.5)
            time_variation = base_rate * 0.3 * (math.sin(time_offset * 0.1 + port_index))
            value = variation + time_variation
        elif 50044 <= self.ports[port_index] <= 50049:
            # Angular positions - small values typical for satellite attitude angles
            base_angle = 0.001  # 1 mrad
            # Add sinusoidal variation for realism
            variation = base_angle * 0.5 * (random.random() - 0.5)
            time_variation = base_angle * 0.3 * (math.sin(time_offset * 0.05 + port_index))
            value = variation + time_variation
        else:
            # Default for other ports
            value = random.uniform(-0.001, 0.001)
        
        return value
    
    def send_data_to_port(self, port: int, data: float):
        """Send float data to a specific port"""
        if port not in self.sockets:
            return False
        
        try:
            # Pack float as 8-byte double (little endian)
            data_bytes = struct.pack('<d', data)
            self.sockets[port].sendall(data_bytes)
            return True
        except Exception as e:
            logger.error(f"Error sending data to port {port}: {e}")
            return False
    
    def run_simulation(self, duration: float = 60.0):
        """Run the simulation for specified duration"""
        logger.info(f"🚀 Starting MATLAB bridge simulation for {duration} seconds")
        logger.info(f"📡 Sending data to ports: {self.ports}")
        
        if not self.connect_to_ports():
            return
        
        self.running = True
        self.start_time = time.time()
        
        try:
            packet_count = 0
            while self.running and (time.time() - self.start_time) < duration:
                current_time = time.time() - self.start_time
                
                # Send data to all ports
                for i, port in enumerate(self.ports):
                    # Generate realistic attitude data
                    float_value = self.generate_realistic_attitude_data(i, current_time)
                    
                    # Send data
                    if self.send_data_to_port(port, float_value):
                        packet_count += 1
                        
                        # Log every 100 packets to avoid spam
                        if packet_count % 100 == 0:
                            logger.info(f"📡 Sent packet {packet_count} to port {port}: {float_value:.6f}")
                
                # Send at approximately 10 Hz (100ms intervals)
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Simulation interrupted by user")
        finally:
            self.running = False
            logger.info("✅ Simulation completed")
    
    def close_connections(self):
        """Close all connections"""
        self.running = False
        
        for port, sock in self.sockets.items():
            try:
                sock.close()
                logger.info(f"🔌 Closed connection to port {port}")
            except Exception as e:
                logger.error(f"❌ Error closing port {port}: {e}")

def main():
    """Main function"""
    print("🛰️ MATLAB Bridge - Direct Port Sender")
    print("=" * 50)
    
    # Define the ARS ports as per the plan
    ars_ports = list(range(50038, 50050))  # 50038-50049
    
    # Create bridge sender
    bridge = MATLABBridgeSender(ars_ports)
    
    try:
        # Run simulation for 60 seconds
        bridge.run_simulation(duration=60.0)
        
    except Exception as e:
        logger.error(f"❌ Bridge failed: {e}")
        
    finally:
        # Clean up
        bridge.close_connections()
        logger.info("🧹 Cleanup completed")

if __name__ == "__main__":
    main()
