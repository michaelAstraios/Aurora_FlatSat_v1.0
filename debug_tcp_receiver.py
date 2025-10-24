#!/usr/bin/env python3
"""
Debug script to check TCP receiver data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tcp_receiver import TCPReceiver, TCPConfig

def test_tcp_receiver():
    """Test if TCP receiver is storing data"""
    print("🔍 Testing TCP receiver data storage...")
    
    # Create a simple TCP receiver config
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
        
        # Check data for 10 seconds
        import time
        for i in range(10):
            data = receiver.get_data('ars')
            if data:
                print(f"📊 ARS data: {[f'{x:.6f}' for x in data[:6]]}...")  # Show first 6 values
            else:
                print(f"❌ No ARS data at iteration {i}")
            time.sleep(1)
        
        receiver.stop()
        print("✅ TCP receiver stopped")
    else:
        print("❌ Failed to start TCP receiver")

if __name__ == "__main__":
    test_tcp_receiver()
