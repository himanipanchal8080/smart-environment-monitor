CREATE DATABASE IF NOT EXISTS urban_city_monitor;
USE urban_city_monitor;

CREATE TABLE IF NOT EXISTS environment_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    area VARCHAR(100),
    air_quality_index INT,
    temperature FLOAT,
    humidity FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
