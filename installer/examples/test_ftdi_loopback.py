#!/usr/bin/env python3
"""
FTDI USB Loopback Test Demo

Demonstrates USB loopback testing for RS232 FTDI devices.
Optimized for FTDI USB-to-serial converters commonly used in loopback testing.
"""

import time
import logging
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ftdi_usb_loopback_tester import FTDIUSBLoopbackTester, FTDIUSBPortConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_packets():
    """Create test packets for each device optimized for FTDI testing"""
    
    # ARS test packet (Honeywell format) - optimized for FTDI
    ars_packet = bytes([
        0xAA,  # Sync byte (Rate Sensor address)
        0x00, 0x01,  # Angular rate X (2 bytes, little-endian)
        0x00, 0x02,  # Angular rate Y
        0x00, 0x03,  # Angular rate Z
        0x00, 0x04,  # Status Word 1
        0x00, 0x05,  # Status Word 2
        0x00, 0x06,  # Status Word 3
        0x00, 0x00, 0x00, 0x01,  # Summed angle X (4 bytes)
        0x00, 0x00, 0x00, 0x02,  # Summed angle Y
        0x00, 0x00, 0x00, 0x03,  # Summed angle Z
        0x00, 0x00   # CRC-16
    ])
    
    # Magnetometer test packet (CAN format) - optimized for FTDI
    mag_packet = bytes([
        0x01,  # Message type (MAGDATA)
        0x00, 0x00, 0x00, 0x00,  # X field (32-bit float)
        0x00, 0x00, 0x00, 0x00,  # Y field
        0x00, 0x00, 0x00, 0x00,  # Z field
        0x00, 0x00, 0x00, 0x00,  # Temperature
        0x00, 0x00, 0x00, 0x00,  # Timestamp
        0x00, 0x00, 0x00, 0x00   # CRC
    ])
    
    # Reaction Wheel test packet (TCP format) - optimized for FTDI
    rw_packet = bytes([
        0x15,  # Telemetry type (HEALTH_STATUS)
        0x00, 0x00, 0x00, 0x00,  # Wheel speed (32-bit float)
        0x00, 0x00, 0x00, 0x00,  # Motor current
        0x00, 0x00, 0x00, 0x00,  # Temperature
        0x00, 0x00, 0x00, 0x00,  # Bus voltage
        0x00, 0x00, 0x00, 0x00,  # Power consumption
        0x00, 0x00, 0x00, 0x00,  # Timestamp
        0x00, 0x00, 0x00, 0x00   # CRC
    ])
    
    return {
        'ars': ars_packet,
        'magnetometer': mag_packet,
        'reaction_wheel': rw_packet
    }

def main():
    """Main FTDI test function"""
    
    # Configure FTDI USB ports for each device
    device_configs = {
        'ars': FTDIUSBPortConfig(
            port='/dev/ttyUSB0', 
            baud_rate=115200,
            rtscts=False,  # No hardware flow control
            dsrdtr=False,  # No DSR/DTR flow control
            xonxoff=False  # No software flow control
        ),
        'magnetometer': FTDIUSBPortConfig(
            port='/dev/ttyUSB1', 
            baud_rate=115200,
            rtscts=False,
            dsrdtr=False,
            xonxoff=False
        ),
        'reaction_wheel': FTDIUSBPortConfig(
            port='/dev/ttyUSB2', 
            baud_rate=115200,
            rtscts=False,
            dsrdtr=False,
            xonxoff=False
        )
    }
    
    # Create test packets
    test_packets = create_test_packets()
    
    # Create FTDI USB loopback tester
    tester = FTDIUSBLoopbackTester(device_configs)
    
    logger.info("Starting FTDI USB Loopback Test Demo")
    logger.info("Make sure FTDI USB loopback cables are connected:")
    logger.info("  ARS: /dev/ttyUSB0 -> loopback")
    logger.info("  Magnetometer: /dev/ttyUSB1 -> loopback")
    logger.info("  Reaction Wheel: /dev/ttyUSB2 -> loopback")
    logger.info("")
    logger.info("FTDI Configuration:")
    logger.info("  Baud Rate: 115200")
    logger.info("  Data Bits: 8")
    logger.info("  Stop Bits: 1")
    logger.info("  Parity: None")
    logger.info("  Flow Control: None")
    
    if tester.start_testing():
        try:
            # Test each device
            logger.info("Testing all devices with FTDI loopback...")
            results = tester.test_all_devices(test_packets)
            
            # Print results
            logger.info("=== FTDI Test Results ===")
            for device_name, result in results.items():
                status = "PASS" if result.success else "FAIL"
                logger.info(f"{device_name.upper()}: {status}")
                logger.info(f"  Sent:    {result.sent_bytes.hex().upper()}")
                logger.info(f"  Received: {result.received_bytes.hex().upper()}")
                logger.info(f"  Latency:  {result.latency_ms:.2f}ms")
                
                if result.port_info:
                    logger.info(f"  Port: {result.port_info['port']} @ {result.port_info['baudrate']} baud")
                    logger.info(f"  Flow Control: RTS/CTS={result.port_info['rtscts']}, DSR/DTR={result.port_info['dsrdtr']}")
                
                logger.info("")
            
            # Print summary
            tester.print_test_summary()
            
        finally:
            tester.stop_testing()
    else:
        logger.error("Failed to start FTDI USB Loopback Test System")
        logger.error("Make sure FTDI USB ports are available and loopback cables are connected")
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("1. Check that FTDI devices are connected: ls /dev/ttyUSB*")
        logger.error("2. Verify loopback cables are properly connected")
        logger.error("3. Check permissions: sudo usermod -a -G dialout $USER")
        logger.error("4. Try different baud rates if needed")

if __name__ == '__main__':
    main()



