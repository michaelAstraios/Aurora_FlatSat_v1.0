#!/bin/bash
"""
FlatSat Device Simulator - TCP Installer

This script installs the TCP-based ARS system for the FlatSat Device Simulator.
The ARS system has been upgraded from UDP to TCP/IP for improved reliability.
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/flatsat_tcp"
SERVICE_USER="flatsat"
LOG_DIR="/var/log/flatsat_tcp"
CONFIG_DIR="/etc/flatsat_tcp"

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_success "Python $PYTHON_VERSION found"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    print_success "pip3 found"
    
    # Check if ports are available
    for port in {5000..5011}; do
        if netstat -an | grep -q ":$port "; then
            print_warning "Port $port is already in use"
        fi
    done
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Install required packages
    pip3 install --upgrade pip
    pip3 install pyserial python-can
    
    print_success "Python dependencies installed"
}

# Create system directories
create_directories() {
    print_status "Creating system directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$CONFIG_DIR"
    
    print_success "Directories created"
}

# Install files
install_files() {
    print_status "Installing TCP ARS system files..."
    
    # Copy TCP ARS files
    cp ars_tcp_socket_reader*.py "$INSTALL_DIR/"
    cp test_ars_tcp_client.py "$INSTALL_DIR/"
    cp start_ars_tcp_reader.sh "$INSTALL_DIR/"
    
    # Copy configuration files
    cp -r config/* "$CONFIG_DIR/"
    
    # Copy device encoders and transmitters
    cp -r device_encoders "$INSTALL_DIR/"
    cp -r output_transmitters "$INSTALL_DIR/"
    
    # Copy other essential files
    cp flatsat_device_simulator.py "$INSTALL_DIR/"
    cp requirements.txt "$INSTALL_DIR/"
    cp README_TCP_INSTALLER.md "$INSTALL_DIR/"
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR"/*.sh
    chmod +x "$INSTALL_DIR"/*.py
    
    print_success "Files installed to $INSTALL_DIR"
}

# Create system user
create_user() {
    print_status "Creating system user..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        print_success "User $SERVICE_USER created"
    else
        print_warning "User $SERVICE_USER already exists"
    fi
}

# Set permissions
set_permissions() {
    print_status "Setting permissions..."
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR"
    
    # Set permissions
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 644 "$CONFIG_DIR"/*.json
    
    print_success "Permissions set"
}

# Create systemd service
create_service() {
    print_status "Creating systemd service..."
    
    cat > /etc/systemd/system/flatsat-tcp-ars.service << EOF
[Unit]
Description=FlatSat TCP ARS Socket Reader
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start_ars_tcp_reader.sh
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=flatsat-tcp-ars

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    print_success "Systemd service created"
}

# Create configuration symlinks
create_symlinks() {
    print_status "Creating configuration symlinks..."
    
    # Create symlink to default config
    ln -sf "$CONFIG_DIR/simulator_config_tcp.json" "$INSTALL_DIR/simulator_config.json"
    
    print_success "Configuration symlinks created"
}

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    # Test Python imports
    if python3 -c "import socket, struct, threading, time, json, logging" 2>/dev/null; then
        print_success "Python imports successful"
    else
        print_error "Python import test failed"
        exit 1
    fi
    
    # Test TCP ARS reader
    if python3 "$INSTALL_DIR/ars_tcp_socket_reader_endianness.py" --help >/dev/null 2>&1; then
        print_success "TCP ARS reader test successful"
    else
        print_error "TCP ARS reader test failed"
        exit 1
    fi
    
    print_success "Installation test passed"
}

# Create quick start script
create_quickstart() {
    print_status "Creating quick start script..."
    
    cat > "$INSTALL_DIR/quick_start_tcp.sh" << 'EOF'
#!/bin/bash
"""
Quick Start Script for FlatSat TCP ARS System
"""

echo "=========================================="
echo "FlatSat TCP ARS System - Quick Start"
echo "=========================================="
echo ""

# Check if service is running
if systemctl is-active --quiet flatsat-tcp-ars; then
    echo "✅ TCP ARS service is running"
else
    echo "⚠️  TCP ARS service is not running"
    echo "Starting service..."
    sudo systemctl start flatsat-tcp-ars
    sleep 2
    
    if systemctl is-active --quiet flatsat-tcp-ars; then
        echo "✅ TCP ARS service started successfully"
    else
        echo "❌ Failed to start TCP ARS service"
        exit 1
    fi
fi

echo ""
echo "🔍 Service Status:"
systemctl status flatsat-tcp-ars --no-pager -l

echo ""
echo "📊 Port Status:"
netstat -an | grep -E ":(500[0-9]|501[0-1]) " | head -5

echo ""
echo "🧪 To test the system:"
echo "   python3 test_ars_tcp_client.py --duration 10"
echo ""
echo "📝 To view logs:"
echo "   journalctl -u flatsat-tcp-ars -f"
echo ""
echo "🛑 To stop the service:"
echo "   sudo systemctl stop flatsat-tcp-ars"
EOF

    chmod +x "$INSTALL_DIR/quick_start_tcp.sh"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/quick_start_tcp.sh"
    
    print_success "Quick start script created"
}

# Main installation function
main() {
    echo "=========================================="
    echo "FlatSat Device Simulator - TCP Installer"
    echo "=========================================="
    echo ""
    
    check_root
    check_requirements
    install_dependencies
    create_directories
    install_files
    create_user
    set_permissions
    create_service
    create_symlinks
    test_installation
    create_quickstart
    
    echo ""
    print_success "Installation completed successfully!"
    echo ""
    echo "📁 Installation Directory: $INSTALL_DIR"
    echo "📁 Configuration Directory: $CONFIG_DIR"
    echo "📁 Log Directory: $LOG_DIR"
    echo "👤 Service User: $SERVICE_USER"
    echo ""
    echo "🚀 Quick Start:"
    echo "   sudo systemctl start flatsat-tcp-ars"
    echo "   sudo systemctl enable flatsat-tcp-ars"
    echo ""
    echo "🧪 Test Installation:"
    echo "   cd $INSTALL_DIR"
    echo "   python3 test_ars_tcp_client.py --duration 10"
    echo ""
    echo "📝 View Logs:"
    echo "   journalctl -u flatsat-tcp-ars -f"
    echo ""
    echo "🛑 Stop Service:"
    echo "   sudo systemctl stop flatsat-tcp-ars"
    echo ""
    echo "✅ TCP-based ARS system is ready!"
}

# Run main function
main "$@"
