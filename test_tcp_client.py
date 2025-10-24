#!/usr/bin/env python3
"""
Test Client for TCP Data Dumper

Simple test client that sends sample data to the TCP data dumper
for testing and demonstration purposes.
"""

import socket
import time
import struct
import argparse

def send_test_data(host='127.0.0.1', port=5000, data_type='mixed'):
    """Send test data to the TCP dumper"""
    
    # Create socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to server
        client_socket.connect((host, port))
        print(f"🔗 Connected to {host}:{port}")
        
        if data_type == 'floats':
            # Send floating point data (like from MATLAB)
            print("📤 Sending floating point data...")
            for i in range(5):
                # Send 12 floats (like ARS data)
                floats = [0.1 + i*0.01, -0.05 + i*0.01, 0.02 + i*0.01,
                         1.0 + i*0.1, -0.5 + i*0.1, 0.2 + i*0.1,
                         0.09 + i*0.01, -0.051 + i*0.01, 0.021 + i*0.01,
                         0.99 + i*0.1, -0.49 + i*0.1, 0.19 + i*0.1]
                
                data = struct.pack('<12f', *floats)  # Little-endian floats
                client_socket.send(data)
                print(f"   Sent packet {i+1}: {len(data)} bytes")
                time.sleep(0.1)
        
        elif data_type == 'text':
            # Send text data
            print("📤 Sending text data...")
            messages = [
                b"Hello, TCP Dumper!",
                b"This is test data.",
                b"FlatSat Simulator Data",
                b"ARS Sensor Data",
                b"Magnetometer Data"
            ]
            
            for i, message in enumerate(messages):
                client_socket.send(message)
                print(f"   Sent message {i+1}: {message.decode('ascii', errors='ignore')}")
                time.sleep(0.2)
        
        elif data_type == 'binary':
            # Send binary data
            print("📤 Sending binary data...")
            for i in range(5):
                # Create binary pattern
                data = bytes(range(i*8, (i+1)*8))
                client_socket.send(data)
                print(f"   Sent binary packet {i+1}: {len(data)} bytes")
                time.sleep(0.1)
        
        else:  # mixed
            # Send mixed data types
            print("📤 Sending mixed data...")
            
            # Text data
            client_socket.send(b"FlatSat Test Data")
            time.sleep(0.1)
            
            # Float data
            floats = [1.5, -2.3, 0.7, 3.1]
            data = struct.pack('<4f', *floats)
            client_socket.send(data)
            time.sleep(0.1)
            
            # Binary data
            binary_data = bytes([0xAA, 0x55, 0xFF, 0x00, 0x12, 0x34, 0x56, 0x78])
            client_socket.send(binary_data)
            time.sleep(0.1)
            
            # More text
            client_socket.send(b"End of test data")
        
        print("✅ Test data sent successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client_socket.close()
        print("🔌 Connection closed")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Test client for TCP Data Dumper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_tcp_client.py --port 5000
  python3 test_tcp_client.py --port 5000 --data-type floats
  python3 test_tcp_client.py --port 5000 --data-type text
  python3 test_tcp_client.py --port 5000 --data-type binary
        """
    )
    
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to connect to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to connect to (default: 5000)')
    parser.add_argument('--data-type', choices=['mixed', 'floats', 'text', 'binary'],
                       default='mixed', help='Type of test data to send (default: mixed)')
    
    args = parser.parse_args()
    
    print(f"🚀 TCP Test Client")
    print(f"🎯 Target: {args.host}:{args.port}")
    print(f"📊 Data type: {args.data_type}")
    print("-" * 40)
    
    send_test_data(args.host, args.port, args.data_type)

if __name__ == "__main__":
    main()
