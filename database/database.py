import pymysql
from config import Config
import logging
import bcrypt
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_ADMIN = {
    'name': 'System Admin',
    'enrollment_no': 'ADMIN001',
    'mobile_number': '9999999999',
    'role': 'admin',
    'password': 'admin123',
    'is_verified': True,
    'is_approved': True
}

SAMPLE_FACULTY = [
    {
        'name': 'Ms. Purvi Patel',
        'faculty_id': 'FAC001',
        'department': 'Computer Engineering',
        'mobile_number': '9876543001',
        'email': 'purvi.patel@college.edu',
        'password': 'faculty123'
    },
    {
        'name': 'Mr. Parth Desai',
        'faculty_id': 'FAC002',
        'department': 'Computer Engineering',
        'mobile_number': '9876543002',
        'email': 'parth.desai@college.edu',
        'password': 'faculty123'
    },
    {
        'name': 'Ms. Deepika Shrivastav',
        'faculty_id': 'FAC003',
        'department': 'Computer Engineering',
        'mobile_number': '9876543003',
        'email': 'deepika.s@college.edu',
        'password': 'faculty123'
    },
    {
        'name': 'Mr. Viral Mishra',
        'faculty_id': 'FAC004',
        'department': 'Computer Engineering',
        'mobile_number': '9876543004',
        'email': 'viral.mishra@college.edu',
        'password': 'faculty123'
    },
    {
        'name': 'Mr. Vishal Patel',
        'faculty_id': 'FAC005',
        'department': 'Computer Engineering',
        'mobile_number': '9876543005',
        'email': 'vishal.patel@college.edu',
        'password': 'faculty123'
    },
    {
        'name': 'Ms. Bhoomi Parmar',
        'faculty_id': 'FAC006',
        'department': 'Training & Placement',
        'mobile_number': '9876543006',
        'email': 'bhoomi.parmar@college.edu',
        'password': 'faculty123'
    }
]

