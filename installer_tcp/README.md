# Honeywell Dual Space Magnetometer Communication Library

A Python library for communicating with the Honeywell Dual Space Magnetometer, supporting both CAN and RS485 communication protocols as specified in the ICD documents from the PDF specifications.

## Features

- **Dual Protocol Support**: CAN and RS485 communication interfaces based on ICD specifications
- **Real-time Data Reading**: Single and continuous reading modes with proper message formatting
- **Message Types**: Support for MAGDATA, MAGTEMP, MAGID, MEMREAD, MEMWRITE, MEMCMD, OPMODE commands
- **CRC Validation**: Built-in CRC-16 validation for message integrity
- **Memory Management**: EEPROM read/write operations with proper addressing
- **Operation Modes**: Support for NORMAL, CALIBRATION, TEST, SLEEP, RESET modes
- **Calibration Support**: Built-in calibration algorithms for hard and soft iron correction
- **Status Monitoring**: Comprehensive status monitoring with detailed error codes
- **Data Logging**: JSON export and continuous data collection
- **Thread-safe**: Background reading with thread-safe data access
- **Comprehensive Testing**: Unit tests and integration tests based on actual protocol specifications

## Installation

1. Clone or download the library files
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

### Core Dependencies

- `python-can>=4.0.0`: CAN bus communication
- `pyserial>=3.5`: RS485/Serial communication  
- `crcmod>=1.7`: CRC calculation for message validation (replaced with built-in implementation)

### Optional Dependencies

For enhanced functionality, install optional dependencies:

```bash
pip install numpy matplotlib pandas  # For data analysis and visualization
pip install pytest pytest-cov       # For testing
pip install black flake8            # For code quality
```

## Quick Start

### Basic Usage

```python
from honeywell_magnetometer import HoneywellMagnetometer, MessageType

# Initialize magnetometer (RS485)
mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0", baudrate=9600)

# Connect and read data
if mag.connect():
    reading = mag.read_data()
    if reading:
        print(f"Message Type: {reading.message_type.name}")
        print(f"X: {reading.x_field:.2f} nT")
        print(f"Y: {reading.y_field:.2f} nT")
        print(f"Z: {reading.z_field:.2f} nT")
        print(f"Magnitude: {reading.magnitude():.2f} nT")
    
    mag.disconnect()
```

### CAN Interface

```python
# Initialize magnetometer (CAN)
mag = HoneywellMagnetometer("CAN", channel="can0", bitrate=500000)

if mag.connect():
    reading = mag.read_data()
    # Process reading...
    mag.disconnect()
```

### Device Information

```python
# Get device information using MAGID command
device_info = mag.get_device_info()
if device_info:
    print(f"Device ID: {device_info.device_id}")
    print(f"Firmware Version: {device_info.firmware_version}")
    print(f"Serial Number: {device_info.serial_number}")
    print(f"Calibration Date: {device_info.calibration_date}")
```

### Temperature Reading

```python
# Get temperature using MAGTEMP command
temperature = mag.get_temperature()
if temperature is not None:
    print(f"Temperature: {temperature:.2f} °C")
```

### Memory Operations

```python
# Read calibration data from EEPROM
calibration_data = mag.read_memory(0x0000, 64)  # Read 64 bytes from calibration area
if calibration_data:
    print(f"Read {calibration_data.length} bytes from address 0x{calibration_data.address:04X}")
    print(f"Data: {calibration_data.data.hex()}")

# Write test data to user memory area
test_data = b"TEST_DATA_12345"
if mag.write_memory(0x2000, test_data):
    print("Test data written successfully")
```

### Operation Modes

```python
from honeywell_magnetometer import OperationMode

# Set to calibration mode
if mag.set_operation_mode(OperationMode.CALIBRATION):
    print("Successfully set to calibration mode")
    
    # Perform calibration operations...
    
    # Set back to normal mode
    mag.set_operation_mode(OperationMode.NORMAL)
```

### Continuous Reading

```python
# Start continuous reading
mag.start_continuous_reading(interval=0.1)  # Read every 100ms

# Collect readings for 10 seconds
time.sleep(10)

# Stop and get all readings
mag.stop_continuous_reading()
readings = mag.get_all_readings()
print(f"Collected {len(readings)} readings")
```

## API Reference

### HoneywellMagnetometer Class

#### Constructor
```python
HoneywellMagnetometer(interface_type, **kwargs)
```

