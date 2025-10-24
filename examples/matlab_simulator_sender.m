% MATLAB Simulator Data Sender
% 
% Simulates data generation and sends it to the FlatSat Device Simulator.
% This script demonstrates how to integrate MATLAB with the simulator.

function matlab_simulator_sender()
    % Configuration
    target_ip = '127.0.0.1';
    target_port = 5000;
    duration = 60; % seconds
    
    % Device enable flags
    enable_ars = true;
    enable_magnetometer = true;
    enable_reaction_wheel = false;
    
    % Port mappings
    ars_ports = 5000:5011;        % 12 ports for ARS
    mag_ports = 6000:6002;        % 3 ports for magnetometer
    rw_ports = 7000:7003;         % 4 ports for reaction wheel
    
    % Create TCP connection
    tcp_client = tcpclient(target_ip, target_port);
    
    fprintf('Connected to simulator at %s:%d\n', target_ip, target_port);
    fprintf('Running simulation for %d seconds...\n', duration);
    
    start_time = tic;
    
    try
        while toc(start_time) < duration
            current_time = toc(start_time);
            
            % Send ARS data (600 Hz)
            if enable_ars
                ars_data = generate_ars_data(current_time);
                for i = 1:length(ars_ports)
                    if i <= length(ars_data)
                        write(tcp_client, ars_data(i), 'double');
                    end
                end
            end
            
            % Send magnetometer data (10 Hz)
            if enable_magnetometer && mod(floor(current_time * 10), 10) == 0
                mag_data = generate_magnetometer_data(current_time);
                for i = 1:length(mag_ports)
                    if i <= length(mag_data)
                        write(tcp_client, mag_data(i), 'double');
                    end
                end
            end
            
            % Send reaction wheel data (1 Hz)
            if enable_reaction_wheel && mod(floor(current_time), 1) == 0
                rw_data = generate_reaction_wheel_data(current_time);
                for i = 1:length(rw_ports)
                    if i <= length(rw_data)
                        write(tcp_client, rw_data(i), 'double');
                    end
                end
            end
            
            % Small delay
            pause(0.001);
        end
        
    catch ME
        fprintf('Error during simulation: %s\n', ME.message);
    end
    
    % Clean up
    clear tcp_client;
    fprintf('Simulation completed\n');
end

function ars_data = generate_ars_data(time)
    % Generate ARS data (12 floats)
    % Prime angular rates (rad/sec)
    prime_x = 0.1 * sin(time * 0.5);
    prime_y = -0.05 * cos(time * 0.3);
    prime_z = 0.02 * sin(time * 0.7);
    
    % Redundant angular rates (slightly different)
    redundant_x = prime_x + (rand - 0.5) * 0.002;
    redundant_y = prime_y + (rand - 0.5) * 0.002;
    redundant_z = prime_z + (rand - 0.5) * 0.002;
    
    % Prime summed incremental angles (rad)
    prime_angle_x = 1.0 * sin(time * 0.2);
    prime_angle_y = -0.5 * cos(time * 0.4);
    prime_angle_z = 0.2 * sin(time * 0.6);
    
    % Redundant summed incremental angles
    redundant_angle_x = prime_angle_x + (rand - 0.5) * 0.02;
    redundant_angle_y = prime_angle_y + (rand - 0.5) * 0.02;
    redundant_angle_z = prime_angle_z + (rand - 0.5) * 0.02;
    
    ars_data = [prime_x, prime_y, prime_z, ...
                redundant_x, redundant_y, redundant_z, ...
                prime_angle_x, prime_angle_y, prime_angle_z, ...
                redundant_angle_x, redundant_angle_y, redundant_angle_z];
end

function mag_data = generate_magnetometer_data(time)
    % Generate magnetometer data (3 floats)
    % Simulate Earth's magnetic field (nT)
    x_field = 25000.0 + 1000.0 * sin(time * 0.1);
    y_field = -5000.0 + 500.0 * cos(time * 0.15);
    z_field = 40000.0 + 800.0 * sin(time * 0.08);
    
    mag_data = [x_field, y_field, z_field];
end

function rw_data = generate_reaction_wheel_data(time)
    % Generate reaction wheel data (4 floats)
    % Wheel speed (RPM)
    wheel_speed = 1500.0 + 100.0 * sin(time * 0.2);
    
    % Motor current (A)
    motor_current = 2.5 + 0.5 * cos(time * 0.3);
    
    % Temperature (°C)
    temperature = 35.0 + 5.0 * sin(time * 0.05);
    
    % Bus voltage (V)
    bus_voltage = 28.5 + 0.5 * cos(time * 0.1);
    
    rw_data = [wheel_speed, motor_current, temperature, bus_voltage];
end