TABLE_DEFINITIONS = {
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NULL,
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
    'students': '''
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sr_no INT,
            institute VARCHAR(100) DEFAULT 'SOCET',
            enrollment_no VARCHAR(20) UNIQUE NOT NULL,
            full_name VARCHAR(200) NOT NULL,
            first_name VARCHAR(100),
            middle_name VARCHAR(100),
            last_name VARCHAR(100),
            department VARCHAR(100) DEFAULT 'SOCET',
            year INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_enrollment (enrollment_no),
            INDEX idx_last_name (last_name),
            INDEX idx_year (year)
        )
    ''',
    'attendance_records': '''
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            enrollment_no VARCHAR(20) NOT NULL,
            subject_name VARCHAR(100),
            faculty_name VARCHAR(100),
            date DATE NOT NULL,
            status ENUM('Present', 'Absent') DEFAULT 'Present',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (enrollment_no) REFERENCES students(enrollment_no) ON DELETE CASCADE,
            INDEX idx_enrollment (enrollment_no),
            INDEX idx_date (date),
            INDEX idx_subject (subject_name)
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
    'password_reset_otp': '''
        CREATE TABLE IF NOT EXISTS password_reset_otp (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            mobile_number VARCHAR(15) NOT NULL,
            role ENUM('admin', 'faculty', 'student') NOT NULL,
            identifier VARCHAR(50),
            otp_code VARCHAR(6) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            request_ip VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''',
    'holidays': '''
        CREATE TABLE IF NOT EXISTS holidays (
            id INT AUTO_INCREMENT PRIMARY KEY,
            holiday_date DATE NOT NULL,
            title VARCHAR(150) NOT NULL,
            description VARCHAR(255),
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL,
            FOREIGN KEY (created_by) REFERENCES users(id),
            UNIQUE KEY unique_holiday_date (holiday_date)
        )
    ''',
    'notifications': '''
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            role ENUM('admin', 'faculty', 'student') NULL,
            title VARCHAR(150) NOT NULL,
            message TEXT NOT NULL,
            category VARCHAR(50),
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''',
    'attendance_logs': '''
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            attendance_id INT NOT NULL,
            user_id INT NOT NULL,
            action VARCHAR(100) NOT NULL,
            details TEXT,
            ip_address VARCHAR(45),
            device_info VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (attendance_id) REFERENCES attendance(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''',
    'audit_logs': '''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            role ENUM('admin', 'faculty', 'student') NULL,
            action VARCHAR(150) NOT NULL,
            target VARCHAR(150),
            details TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''',
    'device_tracking': '''
        CREATE TABLE IF NOT EXISTS device_tracking (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            device_id VARCHAR(255),
            browser_fingerprint VARCHAR(255),
            ip_address VARCHAR(45),
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            example_details VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''',
    'qr_sessions': '''
        CREATE TABLE IF NOT EXISTS qr_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            qr_session_id VARCHAR(255) UNIQUE NOT NULL,
            faculty_id INT NOT NULL,
            subject VARCHAR(100) NOT NULL,
            session_type ENUM('lecture', 'lab') DEFAULT 'lecture',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            location_hash VARCHAR(255),
            nonce VARCHAR(64),
            is_active BOOLEAN DEFAULT TRUE,
            scanned_count INT DEFAULT 0,
            FOREIGN KEY (faculty_id) REFERENCES users(id)
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
            marked_by_qr BOOLEAN DEFAULT FALSE,
            qr_session_id VARCHAR(255),
            period_number INT,
            period_start_time TIME,
            period_end_time TIME,
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
            qr_session_id VARCHAR(255) UNIQUE,
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
    ''',
    'faculty': '''
        CREATE TABLE IF NOT EXISTS faculty (
            id INT AUTO_INCREMENT PRIMARY KEY,
            faculty_id VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            department VARCHAR(100),
            mobile_number VARCHAR(15),
            email VARCHAR(100),
            password_hash VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
}

class DatabaseManager:
    def __init__(self):
        self.host = Config.MYSQL_HOST
        self.user = Config.MYSQL_USER
        self.password = Config.MYSQL_PASSWORD
        self.database = Config.MYSQL_DATABASE
        self.connection = None
        self.startup_status = {
            'mysql_connected': False,
            'database_verified': False,
            'tables_verified': False,
            'student_accounts_verified': False,
            'faculty_accounts_verified': False
        }

    def _connect(self, use_database=True):
        """Establish MySQL connection optionally using the configured database."""
        try:
            connection_args = {
                'host': self.host,
                'user': self.user,
                'password': self.password,
                'charset': 'utf8mb4',
                'autocommit': True,
                'cursorclass': pymysql.cursors.DictCursor
            }
            if use_database:
                connection_args['database'] = self.database
            self.connection = pymysql.connect(**connection_args)
            return True
        except Exception as e:
            logger.error(f"[ERROR] MySQL connection failed: {e}")
            self.connection = None
            return False

    def connect(self):
        """Connect to the configured database."""
        return self._connect(use_database=True)

    def connect_server(self):
        """Connect to the MySQL server without selecting a database."""
        return self._connect(use_database=False)

    def disconnect(self):
        """Close database connection."""
        if self.connection and getattr(self.connection, 'open', False):
            self.connection.close()
            logger.info("[INFO] MySQL connection closed")
            self.connection = None

    def execute_query(self, query, params=None, fetch_last_id=False):
        """Execute a query and return results."""
        try:
            if not self.connection or not getattr(self.connection, 'open', False):
                if not self.connect():
                    return None
            cursor = self.connection.cursor()
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
            logger.error(f"[ERROR] Failed query: {e}")
            logger.error(traceback.format_exc())
            if self.connection:
                self.connection.rollback()
            return None

    def verify_mysql_connection(self):
        """Verify MySQL connection before startup."""
        if self.connect_server():
            self.startup_status['mysql_connected'] = True
            logger.info("[INFO] MySQL Connected Successfully")
            self.disconnect()
            return True
        logger.error("[ERROR] Unable to connect to MySQL")
        return False

    def ensure_database_exists(self):
        """Create the configured database if it does not exist."""
        if not self.connect_server():
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW DATABASES LIKE %s", (self.database,))
            exists = cursor.fetchone()
            if exists:
                logger.info(f"[INFO] Database {self.database} Found")
                self.startup_status['database_verified'] = True
            else:
                logger.info(f"[INFO] Database {self.database} missing. Creating database...")
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                logger.info(f"[INFO] Database {self.database} created successfully")
                self.startup_status['database_verified'] = True
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to verify or create database: {e}")
            logger.error(traceback.format_exc())
            self.disconnect()
            return False

    def table_exists(self, table_name):
        """Return True if the specified table exists in the configured database."""
        query = '''
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
        '''
        result = self.execute_query(query, (self.database, table_name))
        return bool(result and result[0].get('count', 0) > 0)

    def create_tables(self):
        """Create required tables and verify their presence."""
        if not self.connection or not getattr(self.connection, 'open', False):
            if not self.connect():
                return False
        logger.info("[INFO] Verifying Tables...")
        success = True
        for table_name, sql in TABLE_DEFINITIONS.items():
            if self.table_exists(table_name):
                logger.info(f"[OK] {table_name}")
                continue
            result = self.execute_query(sql)
            if result is not None:
                logger.info(f"[CREATED] {table_name}")
            else:
                logger.error(f"[ERROR] Failed to create table {table_name}")
                success = False
        self.startup_status['tables_verified'] = success
        return success

    def hash_password(self, password):
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def ensure_default_admin(self):
        """Ensure the default admin account exists."""
        query = "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        result = self.execute_query(query)
        if result and len(result) > 0:
            logger.info("[OK] admin user verified")
            return True
        password_hash = self.hash_password(DEFAULT_ADMIN['password'])
        insert_query = '''
            INSERT INTO users
            (name, enrollment_no, mobile_number, role, password_hash, is_verified, is_approved)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        '''
        self.execute_query(insert_query, (
            DEFAULT_ADMIN['name'],
            DEFAULT_ADMIN['enrollment_no'],
            DEFAULT_ADMIN['mobile_number'],
            DEFAULT_ADMIN['role'],
            password_hash,
            DEFAULT_ADMIN['is_verified'],
            DEFAULT_ADMIN['is_approved']
        ))
        logger.info("[CREATED] default admin user")
        return True

    def recover_student_accounts(self):
        """Recover missing student user records from the students table."""
        student_query = "SELECT COUNT(*) as count FROM users WHERE role = 'student'"
        student_count_result = self.execute_query(student_query)
        student_count = student_count_result[0]['count'] if student_count_result else 0
        if student_count > 0:
            logger.info("[OK] Student accounts verified")
            self.startup_status['student_accounts_verified'] = True
            return True

        student_rows = self.execute_query("SELECT enrollment_no, full_name, department FROM students")
        if not student_rows:
            logger.warning("[WARN] No student records found in students table to recover")
            self.startup_status['student_accounts_verified'] = False
            return False

        created_count = 0
        for student in student_rows:
            enrollment_no = student.get('enrollment_no')
            full_name = student.get('full_name')
            department = student.get('department') or ''
            password_hash = self.hash_password(enrollment_no)
            insert_query = '''
                INSERT IGNORE INTO users
                (name, enrollment_no, mobile_number, role, password_hash, department, is_verified, is_approved)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            result = self.execute_query(insert_query, (
                full_name,
                enrollment_no,
                '9999999999',
                'student',
                password_hash,
                department,
                True,
                True
            ))
            if result is not None:
                created_count += 1
        logger.info(f"[INFO] Recovered {created_count} student accounts from students table")
        self.startup_status['student_accounts_verified'] = True
        return True

    def ensure_faculty_table_and_accounts(self):
        """Ensure faculty metadata and faculty users exist."""
        if not self.table_exists('faculty'):
            result = self.execute_query(TABLE_DEFINITIONS['faculty'])
            if result is not None:
                logger.info("[CREATED] faculty")
            else:
                logger.error("[ERROR] Failed to create faculty table")
                self.startup_status['faculty_accounts_verified'] = False
                return False
        else:
            logger.info("[OK] faculty")

        faculty_count_result = self.execute_query("SELECT COUNT(*) as count FROM faculty")
        faculty_count = faculty_count_result[0]['count'] if faculty_count_result else 0
        if faculty_count > 0:
            logger.info("[OK] faculty accounts verified")
            self.startup_status['faculty_accounts_verified'] = True
            return True

        created_count = 0
        for faculty in SAMPLE_FACULTY:
            password_hash = self.hash_password(faculty['password'])
            insert_faculty = '''
                INSERT IGNORE INTO faculty
                (faculty_id, name, department, mobile_number, email, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
            '''
            self.execute_query(insert_faculty, (
                faculty['faculty_id'],
                faculty['name'],
                faculty['department'],
                faculty['mobile_number'],
                faculty['email'],
                password_hash
            ))
            insert_user = '''
                INSERT IGNORE INTO users
                (name, faculty_id, mobile_number, role, password_hash, department, is_verified, is_approved)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            result = self.execute_query(insert_user, (
                faculty['name'],
                faculty['faculty_id'],
                faculty['mobile_number'],
                'faculty',
                password_hash,
                faculty['department'],
                True,
                True
            ))
            if result is not None:
                created_count += 1
        logger.info(f"[INFO] Created {created_count} sample faculty accounts")
        self.startup_status['faculty_accounts_verified'] = True
        return True

    def initialize_database(self):
        """Perform database recovery and initialization."""
        if not self.verify_mysql_connection():
            return False
        if not self.ensure_database_exists():
            return False
        if not self.connect():
            logger.error("[ERROR] Unable to connect to configured database")
            return False
        tables_ok = self.create_tables()
        self.ensure_default_admin()
        self.recover_student_accounts()
        self.ensure_faculty_table_and_accounts()
        return tables_ok

    def insert_sample_data(self):
        """Legacy compatibility wrapper for sample data creation."""
        self.ensure_default_admin()

# Initialize database
db = DatabaseManager()