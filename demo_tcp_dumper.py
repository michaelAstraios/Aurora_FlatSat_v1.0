#!/usr/bin/env python3
"""
TCP Data Dumper Demo

Demonstrates how to use the TCP data dumper and test client together.
Shows different data types and output formats.
"""

import subprocess
import time
import threading
import sys

def run_dumper(port=5000, output_format="hex"):
    """Run the TCP data dumper in a separate process"""
    cmd = ["python3", "tcp_data_dumper.py", "--port", str(port)]
    
    if output_format == "hex":
        cmd.append("--hex")
    elif output_format == "hex_ascii":
        cmd.extend(["--hex", "--ascii"])
    elif output_format == "ascii":
        cmd.extend(["--no-hex", "--ascii"])
    elif output_format == "binary":
        cmd.append("--binary")
    
    print(f"🚀 Starting TCP dumper on port {port} with {output_format} output...")
    return subprocess.Popen(cmd)

def run_test_client(port=5000, data_type="mixed"):
    """Run the test client"""
    time.sleep(2)  # Wait for dumper to start
    
    cmd = ["python3", "test_tcp_client.py", "--port", str(port), "--data-type", data_type]
    print(f"📤 Sending {data_type} test data...")
    return subprocess.run(cmd)

def demo():
    """Run a complete demo"""
    print("🎬 TCP Data Dumper Demo")
    print("=" * 50)
    
    # Demo 1: Mixed data with hex output
    print("\n📋 Demo 1: Mixed data with hexadecimal output")
    print("-" * 40)
    dumper1 = run_dumper(5001, "hex")
    run_test_client(5001, "mixed")
    dumper1.terminate()
    dumper1.wait()
    
    time.sleep(1)
    
    # Demo 2: Float data with hex + ASCII output
    print("\n📋 Demo 2: Float data with hex + ASCII output")
    print("-" * 40)
    dumper2 = run_dumper(5002, "hex_ascii")
    run_test_client(5002, "floats")
    dumper2.terminate()
    dumper2.wait()
    
    time.sleep(1)
    
    # Demo 3: Text data with ASCII output
    print("\n📋 Demo 3: Text data with ASCII output")
    print("-" * 40)
    dumper3 = run_dumper(5003, "ascii")
    run_test_client(5003, "text")
    dumper3.terminate()
    dumper3.wait()
    
    time.sleep(1)
    
    # Demo 4: Binary data with binary output
    print("\n📋 Demo 4: Binary data with binary output")
    print("-" * 40)
    dumper4 = run_dumper(5004, "binary")
    run_test_client(5004, "binary")
    dumper4.terminate()
    dumper4.wait()
    
    print("\n✅ Demo completed!")
    print("\n💡 Usage Tips:")
    print("   • Use --hex --ascii for debugging text protocols")
    print("   • Use --hex for analyzing binary data")
    print("   • Use --binary for bit-level analysis")
    print("   • Perfect for debugging FlatSat simulator data!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("TCP Data Dumper Demo")
        print("Shows different output formats and data types")
        print("\nUsage: python3 demo_tcp_dumper.py")
        sys.exit(0)
    
    demo()
