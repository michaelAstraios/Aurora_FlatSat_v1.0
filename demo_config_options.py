#!/usr/bin/env python3
"""
Configuration Options Demo

Demonstrates the two configuration options:
1. USB Loopback Testing (for development)
2. Packet Logging (for production with real devices)
"""

import json
import time
import logging
from packet_logger import PacketLogger
from usb_loopback_tester import USBLoopbackTester, USBPortConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def demo_packet_logging():
    """Demonstrate packet logging functionality"""
    logger.info("=== Packet Logging Demo ===")
    
    # Create packet logger
    packet_logger = PacketLogger("demo_logs")
    
    # Setup logging for test devices
    devices = {
        'ars': 'ars_demo.log',
        'magnetometer': 'mag_demo.log',
        'reaction_wheel': 'rw_demo.log'
    }
    
    for device, log_file in devices.items():
        packet_logger.setup_device_logging(device, log_file)
    
    # Generate test packets
    test_packets = {
        'ars': bytes([0x55, 0x55, 0x00, 0x01] + [i % 256 for i in range(50)]),
        'magnetometer': bytes([0x01] + [i % 256 for i in range(30)]),
        'reaction_wheel': bytes([0x15] + [i % 256 for i in range(40)])
    }
    
    # Log packets
    for device, packet in test_packets.items():
        packet_logger.log_packet(device, packet)
        logger.info(f"Logged {len(packet)} bytes for {device}")
    
    # Show summary
    summary = packet_logger.get_log_summary()
    logger.info("Log Summary:")
    for device, info in summary.items():
        logger.info(f"  {device}: {info['size_bytes']} bytes, Active: {info['active']}")
    
    packet_logger.close_all_logging()
    logger.info("Packet logging demo complete")

def demo_usb_loopback():
    """Demonstrate USB loopback testing"""
    logger.info("=== USB Loopback Demo ===")
    
    # Configure USB ports
    device_configs = {
        'ars': USBPortConfig(port='/dev/ttyUSB0', baud_rate=115200),
        'magnetometer': USBPortConfig(port='/dev/ttyUSB1', baud_rate=115200),
        'reaction_wheel': USBPortConfig(port='/dev/ttyUSB2', baud_rate=115200)
    }
    
    # Create test packets
    test_packets = {
        'ars': bytes([0x55, 0x55, 0x00, 0x01] + [i % 256 for i in range(50)]),
        'magnetometer': bytes([0x01] + [i % 256 for i in range(30)]),
        'reaction_wheel': bytes([0x15] + [i % 256 for i in range(40)])
    }
    
    # Create USB loopback tester
    tester = USBLoopbackTester(device_configs)
    
    if tester.start_testing():
        try:
            logger.info("Testing USB loopback (requires loopback cables)")
            results = tester.test_all_devices(test_packets)
            
            logger.info("Loopback Test Results:")
            for device, result in results.items():
                status = "PASS" if result.success else "FAIL"
                logger.info(f"  {device}: {status} - {result.latency_ms:.2f}ms")
            
        finally:
            tester.stop_testing()
    else:
        logger.warning("USB loopback testing not available (no loopback cables)")

def main():
    """Main demo function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Configuration Options Demo')
    parser.add_argument('--demo', choices=['logging', 'loopback', 'both'], 
                       default='both', help='Which demo to run')
    
    args = parser.parse_args()
    
    logger.info("FlatSat Device Simulator - Configuration Options Demo")
    logger.info("This demo shows the two configuration options:")
    logger.info("1. USB Loopback Testing (for development)")
    logger.info("2. Packet Logging (for production)")
    
    if args.demo in ['logging', 'both']:
        demo_packet_logging()
    
    if args.demo in ['loopback', 'both']:
        demo_usb_loopback()
    
    logger.info("Demo complete!")
    logger.info("")
    logger.info("Configuration Options:")
    logger.info("  Development (with loopback cables):")
    logger.info("    usb_loopback_enabled: true")
    logger.info("    log_packets_to_file: false")
    logger.info("")
    logger.info("  Production (with real devices):")
    logger.info("    usb_loopback_enabled: false")
    logger.info("    log_packets_to_file: true")

if __name__ == '__main__':
    main()
