#!/bin/bash
# FlatSat Device Simulator - Quick Start Script

echo "=========================================="
echo "FlatSat Device Simulator - Quick Start"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import serial" 2>/dev/null || {
    echo "Installing pyserial..."
    pip3 install pyserial
}

python3 -c "import can" 2>/dev/null || {
    echo "Installing python-can..."
    pip3 install python-can
}

python3 -c "import flask" 2>/dev/null || {
    echo "Installing flask..."
    pip3 install flask
}

echo "Dependencies OK"
echo ""

# Run installation test
echo "Running installation test..."
python3 test_installation.py
echo ""

# Show available configurations
echo "Available configurations:"
echo "1. Production mode (with real devices) - config/simulator_config.json"
echo "2. Development mode (with loopback cables) - config/simulator_config_loopback.json"
echo "3. Example with all options - config/simulator_config_with_options.json"
echo ""

# Show usage examples
echo "Usage Examples:"
echo ""
echo "1. Test with MATLAB simulator (local development):"
echo "   Terminal 1: python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --listen-port 5001"
echo "   Terminal 2: python3 examples/matlab_tcp_sender.py --enable-ars --target-port 5001 --duration 30"
echo ""
echo "2. Test with real MATLAB system:"
echo "   python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --listen-port 5001"
echo ""
echo "3. Test USB loopback (requires loopback cables):"
echo "   python3 examples/test_usb_loopback.py"
echo ""
echo "4. Demo configuration options:"
echo "   python3 examples/demo_config_options.py --demo both"
echo ""

echo "For detailed instructions, see README.md"
echo "=========================================="
