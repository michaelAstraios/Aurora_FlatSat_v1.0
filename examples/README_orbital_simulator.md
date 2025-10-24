# MATLAB Orbital Simulator for FlatSat

This directory contains MATLAB programs that simulate realistic orbital mechanics and integrate with the FlatSat Device Simulator.

## Files

### 1. `orbital_simulator.m`
**Main orbital mechanics simulator** - A comprehensive orbital dynamics simulation including:

- **Keplerian orbit propagation** with 4th-order Runge-Kutta integration
- **Realistic orbital perturbations**:
  - J2 harmonic (Earth's oblateness)
  - Atmospheric drag (exponential density model)
  - Solar radiation pressure
- **Attitude dynamics** with quaternion integration
- **Sensor data generation**:
  - ARS (Attitude Rate Sensor) data with noise and bias drift
  - Magnetometer data using Earth's magnetic field model
  - Reaction wheel data with thermal and electrical models
- **Real-time 3D visualization** of orbit trajectory
- **Post-simulation analysis** and data export

### 2. `flatsat_orbital_integration.m`
**FlatSat integration script** - Connects the orbital simulator with your existing FlatSat simulator:

- Sends realistic orbital data to FlatSat simulator via TCP
- Matches your existing port configuration (ARS: 5000-5011, Mag: 6000-6002, RW: 7000-7003)
- Generates data at realistic rates (ARS: 10Hz, Mag: 1Hz, RW: 0.1Hz)
- Handles connection errors gracefully

### 3. `matlab_simulator_sender.m`
**Original MATLAB simulator** - Your existing MATLAB data sender (unchanged)

## Usage

### Running the Full Orbital Simulator

```matlab
% Run the complete orbital simulation
orbital_simulator()
```

This will:
- Simulate a 1-hour orbital mission
- Display real-time orbit visualization
- Generate realistic sensor data
- Save results to `orbital_simulation_results.mat`

### Running FlatSat Integration

```matlab
% Connect orbital simulator to FlatSat simulator
flatsat_orbital_integration()
```

**Prerequisites:**
1. Start your FlatSat simulator first:
   ```bash
   python start_simulator.py
   ```

2. Then run the MATLAB integration script

### Configuration

Both scripts can be easily configured by modifying the parameters at the top:

```matlab
% Simulation parameters
sim_duration = 3600;        % Duration in seconds
dt = 0.1;                   % Time step

% Initial orbital elements (ISS-like orbit)
initial_orbit.a = 6798000;      % Semi-major axis (m)
initial_orbit.e = 0.0001;       % Eccentricity
initial_orbit.i = deg2rad(51.6); % Inclination

% Satellite parameters
satellite.mass = 10.0;      % kg
satellite.area = 0.1;       % m^2
satellite.cd = 2.2;         % Drag coefficient
```

## Features

### Orbital Mechanics
- **Realistic orbit propagation** using classical orbital elements
- **Multiple perturbation sources** affecting the orbit
- **Altitude decay** due to atmospheric drag
- **Orbital plane changes** due to J2 effects

### Attitude Dynamics
- **Quaternion-based attitude representation** (avoids gimbal lock)
- **Gravity gradient torques** affecting attitude
- **Realistic attitude drift** and perturbations

### Sensor Simulation
- **ARS data**: Angular rates + integrated angles with noise and bias drift
- **Magnetometer data**: Earth's magnetic field in body frame with noise
- **Reaction wheel data**: Speed, current, temperature, voltage with realistic variations

### Visualization
- **3D orbit trajectory** with Earth visualization
- **Real-time altitude tracking**
- **Attitude quaternion plots**
- **Angular velocity monitoring**

## Output Data

The simulator generates comprehensive data arrays:

- `time_array`: Time vector
- `position_array`: 3D position vectors (m)
- `velocity_array`: 3D velocity vectors (m/s)
- `attitude_array`: Quaternion attitude vectors
- `omega_array`: Angular velocity vectors (rad/s)
- `altitude_array`: Altitude above Earth (m)
- `ars_data_array`: ARS sensor data (12 channels)
- `mag_data_array`: Magnetometer data (3 channels)
- `rw_data_array`: Reaction wheel data (4 channels)

## Integration with FlatSat

The integration script sends data to your FlatSat simulator at realistic rates:

- **ARS data**: 10 Hz (every 0.1s)
- **Magnetometer data**: 1 Hz (every 1s)
- **Reaction wheel data**: 0.1 Hz (every 10s)

Data is sent via TCP to the configured simulator IP and port, matching your existing FlatSat infrastructure.

## Physical Models

### Atmospheric Density Model
```
ρ(h) = ρ₀ * exp(-h/H)
```
Where:
- ρ₀ = 1.225 kg/m³ (sea level density)
- H = 8400 m (scale height)
- h = altitude above Earth's surface

### Earth's Magnetic Field Model
Simplified dipole model:
```
Bx = B₀ * cos(lat) * cos(lon)
By = B₀ * cos(lat) * sin(lon)
Bz = B₀ * sin(lat)
```
Where B₀ = 3.12×10⁻⁵ T

### J2 Perturbation
Accounts for Earth's oblateness:
```
a_J2 = -3/2 * J₂ * μ * Rₑ² / r⁴ * [x(1-5z²/r²), y(1-5z²/r²), z(3-5z²/r²)]
```

## Requirements

- MATLAB R2018b or later
- Instrument Control Toolbox (for TCP communication)
- Your existing FlatSat simulator running

## Example Output

```
Starting orbital simulation...
Duration: 3600.0 seconds (60.0 minutes)
Time step: 0.100 seconds
Initial altitude: 400.0 km
Time: 10.0 s, Altitude: 400.0 km, Speed: 7668.5 m/s
Time: 20.0 s, Altitude: 400.0 km, Speed: 7668.5 m/s
...
Simulation completed in 45.23 seconds

=== SIMULATION ANALYSIS ===
Initial altitude: 400.00 km
Final altitude: 399.95 km
Altitude change: -0.05 km
Initial speed: 7668.50 m/s
Final speed: 7668.45 m/s
Attitude drift: 0.000123
ARS noise level: 1.00e-04 rad/s
Magnetometer noise level: 100.00 nT
```

This orbital simulator provides a realistic foundation for testing your FlatSat hardware and software with actual orbital mechanics!


