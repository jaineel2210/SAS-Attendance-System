-- Add new table for student timetables
CREATE TABLE IF NOT EXISTS student_timetable (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department VARCHAR(100) NOT NULL,
    semester INT NOT NULL,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    period_number INT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    subject VARCHAR(100) NOT NULL,
    session_type ENUM('lecture', 'lab', 'practical') DEFAULT 'lecture',
    faculty_id INT,
    room_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faculty_id) REFERENCES users(id),
    INDEX idx_dept_sem_day (department, semester, day_of_week),
    INDEX idx_time_slot (start_time, end_time)
);

-- Update attendance table to include period tracking
ALTER TABLE attendance ADD COLUMN period_number INT DEFAULT 1;
ALTER TABLE attendance ADD COLUMN period_start_time TIME DEFAULT NULL;
ALTER TABLE attendance ADD COLUMN period_end_time TIME DEFAULT NULL;

-- Modify the unique constraint to allow multiple attendances per day
ALTER TABLE attendance DROP INDEX unique_attendance;
ALTER TABLE attendance ADD UNIQUE KEY unique_period_attendance (user_id, attendance_date, period_number, subject);

-- Insert sample timetable data for testing (Computer Science, Semester 1)
INSERT INTO student_timetable (department, semester, day_of_week, period_number, start_time, end_time, subject, session_type, faculty_id, room_number) VALUES
-- Monday
('Computer Science', 1, 'Monday', 1, '09:00:00', '09:50:00', 'Mathematics-I', 'lecture', 4, 'A101'),
('Computer Science', 1, 'Monday', 2, '09:50:00', '10:40:00', 'Physics', 'lecture', 4, 'A102'),
('Computer Science', 1, 'Monday', 3, '11:00:00', '11:50:00', 'Programming in C', 'lecture', 4, 'A103'),
('Computer Science', 1, 'Monday', 4, '11:50:00', '12:40:00', 'Programming in C Lab', 'lab', 4, 'Lab1'),
('Computer Science', 1, 'Monday', 5, '14:00:00', '14:50:00', 'English', 'lecture', 4, 'A104'),
('Computer Science', 1, 'Monday', 6, '14:50:00', '15:40:00', 'Engineering Graphics', 'practical', 4, 'A105'),

-- Tuesday  
('Computer Science', 1, 'Tuesday', 1, '09:00:00', '09:50:00', 'Mathematics-I', 'lecture', 4, 'A101'),
('Computer Science', 1, 'Tuesday', 2, '09:50:00', '10:40:00', 'Chemistry', 'lecture', 4, 'A102'),
('Computer Science', 1, 'Tuesday', 3, '11:00:00', '11:50:00', 'Chemistry Lab', 'lab', 4, 'Lab2'),
('Computer Science', 1, 'Tuesday', 4, '11:50:00', '12:40:00', 'Physics Lab', 'lab', 4, 'Lab3'),
('Computer Science', 1, 'Tuesday', 5, '14:00:00', '14:50:00', 'Programming in C', 'lecture', 4, 'A103'),
('Computer Science', 1, 'Tuesday', 6, '14:50:00', '15:40:00', 'Environmental Science', 'lecture', 4, 'A104');