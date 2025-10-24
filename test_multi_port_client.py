#!/usr/bin/env python3
"""
Multi-Port Test Client for TCP Data Dumper

Test client that sends data to multiple ports simultaneously
to demonstrate the multi-port TCP data dumper functionality.
"""

import socket
import time
import struct
import threading
import argparse

def send_data_to_port(host, port, data_type, duration=5):
    """Send test data to a specific port"""
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        
        print(f"🔗 Connected to {host}:{port}")
        
        start_time = time.time()
        packet_count = 0
        
        while time.time() - start_time < duration:
            if data_type == 'floats':
                # Send floating point data (like ARS)
                floats = [0.1 + packet_count*0.01, -0.05 + packet_count*0.01, 0.02 + packet_count*0.01,
                         1.0 + packet_count*0.1, -0.5 + packet_count*0.1, 0.2 + packet_count*0.1,
                         0.09 + packet_count*0.01, -0.051 + packet_count*0.01, 0.021 + packet_count*0.01,
                         0.99 + packet_count*0.1, -0.49 + packet_count*0.1, 0.19 + packet_count*0.1]
                data = struct.pack('<12f', *floats)
                
            elif data_type == 'text':
                # Send text data
                message = f"Port {port} message {packet_count}"
                data = message.encode('ascii')
                
            elif data_type == 'binary':
                # Send binary data
                data = bytes([(port % 256) + packet_count, 0xAA, 0x55, 0xFF, 
                             0x00, 0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE])
            
            else:  # mixed
                # Send mixed data
                if packet_count % 3 == 0:
                    data = f"Text from port {port}".encode('ascii')
                elif packet_count % 3 == 1:
                    floats = [1.5 + port*0.1, -2.3 + port*0.1, 0.7 + port*0.1]
                    data = struct.pack('<3f', *floats)
                else:
                    data = bytes([port % 256, 0xFF, 0x00, 0xAA, 0x55])
            
            client_socket.send(data)
            packet_count += 1
            time.sleep(0.1)  # 10 Hz rate
        
        print(f"✅ Port {port}: Sent {packet_count} packets")
        
    except Exception as e:
        print(f"❌ Port {port}: Error: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass

def test_multiple_ports(host='127.0.0.1', ports=None, data_type='mixed', duration=5):
    """Test multiple ports simultaneously"""
    if ports is None:
        ports = [5000, 5001, 5002]
    
    print(f"🚀 Multi-Port Test Client")
    print(f"🎯 Target: {host}")
    print(f"📡 Ports: {', '.join(map(str, ports))}")
    print(f"📊 Data type: {data_type}")
    print(f"⏱️  Duration: {duration} seconds")
    print("-" * 50)
    
    # Start threads for each port
    threads = []
    for port in ports:
        thread = threading.Thread(target=send_data_to_port, args=(host, port, data_type, duration))
        thread.start()
        threads.append(thread)
        time.sleep(0.1)  # Stagger connections
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print(f"\n✅ Test completed for all ports")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Multi-Port Test Client for TCP Data Dumper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_multi_port_client.py --ports 5000,5001,5002
  python3 test_multi_port_client.py --port-range 5000-5005 --data-type floats
  python3 test_multi_port_client.py --ports 5000,6000,7000 --data-type text --duration 10
        """
    )
    
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to connect to (default: 127.0.0.1)')
    parser.add_argument('--ports', 
                       help='Comma-separated list of ports (e.g., 5000,5001,5002)')
    parser.add_argument('--port-range', 
                       help='Port range (e.g., 5000-5005)')
    parser.add_argument('--data-type', choices=['mixed', 'floats', 'text', 'binary'],
                       default='mixed', help='Type of test data to send (default: mixed)')
    parser.add_argument('--duration', type=int, default=5,
                       help='Test duration in seconds (default: 5)')
    
    args = parser.parse_args()
    
    # Parse ports
    ports = []
    if args.ports:
        ports = [int(p.strip()) for p in args.ports.split(',')]
    elif args.port_range:
        start, end = args.port_range.split('-')
        ports = list(range(int(start), int(end) + 1))
    else:
        ports = [5000, 5001, 5002]  # Default
    
    test_multiple_ports(args.host, ports, args.data_type, args.duration)

if __name__ == "__main__":
    main()
