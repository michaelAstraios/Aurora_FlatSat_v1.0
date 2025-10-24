#!/usr/bin/env python3
"""
Comprehensive Test Suite for Device Simulator

Tests all components of the device simulator including:
- Device encoders
- Output transmitters
- TCP receiver
- Error handling
- Performance monitoring
- USB loopback testing
- Packet logging
"""

import unittest
import time
import threading
import tempfile
import os
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Import all components to test
from device_encoders.ars_encoder import ARSEncoder
from device_encoders.magnetometer_encoder import MagnetometerEncoder
from device_encoders.reaction_wheel_encoder import ReactionWheelEncoder
from device_encoders.ars_status_manager import ARSStatusManager
from device_encoders.magnetometer_status_manager import MagnetometerStatusManager
from device_encoders.reaction_wheel_status_manager import RWAStatusManager

from output_transmitters.serial_transmitter import SerialTransmitter, SerialConfig
from output_transmitters.can_transmitter import CANTransmitter, CANConfig
from output_transmitters.tcp_transmitter import TCPTransmitter, TCPConfig

from tcp_receiver import TCPReceiver, TCPConfig as TCPReceiverConfig
from packet_logger import PacketLogger
from usb_loopback_tester import USBLoopbackTester, USBPortConfig
from error_handler import ErrorHandler, ErrorType, ErrorSeverity
from performance_monitor import PerformanceMonitor

from flatsat_device_simulator import FlatSatDeviceSimulator, DeviceConfig, SimulatorConfig

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests

class TestARSEncoder(unittest.TestCase):
    """Test ARS encoder functionality"""
    
    def setUp(self):
        self.encoder = ARSEncoder(duplicate_to_redundant=True, variation_percent=0.1)
    
    def test_primary_data_conversion(self):
        """Test conversion of primary-only MATLAB data"""
        matlab_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]  # 6 floats
        packet = self.encoder.convert_matlab_data(matlab_data)
        
        self.assertIsNotNone(packet)
        # Convert packet to bytes to test encoding
        encoded_data = self.encoder.encode_packet(packet)
        self.assertGreater(len(encoded_data), 0)  # Should have some data
    
    def test_full_data_conversion(self):
        """Test conversion of full MATLAB data with redundant channels"""
        matlab_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]  # 12 floats
        packet = self.encoder.convert_matlab_data(matlab_data)
        
        self.assertIsNotNone(packet)
        # Convert packet to bytes to test encoding
        encoded_data = self.encoder.encode_packet(packet)
        self.assertGreater(len(encoded_data), 0)  # Should have some data
    
    def test_invalid_data_handling(self):
        """Test handling of invalid data"""
        invalid_data = [1.0, 2.0]  # Too few floats
        packet = self.encoder.convert_matlab_data(invalid_data)
        
        self.assertIsNone(packet)

class TestMagnetometerEncoder(unittest.TestCase):
    """Test Magnetometer encoder functionality"""
    
    def setUp(self):
        self.encoder = MagnetometerEncoder()
    
    def test_can_encoding(self):
        """Test CAN message encoding"""
        matlab_data = [100.0, 200.0, 300.0]  # X, Y, Z magnetic field
        result = self.encoder.process_matlab_data_can(matlab_data)
        
        self.assertIsNotNone(result)
        can_id, data = result
        self.assertIsInstance(can_id, int)
        self.assertIsInstance(data, bytes)
    
    def test_rs485_encoding(self):
        """Test RS485 message encoding"""
        matlab_data = [100.0, 200.0, 300.0]
        packet = self.encoder.process_matlab_data_rs485(matlab_data)
        
        self.assertIsNotNone(packet)
        self.assertIsInstance(packet, bytes)

class TestReactionWheelEncoder(unittest.TestCase):
    """Test Reaction Wheel encoder functionality"""
    
    def setUp(self):
        self.encoder = ReactionWheelEncoder()
    
    def test_health_status_encoding(self):
        """Test health status telemetry encoding"""
        matlab_data = [1000.0, 0.5, 25.0, 28.0]  # Speed, current, temp, voltage
        packet = self.encoder.process_matlab_data_health(matlab_data)
        
        self.assertIsNotNone(packet)
        self.assertIsInstance(packet, bytes)

