#!/usr/bin/env python3
"""
Python Bridge for MATLAB Orbital Simulator
Device Format Communication Handler

This Python script acts as a bridge between the MATLAB orbital simulator
and the FlatSat device encoders/transmitters. It receives orbital data
from MATLAB and converts it to proper device formats for transmission
via TCP/IP USB-to-serial or CAN bus interfaces.
"""

import socket
import json
import time
import logging
import threading
import sys
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from queue import Queue, Empty

# Add device encoders to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'device_encoders'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'output_transmitters'))

try:
    from ars_encoder import ARSEncoder
    from magnetometer_encoder import MagnetometerEncoder
    from reaction_wheel_encoder import ReactionWheelEncoder
    from tcp_transmitter import TCPTransmitter, TCPConfig
    from can_transmitter import CANTransmitter, CANConfig
except ImportError as e:
    print(f"Warning: Could not import device encoders/transmitters: {e}")
    print("Running in simulation mode")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BridgeConfig:
    """Bridge configuration"""
    listen_ip: str = "127.0.0.1"
    listen_port: int = 8888
    protocol: str = "tcp"  # "tcp" or "can"
    device_configs: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.device_configs is None:
            self.device_configs = {
                "tcp": {
                    "target_ip": "192.168.1.200",
                    "target_port": 8000
                },
                "can": {
                    "interface": "socketcan",
                    "channel": "can0",
                    "bitrate": 500000
                }
            }

