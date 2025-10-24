# MATLAB Orbital Simulator - Device Format Output

This directory contains MATLAB programs that simulate realistic orbital mechanics and output data in proper device formats for FlatSat hardware testing.

## Overview

The MATLAB Orbital Simulator with Device Format Output provides:

- **Realistic orbital mechanics simulation** with perturbations
- **Proper device data formats** (Honeywell protocols)
- **Multiple communication interfaces** (TCP/IP USB-to-serial, CAN bus)
- **Integration with existing FlatSat infrastructure**

## Files

### MATLAB Programs

1. **`orbital_simulator_device_format.m`** - Main orbital simulator with device format output
2. **`orbital_simulator.m`** - Original orbital simulator (standalone)
3. **`flatsat_orbital_integration.m`** - Integration with existing FlatSat simulator
4. **`matlab_simulator_sender.m`** - Original MATLAB data sender

### Python Bridge

5. **`matlab_bridge.py`** - Python bridge for device format conversion and communication
6. **`start_matlab_bridge.sh`** - Startup script for the Python bridge

### Documentation

7. **`README_orbital_simulator.md`** - Complete documentation for orbital simulator
8. **`README_device_format.md`** - This file

## Quick Start

### 1. Start the Python Bridge

```bash
# For TCP/IP communication
./start_matlab_bridge.sh --protocol tcp --tcp-target-ip 192.168.1.200 --tcp-target-port 8000

# For CAN bus communication
./start_matlab_bridge.sh --protocol can --can-channel can0 --can-bitrate 500000
```

### 2. Run MATLAB Simulator

```matlab
% In MATLAB
orbital_simulator_device_format()
```

## Architecture

```
MATLAB Orbital Simulator
         ↓ (TCP/JSON)
    Python Bridge
         ↓ (Device Format)
    Device Encoders
         ↓ (Protocol Format)
    Output Transmitters
         ↓
    FlatSat Hardware
```

## Device Data Formats

### ARS (Attitude Rate Sensor)
- **Input**: 12 floats from MATLAB (prime + redundant rates + angles)
- **Output**: Honeywell HG4934 protocol format
- **Rate**: 600 Hz
- **Format**: Binary packet with sync byte, angular rates, status words, angles, checksum

### Magnetometer
- **Input**: 3 floats from MATLAB (X, Y, Z magnetic field)
- **Output**: CAN or RS485 format per ICD56011974
- **Rate**: 10 Hz
- **Format**: CAN messages or RS485 packets with CRC

### Reaction Wheel
- **Input**: 4 floats from MATLAB (speed, current, temperature, voltage)
- **Output**: Honeywell RWA protocol per ICD64020011
- **Rate**: 1 Hz
- **Format**: Health & Status telemetry messages

## Communication Protocols

### TCP/IP USB-to-Serial
- **Bridge Port**: 8888 (configurable)
- **Target**: Configurable IP/port
- **Format**: Binary device packets over TCP
- **Use Case**: USB-to-serial converters, Ethernet connections

### CAN Bus
- **Interface**: SocketCAN (Linux)
- **Channels**: can0, can1, etc.
- **Bitrates**: 125k, 250k, 500k, 1M bps
- **Format**: CAN messages with device-specific IDs
- **Use Case**: Direct CAN bus connections

## Configuration

### MATLAB Configuration

Modify these parameters in `orbital_simulator_device_format.m`:

```matlab
% Communication configuration
comm_config.bridge_ip = '127.0.0.1';
comm_config.bridge_port = 8888;
comm_config.protocol = 'tcp';  % 'tcp' or 'can'
comm_config.device_format = true;

% Data rates (Hz)
data_rates.ars = 600;           % ARS data rate
data_rates.magnetometer = 10;   % Magnetometer data rate
data_rates.reaction_wheel = 1;  % Reaction wheel data rate
```

### Python Bridge Configuration

Command line options:

```bash
./start_matlab_bridge.sh [OPTIONS]

Options:
  --protocol PROTOCOL        Output protocol (tcp or can) [default: tcp]
  --tcp-target-ip IP        TCP target IP address [default: 192.168.1.200]
  --tcp-target-port PORT    TCP target port [default: 8000]
  --can-interface IFACE      CAN interface [default: socketcan]
  --can-channel CHANNEL      CAN channel [default: can0]
  --can-bitrate RATE         CAN bitrate [default: 500000]
```

## Usage Examples

### Example 1: TCP/IP Communication

```bash
# Terminal 1: Start bridge
./start_matlab_bridge.sh --protocol tcp --tcp-target-ip 192.168.1.100 --tcp-target-port 9000

# Terminal 2: Run MATLAB simulator
matlab -r "orbital_simulator_device_format()"
```

### Example 2: CAN Bus Communication

