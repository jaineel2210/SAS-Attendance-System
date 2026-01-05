-- Create database if not exists
CREATE DATABASE IF NOT EXISTS attendance_system;
USE attendance_system;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'faculty', 'student') NOT NULL,
    enrollment_no VARCHAR(20) UNIQUE,
    faculty_id VARCHAR(20) UNIQUE,
    department VARCHAR(100),
    rfid_uid VARCHAR(50) UNIQUE,
    face_encoding TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_id INT NOT NULL,
    subject VARCHAR(100) NOT NULL,
    session_type ENUM('lecture', 'lab') DEFAULT 'lecture',
    session_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME,
    is_active BOOLEAN DEFAULT TRUE,
    total_students INT DEFAULT 0,
    present_students INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faculty_id) REFERENCES users(id)
);

-- Create attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    faculty_id INT NOT NULL,
    subject VARCHAR(100) NOT NULL,
    session_type ENUM('lecture', 'lab') DEFAULT 'lecture',
    attendance_date DATE NOT NULL,
    attendance_time TIME NOT NULL,
    status ENUM('P', 'A') DEFAULT 'P',
    marked_by_face BOOLEAN DEFAULT FALSE,
    marked_by_rfid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (faculty_id) REFERENCES users(id),
    UNIQUE KEY unique_attendance (user_id, attendance_date, session_type, subject)
);

-- Insert a test faculty account
INSERT INTO users (name, email, password, role) 
VALUES ('Test Faculty', 'faculty@test.com', '$2b$12$LQrP6ECXN0HYOyv.t9SMqu/ov8BdtgzYGqoQZ8uJFi0ozH7sHLjli', 'faculty')
ON DUPLICATE KEY UPDATE id=id;
