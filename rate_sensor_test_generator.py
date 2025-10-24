#!/usr/bin/env python3
"""
Rate Sensor Test Generator with REST API

This module provides a REST API for generating test data for the Honeywell HG4934
rate sensor. It allows setting values for all parameters described in section 3.2.4
of the Honeywell specification and converts JSON data to the proper serial format.

Based on Honeywell HG4934 specification DS36134-60, section 3.2.4 - Serial Data Output Protocol
"""

import json
import struct
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, render_template_string
import serial
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RateSensorData:
    """Data structure for rate sensor parameters as defined in section 3.2.4"""
    
    # Angular rates (Body, Control Channel) - 2 bytes each, LSB weighting: 600 x 2^-23 rad/sec/LSB
    angular_rate_x: float = 0.0  # rad/sec
    angular_rate_y: float = 0.0  # rad/sec  
    angular_rate_z: float = 0.0  # rad/sec
    
    # Status Word 1 - 2 bytes (see Table 7)
    status_word_1: int = 0x0000
    
    # Status Word 2 - 2 bytes (see Table 8) 
    status_word_2: int = 0x0000
    
    # Status Word 3 - 2 bytes (see Table 9)
    status_word_3: int = 0x0000
    
    # Summed Incremental Angles (Body, Inertial Channel) - 4 bytes each, LSB weighting: 2^-27 rad/LSB
    summed_angle_x: float = 0.0  # rad
    summed_angle_y: float = 0.0  # rad
    summed_angle_z: float = 0.0  # rad
    
    # Additional metadata
    timestamp: float = 0.0
    message_counter: int = 0

class StatusWordBuilder:
    """Helper class for building status words according to Honeywell specification"""
    
    @staticmethod
    def build_status_word_1(
        counter: int = 0,
        bit_mode: int = 1,  # 0=Power-up BIT, 1=Continuous BIT, 2=Initiated BIT
        rate_sensor_failed: bool = False,
        gyro_failed: bool = False,
        agc_voltage_failed: bool = False
    ) -> int:
        """Build Status Word 1 according to Table 7"""
        word = 0
        
        # Bit 0-1: 2 Bit Counter (00 01 10 11...)
        word |= (counter & 0x03)
        
        # Bit 2-3: 2 bit BIT-mode indicator
        word |= ((bit_mode & 0x03) << 2)
        
        # Bit 4: Rate Sensor Failed (Latched)
        if rate_sensor_failed:
            word |= (1 << 4)
            
        # Bit 5: Gyro Failed (Latched)  
        if gyro_failed:
            word |= (1 << 5)
            
        # Bit 6: Reserved (always 0)
        
        # Bit 7: AGC Voltage
        if agc_voltage_failed:
            word |= (1 << 7)
            
        return word & 0xFFFF
    
    @staticmethod
    def build_status_word_2(
        gyro_temperature_a: int = 25,  # Temperature in °C (LSB=1°C)
        motor_bias_voltage_failed: bool = False,
        start_data_flag: bool = False,  # 0=sensor data, 1=5555h sync data
        processor_failed: bool = False,
        memory_failed: bool = False
    ) -> int:
        """Build Status Word 2 according to Table 8"""
        word = 0
        
        # Bit 0-7: Gyro Temperature A (LSB=1°C)
        word |= (gyro_temperature_a & 0xFF)
        
        # Bit 8: Motor Bias Voltage
        if motor_bias_voltage_failed:
            word |= (1 << 8)
            
        # Bit 9: Start data flag
        if start_data_flag:
            word |= (1 << 9)
            
        # Bit 10: Processor
        if processor_failed:
            word |= (1 << 10)
            
        # Bit 11: Memory
        if memory_failed:
            word |= (1 << 11)
            
        return word & 0xFFFF
    
    @staticmethod
    def build_status_word_3(
        gyro_a_start_run: bool = True,  # 0=Start, 1=Run
        gyro_b_start_run: bool = True,
        gyro_c_start_run: bool = True,
        gyro_a_fdc: bool = False,  # 0=OK, 1=Failed
        gyro_b_fdc: bool = False,
        gyro_c_fdc: bool = False,
        fdc_failed: bool = False,
        rs_ok: bool = True  # 0=OK, 1=Failed
    ) -> int:
        """Build Status Word 3 according to Table 9"""
        word = 0
        
        # Bit 8: Gyro A Start/Run
        if gyro_a_start_run:
            word |= (1 << 8)
            
        # Bit 9: Gyro B Start/Run
        if gyro_b_start_run:
            word |= (1 << 9)
            
        # Bit 10: Gyro C Start/Run
        if gyro_c_start_run:
            word |= (1 << 10)
            
        # Bit 11: Gyro A FDC
        if gyro_a_fdc:
            word |= (1 << 11)
            
        # Bit 12: Gyro B FDC
        if gyro_b_fdc:
            word |= (1 << 12)
            
        # Bit 13: Gyro C FDC
        if gyro_c_fdc:
            word |= (1 << 13)
            
        # Bit 14: FDC Failed
        if fdc_failed:
            word |= (1 << 14)
            
        # Bit 15: RS OK
        if rs_ok:
            word |= (1 << 15)
            
        return word & 0xFFFF

