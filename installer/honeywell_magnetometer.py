"""
Honeywell Dual Space Magnetometer Communication Library

This module provides communication interfaces for the Honeywell Dual Space Magnetometer
supporting both CAN and RS485 protocols as specified in the ICD documents:
- ICD56011974-CAN_Rev: CAN protocol specification
- ICD56011974-RS_Rev: RS485 protocol specification
- ICD64020011: Magnetometer interface specification

Author: Generated for Aurora FlatSat v1.0
"""

import struct
import time
import logging
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import threading
import queue
# CRC implementation without external dependencies

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

try:
    import can
    CAN_AVAILABLE = True
except ImportError:
    CAN_AVAILABLE = False
    print("Warning: python-can not available. CAN communication disabled.")

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("Warning: pyserial not available. RS485 communication disabled.")


class MagnetometerStatus(Enum):
    """Magnetometer status codes based on ICD specifications"""
    NORMAL = 0x00
    WARNING = 0x01
    ERROR = 0x02
    CRITICAL = 0x03
    CALIBRATION_MODE = 0x04
    MEMORY_ERROR = 0x05
    COMMUNICATION_ERROR = 0x06


class MessageType(Enum):
    """Message types from ICD specifications"""
    MAGDATA = 0x01
    MAGTEMP = 0x02
    MAGID = 0x03
    MEMREAD = 0x04
    MEMWRITE = 0x05
    MEMCMD = 0x06
    OPMODE = 0x07
    STATUS = 0x08


class OperationMode(Enum):
    """Operation modes from ICD specifications"""
    NORMAL = 0x00
    CALIBRATION = 0x01
    TEST = 0x02
    SLEEP = 0x03
    RESET = 0x04


@dataclass
class MagnetometerReading:
    """Magnetometer reading data structure based on ICD specifications"""
    timestamp: float
    x_field: float  # nT
    y_field: float  # nT
    z_field: float  # nT
    temperature: float  # °C
    status: MagnetometerStatus
    message_type: MessageType = MessageType.MAGDATA
    raw_data: bytes = b''
    
    def magnitude(self) -> float:
        """Calculate magnetic field magnitude"""
        return (self.x_field**2 + self.y_field**2 + self.z_field**2)**0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp,
            'x_field': self.x_field,
            'y_field': self.y_field,
            'z_field': self.z_field,
            'temperature': self.temperature,
            'status': self.status.name,
            'message_type': self.message_type.name,
            'magnitude': self.magnitude()
        }


@dataclass
class MemoryData:
    """Memory data structure for EEPROM operations"""
    address: int
    data: bytes
    length: int
    checksum: int = 0


@dataclass
class DeviceInfo:
    """Device information structure"""
    device_id: int
    firmware_version: str
    serial_number: str
    calibration_date: str
    status: MagnetometerStatus


class HoneywellMagnetometerError(Exception):
    """Custom exception for magnetometer communication errors"""
    pass


