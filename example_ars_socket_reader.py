#!/usr/bin/env python3
"""
Example Usage of ARS Socket Reader and Rate Sensor Simulator

This script demonstrates how to use the ARS socket reader to simulate
the Honeywell Rate Sensor output format.
"""

import time
import json
import argparse
from ars_socket_reader import ARSRateSensorSimulator, SocketReader, RateSensorSimulator

def example_basic_usage():
    """Example: Basic usage of the ARS socket reader"""
    print("=== Basic ARS Socket Reader Example ===")
    
    # Create simulator with default settings
    simulator = ARSRateSensorSimulator('0.0.0.0', 5000)
    
    try:
        print("Starting ARS to Rate Sensor Simulator...")
        if simulator.start():
            print("Simulator started successfully!")
            print("Waiting for ARS data on ports 5000-5011...")
            print("Press Ctrl+C to stop")
            
            # Keep running
            while True:
                time.sleep(1.0)
        else:
            print("Failed to start simulator")
            
    except KeyboardInterrupt:
        print("\nStopping simulator...")
        simulator.stop()
        print("Simulator stopped")

def example_custom_configuration():
    """Example: Custom configuration"""
    print("\n=== Custom Configuration Example ===")
    
    # Custom configuration
    ip_address = '192.168.1.100'  # Specific IP
    start_port = 6000             # Different port range
    log_file = 'ars_simulation.log'
    
    simulator = ARSRateSensorSimulator(ip_address, start_port, log_file)
    
    try:
        print(f"Starting simulator on {ip_address}:{start_port}-{start_port + 11}")
        print(f"Logging to: {log_file}")
        
        if simulator.start():
            print("Custom configuration simulator started!")
            time.sleep(5)  # Run for 5 seconds as example
        else:
            print("Failed to start simulator")
            
    except KeyboardInterrupt:
        print("\nStopping simulator...")
        simulator.stop()

def example_data_analysis():
    """Example: Data analysis and monitoring"""
    print("\n=== Data Analysis Example ===")
    
    simulator = ARSRateSensorSimulator('0.0.0.0', 5000)
    
    try:
        if simulator.start():
            print("Starting data analysis...")
            
            # Monitor for 30 seconds
            start_time = time.time()
            data_samples = []
            
            while time.time() - start_time < 30:
                # Get latest data
                ars_data = simulator.socket_reader.get_latest_data()
                simulated_data = simulator.simulator.convert_ars_to_rate_sensor(ars_data)
                
                # Store sample
                sample = {
                    'timestamp': time.time(),
                    'ars_prime_rates': [ars_data.prime_x, ars_data.prime_y, ars_data.prime_z],
                    'ars_redundant_rates': [ars_data.redundant_x, ars_data.redundant_y, ars_data.redundant_z],
                    'simulated_rates': [simulated_data.angular_rate_x, simulated_data.angular_rate_y, simulated_data.angular_rate_z],
                    'status_words': [simulated_data.status_word_1, simulated_data.status_word_2, simulated_data.status_word_3]
                }
                data_samples.append(sample)
                
                time.sleep(0.1)
            
            # Analyze collected data
            print(f"\nCollected {len(data_samples)} data samples")
            
            if data_samples:
                # Calculate statistics
                prime_x_values = [s['ars_prime_rates'][0] for s in data_samples]
                prime_y_values = [s['ars_prime_rates'][1] for s in data_samples]
                prime_z_values = [s['ars_prime_rates'][2] for s in data_samples]
                
                print(f"Prime X: min={min(prime_x_values):.6f}, max={max(prime_x_values):.6f}")
                print(f"Prime Y: min={min(prime_y_values):.6f}, max={max(prime_y_values):.6f}")
                print(f"Prime Z: min={min(prime_z_values):.6f}, max={max(prime_z_values):.6f}")
                
                # Check for discrepancies
                discrepancies = []
                for sample in data_samples:
                    prime = sample['ars_prime_rates']
                    redundant = sample['ars_redundant_rates']
                    diff_x = abs(prime[0] - redundant[0])
                    diff_y = abs(prime[1] - redundant[1])
                    diff_z = abs(prime[2] - redundant[2])
                    max_diff = max(diff_x, diff_y, diff_z)
                    discrepancies.append(max_diff)
                
                if discrepancies:
                    avg_discrepancy = sum(discrepancies) / len(discrepancies)
                    max_discrepancy = max(discrepancies)
                    print(f"Prime/Redundant discrepancy: avg={avg_discrepancy:.6f}, max={max_discrepancy:.6f}")
                
                # Save analysis results
                analysis_results = {
                    'collection_time': 30,
                    'sample_count': len(data_samples),
                    'prime_x_range': [min(prime_x_values), max(prime_x_values)],
                    'prime_y_range': [min(prime_y_values), max(prime_y_values)],
                    'prime_z_range': [min(prime_z_values), max(prime_z_values)],
                    'avg_discrepancy': avg_discrepancy if discrepancies else 0,
                    'max_discrepancy': max_discrepancy if discrepancies else 0
                }
                
                with open('ars_analysis_results.json', 'w') as f:
                    json.dump(analysis_results, f, indent=2)
                
                print("Analysis results saved to ars_analysis_results.json")
            
        else:
            print("Failed to start simulator")
            
    except KeyboardInterrupt:
        print("\nStopping analysis...")
        simulator.stop()

