# Honeywell HG4934 3-Axis Rate Sensor Test Program

This test program provides comprehensive testing capabilities for the Honeywell HG4934 3-axis rate sensor using RS422 communication interface.

## Overview

The Honeywell HG4934 is a space-rated 3-axis rate sensor designed for satellite applications. This test program implements:

- RS422 serial communication interface
- Real-time data acquisition and monitoring
- Comprehensive test suite including built-in tests
- Data logging and analysis capabilities
- Error detection and handling
- Performance and stability testing

## Hardware Requirements

### Rate Sensor
- **Model**: Honeywell HG4934 (68904934-BA60)
- **Interface**: RS422 serial communication
- **Power**: 5V DC (4.5V to 5.5V range)
- **Connector**: 14-pin connector
- **Operating Temperature**: -25°C to +45°C

### Communication Interface
- **Protocol**: RS422 (full-duplex)
- **Baud Rate**: 115200 bps (configurable)
- **Data Format**: 8 data bits, no parity, 1 stop bit
- **Connector Pins**:
  - SER_DATA_OUT_H (Pin 9): RS422 High Output
  - SER_DATA_OUT_L (Pin 10): RS422 Low Output
  - GND: Signal Ground

### System Requirements
- Linux/Windows system with serial port capability
- USB-to-RS422 converter (if needed)
- Python 3.7 or higher

## Software Installation

### Prerequisites
```bash
pip install pyserial
```

### Files
- `test_rate_sensor.py` - Main test program
- `rate_sensor_config.json` - Configuration file
- `README_rate_sensor.md` - This documentation

## Configuration

Edit `rate_sensor_config.json` to configure:

### Serial Communication
```json
{
  "sensor_config": {
    "port": "/dev/ttyUSB0",  // Adjust for your system
    "baud_rate": 115200
  }
}
```

### Data Acquisition
```json
{
  "data_acquisition": {
    "sample_rate_hz": 100,
    "enable_logging": true
  }
}
```

## Usage

### Basic Testing
```bash
python test_rate_sensor.py
```

### Advanced Configuration
```bash
# Custom port
python test_rate_sensor.py --port /dev/ttyUSB1

# Custom baud rate
python test_rate_sensor.py --baud-rate 57600

# Extended test duration
python test_rate_sensor.py --duration 300
```

## Test Suite

The program includes comprehensive testing capabilities:

### 1. Connection Test
- Verifies serial communication
- Tests basic connectivity

### 2. Built-in Test (BIT)
- Runs sensor's internal diagnostics
- Checks sensor health and calibration
- Verifies temperature monitoring

### 3. Data Acquisition Test
- Tests continuous data streaming
- Verifies data integrity
- Measures sample rates

### 4. Communication Test
- Tests command/response reliability
- Measures communication success rate
- Verifies message parsing

### 5. Performance Test
- Analyzes sensor performance characteristics
- Measures sample rate consistency
- Evaluates data stability

### 6. Stability Test
- Long-term stability analysis
- Drift measurement over time
- Temperature compensation verification

## Data Output

### Real-time Display
```
Time: 45.2s | Rate: X=+0.123, Y=-0.045, Z=+0.067 deg/s | Temp: 23.4°C | Status: 0x00
```

### CSV Logging
Data is automatically logged to CSV files with columns:
- `timestamp` - Unix timestamp
- `type` - Data type (rate_data, angle_data, status)
- `x_rate`, `y_rate`, `z_rate` - Angular rates (deg/s)
- `x_angle`, `y_angle`, `z_angle` - Accumulated angles (deg)
- `status` - Sensor status flags
- `temperature` - Sensor temperature (°C)

### Log Files
- Application logs: `rate_sensor_YYYYMMDD_HHMMSS.log`
- Data logs: `rate_sensor_data_YYYYMMDD_HHMMSS.csv`

## Message Protocol

### Message Format
```
[SYNC][TYPE][LENGTH][DATA][CRC]
```

- **SYNC**: 0xAA (synchronization byte)
- **TYPE**: Message type identifier
- **LENGTH**: Data payload length
- **DATA**: Message payload
- **CRC**: CRC-16 checksum (little-endian)

### Message Types
- `0x01`: Rate Data - Angular rate measurements
- `0x02`: Angle Data - Accumulated angle measurements  
- `0x03`: Status - Sensor status and temperature
- `0x04`: Configuration - Configuration commands
- `0x05`: Built-in Test - BIT commands and responses
- `0x06`: Reset - Sensor reset command

## Error Handling

### Common Issues

#### Connection Errors
```
Failed to connect to rate sensor
```
**Solutions**:
- Verify serial port configuration
- Check RS422 cable connections
- Ensure sensor power is applied
- Verify correct baud rate

#### Communication Errors
```
CRC mismatch in received message
```
**Solutions**:
- Check cable integrity
- Verify RS422 termination resistors
- Reduce cable length if possible
- Check for electrical interference

#### Data Quality Issues
```
Performance test failed (sample_rate: 45.2 Hz, std: 0.15 deg/s)
```
**Solutions**:
- Check sensor mounting stability
- Verify temperature is within operating range
- Allow sensor warm-up time
- Check for vibration sources

### Status Flags
- `0x01`: Power OK
- `0x02`: Sensor OK
- `0x04`: Communication OK
- `0x08`: Calibrated
- `0x10`: Warmup Complete
- `0x80`: Error

## Performance Specifications

### Expected Performance
- **Sample Rate**: 50-100 Hz
- **Rate Range**: ±500 deg/s
- **Resolution**: 0.0001 deg/s
- **Stability**: <0.01 deg/s drift per minute
- **Temperature Range**: -25°C to +45°C

### Test Criteria
- **Minimum Sample Rate**: 50 Hz
- **Maximum Standard Deviation**: 0.1 deg/s
- **Maximum Drift**: 0.01 deg/s per minute
- **Communication Success Rate**: >80%

## Troubleshooting

### No Data Received
1. Check power connections
2. Verify RS422 cable connections
3. Confirm correct serial port
4. Check baud rate configuration
5. Run built-in test

### Poor Data Quality
1. Check sensor mounting
2. Verify temperature range
3. Allow adequate warm-up time
4. Check for vibration sources
5. Verify cable shielding

### Communication Failures
1. Check RS422 termination
2. Verify cable length (<10m recommended)
3. Check for electrical interference
4. Verify connector pinout
5. Test with shorter cable

## Safety Considerations

- Ensure proper electrical grounding
- Use shielded cables for RS422 communication
- Follow ESD protection procedures
- Maintain operating temperature limits
- Use non-magnetic mounting hardware

## Support

For technical support or questions:
- Check sensor documentation (DS36134-60)
- Verify hardware connections
- Review configuration settings
- Check log files for error details

## Version History

- **v1.0** - Initial release with comprehensive test suite
  - RS422 communication interface
  - Real-time data acquisition
  - Built-in test support
  - Performance and stability testing
  - CSV data logging
  - Error handling and diagnostics








