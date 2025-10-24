#!/usr/bin/env python3
"""
Test suite for Honeywell Dual Space Magnetometer

This script provides comprehensive testing of the magnetometer communication library
based on the actual ICD specifications from the PDF documents.
"""

import unittest
import time
import threading
import struct
from unittest.mock import Mock, patch, MagicMock
from honeywell_magnetometer import (
    HoneywellMagnetometer, 
    MagnetometerReading, 
    MagnetometerStatus,
    MessageType,
    OperationMode,
    DeviceInfo,
    MemoryData,
    HoneywellMagnetometerError
)

def calculate_crc16(data: bytes) -> int:
    """
    Calculate CRC-16 checksum using the standard CRC-16-CCITT algorithm.
    This replaces the crcmod dependency with a pure Python implementation.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


class TestMagnetometerReading(unittest.TestCase):
    """Test MagnetometerReading class"""
    
    def test_reading_creation(self):
        """Test reading creation and basic properties"""
        reading = MagnetometerReading(
            timestamp=1234567890.0,
            x_field=100.0,
            y_field=200.0,
            z_field=300.0,
            temperature=25.0,
            status=MagnetometerStatus.NORMAL,
            message_type=MessageType.MAGDATA
        )
        
        self.assertEqual(reading.timestamp, 1234567890.0)
        self.assertEqual(reading.x_field, 100.0)
        self.assertEqual(reading.y_field, 200.0)
        self.assertEqual(reading.z_field, 300.0)
        self.assertEqual(reading.temperature, 25.0)
        self.assertEqual(reading.status, MagnetometerStatus.NORMAL)
        self.assertEqual(reading.message_type, MessageType.MAGDATA)
    
    def test_magnitude_calculation(self):
        """Test magnetic field magnitude calculation"""
        reading = MagnetometerReading(
            timestamp=0, x_field=3.0, y_field=4.0, z_field=0.0,
            temperature=0, status=MagnetometerStatus.NORMAL,
            message_type=MessageType.MAGDATA
        )
        
        # 3-4-5 triangle
        expected_magnitude = 5.0
        self.assertAlmostEqual(reading.magnitude(), expected_magnitude, places=6)
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        reading = MagnetometerReading(
            timestamp=1234567890.0,
            x_field=100.0,
            y_field=200.0,
            z_field=300.0,
            temperature=25.0,
            status=MagnetometerStatus.NORMAL,
            message_type=MessageType.MAGDATA
        )
        
        data_dict = reading.to_dict()
        
        self.assertIn('timestamp', data_dict)
        self.assertIn('x_field', data_dict)
        self.assertIn('y_field', data_dict)
        self.assertIn('z_field', data_dict)
        self.assertIn('temperature', data_dict)
        self.assertIn('status', data_dict)
        self.assertIn('message_type', data_dict)
        self.assertIn('magnitude', data_dict)
        
        self.assertEqual(data_dict['status'], 'NORMAL')
        self.assertEqual(data_dict['message_type'], 'MAGDATA')


class TestMessageValidation(unittest.TestCase):
    """Test message validation and CRC functionality"""
    
    def test_message_creation(self):
        """Test message creation with proper format"""
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        
        # Test message creation
        message = mag._create_message(0x01, b"test_data", MessageType.MAGDATA)
        
        # Check message structure: [Header][Command][Data][CRC]
        self.assertGreaterEqual(len(message), 7)  # Minimum message size
        
        # Verify header format
        message_type, command, sequence = struct.unpack('<BBH', message[:4])
        self.assertEqual(message_type, MessageType.MAGDATA.value)
        self.assertEqual(command, 0x01)
        self.assertEqual(sequence, 0)  # First message
    
    def test_message_validation(self):
        """Test message validation with CRC"""
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        
        # Create a valid message
        message = mag._create_message(0x01, b"test_data", MessageType.MAGDATA)
        
        # Validate the message
        self.assertTrue(mag._validate_message(message))
        
        # Test with corrupted message
        corrupted_message = message[:-1] + b'\x00'  # Corrupt CRC
        self.assertFalse(mag._validate_message(corrupted_message))


class TestHoneywellMagnetometer(unittest.TestCase):
    """Test HoneywellMagnetometer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mag = None
    
    def tearDown(self):
        """Clean up after tests"""
        if self.mag:
            self.mag.disconnect()
    
    @patch('honeywell_magnetometer.can')
    def test_can_initialization(self, mock_can):
        """Test CAN interface initialization"""
        mock_bus = Mock()
        mock_can.interface.Bus.return_value = mock_bus
        
        mag = HoneywellMagnetometer("CAN", channel="can0")
        
        self.assertEqual(mag.interface_type, "CAN")
        self.assertIsNotNone(mag.interface)
        self.assertIsNotNone(mag.crc_calculator)
        self.assertEqual(mag.sequence_counter, 0)
        mock_can.interface.Bus.assert_called_once()
    
    @patch('honeywell_magnetometer.serial')
    def test_rs485_initialization(self, mock_serial):
        """Test RS485 interface initialization"""
        mock_serial.Serial.return_value = Mock()
        
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        
        self.assertEqual(mag.interface_type, "RS485")
        self.assertIsNotNone(mag.interface)
        self.assertIsNotNone(mag.crc_calculator)
        self.assertEqual(mag.sequence_counter, 0)
        mock_serial.Serial.assert_called_once()
    
    def test_invalid_interface_type(self):
        """Test invalid interface type raises error"""
        with self.assertRaises(ValueError):
            HoneywellMagnetometer("INVALID")
    
    @patch('honeywell_magnetometer.can')
    def test_can_connect(self, mock_can):
        """Test CAN connection"""
        mock_bus = Mock()
        mock_can.interface.Bus.return_value = mock_bus
        
        mag = HoneywellMagnetometer("CAN", channel="can0")
        result = mag.connect()
        
        self.assertTrue(result)
        self.assertTrue(mag.is_connected)
        mock_bus.send.assert_called_once()
    
    @patch('honeywell_magnetometer.serial')
    def test_rs485_connect(self, mock_serial):
        """Test RS485 connection"""
        mock_serial_obj = Mock()
        mock_serial_obj.is_open = True
        mock_serial.Serial.return_value = mock_serial_obj
        
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        result = mag.connect()
        
        self.assertTrue(result)
        self.assertTrue(mag.is_connected)
    
    def test_calibration_application(self):
        """Test calibration matrix application"""
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        
        # Set test calibration parameters
        mag.calibration_matrix = [[2.0, 0.0, 0.0],
                                 [0.0, 2.0, 0.0],
                                 [0.0, 0.0, 2.0]]
        mag.offset = [10.0, 20.0, 30.0]
        mag.scale_factors = [1.5, 1.5, 1.5]
        
        # Test calibration
        x_cal, y_cal, z_cal = mag._apply_calibration(1.0, 2.0, 3.0)
        
        # Expected: (1.0 * 1.5 * 2.0) + 10.0 = 13.0
        self.assertAlmostEqual(x_cal, 13.0, places=6)
        # Expected: (2.0 * 1.5 * 2.0) + 20.0 = 26.0
        self.assertAlmostEqual(y_cal, 26.0, places=6)
        # Expected: (3.0 * 1.5 * 2.0) + 30.0 = 39.0
        self.assertAlmostEqual(z_cal, 39.0, places=6)
    
    def test_calibration_with_readings(self):
        """Test calibration with sample readings"""
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        
        # Create test readings
        readings = []
        for i in range(20):
            reading = MagnetometerReading(
                timestamp=time.time(),
                x_field=100.0 + i,
                y_field=200.0 + i,
                z_field=300.0 + i,
                temperature=25.0,
                status=MagnetometerStatus.NORMAL,
                message_type=MessageType.MAGDATA
            )
            readings.append(reading)
        
        # Perform calibration
        result = mag.calibrate(readings)
        
        self.assertTrue(result)
        self.assertIsNotNone(mag.offset)
        self.assertIsNotNone(mag.scale_factors)


