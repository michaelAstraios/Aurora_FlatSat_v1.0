#!/bin/bash
"""
Start ARS TCP Socket Reader

This script starts the ARS TCP Socket Reader with automatic endianness detection.
It provides better reliability and connection management compared to the UDP version.
"""

# Configuration
IP_ADDRESS="127.0.0.1"
START_PORT=5000
NUM_PORTS=12
LOG_LEVEL="INFO"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ip)
            IP_ADDRESS="$2"
            shift 2
            ;;
        --start-port)
            START_PORT="$2"
            shift 2
            ;;
        --num-ports)
            NUM_PORTS="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --ip IP_ADDRESS      IP address to listen on (default: 127.0.0.1)"
            echo "  --start-port PORT    Starting port number (default: 5000)"
            echo "  --num-ports NUM      Number of ports to listen on (default: 12)"
            echo "  --log-level LEVEL    Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Python script exists
SCRIPT_PATH="ars_tcp_socket_reader_endianness.py"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: $SCRIPT_PATH not found"
    echo "Please ensure you're running this script from the correct directory"
    exit 1
fi

# Display configuration
echo "=========================================="
echo "ARS TCP Socket Reader with Endianness Detection"
echo "=========================================="
echo "IP Address: $IP_ADDRESS"
echo "Port Range: $START_PORT - $((START_PORT + NUM_PORTS - 1))"
echo "Log Level: $LOG_LEVEL"
echo "=========================================="
echo ""

# Start the TCP socket reader
echo "Starting ARS TCP Socket Reader..."
python3 "$SCRIPT_PATH" \
    --ip "$IP_ADDRESS" \
    --start-port "$START_PORT" \
    --num-ports "$NUM_PORTS" \
    --log-level "$LOG_LEVEL"

echo ""
echo "ARS TCP Socket Reader stopped."
