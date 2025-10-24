# FlatSat Device Simulator - Implementation Plan

## Overview
Comprehensive application that receives data from MATLAB simulator via TCP/IP and converts it to proper device packet formats for testing satellite systems. Supports ARS (Angular Rate Sensor), Magnetometer, and Reaction Wheel devices with multiple output interfaces.

## Architecture Design

### Core Components
1. **TCP/IP Receiver** - Dual server/client mode with configurable endianness
2. **Device Encoders** - Convert MATLAB data to device-specific packet formats
3. **Output Transmitters** - Serial, CAN, and TCP/IP output interfaces
4. **Main Application** - Device selection and configuration system
5. **Configuration System** - JSON config with CLI overrides

### Data Flow
```
MATLAB Simulator → TCP/IP → Device Encoders → Output Transmitters → Satellite Test System
```

## Implementation Tasks

### ✅ Phase 1: TCP/IP Receiver
- [x] Create TCP/IP receiver with dual server/client mode
- [x] Implement configurable endianness (big/little endian option)
- [x] Handle data boundary detection and packet validation
- [x] Support multiple concurrent connections
- [x] Add timing gap detection and quality monitoring

### ✅ Phase 2: Device Encoders
- [x] **ARS Encoder**: Adapt from rate_sensor_test_generator.py for MATLAB data
  - Convert 12 floats to Honeywell HG4934 format (28 bytes)
  - Handle prime/redundant rates and angles
  - Implement status word generation
- [x] **Magnetometer Encoder**: CAN and RS485 output formats
  - Convert 3 floats to CAN format (big-endian per ICD56011974-CAN)
  - Convert 3 floats to RS485 format (message with CRC per ICD56011974-RS)
- [x] **Reaction Wheel Encoder**: Extract from PDF and create encoder
  - Convert 4 floats to RWA telemetry format per ICD64020011
  - Support Health & Status, Speed, Current telemetry messages

### ✅ Phase 3: Output Transmitters
- [x] **Serial Transmitter**: RS422/RS485 interfaces
  - Configurable baud rate, parity, flow control
  - Queue-based transmission with threading
- [x] **CAN Transmitter**: CAN bus communication
  - Support multiple CAN interfaces (socketcan, etc.)
  - Configurable bitrate and filters
- [x] **TCP Transmitter**: TCP/IP output
  - Target IP/port configuration
  - Automatic reconnection and keepalive

### ✅ Phase 4: Main Application
- [x] Build main application with device selection system
- [x] Implement configuration management
- [x] Add CLI argument parser with overrides
- [x] Create JSON configuration file
- [x] Implement multi-threading for concurrent device processing

### ✅ Phase 5: Testing & Documentation
- [x] Create comprehensive test scripts
- [x] Write detailed documentation (README)
- [x] Create example MATLAB sender scripts (Python and MATLAB)
- [x] Add startup script for easy launching
- [x] Update requirements.txt with dependencies

## Device Specifications

### ARS (Angular Rate Sensor)
- **Input**: 12 floats from MATLAB
  - Ports 5000-5011: Prime/redundant rates and angles
- **Output**: 28-byte Honeywell HG4934 format
- **Protocol**: Sync byte, angular rates, status words, summed angles, CRC
- **Rate**: 600 Hz

### Magnetometer
- **Input**: 3 floats from MATLAB
  - Ports 6000-6002: X, Y, Z magnetic field
- **CAN Output**: Big-endian format per ICD56011974-CAN
- **RS485 Output**: Message with CRC per ICD56011974-RS
- **Rate**: Configurable

### Reaction Wheel
- **Input**: 4 floats from MATLAB
  - Ports 7000-7003: Speed, current, temperature, voltage
- **Output**: RWA telemetry format per ICD64020011
- **Protocol**: Health & Status, Speed, Current telemetry messages
- **Rate**: Configurable

## Configuration Structure

