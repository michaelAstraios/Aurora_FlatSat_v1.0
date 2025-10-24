#!/usr/bin/env python3
"""
TCP Data Dumper Float Conversion Demo

This script demonstrates the float conversion functionality of the modified
TCP data dumper by running both the dumper and a test client.
"""

import subprocess
import time
import threading
import sys
import os

def run_tcp_dumper(ports="5000,5001,5002", endianness="little"):
    """Run the TCP data dumper"""
    cmd = [
        "python3", "tcp_data_dumper.py", 
        "--ports", ports,
        "--hex", "--ascii", "--float",
        "--endianness", endianness
    ]
    
    print(f"🚀 Starting TCP Data Dumper with float conversion...")
    print(f"📡 Ports: {ports}")
    print(f"🔢 Endianness: {endianness}")
    print(f"📊 Output: HEX + ASCII + FLOAT")
    print("-" * 60)
    
    return subprocess.Popen(cmd)

def run_float_test_client(ports="5000,5001,5002", duration=15, endianness="little"):
    """Run the float test client"""
    time.sleep(2)  # Wait for dumper to start
    
    port_list = ports.split(',')
    start_port = int(port_list[0])
    num_ports = len(port_list)
    
    cmd = [
        "python3", "test_float_client.py",
        "--start-port", str(start_port),
        "--num-ports", str(num_ports),
        "--duration", str(duration),
        "--endianness", endianness
    ]
    
    print(f"📤 Starting Float Test Client...")
    print(f"🎯 Target ports: {ports}")
    print(f"⏱️  Duration: {duration} seconds")
    print(f"🔢 Endianness: {endianness}")
    print("-" * 60)
    
    return subprocess.run(cmd)

def demo():
    """Run the complete demo"""
    print("🎬 TCP Data Dumper Float Conversion Demo")
    print("=" * 60)
    print("This demo shows how the TCP data dumper converts 8-byte data")
    print("into floating point values with different endianness options.")
    print("=" * 60)
    
    # Demo 1: Little endian
    print("\n📋 Demo 1: Little Endian Float Conversion")
    print("-" * 50)
    dumper1 = run_tcp_dumper("5000,5001,5002", "little")
    run_float_test_client("5000,5001,5002", 10, "little")
    dumper1.terminate()
    dumper1.wait()
    
    time.sleep(2)
    
    # Demo 2: Big endian
    print("\n📋 Demo 2: Big Endian Float Conversion")
    print("-" * 50)
    dumper2 = run_tcp_dumper("5000,5001,5002", "big")
    run_float_test_client("5000,5001,5002", 10, "big")
    dumper2.terminate()
    dumper2.wait()
    
    time.sleep(2)
    
    # Demo 3: Float only output
    print("\n📋 Demo 3: Float Only Output")
    print("-" * 50)
    dumper3 = subprocess.Popen([
        "python3", "tcp_data_dumper.py", 
        "--ports", "5000,5001,5002",
        "--no-hex", "--no-ascii", "--float",
        "--endianness", "little"
    ])
    run_float_test_client("5000,5001,5002", 8, "little")
    dumper3.terminate()
    dumper3.wait()
    
    print("\n✅ Demo completed!")
    print("\n💡 Key Features Demonstrated:")
    print("   • 8-byte to float conversion")
    print("   • Little and big endian support")
    print("   • Multiple output format combinations")
    print("   • Real-time float value display")
    print("   • Error handling for invalid floats")
    print("\n🔧 Usage Examples:")
    print("   • python3 tcp_data_dumper.py --ports 5000,5001 --float")
    print("   • python3 tcp_data_dumper.py --ports 5000 --float --endianness big")
    print("   • python3 tcp_data_dumper.py --ports 5000 --no-hex --no-ascii --float")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("TCP Data Dumper Float Conversion Demo")
        print("Demonstrates 8-byte to float conversion with different endianness")
        print("\nUsage: python3 demo_float_conversion.py")
        sys.exit(0)
    
    demo()
