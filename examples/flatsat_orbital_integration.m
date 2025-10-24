function flatsat_orbital_integration()
    % FLATSAT ORBITAL INTEGRATION SCRIPT
    % 
    % This script integrates the orbital simulator with the existing FlatSat
    % simulator infrastructure, sending realistic orbital data to the simulator.
    
    clc; clear; close all;
    
    % =========================================================================
    % CONFIGURATION
    % =========================================================================
    
    % Simulation parameters
    sim_duration = 300;         % 5 minutes for demo
    dt = 0.1;                  % Time step
    time_steps = sim_duration / dt;
    
    % FlatSat simulator connection
    simulator_ip = '127.0.0.1';
    simulator_port = 5000;
    
    % Device ports (matching your existing configuration)
    ars_ports = 5000:5011;     % 12 ports for ARS
    mag_ports = 6000:6002;     % 3 ports for magnetometer
    rw_ports = 7000:7003;      % 4 ports for reaction wheel
    
    % =========================================================================
    % INITIALIZATION
    % =========================================================================
    
    fprintf('Starting FlatSat Orbital Integration...\n');
    fprintf('Connecting to simulator at %s:%d\n', simulator_ip, simulator_port);
    
    % Initialize orbital state (ISS-like orbit)
    initial_orbit.a = 6798000;      % Semi-major axis (m)
    initial_orbit.e = 0.0001;       % Eccentricity
    initial_orbit.i = deg2rad(51.6); % Inclination
    initial_orbit.Omega = deg2rad(0);
    initial_orbit.omega = deg2rad(0);
    initial_orbit.nu = deg2rad(0);
    
    % Convert to Cartesian
    mu = 3.986004418e14;
    [r0, v0] = oe2cartesian(initial_orbit, mu);
    
    % Initialize state
    state.r = r0;
    state.v = v0;
    state.q = [1, 0, 0, 0];  % Identity quaternion
    state.omega = [0.01, 0.005, -0.02];
    
    % Satellite parameters
    satellite.mass = 10.0;
    satellite.area = 0.1;
    satellite.cd = 2.2;
    satellite.cr = 1.8;
    
    % Physical constants
    Re = 6378137.0;
    J2 = 1.08263e-3;
    rho0 = 1.225;
    H = 8400;
    P_solar = 4.56e-6;
    
    % =========================================================================
    % MAIN SIMULATION LOOP
    % =========================================================================
    
    try
        % Create TCP connection to FlatSat simulator
        tcp_client = tcpclient(simulator_ip, simulator_port);
        fprintf('Connected successfully!\n');
        
        start_time = tic;
        
        for step = 1:time_steps
            current_time = (step - 1) * dt;
            
            % =================================================================
            % ORBITAL PROPAGATION
            % =================================================================
            
            % Calculate perturbations
            [a_perturb, r_mag] = calculate_perturbations(state.r, state.v, satellite, mu, Re, J2, rho0, H, P_solar);
            
            % Propagate orbit
            [state.r, state.v] = rk4_orbit(state.r, state.v, a_perturb, dt, mu);
            
            % =================================================================
            % ATTITUDE PROPAGATION
            % =================================================================
            
            % Calculate attitude perturbations
            tau_perturb = calculate_attitude_perturbations(state.r, state.q, state.omega, satellite);
            
            % Propagate attitude
            [state.q, state.omega] = propagate_attitude(state.q, state.omega, tau_perturb, dt, satellite);
            
            % =================================================================
            % SENSOR DATA GENERATION
            % =================================================================
            
            % Generate realistic sensor data
            ars_data = generate_realistic_ars_data(state.omega, state.q, current_time);
            mag_data = generate_realistic_magnetometer_data(state.r, state.q, current_time);
            rw_data = generate_realistic_rw_data(state.omega, current_time);
            
            % =================================================================
            % SEND TO FLATSAT SIMULATOR
            % =================================================================
            
            % Send ARS data (600 Hz equivalent - every 0.1s = 10 Hz)
            if mod(step, 1) == 0  % Every time step
                for i = 1:min(length(ars_data), length(ars_ports))
                    try
                        write(tcp_client, ars_data(i), 'double');
                    catch
                        % Handle connection errors gracefully
                    end
                end
            end
            
            % Send magnetometer data (10 Hz)
            if mod(step, 10) == 0  % Every 1 second
                for i = 1:min(length(mag_data), length(mag_ports))
                    try
                        write(tcp_client, mag_data(i), 'double');
                    catch
                        % Handle connection errors gracefully
                    end
                end
            end
            
            % Send reaction wheel data (1 Hz)
            if mod(step, 100) == 0  % Every 10 seconds
                for i = 1:min(length(rw_data), length(rw_ports))
                    try
                        write(tcp_client, rw_data(i), 'double');
                    catch
                        % Handle connection errors gracefully
                    end
                end
            end
            
            % =================================================================
            % STATUS OUTPUT
            % =================================================================
            
            if mod(step, 100) == 0  % Every 10 seconds
                altitude = (norm(state.r) - Re) / 1000;
                speed = norm(state.v);
                fprintf('Time: %.1fs, Altitude: %.1fkm, Speed: %.1fm/s\n', ...
                        current_time, altitude, speed);
            end
            
            % Small delay to prevent overwhelming the simulator
            pause(0.001);
        end
        
    catch ME
        fprintf('Error during simulation: %s\n', ME.message);
    end
    
    % Clean up
    if exist('tcp_client', 'var')
        clear tcp_client;
    end
    
    fprintf('Orbital integration completed!\n');