class TestStatusManagers(unittest.TestCase):
    """Test status managers for all devices"""
    
    def test_ars_status_manager(self):
        """Test ARS status manager"""
        manager = ARSStatusManager(enabled=True, cycle_interval=1.0, 
                                  scenarios=["normal", "warning"])
        
        # Test status word generation
        word1, word2, word3 = manager.get_status_words()
        self.assertIsInstance(word1, int)
        self.assertIsInstance(word2, int)
        self.assertIsInstance(word3, int)
        
        # Test scenario cycling
        time.sleep(1.1)  # Wait for cycle
        scenario = manager.get_current_scenario()
        self.assertIn(scenario, ["normal", "warning"])
    
    def test_magnetometer_status_manager(self):
        """Test Magnetometer status manager"""
        manager = MagnetometerStatusManager(enabled=True, cycle_interval=1.0,
                                          scenarios=["normal", "warning"])
        
        params = manager.get_status_parameters()
        self.assertIn("status", params)
        self.assertIn("temperature", params)
        self.assertIn("data_quality", params)
    
    def test_rwa_status_manager(self):
        """Test Reaction Wheel status manager"""
        manager = RWAStatusManager(enabled=True, cycle_interval=1.0,
                                 scenarios=["normal", "warning"])
        
        params = manager.get_status_parameters()
        self.assertIn("mode", params)
        self.assertIn("wheel_speed", params)
        self.assertIn("temperature", params)

class TestOutputTransmitters(unittest.TestCase):
    """Test output transmitters"""
    
    def test_serial_transmitter_simulation_mode(self):
        """Test serial transmitter in simulation mode"""
        config = SerialConfig(port="/dev/nonexistent")
        transmitter = SerialTransmitter(config)
        
        # Should fail to connect but not crash
        result = transmitter.connect()
        self.assertFalse(result)
        
        # Should work in simulation mode
        result = transmitter.send_data(b"test", "test_device")
        self.assertTrue(result)
    
    def test_can_transmitter_simulation_mode(self):
        """Test CAN transmitter in simulation mode"""
        config = CANConfig(channel="nonexistent")
        transmitter = CANTransmitter(config)
        
        # Should fail to connect but not crash
        result = transmitter.connect()
        self.assertFalse(result)
        
        # Should work in simulation mode
        result = transmitter.send_message(0x123, b"test", "test_device")
        self.assertTrue(result)
    
    def test_tcp_transmitter(self):
        """Test TCP transmitter"""
        config = TCPConfig(target_ip="127.0.0.1", target_port=9999)
        transmitter = TCPTransmitter(config)
        
        # Should fail to connect to non-existent server
        result = transmitter.connect()
        self.assertFalse(result)

class TestTCPReceiver(unittest.TestCase):
    """Test TCP receiver functionality"""
    
    def test_tcp_receiver_config(self):
        """Test TCP receiver configuration"""
        config = TCPReceiverConfig(mode="server", ip_address="127.0.0.1", port=5000)
        receiver = TCPReceiver(config)
        
        self.assertEqual(receiver.config.mode, "server")
        self.assertEqual(receiver.config.ip_address, "127.0.0.1")
        self.assertEqual(receiver.config.port, 5000)

class TestPacketLogger(unittest.TestCase):
    """Test packet logging functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")
    
    def tearDown(self):
        # Clean up temp files
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        os.rmdir(self.temp_dir)
    
    def test_packet_logging(self):
        """Test packet logging to file"""
        logger = PacketLogger()
        logger.setup_device_logging("test_device", self.log_file)
        
        # Log a test packet
        test_data = b"\x01\x02\x03\x04"
        logger.log_packet("test_device", test_data)
        logger.close_all_logging()
        
        # Verify log file was created and contains data
        self.assertTrue(os.path.exists(self.log_file))
        
        with open(self.log_file, 'r') as f:
            content = f.read()
            self.assertIn("TEST_DEVICE", content)  # Device name is uppercase in log
            self.assertIn("01020304", content)

class TestUSBLoopbackTester(unittest.TestCase):
    """Test USB loopback testing functionality"""
    
    def test_usb_loopback_config(self):
        """Test USB loopback tester configuration"""
        configs = {
            "test_device": USBPortConfig(port="/dev/ttyUSB0", baud_rate=115200)
        }
        
        tester = USBLoopbackTester(configs)
        self.assertIn("test_device", tester.device_configs)

class TestErrorHandler(unittest.TestCase):
    """Test error handling functionality"""
    
    def setUp(self):
        self.error_handler = ErrorHandler()
    
    def test_error_handling(self):
        """Test error handling and recovery"""
        context = self.error_handler.get_error_context("test_device", "test_component")
        context.error_type = ErrorType.CONNECTION
        context.severity = ErrorSeverity.MEDIUM
        
        # Test error handling
        test_error = ConnectionError("Test connection error")
        result = self.error_handler.handle_error(test_error, context)
        
        # Should attempt recovery
        self.assertTrue(result)
        self.assertEqual(context.error_count, 1)
    
    def test_error_statistics(self):
        """Test error statistics collection"""
        context = self.error_handler.get_error_context("test_device", "test_component")
        context.error_type = ErrorType.DATA_PROCESSING
        
        # Generate some errors
        for _ in range(5):
            test_error = ValueError("Test data error")
            self.error_handler.handle_error(test_error, context)
        
        stats = self.error_handler.get_error_statistics()
        self.assertEqual(stats["total_errors"], 5)

class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring functionality"""
    
    def setUp(self):
        self.monitor = PerformanceMonitor()
    
    def test_latency_measurement(self):
        """Test latency measurement"""
        with self.monitor.measure_latency("test_component", "test_operation"):
            time.sleep(0.001)  # 1ms operation
        
        metrics = self.monitor.get_component_metrics("test_component")
        self.assertEqual(metrics.total_operations, 1)
        self.assertGreater(metrics.get_average_latency(), 0)
    
    def test_performance_summary(self):
        """Test performance summary generation"""
        # Generate some metrics
        with self.monitor.measure_latency("test_component", "test_operation"):
            time.sleep(0.001)
        
        summary = self.monitor.get_performance_summary()
        self.assertIn("system_metrics", summary)
        self.assertIn("component_metrics", summary)
        self.assertIn("test_component", summary["component_metrics"])