class MessageEncoder:
    """Encodes rate sensor data into Honeywell protocol format"""
    
    # Scale factors from specification
    ANGULAR_RATE_SCALE = 600 * (2 ** -23)  # rad/sec/LSB
    ANGLE_SCALE = 2 ** -27  # rad/LSB
    
    @classmethod
    def encode_angular_rate(cls, rate_rad_per_sec: float) -> bytes:
        """Convert angular rate from rad/sec to 16-bit signed integer"""
        # Convert to LSB units
        lsb_value = int(rate_rad_per_sec / cls.ANGULAR_RATE_SCALE)
        
        # Clamp to 16-bit signed range
        lsb_value = max(-32768, min(32767, lsb_value))
        
        # Pack as little-endian 16-bit signed integer
        return struct.pack('<h', lsb_value)
    
    @classmethod
    def encode_angle(cls, angle_rad: float) -> bytes:
        """Convert angle from rad to 32-bit signed integer"""
        # Convert to LSB units
        lsb_value = int(angle_rad / cls.ANGLE_SCALE)
        
        # Clamp to 32-bit signed range
        lsb_value = max(-2147483648, min(2147483647, lsb_value))
        
        # Pack as little-endian 32-bit signed integer
        return struct.pack('<i', lsb_value)
    
    @classmethod
    def encode_message(cls, data: RateSensorData) -> bytes:
        """Encode complete message according to Honeywell protocol"""
        message = bytearray()
        
        # Add sync byte (Rate Sensor address)
        message.append(0xAA)  # Sync byte
        
        # Angular rates (2 bytes each, little-endian)
        message.extend(cls.encode_angular_rate(data.angular_rate_x))
        message.extend(cls.encode_angular_rate(data.angular_rate_y))
        message.extend(cls.encode_angular_rate(data.angular_rate_z))
        
        # Status words (2 bytes each, little-endian)
        message.extend(struct.pack('<H', data.status_word_1))
        message.extend(struct.pack('<H', data.status_word_2))
        message.extend(struct.pack('<H', data.status_word_3))
        
        # Summed incremental angles (4 bytes each, little-endian)
        message.extend(cls.encode_angle(data.summed_angle_x))
        message.extend(cls.encode_angle(data.summed_angle_y))
        message.extend(cls.encode_angle(data.summed_angle_z))
        
        # Calculate and append checksum (16-bit unsigned sum)
        checksum = sum(message[1:]) & 0xFFFF  # Skip sync byte
        message.extend(struct.pack('<H', checksum))
        
        return bytes(message)

