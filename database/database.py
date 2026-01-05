import pymysql
from pymysql import Error
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.host = Config.MYSQL_HOST
        self.user = Config.MYSQL_USER
        self.password = Config.MYSQL_PASSWORD
        self.database = Config.MYSQL_DATABASE
        self.connection = None

    def connect(self):
        """Establish database connection"""
        try:
            logger.info("Attempting database connection with PyMySQL")
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                autocommit=True
            )
            logger.info("Successfully connected to MySQL database using PyMySQL")
            return True
        except Exception as e:
            logger.error(f"Error connecting to MySQL with PyMySQL: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.open:
            self.connection.close()
            logger.info("MySQL connection closed")

    def execute_query(self, query, params=None, fetch_last_id=False):
        """Execute a query and return results"""
        try:
            if not self.connection or not self.connection.open:
                self.connect()
            
            cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
                if fetch_last_id:
                    result = cursor.lastrowid
                
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def create_tables(self):
        """Create all necessary tables"""
        tables = {
            'users': '''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    enrollment_no VARCHAR(20) UNIQUE,
                    faculty_id VARCHAR(20) UNIQUE,
                    mobile_number VARCHAR(15) NOT NULL,
                    role ENUM('admin', 'faculty', 'student') DEFAULT 'student',
                    password_hash VARCHAR(255),
                    face_encoding TEXT,
                    rfid_uid VARCHAR(50),
                    department VARCHAR(100),
                    admin_level ENUM('standard', 'super', 'system') DEFAULT 'standard',
                    is_verified BOOLEAN DEFAULT FALSE,
                    is_approved BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL
                )
            ''',
            'otp_verification': '''
                CREATE TABLE IF NOT EXISTS otp_verification (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    mobile_number VARCHAR(15) NOT NULL,
                    otp_code VARCHAR(6) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    is_used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'attendance': '''
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
                )
            ''',
            'sessions': '''
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
                )
            ''',
            'login_attempts': '''
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    identifier VARCHAR(100) NOT NULL,
                    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    success BOOLEAN DEFAULT FALSE
                )
            '''
        }

        for table_name, query in tables.items():
            result = self.execute_query(query)
            if result is not None:
                logger.info(f"Table '{table_name}' created/verified successfully")
            else:
                logger.error(f"Failed to create table '{table_name}'")

    def insert_sample_data(self):
        """Insert sample admin user"""
        admin_query = '''
            INSERT IGNORE INTO users (name, enrollment_no, mobile_number, role, password_hash, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        admin_data = ('System Admin', 'ADMIN001', '9999999999', 'admin', 
                     '$2b$12$LQv3c1yqBwEHxPuNY.Q.EuTDWiOuIj4lLJkFQ9B8kNnX9QK1bQ1K6', True)
        
        self.execute_query(admin_query, admin_data)
        logger.info("Sample admin user created (default password: admin123)")

# Initialize database
db = DatabaseManager()