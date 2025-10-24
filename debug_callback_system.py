#!/usr/bin/env python3
"""
Debug script to test the callback system
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tcp_receiver import TCPReceiver, TCPConfig

def test_callback_system():
    """Test the callback system"""
    print("🔍 Testing callback system...")
    
    # Create TCP receiver config
    config = TCPConfig(
        mode="server",
        ip_address="127.0.0.1",
        port=50038
    )
    
    receiver = TCPReceiver(config)
    
    if receiver.start():
        print("✅ TCP receiver started")
        
        # Configure devices
        device_configs = {
            'ars': {
                'enabled': True,
                'matlab_ports': [50038, 50039, 50040, 50041, 50042, 50043, 50044, 50045, 50046, 50047, 50048, 50049]
            }
        }
        
        receiver.configure_devices(device_configs)
        print("✅ TCP receiver configured")
        
        # Check device_port_mapping
        print(f"🔍 device_port_mapping: {receiver.device_port_mapping}")
        print(f"🔍 device_data: {receiver.device_data}")
        
        # Check MATLAB receiver data
        if receiver.matlab_receiver:
            print(f"🔍 MATLAB receiver device_data: {receiver.matlab_receiver.device_data}")
            print(f"🔍 MATLAB receiver data_callbacks: {list(receiver.matlab_receiver.data_callbacks.keys())}")
        
        # Check data for 5 seconds
        for i in range(5):
            data = receiver.get_data('ars')
            if data:
                non_zero_count = sum(1 for x in data if abs(x) > 1e-10)
                print(f"📊 ARS data: {non_zero_count}/12 non-zero values, sample: {[f'{x:.6f}' for x in data[:3]]}")
            else:
                print(f"❌ No ARS data at iteration {i}")
            time.sleep(1)
        
        receiver.stop()
        print("✅ TCP receiver stopped")
    else:
        print("❌ Failed to start TCP receiver")

if __name__ == "__main__":
    test_callback_system()