class TestSimulatorIntegration(unittest.TestCase):
    """Test simulator integration"""
    
    def setUp(self):
        # Create a temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
        config_data = {
            "tcp_mode": "server",
            "matlab_server_ip": "127.0.0.1",
            "matlab_server_port": 5000,
            "devices": {
                "ars": {
                    "enabled": True,
                    "matlab_ports": [5000, 5001, 5002, 5003, 5004, 5005],
                    "duplicate_primary_to_redundant": True,
                    "redundant_variation_percent": 0.1,
                    "output_mode": "serial",
                    "output_config": {
                        "port": "/dev/ttyUSB0",
                        "baud_rate": 115200
                    },
                    "endianness": "little",
                    "usb_loopback_enabled": False,
                    "log_packets_to_file": False,
                    "status_cycling_enabled": False,
                    "status_scenarios": ["normal"]
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
    
    def tearDown(self):
        # Clean up temp files
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.temp_dir)
    
    def test_simulator_config_loading(self):
        """Test simulator configuration loading"""
        from flatsat_device_simulator import load_config
        
        config = load_config(self.config_file)
        self.assertIsInstance(config, SimulatorConfig)
        self.assertEqual(config.tcp_mode, "server")
        self.assertIn("ars", config.devices)
    
    def test_simulator_initialization(self):
        """Test simulator initialization"""
        from flatsat_device_simulator import load_config
        
        config = load_config(self.config_file)
        simulator = FlatSatDeviceSimulator(config)
        
        self.assertIsInstance(simulator, FlatSatDeviceSimulator)
        self.assertIsNotNone(simulator.config)

class TestEndToEnd(unittest.TestCase):
    """End-to-end integration tests"""
    
    def test_matlab_data_flow(self):
        """Test complete MATLAB data flow"""
        # This would test the complete flow from MATLAB data to device packets
        # For now, just verify components can be instantiated together
        encoder = ARSEncoder()
        transmitter = SerialTransmitter(SerialConfig(port="/dev/nonexistent"))
        
        # Test data flow
        matlab_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        packet = encoder.convert_matlab_data(matlab_data)
        
        if packet:
            result = transmitter.send_data(packet.data, "ars")
            self.assertTrue(result)

def run_performance_tests():
    """Run performance-focused tests"""
    print("\n=== Performance Tests ===")
    
    # Test encoder performance
    encoder = ARSEncoder(duplicate_to_redundant=True)  # Enable duplication for test
    start_time = time.time()
    
    for _ in range(1000):
        matlab_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        packet = encoder.convert_matlab_data(matlab_data)
    
    end_time = time.time()
    duration = end_time - start_time
    rate = 1000 / duration
    
    print(f"ARS Encoder: {rate:.1f} packets/second")
    
    # Test transmitter performance
    transmitter = SerialTransmitter(SerialConfig(port="/dev/nonexistent"))
    start_time = time.time()
    
    for _ in range(1000):
        transmitter.send_data(b"test_data", "test_device")
    
    end_time = time.time()
    duration = end_time - start_time
    rate = 1000 / duration
    
    print(f"Serial Transmitter: {rate:.1f} packets/second")

def main():
    """Run all tests"""
    print("=== FlatSat Device Simulator Test Suite ===")
    
    # Run unit tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run performance tests
    run_performance_tests()
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'PASS' if success else 'FAIL'}")
    
    return success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
