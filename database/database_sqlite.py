"""
SQLite Database module for deployment
Falls back to SQLite when MySQL is not available
"""

import sqlite3
import os
import logging
import bcrypt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.environ.get('DATABASE_PATH', 'secureattend.db')

def get_db_connection():
    """Get SQLite database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        logger.info(f"Connected to SQLite database: {DB_PATH}")
        return conn
    except Exception as e:
        logger.error(f"SQLite connection error: {e}")
        return None

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute a query and return results"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        # Convert MySQL placeholders (%s) to SQLite (?)
        query = query.replace('%s', '?')
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_one:
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None
        elif fetch_all:
            results = cursor.fetchall()
            return [dict(row) for row in results]
        else:
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
            
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return None
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize the SQLite database with tables"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                enrollment_no VARCHAR(50) UNIQUE,
                mobile_number VARCHAR(15),
                role VARCHAR(20) DEFAULT 'student',
                password_hash VARCHAR(255),
                face_encoding BLOB,
                rfid_tag VARCHAR(100),
                admin_level VARCHAR(20),
                is_verified INTEGER DEFAULT 0,
                department VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Table 'users' created/verified successfully")
        
        # Create otp_verification table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS otp_verification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mobile_number VARCHAR(15) NOT NULL,
                otp VARCHAR(6) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_verified INTEGER DEFAULT 0
            )
        ''')
        logger.info("Table 'otp_verification' created/verified successfully")
        
        # Create attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id INTEGER,
                date DATE,
                time TIME,
                status VARCHAR(20) DEFAULT 'present',
                method VARCHAR(20),
                subject VARCHAR(100),
                faculty_id INTEGER,
                location VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        logger.info("Table 'attendance' created/verified successfully")
        
        # Create sessions table  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_id INTEGER,
                subject VARCHAR(100),
                session_type VARCHAR(50),
                qr_code VARCHAR(500),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (faculty_id) REFERENCES users(id)
            )
        ''')
        logger.info("Table 'sessions' created/verified successfully")
        
        # Create login_attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier VARCHAR(100),
                ip_address VARCHAR(50),
                attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 0
            )
        ''')
        logger.info("Table 'login_attempts' created/verified successfully")
        
        conn.commit()
        
        # Create sample admin user
        cursor.execute("SELECT * FROM users WHERE role = 'admin' LIMIT 1")
        if not cursor.fetchone():
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('''
                INSERT INTO users (name, enrollment_no, mobile_number, role, password_hash, admin_level, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('Admin', 'ADM001', '0000000000', 'admin', password_hash, 'super', 1))
            conn.commit()
            logger.info("Sample admin user created (default password: admin123)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False
    finally:
        if conn:
            conn.close()
