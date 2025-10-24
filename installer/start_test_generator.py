#!/usr/bin/env python3
"""
Startup script for Rate Sensor Test Generator

This script provides an easy way to start the Rate Sensor Test Generator
with common configurations.
"""

import subprocess
import sys
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description='Start Rate Sensor Test Generator')
    parser.add_argument('--port', type=int, default=5000, help='API port (default: 5000)')
    parser.add_argument('--serial-port', default='/dev/ttyUSB0', help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--serial-baud', type=int, default=115200, help='Serial baud rate (default: 115200)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--host', default='0.0.0.0', help='API host (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    # Check if the main script exists
    script_path = os.path.join(os.path.dirname(__file__), 'rate_sensor_test_generator.py')
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found")
        sys.exit(1)
    
    # Build command
    cmd = [
        sys.executable, script_path,
        '--host', args.host,
        '--port', str(args.port),
        '--serial-port', args.serial_port,
        '--serial-baud', str(args.serial_baud)
    ]
    
    if args.debug:
        cmd.append('--debug')
    
    print(f"Starting Rate Sensor Test Generator...")
    print(f"API: http://{args.host}:{args.port}")
    print(f"Serial: {args.serial_port} @ {args.serial_baud} baud")
    print(f"Debug: {'ON' if args.debug else 'OFF'}")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == '__main__':
    main()



