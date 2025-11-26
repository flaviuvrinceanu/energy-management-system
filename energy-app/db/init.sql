-- Create databases
CREATE DATABASE energy_auth;
CREATE DATABASE energy_users;
CREATE DATABASE energy_devices;
CREATE DATABASE energy_monitoring;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE energy_auth TO postgres;
GRANT ALL PRIVILEGES ON DATABASE energy_users TO postgres;
GRANT ALL PRIVILEGES ON DATABASE energy_devices TO postgres;
GRANT ALL PRIVILEGES ON DATABASE energy_monitoring TO postgres;