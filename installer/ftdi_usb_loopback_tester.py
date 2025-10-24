#!/usr/bin/env python3
"""
Enhanced USB Loopback Test System for FTDI RS232 Devices

Optimized for RS232 FTDI USB-to-serial converters commonly used in loopback testing.
Includes FTDI-specific configurations and improved error handling.
"""

import serial
import threading
import time
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from queue import Queue, Empty
import struct
import os

logger = logging.getLogger(__name__)

@dataclass
class FTDIUSBPortConfig:
    """Enhanced configuration for FTDI USB ports"""
    port: str
    baud_rate: int = 115200
    data_bits: int = 8
    stop_bits: int = 1
    parity: str = "N"
    timeout: float = 1.0
    # FTDI-specific settings
    rtscts: bool = False  # Hardware flow control
    dsrdtr: bool = False  # DSR/DTR flow control
    xonxoff: bool = False  # Software flow control
    write_timeout: float = 1.0
    inter_byte_timeout: float = 0.1

@dataclass
class LoopbackTestResult:
    """Result of loopback test"""
    device_name: str
    sent_bytes: bytes
    received_bytes: bytes
    timestamp: float
    success: bool
    latency_ms: float
    port_info: Optional[Dict] = None

class FTDIUSBLoopbackMonitor:
    """Enhanced monitor for FTDI USB loopback ports"""
    
    def __init__(self, port_configs: Dict[str, FTDIUSBPortConfig]):
        self.port_configs = port_configs
        self.monitors: Dict[str, serial.Serial] = {}
        self.data_queues: Dict[str, Queue] = {}
        self.monitor_threads: Dict[str, threading.Thread] = {}
        self.running = False
        
        # Initialize queues
        for device_name in port_configs.keys():
            self.data_queues[device_name] = Queue()
    
    def _detect_ftdi_ports(self) -> Dict[str, str]:
        """Detect available FTDI USB ports"""
        ftdi_ports = {}
        
        # Common FTDI port patterns
        port_patterns = [
            "/dev/ttyUSB*",
            "/dev/tty.usbserial*",  # macOS
            "/dev/tty.usbmodem*",    # macOS
            "COM*"                  # Windows
        ]
        
        # Check for existing ports
        for device_name, config in self.port_configs.items():
            if os.path.exists(config.port):
                ftdi_ports[device_name] = config.port
                logger.info(f"Found FTDI port for {device_name}: {config.port}")
            else:
                logger.warning(f"FTDI port not found for {device_name}: {config.port}")
        
        return ftdi_ports
    
    def _configure_ftdi_port(self, port: serial.Serial, config: FTDIUSBPortConfig):
        """Configure FTDI-specific port settings"""
        try:
            # Set FTDI-specific parameters
            port.rtscts = config.rtscts
            port.dsrdtr = config.dsrdtr
            port.xonxoff = config.xonxoff
            port.write_timeout = config.write_timeout
            port.inter_byte_timeout = config.inter_byte_timeout
            
            # Reset FTDI device buffers
            port.reset_input_buffer()
            port.reset_output_buffer()
            
            # Set DTR/RTS for proper FTDI initialization
            port.dtr = True
            port.rts = True
            time.sleep(0.1)  # Allow time for FTDI initialization
            
            logger.debug(f"Configured FTDI port {port.port} with flow control: RTS/CTS={config.rtscts}, DSR/DTR={config.dsrdtr}")
            
        except Exception as e:
            logger.warning(f"Could not configure FTDI-specific settings: {e}")
    
    def start_monitoring(self) -> bool:
        """Start monitoring all FTDI USB ports"""
        try:
            # Detect available ports
            available_ports = self._detect_ftdi_ports()
            
            for device_name, config in self.port_configs.items():
                if device_name not in available_ports:
                    logger.error(f"FTDI port not available for {device_name}: {config.port}")
                    continue
                
                try:
                    # Open serial port for monitoring
                    monitor_port = serial.Serial(
                        port=config.port,
                        baudrate=config.baud_rate,
                        bytesize=config.data_bits,
                        stopbits=config.stop_bits,
                        parity=config.parity,
                        timeout=config.timeout
                    )
                    
                    # Configure FTDI-specific settings
                    self._configure_ftdi_port(monitor_port, config)
                    
                    self.monitors[device_name] = monitor_port
                    
                    # Start monitoring thread
                    thread = threading.Thread(
                        target=self._monitor_port,
                        args=(device_name, monitor_port),
                        daemon=True
                    )
                    thread.start()
                    self.monitor_threads[device_name] = thread
                    
                    logger.info(f"Started monitoring FTDI port {config.port} for {device_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to open FTDI port {config.port} for {device_name}: {e}")
                    continue
            
            if self.monitors:
                self.running = True
                logger.info(f"Started monitoring {len(self.monitors)} FTDI ports")
                return True
            else:
                logger.error("No FTDI ports could be opened")
                return False
            
        except Exception as e:
            logger.error(f"Failed to start FTDI monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop monitoring all FTDI USB ports"""
        self.running = False
        
        # Close all monitor ports
        for device_name, monitor in self.monitors.items():
            try:
                # Reset DTR/RTS before closing
                monitor.dtr = False
                monitor.rts = False
                monitor.close()
                logger.info(f"Stopped monitoring FTDI port for {device_name}")
            except:
                pass
        
        # Wait for threads to finish
        for device_name, thread in self.monitor_threads.items():
            thread.join(timeout=2.0)
    
    def _monitor_port(self, device_name: str, monitor_port: serial.Serial):
        """Monitor a single FTDI USB port for incoming data"""
        logger.info(f"Monitoring FTDI port {monitor_port.port} for {device_name}")
        
        while self.running:
            try:
                # Read available data
                if monitor_port.in_waiting > 0:
                    data = monitor_port.read(monitor_port.in_waiting)
                    if data:
                        # Put data in queue with timestamp
                        self.data_queues[device_name].put((data, time.time()))
                        logger.debug(f"{device_name}: Received {len(data)} bytes: {data.hex().upper()}")
                
                time.sleep(0.001)  # Small delay to prevent busy waiting
                
            except Exception as e:
                logger.error(f"Error monitoring {device_name} FTDI port: {e}")
                time.sleep(0.1)
    
    def get_received_data(self, device_name: str, timeout: float = 1.0) -> Optional[bytes]:
        """Get received data for a specific device"""
        try:
            data, timestamp = self.data_queues[device_name].get(timeout=timeout)
            return data
        except Empty:
            return None
    
    def get_port_info(self, device_name: str) -> Optional[Dict]:
        """Get FTDI port information"""
        if device_name in self.monitors:
            port = self.monitors[device_name]
            return {
                "port": port.port,
                "baudrate": port.baudrate,
                "bytesize": port.bytesize,
                "stopbits": port.stopbits,
                "parity": port.parity,
                "rtscts": port.rtscts,
                "dsrdtr": port.dsrdtr,
                "xonxoff": port.xonxoff,
                "is_open": port.is_open
            }
        return None

class FTDIUSBLoopbackTester:
    """Enhanced USB loopback test system for FTDI devices"""
    
    def __init__(self, device_configs: Dict[str, FTDIUSBPortConfig]):
        self.device_configs = device_configs
        self.monitor = FTDIUSBLoopbackMonitor(device_configs)
        self.test_results: List[LoopbackTestResult] = []
        
    def start_testing(self) -> bool:
        """Start the FTDI loopback test system"""
        logger.info("Starting FTDI USB Loopback Test System")
        
        if self.monitor.start_monitoring():
            logger.info("FTDI USB Loopback Test System started successfully")
            return True
        else:
            logger.error("Failed to start FTDI USB Loopback Test System")
            return False
    
    def stop_testing(self):
        """Stop the FTDI loopback test system"""
        logger.info("Stopping FTDI USB Loopback Test System")
        self.monitor.stop_monitoring()
    
    def test_device_packet(self, device_name: str, packet_data: bytes) -> LoopbackTestResult:
        """
        Test a device packet using FTDI loopback
        
        Args:
            device_name: Name of the device (ars, magnetometer, reaction_wheel)
            packet_data: Packet data to send
            
        Returns:
            LoopbackTestResult with test results
        """
        if device_name not in self.device_configs:
            logger.error(f"Unknown device: {device_name}")
            return LoopbackTestResult(
                device_name=device_name,
                sent_bytes=packet_data,
                received_bytes=b"",
                timestamp=time.time(),
                success=False,
                latency_ms=0.0
            )
        
        config = self.device_configs[device_name]
        start_time = time.time()
        
        try:
            # Send packet to FTDI USB port
            with serial.Serial(
                port=config.port,
                baudrate=config.baud_rate,
                bytesize=config.data_bits,
                stopbits=config.stop_bits,
                parity=config.parity,
                timeout=config.timeout,
                write_timeout=config.write_timeout
            ) as sender_port:
                
                # Configure FTDI-specific settings
                self.monitor._configure_ftdi_port(sender_port, config)
                
                # Send data
                sender_port.write(packet_data)
                sender_port.flush()
                
                logger.info(f"Sent {len(packet_data)} bytes to {device_name} FTDI port {config.port}")
                logger.info(f"Sent data: {packet_data.hex().upper()}")
                
                # Wait for loopback data
                time.sleep(0.1)  # Allow time for FTDI loopback
                
                # Get received data
                received_data = self.monitor.get_received_data(device_name, timeout=2.0)
                
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                # Get port info
                port_info = self.monitor.get_port_info(device_name)
                
                if received_data:
                    logger.info(f"Received {len(received_data)} bytes from {device_name}")
                    logger.info(f"Received data: {received_data.hex().upper()}")
                    
                    # Check if received data matches sent data
                    success = received_data == packet_data
                    
                    result = LoopbackTestResult(
                        device_name=device_name,
                        sent_bytes=packet_data,
                        received_bytes=received_data,
                        timestamp=start_time,
                        success=success,
                        latency_ms=latency_ms,
                        port_info=port_info
                    )
                    
                    self.test_results.append(result)
                    return result
                else:
                    logger.warning(f"No data received from {device_name} FTDI loopback")
                    return LoopbackTestResult(
                        device_name=device_name,
                        sent_bytes=packet_data,
                        received_bytes=b"",
                        timestamp=start_time,
                        success=False,
                        latency_ms=latency_ms,
                        port_info=port_info
                    )
                    
        except Exception as e:
            logger.error(f"Error testing {device_name} FTDI port: {e}")
            return LoopbackTestResult(
                device_name=device_name,
                sent_bytes=packet_data,
                received_bytes=b"",
                timestamp=time.time(),
                success=False,
                latency_ms=0.0
            )
    
    def test_all_devices(self, device_packets: Dict[str, bytes]) -> Dict[str, LoopbackTestResult]:
        """Test all devices with their respective packets"""
        results = {}
        
        for device_name, packet_data in device_packets.items():
            logger.info(f"Testing {device_name} with {len(packet_data)} bytes")
            result = self.test_device_packet(device_name, packet_data)
            results[device_name] = result
            
            # Small delay between tests
            time.sleep(0.5)
        
        return results
    
    def print_test_summary(self):
        """Print summary of all FTDI test results"""
        logger.info("=== FTDI USB Loopback Test Summary ===")
        
        for result in self.test_results:
            status = "PASS" if result.success else "FAIL"
            logger.info(f"{result.device_name}: {status} - "
                       f"Sent: {len(result.sent_bytes)} bytes, "
                       f"Received: {len(result.received_bytes)} bytes, "
                       f"Latency: {result.latency_ms:.2f}ms")
            
            if result.port_info:
                logger.info(f"  Port: {result.port_info['port']} @ {result.port_info['baudrate']} baud")
                logger.info(f"  Flow Control: RTS/CTS={result.port_info['rtscts']}, DSR/DTR={result.port_info['dsrdtr']}")
            
            if result.sent_bytes:
                logger.info(f"  Sent:    {result.sent_bytes.hex().upper()}")
            if result.received_bytes:
                logger.info(f"  Received: {result.received_bytes.hex().upper()}")
            
            if not result.success and result.sent_bytes and result.received_bytes:
                logger.warning(f"  Data mismatch detected!")

def main():
    """Test FTDI USB loopback system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FTDI USB Loopback Test System')
    parser.add_argument('--ars-port', default='/dev/ttyUSB0', help='ARS FTDI USB port')
    parser.add_argument('--mag-port', default='/dev/ttyUSB1', help='Magnetometer FTDI USB port')
    parser.add_argument('--rw-port', default='/dev/ttyUSB2', help='Reaction Wheel FTDI USB port')
    parser.add_argument('--baud-rate', type=int, default=115200, help='Baud rate')
    parser.add_argument('--test-duration', type=float, default=30.0, help='Test duration in seconds')
    parser.add_argument('--flow-control', choices=['none', 'rtscts', 'dsrdtr', 'xonxoff'], 
                       default='none', help='Flow control type')
    
    args = parser.parse_args()
    
    # Configure FTDI USB ports for each device
    flow_control_map = {
        'none': {'rtscts': False, 'dsrdtr': False, 'xonxoff': False},
        'rtscts': {'rtscts': True, 'dsrdtr': False, 'xonxoff': False},
        'dsrdtr': {'rtscts': False, 'dsrdtr': True, 'xonxoff': False},
        'xonxoff': {'rtscts': False, 'dsrdtr': False, 'xonxoff': True}
    }
    
    fc_settings = flow_control_map[args.flow_control]
    
    device_configs = {
        'ars': FTDIUSBPortConfig(
            port=args.ars_port, 
            baud_rate=args.baud_rate,
            **fc_settings
        ),
        'magnetometer': FTDIUSBPortConfig(
            port=args.mag_port, 
            baud_rate=args.baud_rate,
            **fc_settings
        ),
        'reaction_wheel': FTDIUSBPortConfig(
            port=args.rw_port, 
            baud_rate=args.baud_rate,
            **fc_settings
        )
    }
    
    # Create test system
    tester = FTDIUSBLoopbackTester(device_configs)
    
    if tester.start_testing():
        try:
            logger.info(f"FTDI USB Loopback Test running for {args.test_duration} seconds")
            logger.info(f"Flow Control: {args.flow_control}")
            logger.info("Send test packets to the configured FTDI USB ports")
            
            # Run test for specified duration
            start_time = time.time()
            while time.time() - start_time < args.test_duration:
                time.sleep(1.0)
            
            # Print summary
            tester.print_test_summary()
            
        finally:
            tester.stop_testing()
    else:
        logger.error("Failed to start FTDI USB Loopback Test System")

if __name__ == '__main__':
    main()



