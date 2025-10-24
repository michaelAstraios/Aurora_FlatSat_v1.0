# ARS Socket Reader and Rate Sensor Simulator

A comprehensive socket reader application that listens to ARS sensor data from 12 sequential ports and converts it to simulate the Honeywell Rate Sensor output format. This system provides real-time conversion from ARS sensor data to the Honeywell HG4934 rate sensor protocol.

## Features

- **Multi-Port Socket Listening**: Simultaneously listens on 12 sequential UDP ports
- **Real-Time Data Conversion**: Converts ARS data to Honeywell Rate Sensor format
- **Dual Channel Support**: Handles both Prime and Redundant ARS channels
- **Data Quality Monitoring**: Monitors discrepancies between Prime and Redundant data
- **Status Word Generation**: Generates proper Honeywell status words based on data quality
- **Comprehensive Logging**: Logs both ARS and simulated Rate Sensor data
- **Configurable Output**: JSON logging and console display options

## ARS Sensor Data Format

### Port Mapping
The system listens on 12 sequential ports for the following data:

| Port | Data Type | Description |
|------|-----------|-------------|
| 0 | ARS Prime X | Primary X-axis angular rate |
| 1 | ARS Prime Y | Primary Y-axis angular rate |
| 2 | ARS Prime Z | Primary Z-axis angular rate |
| 3 | ARS Redundant X | Redundant X-axis angular rate |
| 4 | ARS Redundant Y | Redundant Y-axis angular rate |
| 5 | ARS Redundant Z | Redundant Z-axis angular rate |
| 6 | Summed Incremental Prime X | Primary X-axis summed angle |
| 7 | Summed Incremental Prime Y | Primary Y-axis summed angle |
| 8 | Summed Incremental Prime Z | Primary Z-axis summed angle |
| 9 | Summed Incremental Redundant X | Redundant X-axis summed angle |
| 10 | Summed Incremental Redundant Y | Redundant Y-axis summed angle |
| 11 | Summed Incremental Redundant Z | Redundant Z-axis summed angle |

### Data Format
- **Data Type**: 8-byte 64-bit float
- **Byte Order**: Auto-detected (big or little endian)
- **Update Rate**: Every 10ms per port
- **Protocol**: UDP

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure network access to the specified IP address and ports

## Usage

### Basic Usage

```bash
python ars_socket_reader.py
```

### Custom Configuration

```bash
python ars_socket_reader.py --ip 192.168.1.100 --start-port 6000 --num-ports 12
```

### Using Configuration File

```bash
python start_ars_reader.py --config ars_config.json
```

### Command Line Options

```bash
python ars_socket_reader.py --help
```

Options:
- `--ip`: IP address to listen on (default: 0.0.0.0)
- `--start-port`: Starting port number (default: 5000)
- `--num-ports`: Number of ports to listen on (default: 12)
- `--log-file`: Log file to save data (optional)
- `--debug`: Enable debug logging

## Configuration

### Configuration File (ars_config.json)

```json
{
  "ars_config": {
    "ip_address": "0.0.0.0",
    "start_port": 5000,
    "num_ports": 12
  },
  "simulation": {
    "primary_source": "prime",
    "discrepancy_threshold": 0.1,
    "temperature_celsius": 25
  },
  "output": {
    "display_rate_hz": 10,
    "log_file": null,
    "console_output": true
  }
}
```

## Output Format

### Console Output

```
=== ARS to Rate Sensor Simulation ===
Time: 14:30:25
ARS Prime Rates: X=+0.123456, Y=-0.045678, Z=+0.067890
ARS Redundant Rates: X=+0.123450, Y=-0.045680, Z=+0.067885
Simulated Rates: X=+0.123456, Y=-0.045678, Z=+0.067890
Status Words: SW1=0x0001, SW2=0x0019, SW3=0xE000
```

### Log File Format

