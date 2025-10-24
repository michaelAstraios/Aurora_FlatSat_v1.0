# FlatSat Device Simulator - TCP Installer

## Overview
This installer contains the **TCP-based ARS system** for the FlatSat Device Simulator. The ARS (Angular Rate Sensor) system has been upgraded from UDP to TCP/IP for improved reliability, connection management, and error handling.

## 🆕 TCP Upgrade Benefits

### **Improved Reliability**
- **Connection-oriented**: TCP provides reliable, ordered data delivery
- **Error detection**: Automatic retransmission of lost packets
- **Flow control**: Prevents data overflow and buffer issues

### **Better Connection Management**
- **Client tracking**: Monitor active connections per port
- **Graceful disconnection**: Proper cleanup when clients disconnect
- **Connection limits**: One client per port for data integrity

### **Enhanced Error Handling**
- **Timeout management**: Configurable timeouts for connections
- **Automatic reconnection**: Clients can reconnect after disconnection
- **Robust error recovery**: Better handling of network issues

## 📁 TCP Installer Contents

### **Core ARS TCP Components**
- `ars_tcp_socket_reader.py` - Basic TCP socket reader
- `ars_tcp_socket_reader_enhanced.py` - Enhanced TCP reader with data boundary handling
- `ars_tcp_socket_reader_endianness.py` - TCP reader with automatic endianness detection

### **Configuration Files**
- `config/simulator_config_tcp.json` - TCP-specific configuration
- `config/simulator_config.json` - Standard configuration (updated for TCP)
- `config/simulator_config_with_options.json` - Configuration with all options

### **Startup Scripts**
- `start_ars_tcp_reader.sh` - Start ARS TCP reader with endianness detection
- `install.sh` - Installation script
- `quick_start.sh` - Quick start script

### **Testing Tools**
- `test_ars_tcp_client.py` - TCP test client for ARS system
- `test_suite.py` - Comprehensive test suite
- `test_installation.py` - Installation verification

### **Device Encoders & Transmitters**
- `device_encoders/` - Device-specific data encoders
- `output_transmitters/` - Serial, CAN, and TCP output interfaces

## 🚀 Quick Start

### **1. Installation**
```bash
cd installer_tcp
./install.sh
```

### **2. Start ARS TCP Reader**
```bash
# Start with default settings
./start_ars_tcp_reader.sh

# Start with custom settings
./start_ars_tcp_reader.sh --ip 192.168.1.100 --start-port 5000 --num-ports 12
```

### **3. Test the System**
```bash
# Test with default settings
python3 test_ars_tcp_client.py

# Test with custom settings
python3 test_ars_tcp_client.py --host 127.0.0.1 --start-port 5000 --duration 30
```

## 🔧 Configuration

### **TCP-Specific Settings**
```json
{
  "devices": {
    "ars": {
      "enabled": true,
      "matlab_ports": [5000, 5001, 5002, 5003, 5004, 5005],
      "duplicate_primary_to_redundant": true,
      "redundant_variation_percent": 0.1,
      "_comment_tcp": "ARS system now uses TCP/IP instead of UDP for improved reliability"
    }
  }
}
```

### **Command Line Options**
```bash
# ARS TCP Reader Options
--ip IP_ADDRESS      # IP address to listen on (default: 127.0.0.1)
--start-port PORT    # Starting port number (default: 5000)
--num-ports NUM      # Number of ports to listen on (default: 12)
--log-level LEVEL    # Log level: DEBUG, INFO, WARNING, ERROR

# Test Client Options
--host HOST          # Host to connect to (default: 127.0.0.1)
--duration SECONDS   # Test duration in seconds (default: 10)
```

## 📊 TCP vs UDP Comparison

| Feature | UDP (Old) | TCP (New) |
|---------|-----------|-----------|
| **Reliability** | Best effort | Guaranteed delivery |
| **Connection Management** | None | Full connection tracking |
| **Error Handling** | Basic | Comprehensive |
| **Data Integrity** | No guarantees | Automatic verification |
| **Flow Control** | None | Built-in |
| **Client Tracking** | None | Per-port client monitoring |
| **Reconnection** | Manual | Automatic |
| **Timeout Handling** | Basic | Configurable |

