#!/usr/bin/env python3
"""
Example usage of Honeywell Dual Space Magnetometer

This script demonstrates various ways to use the magnetometer communication library
based on the actual ICD specifications from the PDF documents.
"""

import time
import json
from honeywell_magnetometer import (
    HoneywellMagnetometer, 
    setup_logging, 
    MagnetometerStatus,
    MessageType,
    OperationMode
)


def example_single_reading():
    """Example: Single reading from magnetometer using MAGDATA command"""
    print("=== Single Reading Example ===")
    
    # Initialize magnetometer (adjust parameters based on your setup)
    mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0", baudrate=9600)
    
    try:
        if mag.connect():
            print("Connected to magnetometer")
            
            # Read single measurement using MAGDATA command
            reading = mag.read_data()
            if reading:
                print(f"Timestamp: {reading.timestamp}")
                print(f"Message Type: {reading.message_type.name}")
                print(f"X Field: {reading.x_field:.2f} nT")
                print(f"Y Field: {reading.y_field:.2f} nT")
                print(f"Z Field: {reading.z_field:.2f} nT")
                print(f"Temperature: {reading.temperature:.2f} °C")
                print(f"Status: {reading.status.name}")
                print(f"Magnitude: {reading.magnitude():.2f} nT")
            else:
                print("Failed to read data")
        else:
            print("Failed to connect to magnetometer")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        mag.disconnect()


def example_device_info():
    """Example: Get device information using MAGID command"""
    print("\n=== Device Information Example ===")
    
    mag = HoneywellMagnetometer("CAN", channel="can0")
    
    try:
        if mag.connect():
            print("Connected to magnetometer")
            
            # Get device information
            device_info = mag.get_device_info()
            if device_info:
                print(f"Device ID: {device_info.device_id}")
                print(f"Firmware Version: {device_info.firmware_version}")
                print(f"Serial Number: {device_info.serial_number}")
                print(f"Calibration Date: {device_info.calibration_date}")
                print(f"Status: {device_info.status.name}")
            else:
                print("Failed to get device information")
        else:
            print("Failed to connect to magnetometer")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        mag.disconnect()


def example_temperature_reading():
    """Example: Get temperature using MAGTEMP command"""
    print("\n=== Temperature Reading Example ===")
    
    mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
    
    try:
        if mag.connect():
            print("Connected to magnetometer")
            
            # Get temperature reading
            temperature = mag.get_temperature()
            if temperature is not None:
                print(f"Temperature: {temperature:.2f} °C")
            else:
                print("Failed to read temperature")
        else:
            print("Failed to connect to magnetometer")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        mag.disconnect()


def example_memory_operations():
    """Example: EEPROM memory operations using MEMREAD/MEMWRITE commands"""
    print("\n=== Memory Operations Example ===")
    
    mag = HoneywellMagnetometer("CAN", channel="can0")
    
    try:
        if mag.connect():
            print("Connected to magnetometer")
            
            # Read calibration data from memory
            print("Reading calibration data from EEPROM...")
            calibration_data = mag.read_memory(0x0000, 64)  # Read 64 bytes from calibration area
            if calibration_data:
                print(f"Read {calibration_data.length} bytes from address 0x{calibration_data.address:04X}")
                print(f"Data: {calibration_data.data.hex()}")
                print(f"Checksum: 0x{calibration_data.checksum:04X}")
            else:
                print("Failed to read calibration data")
            
            # Write test data to user memory area
            print("\nWriting test data to user memory...")
            test_data = b"TEST_DATA_12345"
            if mag.write_memory(0x2000, test_data):
                print("Test data written successfully")
                
                # Read back the data to verify
                read_back = mag.read_memory(0x2000, len(test_data))
                if read_back and read_back.data == test_data:
                    print("Data verification successful")
                else:
                    print("Data verification failed")
            else:
                print("Failed to write test data")
        else:
            print("Failed to connect to magnetometer")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        mag.disconnect()


def example_operation_modes():
    """Example: Set different operation modes using OPMODE command"""
    print("\n=== Operation Modes Example ===")
    
    mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
    
    try:
        if mag.connect():
            print("Connected to magnetometer")
            
            # Set to calibration mode
            print("Setting to calibration mode...")
            if mag.set_operation_mode(OperationMode.CALIBRATION):
                print("Successfully set to calibration mode")
                
                # Wait a bit
                time.sleep(2)
                
                # Set back to normal mode
                print("Setting back to normal mode...")
                if mag.set_operation_mode(OperationMode.NORMAL):
                    print("Successfully set to normal mode")
                else:
                    print("Failed to set to normal mode")
            else:
                print("Failed to set to calibration mode")
        else:
            print("Failed to connect to magnetometer")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        mag.disconnect()


