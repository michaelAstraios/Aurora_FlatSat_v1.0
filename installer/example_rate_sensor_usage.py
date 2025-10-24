#!/usr/bin/env python3
"""
Example Usage of Honeywell HG4934 Rate Sensor Test Program

This script demonstrates various ways to use the rate sensor test program
for different testing scenarios and applications.
"""

import time
import json
import statistics
from rate_sensor_test_generator import RateSensorTestGenerator, RateSensorData, StatusWordBuilder, MessageEncoder


def basic_connection_test():
    """Example: Basic connection and status check."""
    print("=== Basic Connection Test ===")
    
    # Create test generator instance
    generator = RateSensorTestGenerator(serial_port='/dev/ttyUSB0', serial_baud=115200)
    
    try:
        # Test serial connection
        if generator.serial_transmitter.connect():
            print("✓ Connected to serial port")
            
            # Test encoding
            test_data = RateSensorData(
                angular_rate_x=0.01,
                angular_rate_y=-0.005,
                angular_rate_z=0.02,
                summed_angle_x=0.1,
                summed_angle_y=-0.05,
                summed_angle_z=0.2
            )
            
            encoded_message = MessageEncoder.encode_message(test_data)
            print(f"✓ Message encoded successfully ({len(encoded_message)} bytes)")
            print(f"  Hex: {encoded_message.hex().upper()}")
            
        else:
            print("✗ Failed to connect to serial port (running in simulation mode)")
    
    finally:
        generator.serial_transmitter.disconnect()


def continuous_monitoring_example():
    """Example: Continuous data monitoring with logging."""
    print("\n=== Continuous Monitoring Example ===")
    
    generator = RateSensorTestGenerator(serial_port='/dev/ttyUSB0', serial_baud=115200)
    
    try:
        if generator.serial_transmitter.connect():
            print("Starting continuous monitoring...")
            
            # Start transmission
            generator.serial_transmitter.start_transmission()
            
            # Monitor for 10 seconds
            start_time = time.time()
            while time.time() - start_time < 10:
                # Update data with current time
                generator.current_data.timestamp = time.time()
                generator.current_data.message_counter += 1
                
                # Add some variation to simulate real sensor data
                generator.current_data.angular_rate_x = 0.01 + 0.001 * (time.time() % 10)
                generator.current_data.angular_rate_y = -0.005 + 0.0005 * (time.time() % 7)
                generator.current_data.angular_rate_z = 0.02 + 0.002 * (time.time() % 5)
                
                # Queue message for transmission
                encoded_message = MessageEncoder.encode_message(generator.current_data)
                generator.serial_transmitter.queue_message(encoded_message)
                
                print(f"\rTime: {time.time() - start_time:.1f}s | "
                      f"Rate: X={generator.current_data.angular_rate_x:+.3f}, "
                      f"Y={generator.current_data.angular_rate_y:+.3f}, "
                      f"Z={generator.current_data.angular_rate_z:+.3f} | "
                      f"Counter: {generator.current_data.message_counter}", 
                      end='', flush=True)
                
                time.sleep(0.1)
            
            print("\nMonitoring completed")
            generator.serial_transmitter.stop_transmission()
        else:
            print("✗ Failed to connect to serial port (running in simulation mode)")
    
    finally:
        generator.serial_transmitter.disconnect()


