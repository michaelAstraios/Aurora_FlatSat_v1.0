# FlatSat Device Simulator - Deployment Checklist

## Pre-Deployment Checklist

### ✅ Files Included
- [ ] Main application files
  - [ ] `flatsat_device_simulator.py`
  - [ ] `tcp_receiver.py`
  - [ ] `packet_logger.py`
  - [ ] `usb_loopback_tester.py`
- [ ] Device encoders
  - [ ] `device_encoders/ars_encoder.py`
  - [ ] `device_encoders/magnetometer_encoder.py`
  - [ ] `device_encoders/reaction_wheel_encoder.py`
- [ ] Output transmitters
  - [ ] `output_transmitters/serial_transmitter.py`
  - [ ] `output_transmitters/can_transmitter.py`
  - [ ] `output_transmitters/tcp_transmitter.py`
- [ ] Configuration files
  - [ ] `config/simulator_config.json` (production)
  - [ ] `config/simulator_config_loopback.json` (development)
  - [ ] `config/simulator_config_with_options.json` (example)
- [ ] Test and example scripts
  - [ ] `examples/matlab_tcp_sender.py`
  - [ ] `test_usb_loopback.py`
  - [ ] `demo_config_options.py`
- [ ] Documentation
  - [ ] `README.md`
  - [ ] `FLATSAT_SIMULATOR_PLAN.md`
  - [ ] `requirements.txt`
  - [ ] `quick_start.sh`

## Test Machine Setup Checklist

### ✅ System Requirements
- [ ] Python 3.8 or higher installed
- [ ] pip package manager available
- [ ] USB ports available (`/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/ttyUSB2`)
- [ ] Network connectivity for TCP/IP communication

### ✅ Python Dependencies
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify pyserial installation: `python3 -c "import serial"`
- [ ] Verify python-can installation: `python3 -c "import can"`

### ✅ Hardware Setup (Choose One)

#### Development Mode (Loopback Testing)
- [ ] USB-to-USB loopback cables connected
- [ ] `/dev/ttyUSB0` → Loopback
- [ ] `/dev/ttyUSB1` → Loopback
- [ ] `/dev/ttyUSB2` → Loopback
- [ ] Configuration: `usb_loopback_enabled: true`

#### Production Mode (Real Devices)
- [ ] Real ARS device connected to `/dev/ttyUSB0`
- [ ] Real Magnetometer device connected to `/dev/ttyUSB1`
- [ ] Real Reaction Wheel device connected to `/dev/ttyUSB2`
- [ ] Configuration: `log_packets_to_file: true`

## Testing Checklist

### ✅ MATLAB Simulator Testing
- [ ] Run quick start script: `./quick_start.sh`
- [ ] Start device simulator: `python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --listen-port 5001`
- [ ] Start MATLAB simulator: `python3 examples/matlab_tcp_sender.py --enable-ars --target-port 5001 --duration 30`
- [ ] Verify data reception and processing
- [ ] Check console output for statistics

### ✅ USB Loopback Testing (Development)
- [ ] Run loopback test: `python3 test_usb_loopback.py`
- [ ] Verify hex data display
- [ ] Check data validation results
- [ ] Measure loopback latency

### ✅ Real MATLAB System Testing (Production)
- [ ] Configure MATLAB to send data to correct IP/port
- [ ] Start device simulator with production config
- [ ] Verify MATLAB data reception
- [ ] Check packet log files
- [ ] Validate device packet output

### ✅ All Devices Testing
- [ ] Test ARS device: `--enable-ars`
- [ ] Test Magnetometer device: `--enable-magnetometer`
- [ ] Test Reaction Wheel device: `--enable-reaction-wheel`
- [ ] Test all devices simultaneously
- [ ] Verify each device's specific protocol output

## Configuration Validation

### ✅ Network Configuration
- [ ] TCP mode: `server` or `client`
- [ ] MATLAB server IP: `127.0.0.1` (local) or actual MATLAB IP
- [ ] MATLAB server port: `5000` (default) or custom port
- [ ] Listen port matches MATLAB target port

### ✅ Device Configuration
- [ ] ARS: 6 ports (5000-5005) for primary data
- [ ] Magnetometer: 3 ports (6000-6002) for X,Y,Z data
- [ ] Reaction Wheel: 4 ports (7000-7003) for speed,current,temp,voltage
- [ ] Data duplication enabled for ARS if needed
- [ ] Variation percentage set appropriately

### ✅ Output Configuration
- [ ] Serial output: correct baud rate (115200)
- [ ] CAN output: correct bitrate (500000)
- [ ] TCP output: correct target IP/port
- [ ] USB ports match hardware connections

## Troubleshooting Checklist

### ✅ Common Issues
- [ ] Port conflicts: Check `lsof -i :5000`
- [ ] USB port access: Check `ls /dev/ttyUSB*`
- [ ] Permission issues: Check USB port permissions
- [ ] CAN bus setup: Install `can-utils` if needed
- [ ] Firewall: Allow TCP connections on configured ports

### ✅ Debug Mode
- [ ] Enable debug logging: `--debug`
- [ ] Check detailed console output
- [ ] Verify data flow through each component
- [ ] Monitor packet log files if enabled

## Performance Validation

### ✅ Data Rates
- [ ] MATLAB data: ~100 packets/second (10ms spacing)
- [ ] Device packets: Appropriate for each device protocol
- [ ] No data loss or timing issues
- [ ] Consistent data flow

### ✅ Latency
- [ ] TCP reception latency < 1ms
- [ ] Device encoding latency < 1ms
- [ ] USB output latency < 5ms
- [ ] Overall system latency < 10ms

## Documentation Validation

### ✅ User Documentation
- [ ] README.md covers all use cases
- [ ] Configuration examples are correct
- [ ] Command line options documented
- [ ] Troubleshooting section complete

### ✅ Technical Documentation
- [ ] FLATSAT_SIMULATOR_PLAN.md is current
- [ ] Device protocols documented
- [ ] Configuration options explained
- [ ] File structure documented

## Sign-off

### ✅ Deployment Approval
- [ ] All tests passed
- [ ] Documentation complete
- [ ] Configuration validated
- [ ] Hardware setup verified
- [ ] Ready for production use

**Deployment Date:** _______________
**Deployed By:** _______________
**Test Machine:** _______________
**Configuration Used:** _______________
