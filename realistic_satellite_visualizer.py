#!/usr/bin/env python3
"""
Realistic Satellite Movement Visualization
Shows actual satellite model with realistic 3D orientation changes
Uses ports 50038=x, 50039=y, 50040=z for satellite attitude
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
from matplotlib.patches import FancyBboxPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class RealisticSatelliteVisualizer:
    def __init__(self, input_file):
        self.input_file = input_file
        self.x_data = []  # Port 50038 - Roll
        self.y_data = []  # Port 50039 - Pitch  
        self.z_data = []  # Port 50040 - Yaw
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
                    
                    if port == 50038:  # Roll (X-axis rotation)
                        self.x_data.append(float_value)
                        self.timestamps.append(timestamp)
                    elif port == 50039:  # Pitch (Y-axis rotation)
                        self.y_data.append(float_value)
                    elif port == 50040:  # Yaw (Z-axis rotation)
                        self.z_data.append(float_value)
                
                if line_num % 1000 == 0:
                    print(f"Processed {line_num} lines...")
        
        # Ensure all arrays have the same length
        min_length = min(len(self.x_data), len(self.y_data), len(self.z_data))
        self.x_data = self.x_data[:min_length]
        self.y_data = self.y_data[:min_length]
        self.z_data = self.z_data[:min_length]
        self.timestamps = self.timestamps[:min_length]
        
        print(f"Extracted {min_length} attitude data points")
        print(f"Roll (X) range: {min(self.x_data):.6f} to {max(self.x_data):.6f} rad")
        print(f"Pitch (Y) range: {min(self.y_data):.6f} to {max(self.y_data):.6f} rad")
        print(f"Yaw (Z) range: {min(self.z_data):.6f} to {max(self.z_data):.6f} rad")
    
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
    
    def create_satellite_model(self):
        """Create a realistic satellite 3D model"""
        # Satellite body (main bus) - rectangular box
        body_vertices = np.array([
            [-0.5, -0.3, -0.2], [0.5, -0.3, -0.2], [0.5, 0.3, -0.2], [-0.5, 0.3, -0.2],  # Bottom
            [-0.5, -0.3, 0.2], [0.5, -0.3, 0.2], [0.5, 0.3, 0.2], [-0.5, 0.3, 0.2]   # Top
        ])
        
        # Solar panels - flat rectangles extending from sides
        panel1_vertices = np.array([
            [-0.5, -0.8, -0.1], [-0.5, -0.3, -0.1], [-0.5, -0.3, 0.1], [-0.5, -0.8, 0.1]
        ])
        
        panel2_vertices = np.array([
            [0.5, -0.3, -0.1], [0.5, -0.8, -0.1], [0.5, -0.8, 0.1], [0.5, -0.3, 0.1]
        ])
        
        # Antenna - small cylinder on top
        antenna_vertices = np.array([
            [0, 0, 0.2], [0.1, 0, 0.2], [0.1, 0, 0.4], [0, 0, 0.4]
        ])
        
        return {
            'body': body_vertices,
            'panel1': panel1_vertices,
            'panel2': panel2_vertices,
            'antenna': antenna_vertices
        }
    
    def apply_rotation(self, vertices, roll, pitch, yaw):
        """Apply roll, pitch, yaw rotations to vertices"""
        # Convert to radians if needed (assuming input is already in radians)
        roll_rad = roll
        pitch_rad = pitch
        yaw_rad = yaw
        
        # Rotation matrices
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(roll_rad), -np.sin(roll_rad)],
            [0, np.sin(roll_rad), np.cos(roll_rad)]
        ])
        
        Ry = np.array([
            [np.cos(pitch_rad), 0, np.sin(pitch_rad)],
            [0, 1, 0],
            [-np.sin(pitch_rad), 0, np.cos(pitch_rad)]
        ])
        
        Rz = np.array([
            [np.cos(yaw_rad), -np.sin(yaw_rad), 0],
            [np.sin(yaw_rad), np.cos(yaw_rad), 0],
            [0, 0, 1]
        ])
        
        # Combined rotation matrix
        R = Rz @ Ry @ Rx
        
        # Apply rotation to all vertices
        rotated_vertices = vertices @ R.T
        return rotated_vertices
    
    def create_animation(self, output_file="realistic_satellite_movement.mp4", fps=30):
        """Create animated 3D visualization of realistic satellite movement"""
        print(f"Creating realistic satellite animation: {output_file}")
        
        # Set up the figure and 3D axis
        fig = plt.figure(figsize=(15, 12))
        ax = fig.add_subplot(111, projection='3d')
        
        # Convert to numpy arrays
        roll_data = np.array(self.x_data)
        pitch_data = np.array(self.y_data)
        yaw_data = np.array(self.z_data)
        
        # Scale the rotations for better visualization (multiply by 100 for visibility)
        roll_data *= 100
        pitch_data *= 100
        yaw_data *= 100
        
        # Set axis limits
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        ax.set_zlim(-2, 2)
        
        # Labels and title
        ax.set_xlabel('X Axis (Roll)', fontsize=12)
        ax.set_ylabel('Y Axis (Pitch)', fontsize=12)
        ax.set_zlabel('Z Axis (Yaw)', fontsize=12)
        ax.set_title('Realistic Satellite Attitude Control', fontsize=14, fontweight='bold')
        
        # Create satellite model
        satellite_model = self.create_satellite_model()
        
        # Initialize plot elements
        body_poly = None
        panel1_poly = None
        panel2_poly = None
        antenna_poly = None
        
        # Add coordinate system reference
        ax.quiver(0, 0, 0, 1.5, 0, 0, color='red', alpha=0.7, linewidth=2, label='X (Roll)')
        ax.quiver(0, 0, 0, 0, 1.5, 0, color='green', alpha=0.7, linewidth=2, label='Y (Pitch)')
        ax.quiver(0, 0, 0, 0, 0, 1.5, color='blue', alpha=0.7, linewidth=2, label='Z (Yaw)')
        
        # Add legend
        ax.legend()
        
        def animate(frame):
            """Animation function"""
            nonlocal body_poly, panel1_poly, panel2_poly, antenna_poly
            
            if frame >= len(roll_data):
                return
            
            # Clear previous satellite
            if body_poly:
                body_poly.remove()
            if panel1_poly:
                panel1_poly.remove()
            if panel2_poly:
                panel2_poly.remove()
            if antenna_poly:
                antenna_poly.remove()
            
            # Get current attitude
            current_roll = roll_data[frame]
            current_pitch = pitch_data[frame]
            current_yaw = yaw_data[frame]
            
            # Apply rotations to satellite components
            rotated_body = self.apply_rotation(satellite_model['body'], current_roll, current_pitch, current_yaw)
            rotated_panel1 = self.apply_rotation(satellite_model['panel1'], current_roll, current_pitch, current_yaw)
            rotated_panel2 = self.apply_rotation(satellite_model['panel2'], current_roll, current_pitch, current_yaw)
            rotated_antenna = self.apply_rotation(satellite_model['antenna'], current_roll, current_pitch, current_yaw)
            
            # Create faces for the satellite body
            body_faces = [
                [rotated_body[0], rotated_body[1], rotated_body[2], rotated_body[3]],  # Bottom
                [rotated_body[4], rotated_body[5], rotated_body[6], rotated_body[7]],  # Top
                [rotated_body[0], rotated_body[1], rotated_body[5], rotated_body[4]],  # Front
                [rotated_body[2], rotated_body[3], rotated_body[7], rotated_body[6]],  # Back
                [rotated_body[0], rotated_body[3], rotated_body[7], rotated_body[4]],  # Left
                [rotated_body[1], rotated_body[2], rotated_body[6], rotated_body[5]]   # Right
            ]
            
            # Draw satellite components
            body_poly = Poly3DCollection(body_faces, alpha=0.8, facecolor='lightgray', edgecolor='black', linewidth=1)
            ax.add_collection3d(body_poly)
            
            # Draw solar panels
            panel1_faces = [[rotated_panel1[0], rotated_panel1[1], rotated_panel1[2], rotated_panel1[3]]]
            panel1_poly = Poly3DCollection(panel1_faces, alpha=0.9, facecolor='darkblue', edgecolor='black', linewidth=1)
            ax.add_collection3d(panel1_poly)
            
            panel2_faces = [[rotated_panel2[0], rotated_panel2[1], rotated_panel2[2], rotated_panel2[3]]]
            panel2_poly = Poly3DCollection(panel2_faces, alpha=0.9, facecolor='darkblue', edgecolor='black', linewidth=1)
            ax.add_collection3d(panel2_poly)
            
            # Draw antenna
            antenna_faces = [[rotated_antenna[0], rotated_antenna[1], rotated_antenna[2], rotated_antenna[3]]]
            antenna_poly = Poly3DCollection(antenna_faces, alpha=0.9, facecolor='red', edgecolor='black', linewidth=1)
            ax.add_collection3d(antenna_poly)
            
            # Update title with attitude information
            if frame < len(self.timestamps):
                timestamp_str = self.timestamps[frame].strftime("%H:%M:%S.%f")[:-3]
                roll_deg = np.degrees(current_roll)
                pitch_deg = np.degrees(current_pitch)
                yaw_deg = np.degrees(current_yaw)
                ax.set_title(f'Realistic Satellite Attitude Control\n{timestamp_str}\n'
                           f'Roll: {roll_deg:.2f}° | Pitch: {pitch_deg:.2f}° | Yaw: {yaw_deg:.2f}°', 
                           fontsize=12, fontweight='bold')
            
            return body_poly, panel1_poly, panel2_poly, antenna_poly
        
        # Create animation
        anim = animation.FuncAnimation(
            fig, animate, frames=len(roll_data), 
            interval=1000//fps, blit=False, repeat=True
        )
        
        # Save animation
        print("Saving realistic satellite animation...")
        anim.save(output_file, writer='ffmpeg', fps=fps, bitrate=2000)
        print(f"Realistic satellite animation saved as {output_file}")
        
        return anim
    
    def create_attitude_plot(self, output_file="satellite_attitude_analysis.png"):
        """Create detailed attitude analysis plots"""
        print(f"Creating attitude analysis plot: {output_file}")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Convert to numpy arrays
        roll_data = np.array(self.x_data)
        pitch_data = np.array(self.y_data)
        yaw_data = np.array(self.z_data)
        
        # Convert to degrees for better readability
        roll_deg = np.degrees(roll_data)
        pitch_deg = np.degrees(pitch_data)
        yaw_deg = np.degrees(yaw_data)
        
        time_points = range(len(roll_data))
        
        # Roll vs Time
        axes[0, 0].plot(time_points, roll_deg, 'r-', linewidth=2, label='Roll')
        axes[0, 0].set_xlabel('Time Points')
        axes[0, 0].set_ylabel('Roll Angle (degrees)')
        axes[0, 0].set_title('Roll Attitude vs Time')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].legend()
        
        # Pitch vs Time
        axes[0, 1].plot(time_points, pitch_deg, 'g-', linewidth=2, label='Pitch')
        axes[0, 1].set_xlabel('Time Points')
        axes[0, 1].set_ylabel('Pitch Angle (degrees)')
        axes[0, 1].set_title('Pitch Attitude vs Time')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].legend()
        
        # Yaw vs Time
        axes[1, 0].plot(time_points, yaw_deg, 'b-', linewidth=2, label='Yaw')
        axes[1, 0].set_xlabel('Time Points')
        axes[1, 0].set_ylabel('Yaw Angle (degrees)')
        axes[1, 0].set_title('Yaw Attitude vs Time')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].legend()
        
        # All attitudes together
        axes[1, 1].plot(time_points, roll_deg, 'r-', linewidth=2, label='Roll', alpha=0.8)
        axes[1, 1].plot(time_points, pitch_deg, 'g-', linewidth=2, label='Pitch', alpha=0.8)
        axes[1, 1].plot(time_points, yaw_deg, 'b-', linewidth=2, label='Yaw', alpha=0.8)
        axes[1, 1].set_xlabel('Time Points')
        axes[1, 1].set_ylabel('Attitude Angle (degrees)')
        axes[1, 1].set_title('All Attitude Angles vs Time')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Attitude analysis plot saved as {output_file}")
        
        return fig

def main():
    parser = argparse.ArgumentParser(description='Realistic Satellite Movement Visualizer')
    parser.add_argument('input_file', help='Input .dmp file')
    parser.add_argument('--video', '-v', help='Output video file (default: realistic_satellite_movement.mp4)')
    parser.add_argument('--fps', type=int, default=30, help='Video FPS (default: 30)')
    parser.add_argument('--attitude', '-a', action='store_true', help='Create attitude analysis plots')
    
    args = parser.parse_args()
    
    # Create visualizer
    visualizer = RealisticSatelliteVisualizer(args.input_file)
    
    # Parse data
    visualizer.parse_data()
    
    if not visualizer.x_data:
        print("No data found! Check that ports 50038, 50039, 50040 exist in the file.")
        return
    
    # Create visualizations
    output_video = args.video or "realistic_satellite_movement.mp4"
    visualizer.create_animation(output_video, args.fps)
    
    if args.attitude:
        visualizer.create_attitude_plot()
    
    print("Realistic satellite visualization complete!")

if __name__ == "__main__":
    main()