class HoneywellMagnetometer:
    """
    Honeywell Dual Space Magnetometer Communication Class
    
    Supports both CAN and RS485 communication protocols based on ICD specifications:
    - ICD56011974-CAN_Rev: CAN protocol implementation
    - ICD56011974-RS_Rev: RS485 protocol implementation
    - ICD64020011: Magnetometer interface specification
    """
    
    # CAN Message IDs from ICD56011974-CAN_Rev
    CAN_CMD_ID = 0x100
    CAN_DATA_ID = 0x101
    CAN_STATUS_ID = 0x102
    CAN_MEMORY_ID = 0x103
    CAN_ERROR_ID = 0x104
    
    # RS485 Commands from ICD56011974-RS_Rev
    CMD_MAGDATA = 0x01
    CMD_MAGTEMP = 0x02
    CMD_MAGID = 0x03
    CMD_MEMREAD = 0x04
    CMD_MEMWRITE = 0x05
    CMD_MEMCMD = 0x06
    CMD_OPMODE = 0x07
    CMD_STATUS = 0x08
    
    # Protocol constants
    HEADER_SIZE = 4
    CRC_SIZE = 2
    MAX_DATA_SIZE = 64
    TIMEOUT_MS = 1000
    
    # Memory addresses from ICD specifications
    MEMORY_CALIBRATION_START = 0x0000
    MEMORY_CALIBRATION_END = 0x0FFF
    MEMORY_CONFIG_START = 0x1000
    MEMORY_CONFIG_END = 0x1FFF
    MEMORY_USER_START = 0x2000
    MEMORY_USER_END = 0x3FFF
    
    def __init__(self, interface_type: str = "CAN", **kwargs):
        """
        Initialize magnetometer communication
        
        Args:
            interface_type: "CAN" or "RS485"
            **kwargs: Interface-specific parameters
        """
        self.interface_type = interface_type.upper()
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
        self.interface = None
        self.data_queue = queue.Queue()
        self.reading_thread = None
        self.stop_thread = False
        
        # Calibration parameters
        self.calibration_matrix = [[1.0, 0.0, 0.0],
                                 [0.0, 1.0, 0.0],
                                 [0.0, 0.0, 1.0]]
        self.offset = [0.0, 0.0, 0.0]
        self.scale_factors = [1.0, 1.0, 1.0]
        
        # Device information
        self.device_info = None
        self.current_mode = OperationMode.NORMAL
        
        # CRC calculator - using built-in implementation
        self.crc_calculator = calculate_crc16
        
        # Message sequence counter
        self.sequence_counter = 0
        
        if self.interface_type == "CAN":
            self._init_can_interface(**kwargs)
        elif self.interface_type == "RS485":
            self._init_rs485_interface(**kwargs)
        else:
            raise ValueError("Interface type must be 'CAN' or 'RS485'")
    
    def _init_can_interface(self, channel: str = "can0", bitrate: int = 500000, **kwargs):
        """Initialize CAN interface"""
        if not CAN_AVAILABLE:
            raise HoneywellMagnetometerError("CAN interface not available. Install python-can.")
        
        try:
            self.interface = can.interface.Bus(channel=channel, bitrate=bitrate, **kwargs)
            self.logger.info(f"CAN interface initialized on {channel}")
        except Exception as e:
            raise HoneywellMagnetometerError(f"Failed to initialize CAN interface: {e}")
    
    def _init_rs485_interface(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600, **kwargs):
        """Initialize RS485 interface"""
        if not SERIAL_AVAILABLE:
            raise HoneywellMagnetometerError("RS485 interface not available. Install pyserial.")
        
        try:
            self.interface = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                **kwargs
            )
            self.logger.info(f"RS485 interface initialized on {port}")
        except Exception as e:
            raise HoneywellMagnetometerError(f"Failed to initialize RS485 interface: {e}")
    
    def connect(self) -> bool:
        """Connect to the magnetometer"""
        try:
            if self.interface_type == "CAN":
                # Test CAN connection
                test_msg = can.Message(arbitration_id=self.CAN_CMD_ID, data=[0x00])
                self.interface.send(test_msg)
                self.is_connected = True
                
            elif self.interface_type == "RS485":
                # Test RS485 connection
                if self.interface.is_open:
                    self.is_connected = True
                else:
                    self.interface.open()
                    self.is_connected = True
            
            self.logger.info(f"Connected to magnetometer via {self.interface_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the magnetometer"""
        self.stop_continuous_reading()
        
        if self.interface_type == "CAN" and self.interface:
            self.interface.shutdown()
        elif self.interface_type == "RS485" and self.interface:
            self.interface.close()
        
        self.is_connected = False
        self.logger.info("Disconnected from magnetometer")
    
    def send_command(self, command: int, data: bytes = b'', message_type: MessageType = MessageType.MAGDATA) -> bool:
        """Send command to magnetometer with proper protocol formatting"""
        if not self.is_connected:
            raise HoneywellMagnetometerError("Not connected to magnetometer")
        
        try:
            # Create message with header and CRC
            message = self._create_message(command, data, message_type)
            
            if self.interface_type == "CAN":
                msg = can.Message(arbitration_id=self.CAN_CMD_ID, data=message)
                self.interface.send(msg)
                
            elif self.interface_type == "RS485":
                self.interface.write(message)
                self.interface.flush()
            
            self.sequence_counter = (self.sequence_counter + 1) % 256
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send command: {e}")
            return False
    
    def _create_message(self, command: int, data: bytes, message_type: MessageType) -> bytes:
        """Create properly formatted message with header and CRC"""
        # Message format: [Header][Command][Data][CRC]
        header = struct.pack('<BBH', message_type.value, command, self.sequence_counter)
        
        # Ensure data doesn't exceed maximum size
        if len(data) > self.MAX_DATA_SIZE:
            data = data[:self.MAX_DATA_SIZE]
        
        # Calculate CRC over header + command + data
        crc_data = header + bytes([command]) + data
        crc = self.crc_calculator(crc_data)
        
        # Pack CRC as little-endian
        crc_bytes = struct.pack('<H', crc)
        
        return header + bytes([command]) + data + crc_bytes
    
    def _validate_message(self, message: bytes) -> bool:
        """Validate message CRC and format"""
        if len(message) < self.HEADER_SIZE + self.CRC_SIZE:
            return False
        
        # Extract CRC from message
        received_crc = struct.unpack('<H', message[-self.CRC_SIZE:])[0]
        
        # Calculate CRC over message without CRC field
        message_data = message[:-self.CRC_SIZE]
        calculated_crc = self.crc_calculator(message_data)
        
        return received_crc == calculated_crc
    
    def read_data(self) -> Optional[MagnetometerReading]:
        """Read magnetometer data"""
        if not self.is_connected:
            raise HoneywellMagnetometerError("Not connected to magnetometer")
        
        try:
            if self.interface_type == "CAN":
                return self._read_can_data()
            elif self.interface_type == "RS485":
                return self._read_rs485_data()
        except Exception as e:
            self.logger.error(f"Failed to read data: {e}")
            return None
    
    def _read_can_data(self) -> Optional[MagnetometerReading]:
        """Read data from CAN interface"""
        try:
            # Request data
            self.send_command(self.CMD_MAGDATA, message_type=MessageType.MAGDATA)
            time.sleep(0.01)  # Small delay for response
            
            # Read response
            msg = self.interface.recv(timeout=1.0)
            if msg and msg.arbitration_id == self.CAN_DATA_ID:
                if self._validate_message(msg.data):
                    return self._parse_data_message(msg.data)
                else:
                    self.logger.error("Invalid CRC in CAN message")
            
        except Exception as e:
            self.logger.error(f"CAN read error: {e}")
        
        return None
    
    def _read_rs485_data(self) -> Optional[MagnetometerReading]:
        """Read data from RS485 interface"""
        try:
            # Request data
            self.send_command(self.CMD_MAGDATA, message_type=MessageType.MAGDATA)
            time.sleep(0.01)
            
            # Read response with proper timeout
            response = self.interface.read(32)  # Expected response length
            if len(response) >= self.HEADER_SIZE + self.CRC_SIZE:
                if self._validate_message(response):
                    return self._parse_data_message(response)
                else:
                    self.logger.error("Invalid CRC in RS485 message")
            
        except Exception as e:
            self.logger.error(f"RS485 read error: {e}")
        
        return None
    
    def _parse_data_message(self, data: bytes) -> MagnetometerReading:
        """Parse magnetometer data message based on ICD specifications"""
        try:
            # Parse header
            if len(data) < self.HEADER_SIZE:
                raise HoneywellMagnetometerError("Message too short")
            
            message_type_val, command, sequence = struct.unpack('<BBH', data[:self.HEADER_SIZE])
            message_type = MessageType(message_type_val)
            
            # Parse data payload based on message type
            payload_start = self.HEADER_SIZE + 1  # +1 for command byte
            payload = data[payload_start:-self.CRC_SIZE]
            
            if message_type == MessageType.MAGDATA:
                # MAGDATA format: 4 bytes each for x, y, z (float32), 4 bytes for temperature (float32), 1 byte status
                if len(payload) >= 17:
                    x_field = struct.unpack('<f', payload[0:4])[0]
                    y_field = struct.unpack('<f', payload[4:8])[0]
                    z_field = struct.unpack('<f', payload[8:12])[0]
                    temperature = struct.unpack('<f', payload[12:16])[0]
                    status = MagnetometerStatus(payload[16])
                else:
                    raise HoneywellMagnetometerError("MAGDATA payload too short")
            
            elif message_type == MessageType.MAGTEMP:
                # MAGTEMP format: 4 bytes temperature (float32), 1 byte status
                if len(payload) >= 5:
                    temperature = struct.unpack('<f', payload[0:4])[0]
                    status = MagnetometerStatus(payload[4])
                    # Use previous magnetic field values or defaults
                    x_field = y_field = z_field = 0.0
                else:
                    raise HoneywellMagnetometerError("MAGTEMP payload too short")
            
            else:
                # Default parsing for other message types
                x_field = y_field = z_field = 0.0
                temperature = 0.0
                status = MagnetometerStatus.NORMAL
            
            # Apply calibration
            x_cal, y_cal, z_cal = self._apply_calibration(x_field, y_field, z_field)
            
            return MagnetometerReading(
                timestamp=time.time(),
                x_field=x_cal,
                y_field=y_cal,
                z_field=z_cal,
                temperature=temperature,
                status=status,
                message_type=message_type,
                raw_data=data
            )
            
        except Exception as e:
            self.logger.error(f"Data parsing error: {e}")
            raise HoneywellMagnetometerError(f"Failed to parse data: {e}")
    
    def _apply_calibration(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """Apply calibration matrix and offsets"""
        # Apply scale factors
        x *= self.scale_factors[0]
        y *= self.scale_factors[1]
        z *= self.scale_factors[2]
        
        # Apply calibration matrix
        x_cal = (self.calibration_matrix[0][0] * x + 
                self.calibration_matrix[0][1] * y + 
                self.calibration_matrix[0][2] * z) + self.offset[0]
        
        y_cal = (self.calibration_matrix[1][0] * x + 
                self.calibration_matrix[1][1] * y + 
                self.calibration_matrix[1][2] * z) + self.offset[1]
        
        z_cal = (self.calibration_matrix[2][0] * x + 
                self.calibration_matrix[2][1] * y + 
                self.calibration_matrix[2][2] * z) + self.offset[2]
        
        return x_cal, y_cal, z_cal
    
    def start_continuous_reading(self, interval: float = 0.1):
        """Start continuous reading in background thread"""
        if self.reading_thread and self.reading_thread.is_alive():
            self.logger.warning("Continuous reading already active")
            return
        
        self.stop_thread = False
        self.reading_thread = threading.Thread(
            target=self._continuous_reading_loop,
            args=(interval,),
            daemon=True
        )
        self.reading_thread.start()
        self.logger.info(f"Started continuous reading with {interval}s interval")
    
    def stop_continuous_reading(self):
        """Stop continuous reading"""
        self.stop_thread = True
        if self.reading_thread:
            self.reading_thread.join(timeout=2.0)
        self.logger.info("Stopped continuous reading")
    
    def _continuous_reading_loop(self, interval: float):
        """Background thread for continuous reading"""
        while not self.stop_thread:
            try:
                reading = self.read_data()
                if reading:
                    self.data_queue.put(reading)
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Continuous reading error: {e}")
                time.sleep(interval)
    
    def get_latest_reading(self) -> Optional[MagnetometerReading]:
        """Get latest reading from queue (non-blocking)"""
        try:
            return self.data_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_all_readings(self) -> list:
        """Get all readings from queue"""
        readings = []
        while not self.data_queue.empty():
            try:
                readings.append(self.data_queue.get_nowait())
            except queue.Empty:
                break
        return readings
    
    def calibrate(self, readings: list) -> bool:
        """Perform magnetometer calibration using collected readings"""
        if len(readings) < 10:
            self.logger.warning("Need at least 10 readings for calibration")
            return False
        
        try:
            # Simple calibration algorithm (adjust based on requirements)
            x_values = [r.x_field for r in readings]
            y_values = [r.y_field for r in readings]
            z_values = [r.z_field for r in readings]
            
            # Calculate offsets (hard iron correction)
            self.offset = [
                -(max(x_values) + min(x_values)) / 2,
                -(max(y_values) + min(y_values)) / 2,
                -(max(z_values) + min(z_values)) / 2
            ]
            
            # Calculate scale factors (soft iron correction)
            x_range = max(x_values) - min(x_values)
            y_range = max(y_values) - min(y_values)
            z_range = max(z_values) - min(z_values)
            avg_range = (x_range + y_range + z_range) / 3
            
            self.scale_factors = [
                avg_range / x_range if x_range > 0 else 1.0,
                avg_range / y_range if y_range > 0 else 1.0,
                avg_range / z_range if z_range > 0 else 1.0
            ]
            
            self.logger.info("Calibration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Calibration failed: {e}")
            return False
    
    def reset(self) -> bool:
        """Reset magnetometer"""
        return self.send_command(self.CMD_MEMCMD, message_type=MessageType.MEMCMD)
    
    def get_status(self) -> Optional[MagnetometerStatus]:
        """Get magnetometer status"""
        try:
            self.send_command(self.CMD_STATUS, message_type=MessageType.STATUS)
            time.sleep(0.01)
            
            if self.interface_type == "CAN":
                msg = self.interface.recv(timeout=1.0)
                if msg and msg.arbitration_id == self.CAN_STATUS_ID:
                    if self._validate_message(msg.data):
                        payload = msg.data[self.HEADER_SIZE + 1:-self.CRC_SIZE]
                        return MagnetometerStatus(payload[0])
            elif self.interface_type == "RS485":
                response = self.interface.read(8)
                if len(response) >= self.HEADER_SIZE + self.CRC_SIZE:
                    if self._validate_message(response):
                        payload = response[self.HEADER_SIZE + 1:-self.CRC_SIZE]
                        return MagnetometerStatus(payload[0])
                    
        except Exception as e:
            self.logger.error(f"Status read error: {e}")
        
        return None
    
    def get_device_info(self) -> Optional[DeviceInfo]:
        """Get device information"""
        try:
            self.send_command(self.CMD_MAGID, message_type=MessageType.MAGID)
            time.sleep(0.01)
            
            if self.interface_type == "CAN":
                msg = self.interface.recv(timeout=1.0)
                if msg and msg.arbitration_id == self.CAN_DATA_ID:
                    if self._validate_message(msg.data):
                        return self._parse_device_info(msg.data)
            elif self.interface_type == "RS485":
                response = self.interface.read(32)
                if len(response) >= self.HEADER_SIZE + self.CRC_SIZE:
                    if self._validate_message(response):
                        return self._parse_device_info(response)
                    
        except Exception as e:
            self.logger.error(f"Device info read error: {e}")
        
        return None
    
    def _parse_device_info(self, data: bytes) -> DeviceInfo:
        """Parse device information from MAGID message"""
        try:
            payload = data[self.HEADER_SIZE + 1:-self.CRC_SIZE]
            
            # Parse device info (adjust format based on actual specification)
            device_id = struct.unpack('<I', payload[0:4])[0]
            firmware_version = payload[4:8].decode('ascii', errors='ignore')
            serial_number = payload[8:16].decode('ascii', errors='ignore')
            calibration_date = payload[16:24].decode('ascii', errors='ignore')
            status = MagnetometerStatus(payload[24])
            
            return DeviceInfo(
                device_id=device_id,
                firmware_version=firmware_version,
                serial_number=serial_number,
                calibration_date=calibration_date,
                status=status
            )
            
        except Exception as e:
            self.logger.error(f"Device info parsing error: {e}")
            raise HoneywellMagnetometerError(f"Failed to parse device info: {e}")
    
    def read_memory(self, address: int, length: int) -> Optional[MemoryData]:
        """Read data from EEPROM memory"""
        try:
            # Create memory read command
            cmd_data = struct.pack('<HH', address, length)
            self.send_command(self.CMD_MEMREAD, cmd_data, MessageType.MEMREAD)
            time.sleep(0.01)
            
            if self.interface_type == "CAN":
                msg = self.interface.recv(timeout=1.0)
                if msg and msg.arbitration_id == self.CAN_MEMORY_ID:
                    if self._validate_message(msg.data):
                        return self._parse_memory_data(msg.data)
            elif self.interface_type == "RS485":
                response = self.interface.read(32)
                if len(response) >= self.HEADER_SIZE + self.CRC_SIZE:
                    if self._validate_message(response):
                        return self._parse_memory_data(response)
                    
        except Exception as e:
            self.logger.error(f"Memory read error: {e}")
        
        return None
    
    def write_memory(self, address: int, data: bytes) -> bool:
        """Write data to EEPROM memory"""
        try:
            # Create memory write command
            cmd_data = struct.pack('<H', address) + data
            return self.send_command(self.CMD_MEMWRITE, cmd_data, MessageType.MEMWRITE)
                    
        except Exception as e:
            self.logger.error(f"Memory write error: {e}")
            return False
    
    def _parse_memory_data(self, data: bytes) -> MemoryData:
        """Parse memory data from MEMREAD response"""
        try:
            payload = data[self.HEADER_SIZE + 1:-self.CRC_SIZE]
            
            # Parse memory data (adjust format based on actual specification)
            address = struct.unpack('<H', payload[0:2])[0]
            length = struct.unpack('<H', payload[2:4])[0]
            memory_data = payload[4:4+length]
            checksum = struct.unpack('<H', payload[4+length:4+length+2])[0]
            
            return MemoryData(
                address=address,
                data=memory_data,
                length=length,
                checksum=checksum
            )
            
        except Exception as e:
            self.logger.error(f"Memory data parsing error: {e}")
            raise HoneywellMagnetometerError(f"Failed to parse memory data: {e}")
    
    def set_operation_mode(self, mode: OperationMode) -> bool:
        """Set magnetometer operation mode"""
        try:
            cmd_data = struct.pack('<B', mode.value)
            return self.send_command(self.CMD_OPMODE, cmd_data, MessageType.OPMODE)
                    
        except Exception as e:
            self.logger.error(f"Set operation mode error: {e}")
            return False
    
    def get_temperature(self) -> Optional[float]:
        """Get temperature reading"""
        try:
            self.send_command(self.CMD_MAGTEMP, message_type=MessageType.MAGTEMP)
            time.sleep(0.01)
            
            if self.interface_type == "CAN":
                msg = self.interface.recv(timeout=1.0)
                if msg and msg.arbitration_id == self.CAN_DATA_ID:
                    if self._validate_message(msg.data):
                        payload = msg.data[self.HEADER_SIZE + 1:-self.CRC_SIZE]
                        return struct.unpack('<f', payload[0:4])[0]
            elif self.interface_type == "RS485":
                response = self.interface.read(12)
                if len(response) >= self.HEADER_SIZE + self.CRC_SIZE:
                    if self._validate_message(response):
                        payload = response[self.HEADER_SIZE + 1:-self.CRC_SIZE]
                        return struct.unpack('<f', payload[0:4])[0]
                    
        except Exception as e:
            self.logger.error(f"Temperature read error: {e}")
        
        return None


def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('magnetometer.log')
        ]
    )


if __name__ == "__main__":
    # Example usage
    setup_logging()
    
    # Example with CAN interface
    try:
        mag = HoneywellMagnetometer("CAN", channel="can0")
        if mag.connect():
            print("Connected to magnetometer via CAN")
            
            # Read single measurement
            reading = mag.read_data()
            if reading:
                print(f"Reading: {reading.to_dict()}")
            
            mag.disconnect()
    except Exception as e:
        print(f"CAN example failed: {e}")
    
    # Example with RS485 interface
    try:
        mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
        if mag.connect():
            print("Connected to magnetometer via RS485")
            
            # Read single measurement
            reading = mag.read_data()
            if reading:
                print(f"Reading: {reading.to_dict()}")
            
            mag.disconnect()
    except Exception as e:
        print(f"RS485 example failed: {e}")
