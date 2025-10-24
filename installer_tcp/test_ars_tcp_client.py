#!/usr/bin/env python3
"""
TCP Test Client for ARS Socket Reader

This test client connects to the ARS TCP Socket Reader and sends test data
to verify the TCP-based ARS system is working correctly.
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

class ARSTCPTestClient:
    """TCP test client for ARS socket reader"""
    
    def __init__(self, host='127.0.0.1', start_port=5000, num_ports=12):
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
    
    def send_test_data(self, client_sock, port, port_index, duration=10):
        """Send test data to a specific port"""
        logger.info(f"Starting test data transmission on port {port}")
        
        start_time = time.time()
        packet_count = 0
        
        try:
            while time.time() - start_time < duration and self.is_running:
                # Generate test data based on port index
                if port_index < 3:  # Prime rates (X, Y, Z)
                    value = 0.1 * (port_index + 1) + 0.01 * packet_count
                elif port_index < 6:  # Redundant rates (X, Y, Z)
                    value = 0.1 * (port_index - 2) + 0.01 * packet_count + 0.001
                elif port_index < 9:  # Prime angles (X, Y, Z)
                    value = 1.0 * (port_index - 5) + 0.1 * packet_count
                else:  # Redundant angles (X, Y, Z)
                    value = 1.0 * (port_index - 8) + 0.1 * packet_count + 0.01
                
                # Pack as 8-byte float (little endian)
                data = struct.pack('<d', value)
                
                # Send data
                client_sock.send(data)
                packet_count += 1
                
                # Log every 100 packets
                if packet_count % 100 == 0:
                    logger.info(f"Port {port}: Sent {packet_count} packets, value: {value:.6f}")
                
                # 10ms interval (100 Hz)
                time.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error sending data on port {port}: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass
            
            logger.info(f"Port {port}: Sent {packet_count} packets total")
    
    def start_test(self, duration=10):
        """Start the test client"""
        logger.info(f"Starting ARS TCP Test Client")
        logger.info(f"Target: {self.host}:{self.start_port}-{self.start_port + self.num_ports - 1}")
        logger.info(f"Duration: {duration} seconds")
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
                    target=self.send_test_data,
                    args=(client_sock, port, i, duration),
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
        
        logger.info("Test completed")
    
    def stop_test(self):
        """Stop the test client"""
        self.is_running = False
        
        # Close all connections
        for port, client_sock in self.clients.items():
            try:
                client_sock.close()
            except:
                pass
        
        logger.info("Test client stopped")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='ARS TCP Test Client')
    parser.add_argument('--host', default='127.0.0.1', help='Host to connect to')
    parser.add_argument('--start-port', type=int, default=5000, help='Starting port number')
    parser.add_argument('--num-ports', type=int, default=12, help='Number of ports to test')
    parser.add_argument('--duration', type=int, default=10, help='Test duration in seconds')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and start test client
    test_client = ARSTCPTestClient(args.host, args.start_port, args.num_ports)
    
    try:
        test_client.start_test(args.duration)
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    finally:
        test_client.stop_test()

if __name__ == "__main__":
    main()