def example_port_mapping():
    """Example: Understanding port mapping"""
    print("\n=== Port Mapping Example ===")
    
    print("ARS Sensor Port Mapping:")
    print("Port 0: ARS Prime X")
    print("Port 1: ARS Prime Y") 
    print("Port 2: ARS Prime Z")
    print("Port 3: ARS Redundant X")
    print("Port 4: ARS Redundant Y")
    print("Port 5: ARS Redundant Z")
    print("Port 6: Summed Incremental Prime X")
    print("Port 7: Summed Incremental Prime Y")
    print("Port 8: Summed Incremental Prime Z")
    print("Port 9: Summed Incremental Redundant X")
    print("Port 10: Summed Incremental Redundant Y")
    print("Port 11: Summed Incremental Redundant Z")
    print()
    print("Data Format: 8-byte 64-bit float (big or little endian)")
    print("Update Rate: Every 10ms per port")
    print("Simulation Output: Honeywell Rate Sensor format")

def example_status_word_analysis():
    """Example: Status word analysis"""
    print("\n=== Status Word Analysis Example ===")
    
    simulator = ARSRateSensorSimulator('0.0.0.0', 5000)
    
    try:
        if simulator.start():
            print("Monitoring status words...")
            
            status_samples = []
            start_time = time.time()
            
            while time.time() - start_time < 10:  # Monitor for 10 seconds
                ars_data = simulator.socket_reader.get_latest_data()
                simulated_data = simulator.simulator.convert_ars_to_rate_sensor(ars_data)
                
                status_sample = {
                    'timestamp': time.time(),
                    'status_word_1': simulated_data.status_word_1,
                    'status_word_2': simulated_data.status_word_2,
                    'status_word_3': simulated_data.status_word_3,
                    'has_data': any([ars_data.prime_x, ars_data.prime_y, ars_data.prime_z])
                }
                status_samples.append(status_sample)
                
                time.sleep(0.1)
            
            # Analyze status words
            print(f"Collected {len(status_samples)} status samples")
            
            if status_samples:
                # Count different status word values
                sw1_values = set(s['status_word_1'] for s in status_samples)
                sw2_values = set(s['status_word_2'] for s in status_samples)
                sw3_values = set(s['status_word_3'] for s in status_samples)
                
                print(f"Status Word 1 values: {[f'0x{v:04X}' for v in sw1_values]}")
                print(f"Status Word 2 values: {[f'0x{v:04X}' for v in sw2_values]}")
                print(f"Status Word 3 values: {[f'0x{v:04X}' for v in sw3_values]}")
                
                # Check for data availability
                data_available_count = sum(1 for s in status_samples if s['has_data'])
                print(f"Data available in {data_available_count}/{len(status_samples)} samples")
            
        else:
            print("Failed to start simulator")
            
    except KeyboardInterrupt:
        print("\nStopping status analysis...")
        simulator.stop()

def main():
    """Run all examples"""
    parser = argparse.ArgumentParser(description='ARS Socket Reader Examples')
    parser.add_argument('--example', choices=['basic', 'custom', 'analysis', 'mapping', 'status'], 
                       default='basic', help='Example to run')
    
    args = parser.parse_args()
    
    print("ARS Socket Reader and Rate Sensor Simulator - Examples")
    print("=" * 60)
    
    if args.example == 'basic':
        example_basic_usage()
    elif args.example == 'custom':
        example_custom_configuration()
    elif args.example == 'analysis':
        example_data_analysis()
    elif args.example == 'mapping':
        example_port_mapping()
    elif args.example == 'status':
        example_status_word_analysis()
    
    print("\n" + "=" * 60)
    print("Example completed!")

if __name__ == '__main__':
    main()