**Parameters:**
- `interface_type` (str): "CAN" or "RS485"
- `**kwargs`: Interface-specific parameters

**CAN Parameters:**
- `channel` (str): CAN interface channel (default: "can0")
- `bitrate` (int): CAN bitrate (default: 500000)

**RS485 Parameters:**
- `port` (str): Serial port (default: "/dev/ttyUSB0")
- `baudrate` (int): Baud rate (default: 9600)

#### Methods

##### Connection Management
- `connect() -> bool`: Connect to magnetometer
- `disconnect()`: Disconnect from magnetometer

##### Data Reading
- `read_data() -> MagnetometerReading`: Read single measurement using MAGDATA command
- `get_temperature() -> float`: Get temperature reading using MAGTEMP command
- `start_continuous_reading(interval: float)`: Start background reading
- `stop_continuous_reading()`: Stop background reading
- `get_latest_reading() -> MagnetometerReading`: Get latest reading (non-blocking)
- `get_all_readings() -> list`: Get all queued readings

##### Device Information
- `get_device_info() -> DeviceInfo`: Get device information using MAGID command

##### Memory Operations
- `read_memory(address: int, length: int) -> MemoryData`: Read data from EEPROM
- `write_memory(address: int, data: bytes) -> bool`: Write data to EEPROM

##### Operation Modes
- `set_operation_mode(mode: OperationMode) -> bool`: Set magnetometer operation mode

##### Calibration
- `calibrate(readings: list) -> bool`: Perform calibration using collected readings

##### Status and Control
- `get_status() -> MagnetometerStatus`: Get magnetometer status using STATUS command
- `reset() -> bool`: Reset magnetometer using MEMCMD command
- `send_command(command: int, data: bytes, message_type: MessageType) -> bool`: Send custom command

### MagnetometerReading Class

#### Properties
- `timestamp` (float): Reading timestamp
- `x_field` (float): X-axis magnetic field (nT)
- `y_field` (float): Y-axis magnetic field (nT)
- `z_field` (float): Z-axis magnetic field (nT)
- `temperature` (float): Temperature (°C)
- `status` (MagnetometerStatus): Reading status
- `message_type` (MessageType): Type of message received
- `raw_data` (bytes): Raw data bytes

#### Methods
- `magnitude() -> float`: Calculate magnetic field magnitude
- `to_dict() -> dict`: Convert to dictionary for JSON serialization

### Enums

#### MagnetometerStatus
- `NORMAL`: Normal operation
- `WARNING`: Warning condition
- `ERROR`: Error condition
- `CRITICAL`: Critical error
- `CALIBRATION_MODE`: Calibration mode active
- `MEMORY_ERROR`: Memory error detected
- `COMMUNICATION_ERROR`: Communication error detected

#### MessageType
- `MAGDATA`: Magnetic field data
- `MAGTEMP`: Temperature data
- `MAGID`: Device identification
- `MEMREAD`: Memory read operation
- `MEMWRITE`: Memory write operation
- `MEMCMD`: Memory command
- `OPMODE`: Operation mode
- `STATUS`: Status information

#### OperationMode
- `NORMAL`: Normal operation mode
- `CALIBRATION`: Calibration mode
- `TEST`: Test mode
- `SLEEP`: Sleep mode
- `RESET`: Reset mode

### Data Classes

#### DeviceInfo
- `device_id` (int): Device identifier
- `firmware_version` (str): Firmware version string
- `serial_number` (str): Device serial number
- `calibration_date` (str): Calibration date
- `status` (MagnetometerStatus): Device status

#### MemoryData
- `address` (int): Memory address
- `data` (bytes): Memory data
- `length` (int): Data length
- `checksum` (int): Data checksum

## Examples

### Single Reading
```python
from honeywell_magnetometer import HoneywellMagnetometer

mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
if mag.connect():
    reading = mag.read_data()
    print(f"Reading: {reading.to_dict()}")
    mag.disconnect()
```

### Data Logging
```python
import json
import time

mag = HoneywellMagnetometer("CAN", channel="can0")
if mag.connect():
    mag.start_continuous_reading(interval=1.0)
    
    readings = []
    for _ in range(60):  # Collect for 60 seconds
        reading = mag.get_latest_reading()
        if reading:
            readings.append(reading.to_dict())
        time.sleep(1)
    
    mag.stop_continuous_reading()
    
    # Save to file
    with open("magnetometer_data.json", "w") as f:
        json.dump(readings, f, indent=2)
    
    mag.disconnect()
```