```bash
# Setup CAN interface (if needed)
sudo modprobe can can_raw
sudo ip link add dev can0 type vcan
sudo ip link set up can0

# Terminal 1: Start bridge
./start_matlab_bridge.sh --protocol can --can-channel can0 --can-bitrate 500000

# Terminal 2: Run MATLAB simulator
matlab -r "orbital_simulator_device_format()"
```

### Example 3: Custom Configuration

```matlab
% Modify MATLAB configuration
comm_config.bridge_ip = '192.168.1.50';
comm_config.bridge_port = 9999;
comm_config.protocol = 'can';

% Run simulator
orbital_simulator_device_format()
```

## Device Integration

### ARS Integration
The ARS encoder converts MATLAB angular rate data to Honeywell HG4934 format:

```python
# Python bridge automatically handles:
# - Prime and redundant sensor data
# - Status word generation
# - Checksum calculation
# - Protocol formatting
```

### Magnetometer Integration
The magnetometer encoder supports both CAN and RS485 formats:

```python
# CAN format (ICD56011974-CAN)
can_id, data = mag_encoder.process_matlab_data_can([x_field, y_field, z_field])

# RS485 format (ICD56011974-RS)
data = mag_encoder.process_matlab_data_rs485([x_field, y_field, z_field])
```

### Reaction Wheel Integration
The reaction wheel encoder generates health & status telemetry:

```python
# Health & Status telemetry (ICD64020011)
data = rw_encoder.process_matlab_data_health([speed, current, temp, voltage])
```

## Troubleshooting

### Common Issues

1. **"Could not connect to Python bridge"**
   - Ensure the Python bridge is running
   - Check IP address and port configuration
   - Verify firewall settings

2. **"Device encoders not found"**
   - Check that device encoder files exist in `../device_encoders/`
   - Bridge will run in simulation mode if encoders are missing

3. **"CAN interface not found"**
   - Load CAN modules: `sudo modprobe can can_raw`
   - Create virtual CAN: `sudo ip link add dev can0 type vcan`
   - Bring up interface: `sudo ip link set up can0`

4. **"TCP connection failed"**
   - Check target IP and port
   - Verify network connectivity
   - Ensure target device is listening

### Debug Mode

Enable verbose logging:

```bash
./start_matlab_bridge.sh --protocol tcp --verbose
```

### Simulation Mode

The bridge automatically falls back to simulation mode if:
- Device encoders are not available
- Communication interfaces fail to connect
- Hardware is not present

In simulation mode, data is processed and logged but not transmitted.

## Performance

### Data Rates
- **ARS**: 600 Hz (every 1.67 ms)
- **Magnetometer**: 10 Hz (every 100 ms)
- **Reaction Wheel**: 1 Hz (every 1000 ms)

### Bandwidth Requirements
- **ARS**: ~1.2 KB/s (20 bytes × 600 Hz)
- **Magnetometer**: ~0.1 KB/s (10 bytes × 10 Hz)
- **Reaction Wheel**: ~0.02 KB/s (20 bytes × 1 Hz)
- **Total**: ~1.3 KB/s

### Latency
- **MATLAB → Bridge**: < 1 ms (TCP)
- **Bridge → Device**: < 5 ms (TCP) or < 1 ms (CAN)
- **Total**: < 10 ms end-to-end

## Integration with FlatSat

### Existing Infrastructure
The device format output integrates with your existing FlatSat infrastructure:

- **Device Encoders**: Uses existing `ars_encoder.py`, `magnetometer_encoder.py`, `reaction_wheel_encoder.py`
- **Output Transmitters**: Uses existing `tcp_transmitter.py`, `can_transmitter.py`
- **Protocols**: Follows existing ICD specifications

### Hardware Testing
This simulator enables:

- **End-to-end testing** of FlatSat hardware
- **Protocol validation** with real device formats
- **Performance testing** at realistic data rates
- **Integration testing** with existing software

### Data Flow
```
Orbital Simulation → Device Format → Protocol Format → Hardware
     (MATLAB)         (Python)        (Transmitter)    (FlatSat)
```

## Advanced Usage

### Custom Device Formats
To add support for new devices:

1. Create device encoder in `../device_encoders/`
2. Add processing method in `matlab_bridge.py`
3. Update MATLAB simulator to send new device data

### Multiple Devices
The bridge supports multiple devices simultaneously:

```matlab
% Enable/disable devices
output_config.enable_ars = true;
output_config.enable_magnetometer = true;
output_config.enable_reaction_wheel = false;  % Disable RW
```

### Custom Data Rates
Modify data rates in MATLAB:

```matlab
data_rates.ars = 1000;          % 1 kHz ARS
data_rates.magnetometer = 50;   % 50 Hz magnetometer
data_rates.reaction_wheel = 5;  % 5 Hz reaction wheel
```

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review log output from the Python bridge
3. Verify device encoder functionality
4. Test with simulation mode first

The MATLAB Orbital Simulator with Device Format Output provides a complete solution for testing FlatSat hardware with realistic orbital data in proper device formats!