## 🔍 Endianness Detection

The TCP system includes automatic endianness detection:

### **Detection Methods**
1. **Range Analysis**: Analyzes value ranges for reasonableness
2. **Pattern Analysis**: Examines byte patterns
3. **Consistency Analysis**: Checks value consistency

### **Usage**
```bash
# Start with endianness detection (recommended)
./start_ars_tcp_reader.sh

# Monitor detection results in logs
tail -f flatsat_simulator.log | grep "Endianness Detection"
```

## 🧪 Testing

### **Basic Test**
```bash
# Start ARS TCP reader in one terminal
./start_ars_tcp_reader.sh

# Run test client in another terminal
python3 test_ars_tcp_client.py --duration 30
```

### **Advanced Testing**
```bash
# Test with custom ports
python3 test_ars_tcp_client.py --start-port 5000 --num-ports 6 --duration 60

# Test with debug logging
python3 test_ars_tcp_client.py --log-level DEBUG --duration 10
```

### **Multi-Port Testing**
```bash
# Test all ARS ports simultaneously
python3 test_ars_tcp_client.py --num-ports 12 --duration 30

# Test specific port range
python3 test_ars_tcp_client.py --start-port 5000 --num-ports 6 --duration 20
```

## 📈 Performance

### **Expected Performance**
- **Data Rate**: 100 Hz per port (10ms intervals)
- **Latency**: < 5ms end-to-end
- **Throughput**: ~1.2 KB/s per port
- **Memory Usage**: Minimal overhead
- **CPU Usage**: Low (< 5% on modern systems)

### **Scalability**
- **Ports**: Up to 12 ports simultaneously
- **Clients**: One client per port (for data integrity)
- **Connections**: Automatic reconnection support
- **Buffering**: Configurable buffer sizes

## 🛠️ Troubleshooting

### **Connection Issues**
```bash
# Check if ports are available
netstat -an | grep :5000

# Test connectivity
telnet 127.0.0.1 5000
```

### **Performance Issues**
```bash
# Monitor system resources
top -p $(pgrep -f ars_tcp_socket_reader)

# Check network statistics
netstat -i
```

### **Log Analysis**
```bash
# Monitor logs in real-time
tail -f flatsat_simulator.log

# Search for errors
grep ERROR flatsat_simulator.log

# Check endianness detection
grep "Endianness Detection" flatsat_simulator.log
```

## 🔄 Migration from UDP

### **Key Changes**
1. **Protocol**: UDP → TCP
2. **Connection Model**: Connectionless → Connection-oriented
3. **Error Handling**: Basic → Comprehensive
4. **Client Management**: None → Full tracking

### **Migration Steps**
1. **Stop UDP system**: Stop existing UDP-based ARS readers
2. **Install TCP system**: Run `./install.sh` in `installer_tcp/`
3. **Update configuration**: Use TCP-specific config files
4. **Test system**: Run test client to verify functionality
5. **Update clients**: Ensure clients connect via TCP

## 📚 Additional Resources

### **Documentation**
- `README_ars_socket_reader.md` - Detailed ARS documentation
- `ENDIANNESS_DETECTION.md` - Endianness detection guide
- `ENHANCED_ARS_IMPROVEMENTS.md` - Enhancement details

### **Examples**
- `examples/` - Usage examples and demos
- `test_ars_tcp_client.py` - Test client implementation
- `start_ars_tcp_reader.sh` - Startup script example

### **Configuration**
- `config/simulator_config_tcp.json` - TCP-specific configuration
- `config/simulator_config_with_options.json` - Full configuration options

## ✅ Verification Checklist

- [ ] TCP installer installed successfully
- [ ] ARS TCP reader starts without errors
- [ ] Test client connects successfully
- [ ] Data transmission verified
- [ ] Endianness detection working
- [ ] Error handling tested
- [ ] Performance meets requirements
- [ ] Logging configured correctly

## 🎯 Next Steps

1. **Deploy TCP system** in your environment
2. **Update client applications** to use TCP
3. **Monitor performance** and adjust configuration
4. **Test with real hardware** when available
5. **Document any issues** for future improvements

The TCP-based ARS system provides a more robust and reliable foundation for your FlatSat simulator! 🚀
