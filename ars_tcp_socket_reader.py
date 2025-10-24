#!/usr/bin/env python3
"""
ARS Sensor TCP Socket Reader and Rate Sensor Simulator

This application listens to ARS sensor data from 12 sequential TCP ports representing:
- ARS Prime X, Y, Z (ports 0-2)
- ARS Redundant X, Y, Z (ports 3-5) 
- Summed Incremental Prime X, Y, Z (ports 6-8)
- Summed Incremental Redundant X, Y, Z (ports 9-11)

The data comes as 8-byte 64-bit floats every 10ms and is converted to simulate
the Honeywell Rate Sensor output format.
"""

import socket
import struct
import threading
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ARSData:
    """Data structure for ARS sensor readings"""
    # Prime angular rates
    prime_x: float = 0.0
    prime_y: float = 0.0
    prime_z: float = 0.0
    
    # Redundant angular rates
    redundant_x: float = 0.0
    redundant_y: float = 0.0
    redundant_z: float = 0.0
    
    # Prime summed incremental angles
    prime_angle_x: float = 0.0
    prime_angle_y: float = 0.0
    prime_angle_z: float = 0.0
    
    # Redundant summed incremental angles
    redundant_angle_x: float = 0.0
    redundant_angle_y: float = 0.0
    redundant_angle_z: float = 0.0
    
    # Metadata
    timestamp: float = 0.0
    port_data_count: Dict[int, int] = None
    
    def __post_init__(self):
        if self.port_data_count is None:
            self.port_data_count = {i: 0 for i in range(12)}

@dataclass
class RateSensorSimulatedData:
    """Simulated Rate Sensor data structure matching Honeywell format"""
    # Angular rates (using Prime data as primary)
    angular_rate_x: float = 0.0
    angular_rate_y: float = 0.0
    angular_rate_z: float = 0.0
    
    # Summed incremental angles (using Prime data)
    summed_angle_x: float = 0.0
    summed_angle_y: float = 0.0
    summed_angle_z: float = 0.0
    
    # Status words (simulated)
    status_word_1: int = 0x0000
    status_word_2: int = 0x0019  # Temperature ~25°C
    status_word_3: int = 0xE000  # All gyros running
    
    # Additional metadata
    timestamp: float = 0.0
    message_counter: int = 0
    data_source: str = "ARS_TCP_SIMULATED"

