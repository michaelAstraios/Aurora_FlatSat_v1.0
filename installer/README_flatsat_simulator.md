# FlatSat Device Simulator

A comprehensive application that receives data from MATLAB simulator via TCP/IP and converts it to proper device packet formats for testing satellite systems. Supports ARS (Angular Rate Sensor), Magnetometer, and Reaction Wheel devices with multiple output interfaces.

## Features

### **Core Functionality**
- **Multi-Device Support**: ARS, Magnetometer, and Reaction Wheel
- **Multiple Output Interfaces**: Serial (RS422/RS485), CAN, and TCP/IP
- **Flexible Configuration**: JSON config file with CLI overrides
- **Dual TCP Modes**: Server (listen) or client (connect)
- **Configurable Endianness**: Big/little endian setting per device
- **Data Duplication**: Automatic duplication from primary to redundant channels with optional variation

### **Advanced Features**
- **Status Cycling**: Configurable device status scenarios (normal, warning, error, fault)
- **USB Loopback Testing**: Real-time hex display and data validation for development
- **Packet Logging**: Timestamped hex logging for production environments
- **Error Handling**: Comprehensive error recovery with graceful degradation
- **Performance Monitoring**: Real-time latency and throughput tracking
- **Simulation Mode**: Continues operation when hardware unavailable

### **Testing & Validation**
- **MATLAB Simulator**: Local test sender with 10ms timing
- **Comprehensive Test Suite**: 22 tests covering all components
- **Performance Benchmarks**: Throughput and latency validation
- **Error Recovery Testing**: Fault injection and recovery validation
- **Real-time Monitoring**: Data rates, packet counts, error tracking
- **Comprehensive Logging**: JSON logs with device data and quality metrics

## Architecture

```
flatsat_device_simulator.py          # Main application
├── tcp_receiver.py                   # MATLAB TCP/IP handler
├── device_encoders/
│   ├── ars_encoder.py               # ARS packet encoding
│   ├── magnetometer_encoder.py      # Mag packet encoding
│   ├── reaction_wheel_encoder.py    # RW packet encoding
│   ├── ars_status_manager.py        # ARS status cycling
│   ├── magnetometer_status_manager.py # Mag status cycling
│   └── reaction_wheel_status_manager.py # RW status cycling
├── output_transmitters/
│   ├── serial_transmitter.py        # Serial output
│   ├── can_transmitter.py           # CAN output
│   └── tcp_transmitter.py           # TCP output
├── usb_loopback_tester.py           # USB loopback testing
├── packet_logger.py                 # Packet logging system
├── error_handler.py                 # Error handling & recovery
├── performance_monitor.py           # Performance monitoring
├── test_suite.py                    # Comprehensive test suite
└── config/
    └── simulator_config.json         # Master configuration
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install additional system dependencies:
```bash
# For CAN support
sudo apt-get install python3-can

# For serial support
sudo apt-get install python3-serial
```

## Configuration

### JSON Configuration File

Edit `config/simulator_config.json`:

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

### Data Duplication Feature (NEW)

**Problem**: MATLAB typically only sends primary sensor data, not redundant/secondary channels.

**Solution**: The simulator can automatically duplicate primary data to redundant channels with optional realistic variation.

```json
{
  "devices": {
    "ars": {
      "enabled": true,
      "matlab_ports": [5000, 5001, 5002, 5003, 5004, 5005],  // Only 6 ports for primary data
      "duplicate_primary_to_redundant": true,
      "redundant_variation_percent": 0.1,  // Add 0.1% random variation to redundant
      "output_mode": "serial",
      ...
    }
  }
}
```

**Variation Options**:
- `0.0`: Exact copy (no variation)
- `0.1`: 0.1% random variation (realistic sensor differences)
- `0.5`: 0.5% variation (for fault testing)

### Device Port Mappings

#### With Data Duplication (MATLAB sends primary only)
- **ARS**: 6 ports (5000-5005) for primary rates and angles → Simulator duplicates to 12 values
- **Magnetometer**: 3 ports (6000-6002) for X, Y, Z magnetic field
- **Reaction Wheel**: 4 ports (7000-7003) for speed, current, temperature, voltage

#### Without Data Duplication (MATLAB sends all data)
- **ARS**: 12 ports (5000-5011) for prime/redundant rates and angles
- **Magnetometer**: 3 ports (6000-6002) for X, Y, Z magnetic field
- **Reaction Wheel**: 4 ports (7000-7003) for speed, current, temperature, voltage

## Usage

### Basic Usage

```bash
# Start with default configuration
python flatsat_device_simulator.py

# Start with custom configuration
python flatsat_device_simulator.py --config config/simulator_config.json
```

### Command Line Options

```bash
# Enable specific devices
python flatsat_device_simulator.py --enable-ars --enable-mag

# Override output modes
python flatsat_device_simulator.py --ars-output serial --mag-output can --rw-output tcp

# TCP mode selection
python flatsat_device_simulator.py --tcp-mode server --listen-port 5000