class TestMessageParsing(unittest.TestCase):
    """Test message parsing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
    
    def test_parse_magdata_message(self):
        """Test parsing MAGDATA message"""
        # Create a valid MAGDATA message
        x_field = 100.0
        y_field = 200.0
        z_field = 300.0
        temperature = 25.0
        status = MagnetometerStatus.NORMAL.value
        
        # Pack data as it would come from the device
        data = struct.pack('<f', x_field) + struct.pack('<f', y_field) + \
               struct.pack('<f', z_field) + struct.pack('<f', temperature) + \
               struct.pack('<B', status)
        
        # Create full message with header and CRC
        header = struct.pack('<BBH', MessageType.MAGDATA.value, 0x01, 0)
        message_data = header + b'\x01' + data
        crc = self.mag.crc_calculator(message_data)
        crc_bytes = struct.pack('<H', crc)
        full_message = message_data + crc_bytes
        
        # Parse the message
        reading = self.mag._parse_data_message(full_message)
        
        self.assertIsNotNone(reading)
        self.assertEqual(reading.message_type, MessageType.MAGDATA)
        self.assertAlmostEqual(reading.x_field, x_field, places=6)
        self.assertAlmostEqual(reading.y_field, y_field, places=6)
        self.assertAlmostEqual(reading.z_field, z_field, places=6)
        self.assertAlmostEqual(reading.temperature, temperature, places=6)
        self.assertEqual(reading.status, MagnetometerStatus.NORMAL)
    
    def test_parse_magtemp_message(self):
        """Test parsing MAGTEMP message"""
        # Create a valid MAGTEMP message
        temperature = 25.0
        status = MagnetometerStatus.NORMAL.value
        
        # Pack data as it would come from the device
        data = struct.pack('<f', temperature) + struct.pack('<B', status)
        
        # Create full message with header and CRC
        header = struct.pack('<BBH', MessageType.MAGTEMP.value, 0x02, 0)
        message_data = header + b'\x02' + data
        crc = self.mag.crc_calculator(message_data)
        crc_bytes = struct.pack('<H', crc)
        full_message = message_data + crc_bytes
        
        # Parse the message
        reading = self.mag._parse_data_message(full_message)
        
        self.assertIsNotNone(reading)
        self.assertEqual(reading.message_type, MessageType.MAGTEMP)
        self.assertAlmostEqual(reading.temperature, temperature, places=6)
        self.assertEqual(reading.status, MagnetometerStatus.NORMAL)


class TestDeviceInfo(unittest.TestCase):
    """Test DeviceInfo functionality"""
    
    def test_device_info_creation(self):
        """Test DeviceInfo creation"""
        device_info = DeviceInfo(
            device_id=12345,
            firmware_version="1.0.0",
            serial_number="SN123456",
            calibration_date="2024-01-01",
            status=MagnetometerStatus.NORMAL
        )
        
        self.assertEqual(device_info.device_id, 12345)
        self.assertEqual(device_info.firmware_version, "1.0.0")
        self.assertEqual(device_info.serial_number, "SN123456")
        self.assertEqual(device_info.calibration_date, "2024-01-01")
        self.assertEqual(device_info.status, MagnetometerStatus.NORMAL)


class TestMemoryData(unittest.TestCase):
    """Test MemoryData functionality"""
    
    def test_memory_data_creation(self):
        """Test MemoryData creation"""
        test_data = b"test_data_12345"
        memory_data = MemoryData(
            address=0x2000,
            data=test_data,
            length=len(test_data),
            checksum=0x1234
        )
        
        self.assertEqual(memory_data.address, 0x2000)
        self.assertEqual(memory_data.data, test_data)
        self.assertEqual(memory_data.length, len(test_data))
        self.assertEqual(memory_data.checksum, 0x1234)


class TestMagnetometerIntegration(unittest.TestCase):
    """Integration tests for magnetometer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mag = None
    
    def tearDown(self):
        """Clean up after tests"""
        if self.mag:
            self.mag.disconnect()
    
    @patch('honeywell_magnetometer.serial')
    def test_full_workflow(self, mock_serial):
        """Test complete workflow from connection to data reading"""
        # Mock serial interface
        mock_serial_obj = Mock()
        mock_serial_obj.is_open = True
        
        # Create a valid MAGDATA response
        x_field = 100.0
        y_field = 200.0
        z_field = 300.0
        temperature = 25.0
        status = MagnetometerStatus.NORMAL.value
        
        data = struct.pack('<f', x_field) + struct.pack('<f', y_field) + \
               struct.pack('<f', z_field) + struct.pack('<f', temperature) + \
               struct.pack('<B', status)
        
        header = struct.pack('<BBH', MessageType.MAGDATA.value, 0x01, 0)
        message_data = header + b'\x01' + data
        
        # Calculate CRC
        crc = calculate_crc16(message_data)
        crc_bytes = struct.pack('<H', crc)
        full_message = message_data + crc_bytes
        
        mock_serial_obj.read.return_value = full_message
        mock_serial.Serial.return_value = mock_serial_obj
        
        # Create magnetometer
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        
        # Connect
        self.assertTrue(mag.connect())
        
        # Read data
        reading = mag.read_data()
        self.assertIsNotNone(reading)
        self.assertIsInstance(reading, MagnetometerReading)
        self.assertEqual(reading.message_type, MessageType.MAGDATA)
        
        # Disconnect
        mag.disconnect()
        self.assertFalse(mag.is_connected)
    
    @patch('honeywell_magnetometer.serial')
    def test_continuous_reading(self, mock_serial):
        """Test continuous reading functionality"""
        # Mock serial interface
        mock_serial_obj = Mock()
        mock_serial_obj.is_open = True
        
        # Create a valid MAGDATA response
        x_field = 100.0
        y_field = 200.0
        z_field = 300.0
        temperature = 25.0
        status = MagnetometerStatus.NORMAL.value
        
        data = struct.pack('<f', x_field) + struct.pack('<f', y_field) + \
               struct.pack('<f', z_field) + struct.pack('<f', temperature) + \
               struct.pack('<B', status)
        
        header = struct.pack('<BBH', MessageType.MAGDATA.value, 0x01, 0)
        message_data = header + b'\x01' + data
        
        # Calculate CRC
        crc = calculate_crc16(message_data)
        crc_bytes = struct.pack('<H', crc)
        full_message = message_data + crc_bytes
        
        mock_serial_obj.read.return_value = full_message
        mock_serial.Serial.return_value = mock_serial_obj
        
        # Create magnetometer
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        
        try:
            # Connect
            self.assertTrue(mag.connect())
            
            # Start continuous reading
            mag.start_continuous_reading(interval=0.1)
            
            # Wait for some readings
            time.sleep(0.5)
            
            # Stop continuous reading
            mag.stop_continuous_reading()
            
            # Check if readings were collected
            readings = mag.get_all_readings()
            self.assertGreater(len(readings), 0)
            
        finally:
            mag.disconnect()


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def test_connection_error(self):
        """Test connection error handling"""
        with patch('honeywell_magnetometer.serial') as mock_serial:
            mock_serial.Serial.side_effect = Exception("Connection failed")
            
            with self.assertRaises(HoneywellMagnetometerError):
                HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
    
    def test_read_data_when_not_connected(self):
        """Test reading data when not connected"""
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        
        with self.assertRaises(HoneywellMagnetometerError):
            mag.read_data()
    
    def test_send_command_when_not_connected(self):
        """Test sending command when not connected"""
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        
        with self.assertRaises(HoneywellMagnetometerError):
            mag.send_command(0x01)
    
    def test_invalid_message_parsing(self):
        """Test parsing invalid messages"""
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        
        # Test with too short message
        with self.assertRaises(HoneywellMagnetometerError):
            mag._parse_data_message(b"short")
        
        # Test with invalid message type
        invalid_message = struct.pack('<BBH', 0xFF, 0x01, 0) + b'\x01' + b"data" + b'\x00\x00'
        with self.assertRaises(HoneywellMagnetometerError):
            mag._parse_data_message(invalid_message)


def run_performance_test():
    """Run performance test (not part of unittest)"""
    print("Running performance test...")
    
    # This would be run separately as it requires actual hardware
    # or more sophisticated mocking
    pass


if __name__ == "__main__":
    # Run unit tests
    unittest.main(verbosity=2)
    
    # Run performance test if needed
    # run_performance_test()