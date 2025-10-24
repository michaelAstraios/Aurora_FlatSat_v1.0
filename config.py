"""
Configuration file for Honeywell Dual Space Magnetometer

This file contains default configuration parameters for different environments
and use cases.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MagnetometerConfig:
    """Configuration class for magnetometer settings"""
    
    # Interface settings
    interface_type: str = "RS485"  # "CAN" or "RS485"
    
    # RS485 settings
    rs485_port: str = "/dev/ttyUSB0"
    rs485_baudrate: int = 9600
    rs485_timeout: float = 1.0
    
    # CAN settings
    can_channel: str = "can0"
    can_bitrate: int = 500000
    
    # Reading settings
    continuous_interval: float = 0.1  # seconds
    max_queue_size: int = 1000
    
    # Calibration settings
    min_calibration_readings: int = 10
    calibration_duration: float = 30.0  # seconds
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "magnetometer.log"
    
    # Data settings
    data_format: str = "json"  # "json" or "csv"
    data_file: str = "magnetometer_data.json"


# Predefined configurations for different environments
CONFIGURATIONS = {
    "development": MagnetometerConfig(
        interface_type="RS485",
        rs485_port="/dev/ttyUSB0",
        continuous_interval=0.5,
        log_level="DEBUG"
    ),
    
    "production": MagnetometerConfig(
        interface_type="CAN",
        can_channel="can0",
        continuous_interval=0.1,
        log_level="INFO",
        max_queue_size=5000
    ),
    
    "testing": MagnetometerConfig(
        interface_type="RS485",
        rs485_port="/dev/ttyUSB1",
        continuous_interval=0.2,
        log_level="WARNING",
        min_calibration_readings=5
    ),
    
    "simulation": MagnetometerConfig(
        interface_type="RS485",
        rs485_port="/dev/ttyUSB0",
        continuous_interval=0.1,
        log_level="DEBUG"
    )
}


def get_config(environment: str = "development") -> MagnetometerConfig:
    """
    Get configuration for specified environment
    
    Args:
        environment: Configuration environment name
        
    Returns:
        MagnetometerConfig object
    """
    if environment not in CONFIGURATIONS:
        raise ValueError(f"Unknown environment: {environment}. Available: {list(CONFIGURATIONS.keys())}")
    
    return CONFIGURATIONS[environment]


def get_config_dict(environment: str = "development") -> Dict[str, Any]:
    """
    Get configuration as dictionary for easy parameter passing
    
    Args:
        environment: Configuration environment name
        
    Returns:
        Dictionary of configuration parameters
    """
    config = get_config(environment)
    
    if config.interface_type == "CAN":
        return {
            "interface_type": config.interface_type,
            "channel": config.can_channel,
            "bitrate": config.can_bitrate
        }
    else:  # RS485
        return {
            "interface_type": config.interface_type,
            "port": config.rs485_port,
            "baudrate": config.rs485_baudrate,
            "timeout": config.rs485_timeout
        }


# Example usage in main application
if __name__ == "__main__":
    # Get configuration for different environments
    dev_config = get_config("development")
    prod_config = get_config("production")
    
    print("Development Configuration:")
    print(f"  Interface: {dev_config.interface_type}")
    print(f"  Port: {dev_config.rs485_port}")
    print(f"  Baudrate: {dev_config.rs485_baudrate}")
    
    print("\nProduction Configuration:")
    print(f"  Interface: {prod_config.interface_type}")
    print(f"  Channel: {prod_config.can_channel}")
    print(f"  Bitrate: {prod_config.can_bitrate}")
    
    # Get configuration dictionary for easy use
    config_dict = get_config_dict("development")
    print(f"\nConfiguration Dictionary: {config_dict}")

