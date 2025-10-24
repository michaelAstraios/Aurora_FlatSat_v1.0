#!/usr/bin/env python3
"""
TCP ARS System Verification Script

This script verifies that the TCP-based ARS system is working correctly
by testing all components and providing a comprehensive status report.
"""

import socket
import struct
import time
import threading
import subprocess
import sys
import os
import json
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TCPARSVerifier:
    """Verification tool for TCP ARS system"""
    
    def __init__(self, host='127.0.0.1', start_port=5000, num_ports=12):
        self.host = host
        self.start_port = start_port
        self.num_ports = num_ports
        self.test_results = {}
        
    def check_files_exist(self) -> bool:
        """Check if all required TCP ARS files exist"""
        logger.info("Checking TCP ARS files...")
        
        required_files = [
            'ars_tcp_socket_reader.py',
            'ars_tcp_socket_reader_enhanced.py',
            'ars_tcp_socket_reader_endianness.py',
            'test_ars_tcp_client.py',
            'start_ars_tcp_reader.sh',
            'install_tcp.sh',
            'README_TCP_INSTALLER.md'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"Missing files: {missing_files}")
            return False
        
        logger.info("✅ All required TCP ARS files exist")
        return True
    
    def check_python_imports(self) -> bool:
        """Check if Python can import required modules"""
        logger.info("Checking Python imports...")
        
        try:
            import socket
            import struct
            import threading
            import time
            import json
            import logging
            logger.info("✅ All required Python modules available")
            return True
        except ImportError as e:
            logger.error(f"❌ Missing Python module: {e}")
            return False
    
    def check_ports_available(self) -> bool:
        """Check if required ports are available"""
        logger.info("Checking port availability...")
        
        unavailable_ports = []
        for i in range(self.num_ports):
            port = self.start_port + i
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind((self.host, port))
                sock.close()
            except OSError:
                unavailable_ports.append(port)
        
        if unavailable_ports:
            logger.warning(f"⚠️  Ports in use: {unavailable_ports}")
            return False
        
        logger.info("✅ All required ports are available")
        return True
    
    def test_tcp_ars_reader(self) -> bool:
        """Test the TCP ARS reader functionality"""
        logger.info("Testing TCP ARS reader...")
        
        try:
            # Test help command
            result = subprocess.run([
                sys.executable, 'ars_tcp_socket_reader_endianness.py', '--help'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("✅ TCP ARS reader help command works")
                return True
            else:
                logger.error(f"❌ TCP ARS reader help failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ TCP ARS reader help command timed out")
            return False
        except Exception as e:
            logger.error(f"❌ TCP ARS reader test failed: {e}")
            return False
    
    def test_tcp_client(self) -> bool:
        """Test the TCP test client"""
        logger.info("Testing TCP test client...")
        
        try:
            # Test help command
            result = subprocess.run([
                sys.executable, 'test_ars_tcp_client.py', '--help'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("✅ TCP test client help command works")
                return True
            else:
                logger.error(f"❌ TCP test client help failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ TCP test client help command timed out")
            return False
        except Exception as e:
            logger.error(f"❌ TCP test client test failed: {e}")
            return False
    
    def test_configuration_files(self) -> bool:
        """Test configuration files"""
        logger.info("Testing configuration files...")
        
        config_files = [
            'config/simulator_config_tcp.json',
            'config/simulator_config.json'
        ]
        
        for config_file in config_files:
            if not os.path.exists(config_file):
                logger.error(f"❌ Configuration file missing: {config_file}")
                return False
            
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Check for TCP-specific settings
                if 'devices' in config and 'ars' in config['devices']:
                    logger.info(f"✅ Configuration file valid: {config_file}")
                else:
                    logger.warning(f"⚠️  Configuration file missing ARS settings: {config_file}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in {config_file}: {e}")
                return False
            except Exception as e:
                logger.error(f"❌ Error reading {config_file}: {e}")
                return False
        
        return True
    
    def test_startup_script(self) -> bool:
        """Test the startup script"""
        logger.info("Testing startup script...")
        
        script_path = 'start_ars_tcp_reader.sh'
        if not os.path.exists(script_path):
            logger.error(f"❌ Startup script missing: {script_path}")
            return False
        
        if not os.access(script_path, os.X_OK):
            logger.error(f"❌ Startup script not executable: {script_path}")
            return False
        
        logger.info("✅ Startup script exists and is executable")
        return True
    
    def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run comprehensive verification test"""
        logger.info("=" * 60)
        logger.info("TCP ARS System Verification")
        logger.info("=" * 60)
        
        tests = [
            ("File Existence", self.check_files_exist),
            ("Python Imports", self.check_python_imports),
            ("Port Availability", self.check_ports_available),
            ("TCP ARS Reader", self.test_tcp_ars_reader),
            ("TCP Test Client", self.test_tcp_client),
            ("Configuration Files", self.test_configuration_files),
            ("Startup Script", self.test_startup_script)
        ]
        
        results = {}
        for test_name, test_func in tests:
            logger.info(f"\n--- {test_name} ---")
            try:
                results[test_name] = test_func()
            except Exception as e:
                logger.error(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print verification summary"""
        logger.info("\n" + "=" * 60)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name:20} {status}")
        
        logger.info("-" * 60)
        logger.info(f"Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - TCP ARS system is ready!")
            logger.info("\nNext steps:")
            logger.info("1. Start the TCP ARS reader: ./start_ars_tcp_reader.sh")
            logger.info("2. Test the system: python3 test_ars_tcp_client.py --duration 10")
            logger.info("3. Monitor logs for any issues")
        else:
            logger.info("⚠️  SOME TESTS FAILED - Please address the issues above")
            logger.info("\nCommon solutions:")
            logger.info("1. Ensure all files are present in the installer_tcp directory")
            logger.info("2. Check that required ports (5000-5011) are available")
            logger.info("3. Verify Python 3.6+ is installed")
            logger.info("4. Run: chmod +x *.sh to make scripts executable")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TCP ARS System Verification')
    parser.add_argument('--host', default='127.0.0.1', help='Host to test')
    parser.add_argument('--start-port', type=int, default=5000, help='Starting port')
    parser.add_argument('--num-ports', type=int, default=12, help='Number of ports')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create verifier and run tests
    verifier = TCPARSVerifier(args.host, args.start_port, args.num_ports)
    results = verifier.run_comprehensive_test()
    verifier.print_summary(results)
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