class DeviceBridge:
    """Bridge between MATLAB simulator and device transmitters"""
    
    def __init__(self, config: BridgeConfig):
        self.config = config
        self.socket: Optional[socket.socket] = None
        self.is_running = False
        self.message_queue = Queue()
        
        # Initialize device encoders
        self.ars_encoder = ARSEncoder(duplicate_to_redundant=True, variation_percent=0.1)
        self.mag_encoder = MagnetometerEncoder()
        self.rw_encoder = ReactionWheelEncoder()
        
        # Initialize transmitters
        self.transmitters = {}
        self._initialize_transmitters()
        
        # Statistics
        self.stats = {
            "messages_received": 0,
            "ars_packets_sent": 0,
            "mag_packets_sent": 0,
            "rw_packets_sent": 0,
            "errors": 0
        }
    
    def _initialize_transmitters(self):
        """Initialize transmitters based on configuration"""
        try:
            if self.config.protocol == "tcp":
                tcp_config = TCPConfig(
                    target_ip=self.config.device_configs["tcp"]["target_ip"],
                    target_port=self.config.device_configs["tcp"]["target_port"]
                )
                self.transmitters["tcp"] = TCPTransmitter(tcp_config)
                if self.transmitters["tcp"].connect():
                    self.transmitters["tcp"].start_transmission()
                    logger.info("TCP transmitter initialized")
                else:
                    logger.warning("TCP transmitter failed to connect - running in simulation mode")
            
            elif self.config.protocol == "can":
                can_config = CANConfig(
                    interface=self.config.device_configs["can"]["interface"],
                    channel=self.config.device_configs["can"]["channel"],
                    bitrate=self.config.device_configs["can"]["bitrate"]
                )
                self.transmitters["can"] = CANTransmitter(can_config)
                if self.transmitters["can"].connect():
                    self.transmitters["can"].start_transmission()
                    logger.info("CAN transmitter initialized")
                else:
                    logger.warning("CAN transmitter failed to connect - running in simulation mode")
            
        except Exception as e:
            logger.error(f"Failed to initialize transmitters: {e}")
    
    def start(self):
        """Start the bridge server"""
        try:
            # Create server socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.config.listen_ip, self.config.listen_port))
            self.socket.listen(1)
            
            self.is_running = True
            logger.info(f"Bridge server listening on {self.config.listen_ip}:{self.config.listen_port}")
            
            # Start message processing thread
            processing_thread = threading.Thread(target=self._process_messages, daemon=True)
            processing_thread.start()
            
            # Main server loop
            while self.is_running:
                try:
                    client_socket, client_address = self.socket.accept()
                    logger.info(f"MATLAB client connected from {client_address}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.is_running:
                        logger.error(f"Socket error: {e}")
                    break
            
        except Exception as e:
            logger.error(f"Failed to start bridge server: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop the bridge server"""
        self.is_running = False
        
        if self.socket:
            self.socket.close()
        
        # Disconnect all transmitters
        for transmitter in self.transmitters.values():
            transmitter.disconnect()
        
        logger.info("Bridge server stopped")
    
    def _handle_client(self, client_socket: socket.socket, client_address):
        """Handle communication with MATLAB client"""
        try:
            while self.is_running:
                # Receive message from MATLAB
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    self.message_queue.put((message, client_socket))
                    self.stats["messages_received"] += 1
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from MATLAB: {e}")
                    self.stats["errors"] += 1
                
        except Exception as e:
            logger.error(f"Error handling MATLAB client: {e}")
        finally:
            client_socket.close()
            logger.info(f"MATLAB client {client_address} disconnected")
    
    def _process_messages(self):
        """Process messages from MATLAB"""
        while self.is_running:
            try:
                message, client_socket = self.message_queue.get(timeout=0.1)
                self._process_matlab_message(message, client_socket)
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                self.stats["errors"] += 1
    
    def _process_matlab_message(self, message: Dict[str, Any], client_socket: socket.socket):
        """Process a message from MATLAB"""
        try:
            command = message.get("command")
            
            if command == "init":
                self._handle_init(message, client_socket)
            elif command == "send_data":
                self._handle_send_data(message, client_socket)
            elif command == "shutdown":
                self._handle_shutdown(message, client_socket)
            else:
                logger.warning(f"Unknown command: {command}")
                self.stats["errors"] += 1
                
        except Exception as e:
            logger.error(f"Error processing MATLAB message: {e}")
            self.stats["errors"] += 1
    
    def _handle_init(self, message: Dict[str, Any], client_socket: socket.socket):
        """Handle initialization message from MATLAB"""
        try:
            config = message.get("config", {})
            
            # Update bridge configuration if provided
            if "protocol" in config:
                self.config.protocol = config["protocol"]
            
            # Send acknowledgment
            response = {"status": "ready", "protocol": self.config.protocol}
            client_socket.send(json.dumps(response).encode('utf-8'))
            
            logger.info(f"MATLAB client initialized with protocol: {self.config.protocol}")
            
        except Exception as e:
            logger.error(f"Error handling init: {e}")
            self.stats["errors"] += 1
    
    def _handle_send_data(self, message: Dict[str, Any], client_socket: socket.socket):
        """Handle data transmission message from MATLAB"""
        try:
            device_type = message.get("device_type")
            data = message.get("data", [])
            timestamp = message.get("timestamp", time.time())
            
            # Process data based on device type
            if device_type == "ars":
                self._process_ars_data(data, timestamp)
            elif device_type == "magnetometer":
                self._process_magnetometer_data(data, timestamp)
            elif device_type == "reaction_wheel":
                self._process_reaction_wheel_data(data, timestamp)
            else:
                logger.warning(f"Unknown device type: {device_type}")
                self.stats["errors"] += 1
                return
            
            # Send acknowledgment
            response = {"status": "sent", "device_type": device_type, "timestamp": timestamp}
            client_socket.send(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error handling send_data: {e}")
            self.stats["errors"] += 1
    
    def _handle_shutdown(self, message: Dict[str, Any], client_socket: socket.socket):
        """Handle shutdown message from MATLAB"""
        try:
            response = {"status": "shutdown_ack"}
            client_socket.send(json.dumps(response).encode('utf-8'))
            
            logger.info("MATLAB client requested shutdown")
            
        except Exception as e:
            logger.error(f"Error handling shutdown: {e}")
            self.stats["errors"] += 1
    
    def _process_ars_data(self, data: List[float], timestamp: float):
        """Process ARS data and send via appropriate transmitter"""
        try:
            # Convert MATLAB data to device format
            encoded_bytes = self.ars_encoder.process_matlab_data(data)
            
            if encoded_bytes:
                # Send via appropriate transmitter
                if self.config.protocol == "tcp" and "tcp" in self.transmitters:
                    success = self.transmitters["tcp"].send_data(encoded_bytes, "ars")
                    if success:
                        self.stats["ars_packets_sent"] += 1
                        logger.debug(f"Sent ARS data: {len(encoded_bytes)} bytes")
                
                elif self.config.protocol == "can" and "can" in self.transmitters:
                    # For CAN, we need a CAN ID (using ARS ID from specification)
                    can_id = 0x100  # ARS CAN ID
                    success = self.transmitters["can"].send_message(can_id, encoded_bytes, "ars")
                    if success:
                        self.stats["ars_packets_sent"] += 1
                        logger.debug(f"Sent ARS CAN message ID 0x{can_id:03X}: {len(encoded_bytes)} bytes")
                
                else:
                    # Simulation mode
                    logger.debug(f"Simulation: ARS data {len(data)} floats -> {len(encoded_bytes)} bytes")
                    self.stats["ars_packets_sent"] += 1
            
        except Exception as e:
            logger.error(f"Error processing ARS data: {e}")
            self.stats["errors"] += 1
    
    def _process_magnetometer_data(self, data: List[float], timestamp: float):
        """Process magnetometer data and send via appropriate transmitter"""
        try:
            if self.config.protocol == "tcp":
                # Use RS485 format for TCP
                encoded_bytes = self.mag_encoder.process_matlab_data_rs485(data)
                
                if encoded_bytes and "tcp" in self.transmitters:
                    success = self.transmitters["tcp"].send_data(encoded_bytes, "magnetometer")
                    if success:
                        self.stats["mag_packets_sent"] += 1
                        logger.debug(f"Sent magnetometer data: {len(encoded_bytes)} bytes")
            
            elif self.config.protocol == "can":
                # Use CAN format
                result = self.mag_encoder.process_matlab_data_can(data)
                
                if result and "can" in self.transmitters:
                    can_id, encoded_bytes = result
                    success = self.transmitters["can"].send_message(can_id, encoded_bytes, "magnetometer")
                    if success:
                        self.stats["mag_packets_sent"] += 1
                        logger.debug(f"Sent magnetometer CAN message ID 0x{can_id:03X}: {len(encoded_bytes)} bytes")
            
            else:
                # Simulation mode
                logger.debug(f"Simulation: Magnetometer data {len(data)} floats")
                self.stats["mag_packets_sent"] += 1
            
        except Exception as e:
            logger.error(f"Error processing magnetometer data: {e}")
            self.stats["errors"] += 1
    
    def _process_reaction_wheel_data(self, data: List[float], timestamp: float):
        """Process reaction wheel data and send via appropriate transmitter"""
        try:
            # Use health status telemetry format
            encoded_bytes = self.rw_encoder.process_matlab_data_health(data)
            
            if encoded_bytes:
                # Send via appropriate transmitter
                if self.config.protocol == "tcp" and "tcp" in self.transmitters:
                    success = self.transmitters["tcp"].send_data(encoded_bytes, "reaction_wheel")
                    if success:
                        self.stats["rw_packets_sent"] += 1
                        logger.debug(f"Sent reaction wheel data: {len(encoded_bytes)} bytes")
                
                elif self.config.protocol == "can" and "can" in self.transmitters:
                    # For CAN, we need a CAN ID (using RWA ID from specification)
                    can_id = 0x200  # RWA CAN ID
                    success = self.transmitters["can"].send_message(can_id, encoded_bytes, "reaction_wheel")
                    if success:
                        self.stats["rw_packets_sent"] += 1
                        logger.debug(f"Sent reaction wheel CAN message ID 0x{can_id:03X}: {len(encoded_bytes)} bytes")
                
                else:
                    # Simulation mode
                    logger.debug(f"Simulation: Reaction wheel data {len(data)} floats -> {len(encoded_bytes)} bytes")
                    self.stats["rw_packets_sent"] += 1
            
        except Exception as e:
            logger.error(f"Error processing reaction wheel data: {e}")
            self.stats["errors"] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get bridge status and statistics"""
        status = {
            "running": self.is_running,
            "protocol": self.config.protocol,
            "listening": f"{self.config.listen_ip}:{self.config.listen_port}",
            "transmitters": {},
            "statistics": self.stats.copy()
        }
        
        # Add transmitter status
        for name, transmitter in self.transmitters.items():
            status["transmitters"][name] = transmitter.get_status()
        
        return status

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MATLAB Orbital Simulator Bridge')
    parser.add_argument('--listen-ip', default='127.0.0.1', help='IP address to listen on')
    parser.add_argument('--listen-port', type=int, default=8888, help='Port to listen on')
    parser.add_argument('--protocol', choices=['tcp', 'can'], default='tcp', help='Output protocol')
    parser.add_argument('--tcp-target-ip', default='192.168.1.200', help='TCP target IP')
    parser.add_argument('--tcp-target-port', type=int, default=8000, help='TCP target port')
    parser.add_argument('--can-interface', default='socketcan', help='CAN interface')
    parser.add_argument('--can-channel', default='can0', help='CAN channel')
    parser.add_argument('--can-bitrate', type=int, default=500000, help='CAN bitrate')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create configuration
    config = BridgeConfig(
        listen_ip=args.listen_ip,
        listen_port=args.listen_port,
        protocol=args.protocol,
        device_configs={
            "tcp": {
                "target_ip": args.tcp_target_ip,
                "target_port": args.tcp_target_port
            },
            "can": {
                "interface": args.can_interface,
                "channel": args.can_channel,
                "bitrate": args.can_bitrate
            }
        }
    )
    
    # Create and start bridge
    bridge = DeviceBridge(config)
    
    try:
        print(f"Starting MATLAB Orbital Simulator Bridge...")
        print(f"Listening on: {config.listen_ip}:{config.listen_port}")
        print(f"Output protocol: {config.protocol}")
        print(f"Press Ctrl+C to stop")
        
        bridge.start()
        
    except KeyboardInterrupt:
        print("\nShutting down bridge...")
        bridge.stop()
        
        # Print final statistics
        status = bridge.get_status()
        print(f"\nFinal Statistics:")
        print(f"Messages received: {status['statistics']['messages_received']}")
        print(f"ARS packets sent: {status['statistics']['ars_packets_sent']}")
        print(f"Magnetometer packets sent: {status['statistics']['mag_packets_sent']}")
        print(f"Reaction wheel packets sent: {status['statistics']['rw_packets_sent']}")
        print(f"Errors: {status['statistics']['errors']}")

if __name__ == '__main__':
    main()


