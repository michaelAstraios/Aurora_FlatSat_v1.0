#!/usr/bin/env python3
"""
Multi-Port TCP Data Dumper Demo

Demonstrates the multi-port TCP data dumper with the requested format:
"port:Timestamp: dataHex    dataAscii"
"""

import subprocess
import time
import threading
import sys

def run_dumper(port_spec, output_format="hex_ascii"):
    """Run the multi-port TCP data dumper"""
    cmd = ["python3", "tcp_data_dumper.py", "--ports", port_spec]
    
    if output_format == "hex_ascii":
        cmd.extend(["--hex", "--ascii"])
    elif output_format == "hex":
        cmd.append("--hex")
    elif output_format == "ascii":
        cmd.extend(["--no-hex", "--ascii"])
    
    print(f"🚀 Starting multi-port TCP dumper on ports {port_spec}...")
    return subprocess.Popen(cmd)

def run_test_client(ports, data_type="mixed", duration=3):
    """Run the multi-port test client"""
    time.sleep(2)  # Wait for dumper to start
    
    port_list = ','.join(map(str, ports))
    cmd = ["python3", "test_multi_port_client.py", "--ports", port_list, 
           "--data-type", data_type, "--duration", str(duration)]
    
    print(f"📤 Sending {data_type} test data to ports {port_list}...")
    return subprocess.run(cmd)

def demo():
    """Run a complete demo"""
    print("🎬 Multi-Port TCP Data Dumper Demo")
    print("=" * 60)
    print("Format: port:Timestamp: dataHex    dataAscii")
    print("=" * 60)
    
    # Demo 1: ARS ports (5000-5002) with mixed data
    print("\n📋 Demo 1: ARS Ports (5000-5002) with Mixed Data")
    print("-" * 50)
    dumper1 = run_dumper("5000,5001,5002", "hex_ascii")
    run_test_client([5000, 5001, 5002], "mixed", 3)
    dumper1.terminate()
    dumper1.wait()
    
    time.sleep(1)
    
    # Demo 2: FlatSat Simulator Ports with Float Data
    print("\n📋 Demo 2: FlatSat Simulator Ports with Float Data")
    print("-" * 50)
    dumper2 = run_dumper("5000,6000,7000", "hex_ascii")
    run_test_client([5000, 6000, 7000], "floats", 3)
    dumper2.terminate()
    dumper2.wait()
    
    time.sleep(1)
    
    # Demo 3: Port Range with Text Data
    print("\n📋 Demo 3: Port Range (5000-5003) with Text Data")
    print("-" * 50)
    dumper3 = run_dumper("5000-5003", "hex_ascii")
    run_test_client([5000, 5001, 5002, 5003], "text", 3)
    dumper3.terminate()
    dumper3.wait()
    
    print("\n✅ Demo completed!")
    print("\n💡 Usage Examples:")
    print("   • ARS debugging: python3 tcp_data_dumper.py --ports 5000,5001,5002,5003,5004,5005")
    print("   • Magnetometer: python3 tcp_data_dumper.py --ports 6000,6001,6002")
    print("   • Reaction Wheel: python3 tcp_data_dumper.py --ports 7000,7001,7002,7003")
    print("   • Port range: python3 tcp_data_dumper.py --port-range 5000-5010")
    print("   • Perfect for debugging FlatSat simulator data!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Multi-Port TCP Data Dumper Demo")
        print("Shows the requested format: port:Timestamp: dataHex    dataAscii")
        print("\nUsage: python3 demo_multi_port_dumper.py")
        sys.exit(0)
    
    demo()
