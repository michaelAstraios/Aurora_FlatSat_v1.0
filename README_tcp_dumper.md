# Multi-Port TCP Data Dumper

A Python program that listens for data on multiple TCP/IP ports simultaneously and dumps the received data in groups of 8 bytes with port identification and timestamps.

## Features

- **Multi-Port Support**: Listen on single ports, port ranges, or specific port lists
- **Simultaneous Monitoring**: Monitor multiple ports concurrently using threading
- **Port Identification**: Each data line shows the source port number
- **Timestamp Display**: Precise timestamps for each data chunk
- **8-Byte Grouping**: Displays data in groups of 8 bytes for easy analysis
- **Multiple Output Formats**: Hexadecimal, ASCII, and binary output options
- **Real-time Display**: Shows data as it arrives with port and timestamp
- **Per-Port Statistics**: Tracks bytes, packets, and connections per port
- **Thread-Safe**: Safe concurrent access to shared data structures

## Output Format

The data is displayed in the requested format:
```
port:Timestamp: dataHex    dataAscii
```

Example:
```
5000:17:45:32.123: 48 65 6C 6C 6F 2C 20 54    Hello, T
5000:17:45:32.124: 43 50 20 44 75 6D 70 65    CP Dumpe
5001:17:45:32.125: 3F 80 00 00 BF 00 00 00    ?...?...
6000:17:45:32.126: 48 65 6C 6C 6F 20 57 6F    Hello Wo
```

## Usage

### Single Port
```bash
# Listen on single port
python3 tcp_data_dumper.py --port 5000

# Listen on single port with specific host
python3 tcp_data_dumper.py --port 5000 --host 0.0.0.0
```

### Port Range
```bash
# Listen on port range (5000-5010)
python3 tcp_data_dumper.py --port-range 5000-5010

# Listen on ARS ports (5000-5011)
python3 tcp_data_dumper.py --port-range 5000-5011
```

### Specific Port List
```bash
# Listen on specific ports
python3 tcp_data_dumper.py --ports 5000,5001,5002,6000,6001

# Listen on FlatSat simulator ports
python3 tcp_data_dumper.py --ports 5000,6000,7000
```

### Output Formats
```bash
# Hexadecimal + ASCII output (default)
python3 tcp_data_dumper.py --ports 5000,5001 --hex --ascii

# Hexadecimal only
python3 tcp_data_dumper.py --ports 5000,5001 --hex --no-ascii

# ASCII only
python3 tcp_data_dumper.py --ports 5000,5001 --no-hex --ascii

# Binary output
python3 tcp_data_dumper.py --ports 5000,5001 --binary
```

### Command Line Options
- `--host`: Host to listen on (default: 127.0.0.1)
- `--port`: Single port to listen on
- `--port-range`: Port range to listen on (e.g., 5000-5010)
- `--ports`: Comma-separated list of ports (e.g., 5000,5001,6000)
- `--hex`: Display data in hexadecimal format (default: True)
- `--no-hex`: Disable hexadecimal output
- `--ascii`: Display ASCII representation alongside hex (default: True)
- `--no-ascii`: Disable ASCII output
- `--binary`: Display data in binary format instead of hex

## Example Output

```
🚀 Multi-Port TCP Data Dumper started
📡 Listening on 127.0.0.1 on ports: 5000, 5001, 5002
📊 Output: HEX + ASCII
⏰ Started at: 2024-10-22 17:45:30
📝 Data will be displayed in groups of 8 bytes
🛑 Press Ctrl+C to stop
--------------------------------------------------------------------------------

✅ Port 5000: Listening for connections...
✅ Port 5001: Listening for connections...
✅ Port 5002: Listening for connections...

🔗 Port 5000: Client connected from 127.0.0.1:54321
🔗 Port 5001: Client connected from 127.0.0.1:54322
🔗 Port 5002: Client connected from 127.0.0.1:54323

5000:17:45:32.123: 48 65 6C 6C 6F 2C 20 54    Hello, T
5000:17:45:32.124: 43 50 20 44 75 6D 70 65    CP Dumpe
5001:17:45:32.125: 3F 80 00 00 BF 00 00 00    ?...?...
5001:17:45:32.126: 3F 00 00 00 3E CC CC CD    ?...>...
5002:17:45:32.127: 50 6F 72 74 20 35 30 30    Port 50
5002:17:45:32.128: 32 20 6D 65 73 73 61 67    2 messag
5000:17:45:32.129: 65 21 00 00 00 00 00 00    e!......

📊 Port 5000: 24 bytes, 3 packets
📊 Port 5001: 16 bytes, 2 packets
📊 Port 5002: 16 bytes, 2 packets
```

