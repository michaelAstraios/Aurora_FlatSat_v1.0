#!/usr/bin/env python3
"""
Multi-Port TCP Data Dumper

A Python program that listens for data on a range of TCP/IP ports simultaneously
and dumps the received data in groups of 8 bytes with port identification.

Usage:
    python3 tcp_data_dumper.py --port 5000
    python3 tcp_data_dumper.py --port-range 5000-5010
    python3 tcp_data_dumper.py --ports 5000,5001,5002,6000,6001
"""

import socket
import argparse
import time
import threading
import struct
import sys
from datetime import datetime

class MultiPortTCPDataDumper:
    """Multi-port TCP data dumper for debugging and analysis"""
    
    def __init__(self, host='127.0.0.1', ports=None, hex_output=True, ascii_output=True, float_output=True, endianness='little'):
        self.host = host
        self.ports = ports if ports else [5000]
        self.hex_output = hex_output
        self.ascii_output = ascii_output
        self.float_output = float_output
        self.endianness = endianness  # 'little' or 'big'
        self.sockets = {}
        self.running = False
        self.stats = {}  # Per-port statistics
        self.lock = threading.Lock()
        
    def bytes_to_float(self, data_bytes):
        """Convert 8 bytes to floating point value with robust error handling"""
        if len(data_bytes) != 8:
            return None
        
        try:
            if self.endianness == 'big':
                # Big endian double precision float
                value = struct.unpack('>d', data_bytes)[0]
            else:
                # Little endian double precision float
                value = struct.unpack('<d', data_bytes)[0]
            
            # Additional validation for extreme values
            if not isinstance(value, (int, float)):
                return None
                
            # Check for infinity and NaN
            if not (float('-inf') < value < float('inf')):
                return None
                
            return value
            
        except (struct.error, OverflowError, ValueError, TypeError):
            return None
        
    def start_server(self):
        """Start the multi-port TCP server"""
        try:
            # Initialize statistics for each port
            for port in self.ports:
                self.stats[port] = {'bytes': 0, 'packets': 0, 'connections': 0}
            
            print(f"🚀 Multi-Port TCP Data Dumper started")
            print(f"📡 Listening on {self.host} on ports: {', '.join(map(str, self.ports))}")
            output_modes = []
            if self.hex_output:
                output_modes.append("HEX")
            if self.ascii_output:
                output_modes.append("ASCII")
            if self.float_output:
                output_modes.append("FLOAT")
            if not output_modes:
                output_modes.append("BINARY")
            print(f"📊 Output: {' + '.join(output_modes)} ({self.endianness} endian)")
            print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📝 Data will be displayed in groups of 8 bytes")
            print(f"🛑 Press Ctrl+C to stop")
            print("-" * 80)
            
            self.running = True
            
            # Start a thread for each port
            threads = []
            for port in self.ports:
                thread = threading.Thread(target=self.listen_on_port, args=(port,))
                thread.daemon = True
                thread.start()
                threads.append(thread)
            
            # Wait for threads or keyboard interrupt
            try:
                while self.running:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print(f"\n🛑 Stopping server...")
                self.running = False
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
        finally:
            self.cleanup()
    
    def listen_on_port(self, port):
        """Listen on a specific port"""
        try:
            # Create socket for this port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, port))
            sock.listen(1)
            
            with self.lock:
                self.sockets[port] = sock
            
            print(f"✅ Port {port}: Listening for connections...")
            
            while self.running:
                try:
                    client_socket, client_address = sock.accept()
                    with self.lock:
                        self.stats[port]['connections'] += 1
                    
                    print(f"🔗 Port {port}: Client connected from {client_address[0]}:{client_address[1]}")
                    
                    # Handle client data
                    self.handle_client(client_socket, client_address, port)
                    
                except socket.error as e:
                    if self.running:
                        print(f"❌ Port {port}: Socket error: {e}")
                    break
                except Exception as e:
                    if self.running:
                        print(f"❌ Port {port}: Error: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Port {port}: Failed to start: {e}")
        finally:
            if port in self.sockets:
                self.sockets[port].close()
                del self.sockets[port]
    
    def handle_client(self, client_socket, client_address, port):
        """Handle data from a connected client"""
        try:
            while self.running:
                # Receive data
                data = client_socket.recv(4096)
                if not data:
                    print(f"🔌 Port {port}: Client {client_address[0]}:{client_address[1]} disconnected")
                    break
                
                # Process received data
                try:
                    self.process_data(data, client_address, port)
                except Exception as e:
                    print(f"⚠️  Port {port}: Error processing data from {client_address}: {e}")
                    # Continue processing other data
                
        except Exception as e:
            print(f"❌ Port {port}: Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
    
    def process_data(self, data, client_address, port):
        """Process received data and display it with robust error handling"""
        try:
            with self.lock:
                self.stats[port]['packets'] += 1
                self.stats[port]['bytes'] += len(data)
        except Exception as e:
            print(f"⚠️  Port {port}: Error updating stats: {e}")
            return
        
        # Display data in groups of 8 bytes
        try:
            for i in range(0, len(data), 8):
                chunk = data[i:i+8]
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                # Format hex data
                hex_str = ' '.join(f'{b:02X}' for b in chunk)
                hex_str = hex_str.ljust(23)  # Pad to align columns
                
                # Format ASCII data
                ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
                
                # Convert to float if enabled and we have exactly 8 bytes
                float_str = ""
                if self.float_output and len(chunk) == 8:
                    try:
                        float_value = self.bytes_to_float(chunk)
                        if float_value is not None:
                            # Check if it's a reasonable float value for display
                            if abs(float_value) < 1e10 and abs(float_value) > 1e-10:
                                # Format with appropriate precision
                                if abs(float_value) < 1e-3 or abs(float_value) > 1e3:
                                    float_str = f" = {float_value:.6e}"  # Scientific notation
                                else:
                                    float_str = f" = {float_value:.6f}"  # Fixed point
                            elif abs(float_value) == 0.0:
                                float_str = f" = 0.000000"
                            else:
                                float_str = " = [extreme value]"
                        else:
                            float_str = " = [parse error]"
                    except (OverflowError, ValueError, TypeError) as e:
                        float_str = f" = [error: {type(e).__name__}]"
                
                # Display line in requested format: "port:Timestamp: dataHex    dataAscii    floatValue"
                if self.hex_output and self.ascii_output and self.float_output:
                    print(f"{port}:{timestamp}: {hex_str}    {ascii_str}    {float_str}")
                elif self.hex_output and self.ascii_output:
                    print(f"{port}:{timestamp}: {hex_str}    {ascii_str}")
                elif self.hex_output and self.float_output:
                    print(f"{port}:{timestamp}: {hex_str}    {float_str}")
                elif self.ascii_output and self.float_output:
                    print(f"{port}:{timestamp}: {ascii_str}    {float_str}")
                elif self.hex_output:
                    print(f"{port}:{timestamp}: {hex_str}")
                elif self.ascii_output:
                    print(f"{port}:{timestamp}: {ascii_str}")
                elif self.float_output:
                    print(f"{port}:{timestamp}: {float_str}")
                else:
                    # Binary output
                    binary_str = ' '.join(f'{b:08b}' for b in chunk)
                    print(f"{port}:{timestamp}: {binary_str}")
            
            # Display summary every 10 packets
            try:
                with self.lock:
                    if self.stats[port]['packets'] % 10 == 0:
                        total_bytes = self.stats[port]['bytes']
                        total_packets = self.stats[port]['packets']
                        print(f"📊 Port {port}: {total_bytes} bytes, {total_packets} packets")
            except Exception as e:
                print(f"⚠️  Port {port}: Error displaying summary: {e}")
                
        except Exception as e:
            print(f"⚠️  Port {port}: Error processing data chunk: {e}")
            # Continue processing other data
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        for port, sock in self.sockets.items():
            try:
                sock.close()
            except:
                pass
        
        print(f"\n✅ Server stopped")
        print(f"📊 Final stats:")
        for port, stats in self.stats.items():
            print(f"   Port {port}: {stats['bytes']} bytes, {stats['packets']} packets, {stats['connections']} connections")

def parse_ports(port_spec):
    """Parse port specification into a list of ports"""
    ports = []
    
    for part in port_spec.split(','):
        part = part.strip()
        if '-' in part:
            # Range specification (e.g., "5000-5010")
            start, end = part.split('-', 1)
            try:
                start_port = int(start.strip())
                end_port = int(end.strip())
                ports.extend(range(start_port, end_port + 1))
            except ValueError:
                raise ValueError(f"Invalid port range: {part}")
        else:
            # Single port
            try:
                ports.append(int(part))
            except ValueError:
                raise ValueError(f"Invalid port: {part}")
    
    return sorted(list(set(ports)))  # Remove duplicates and sort

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Multi-Port TCP Data Dumper - Listen for data on multiple ports and display in 8-byte groups',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tcp_data_dumper.py --port 5000
  python3 tcp_data_dumper.py --port-range 5000-5010
  python3 tcp_data_dumper.py --ports 5000,5001,5002,6000,6001
  python3 tcp_data_dumper.py --port-range 5000-5010 --host 0.0.0.0
  python3 tcp_data_dumper.py --ports 5000,6000,7000 --hex --ascii --float
  python3 tcp_data_dumper.py --ports 5000,5001 --float --endianness big
  python3 tcp_data_dumper.py --ports 5000 --no-hex --no-ascii --float
        """
    )
    
    parser.add_argument('--host', default='127.0.0.1', 
                       help='Host to listen on (default: 127.0.0.1)')
    
    # Port specification options (mutually exclusive)
    port_group = parser.add_mutually_exclusive_group(required=True)
    port_group.add_argument('--port', type=int, 
                           help='Single port to listen on')
    port_group.add_argument('--port-range', 
                           help='Port range to listen on (e.g., 5000-5010)')
    port_group.add_argument('--ports', 
                           help='Comma-separated list of ports (e.g., 5000,5001,6000)')
    
    parser.add_argument('--hex', action='store_true', default=True,
                       help='Display data in hexadecimal format (default: True)')
    parser.add_argument('--no-hex', action='store_true',
                       help='Disable hexadecimal output')
    parser.add_argument('--ascii', action='store_true', default=True,
                       help='Display ASCII representation alongside hex (default: True)')
    parser.add_argument('--no-ascii', action='store_true',
                       help='Disable ASCII output')
    parser.add_argument('--float', action='store_true', default=True,
                       help='Display floating point values (default: True)')
    parser.add_argument('--no-float', action='store_true',
                       help='Disable floating point output')
    parser.add_argument('--endianness', choices=['little', 'big'], default='little',
                       help='Endianness for float conversion (default: little)')
    parser.add_argument('--binary', action='store_true',
                       help='Display data in binary format instead of hex')
    
    args = parser.parse_args()
    
    # Parse ports
    try:
        if args.port:
            ports = [args.port]
        elif args.port_range:
            ports = parse_ports(args.port_range)
        elif args.ports:
            ports = parse_ports(args.ports)
        else:
            ports = [5000]  # Default
    except ValueError as e:
        print(f"❌ Error parsing ports: {e}")
        sys.exit(1)
    
    # Determine output format
    hex_output = args.hex and not args.no_hex and not args.binary
    ascii_output = args.ascii and not args.no_ascii
    float_output = args.float and not args.no_float
    binary_output = args.binary
    
    if binary_output:
        hex_output = False
        ascii_output = False
        float_output = False
    
    # Validate port range
    if len(ports) > 50:
        print(f"⚠️  Warning: Listening on {len(ports)} ports may impact performance")
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted")
            sys.exit(0)
    
    # Create and start dumper
    dumper = MultiPortTCPDataDumper(
        host=args.host,
        ports=ports,
        hex_output=hex_output,
        ascii_output=ascii_output,
        float_output=float_output,
        endianness=args.endianness
    )
    
    try:
        dumper.start_server()
    except KeyboardInterrupt:
        print(f"\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
