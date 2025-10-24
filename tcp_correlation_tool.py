#!/usr/bin/env python3
"""
TCP Data Dumper Timestamp Correlation Tool

Analyzes TCP data dumper capture files to correlate timestamps across all ports
and group data within 10ms time windows.
"""

import re
import sys
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import argparse

class TimestampCorrelator:
    """Correlates timestamps across multiple ports"""
    
    def __init__(self, time_window_ms: float = 10.0):
        self.time_window_ms = time_window_ms
        self.time_window_seconds = time_window_ms / 1000.0
        self.port_data = defaultdict(list)  # port -> [(timestamp, data_line)]
        self.correlated_groups = []
        
    def parse_line(self, line: str) -> Optional[Tuple[int, datetime, str]]:
        """Parse a data line and extract port, timestamp, and data"""
        # Pattern: PORT:HH:MM:SS.mmm: DATA...
        pattern = r'^(\d+):(\d{2}):(\d{2}):(\d{2})\.(\d{3}):(.+)$'
        match = re.match(pattern, line.strip())
        
        if not match:
            return None
            
        port = int(match.group(1))
        hour = int(match.group(2))
        minute = int(match.group(3))
        second = int(match.group(4))
        millisecond = int(match.group(5))
        data = match.group(6)
        
        # Create datetime object (using today's date)
        today = datetime.now().date()
        timestamp = datetime.combine(today, datetime.min.time().replace(
            hour=hour, minute=minute, second=second, microsecond=millisecond * 1000
        ))
        
        return port, timestamp, data
    
    def load_data(self, filename: str):
        """Load data from capture file"""
        print(f"Loading data from {filename}...")
        
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip().startswith('📊'):  # Skip summary lines
                    continue
                    
                parsed = self.parse_line(line)
                if parsed:
                    port, timestamp, data = parsed
                    self.port_data[port].append((timestamp, data))
                    
                if line_num % 1000 == 0:
                    print(f"Processed {line_num} lines...")
        
        print(f"Loaded data for {len(self.port_data)} ports")
        for port in sorted(self.port_data.keys()):
            print(f"  Port {port}: {len(self.port_data[port])} entries")
    
    def correlate_timestamps(self):
        """Correlate timestamps across all ports"""
        print(f"Correlating timestamps with {self.time_window_ms}ms window...")
        
        # Get all unique timestamps
        all_timestamps = set()
        for port_data in self.port_data.values():
            for timestamp, _ in port_data:
                all_timestamps.add(timestamp)
        
        all_timestamps = sorted(all_timestamps)
        print(f"Found {len(all_timestamps)} unique timestamps")
        
        # Group timestamps within the time window
        groups = []
        current_group = []
        
        for timestamp in all_timestamps:
            if not current_group:
                current_group = [timestamp]
            else:
                # Check if this timestamp is within the time window of the group
                time_diff = (timestamp - current_group[0]).total_seconds()
                if time_diff <= self.time_window_seconds:
                    current_group.append(timestamp)
                else:
                    # Start a new group
                    if len(current_group) > 1:  # Only save groups with multiple timestamps
                        groups.append(current_group)
                    current_group = [timestamp]
        
        # Don't forget the last group
        if len(current_group) > 1:
            groups.append(current_group)
        
        print(f"Found {len(groups)} correlated timestamp groups")
        
        # For each group, collect data from all ports
        for group_idx, timestamp_group in enumerate(groups):
            group_data = {}
            group_start_time = timestamp_group[0]
            
            for port in sorted(self.port_data.keys()):
                port_entries = []
                for timestamp, data in self.port_data[port]:
                    time_diff = (timestamp - group_start_time).total_seconds()
                    if abs(time_diff) <= self.time_window_seconds:
                        port_entries.append((timestamp, data, time_diff))
                
                if port_entries:
                    # Sort by time difference and take the closest one
                    port_entries.sort(key=lambda x: abs(x[2]))
                    group_data[port] = port_entries[0]
            
            if len(group_data) >= 2:  # Only include groups with data from multiple ports
                self.correlated_groups.append((group_start_time, group_data))
        
        print(f"Created {len(self.correlated_groups)} correlated groups")
    
    def generate_report(self, output_file: Optional[str] = None):
        """Generate correlation report"""
        if not self.correlated_groups:
            print("No correlated groups found!")
            return
        
        # Determine output destination
        if output_file:
            f = open(output_file, 'w')
            print(f"Writing report to {output_file}...")
        else:
            f = sys.stdout
            print("\n" + "="*120)
            print("TCP DATA DUMPER TIMESTAMP CORRELATION REPORT")
            print("="*120)
        
        # Header
        ports = sorted(set(port for _, group_data in self.correlated_groups for port in group_data.keys()))
        header = f"{'Timestamp':<20} {'Max Diff (ms)':<12}"
        for port in ports:
            header += f" {f'Port {port}':<15}"
        f.write(header + "\n")
        f.write("-" * len(header) + "\n")
        
        # Data rows
        for group_start_time, group_data in self.correlated_groups[:100]:  # Limit to first 100 groups
            # Calculate time differences
            time_diffs = []
            port_times = {}
            
            for port, (timestamp, data, time_diff) in group_data.items():
                time_diffs.append(abs(time_diff))
                port_times[port] = f"{time_diff*1000:+.1f}ms"
            
            max_diff_ms = max(time_diffs) * 1000 if time_diffs else 0
            
            # Format timestamp
            timestamp_str = group_start_time.strftime("%H:%M:%S.%f")[:-3]
            
            # Create row
            row = f"{timestamp_str:<20} {max_diff_ms:<12.1f}"
            for port in ports:
                if port in port_times:
                    row += f" {port_times[port]:<15}"
                else:
                    row += f" {'--':<15}"
            
            f.write(row + "\n")
        
        # Summary
        f.write("\n" + "="*120 + "\n")
        f.write("SUMMARY\n")
        f.write("="*120 + "\n")
        f.write(f"Total correlated groups: {len(self.correlated_groups)}\n")
        f.write(f"Time window: {self.time_window_ms}ms\n")
        f.write(f"Ports analyzed: {sorted(ports)}\n")
        
        # Calculate statistics
        if self.correlated_groups:
            all_max_diffs = []
            for _, group_data in self.correlated_groups:
                time_diffs = [abs(time_diff) for _, _, time_diff in group_data.values()]
                if time_diffs:
                    all_max_diffs.append(max(time_diffs) * 1000)
            
            if all_max_diffs:
                f.write(f"Average max time difference: {sum(all_max_diffs)/len(all_max_diffs):.2f}ms\n")
                f.write(f"Maximum time difference: {max(all_max_diffs):.2f}ms\n")
                f.write(f"Minimum time difference: {min(all_max_diffs):.2f}ms\n")
        
        if output_file:
            f.close()
            print(f"Report written to {output_file}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='TCP Data Dumper Timestamp Correlation Tool')
    parser.add_argument('input_file', help='Input capture file (.dmp)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--window', '-w', type=float, default=10.0,
                       help='Time window in milliseconds (default: 10.0)')
    parser.add_argument('--max-groups', type=int, default=100,
                       help='Maximum number of groups to display (default: 100)')
    
    args = parser.parse_args()
    
    # Create correlator
    correlator = TimestampCorrelator(time_window_ms=args.window)
    
    # Load and correlate data
    correlator.load_data(args.input_file)
    correlator.correlate_timestamps()
    
    # Generate report
    correlator.generate_report(args.output)

if __name__ == "__main__":
    main()