end

% =========================================================================
% ORBITAL MECHANICS FUNCTIONS (Same as main simulator)
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
        v_rel = v;
        v_rel_mag = norm(v_rel);
        a_drag = -0.5 * rho * satellite.cd * satellite.area / satellite.mass * ...
                 v_rel_mag * v_rel;
    else
        a_drag = [0; 0; 0];
    end
    
    % Solar radiation pressure
    a_srp = P_solar * satellite.cr * satellite.area / satellite.mass * [1; 0; 0];
    
    % Total perturbation
    a_perturb = a_j2 + a_drag + a_srp;
end

function [r_new, v_new] = rk4_orbit(r, v, a_perturb, dt, mu)
    % 4th order Runge-Kutta orbit propagation
    
    drdt = @(r, v) v;
    dvdt = @(r, v) -mu * r / norm(r)^3 + a_perturb;
    
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

function tau_perturb = calculate_attitude_perturbations(r, q, omega, satellite)
    % Calculate attitude perturbations
    
    r_mag = norm(r);
    r_unit = r / r_mag;
    
    I = diag([0.1, 0.1, 0.05]);
    
    tau_gg = 3 * 3.986004418e14 / r_mag^3 * cross(r_unit, I * r_unit);
    tau_random = 1e-6 * (rand(3,1) - 0.5);
    
    tau_perturb = tau_gg + tau_random;
end

function [q_new, omega_new] = propagate_attitude(q, omega, tau, dt, satellite)
    % Propagate attitude using quaternion integration
    
    I = diag([0.1, 0.1, 0.05]);
    alpha = I \ tau;
    omega_new = omega + dt * alpha;
    
    omega_mag = norm(omega_new);
    if omega_mag > 1e-10
        axis = omega_new / omega_mag;
        angle = omega_mag * dt;
        dq = [cos(angle/2); sin(angle/2) * axis];
        q_new = quatmultiply(q', dq')';
    else
        q_new = q;
    end
    
    q_new = q_new / norm(q_new);
end

function ars_data = generate_realistic_ars_data(omega, q, time)
    % Generate realistic ARS data
    
    noise_level = 1e-4;
    omega_noisy = omega + noise_level * (rand(3,1) - 0.5);
    
    prime_omega = omega_noisy;
    redundant_omega = omega_noisy + noise_level * 0.1 * (rand(3,1) - 0.5);
    
    angle_integration_time = 0.1;
    prime_angles = prime_omega * angle_integration_time;
    redundant_angles = redundant_omega * angle_integration_time;
    
    bias_drift = 1e-5 * sin(time * 0.01);
    prime_omega = prime_omega + bias_drift;
    redundant_omega = redundant_omega + bias_drift * 0.8;
    
    ars_data = [prime_omega; redundant_omega; prime_angles; redundant_angles];
end

function mag_data = generate_realistic_magnetometer_data(r, q, time)
    % Generate realistic magnetometer data
    
    r_mag = norm(r);
    lat = asin(r(3) / r_mag);
    lon = atan2(r(2), r(1));
    
    B0 = 3.12e-5;
    Bx = B0 * cos(lat) * cos(lon);
    By = B0 * cos(lat) * sin(lon);
    Bz = B0 * sin(lat);
    
    B_earth = [Bx; By; Bz];
    R = quat2dcm(q');
    B_body = R * B_earth;
    
    noise_level = 1e-7;
    B_noisy = B_body + noise_level * (rand(3,1) - 0.5);
    
    mag_data = B_noisy * 1e9; % Tesla to nT
end

function rw_data = generate_realistic_rw_data(omega, time)
    % Generate realistic reaction wheel data
    
    wheel_speed = 1500 + 100 * sin(time * 0.1) + norm(omega) * 1000;
    motor_current = 2.5 + 0.5 * cos(time * 0.2) + norm(omega) * 10;
    temperature = 35 + 5 * sin(time * 0.05) + motor_current * 2;
    bus_voltage = 28.5 + 0.5 * cos(time * 0.1) - motor_current * 0.1;
    
    rw_data = [wheel_speed, motor_current, temperature, bus_voltage];
end

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