## Testing

Use the included multi-port test client to send sample data:

```bash
# Send mixed test data to multiple ports
python3 test_multi_port_client.py --ports 5000,5001,5002

# Send floating point data to port range
python3 test_multi_port_client.py --port-range 5000-5005 --data-type floats

# Send text data to specific ports
python3 test_multi_port_client.py --ports 5000,6000,7000 --data-type text --duration 10

# Send binary data to ARS ports
python3 test_multi_port_client.py --ports 5000,5001,5002,5003,5004,5005 --data-type binary
```

### Demo Script
```bash
# Run complete demo showing all features
python3 demo_multi_port_dumper.py
```

## Use Cases

### FlatSat Simulator Debugging
```bash
# Debug ARS data (ports 5000-5011)
python3 tcp_data_dumper.py --port-range 5000-5011 --hex --ascii

# Debug magnetometer data (ports 6000-6002)
python3 tcp_data_dumper.py --ports 6000,6001,6002 --hex --ascii

# Debug reaction wheel data (ports 7000-7003)
python3 tcp_data_dumper.py --port-range 7000-7003 --hex --ascii

# Debug all FlatSat simulator ports simultaneously
python3 tcp_data_dumper.py --ports 5000,5001,5002,5003,5004,5005,6000,6001,6002,7000,7001,7002,7003 --hex --ascii
```

### MATLAB Data Analysis
```bash
# Analyze MATLAB simulator output on ARS ports
python3 tcp_data_dumper.py --port-range 5000-5011 --hex --ascii

# Monitor Python bridge communication
python3 tcp_data_dumper.py --ports 8888,8889 --hex --ascii

# Debug MATLAB orbital simulator data
python3 tcp_data_dumper.py --ports 5000,6000,7000 --hex --ascii
```

### General Multi-Port TCP Debugging
```bash
# Debug any multi-port TCP application
python3 tcp_data_dumper.py --ports <PORT1>,<PORT2>,<PORT3> --hex --ascii

# Monitor port ranges
python3 tcp_data_dumper.py --port-range <START>-<END> --hex --ascii
```

## Output Format Details

### Hexadecimal Output
- **Offset**: 4-digit hexadecimal offset
- **Hex Data**: Space-separated hexadecimal bytes
- **Alignment**: Padded to align columns

### ASCII Output
- **ASCII Column**: Printable characters, dots for non-printable
- **Combined**: Shows both hex and ASCII when both enabled

### Binary Output
- **Binary Data**: 8-bit binary representation of each byte
- **Space Separated**: Easy to read binary patterns

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)

## Files

- `tcp_data_dumper.py` - Main multi-port TCP data dumper
- `test_multi_port_client.py` - Multi-port test client for demonstration
- `demo_multi_port_dumper.py` - Complete demo script
- `README_tcp_dumper.md` - This documentation

## Tips

1. **Use with FlatSat Simulator**: Perfect for debugging data from your MATLAB simulator on multiple ports simultaneously
2. **Port Ranges**: Use `--port-range` for consecutive ports (e.g., ARS ports 5000-5011)
3. **Specific Ports**: Use `--ports` for non-consecutive ports (e.g., 5000,6000,7000)
4. **ASCII Output**: Helps identify text data and debug communication protocols
5. **Binary Output**: Useful for analyzing bit patterns and binary protocols
6. **Per-Port Statistics**: Monitor data rates and packet counts for each port
7. **Thread Safety**: Safe concurrent monitoring of multiple ports
8. **Performance**: Monitor up to 50 ports simultaneously (with warning)
9. **Format**: Data displayed as "port:Timestamp: dataHex    dataAscii" for easy analysis
10. **Real-time**: See data from all ports as it arrives with precise timestamps

This tool is perfect for debugging TCP communication in your FlatSat simulator and understanding the data flow between MATLAB and your device encoders! 🔍📡