# Debug mode
python flatsat_device_simulator.py --debug --log-file simulator.log
```

### Device-Specific Examples

#### ARS (Angular Rate Sensor)
```bash
# Enable ARS with serial output
python flatsat_device_simulator.py --enable-ars --ars-output serial

# Enable ARS with CAN output
python flatsat_device_simulator.py --enable-ars --ars-output can
```

#### Magnetometer
```bash
# Enable Magnetometer with CAN output
python flatsat_device_simulator.py --enable-mag --mag-output can

# Enable Magnetometer with RS485 output
python flatsat_device_simulator.py --enable-mag --mag-output serial
```

#### Reaction Wheel
```bash
# Enable Reaction Wheel with TCP output
python flatsat_device_simulator.py --enable-rw --rw-output tcp

# Enable Reaction Wheel with serial output
python flatsat_device_simulator.py --enable-rw --rw-output serial
```

## Device Protocols

### ARS (Angular Rate Sensor)
- **Input**: 12 floats from MATLAB (prime/redundant rates and angles)
- **Output**: 28-byte Honeywell HG4934 format
- **Protocol**: Sync byte, angular rates, status words, summed angles, CRC
- **Rate**: 600 Hz

### Magnetometer
- **Input**: 3 floats from MATLAB (X, Y, Z magnetic field)
- **CAN Output**: Big-endian format per ICD56011974-CAN
- **RS485 Output**: Message with CRC per ICD56011974-RS
- **Rate**: Configurable

### Reaction Wheel
- **Input**: 4 floats from MATLAB (speed, current, temperature, voltage)
- **Output**: RWA telemetry format per ICD64020011
- **Protocol**: Health & Status, Speed, Current telemetry messages
- **Rate**: Configurable

## Testing

### Test with MATLAB TCP Sender (Recommended)

The included **MATLAB TCP Sender** allows you to test the simulator locally without MATLAB. It accurately simulates MATLAB's TCP/IP behavior with 10ms spacing between 8-byte floats.

```bash
# Terminal 1: Start the simulator
python flatsat_device_simulator.py --enable-ars --debug

# Terminal 2: Start the test sender
python examples/matlab_tcp_sender.py --enable-ars --duration 60
```

**Full System Test**:
```bash
# Terminal 1: Start simulator with all devices
python flatsat_device_simulator.py --all-devices

# Terminal 2: Send test data for all devices
python examples/matlab_tcp_sender.py --all-devices
```

**Test Options**:
- `--enable-ars`: Send ARS data (6 primary floats)
- `--enable-mag`: Send magnetometer data (3 floats)
- `--enable-rw`: Send reaction wheel data (4 floats)
- `--all-devices`: Enable all devices
- `--duration N`: Run for N seconds (0=continuous)
- `--endianness big`: Use big-endian format

See `examples/README_test_sender.md` for complete documentation.

### Test Individual Encoders

```bash
# Test ARS encoder with duplication
python device_encoders/ars_encoder.py --test-data

# Test Magnetometer encoder
python device_encoders/magnetometer_encoder.py --test-data --output-format can

# Test Reaction Wheel encoder
python device_encoders/reaction_wheel_encoder.py --test-data --telemetry-type health
```

### Test Output Transmitters

```bash
# Test Serial transmitter
python output_transmitters/serial_transmitter.py --port /dev/ttyUSB0 --test-data

# Test CAN transmitter
python output_transmitters/can_transmitter.py --channel can0 --test-data

# Test TCP transmitter
python output_transmitters/tcp_transmitter.py --target-ip 192.168.1.200 --test-data
```

## MATLAB Integration

### Data Format
All MATLAB data should be sent as 8-byte (64-bit) floats over TCP/IP with **10ms spacing** between each float:

- **ARS (with duplication)**: 6 floats (primary only) → Simulator creates 12 values
- **ARS (without duplication)**: 12 floats (primary + redundant)
- **Magnetometer**: 3 floats per message  
- **Reaction Wheel**: 4 floats per message

**Important**: Each 8-byte float must be sent with 10ms spacing to match MATLAB's timing.

### Example MATLAB Sender
See `examples/matlab_simulator_sender.m` for a complete MATLAB implementation that includes proper 10ms timing.

## Troubleshooting

### Common Issues

1. **Serial Port Access Denied**
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```

2. **CAN Interface Not Found**
   ```bash
   sudo ip link set can0 up type can bitrate 500000
   ```

3. **TCP Connection Failed**
   - Check firewall settings
   - Verify IP addresses and ports
   - Ensure MATLAB simulator is running

### Logging

- **Console Output**: Real-time status and errors
- **Log File**: Detailed logging to `flatsat_simulator.log`
- **Debug Mode**: Use `--debug` flag for verbose output

### Status Monitoring

The simulator provides real-time status information:
- Connection status
- Data rates and packet counts
- Error rates and quality metrics
- Queue sizes and buffer status

## Dependencies

- Python 3.7+
- pyserial (serial communication)
- python-can (CAN communication)
- Standard library modules (socket, threading, etc.)

## License

This project is part of the Aurora FlatSat v1.0 system.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Verify configuration settings
4. Test individual components
