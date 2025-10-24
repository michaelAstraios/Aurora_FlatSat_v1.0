#!/usr/bin/env python3
"""
Startup script for ARS Socket Reader and Rate Sensor Simulator

This script provides an easy way to start the ARS socket reader with
common configurations.
"""

import subprocess
import sys
import argparse
import os
import json

def load_config(config_file: str = 'ars_config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Configuration file {config_file} not found, using defaults")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_file}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Start ARS Socket Reader and Rate Sensor Simulator')
    parser.add_argument('--ip', help='IP address to listen on')
    parser.add_argument('--start-port', type=int, help='Starting port number')
    parser.add_argument('--num-ports', type=int, help='Number of ports to listen on')
    parser.add_argument('--log-file', help='Log file to save data')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--config', default='ars_config.json', help='Configuration file')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set defaults
    ip_address = '0.0.0.0'
    start_port = 5000
    num_ports = 12
    log_file = None
    
    # Override with config file values
    if config:
        ars_config = config.get('ars_config', {})
        ip_address = ars_config.get('ip_address', ip_address)
        start_port = ars_config.get('start_port', start_port)
        num_ports = ars_config.get('num_ports', num_ports)
        
        output_config = config.get('output', {})
        log_file = output_config.get('log_file')
    
    # Override with command line arguments
    if args.ip:
        ip_address = args.ip
    if args.start_port:
        start_port = args.start_port
    if args.num_ports:
        num_ports = args.num_ports
    if args.log_file:
        log_file = args.log_file
    
    # Check if the main script exists
    script_path = os.path.join(os.path.dirname(__file__), 'ars_socket_reader.py')
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found")
        sys.exit(1)
    
    # Build command
    cmd = [
        sys.executable, script_path,
        '--ip', ip_address,
        '--start-port', str(start_port),
        '--num-ports', str(num_ports)
    ]
    
    if log_file:
        cmd.extend(['--log-file', log_file])
    
    if args.debug:
        cmd.append('--debug')
    
    print(f"Starting ARS Socket Reader and Rate Sensor Simulator...")
    print(f"Configuration: {args.config}")
    print(f"Listening on: {ip_address}:{start_port}-{start_port + num_ports - 1}")
    print(f"Log file: {log_file or 'None'}")
    print(f"Debug mode: {'ON' if args.debug else 'OFF'}")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == '__main__':
    main()
