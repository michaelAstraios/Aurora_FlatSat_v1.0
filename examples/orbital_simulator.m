function orbital_simulator()
    % ORBITAL MECHANICS SIMULATOR FOR FLATSAT
    % 
    % This MATLAB program simulates realistic orbital mechanics including:
    % - Keplerian orbit propagation
    % - Orbital perturbations (J2, atmospheric drag, SRP)
    % - Attitude dynamics
    % - Sensor data generation (ARS, magnetometer, reaction wheels)
    % - Real-time visualization
    % - Integration with FlatSat simulator
    
    clc; clear; close all;
    
    % =========================================================================
    % SIMULATION CONFIGURATION
    % =========================================================================
    
    % Simulation parameters
    sim_duration = 3600;        % Simulation duration (seconds) - 1 hour
    dt = 0.1;                   % Time step (seconds)
    time_steps = sim_duration / dt;
    
    % Satellite parameters
    satellite.mass = 10.0;      % kg
    satellite.area = 0.1;       % m^2 (cross-sectional area)
    satellite.cd = 2.2;         % Drag coefficient
    satellite.cr = 1.8;         % Radiation pressure coefficient
    
    % Initial orbital elements (ISS-like orbit)
    initial_orbit.a = 6798000;      % Semi-major axis (m) - ~400 km altitude
    initial_orbit.e = 0.0001;       % Eccentricity (nearly circular)
    initial_orbit.i = deg2rad(51.6); % Inclination (degrees to radians)
    initial_orbit.Omega = deg2rad(0); % Right ascension of ascending node
    initial_orbit.omega = deg2rad(0); % Argument of periapsis
    initial_orbit.nu = deg2rad(0);    % True anomaly
    
    % Initial attitude (quaternion: [w, x, y, z])
    initial_attitude = [1, 0, 0, 0]; % Identity quaternion (no rotation)
    
    % Initial angular velocity (rad/s)
    initial_omega = [0.01, 0.005, -0.02]; % Small initial rotation rates
    
    % =========================================================================
    % PHYSICAL CONSTANTS
    % =========================================================================
    
    % Earth parameters
    mu = 3.986004418e14;        % Earth's gravitational parameter (m^3/s^2)
    Re = 6378137.0;             % Earth's radius (m)
    J2 = 1.08263e-3;            % J2 harmonic coefficient
    
    % Atmospheric parameters
    rho0 = 1.225;               % Sea level air density (kg/m^3)
    H = 8400;                   % Scale height (m)
    
    % Solar radiation pressure
    P_solar = 4.56e-6;          % Solar radiation pressure (N/m^2)
    
    % =========================================================================
    % INITIALIZATION
    % =========================================================================
    
    % Convert orbital elements to Cartesian state
    [r0, v0] = oe2cartesian(initial_orbit, mu);
    
    % Initialize state vectors
    state.r = r0;               % Position vector (m)
    state.v = v0;               % Velocity vector (m/s)
    state.q = initial_attitude; % Attitude quaternion
    state.omega = initial_omega; % Angular velocity (rad/s)
    
    % Initialize storage arrays
    time_array = zeros(time_steps, 1);
    position_array = zeros(time_steps, 3);
    velocity_array = zeros(time_steps, 3);
    attitude_array = zeros(time_steps, 4);
    omega_array = zeros(time_steps, 3);
    altitude_array = zeros(time_steps, 1);
    
    % Sensor data arrays
    ars_data_array = zeros(time_steps, 12);
    mag_data_array = zeros(time_steps, 3);
    rw_data_array = zeros(time_steps, 4);
    
    % =========================================================================
    % MAIN SIMULATION LOOP
    % =========================================================================
    
    fprintf('Starting orbital simulation...\n');
    fprintf('Duration: %.1f seconds (%.1f minutes)\n', sim_duration, sim_duration/60);
    fprintf('Time step: %.3f seconds\n', dt);
    fprintf('Initial altitude: %.1f km\n', (norm(state.r) - Re)/1000);
    
    % Setup visualization
    setup_visualization();
    
    tic;
    for step = 1:time_steps
        current_time = (step - 1) * dt;
        
        % =================================================================
        % ORBITAL DYNAMICS
        % =================================================================
        
        % Calculate orbital perturbations
        [a_perturb, r_mag] = calculate_perturbations(state.r, state.v, satellite, mu, Re, J2, rho0, H, P_solar);
        
        % Propagate orbit using RK4
        [state.r, state.v] = rk4_orbit(state.r, state.v, a_perturb, dt, mu);
        
        % =================================================================
        % ATTITUDE DYNAMICS
        % =================================================================
        
        % Calculate attitude perturbations (gravity gradient, magnetic torque)
        tau_perturb = calculate_attitude_perturbations(state.r, state.q, state.omega, satellite);
        
        % Propagate attitude using quaternion integration
        [state.q, state.omega] = propagate_attitude(state.q, state.omega, tau_perturb, dt, satellite);
        
        % =================================================================
        % SENSOR DATA GENERATION
        % =================================================================
        
        % Generate ARS data (angular rates + integrated angles)
        ars_data = generate_realistic_ars_data(state.omega, state.q, current_time);
        
        % Generate magnetometer data (Earth's magnetic field)
        mag_data = generate_realistic_magnetometer_data(state.r, state.q, current_time);
        
        % Generate reaction wheel data
        rw_data = generate_realistic_rw_data(state.omega, current_time);
        
        % =================================================================
        % DATA STORAGE
        % =================================================================
        
        time_array(step) = current_time;
        position_array(step, :) = state.r;
        velocity_array(step, :) = state.v;
        attitude_array(step, :) = state.q;
        omega_array(step, :) = state.omega;
        altitude_array(step) = r_mag - Re;
        
        ars_data_array(step, :) = ars_data;
        mag_data_array(step, :) = mag_data;
        rw_data_array(step, :) = rw_data;
        
        % =================================================================
        % VISUALIZATION UPDATE
        % =================================================================
        
        if mod(step, 100) == 0  % Update every 10 seconds
            update_visualization(position_array(1:step, :), attitude_array(1:step, :), current_time);
            fprintf('Time: %.1f s, Altitude: %.1f km, Speed: %.1f m/s\n', ...
                    current_time, altitude_array(step)/1000, norm(state.v));
        end
        
        % =================================================================
        % FLATSAT SIMULATOR INTEGRATION
        % =================================================================
        
        if mod(step, 10) == 0  % Send data every 1 second
            send_to_flatsat_simulator(ars_data, mag_data, rw_data, current_time);
        end
    end
    
    simulation_time = toc;
    fprintf('\nSimulation completed in %.2f seconds\n', simulation_time);
    
    % =========================================================================
    % POST-SIMULATION ANALYSIS
    % =========================================================================
    
    analyze_results(time_array, position_array, velocity_array, attitude_array, ...
                   omega_array, altitude_array, ars_data_array, mag_data_array, rw_data_array);
    
    % Save results
    save_simulation_data(time_array, position_array, velocity_array, attitude_array, ...
                        omega_array, altitude_array, ars_data_array, mag_data_array, rw_data_array);
    
    fprintf('Simulation data saved to orbital_simulation_results.mat\n');
end

% =========================================================================
% ORBITAL MECHANICS FUNCTIONS
% =========================================================================

function [r, v] = oe2cartesian(oe, mu)
    % Convert orbital elements to Cartesian coordinates
    
    a = oe.a;
    e = oe.e;
    i = oe.i;
    Omega = oe.Omega;
    omega = oe.omega;
    nu = oe.nu;
    
    % Calculate position and velocity in perifocal frame
    p = a * (1 - e^2);
    r_mag = p / (1 + e * cos(nu));
    
    r_pf = [r_mag * cos(nu); r_mag * sin(nu); 0];
    v_pf = sqrt(mu/p) * [-sin(nu); e + cos(nu); 0];
    
    % Rotation matrices
    R3_Omega = [cos(Omega) sin(Omega) 0; -sin(Omega) cos(Omega) 0; 0 0 1];
    R1_i = [1 0 0; 0 cos(i) sin(i); 0 -sin(i) cos(i)];
    R3_omega = [cos(omega) sin(omega) 0; -sin(omega) cos(omega) 0; 0 0 1];
    
    % Transform to inertial frame
    R = R3_Omega * R1_i * R3_omega;
    r = R * r_pf;
    v = R * v_pf;
end

function [a_perturb, r_mag] = calculate_perturbations(r, v, satellite, mu, Re, J2, rho0, H, P_solar)
    % Calculate orbital perturbations
    
    r_mag = norm(r);
    r_unit = r / r_mag;
    
    % J2 perturbation
    z_over_r = r(3) / r_mag;
    a_j2 = -3/2 * J2 * mu * Re^2 / r_mag^4 * ...
           [r_unit(1) * (1 - 5*z_over_r^2);
            r_unit(2) * (1 - 5*z_over_r^2);
            r_unit(3) * (3 - 5*z_over_r^2)];
    
    % Atmospheric drag
    altitude = r_mag - Re;
    if altitude > 0
        rho = rho0 * exp(-altitude / H);
        v_rel = v; % Assuming no atmosphere rotation
        v_rel_mag = norm(v_rel);
        a_drag = -0.5 * rho * satellite.cd * satellite.area / satellite.mass * ...
                 v_rel_mag * v_rel;
    else
        a_drag = [0; 0; 0];
    end
    
    % Solar radiation pressure (simplified)
    a_srp = P_solar * satellite.cr * satellite.area / satellite.mass * ...
            [1; 0; 0]; % Simplified: always in +X direction
    
    % Total perturbation
    a_perturb = a_j2 + a_drag + a_srp;
end

function [r_new, v_new] = rk4_orbit(r, v, a_perturb, dt, mu)
    % 4th order Runge-Kutta orbit propagation
    
    % Define derivatives
    drdt = @(r, v) v;
    dvdt = @(r, v) -mu * r / norm(r)^3 + a_perturb;
    
    % RK4 integration
    k1_r = drdt(r, v);
    k1_v = dvdt(r, v);
    
    k2_r = drdt(r + dt/2 * k1_r, v + dt/2 * k1_v);
    k2_v = dvdt(r + dt/2 * k1_r, v + dt/2 * k1_v);
    
    k3_r = drdt(r + dt/2 * k2_r, v + dt/2 * k2_v);
    k3_v = dvdt(r + dt/2 * k2_r, v + dt/2 * k2_v);
    
    k4_r = drdt(r + dt * k3_r, v + dt * k3_v);
    k4_v = dvdt(r + dt * k3_r, v + dt * k3_v);
    
    r_new = r + dt/6 * (k1_r + 2*k2_r + 2*k3_r + k4_r);
    v_new = v + dt/6 * (k1_v + 2*k2_v + 2*k3_v + k4_v);
end

% =========================================================================
% ATTITUDE DYNAMICS FUNCTIONS
% =========================================================================

function tau_perturb = calculate_attitude_perturbations(r, q, omega, satellite)
    % Calculate attitude perturbations
    
    % Gravity gradient torque (simplified)
    r_mag = norm(r);
    r_unit = r / r_mag;
    
    % Assume principal axes inertia tensor
    I = diag([0.1, 0.1, 0.05]); % kg*m^2 (simplified)
    
    % Gravity gradient torque
    tau_gg = 3 * 3.986004418e14 / r_mag^3 * cross(r_unit, I * r_unit);
    
    % Add some random perturbations
    tau_random = 1e-6 * (rand(3,1) - 0.5);
    
    tau_perturb = tau_gg + tau_random;
end

function [q_new, omega_new] = propagate_attitude(q, omega, tau, dt, satellite)
    % Propagate attitude using quaternion integration
    
    % Inertia tensor
    I = diag([0.1, 0.1, 0.05]); % kg*m^2
    
    % Angular acceleration
    alpha = I \ tau;
    
    % Update angular velocity
    omega_new = omega + dt * alpha;
    
    % Quaternion integration
    omega_mag = norm(omega_new);
    if omega_mag > 1e-10
        axis = omega_new / omega_mag;
        angle = omega_mag * dt;
        
        % Quaternion from axis-angle
        dq = [cos(angle/2); sin(angle/2) * axis];
        
        % Quaternion multiplication
        q_new = quatmultiply(q', dq')';
    else
        q_new = q;
    end
    
    % Normalize quaternion
    q_new = q_new / norm(q_new);
end

% =========================================================================
% SENSOR DATA GENERATION FUNCTIONS
% =========================================================================

function ars_data = generate_realistic_ars_data(omega, q, time)
    % Generate realistic ARS (Attitude Rate Sensor) data
    
    % Add noise to angular velocity
    noise_level = 1e-4; % rad/s
    omega_noisy = omega + noise_level * (rand(3,1) - 0.5);
    
    % Prime and redundant sensors (slightly different)
    prime_omega = omega_noisy;
    redundant_omega = omega_noisy + noise_level * 0.1 * (rand(3,1) - 0.5);
    
    % Integrated angles (simplified integration)
    angle_integration_time = 0.1; % seconds
    prime_angles = prime_omega * angle_integration_time;
    redundant_angles = redundant_omega * angle_integration_time;
    
    % Add some realistic sensor characteristics
    bias_drift = 1e-5 * sin(time * 0.01); % Slow bias drift
    prime_omega = prime_omega + bias_drift;
    redundant_omega = redundant_omega + bias_drift * 0.8;
    
    ars_data = [prime_omega; redundant_omega; prime_angles; redundant_angles];
end

function mag_data = generate_realistic_magnetometer_data(r, q, time)
    % Generate realistic magnetometer data
    
    % Earth's magnetic field model (simplified dipole)
    r_mag = norm(r);
    lat = asin(r(3) / r_mag);
    lon = atan2(r(2), r(1));
    
    % Dipole field strength
    B0 = 3.12e-5; % Tesla
    
    % Magnetic field components
    Bx = B0 * cos(lat) * cos(lon);
    By = B0 * cos(lat) * sin(lon);
    Bz = B0 * sin(lat);
    
    B_earth = [Bx; By; Bz];
    
    % Transform to body frame using attitude quaternion
    R = quat2dcm(q');
    B_body = R * B_earth;
    
    % Add noise
    noise_level = 1e-7; % Tesla
    B_noisy = B_body + noise_level * (rand(3,1) - 0.5);
    
    % Convert to nT
    mag_data = B_noisy * 1e9; % Tesla to nT
end

function rw_data = generate_realistic_rw_data(omega, time)
    % Generate realistic reaction wheel data
    
    % Wheel speed (RPM) - related to angular momentum
    wheel_speed = 1500 + 100 * sin(time * 0.1) + norm(omega) * 1000;
    
    % Motor current (A) - related to torque
    motor_current = 2.5 + 0.5 * cos(time * 0.2) + norm(omega) * 10;
    
    % Temperature (°C) - thermal model
    temperature = 35 + 5 * sin(time * 0.05) + motor_current * 2;
    
    % Bus voltage (V) - power system model
    bus_voltage = 28.5 + 0.5 * cos(time * 0.1) - motor_current * 0.1;
    
    rw_data = [wheel_speed, motor_current, temperature, bus_voltage];
end

% =========================================================================
% VISUALIZATION FUNCTIONS
% =========================================================================

function setup_visualization()
    % Setup 3D visualization
    
    figure('Name', 'Orbital Simulator', 'Position', [100, 100, 1200, 800]);
    
    % 3D orbit plot
    subplot(2,2,1);
    [x, y, z] = sphere(20);
    surf(x*6378137, y*6378137, z*6378137, 'FaceAlpha', 0.3, 'EdgeColor', 'none');
    colormap('blue');
    hold on;
    plot3(0, 0, 0, 'ro', 'MarkerSize', 10, 'MarkerFaceColor', 'red');
    title('Orbit Trajectory');
    xlabel('X (m)'); ylabel('Y (m)'); zlabel('Z (m)');
    axis equal; grid on;
    
    % Altitude plot
    subplot(2,2,2);
    title('Altitude vs Time');
    xlabel('Time (s)'); ylabel('Altitude (km)');
    grid on;
    
    % Attitude plot
    subplot(2,2,3);
    title('Attitude Quaternion');
    xlabel('Time (s)'); ylabel('Quaternion Components');
    grid on;
    
    % Angular velocity plot
    subplot(2,2,4);
    title('Angular Velocity');
    xlabel('Time (s)'); ylabel('Angular Velocity (rad/s)');
    grid on;
end

function update_visualization(position_array, attitude_array, current_time)
    % Update visualization plots
    
    % Orbit trajectory
    subplot(2,2,1);
    plot3(position_array(:,1), position_array(:,2), position_array(:,3), 'b-', 'LineWidth', 1);
    
    % Altitude
    subplot(2,2,2);
    altitude = sqrt(sum(position_array.^2, 2)) - 6378137;
    plot(current_time, altitude(end)/1000, 'b.', 'MarkerSize', 6);
    xlim([max(0, current_time-300), current_time+50]);
    
    % Attitude
    subplot(2,2,3);
    plot(current_time, attitude_array(end,:), 'b.', 'MarkerSize', 6);
    xlim([max(0, current_time-300), current_time+50]);
    
    % Angular velocity
    subplot(2,2,4);
    % This would need omega_array, but we'll skip for now
    xlim([max(0, current_time-300), current_time+50]);
    
    drawnow;
end

% =========================================================================
% FLATSAT INTEGRATION FUNCTIONS
% =========================================================================

function send_to_flatsat_simulator(ars_data, mag_data, rw_data, time)
    % Send data to FlatSat simulator (placeholder)
    
    % This would integrate with your existing FlatSat simulator
    % For now, just display the data
    if mod(time, 10) == 0  % Every 10 seconds
        fprintf('Sending to FlatSat: ARS[%.3f,%.3f,%.3f], MAG[%.1f,%.1f,%.1f], RW[%.1f,%.1f,%.1f,%.1f]\n', ...
                ars_data(1), ars_data(2), ars_data(3), ...
                mag_data(1), mag_data(2), mag_data(3), ...
                rw_data(1), rw_data(2), rw_data(3), rw_data(4));
    end
end

% =========================================================================
% ANALYSIS AND UTILITY FUNCTIONS
% =========================================================================

function analyze_results(time_array, position_array, velocity_array, attitude_array, ...
                         omega_array, altitude_array, ars_data_array, mag_data_array, rw_data_array)
    % Analyze simulation results
    
    fprintf('\n=== SIMULATION ANALYSIS ===\n');
    
    % Orbital analysis
    initial_altitude = altitude_array(1) / 1000;
    final_altitude = altitude_array(end) / 1000;
    altitude_change = final_altitude - initial_altitude;
    
    fprintf('Initial altitude: %.2f km\n', initial_altitude);
    fprintf('Final altitude: %.2f km\n', final_altitude);
    fprintf('Altitude change: %.2f km\n', altitude_change);
    
    % Speed analysis
    initial_speed = norm(velocity_array(1,:));
    final_speed = norm(velocity_array(end,:));
    
    fprintf('Initial speed: %.2f m/s\n', initial_speed);
    fprintf('Final speed: %.2f m/s\n', final_speed);
    
    % Attitude analysis
    attitude_drift = norm(attitude_array(end,:) - attitude_array(1,:));
    fprintf('Attitude drift: %.6f\n', attitude_drift);
    
    % Sensor data analysis
    ars_std = std(ars_data_array, 0, 1);
    mag_std = std(mag_data_array, 0, 1);
    
    fprintf('ARS noise level: %.2e rad/s\n', mean(ars_std(1:3)));
    fprintf('Magnetometer noise level: %.2f nT\n', mean(mag_std));
end

function save_simulation_data(time_array, position_array, velocity_array, attitude_array, ...
                             omega_array, altitude_array, ars_data_array, mag_data_array, rw_data_array)
    % Save simulation data to .mat file
    
    save('orbital_simulation_results.mat', ...
         'time_array', 'position_array', 'velocity_array', 'attitude_array', ...
         'omega_array', 'altitude_array', 'ars_data_array', 'mag_data_array', 'rw_data_array');
end

% =========================================================================
% UTILITY FUNCTIONS
% =========================================================================

function q_out = quatmultiply(q1, q2)
    % Quaternion multiplication
    w1 = q1(1); x1 = q1(2); y1 = q1(3); z1 = q1(4);
    w2 = q2(1); x2 = q2(2); y2 = q2(3); z2 = q2(4);
    
    q_out = [w1*w2 - x1*x2 - y1*y2 - z1*z2;
             w1*x2 + x1*w2 + y1*z2 - z1*y2;
             w1*y2 - x1*z2 + y1*w2 + z1*x2;
             w1*z2 + x1*y2 - y1*x2 + z1*w2];
end

function R = quat2dcm(q)
    % Convert quaternion to rotation matrix
    w = q(1); x = q(2); y = q(3); z = q(4);
    
    R = [1-2*(y^2+z^2), 2*(x*y-w*z), 2*(x*z+w*y);
         2*(x*y+w*z), 1-2*(x^2+z^2), 2*(y*z-w*x);
         2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x^2+y^2)];
end