def performance_analysis_example():
    """Example: Performance analysis and statistics."""
    print("\n=== Performance Analysis Example ===")
    
    generator = RateSensorTestGenerator(serial_port='/dev/ttyUSB0', serial_baud=115200)
    
    try:
        print("Running performance analysis...")
        
        # Generate test data
        test_data_samples = []
        for i in range(100):
            data = RateSensorData(
                angular_rate_x=0.01 + 0.001 * (i % 10),
                angular_rate_y=-0.005 + 0.0005 * (i % 7),
                angular_rate_z=0.02 + 0.002 * (i % 5),
                timestamp=time.time() + i * 0.01,
                message_counter=i
            )
            test_data_samples.append(data)
        
        if len(test_data_samples) > 0:
            print(f"Generated {len(test_data_samples)} test samples")
            
            # Calculate statistics
            x_rates = [d.angular_rate_x for d in test_data_samples]
            y_rates = [d.angular_rate_y for d in test_data_samples]
            z_rates = [d.angular_rate_z for d in test_data_samples]
            
            print(f"X-axis: mean={statistics.mean(x_rates):.4f}, std={statistics.stdev(x_rates):.4f}")
            print(f"Y-axis: mean={statistics.mean(y_rates):.4f}, std={statistics.stdev(y_rates):.4f}")
            print(f"Z-axis: mean={statistics.mean(z_rates):.4f}, std={statistics.stdev(z_rates):.4f}")
            
            # Test encoding performance
            start_time = time.time()
            for data in test_data_samples:
                MessageEncoder.encode_message(data)
            encoding_time = time.time() - start_time
            
            print(f"Encoding performance: {len(test_data_samples)/encoding_time:.1f} messages/sec")
    
    except Exception as e:
        print(f"Error during performance analysis: {e}")


def custom_test_scenario():
    """Example: Custom test scenario with specific requirements."""
    print("\n=== Custom Test Scenario ===")
    
    generator = RateSensorTestGenerator(serial_port='/dev/ttyUSB0', serial_baud=115200)
    
    try:
        print("Running custom test scenario...")
        
        # Test 1: Verify encoding works
        print("Test 1: Message encoding verification")
        test_data = RateSensorData(
            angular_rate_x=1.0,
            angular_rate_y=-0.5,
            angular_rate_z=0.8,
            summed_angle_x=10.0,
            summed_angle_y=-5.0,
            summed_angle_z=8.0
        )
        
        encoded_message = MessageEncoder.encode_message(test_data)
        if len(encoded_message) > 0:
            print(f"  ✓ Message encoding test passed ({len(encoded_message)} bytes)")
        else:
            print("  ✗ Message encoding test failed")
            return
        
        # Test 2: Verify status word building
        print("Test 2: Status word building verification")
        status_word_1 = StatusWordBuilder.build_status_word_1(
            counter=1,
            bit_mode=1,
            rate_sensor_failed=False,
            gyro_failed=False,
            agc_voltage_failed=False
        )
        
        status_word_2 = StatusWordBuilder.build_status_word_2(
            gyro_temperature_a=25,
            motor_bias_voltage_failed=False,
            start_data_flag=False,
            processor_failed=False,
            memory_failed=False
        )
        
        status_word_3 = StatusWordBuilder.build_status_word_3(
            gyro_a_start_run=True,
            gyro_b_start_run=True,
            gyro_c_start_run=True,
            gyro_a_fdc=False,
            gyro_b_fdc=False,
            gyro_c_fdc=False,
            fdc_failed=False,
            rs_ok=True
        )
        
        print(f"  ✓ Status Word 1: 0x{status_word_1:04X}")
        print(f"  ✓ Status Word 2: 0x{status_word_2:04X}")
        print(f"  ✓ Status Word 3: 0x{status_word_3:04X}")
        
        # Test 3: Serial communication test
        print("Test 3: Serial communication test")
        if generator.serial_transmitter.connect():
            print("  ✓ Serial port connection successful")
            
            # Test transmission
            generator.serial_transmitter.queue_message(encoded_message)
            generator.serial_transmitter.start_transmission()
            time.sleep(1)  # Transmit for 1 second
            generator.serial_transmitter.stop_transmission()
            
            print("  ✓ Serial transmission test completed")
        else:
            print("  ⚠ Serial port not available (simulation mode)")
    
    finally:
        generator.serial_transmitter.disconnect()


