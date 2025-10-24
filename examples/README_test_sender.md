# MATLAB TCP Sender - Test Program Documentation

## Overview
The MATLAB TCP Sender is a comprehensive test program that simulates MATLAB's TCP/IP output behavior. It sends 8-byte (64-bit) float values with precisely timed 10ms spacing between each transmission, allowing you to test the FlatSat Device Simulator locally without MATLAB.

## Features

- **Accurate Timing**: Maintains 10ms spacing between each 8-byte float transmission
- **Multiple Devices**: Supports ARS, Magnetometer, and Reaction Wheel
- **Configurable Endianness**: Big or little endian byte order
- **Realistic Data**: Generates physically realistic sensor data with noise
- **Continuous or Timed**: Run indefinitely or for a specified duration
- **Statistics**: Real-time and final transmission statistics

## Data Generation

### ARS (Angular Rate Sensor)
Sends **6 floats** (primary data only):
1. Prime X angular rate (rad/sec)
2. Prime Y angular rate (rad/sec)
3. Prime Z angular rate (rad/sec)
4. Prime X summed angle (rad)
5. Prime Y summed angle (rad)
6. Prime Z summed angle (rad)

The simulator will duplicate this to redundant channels if configured.

### Magnetometer
Sends **3 floats**:
1. X magnetic field (nT)
2. Y magnetic field (nT)
3. Z magnetic field (nT)

### Reaction Wheel
Sends **4 floats**:
1. Wheel speed (RPM)
2. Motor current (A)
3. Temperature (°C)
4. Bus voltage (V)

## Usage

### Basic Usage

```bash
# Send ARS data only
python matlab_tcp_sender.py --enable-ars

# Send all device data
python matlab_tcp_sender.py --all-devices

# Send magnetometer data for 60 seconds
python matlab_tcp_sender.py --enable-mag --duration 60
```

### Advanced Usage

```bash
# Connect to remote simulator
python matlab_tcp_sender.py --target-ip 192.168.1.100 --target-port 5000 --enable-ars

# Use big-endian format
python matlab_tcp_sender.py --enable-ars --endianness big

# Debug mode with all devices
python matlab_tcp_sender.py --all-devices --log-level DEBUG
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--target-ip` | Target IP address | 127.0.0.1 |
| `--target-port` | Target port | 5000 |
| `--endianness` | Float byte order (little/big) | little |
| `--enable-ars` | Enable ARS data | False |
| `--enable-mag` | Enable magnetometer data | False |
| `--enable-rw` | Enable reaction wheel data | False |
| `--all-devices` | Enable all devices | False |
| `--duration` | Test duration in seconds (0=continuous) | 0 |
| `--log-level` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO |

## Timing Specifications

The program maintains precise timing:
- **10ms spacing** between each 8-byte float
- For ARS (6 floats): Total cycle time = 60ms
- For Magnetometer (3 floats): Total cycle time = 30ms
- For Reaction Wheel (4 floats): Total cycle time = 40ms
- For all devices (13 floats): Total cycle time = 130ms

## Data Characteristics

### ARS Data
- Angular rates: ~0.1 rad/sec with sinusoidal variation
- Summed angles: ~1 rad with sinusoidal variation
- Random noise: ±0.001 rad/sec

### Magnetometer Data
- Typical Earth field values: 25000-40000 nT
- Sinusoidal variations simulating spacecraft rotation
- Realistic noise characteristics

### Reaction Wheel Data
- Wheel speed: 1400-1600 RPM nominal
- Motor current: 2.0-3.0 A
- Temperature: 30-40°C
- Bus voltage: 28.0-29.0 V

## Testing with FlatSat Simulator

### Test Setup 1: Local ARS Testing

Terminal 1 - Start simulator:
```bash
python flatsat_device_simulator.py --enable-ars --debug
```

Terminal 2 - Start test sender:
```bash
python examples/matlab_tcp_sender.py --enable-ars --duration 60
```

### Test Setup 2: All Devices with Data Duplication

Terminal 1 - Start simulator with config:
```bash
python flatsat_device_simulator.py --config config/simulator_config.json
```

Terminal 2 - Start test sender:
```bash
python examples/matlab_tcp_sender.py --all-devices
```

### Test Setup 3: Network Testing

Simulator machine:
```bash
python flatsat_device_simulator.py --tcp-mode server --listen-port 5000 --enable-ars
```

Test machine:
```bash
python examples/matlab_tcp_sender.py --target-ip 192.168.1.100 --target-port 5000 --enable-ars
```

## Statistics Output

The program provides statistics every 10 seconds and final statistics on exit:

```
INFO - Statistics: 6000 packets, 48000 bytes, 100.0 packets/sec, 800.0 bytes/sec
```

- **Packets sent**: Total number of 8-byte floats transmitted
- **Bytes sent**: Total data volume
- **Packets/sec**: Transmission rate
- **Bytes/sec**: Data throughput

## Troubleshooting

### Connection Refused
- Ensure the simulator is running
- Check IP address and port
- Verify firewall settings

### Timing Issues
- The program uses `time.sleep(0.010)` for 10ms spacing
- System timer resolution may affect accuracy
- Use `--log-level DEBUG` to see actual timing

### Data Validation
- Monitor simulator logs for data quality
- Check for NaN or infinity warnings
- Verify endianness matches simulator config

## Integration with MATLAB

This Python test program replicates MATLAB's behavior:

```matlab
% MATLAB equivalent
tcp_client = tcpclient('127.0.0.1', 5000);

% Send ARS primary data
ars_data = [prime_x, prime_y, prime_z, angle_x, angle_y, angle_z];
for i = 1:length(ars_data)
    write(tcp_client, ars_data(i), 'double');  % 8-byte float
    pause(0.010);  % 10ms spacing
end
```

## Performance

- **CPU Usage**: < 1% on modern systems
- **Memory**: ~10 MB
- **Network**: ~800 bytes/sec per device
- **Precision**: Sub-millisecond timing accuracy

## Development

To modify data generation patterns:

1. Edit `generate_ars_primary_data()` for ARS
2. Edit `generate_magnetometer_data()` for magnetometer
3. Edit `generate_reaction_wheel_data()` for RW

Each function returns a list of floats that will be sent with 10ms spacing.

## See Also

- **FlatSat Device Simulator**: Main simulator documentation
- **Configuration Guide**: `README_flatsat_simulator.md`
- **Device Protocols**: See individual device ICDs
