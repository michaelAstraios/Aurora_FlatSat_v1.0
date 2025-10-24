#!/usr/bin/env python3
"""
Test script to verify data flow from MATLAB bridge to FlatSat simulator
"""

import socket
import struct
import time
import threading
from datetime import datetime

def test_single_port(port, duration=10):
    """Test data reception on a single port"""
    print(f"Testing port {port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', port))
        
        start_time = time.time()
        packet_count = 0
        
        while time.time() - start_time < duration:
            # Read exactly 8 bytes
            data = b''
            while len(data) < 8:
                chunk = sock.recv(8 - len(data))
                if not chunk:
                    print(f"Connection closed on port {port}")
                    break
                data += chunk
            
            if len(data) == 8:
                # Convert to float
                float_value = struct.unpack('<d', data)[0]
                packet_count += 1
                
                if packet_count % 10 == 0:
                    print(f"Port {port}: Received packet {packet_count}, value: {float_value:.6f}")
        
        sock.close()
        print(f"Port {port}: Received {packet_count} packets in {duration} seconds")
        return packet_count
        
    except Exception as e:
        print(f"Error testing port {port}: {e}")
        return 0

def main():
    """Test all ARS ports"""
    print("🧪 Testing data flow from MATLAB bridge to FlatSat simulator")
    print("=" * 60)
    
    # Test a few ports
    test_ports = [50038, 50039, 50040, 50041, 50042]
    total_packets = 0
    
    for port in test_ports:
        packets = test_single_port(port, duration=5)
        total_packets += packets
        time.sleep(0.5)  # Small delay between tests
    
    print(f"\n📊 Total packets received: {total_packets}")
    
    if total_packets > 0:
        print("✅ Data flow is working!")
    else:
        print("❌ No data received - check FlatSat simulator")

if __name__ == "__main__":
    main()
