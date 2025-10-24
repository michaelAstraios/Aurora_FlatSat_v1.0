#!/usr/bin/env python3
"""
Test Client for FlatSat Simulator Data Flow Verification
Sends test data to ports 50038-50049 to verify MATLAB simulator communication
"""

import socket
import time
import struct
import random
import threading
from typing import List

class FlatSatTestClient:
    def __init__(self, ports: List[int], host: str = "127.0.0.1"):
        self.ports = ports
        self.host = host
        self.sockets = {}
        self.running = False
        
    def connect_to_ports(self):
        """Connect to all specified ports"""
        for port in self.ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, port))
                self.sockets[port] = sock
                print(f"✅ Connected to port {port}")
            except Exception as e:
                print(f"❌ Failed to connect to port {port}: {e}")
                
    def generate_test_data(self, port: int) -> bytes:
        """Generate test data based on port number"""
        # Generate realistic attitude data based on port mapping
        if port in [50038, 50041]:  # Roll rates (primary and redundant)
            value = random.uniform(-0.0001, 0.0001)  # Small roll rate
        elif port in [50039, 50042]:  # Pitch rates (primary and redundant)
            value = random.uniform(-0.0001, 0.0001)  # Small pitch rate
        elif port in [50040, 50043]:  # Yaw rates (primary and redundant)
            value = random.uniform(-0.0001, 0.0001)  # Small yaw rate
        elif port in [50044, 50047]:  # Roll angles (primary and redundant)
            value = random.uniform(-0.001, 0.001)  # Small roll angle
        elif port in [50045, 50048]:  # Pitch angles (primary and redundant)
            value = random.uniform(-0.001, 0.001)  # Small pitch angle
        elif port in [50046, 50049]:  # Yaw angles (primary and redundant)
            value = random.uniform(-0.001, 0.001)  # Small yaw angle
        else:
            value = random.uniform(-1.0, 1.0)  # Generic value
            
        # Convert to 64-bit float (8 bytes) in little-endian format
        return struct.pack('<d', value)
        
    def send_data_to_port(self, port: int):
        """Send data to a specific port"""
        if port not in self.sockets:
            return
            
        sock = self.sockets[port]
        try:
            data = self.generate_test_data(port)
            sock.send(data)
            print(f"📡 Sent data to port {port}: {data.hex()} ({struct.unpack('<d', data)[0]:.6f})")
        except Exception as e:
            print(f"❌ Error sending data to port {port}: {e}")
            
    def send_data_to_all_ports(self):
        """Send data to all connected ports"""
        for port in self.sockets:
            self.send_data_to_port(port)
            
    def run_test(self, duration: int = 30, interval: float = 0.1):
        """Run the test for specified duration"""
        print(f"🚀 Starting FlatSat simulator test for {duration} seconds...")
        print(f"📡 Sending data every {interval} seconds to ports: {self.ports}")
        
        self.running = True
        start_time = time.time()
        
        try:
            while self.running and (time.time() - start_time) < duration:
                self.send_data_to_all_ports()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹️ Test interrupted by user")
            
        self.running = False
        print("✅ Test completed")
        
    def close_connections(self):
        """Close all connections"""
        for port, sock in self.sockets.items():
            try:
                sock.close()
                print(f"🔌 Closed connection to port {port}")
            except Exception as e:
                print(f"❌ Error closing port {port}: {e}")

def main():
    """Main test function"""
    print("🛰️ FlatSat Simulator Data Flow Test")
    print("=" * 50)
    
    # Define the ARS ports as per the plan
    ars_ports = list(range(50038, 50050))  # 50038-50049
    
    # Create test client
    client = FlatSatTestClient(ars_ports)
    
    try:
        # Connect to all ports
        print("🔌 Connecting to FlatSat simulator ports...")
        client.connect_to_ports()
        
        if not client.sockets:
            print("❌ No connections established. Exiting.")
            return
            
        print(f"✅ Connected to {len(client.sockets)} ports")
        
        # Run the test
        client.run_test(duration=30, interval=0.1)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        # Clean up
        client.close_connections()
        print("🧹 Cleanup completed")

if __name__ == "__main__":
    main()
