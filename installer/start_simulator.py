#!/usr/bin/env python3
"""
Startup script for FlatSat Device Simulator

Provides easy startup options for different configurations.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='FlatSat Device Simulator Startup')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--enable-ars', action='store_true', help='Enable ARS device')
    parser.add_argument('--enable-mag', action='store_true', help='Enable Magnetometer device')
    parser.add_argument('--enable-rw', action='store_true', help='Enable Reaction Wheel device')
    parser.add_argument('--all-devices', action='store_true', help='Enable all devices')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with sample data')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    simulator_script = script_dir / "flatsat_device_simulator.py"
    
    if not simulator_script.exists():
        print(f"Error: Simulator script not found at {simulator_script}")
        sys.exit(1)
    
    # Build command
    cmd = [sys.executable, str(simulator_script)]
    
    # Add configuration file
    if args.config:
        cmd.extend(['--config', args.config])
    else:
        # Use default config
        default_config = script_dir / "config" / "simulator_config.json"
        if default_config.exists():
            cmd.extend(['--config', str(default_config)])
    
    # Add device enable flags
    if args.all_devices:
        cmd.extend(['--enable-ars', '--enable-mag', '--enable-rw'])
    else:
        if args.enable_ars:
            cmd.append('--enable-ars')
        if args.enable_mag:
            cmd.append('--enable-mag')
        if args.enable_rw:
            cmd.append('--enable-rw')
    
    # Add debug flag
    if args.debug:
        cmd.append('--debug')
    
    # Add test mode
    if args.test_mode:
        cmd.append('--tcp-mode')
        cmd.append('server')
        cmd.append('--listen-port')
        cmd.append('5000')
    
    print(f"Starting FlatSat Device Simulator...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        # Run the simulator
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Simulator exited with error code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nSimulator interrupted by user")
        sys.exit(0)

if __name__ == '__main__':
    main()
