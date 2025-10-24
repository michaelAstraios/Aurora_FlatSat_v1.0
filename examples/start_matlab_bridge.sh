#!/bin/bash
# MATLAB Orbital Simulator Bridge Startup Script
# 
# This script starts the Python bridge that handles device format conversion
# and communication between MATLAB orbital simulator and FlatSat hardware.

set -e

# Configuration
BRIDGE_IP="127.0.0.1"
BRIDGE_PORT="8888"
PROTOCOL="tcp"  # or "can"
TCP_TARGET_IP="192.168.1.200"
TCP_TARGET_PORT="8000"
CAN_INTERFACE="socketcan"
CAN_CHANNEL="can0"
CAN_BITRATE="500000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MATLAB Orbital Simulator Bridge${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 is not installed or not in PATH${NC}"
    exit 1
fi

# Check if required Python packages are available
echo -e "${YELLOW}Checking Python dependencies...${NC}"
python3 -c "import json, socket, threading, logging, queue, time, sys, os" 2>/dev/null || {
    echo -e "${RED}Error: Required Python packages not available${NC}"
    echo "Please install: json, socket, threading, logging, queue, time, sys, os"
    exit 1
}

# Check if device encoders are available
if [ ! -f "../device_encoders/ars_encoder.py" ]; then
    echo -e "${YELLOW}Warning: ARS encoder not found - running in simulation mode${NC}"
fi

if [ ! -f "../device_encoders/magnetometer_encoder.py" ]; then
    echo -e "${YELLOW}Warning: Magnetometer encoder not found - running in simulation mode${NC}"
fi

if [ ! -f "../device_encoders/reaction_wheel_encoder.py" ]; then
    echo -e "${YELLOW}Warning: Reaction wheel encoder not found - running in simulation mode${NC}"
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --protocol)
            PROTOCOL="$2"
            shift 2
            ;;
        --tcp-target-ip)
            TCP_TARGET_IP="$2"
            shift 2
            ;;
        --tcp-target-port)
            TCP_TARGET_PORT="$2"
            shift 2
            ;;
        --can-interface)
            CAN_INTERFACE="$2"
            shift 2
            ;;
        --can-channel)
            CAN_CHANNEL="$2"
            shift 2
            ;;
        --can-bitrate)
            CAN_BITRATE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --protocol PROTOCOL        Output protocol (tcp or can) [default: tcp]"
            echo "  --tcp-target-ip IP        TCP target IP address [default: 192.168.1.200]"
            echo "  --tcp-target-port PORT    TCP target port [default: 8000]"
            echo "  --can-interface IFACE      CAN interface [default: socketcan]"
            echo "  --can-channel CHANNEL      CAN channel [default: can0]"
            echo "  --can-bitrate RATE         CAN bitrate [default: 500000]"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --protocol tcp --tcp-target-ip 192.168.1.100 --tcp-target-port 9000"
            echo "  $0 --protocol can --can-channel can1 --can-bitrate 1000000"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Display configuration
echo -e "${GREEN}Configuration:${NC}"
echo "  Bridge IP: $BRIDGE_IP"
echo "  Bridge Port: $BRIDGE_PORT"
echo "  Protocol: $PROTOCOL"

if [ "$PROTOCOL" = "tcp" ]; then
    echo "  TCP Target: $TCP_TARGET_IP:$TCP_TARGET_PORT"
elif [ "$PROTOCOL" = "can" ]; then
    echo "  CAN Interface: $CAN_INTERFACE"
    echo "  CAN Channel: $CAN_CHANNEL"
    echo "  CAN Bitrate: $CAN_BITRATE"
else
    echo -e "${RED}Error: Invalid protocol '$PROTOCOL'. Use 'tcp' or 'can'${NC}"
    exit 1
fi

echo ""

# Check CAN interface if using CAN protocol
if [ "$PROTOCOL" = "can" ]; then
    echo -e "${YELLOW}Checking CAN interface...${NC}"
    
    if [ "$CAN_INTERFACE" = "socketcan" ]; then
        if ! ip link show "$CAN_CHANNEL" &> /dev/null; then
            echo -e "${YELLOW}Warning: CAN interface '$CAN_CHANNEL' not found${NC}"
            echo "You may need to:"
            echo "  1. Load CAN modules: sudo modprobe can && sudo modprobe can_raw"
            echo "  2. Create virtual CAN: sudo ip link add dev $CAN_CHANNEL type vcan"
            echo "  3. Bring up interface: sudo ip link set up $CAN_CHANNEL"
            echo ""
            echo -e "${YELLOW}Continuing in simulation mode...${NC}"
        else
            echo -e "${GREEN}CAN interface '$CAN_CHANNEL' found${NC}"
        fi
    fi
fi

# Start the bridge
echo -e "${GREEN}Starting MATLAB Orbital Simulator Bridge...${NC}"
echo ""

# Build command line arguments
ARGS="--listen-ip $BRIDGE_IP --listen-port $BRIDGE_PORT --protocol $PROTOCOL"

if [ "$PROTOCOL" = "tcp" ]; then
    ARGS="$ARGS --tcp-target-ip $TCP_TARGET_IP --tcp-target-port $TCP_TARGET_PORT"
elif [ "$PROTOCOL" = "can" ]; then
    ARGS="$ARGS --can-interface $CAN_INTERFACE --can-channel $CAN_CHANNEL --can-bitrate $CAN_BITRATE"
fi

# Start the Python bridge
echo -e "${BLUE}Running: python3 matlab_bridge.py $ARGS${NC}"
echo ""

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}Shutting down bridge...${NC}"; exit 0' INT

# Run the bridge
python3 matlab_bridge.py $ARGS --verbose