### JSON Configuration
```json
{
  "tcp_mode": "server",
  "matlab_server_ip": "192.168.1.100",
  "matlab_server_port": 5000,
  "devices": {
    "ars": {
      "enabled": true,
      "matlab_ports": [5000, 5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5010, 5011],
      "output_mode": "serial",
      "output_config": {
        "port": "/dev/ttyUSB0",
        "baud_rate": 115200
      },
      "endianness": "little"
    },
    "magnetometer": {
      "enabled": true,
      "matlab_ports": [6000, 6001, 6002],
      "output_mode": "can",
      "output_config": {
        "interface": "socketcan",
        "channel": "can0",
        "bitrate": 500000
      },
      "endianness": "little"
    },
    "reaction_wheel": {
      "enabled": false,
      "matlab_ports": [7000, 7001, 7002, 7003],
      "output_mode": "tcp",
      "output_config": {
        "target_ip": "192.168.1.200",
        "target_port": 8000
      },
      "endianness": "little"
    }
  }
}
```

### CLI Arguments
- `--config`: Configuration file path
- `--enable-ars`, `--enable-mag`, `--enable-rw`: Enable specific devices
- `--ars-output`, `--mag-output`, `--rw-output`: Override output modes
- `--tcp-mode`: Server or client mode
- `--listen-port`: TCP listen port
- `--debug`: Enable debug logging

## File Structure
```
flatsat_device_simulator.py          # Main application
├── tcp_receiver.py                   # MATLAB TCP/IP handler
├── device_encoders/
│   ├── ars_encoder.py               # ARS packet encoding
│   ├── magnetometer_encoder.py      # Mag packet encoding
│   └── reaction_wheel_encoder.py    # RW packet encoding
├── output_transmitters/
│   ├── serial_transmitter.py        # Serial output
│   ├── can_transmitter.py           # CAN output
│   └── tcp_transmitter.py           # TCP output
├── config/
│   └── simulator_config.json         # Master configuration
├── examples/
│   ├── matlab_data_sender.py        # Python test sender
│   └── matlab_simulator_sender.m    # MATLAB test sender
└── start_simulator.py               # Startup script
```

## Key Features

### Multi-Device Support
- ARS (Angular Rate Sensor)
- Magnetometer (Dual Space)
- Reaction Wheel Assembly

### Multiple Output Interfaces
- Serial (RS422/RS485)
- CAN Bus
- TCP/IP

### Flexible Configuration
- JSON configuration file
- CLI argument overrides
- Per-device settings

### Real-time Monitoring
- Data rates and packet counts
- Error rates and quality metrics
- Connection status
- Queue sizes and buffer status

### Robust Error Handling
- Automatic reconnection
- Data validation
- Comprehensive logging
- Graceful degradation

## Usage Examples

### Basic Usage
```bash
# Start with default configuration
python flatsat_device_simulator.py

# Start with custom configuration
python flatsat_device_simulator.py --config config/simulator_config.json
```

### Device-Specific Examples
```bash
# Enable ARS with serial output
python flatsat_device_simulator.py --enable-ars --ars-output serial

# Enable Magnetometer with CAN output
python flatsat_device_simulator.py --enable-mag --mag-output can

# Enable Reaction Wheel with TCP output
python flatsat_device_simulator.py --enable-rw --rw-output tcp
```

### Testing
```bash
# Test with sample data
python examples/matlab_data_sender.py --all-devices

# Test individual components
python device_encoders/ars_encoder.py --test-data
python output_transmitters/serial_transmitter.py --test-data
```

## Dependencies
- Python 3.7+
- pyserial (serial communication)
- python-can (CAN communication)
- Standard library modules (socket, threading, etc.)

## Recent Updates

### Data Duplication Feature (Latest)
**Problem**: MATLAB only sends primary sensor data, not redundant/secondary channels.