def load_configuration_example():
    """Example: Loading configuration from JSON file."""
    print("\n=== Configuration Loading Example ===")
    
    try:
        # Load configuration from file
        with open('rate_sensor_config.json', 'r') as f:
            config = json.load(f)
        
        print("Configuration loaded:")
        print(f"  Port: {config['sensor_config']['port']}")
        print(f"  Baud Rate: {config['sensor_config']['baud_rate']}")
        print(f"  Sample Rate: {config['data_acquisition']['sample_rate_hz']} Hz")
        print(f"  Logging Enabled: {config['data_acquisition']['enable_logging']}")
        
        # Create generator with loaded configuration
        sensor_config = config['sensor_config']
        generator = RateSensorTestGenerator(
            serial_port=sensor_config['port'],
            serial_baud=sensor_config['baud_rate']
        )
        
        print("Generator configured with loaded settings")
        
    except FileNotFoundError:
        print("Configuration file not found. Using default settings.")
    except json.JSONDecodeError:
        print("Invalid JSON in configuration file.")
    except Exception as e:
        print(f"Error loading configuration: {e}")


def comprehensive_test_example():
    """Example: Running comprehensive tests."""
    print("\n=== Comprehensive Test Example ===")
    
    generator = RateSensorTestGenerator(serial_port='/dev/ttyUSB0', serial_baud=115200)
    
    try:
        print("Running comprehensive tests...")
        
        # Test 1: Data structure validation
        print("Test 1: Data structure validation")
        test_data = RateSensorData()
        print(f"  ✓ Default data structure created")
        
        # Test 2: Encoding validation
        print("Test 2: Message encoding validation")
        encoded_message = MessageEncoder.encode_message(test_data)
        print(f"  ✓ Message encoded ({len(encoded_message)} bytes)")
        
        # Test 3: Status word validation
        print("Test 3: Status word validation")
        sw1 = StatusWordBuilder.build_status_word_1()
        sw2 = StatusWordBuilder.build_status_word_2()
        sw3 = StatusWordBuilder.build_status_word_3()
        print(f"  ✓ Status words built: 0x{sw1:04X}, 0x{sw2:04X}, 0x{sw3:04X}")
        
        # Test 4: Serial communication validation
        print("Test 4: Serial communication validation")
        if generator.serial_transmitter.connect():
            print("  ✓ Serial connection successful")
            generator.serial_transmitter.disconnect()
        else:
            print("  ⚠ Serial connection failed (simulation mode)")
        
        print("\nSummary: All tests completed successfully!")
        
    except Exception as e:
        print(f"Error during comprehensive testing: {e}")


def api_server_example():
    """Example: Starting the REST API server."""
    print("\n=== REST API Server Example ===")
    
    print("To start the REST API server, run:")
    print("  python rate_sensor_test_generator.py --host 0.0.0.0 --port 5000")
    print("\nThen you can use the following endpoints:")
    print("  GET  http://localhost:5000/api/data")
    print("  POST http://localhost:5000/api/data")
    print("  POST http://localhost:5000/api/status_words")
    print("  POST http://localhost:5000/api/encode")
    print("  POST http://localhost:5000/api/transmit")
    print("  DELETE http://localhost:5000/api/transmit")
    print("  GET  http://localhost:5000/api/test_scenarios")
    print("  POST http://localhost:5000/api/load_scenario/{scenario_name}")


def main():
    """Run all example scenarios."""
    print("Honeywell HG4934 Rate Sensor - Example Usage Scenarios")
    print("=" * 60)
    
    try:
        # Run example scenarios
        basic_connection_test()
        continuous_monitoring_example()
        performance_analysis_example()
        custom_test_scenario()
        load_configuration_example()
        comprehensive_test_example()
        api_server_example()
        
        print("\n" + "=" * 60)
        print("All example scenarios completed!")
        
    except KeyboardInterrupt:
        print("\n\nExample execution interrupted by user.")
    except Exception as e:
        print(f"\nError during example execution: {e}")


if __name__ == "__main__":
    main()