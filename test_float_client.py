#!/usr/bin/env python3
"""
Float Test Client for TCP Data Dumper

This test client sends floating point data to demonstrate the float conversion
functionality of the modified TCP data dumper.
"""

import socket
import struct
import time
import threading
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloatTestClient:
    """Test client that sends floating point data"""
    
    def __init__(self, host='127.0.0.1', start_port=5000, num_ports=3):
        self.host = host
        self.start_port = start_port
        self.num_ports = num_ports
        self.clients = {}
        self.is_running = False
        self.threads = []
        
    def create_tcp_client(self, port):
        """Create a TCP client connection to a specific port"""
        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect((self.host, port))
            logger.info(f"Connected to {self.host}:{port}")
            return client_sock
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{port}: {e}")
            return None
    
    def send_float_data(self, client_sock, port, port_index, duration=10, endianness='little'):
        """Send floating point data to a specific port"""
        logger.info(f"Starting float data transmission on port {port} ({endianness} endian)")
        
        start_time = time.time()
        packet_count = 0
        
        try:
            while time.time() - start_time < duration and self.is_running:
                # Generate test float values
                if port_index == 0:  # Port 5000 - Angular rates
                    value = 0.1 * (port_count % 10) + 0.01 * packet_count
                elif port_index == 1:  # Port 5001 - Angles
                    value = 1.0 * (port_count % 5) + 0.1 * packet_count
                else:  # Port 5002 - Temperature
                    value = 25.0 + 5.0 * (packet_count % 20) / 20.0
                
                # Pack as 8-byte float
                if endianness == 'big':
                    data = struct.pack('>d', value)  # Big endian
                else:
                    data = struct.pack('<d', value)  # Little endian
                
                # Send data
                client_sock.send(data)
                packet_count += 1
                
                # Log every 50 packets
                if packet_count % 50 == 0:
                    logger.info(f"Port {port}: Sent {packet_count} packets, value: {value:.6f}")
                
                # 100ms interval (10 Hz)
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error sending float data on port {port}: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass
            
            logger.info(f"Port {port}: Sent {packet_count} float packets total")
    
    def start_test(self, duration=10, endianness='little'):
        """Start the float test client"""
        logger.info(f"Starting Float Test Client")
        logger.info(f"Target: {self.host}:{self.start_port}-{self.start_port + self.num_ports - 1}")
        logger.info(f"Duration: {duration} seconds")
        logger.info(f"Endianness: {endianness}")
        logger.info("=" * 50)
        
        self.is_running = True
        
        # Create connections to all ports
        for i in range(self.num_ports):
            port = self.start_port + i
            client_sock = self.create_tcp_client(port)
            
            if client_sock:
                self.clients[port] = client_sock
                
                # Start test thread for this port
                thread = threading.Thread(
                    target=self.send_float_data,
                    args=(client_sock, port, i, duration, endianness),
                    daemon=True
                )
                thread.start()
                self.threads.append(thread)
                
                # Small delay between connections
                time.sleep(0.1)
            else:
                logger.warning(f"Failed to connect to port {port}")
        
        logger.info(f"Connected to {len(self.clients)}/{self.num_ports} ports")
        
        # Wait for test to complete
        try:
            for thread in self.threads:
                thread.join()
        except KeyboardInterrupt:
            logger.info("Test interrupted by user")
            self.is_running = False
        
        logger.info("Float test completed")
    
    def stop_test(self):
        """Stop the test client"""
        self.is_running = False
        
        # Close all connections
        for port, client_sock in self.clients.items():
            try:
                client_sock.close()
            except:
                pass
        
        logger.info("Float test client stopped")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Float Test Client for TCP Data Dumper')
    parser.add_argument('--host', default='127.0.0.1', help='Host to connect to')
    parser.add_argument('--start-port', type=int, default=5000, help='Starting port number')
    parser.add_argument('--num-ports', type=int, default=3, help='Number of ports to test')
    parser.add_argument('--duration', type=int, default=10, help='Test duration in seconds')
    parser.add_argument('--endianness', choices=['little', 'big'], default='little', 
                       help='Endianness for float data (default: little)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and start test client
    test_client = FloatTestClient(args.host, args.start_port, args.num_ports)
    
    try:
        test_client.start_test(args.duration, args.endianness)
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    finally:
        test_client.stop_test()

if __name__ == "__main__":
    main()