class TCPSocketReader:
    """Handles TCP socket communication for ARS sensor data"""
    
    def __init__(self, ip_address: str, start_port: int, num_ports: int = 12):
        self.ip_address = ip_address
        self.start_port = start_port
        self.num_ports = num_ports
        self.servers: List[socket.socket] = []
        self.clients: Dict[int, socket.socket] = {}  # Track client connections per port
        self.is_running = False
        self.threads: List[threading.Thread] = []
        self.data_lock = threading.Lock()
        self.latest_data = ARSData()
        self.data_history = deque(maxlen=100)  # Keep last 100 samples
        
        # TCP-specific settings
        self.max_clients_per_port = 1  # Only allow one client per port
        self.client_timeout = 30.0  # 30 second timeout for client connections
        
    def _create_tcp_server(self, port: int) -> Optional[socket.socket]:
        """Create and configure a TCP server socket for the given port"""
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.ip_address, port))
            server_sock.listen(1)  # Allow one pending connection
            server_sock.settimeout(1.0)  # 1 second timeout for accept
            logger.info(f"TCP server created for port {port}")
            return server_sock
        except Exception as e:
            logger.error(f"Failed to create TCP server for port {port}: {e}")
            return None
    
    def _parse_float_data(self, data: bytes, is_big_endian: bool = False) -> Optional[float]:
        """Parse 8-byte data as 64-bit float"""
        if len(data) != 8:
            logger.warning(f"Expected 8 bytes, got {len(data)}")
            return None
            
        try:
            if is_big_endian:
                value = struct.unpack('>d', data)[0]  # Big endian double
            else:
                value = struct.unpack('<d', data)[0]  # Little endian double
            return value
        except struct.error as e:
            logger.error(f"Failed to parse float data: {e}")
            return None
    
    def _handle_client_connection(self, client_sock: socket.socket, client_addr: Tuple[str, int], port: int, port_index: int):
        """Handle data from a connected TCP client"""
        logger.info(f"Client connected from {client_addr[0]}:{client_addr[1]} on port {port}")
        
        try:
            client_sock.settimeout(1.0)  # 1 second timeout for recv
            
            while self.is_running:
                try:
                    # Receive data from client
                    data = client_sock.recv(1024)
                    
                    if not data:
                        logger.info(f"Client {client_addr[0]}:{client_addr[1]} disconnected from port {port}")
                        break
                    
                    if len(data) >= 8:
                        # Parse the float value
                        float_value = self._parse_float_data(data[:8])
                        
                        if float_value is not None:
                            # Update the latest data
                            with self.data_lock:
                                # Map port index to data field
                                if port_index == 0:  # Prime X
                                    self.latest_data.prime_x = float_value
                                elif port_index == 1:  # Prime Y
                                    self.latest_data.prime_y = float_value
                                elif port_index == 2:  # Prime Z
                                    self.latest_data.prime_z = float_value
                                elif port_index == 3:  # Redundant X
                                    self.latest_data.redundant_x = float_value
                                elif port_index == 4:  # Redundant Y
                                    self.latest_data.redundant_y = float_value
                                elif port_index == 5:  # Redundant Z
                                    self.latest_data.redundant_z = float_value
                                elif port_index == 6:  # Prime Angle X
                                    self.latest_data.prime_angle_x = float_value
                                elif port_index == 7:  # Prime Angle Y
                                    self.latest_data.prime_angle_y = float_value
                                elif port_index == 8:  # Prime Angle Z
                                    self.latest_data.prime_angle_z = float_value
                                elif port_index == 9:  # Redundant Angle X
                                    self.latest_data.redundant_angle_x = float_value
                                elif port_index == 10:  # Redundant Angle Y
                                    self.latest_data.redundant_angle_y = float_value
                                elif port_index == 11:  # Redundant Angle Z
                                    self.latest_data.redundant_angle_z = float_value
                                
                                # Update timestamp and counter
                                self.latest_data.timestamp = time.time()
                                self.latest_data.port_data_count[port_index] += 1
                                
                                logger.debug(f"Port {port}: {float_value:.6f} (count: {self.latest_data.port_data_count[port_index]})")
                    
                except socket.timeout:
                    continue  # Normal timeout, keep listening
                except Exception as e:
                    if self.is_running:  # Only log if we're supposed to be running
                        logger.error(f"Error handling client {client_addr} on port {port}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in client handler for port {port}: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass
            
            # Remove client from tracking
            with self.data_lock:
                if port in self.clients:
                    del self.clients[port]
            
            logger.info(f"Client handler for port {port} stopped")
    
    def _tcp_server_listener(self, server_sock: socket.socket, port: int, port_index: int):
        """Listen for TCP connections on a specific port"""
        logger.info(f"Starting TCP server listener for port {port} (index {port_index})")
        
        while self.is_running:
            try:
                # Accept client connection
                client_sock, client_addr = server_sock.accept()
                
                # Check if we already have a client for this port
                with self.data_lock:
                    if port in self.clients:
                        logger.warning(f"Port {port} already has a client, rejecting new connection from {client_addr}")
                        client_sock.close()
                        continue
                    
                    # Track the client
                    self.clients[port] = client_sock
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self._handle_client_connection,
                    args=(client_sock, client_addr, port, port_index),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                continue  # Normal timeout, keep listening
            except Exception as e:
                if self.is_running:  # Only log if we're supposed to be running
                    logger.error(f"Error in TCP server listener for port {port}: {e}")
                break
        
        logger.info(f"TCP server listener for port {port} stopped")
    
    def start_listening(self) -> bool:
        """Start listening on all configured TCP ports"""
        logger.info(f"Starting TCP server readers for {self.ip_address}:{self.start_port}-{self.start_port + self.num_ports - 1}")
        
        self.is_running = True
        
        # Create TCP servers for all ports
        for i in range(self.num_ports):
            port = self.start_port + i
            server_sock = self._create_tcp_server(port)
            
            if server_sock:
                self.servers.append(server_sock)
                # Start server listener thread
                thread = threading.Thread(
                    target=self._tcp_server_listener,
                    args=(server_sock, port, i),
                    daemon=True
                )
                thread.start()
                self.threads.append(thread)
                logger.info(f"TCP server started for port {port}")
            else:
                logger.error(f"Failed to start TCP server for port {port}")
                return False
        
        logger.info(f"All TCP servers started successfully")
        return True
    
    def stop_listening(self):
        """Stop listening on all ports"""
        logger.info("Stopping TCP servers...")
        self.is_running = False
        
        # Close all client connections
        with self.data_lock:
            for port, client_sock in self.clients.items():
                try:
                    client_sock.close()
                except:
                    pass
            self.clients.clear()
        
        # Close all server sockets
        for server_sock in self.servers:
            try:
                server_sock.close()
            except:
                pass
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2.0)
        
        logger.info("All TCP servers stopped")
    
    def get_latest_data(self) -> ARSData:
        """Get the latest ARS data"""
        with self.data_lock:
            return self.latest_data
    
    def get_data_history(self) -> List[ARSData]:
        """Get the data history"""
        with self.data_lock:
            return list(self.data_history)
    
    def get_client_status(self) -> Dict[int, bool]:
        """Get status of client connections per port"""
        with self.data_lock:
            return {port: port in self.clients for port in range(self.start_port, self.start_port + self.num_ports)}