**Solution**: 
- Modified ARS encoder to accept 6 or 12 floats
- Added `duplicate_primary_to_redundant` configuration option
- Added `redundant_variation_percent` for realistic sensor differences (default 0.1%)
- Updated configuration system to parse duplication settings

**Configuration Example**:
```json
{
  "devices": {
    "ars": {
      "matlab_ports": [5000, 5001, 5002, 5003, 5004, 5005],  // Only 6 ports for primary
      "duplicate_primary_to_redundant": true,
      "redundant_variation_percent": 0.1  // 0.1% random variation
    }
  }
}
```

### MATLAB TCP Test Sender (Latest)
Created comprehensive test program that simulates MATLAB's exact TCP/IP behavior:
- Sends 8-byte (64-bit) floats
- Maintains precise 10ms spacing between each float
- Supports all devices with command-line options
- Configurable endianness
- Real-time statistics

**Usage**:
```bash
python examples/matlab_tcp_sender.py --enable-ars --duration 60
```

### USB Loopback Testing & Packet Logging System (Latest)
Created flexible testing and logging system with two configuration options:

#### **Option 1: USB Loopback Testing (Development)**
- **USB Port Assignment**: Each device sends to specific USB port
  - ARS: `/dev/ttyUSB0` (115200 baud)
  - Magnetometer: `/dev/ttyUSB1` (115200 baud) 
  - Reaction Wheel: `/dev/ttyUSB2` (115200 baud)
- **Loopback Monitoring**: Monitors received data on looped-back ports
- **Hex Display**: Shows sent/received data in hex format for analysis
- **Data Validation**: Compares sent vs received packets
- **Latency Measurement**: Measures loopback latency in milliseconds

#### **Option 2: Packet Logging (Production)**
- **File Logging**: Logs sent packets to files when real devices are connected
- **Hex Format**: Timestamp | Packet Size | Hex Data format
- **Multi-device Support**: Separate log files for each device
- **Real-time Logging**: Continuous logging during operation

**Files Created**:
- `usb_loopback_tester.py` - USB loopback testing system
- `packet_logger.py` - Packet logging system
- `test_usb_loopback.py` - Loopback demo script
- `demo_config_options.py` - Configuration options demo
- `config/simulator_config_with_options.json` - Example configuration
- Updated `simulator_config.json` - Added both options
- Updated `flatsat_device_simulator.py` - Integrated both systems

**Usage**:
```bash
# Demo both configuration options
python demo_config_options.py --demo both

# Development mode (with loopback cables)
python flatsat_device_simulator.py --config config/simulator_config.json --enable-ars

# Production mode (with real devices)
python flatsat_device_simulator.py --config config/simulator_config.json --enable-ars
```

**Configuration Options**:
```json
{
  "devices": {
    "ars": {
      "_comment_loopback": "For development/testing with USB loopback cables",
      "usb_loopback_enabled": false,
      "usb_loopback_port": "/dev/ttyUSB0",
      
      "_comment_logging": "For production with real devices",
      "log_packets_to_file": true,
      "packet_log_file": "ars_packets.log"
    }
  }
}
```

### Periodic Status Reporting System (Latest)
Added comprehensive status reporting to show data flow in real-time:

#### **Features**:
- **Data Counters**: Track packets received per device
- **Data Rate Calculation**: Shows packets per second
- **Device Information**: Port count, duplication status, output mode
- **Configurable Interval**: Set any reporting interval (default 10 seconds)
- **Per-Device Status**: Each device reports independently
- **No Data Detection**: Shows when no data is received

#### **Status Message Format**:
```
{DEVICE_NAME} Status: {packet_count} packets received, {data_rate} packets/sec, {device_info}
```

#### **Examples**:
```
INFO:__main__:ARS Status: 150 packets received, 15.0 packets/sec, Floats: 6 ports, Duplication: ON
INFO:__main__:MAGNETOMETER Status: 75 packets received, 7.5 packets/sec, Magnetic field data: 3 ports, Output: CAN
INFO:__main__:REACTION_WHEEL Status: 100 packets received, 10.0 packets/sec, Telemetry data: 4 ports, Output: TCP
```