def example_continuous_reading():
    """Example: Continuous reading with background thread"""
    print("\n=== Continuous Reading Example ===")
    
    mag = HoneywellMagnetometer("CAN", channel="can0")
    
    try:
        if mag.connect():
            print("Connected to magnetometer")
            
            # Start continuous reading
            mag.start_continuous_reading(interval=0.5)  # Read every 0.5 seconds
            
            # Collect readings for 10 seconds
            print("Collecting readings for 10 seconds...")
            time.sleep(10)
            
            # Stop continuous reading
            mag.stop_continuous_reading()
            
            # Get all collected readings
            readings = mag.get_all_readings()
            print(f"Collected {len(readings)} readings")
            
            if readings:
                # Calculate statistics
                x_values = [r.x_field for r in readings]
                y_values = [r.y_field for r in readings]
                z_values = [r.z_field for r in readings]
                
                print(f"X Field - Min: {min(x_values):.2f}, Max: {max(x_values):.2f}, Avg: {sum(x_values)/len(x_values):.2f}")
                print(f"Y Field - Min: {min(y_values):.2f}, Max: {max(y_values):.2f}, Avg: {sum(y_values)/len(y_values):.2f}")
                print(f"Z Field - Min: {min(z_values):.2f}, Max: {max(z_values):.2f}, Avg: {sum(z_values)/len(z_values):.2f}")
        else:
            print("Failed to connect to magnetometer")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        mag.disconnect()


def example_calibration():
    """Example: Magnetometer calibration"""
    print("\n=== Calibration Example ===")
    
    mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
    
    try:
        if mag.connect():
            print("Connected to magnetometer")
            print("Performing calibration - rotate magnetometer in all directions...")
            
            # Set to calibration mode first
            if mag.set_operation_mode(OperationMode.CALIBRATION):
                print("Set to calibration mode")
                
                # Collect readings for calibration
                calibration_readings = []
                mag.start_continuous_reading(interval=0.1)
                
                # Collect readings for 30 seconds (adjust as needed)
                for _ in range(300):  # 30 seconds at 0.1s interval
                    reading = mag.get_latest_reading()
                    if reading:
                        calibration_readings.append(reading)
                    time.sleep(0.1)
                
                mag.stop_continuous_reading()
                
                print(f"Collected {len(calibration_readings)} readings for calibration")
                
                # Perform calibration
                if mag.calibrate(calibration_readings):
                    print("Calibration completed successfully")
                    print(f"Offset: {mag.offset}")
                    print(f"Scale factors: {mag.scale_factors}")
                else:
                    print("Calibration failed")
                
                # Set back to normal mode
                mag.set_operation_mode(OperationMode.NORMAL)
            else:
                print("Failed to set calibration mode")
        else:
            print("Failed to connect to magnetometer")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        mag.disconnect()


def example_data_logging():
    """Example: Data logging to file"""
    print("\n=== Data Logging Example ===")
    
    mag = HoneywellMagnetometer("CAN", channel="can0")
    
    try:
        if mag.connect():
            print("Connected to magnetometer")
            
            # Start continuous reading
            mag.start_continuous_reading(interval=1.0)  # Read every second
            
            # Log data for 60 seconds
            print("Logging data for 60 seconds...")
            start_time = time.time()
            
            with open("magnetometer_data.json", "w") as f:
                f.write("[\n")
                first_reading = True
                
                while time.time() - start_time < 60:
                    reading = mag.get_latest_reading()
                    if reading:
                        if not first_reading:
                            f.write(",\n")
                        json.dump(reading.to_dict(), f, indent=2)
                        first_reading = False
                        print(f"Logged reading: {reading.magnitude():.2f} nT ({reading.message_type.name})")
                    time.sleep(0.1)
                
                f.write("\n]")
            
            mag.stop_continuous_reading()
            print("Data logging completed. Check magnetometer_data.json")
        else:
            print("Failed to connect to magnetometer")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        mag.disconnect()


def example_status_monitoring():
    """Example: Status monitoring using STATUS command"""
    print("\n=== Status Monitoring Example ===")
    
    mag = HoneywellMagnetometer("RS485", port="/dev/ttyUSB0")
    
    try:
        if mag.connect():
            print("Connected to magnetometer")
            
            # Monitor status for 30 seconds
            print("Monitoring status for 30 seconds...")
            start_time = time.time()
            
            while time.time() - start_time < 30:
                status = mag.get_status()
                if status:
                    print(f"Status: {status.name}")
                    
                    if status == MagnetometerStatus.ERROR:
                        print("WARNING: Magnetometer error detected!")
                    elif status == MagnetometerStatus.CRITICAL:
                        print("CRITICAL: Magnetometer critical error!")
                    elif status == MagnetometerStatus.CALIBRATION_MODE:
                        print("INFO: Magnetometer in calibration mode")
                    elif status == MagnetometerStatus.MEMORY_ERROR:
                        print("WARNING: Memory error detected!")
                    elif status == MagnetometerStatus.COMMUNICATION_ERROR:
                        print("WARNING: Communication error detected!")
                else:
                    print("Failed to read status")
                
                time.sleep(2)
        else:
            print("Failed to connect to magnetometer")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        mag.disconnect()


def main():
    """Run all examples"""
    setup_logging()
    
    print("Honeywell Dual Space Magnetometer Examples")
    print("Based on ICD specifications from PDF documents")
    print("=" * 60)
    
    # Run examples (comment out any you don't want to run)
    example_single_reading()
    example_device_info()
    example_temperature_reading()
    example_memory_operations()
    example_operation_modes()
    example_continuous_reading()
    example_calibration()
    example_data_logging()
    example_status_monitoring()
    
    print("\nAll examples completed!")


if __name__ == "__main__":
    main()