class SerialTransmitter:
    """Handles serial communication for sending encoded messages"""
    
    def __init__(self, port: str = '/dev/ttyUSB0', baud_rate: int = 115200):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn: Optional[serial.Serial] = None
        self.is_transmitting = False
        self.transmit_thread: Optional[threading.Thread] = None
        self.message_queue: List[bytes] = []
        self.queue_lock = threading.Lock()
        
    def connect(self) -> bool:
        """Connect to serial port"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1.0
            )
            logger.info(f"Connected to serial port {self.port} at {self.baud_rate} baud")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to serial port: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        self.stop_transmission()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Disconnected from serial port")
    
    def queue_message(self, message: bytes):
        """Queue a message for transmission"""
        with self.queue_lock:
            self.message_queue.append(message)
    
    def start_transmission(self):
        """Start continuous message transmission"""
        if self.is_transmitting:
            return
            
        self.is_transmitting = True
        self.transmit_thread = threading.Thread(target=self._transmit_loop, daemon=True)
        self.transmit_thread.start()
        logger.info("Started message transmission")
    
    def stop_transmission(self):
        """Stop message transmission"""
        self.is_transmitting = False
        if self.transmit_thread:
            self.transmit_thread.join(timeout=1.0)
        logger.info("Stopped message transmission")
    
    def _transmit_loop(self):
        """Main transmission loop"""
        while self.is_transmitting and self.serial_conn and self.serial_conn.is_open:
            try:
                with self.queue_lock:
                    if self.message_queue:
                        message = self.message_queue.pop(0)
                        self.serial_conn.write(message)
                        logger.debug(f"Transmitted {len(message)} bytes")
                
                # Maintain 600 Hz rate (1.67ms between messages)
                time.sleep(1.0 / 600.0)
                
            except Exception as e:
                logger.error(f"Transmission error: {e}")
                break

class RateSensorTestGenerator:
    """Main test generator class with REST API"""
    
    def __init__(self, serial_port: str = '/dev/ttyUSB0', serial_baud: int = 115200):
        self.serial_transmitter = SerialTransmitter(serial_port, serial_baud)
        self.current_data = RateSensorData()
        self.message_counter = 0
        self.app = Flask(__name__)
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup REST API routes"""
        
        @self.app.route('/')
        def index():
            """Serve main API documentation page"""
            return render_template_string(API_DOCUMENTATION_TEMPLATE)
        
        @self.app.route('/api/data', methods=['GET'])
        def get_current_data():
            """Get current rate sensor data"""
            return jsonify({
                'status': 'success',
                'data': asdict(self.current_data)
            })
        
        @self.app.route('/api/data', methods=['POST'])
        def set_data():
            """Set rate sensor data parameters"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400
                
                # Update current data with provided values
                for key, value in data.items():
                    if hasattr(self.current_data, key):
                        setattr(self.current_data, key, value)
                
                # Update timestamp and counter
                self.current_data.timestamp = time.time()
                self.current_data.message_counter = self.message_counter
                self.message_counter += 1
                
                return jsonify({
                    'status': 'success',
                    'message': 'Data updated successfully',
                    'data': asdict(self.current_data)
                })
                
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/status_words', methods=['POST'])
        def set_status_words():
            """Set status words with individual bit control"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400
                
                # Build status words
                if 'status_word_1' in data:
                    sw1_params = data['status_word_1']
                    self.current_data.status_word_1 = StatusWordBuilder.build_status_word_1(**sw1_params)
                
                if 'status_word_2' in data:
                    sw2_params = data['status_word_2']
                    self.current_data.status_word_2 = StatusWordBuilder.build_status_word_2(**sw2_params)
                
                if 'status_word_3' in data:
                    sw3_params = data['status_word_3']
                    self.current_data.status_word_3 = StatusWordBuilder.build_status_word_3(**sw3_params)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Status words updated successfully',
                    'status_words': {
                        'status_word_1': f'0x{self.current_data.status_word_1:04X}',
                        'status_word_2': f'0x{self.current_data.status_word_2:04X}',
                        'status_word_3': f'0x{self.current_data.status_word_3:04X}'
                    }
                })
                
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/encode', methods=['POST'])
        def encode_message():
            """Encode current data to Honeywell protocol format"""
            try:
                encoded_message = MessageEncoder.encode_message(self.current_data)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Message encoded successfully',
                    'encoded_data': {
                        'hex': encoded_message.hex().upper(),
                        'length': len(encoded_message),
                        'bytes': list(encoded_message)
                    }
                })
                
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/transmit', methods=['POST'])
        def start_transmission():
            """Start serial transmission of current data"""
            try:
                if not self.serial_transmitter.connect():
                    return jsonify({'status': 'error', 'message': 'Failed to connect to serial port'}), 500
                
                # Encode current message
                encoded_message = MessageEncoder.encode_message(self.current_data)
                
                # Queue message for transmission
                self.serial_transmitter.queue_message(encoded_message)
                
                # Start transmission
                self.serial_transmitter.start_transmission()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Transmission started',
                    'encoded_message': encoded_message.hex().upper()
                })
                
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/transmit', methods=['DELETE'])
        def stop_transmission():
            """Stop serial transmission"""
            try:
                self.serial_transmitter.stop_transmission()
                self.serial_transmitter.disconnect()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Transmission stopped'
                })
                
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/test_scenarios', methods=['GET'])
        def get_test_scenarios():
            """Get available test scenarios"""
            scenarios = {
                'normal_operation': {
                    'description': 'Normal sensor operation with typical rates',
                    'data': {
                        'angular_rate_x': 0.01,
                        'angular_rate_y': -0.005,
                        'angular_rate_z': 0.02,
                        'summed_angle_x': 0.1,
                        'summed_angle_y': -0.05,
                        'summed_angle_z': 0.2
                    },
                    'status_words': {
                        'status_word_1': {'counter': 0, 'bit_mode': 1, 'rate_sensor_failed': False, 'gyro_failed': False, 'agc_voltage_failed': False},
                        'status_word_2': {'gyro_temperature_a': 25, 'motor_bias_voltage_failed': False, 'start_data_flag': False, 'processor_failed': False, 'memory_failed': False},
                        'status_word_3': {'gyro_a_start_run': True, 'gyro_b_start_run': True, 'gyro_c_start_run': True, 'gyro_a_fdc': False, 'gyro_b_fdc': False, 'gyro_c_fdc': False, 'fdc_failed': False, 'rs_ok': True}
                    }
                },
                'high_rate_test': {
                    'description': 'High angular rate test',
                    'data': {
                        'angular_rate_x': 1.0,
                        'angular_rate_y': -0.5,
                        'angular_rate_z': 0.8,
                        'summed_angle_x': 10.0,
                        'summed_angle_y': -5.0,
                        'summed_angle_z': 8.0
                    },
                    'status_words': {
                        'status_word_1': {'counter': 1, 'bit_mode': 1, 'rate_sensor_failed': False, 'gyro_failed': False, 'agc_voltage_failed': False},
                        'status_word_2': {'gyro_temperature_a': 30, 'motor_bias_voltage_failed': False, 'start_data_flag': False, 'processor_failed': False, 'memory_failed': False},
                        'status_word_3': {'gyro_a_start_run': True, 'gyro_b_start_run': True, 'gyro_c_start_run': True, 'gyro_a_fdc': False, 'gyro_b_fdc': False, 'gyro_c_fdc': False, 'fdc_failed': False, 'rs_ok': True}
                    }
                },
                'fault_condition': {
                    'description': 'Fault condition test',
                    'data': {
                        'angular_rate_x': 0.0,
                        'angular_rate_y': 0.0,
                        'angular_rate_z': 0.0,
                        'summed_angle_x': 0.0,
                        'summed_angle_y': 0.0,
                        'summed_angle_z': 0.0
                    },
                    'status_words': {
                        'status_word_1': {'counter': 2, 'bit_mode': 1, 'rate_sensor_failed': True, 'gyro_failed': True, 'agc_voltage_failed': True},
                        'status_word_2': {'gyro_temperature_a': 50, 'motor_bias_voltage_failed': True, 'start_data_flag': False, 'processor_failed': True, 'memory_failed': True},
                        'status_word_3': {'gyro_a_start_run': False, 'gyro_b_start_run': False, 'gyro_c_start_run': False, 'gyro_a_fdc': True, 'gyro_b_fdc': True, 'gyro_c_fdc': True, 'fdc_failed': True, 'rs_ok': False}
                    }
                }
            }
            
            return jsonify({
                'status': 'success',
                'scenarios': scenarios
            })
        
        @self.app.route('/api/load_scenario/<scenario_name>', methods=['POST'])
        def load_scenario(scenario_name: str):
            """Load a predefined test scenario"""
            try:
                # Get scenarios
                scenarios_response = get_test_scenarios()
                scenarios_data = scenarios_response.get_json()
                
                if scenario_name not in scenarios_data['scenarios']:
                    return jsonify({'status': 'error', 'message': f'Scenario {scenario_name} not found'}), 404
                
                scenario = scenarios_data['scenarios'][scenario_name]
                
                # Load data
                if 'data' in scenario:
                    for key, value in scenario['data'].items():
                        if hasattr(self.current_data, key):
                            setattr(self.current_data, key, value)
                
                # Load status words
                if 'status_words' in scenario:
                    status_words = scenario['status_words']
                    
                    if 'status_word_1' in status_words:
                        self.current_data.status_word_1 = StatusWordBuilder.build_status_word_1(**status_words['status_word_1'])
                    
                    if 'status_word_2' in status_words:
                        self.current_data.status_word_2 = StatusWordBuilder.build_status_word_2(**status_words['status_word_2'])
                    
                    if 'status_word_3' in status_words:
                        self.current_data.status_word_3 = StatusWordBuilder.build_status_word_3(**status_words['status_word_3'])
                
                # Update metadata
                self.current_data.timestamp = time.time()
                self.current_data.message_counter = self.message_counter
                self.message_counter += 1
                
                return jsonify({
                    'status': 'success',
                    'message': f'Scenario {scenario_name} loaded successfully',
                    'data': asdict(self.current_data)
                })
                
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the REST API server"""
        logger.info(f"Starting Rate Sensor Test Generator API on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# API Documentation Template
API_DOCUMENTATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Rate Sensor Test Generator API</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .method { font-weight: bold; color: #0066cc; }
        .url { font-family: monospace; background: #e8e8e8; padding: 2px 5px; }
        pre { background: #f0f0f0; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Rate Sensor Test Generator API</h1>
    <p>REST API for generating test data for Honeywell HG4934 rate sensor</p>
    
    <h2>Endpoints</h2>
    
    <div class="endpoint">
        <div class="method">GET</div>
        <div class="url">/api/data</div>
        <p>Get current rate sensor data</p>
    </div>
    
    <div class="endpoint">
        <div class="method">POST</div>
        <div class="url">/api/data</div>
        <p>Set rate sensor data parameters</p>
        <pre>{
  "angular_rate_x": 0.01,
  "angular_rate_y": -0.005,
  "angular_rate_z": 0.02,
  "summed_angle_x": 0.1,
  "summed_angle_y": -0.05,
  "summed_angle_z": 0.2
}</pre>
    </div>
    
    <div class="endpoint">
        <div class="method">POST</div>
        <div class="url">/api/status_words</div>
        <p>Set status words with individual bit control</p>
        <pre>{
  "status_word_1": {
    "counter": 0,
    "bit_mode": 1,
    "rate_sensor_failed": false,
    "gyro_failed": false,
    "agc_voltage_failed": false
  },
  "status_word_2": {
    "gyro_temperature_a": 25,
    "motor_bias_voltage_failed": false,
    "start_data_flag": false,
    "processor_failed": false,
    "memory_failed": false
  },
  "status_word_3": {
    "gyro_a_start_run": true,
    "gyro_b_start_run": true,
    "gyro_c_start_run": true,
    "gyro_a_fdc": false,
    "gyro_b_fdc": false,
    "gyro_c_fdc": false,
    "fdc_failed": false,
    "rs_ok": true
  }
}</pre>
    </div>
    
    <div class="endpoint">
        <div class="method">POST</div>
        <div class="url">/api/encode</div>
        <p>Encode current data to Honeywell protocol format</p>
    </div>
    
    <div class="endpoint">
        <div class="method">POST</div>
        <div class="url">/api/transmit</div>
        <p>Start serial transmission of current data</p>
    </div>
    
    <div class="endpoint">
        <div class="method">DELETE</div>
        <div class="url">/api/transmit</div>
        <p>Stop serial transmission</p>
    </div>
    
    <div class="endpoint">
        <div class="method">GET</div>
        <div class="url">/api/test_scenarios</div>
        <p>Get available test scenarios</p>
    </div>
    
    <div class="endpoint">
        <div class="method">POST</div>
        <div class="url">/api/load_scenario/{scenario_name}</div>
        <p>Load a predefined test scenario</p>
    </div>
    
    <h2>Data Format</h2>
    <p>All angular rates are in rad/sec, angles in rad. Status words are built according to Honeywell specification Tables 7, 8, and 9.</p>
    
    <h2>Serial Communication</h2>
    <p>Messages are transmitted at 600 Hz over RS422 serial interface. Default port: /dev/ttyUSB0, Baud rate: 115200.</p>
</body>
</html>
"""

def main():
    """Main function to run the test generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Rate Sensor Test Generator API')
    parser.add_argument('--host', default='0.0.0.0', help='API host address')
    parser.add_argument('--port', type=int, default=5000, help='API port')
    parser.add_argument('--serial-port', default='/dev/ttyUSB0', help='Serial port for transmission')
    parser.add_argument('--serial-baud', type=int, default=115200, help='Serial baud rate')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run test generator
    generator = RateSensorTestGenerator(args.serial_port, args.serial_baud)
    
    try:
        generator.run(args.host, args.port, args.debug)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        generator.serial_transmitter.disconnect()

if __name__ == '__main__':
    main()



