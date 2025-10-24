# Rate Sensor Test Generator

A comprehensive REST API-based test generation system for the Honeywell HG4934 3-axis rate sensor. This system allows you to set values for all parameters described in section 3.2.4 of the Honeywell specification and converts JSON data to the proper serial format for transmission over RS422.

## Features

- **REST API Interface**: Easy-to-use HTTP API for setting test parameters
- **JSON Data Structure**: Intuitive JSON format for all rate sensor parameters
- **Protocol Conversion**: Automatic conversion from JSON to Honeywell protocol format
- **Serial Communication**: RS422 serial transmission at 600 Hz
- **Status Word Control**: Individual bit-level control of status words
- **Test Scenarios**: Predefined test scenarios for common use cases
- **Real-time Transmission**: Continuous data transmission with proper timing
- **Comprehensive Documentation**: Built-in API documentation and examples

## Hardware Requirements

- **Rate Sensor**: Honeywell HG4934 (68904934-BA60)
- **Interface**: RS422 serial communication
- **Connector**: 14-pin connector
- **Power**: 5V DC (4.5V to 5.5V range)

## Software Requirements

- Python 3.7 or higher
- Flask web framework
- PySerial for serial communication
- Requests for API testing

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your serial port is available (typically `/dev/ttyUSB0` on Linux)

## Usage

### Starting the Server

```bash
python rate_sensor_test_generator.py
```

The server will start on `http://localhost:5000` by default.

### API Endpoints

#### GET /api/data
Get current rate sensor data

#### POST /api/data
Set rate sensor data parameters
```json
{
  "angular_rate_x": 0.01,
  "angular_rate_y": -0.005,
  "angular_rate_z": 0.02,
  "summed_angle_x": 0.1,
  "summed_angle_y": -0.05,
  "summed_angle_z": 0.2
}
```

#### POST /api/status_words
Set status words with individual bit control
```json
{
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
}
```

#### POST /api/encode
Encode current data to Honeywell protocol format

#### POST /api/transmit
Start serial transmission of current data

#### DELETE /api/transmit
Stop serial transmission

#### GET /api/test_scenarios
Get available test scenarios

#### POST /api/load_scenario/{scenario_name}
Load a predefined test scenario

## Data Format

### Angular Rates
- **Units**: rad/sec
- **Range**: ±500 deg/s (approximately ±8.73 rad/s)
- **Resolution**: 600 × 2^-23 rad/sec/LSB
- **Fields**: `angular_rate_x`, `angular_rate_y`, `angular_rate_z`

### Summed Incremental Angles
- **Units**: rad
- **Resolution**: 2^-27 rad/LSB
- **Fields**: `summed_angle_x`, `summed_angle_y`, `summed_angle_z`

### Status Words

#### Status Word 1 (Table 7)
- **Bit 0-1**: 2-bit counter (00, 01, 10, 11...)
- **Bit 2-3**: BIT mode indicator (0=Power-up, 1=Continuous, 2=Initiated)
- **Bit 4**: Rate Sensor Failed (Latched)
- **Bit 5**: Gyro Failed (Latched)
- **Bit 6**: Reserved
- **Bit 7**: AGC Voltage Failed

#### Status Word 2 (Table 8)
- **Bit 0-7**: Gyro Temperature A (LSB = 1°C)
- **Bit 8**: Motor Bias Voltage Failed
- **Bit 9**: Start Data Flag (0=sensor data, 1=sync data)
- **Bit 10**: Processor Failed
- **Bit 11**: Memory Failed

#### Status Word 3 (Table 9)
- **Bit 8**: Gyro A Start/Run (0=Start, 1=Run)
- **Bit 9**: Gyro B Start/Run
- **Bit 10**: Gyro C Start/Run
- **Bit 11**: Gyro A FDC (0=OK, 1=Failed)
- **Bit 12**: Gyro B FDC
- **Bit 13**: Gyro C FDC
- **Bit 14**: FDC Failed
- **Bit 15**: RS OK (0=OK, 1=Failed)

## Test Scenarios

### Normal Operation
- Typical angular rates
- All systems operational
- Normal temperature

### High Rate Test
- High angular rates
- Stress testing conditions
- Elevated temperature

### Fault Condition
- Zero rates
- Multiple system failures
- High temperature
- All fault flags set

## Message Protocol

The system implements the Honeywell HG4934 message format as specified in section 3.2.4:

```
[SYNC][ANGULAR_RATE_X][ANGULAR_RATE_Y][ANGULAR_RATE_Z][STATUS_1][STATUS_2][STATUS_3][ANGLE_X][ANGLE_Y][ANGLE_Z][CHECKSUM]
```

- **SYNC**: 0xAA (synchronization byte)
- **Angular Rates**: 2 bytes each, little-endian, signed 16-bit
- **Status Words**: 2 bytes each, little-endian, unsigned 16-bit
- **Angles**: 4 bytes each, little-endian, signed 32-bit
- **Checksum**: 2 bytes, little-endian, 16-bit unsigned sum

## Examples

### Basic Usage
```python
import requests

# Set test data
data = {
    'angular_rate_x': 0.1,
    'angular_rate_y': -0.05,
    'angular_rate_z': 0.02
}
response = requests.post('http://localhost:5000/api/data', json=data)

# Encode message
response = requests.post('http://localhost:5000/api/encode')
print(f"Encoded: {response.json()['encoded_data']['hex']}")
```

### Using Test Scenarios
```python
# Load normal operation scenario
response = requests.post('http://localhost:5000/api/load_scenario/normal_operation')

# Start transmission
response = requests.post('http://localhost:5000/api/transmit')

# Stop transmission
response = requests.delete('http://localhost:5000/api/transmit')
```

### Running Examples
```bash
# Start the server
python rate_sensor_test_generator.py

# In another terminal, run examples
python example_test_generator_usage.py
```

## Configuration

### Serial Port Settings
- **Default Port**: `/dev/ttyUSB0`
- **Baud Rate**: 115200
- **Data Bits**: 8
- **Parity**: None
- **Stop Bits**: 1

### API Settings
- **Default Host**: `0.0.0.0`
- **Default Port**: 5000
- **Transmission Rate**: 600 Hz

### Command Line Options
```bash
python rate_sensor_test_generator.py --help
```

Options:
- `--host`: API host address
- `--port`: API port
- `--serial-port`: Serial port for transmission
- `--serial-baud`: Serial baud rate
- `--debug`: Enable debug mode

## Troubleshooting

### Connection Issues
- Verify serial port exists and is accessible
- Check RS422 cable connections
- Ensure sensor power is applied
- Verify correct baud rate

### API Issues
- Check server is running on correct port
- Verify JSON format in requests
- Check API documentation at `http://localhost:5000`

### Transmission Issues
- Verify serial port is not in use by another application
- Check RS422 termination resistors
- Verify cable length (<10m recommended)

## Safety Considerations

- Ensure proper electrical grounding
- Use shielded cables for RS422 communication
- Follow ESD protection procedures
- Maintain operating temperature limits
- Use non-magnetic mounting hardware

## Technical Specifications

Based on Honeywell HG4934 specification DS36134-60:
- **Section 3.2.4**: Serial Data Output Protocol
- **Table 6**: Message Information Field Contents
- **Table 7**: Message Information Status Word 1
- **Table 8**: Message Information Status Word 2
- **Table 9**: Message Information Status Word 3

## Support

For technical support:
- Check Honeywell documentation (DS36134-60)
- Verify hardware connections
- Review configuration settings
- Check server logs for error details

## License

This software is provided for testing and development purposes. Please refer to Honeywell's licensing terms for the sensor specifications.



