#!/usr/bin/env python3
"""
Quick test script to verify FlatSat Device Simulator installation
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing Python imports...")
    
    try:
        import serial
        print("✓ pyserial: OK")
    except ImportError as e:
        print(f"✗ pyserial: FAILED - {e}")
        return False
    
    try:
        import can
        print("✓ python-can: OK")
    except ImportError as e:
        print(f"✗ python-can: FAILED - {e}")
        return False
    
    try:
        import flask
        print("✓ Flask: OK")
    except ImportError as e:
        print(f"✗ Flask: FAILED - {e}")
        return False
    
    return True

def test_simulator_imports():
    """Test that simulator modules can be imported"""
    print("\nTesting simulator imports...")
    
    try:
        from tcp_receiver import TCPReceiver
        print("✓ tcp_receiver: OK")
    except ImportError as e:
        print(f"✗ tcp_receiver: FAILED - {e}")
        return False
    
    try:
        from device_encoders.ars_encoder import ARSEncoder
        print("✓ ars_encoder: OK")
    except ImportError as e:
        print(f"✗ ars_encoder: FAILED - {e}")
        return False
    
    try:
        from device_encoders.magnetometer_encoder import MagnetometerEncoder
        print("✓ magnetometer_encoder: OK")
    except ImportError as e:
        print(f"✗ magnetometer_encoder: FAILED - {e}")
        return False
    
    try:
        from output_transmitters.serial_transmitter import SerialTransmitterManager
        print("✓ serial_transmitter: OK")
    except ImportError as e:
        print(f"✗ serial_transmitter: FAILED - {e}")
        return False
    
    try:
        from output_transmitters.can_transmitter import CANTransmitterManager
        print("✓ can_transmitter: OK")
    except ImportError as e:
        print(f"✗ can_transmitter: FAILED - {e}")
        return False
    
    return True

def test_config_files():
    """Test that configuration files exist"""
    print("\nTesting configuration files...")
    
    config_files = [
        "config/simulator_config.json",
        "config/simulator_config_with_options.json",
        "config/simulator_config_loopback.json"
    ]
    
    all_exist = True
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✓ {config_file}: OK")
        else:
            print(f"✗ {config_file}: MISSING")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("FlatSat Device Simulator - Installation Test")
    print("=" * 50)
    
    # Test basic imports
    basic_ok = test_imports()
    
    # Test simulator imports
    simulator_ok = test_simulator_imports()
    
    # Test config files
    config_ok = test_config_files()
    
    print("\n" + "=" * 50)
    if basic_ok and simulator_ok and config_ok:
        print("✓ ALL TESTS PASSED - Installation is working correctly!")
        print("\nYou can now run the simulator:")
        print("  python3 flatsat_device_simulator.py --config config/simulator_config.json --enable-ars --listen-port 5001")
        return 0
    else:
        print("✗ SOME TESTS FAILED - Please fix the issues above")
        print("\nTo fix missing dependencies, run:")
        print("  ./fix_dependencies.sh")
        return 1

if __name__ == "__main__":
    sys.exit(main())