class RateSensorSimulator:
    """Simulates Honeywell Rate Sensor output from ARS data"""
    
    def __init__(self, socket_reader: TCPSocketReader):
        self.socket_reader = socket_reader
        self.message_counter = 0
        
    def generate_simulated_data(self) -> RateSensorSimulatedData:
        """Generate simulated rate sensor data from current ARS readings"""
        ars_data = self.socket_reader.get_latest_data()
        
        simulated_data = RateSensorSimulatedData(
            # Use prime data as primary angular rates
            angular_rate_x=ars_data.prime_x,
            angular_rate_y=ars_data.prime_y,
            angular_rate_z=ars_data.prime_z,
            
            # Use prime data as primary summed angles
            summed_angle_x=ars_data.prime_angle_x,
            summed_angle_y=ars_data.prime_angle_y,
            summed_angle_z=ars_data.prime_angle_z,
            
            # Status words (simulated)
            status_word_1=0x0000,  # Normal operation
            status_word_2=0x0019,  # Temperature ~25°C
            status_word_3=0xE000,  # All gyros running
            
            # Metadata
            timestamp=ars_data.timestamp,
            message_counter=self.message_counter,
            data_source="ARS_TCP_SIMULATED"
        )
        
        self.message_counter += 1
        return simulated_data
    
    def get_status_report(self) -> Dict:
        """Get a status report of the simulation"""
        ars_data = self.socket_reader.get_latest_data()
        client_status = self.socket_reader.get_client_status()
        
        return {
            "timestamp": time.time(),
            "message_counter": self.message_counter,
            "data_source": "ARS_TCP_SIMULATED",
            "client_connections": client_status,
            "port_data_counts": ars_data.port_data_count,
            "latest_data": {
                "prime_rates": [ars_data.prime_x, ars_data.prime_y, ars_data.prime_z],
                "redundant_rates": [ars_data.redundant_x, ars_data.redundant_y, ars_data.redundant_z],
                "prime_angles": [ars_data.prime_angle_x, ars_data.prime_angle_y, ars_data.prime_angle_z],
                "redundant_angles": [ars_data.redundant_angle_x, ars_data.redundant_angle_y, ars_data.redundant_angle_z]
            }
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='ARS TCP Socket Reader and Rate Sensor Simulator')
    parser.add_argument('--ip', default='127.0.0.1', help='IP address to listen on')
    parser.add_argument('--start-port', type=int, default=5000, help='Starting port number')
    parser.add_argument('--num-ports', type=int, default=12, help='Number of ports to listen on')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Load configuration if provided
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            return 1
    
    # Override with config if available
    ip_address = config.get('ip_address', args.ip)
    start_port = config.get('start_port', args.start_port)
    num_ports = config.get('num_ports', args.num_ports)
    
    logger.info(f"Starting ARS TCP Socket Reader")
    logger.info(f"IP: {ip_address}, Ports: {start_port}-{start_port + num_ports - 1}")
    
    # Create socket reader
    socket_reader = TCPSocketReader(ip_address, start_port, num_ports)
    
    # Create simulator
    simulator = RateSensorSimulator(socket_reader)
    
    try:
        # Start listening
        if not socket_reader.start_listening():
            logger.error("Failed to start TCP servers")
            return 1
        
        logger.info("ARS TCP Socket Reader started successfully")
        logger.info("Press Ctrl+C to stop")
        
        # Main loop - display status periodically
        while True:
            time.sleep(10)  # Update every 10 seconds
            
            status = simulator.get_status_report()
            logger.info(f"Status: {status['message_counter']} messages, "
                       f"Connected clients: {sum(status['client_connections'].values())}/{num_ports}")
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        socket_reader.stop_listening()
        logger.info("ARS TCP Socket Reader stopped")
    
    return 0

if __name__ == "__main__":
    exit(main())
