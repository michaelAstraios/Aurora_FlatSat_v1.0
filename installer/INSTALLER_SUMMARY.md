# FlatSat Device Simulator - Installer Package

## Package Contents

This installer package contains everything needed to deploy and run the FlatSat Device Simulator on a test machine.

### 📁 Directory Structure
```
installer/
├── 📄 README.md                           # Complete operation guide
├── 📄 FLATSAT_SIMULATOR_PLAN.md          # Technical plan and specifications
├── 📄 DEPLOYMENT_CHECKLIST.md            # Deployment validation checklist
├── 📄 requirements.txt                   # Python dependencies
├── 🔧 install.sh                         # Automated installation script
├── 🚀 quick_start.sh                     # Quick start guide script
│
├── 🐍 Main Application Files
├── 📄 flatsat_device_simulator.py        # Main simulator application
├── 📄 tcp_receiver.py                    # TCP/IP data receiver
├── 📄 packet_logger.py                   # Packet logging system
├── 📄 usb_loopback_tester.py             # USB loopback testing
│
├── 📁 config/                            # Configuration files
├── 📄 simulator_config.json              # Production configuration
├── 📄 simulator_config_loopback.json     # Development configuration
├── 📄 simulator_config_with_options.json # Example with all options
│
├── 📁 device_encoders/                   # Device-specific encoders
├── 📄 ars_encoder.py                     # ARS device encoder
├── 📄 magnetometer_encoder.py            # Magnetometer encoder
├── 📄 reaction_wheel_encoder.py          # Reaction wheel encoder
│
├── 📁 output_transmitters/               # Output protocol handlers
├── 📄 serial_transmitter.py             # Serial port output
├── 📄 can_transmitter.py                 # CAN bus output
├── 📄 tcp_transmitter.py                 # TCP output
│
└── 📁 examples/                          # Test and example scripts
    ├── 📄 matlab_tcp_sender.py           # MATLAB simulator
    ├── 📄 test_usb_loopback.py           # USB loopback test
    └── 📄 demo_config_options.py         # Configuration demo
```

## 🚀 Quick Start

### 1. Installation
```bash
cd installer
chmod +x install.sh quick_start.sh
./install.sh
```

### 2. MATLAB Simulator Testing (Local Development)
```bash
# Terminal 1: Start device simulator
python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --listen-port 5001

# Terminal 2: Start MATLAB simulator
python3 examples/matlab_tcp_sender.py --enable-ars --target-port 5001 --duration 30
```

### 3. Real MATLAB System Testing (Production)
```bash
# Start device simulator (configure MATLAB to send to port 5001)
python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --listen-port 5001
```

## 🔧 Configuration Options

### Development Mode (USB Loopback)
- **Config**: `config/simulator_config_loopback.json`
- **Setup**: USB-to-USB loopback cables
- **Features**: Real-time hex display, data validation

### Production Mode (Real Devices)
- **Config**: `config/simulator_config.json`
- **Setup**: Real devices connected to USB ports
- **Features**: Packet logging to files

## 📊 Supported Devices

| Device | MATLAB Ports | USB Port | Protocol | Data Format |
|--------|-------------|----------|----------|-------------|
| **ARS** | 5000-5005 | `/dev/ttyUSB0` | Serial | Honeywell Rate Sensor |
| **Magnetometer** | 6000-6002 | `/dev/ttyUSB1` | CAN | CAN/RS485 |
| **Reaction Wheel** | 7000-7003 | `/dev/ttyUSB2` | TCP | RWA Telemetry |

## 🔍 Testing & Validation

### USB Loopback Testing
```bash
python3 test_usb_loopback.py
```

### Configuration Demo
```bash
python3 demo_config_options.py --demo both
```

### All Devices Test
```bash
python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --enable-magnetometer --enable-reaction-wheel
```

## 📋 Prerequisites

- **Python**: 3.8 or higher
- **Dependencies**: pyserial, python-can
- **Hardware**: USB ports (`/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/ttyUSB2`)
- **Network**: TCP/IP connectivity for MATLAB communication

## 📚 Documentation

- **README.md**: Complete operation guide
- **DEPLOYMENT_CHECKLIST.md**: Step-by-step deployment validation
- **FLATSAT_SIMULATOR_PLAN.md**: Technical specifications and implementation details

## 🆘 Support

1. **Quick Help**: Run `./quick_start.sh`
2. **Installation Issues**: Check `install.sh` output
3. **Configuration**: Review config files in `config/` directory
4. **Troubleshooting**: See README.md troubleshooting section
5. **Validation**: Use DEPLOYMENT_CHECKLIST.md

## ✅ Ready for Deployment

This package is complete and ready for deployment to test machines. All necessary files, documentation, and scripts are included for both development and production use.

**Package Version**: 1.0  
**Last Updated**: October 2024  
**Compatible With**: Python 3.8+, MATLAB R2019b+
