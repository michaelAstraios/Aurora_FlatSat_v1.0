#!/usr/bin/env python3
"""
MATLAB Simulator Client
Sends simulated MATLAB data to the MATLAB bridge on port 8888
"""

import socket
import time
import struct
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

class MATLABSimulatorClient:
    """Sends simulated MATLAB data to the MATLAB bridge"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self.host = host
        self.port = port
        self.socket = None
        
    def connect(self):
        """Connect to the MATLAB bridge"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.info(f"✅ Connected to MATLAB bridge at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MATLAB bridge: {e}")
            return False
    
    def generate_realistic_attitude_data(self, time_offset: float) -> List[float]:
        """Generate realistic attitude data for all 12 ARS ports"""
        data = []
        
        # Generate data for ports 50038-50049 (12 ports total)
        for i in range(12):
            if i < 6:  # Ports 50038-50043: Angular rates
                base_rate = 0.0001  # 0.1 mrad/s
                variation = base_rate * 0.5 * (random.random() - 0.5)
                time_variation = base_rate * 0.3 * (math.sin(time_offset * 0.1 + i))
                value = variation + time_variation
            else:  # Ports 50044-50049: Angular positions
                base_angle = 0.001  # 1 mrad
                variation = base_angle * 0.5 * (random.random() - 0.5)
                time_variation = base_angle * 0.3 * (math.sin(time_offset * 0.05 + i))
                value = variation + time_variation
            
            data.append(value)
        
        return data
    
    def send_data(self, data: List[float]):
        """Send data to the MATLAB bridge"""
        if not self.socket:
            logger.error("❌ Not connected to MATLAB bridge")
            return False
        
        try:
            # Pack all 12 float values into bytes
            data_bytes = b''
            for value in data:
                data_bytes += struct.pack('<d', value)  # Little-endian double
            
            self.socket.sendall(data_bytes)
            logger.debug(f"📡 Sent {len(data)} values: {[f'{x:.6f}' for x in data[:3]]}...")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send data: {e}")
            return False
    
    def run_simulation(self, duration: float = 60.0):
        """Run the simulation"""
        if not self.connect():
            return
        
        logger.info(f"🚀 Starting MATLAB simulation for {duration} seconds")
        start_time = time.time()
        packet_count = 0
        
        try:
            while (time.time() - start_time) < duration:
                time_offset = time.time() - start_time
                data = self.generate_realistic_attitude_data(time_offset)
                
                if self.send_data(data):
                    packet_count += 1
                    if packet_count % 100 == 0:
                        logger.info(f"📡 Sent packet {packet_count}")
                
                time.sleep(0.01)  # 100 Hz
            
            logger.info(f"✅ Simulation completed: {packet_count} packets sent")
            
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        except Exception as e:
            logger.error(f"❌ Simulation failed: {e}")
        finally:
            self.disconnect()
    
    def disconnect(self):
        """Disconnect from the MATLAB bridge"""
        if self.socket:
            self.socket.close()
            logger.info("🔌 Disconnected from MATLAB bridge")

def main():
    """Main function"""
    print("🛰️ MATLAB Simulator Client")
    print("==================================================")
    
    client = MATLABSimulatorClient()
    client.run_simulation(duration=60)

if __name__ == "__main__":
    main()