#### **Command Line Option**:
```bash
--status-interval STATUS_INTERVAL    Status report interval in seconds (default: 10)
```

#### **Usage**:
```bash
# Default 10-second intervals
python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --listen-port 5001

# Custom 5-second intervals
python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --listen-port 5001 --status-interval 5

# Custom 30-second intervals
python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --listen-port 5001 --status-interval 30
```

### FTDI RS232 Device Support (Latest)
Enhanced USB loopback testing specifically for RS232 FTDI USB-to-serial converters:

#### **FTDI-Specific Features**:
- **Automatic Port Detection**: Finds FTDI ports (`/dev/ttyUSB*`, `/dev/tty.usbserial*`)
- **DTR/RTS Control**: Proper initialization for FTDI devices
- **Buffer Management**: Resets input/output buffers
- **Flow Control Options**: Configurable RTS/CTS, DSR/DTR, XON/XOFF
- **Enhanced Error Handling**: Better error messages for FTDI issues
- **Port Information**: Reports detailed port configuration

#### **Files Created**:
- `ftdi_usb_loopback_tester.py` - Enhanced FTDI support
- `config/simulator_config_ftdi_loopback.json` - FTDI configuration
- `examples/test_ftdi_loopback.py` - FTDI test script

#### **Usage**:
```bash
# Test FTDI loopback specifically
python3 examples/test_ftdi_loopback.py

# Use FTDI-optimized configuration
python3 flatsat_device_simulator.py --config config/simulator_config_ftdi_loopback.json --enable-ars
```

#### **FTDI Configuration Example**:
```json
{
  "devices": {
    "ars": {
      "usb_loopback_enabled": true,
      "usb_loopback_port": "/dev/ttyUSB0",
      "usb_loopback_config": {
        "baud_rate": 115200,
        "data_bits": 8,
        "stop_bits": 1,
        "parity": "N",
        "timeout": 1.0,
        "write_timeout": 1.0,
        "inter_byte_timeout": 0.1,
        "rtscts": false,
        "dsrdtr": false,
        "xonxoff": false
      }
    }
  }
}
```

### Enhanced Error Handling & Dependencies (Latest)
Improved system robustness and deployment:

#### **Dependency Management**:
- **Quick Fix Script**: `fix_dependencies.sh` for missing packages
- **Installation Test**: `test_installation.py` for verification
- **Enhanced Installer**: Updated `install.sh` with dependency checking
- **Troubleshooting Guide**: Comprehensive error resolution

#### **Files Created/Updated**:
- `fix_dependencies.sh` - Quick dependency fix
- `test_installation.py` - Installation verification
- Updated `install.sh` - Enhanced installation process
- Updated `quick_start.sh` - Dependency checking and testing
- Updated `README.md` - Troubleshooting section

#### **Usage**:
```bash
# Fix missing dependencies
./fix_dependencies.sh

# Test installation
python3 test_installation.py

# Enhanced installation
./install.sh
```

## Status: ✅ COMPLETE + ENHANCED + FLEXIBLE TESTING & LOGGING + STATUS REPORTING + FTDI SUPPORT
All phases have been successfully implemented and tested. The FlatSat Device Simulator is ready for production use with full support for:
- Primary-only data input with realistic redundant channel simulation
- **Flexible Testing Options**: USB loopback testing (development) OR packet logging (production)
- **Periodic Status Reporting**: Real-time data flow monitoring with configurable intervals
- **FTDI RS232 Support**: Enhanced USB loopback testing for FTDI devices
- **Robust Error Handling**: Comprehensive dependency management and troubleshooting
- Hex data display for packet analysis
- Multi-device simultaneous testing
- **Real Device Support**: Packet logging when loopback is not available