```json
{
  "timestamp": 1640995825.123,
  "ars_data": {
    "prime_x": 0.123456,
    "prime_y": -0.045678,
    "prime_z": 0.067890,
    "redundant_x": 0.123450,
    "redundant_y": -0.045680,
    "redundant_z": 0.067885,
    "prime_angle_x": 1.234567,
    "prime_angle_y": -0.456789,
    "prime_angle_z": 0.678901,
    "redundant_angle_x": 1.234560,
    "redundant_angle_y": -0.456790,
    "redundant_angle_z": 0.678900,
    "timestamp": 1640995825.123,
    "port_data_count": {"0": 1250, "1": 1249, ...}
  },
  "simulated_data": {
    "angular_rate_x": 0.123456,
    "angular_rate_y": -0.045678,
    "angular_rate_z": 0.067890,
    "summed_angle_x": 1.234567,
    "summed_angle_y": -0.456789,
    "summed_angle_z": 0.678901,
    "status_word_1": 1,
    "status_word_2": 25,
    "status_word_3": 57344,
    "timestamp": 1640995825.123,
    "message_counter": 1250,
    "data_source": "ARS_SIMULATED"
  }
}
```

## Rate Sensor Simulation

### Data Conversion
- **Primary Source**: Uses Prime ARS data as primary source
- **Fallback**: Can implement voting logic between Prime and Redundant
- **Status Words**: Generated based on data quality and discrepancies

### Status Word Generation

#### Status Word 1
- **Counter**: 2-bit counter (0-3)
- **BIT Mode**: Continuous BIT mode
- **Rate Sensor Failed**: Set if no data received
- **Gyro Failed**: Set if Prime/Redundant discrepancy exceeds threshold
- **AGC Voltage**: Always OK in simulation

#### Status Word 2
- **Temperature**: Simulated temperature (25°C default)
- **Motor Bias Voltage**: Always OK in simulation
- **Start Data Flag**: Always sensor data (not sync)
- **Processor**: Always OK in simulation
- **Memory**: Always OK in simulation

#### Status Word 3
- **Gyro Start/Run**: Set based on data availability
- **FDC Status**: Set based on Prime/Redundant discrepancy
- **RS OK**: Set based on overall data quality

## Examples

### Basic Example
```bash
python example_ars_socket_reader.py --example basic
```

### Data Analysis Example
```bash
python example_ars_socket_reader.py --example analysis
```

### Status Word Analysis
```bash
python example_ars_socket_reader.py --example status
```

### Port Mapping Information
```bash
python example_ars_socket_reader.py --example mapping
```

## Data Quality Monitoring

### Discrepancy Detection
- Monitors differences between Prime and Redundant channels
- Configurable threshold for discrepancy warnings
- Automatic status word updates based on data quality

### Data Availability
- Tracks data reception on each port
- Monitors data age and timeout conditions
- Provides summary statistics

### Quality Checks
- Validates 8-byte data format
- Checks for reasonable value ranges
- Monitors update rates

## Troubleshooting

### Connection Issues
- Verify IP address and port accessibility
- Check firewall settings
- Ensure ARS sensor is transmitting data
- Verify port range is available

### Data Issues
- Check data format (8-byte 64-bit float)
- Verify byte order (big vs little endian)
- Monitor data update rates
- Check for data corruption

### Performance Issues
- Monitor system resources
- Check network bandwidth
- Verify socket buffer sizes
- Review logging overhead

## Integration

### With Rate Sensor Test Generator
The simulated output can be used with the Rate Sensor Test Generator:

```python
# Start ARS reader
ars_simulator = ARSRateSensorSimulator('0.0.0.0', 5000)
ars_simulator.start()

# Get simulated data
ars_data = ars_simulator.socket_reader.get_latest_data()
simulated_data = ars_simulator.simulator.convert_ars_to_rate_sensor(ars_data)

# Use with test generator
# (Convert simulated_data to test generator format)
```

### With External Systems
The system can be integrated with external monitoring or control systems through:
- JSON log files
- Real-time data access
- Custom output formats
- API integration

## Performance Specifications

### Expected Performance
- **Data Rate**: 12 ports × 100 Hz = 1200 packets/second
- **Latency**: < 10ms from data reception to output
- **Memory Usage**: Minimal with configurable history buffer
- **CPU Usage**: Low with efficient socket handling

### System Requirements
- Python 3.7 or higher
- Network access to ARS sensor
- Sufficient port range availability
- Minimal system resources

## Safety Considerations

- Ensure proper network security
- Use appropriate firewall rules
- Monitor system resources
- Implement proper error handling
- Follow data retention policies

## Support

For technical support:
- Check ARS sensor documentation
- Verify network connectivity
- Review configuration settings
- Check log files for errors
- Monitor system resources

## Version History

- **v1.0** - Initial release
  - Multi-port UDP socket listening
  - ARS to Rate Sensor data conversion
  - Status word generation
  - Comprehensive logging
  - Configuration file support
  - Example usage scripts


