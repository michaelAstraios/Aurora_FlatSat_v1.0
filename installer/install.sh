#!/bin/bash
# FlatSat Device Simulator - Installation Script

set -e  # Exit on any error

echo "=========================================="
echo "FlatSat Device Simulator - Installation"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Check if version is sufficient
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')

if [ $PYTHON_MAJOR -lt 3 ] || ([ $PYTHON_MAJOR -eq 3 ] && [ $PYTHON_MINOR -lt 8 ]); then
    echo "ERROR: Python 3.8 or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo "Python version OK"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    echo "Installing individual packages..."
    pip3 install pyserial python-can
fi

echo "Dependencies installed successfully"
echo ""

# Check if packages are working
echo "Verifying installation..."
python3 -c "import serial; print('pyserial: OK')" || {
    echo "ERROR: pyserial installation failed"
    exit 1
}

python3 -c "import can; print('python-can: OK')" || {
    echo "ERROR: python-can installation failed"
    exit 1
}

echo "Installation verification complete"
echo ""

# Check USB ports
echo "Checking USB ports..."
if ls /dev/ttyUSB* 2>/dev/null; then
    echo "USB ports found:"
    ls /dev/ttyUSB*
else
    echo "WARNING: No USB ports found"
    echo "Make sure USB devices are connected"
fi
echo ""

# Make scripts executable
echo "Setting up executable permissions..."
chmod +x quick_start.sh 2>/dev/null || echo "quick_start.sh not found"
echo ""

# Show next steps
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review README.md for detailed instructions"
echo "2. Run ./quick_start.sh for usage examples"
echo "3. Configure your setup:"
echo "   - Development (loopback): config/simulator_config_loopback.json"
echo "   - Production (real devices): config/simulator_config.json"
echo ""
echo "Quick test:"
echo "  Terminal 1: python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --listen-port 5001"
echo "  Terminal 2: python3 examples/matlab_tcp_sender.py --enable-ars --target-port 5001 --duration 10"
echo ""
echo "For support, see DEPLOYMENT_CHECKLIST.md"
echo "=========================================="