### Calibration
```python
from honeywell_magnetometer import OperationMode

mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
if mag.connect():
    # Set to calibration mode
    if mag.set_operation_mode(OperationMode.CALIBRATION):
        # Collect calibration data
        calibration_readings = []
        mag.start_continuous_reading(interval=0.1)
        
        for _ in range(300):  # 30 seconds of data
            reading = mag.get_latest_reading()
            if reading:
                calibration_readings.append(reading)
            time.sleep(0.1)
        
        mag.stop_continuous_reading()
        
        # Perform calibration
        if mag.calibrate(calibration_readings):
            print("Calibration successful")
            print(f"Offset: {mag.offset}")
            print(f"Scale factors: {mag.scale_factors}")
        
        # Set back to normal mode
        mag.set_operation_mode(OperationMode.NORMAL)
    
    mag.disconnect()
```

## Configuration

### Calibration Parameters

The library supports calibration through the following parameters:

- `calibration_matrix`: 3x3 transformation matrix for soft iron correction
- `offset`: Hard iron offset correction [x, y, z]
- `scale_factors`: Scale factor correction [x, y, z]

### Logging Configuration

```python
from honeywell_magnetometer import setup_logging
import logging

# Setup logging with custom level
setup_logging(level=logging.DEBUG)
```

## Testing

Run the test suite:

```bash
python test_magnetometer.py
```

Run with coverage:

```bash
pytest test_magnetometer.py --cov=honeywell_magnetometer
```

## Hardware Requirements

### CAN Interface
- CAN bus interface (e.g., CANtact, Peak PCAN, etc.)
- Appropriate CAN transceiver
- CAN bus termination resistors

### RS485 Interface
- RS485 to USB converter or serial interface
- RS485 transceiver
- Appropriate cabling and termination

## Protocol Details

The library implements communication protocols based on the ICD specifications from the PDF documents:

### Message Format

All messages follow the format: `[Header][Command][Data][CRC]`

- **Header**: 4 bytes (MessageType, Command, Sequence)
- **Command**: 1 byte command code
- **Data**: Variable length data payload
- **CRC**: 2 bytes CRC-16 checksum

### CAN Protocol (ICD56011974-CAN_Rev)

- **Command ID**: 0x100
- **Data ID**: 0x101
- **Status ID**: 0x102
- **Memory ID**: 0x103
- **Error ID**: 0x104

### RS485 Protocol (ICD56011974-RS_Rev)

- **CMD_MAGDATA**: 0x01 - Read magnetic field data
- **CMD_MAGTEMP**: 0x02 - Read temperature data
- **CMD_MAGID**: 0x03 - Read device information
- **CMD_MEMREAD**: 0x04 - Read EEPROM memory
- **CMD_MEMWRITE**: 0x05 - Write EEPROM memory
- **CMD_MEMCMD**: 0x06 - Memory command (reset)
- **CMD_OPMODE**: 0x07 - Set operation mode
- **CMD_STATUS**: 0x08 - Read status

### Memory Layout

- **Calibration Area**: 0x0000 - 0x0FFF
- **Configuration Area**: 0x1000 - 0x1FFF
- **User Area**: 0x2000 - 0x3FFF

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check interface parameters (port, channel, bitrate)
   - Verify hardware connections
   - Check permissions for serial ports

2. **No Data Received**
   - Verify magnetometer power and status
   - Check communication parameters
   - Review error logs

3. **CRC Validation Errors**
   - Check cable connections
   - Verify baud rate settings
   - Check for electromagnetic interference

4. **Calibration Issues**
   - Ensure sufficient data points (minimum 10)
   - Rotate magnetometer in all directions during calibration
   - Check for magnetic interference
   - Set to calibration mode before starting

5. **Memory Operations Failed**
   - Check memory address ranges
   - Verify write permissions
   - Check for memory protection

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For technical support or questions:
- Check the troubleshooting section
- Review the test examples
- Create an issue with detailed information about your setup

## Changelog

### v1.0.0
- Initial release based on ICD specifications
- CAN and RS485 support with proper message formatting
- CRC-16 validation for message integrity
- Support for all message types (MAGDATA, MAGTEMP, MAGID, MEMREAD, MEMWRITE, MEMCMD, OPMODE)
- EEPROM memory management
- Operation mode control
- Comprehensive status monitoring
- Calibration functionality
- Continuous reading mode
- Comprehensive test suite based on actual protocol specifications