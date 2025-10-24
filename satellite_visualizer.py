#!/usr/bin/env python3
"""
Satellite Movement Visualization
Creates a 3D video from TCP data dumper capture file
Uses ports 50038=x, 50039=y, 50040=z for satellite position
"""

import re
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from datetime import datetime
import argparse
from collections import defaultdict
import struct

class SatelliteVisualizer:
    def __init__(self, input_file):
        self.input_file = input_file
        self.x_data = []  # Port 50038
        self.y_data = []  # Port 50039
        self.z_data = []  # Port 50040
        self.timestamps = []
        
    def parse_data(self):
        """Parse the .dmp file and extract x, y, z coordinates"""
        print(f"Parsing data from {self.input_file}...")
        
        with open(self.input_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip().startswith('📊'):  # Skip summary lines
                    continue
                    
                parsed = self.parse_line(line)
                if parsed:
                    port, timestamp, hex_data, float_value = parsed
                    
                    if port == 50038:  # X coordinate
                        self.x_data.append(float_value)
                        self.timestamps.append(timestamp)
                    elif port == 50039:  # Y coordinate
                        self.y_data.append(float_value)
                    elif port == 50040:  # Z coordinate
                        self.z_data.append(float_value)
                
                if line_num % 1000 == 0:
                    print(f"Processed {line_num} lines...")
        
        # Ensure all arrays have the same length
        min_length = min(len(self.x_data), len(self.y_data), len(self.z_data))
        self.x_data = self.x_data[:min_length]
        self.y_data = self.y_data[:min_length]
        self.z_data = self.z_data[:min_length]
        self.timestamps = self.timestamps[:min_length]
        
        print(f"Extracted {min_length} data points")
        print(f"X range: {min(self.x_data):.6f} to {max(self.x_data):.6f}")
        print(f"Y range: {min(self.y_data):.6f} to {max(self.y_data):.6f}")
        print(f"Z range: {min(self.z_data):.6f} to {max(self.z_data):.6f}")
    
    def parse_line(self, line):
        """Parse a data line and extract port, timestamp, hex data, and float value"""
        # Pattern: PORT:HH:MM:SS.mmm: HEX_DATA    ASCII_DATA    = FLOAT_VALUE
        pattern = r'^(\d+):(\d{2}):(\d{2}):(\d{2})\.(\d{3}):\s+([0-9A-F\s]+)\s+.*?=\s+([+-]?[\d.]+(?:[eE][+-]?\d+)?)'
        match = re.match(pattern, line.strip())
        
        if not match:
            return None
            
        port = int(match.group(1))
        hour = int(match.group(2))
        minute = int(match.group(3))
        second = int(match.group(4))
        millisecond = int(match.group(5))
        hex_data = match.group(6)
        float_value = float(match.group(7))
        
        # Create timestamp
        timestamp = datetime.now().replace(
            hour=hour, minute=minute, second=second, microsecond=millisecond * 1000
        )
        
        return port, timestamp, hex_data, float_value
    
    def create_animation(self, output_file="satellite_movement.mp4", fps=30):
        """Create animated 3D visualization of satellite movement"""
        print(f"Creating animation: {output_file}")
        
        # Set up the figure and 3D axis
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Convert to numpy arrays
        x = np.array(self.x_data)
        y = np.array(self.y_data)
        z = np.array(self.z_data)
        
        # Calculate trajectory bounds
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        z_min, z_max = z.min(), z.max()
        
        # Add some padding
        x_range = x_max - x_min
        y_range = y_max - y_min
        z_range = z_max - z_min
        
        ax.set_xlim(x_min - 0.1 * x_range, x_max + 0.1 * x_range)
        ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)
        ax.set_zlim(z_min - 0.1 * z_range, z_max + 0.1 * z_range)
        
        # Labels and title
        ax.set_xlabel('X Position (Port 50038)')
        ax.set_ylabel('Y Position (Port 50039)')
        ax.set_zlabel('Z Position (Port 50040)')
        ax.set_title('Satellite Movement Trajectory')
        
        # Initialize plot elements
        line, = ax.plot([], [], [], 'b-', linewidth=2, alpha=0.7, label='Trajectory')
        point, = ax.plot([], [], [], 'ro', markersize=8, label='Current Position')
        trail, = ax.plot([], [], [], 'g-', linewidth=1, alpha=0.5, label='Recent Trail')
        
        # Add legend
        ax.legend()
        
        # Animation parameters
        trail_length = min(50, len(x) // 10)  # Show last 50 points or 10% of data
        
        def animate(frame):
            """Animation function"""
            if frame >= len(x):
                return line, point, trail
            
            # Current position
            current_x = x[frame]
            current_y = y[frame]
            current_z = z[frame]
            
            # Update trajectory line (from start to current)
            line.set_data_3d(x[:frame+1], y[:frame+1], z[:frame+1])
            
            # Update current position point
            point.set_data_3d([current_x], [current_y], [current_z])
            
            # Update trail (recent points)
            start_idx = max(0, frame - trail_length)
            trail.set_data_3d(x[start_idx:frame+1], y[start_idx:frame+1], z[start_idx:frame+1])
            
            # Update title with timestamp
            if frame < len(self.timestamps):
                timestamp_str = self.timestamps[frame].strftime("%H:%M:%S.%f")[:-3]
                ax.set_title(f'Satellite Movement - {timestamp_str}')
            
            return line, point, trail
        
        # Create animation
        anim = animation.FuncAnimation(
            fig, animate, frames=len(x), 
            interval=1000//fps, blit=False, repeat=True
        )
        
        # Save animation
        print("Saving animation...")
        anim.save(output_file, writer='ffmpeg', fps=fps, bitrate=1800)
        print(f"Animation saved as {output_file}")
        
        return anim
    
    def create_static_plot(self, output_file="satellite_trajectory.png"):
        """Create a static 3D plot of the satellite trajectory"""
        print(f"Creating static plot: {output_file}")
        
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Convert to numpy arrays
        x = np.array(self.x_data)
        y = np.array(self.y_data)
        z = np.array(self.z_data)
        
        # Plot trajectory
        ax.plot(x, y, z, 'b-', linewidth=2, alpha=0.7, label='Trajectory')
        
        # Mark start and end points
        ax.scatter(x[0], y[0], z[0], color='green', s=100, label='Start')
        ax.scatter(x[-1], y[-1], z[-1], color='red', s=100, label='End')
        
        # Labels and title
        ax.set_xlabel('X Position (Port 50038)')
        ax.set_ylabel('Y Position (Port 50039)')
        ax.set_zlabel('Z Position (Port 50040)')
        ax.set_title('Satellite Movement Trajectory')
        ax.legend()
        
        # Save plot
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Static plot saved as {output_file}")
        
        return fig
    
    def create_2d_projections(self, output_prefix="satellite_projection"):
        """Create 2D projections of the trajectory"""
        print("Creating 2D projections...")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Convert to numpy arrays
        x = np.array(self.x_data)
        y = np.array(self.y_data)
        z = np.array(self.z_data)
        
        # XY projection
        axes[0, 0].plot(x, y, 'b-', linewidth=2)
        axes[0, 0].scatter(x[0], y[0], color='green', s=100, label='Start')
        axes[0, 0].scatter(x[-1], y[-1], color='red', s=100, label='End')
        axes[0, 0].set_xlabel('X Position')
        axes[0, 0].set_ylabel('Y Position')
        axes[0, 0].set_title('XY Projection')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # XZ projection
        axes[0, 1].plot(x, z, 'b-', linewidth=2)
        axes[0, 1].scatter(x[0], z[0], color='green', s=100, label='Start')
        axes[0, 1].scatter(x[-1], z[-1], color='red', s=100, label='End')
        axes[0, 1].set_xlabel('X Position')
        axes[0, 1].set_ylabel('Z Position')
        axes[0, 1].set_title('XZ Projection')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # YZ projection
        axes[1, 0].plot(y, z, 'b-', linewidth=2)
        axes[1, 0].scatter(y[0], z[0], color='green', s=100, label='Start')
        axes[1, 0].scatter(y[-1], z[-1], color='red', s=100, label='End')
        axes[1, 0].set_xlabel('Y Position')
        axes[1, 0].set_ylabel('Z Position')
        axes[1, 0].set_title('YZ Projection')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # Time series
        time_points = range(len(x))
        axes[1, 1].plot(time_points, x, 'r-', label='X', linewidth=1)
        axes[1, 1].plot(time_points, y, 'g-', label='Y', linewidth=1)
        axes[1, 1].plot(time_points, z, 'b-', label='Z', linewidth=1)
        axes[1, 1].set_xlabel('Time Points')
        axes[1, 1].set_ylabel('Position')
        axes[1, 1].set_title('Position vs Time')
        axes[1, 1].legend()
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig(f"{output_prefix}.png", dpi=300, bbox_inches='tight')
        print(f"2D projections saved as {output_prefix}.png")
        
        return fig

def main():
    parser = argparse.ArgumentParser(description='Satellite Movement Visualizer')
    parser.add_argument('input_file', help='Input .dmp file')
    parser.add_argument('--video', '-v', help='Output video file (default: satellite_movement.mp4)')
    parser.add_argument('--fps', type=int, default=30, help='Video FPS (default: 30)')
    parser.add_argument('--static', '-s', help='Create static plot only')
    parser.add_argument('--projections', '-p', action='store_true', help='Create 2D projections')
    
    args = parser.parse_args()
    
    # Create visualizer
    visualizer = SatelliteVisualizer(args.input_file)
    
    # Parse data
    visualizer.parse_data()
    
    if not visualizer.x_data:
        print("No data found! Check that ports 50038, 50039, 50040 exist in the file.")
        return
    
    # Create visualizations
    if args.static:
        visualizer.create_static_plot(args.static)
    else:
        output_video = args.video or "satellite_movement.mp4"
        visualizer.create_animation(output_video, args.fps)
    
    if args.projections:
        visualizer.create_2d_projections()
    
    print("Visualization complete!")

if __name__ == "__main__":
    main()
