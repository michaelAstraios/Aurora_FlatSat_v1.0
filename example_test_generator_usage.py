#!/usr/bin/env python3
"""
Example Usage of Rate Sensor Test Generator

This script demonstrates how to use the Rate Sensor Test Generator REST API
for various testing scenarios.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class RateSensorTestClient:
    """Client for interacting with the Rate Sensor Test Generator API"""
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url.rstrip('/')
        
    def get_current_data(self) -> Dict[str, Any]:
        """Get current rate sensor data"""
        response = requests.get(f'{self.base_url}/api/data')
        response.raise_for_status()
        return response.json()
    
    def set_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set rate sensor data parameters"""
        response = requests.post(f'{self.base_url}/api/data', json=data)
        response.raise_for_status()
        return response.json()
    
    def set_status_words(self, status_words: Dict[str, Any]) -> Dict[str, Any]:
        """Set status words with individual bit control"""
        response = requests.post(f'{self.base_url}/api/status_words', json=status_words)
        response.raise_for_status()
        return response.json()
    
    def encode_message(self) -> Dict[str, Any]:
        """Encode current data to Honeywell protocol format"""
        response = requests.post(f'{self.base_url}/api/encode')
        response.raise_for_status()
        return response.json()
    
    def start_transmission(self) -> Dict[str, Any]:
        """Start serial transmission"""
        response = requests.post(f'{self.base_url}/api/transmit')
        response.raise_for_status()
        return response.json()
    
    def stop_transmission(self) -> Dict[str, Any]:
        """Stop serial transmission"""
        response = requests.delete(f'{self.base_url}/api/transmit')
        response.raise_for_status()
        return response.json()
    
    def get_test_scenarios(self) -> Dict[str, Any]:
        """Get available test scenarios"""
        response = requests.get(f'{self.base_url}/api/test_scenarios')
        response.raise_for_status()
        return response.json()
    
    def load_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Load a predefined test scenario"""
        response = requests.post(f'{self.base_url}/api/load_scenario/{scenario_name}')
        response.raise_for_status()
        return response.json()

def example_basic_usage():
    """Example: Basic usage of the test generator"""
    print("=== Basic Usage Example ===")
    
    client = RateSensorTestClient()
    
    try:
        # Get current data
        print("Getting current data...")
        current_data = client.get_current_data()
        print(f"Current data: {json.dumps(current_data, indent=2)}")
        
        # Set some test data
        print("\nSetting test data...")
        test_data = {
            'angular_rate_x': 0.1,
            'angular_rate_y': -0.05,
            'angular_rate_z': 0.02,
            'summed_angle_x': 1.0,
            'summed_angle_y': -0.5,
            'summed_angle_z': 0.2
        }
        
        result = client.set_data(test_data)
        print(f"Data set result: {json.dumps(result, indent=2)}")
        
        # Encode message
        print("\nEncoding message...")
        encoded = client.encode_message()
        print(f"Encoded message: {encoded['encoded_data']['hex']}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")

def example_status_word_control():
    """Example: Controlling status words"""
    print("\n=== Status Word Control Example ===")
    
    client = RateSensorTestClient()
    
    try:
        # Set status words for normal operation
        print("Setting status words for normal operation...")
        normal_status = {
            'status_word_1': {
                'counter': 0,
                'bit_mode': 1,  # Continuous BIT
                'rate_sensor_failed': False,
                'gyro_failed': False,
                'agc_voltage_failed': False
            },
            'status_word_2': {
                'gyro_temperature_a': 25,  # 25°C
                'motor_bias_voltage_failed': False,
                'start_data_flag': False,
                'processor_failed': False,
                'memory_failed': False
            },
            'status_word_3': {
                'gyro_a_start_run': True,
                'gyro_b_start_run': True,
                'gyro_c_start_run': True,
                'gyro_a_fdc': False,
                'gyro_b_fdc': False,
                'gyro_c_fdc': False,
                'fdc_failed': False,
                'rs_ok': True
            }
        }
        
        result = client.set_status_words(normal_status)
        print(f"Status words set: {json.dumps(result, indent=2)}")
        
        # Set fault condition
        print("\nSetting fault condition...")
        fault_status = {
            'status_word_1': {
                'counter': 1,
                'bit_mode': 1,
                'rate_sensor_failed': True,
                'gyro_failed': True,
                'agc_voltage_failed': True
            },
            'status_word_2': {
                'gyro_temperature_a': 50,  # High temperature
                'motor_bias_voltage_failed': True,
                'start_data_flag': False,
                'processor_failed': True,
                'memory_failed': True
            },
            'status_word_3': {
                'gyro_a_start_run': False,
                'gyro_b_start_run': False,
                'gyro_c_start_run': False,
                'gyro_a_fdc': True,
                'gyro_b_fdc': True,
                'gyro_c_fdc': True,
                'fdc_failed': True,
                'rs_ok': False
            }
        }
        
        result = client.set_status_words(fault_status)
        print(f"Fault status set: {json.dumps(result, indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")

def example_test_scenarios():
    """Example: Using predefined test scenarios"""
    print("\n=== Test Scenarios Example ===")
    
    client = RateSensorTestClient()
    
    try:
        # Get available scenarios
        print("Getting available test scenarios...")
        scenarios = client.get_test_scenarios()
        print(f"Available scenarios: {list(scenarios['scenarios'].keys())}")
        
        # Load normal operation scenario
        print("\nLoading normal operation scenario...")
        result = client.load_scenario('normal_operation')
        print(f"Scenario loaded: {json.dumps(result['data'], indent=2)}")
        
        # Load high rate test scenario
        print("\nLoading high rate test scenario...")
        result = client.load_scenario('high_rate_test')
        print(f"High rate scenario loaded: {json.dumps(result['data'], indent=2)}")
        
        # Load fault condition scenario
        print("\nLoading fault condition scenario...")
        result = client.load_scenario('fault_condition')
        print(f"Fault scenario loaded: {json.dumps(result['data'], indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")

def example_transmission():
    """Example: Serial transmission"""
    print("\n=== Serial Transmission Example ===")
    
    client = RateSensorTestClient()
    
    try:
        # Load a test scenario first
        print("Loading test scenario...")
        client.load_scenario('normal_operation')
        
        # Start transmission
        print("Starting transmission...")
        result = client.start_transmission()
        print(f"Transmission started: {result['message']}")
        
        # Let it run for a few seconds
        print("Transmitting for 5 seconds...")
        time.sleep(5)
        
        # Stop transmission
        print("Stopping transmission...")
        result = client.stop_transmission()
        print(f"Transmission stopped: {result['message']}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")

def example_custom_test_sequence():
    """Example: Custom test sequence"""
    print("\n=== Custom Test Sequence Example ===")
    
    client = RateSensorTestClient()
    
    try:
        # Test sequence: Start with normal operation, then introduce faults
        print("Starting custom test sequence...")
        
        # Step 1: Normal operation
        print("\nStep 1: Normal operation")
        client.load_scenario('normal_operation')
        encoded = client.encode_message()
        print(f"Normal operation message: {encoded['encoded_data']['hex']}")
        
        # Step 2: High rates
        print("\nStep 2: High angular rates")
        client.load_scenario('high_rate_test')
        encoded = client.encode_message()
        print(f"High rate message: {encoded['encoded_data']['hex']}")
        
        # Step 3: Gradual fault introduction
        print("\nStep 3: Gradual fault introduction")
        
        # First, just temperature increase
        temp_fault_status = {
            'status_word_2': {
                'gyro_temperature_a': 45,  # High temperature
                'motor_bias_voltage_failed': False,
                'start_data_flag': False,
                'processor_failed': False,
                'memory_failed': False
            }
        }
        client.set_status_words(temp_fault_status)
        encoded = client.encode_message()
        print(f"Temperature fault message: {encoded['encoded_data']['hex']}")
        
        # Then add processor fault
        processor_fault_status = {
            'status_word_2': {
                'gyro_temperature_a': 50,
                'motor_bias_voltage_failed': False,
                'start_data_flag': False,
                'processor_failed': True,  # Processor fault
                'memory_failed': False
            }
        }
        client.set_status_words(processor_fault_status)
        encoded = client.encode_message()
        print(f"Processor fault message: {encoded['encoded_data']['hex']}")
        
        # Finally, complete failure
        print("\nStep 4: Complete failure")
        client.load_scenario('fault_condition')
        encoded = client.encode_message()
        print(f"Complete failure message: {encoded['encoded_data']['hex']}")
        
        print("\nCustom test sequence completed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")

def example_performance_test():
    """Example: Performance testing with continuous data updates"""
    print("\n=== Performance Test Example ===")
    
    client = RateSensorTestClient()
    
    try:
        print("Running performance test with continuous data updates...")
        
        # Start with normal operation
        client.load_scenario('normal_operation')
        
        # Simulate varying angular rates
        import math
        
        for i in range(10):
            # Generate sinusoidal angular rates
            t = i * 0.1
            angular_rate_x = 0.1 * math.sin(t)
            angular_rate_y = 0.05 * math.cos(t)
            angular_rate_z = 0.02 * math.sin(2 * t)
            
            # Update data
            test_data = {
                'angular_rate_x': angular_rate_x,
                'angular_rate_y': angular_rate_y,
                'angular_rate_z': angular_rate_z,
                'summed_angle_x': angular_rate_x * t,
                'summed_angle_y': angular_rate_y * t,
                'summed_angle_z': angular_rate_z * t
            }
            
            client.set_data(test_data)
            
            # Encode and display
            encoded = client.encode_message()
            print(f"Time {t:.1f}s: Rates=({angular_rate_x:.3f}, {angular_rate_y:.3f}, {angular_rate_z:.3f}) "
                  f"Message={encoded['encoded_data']['hex']}")
            
            time.sleep(0.1)
        
        print("Performance test completed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Run all example scenarios"""
    print("Rate Sensor Test Generator - Example Usage")
    print("=" * 50)
    
    # Check if server is running
    try:
        client = RateSensorTestClient()
        client.get_current_data()
        print("✓ Connected to API server")
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API server")
        print("Please start the server first:")
        print("  python rate_sensor_test_generator.py")
        sys.exit(1)
    
    try:
        # Run examples
        example_basic_usage()
        example_status_word_control()
        example_test_scenarios()
        example_transmission()
        example_custom_test_sequence()
        example_performance_test()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\nError during example execution: {e}")

if __name__ == "__main__":
    main()



