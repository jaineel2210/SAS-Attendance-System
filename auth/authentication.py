import bcrypt
import secrets
import time
from datetime import datetime, timedelta
from database.database import db
from utils.otp_service import OTPService
import logging

logger = logging.getLogger(__name__)

class AuthenticationManager:
    def __init__(self):
        self.otp_service = OTPService()

    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def generate_otp(self):
        """Generate 6-digit OTP"""
        return str(secrets.randbelow(900000) + 100000)

    def send_otp(self, mobile_number):
        """Send OTP to mobile number"""
        try:
            # Generate OTP
            otp_code = self.generate_otp()
            expires_at = datetime.now() + timedelta(seconds=30)
            
            # Store OTP in database
            query = '''
                INSERT INTO otp_verification (mobile_number, otp_code, expires_at)
                VALUES (%s, %s, %s)
            '''
            result = db.execute_query(query, (mobile_number, otp_code, expires_at))
            
            if result:
                # Send OTP via SMS (using Twilio)
                success = self.otp_service.send_sms(mobile_number, otp_code)
                if success:
                    logger.info(f"OTP sent successfully to {mobile_number}")
                    return True, "OTP sent successfully"
                else:
                    return False, "Failed to send OTP"
            else:
                return False, "Failed to store OTP"
                
        except Exception as e:
            logger.error(f"Error sending OTP: {e}")
            return False, "Error sending OTP"

    def verify_otp(self, mobile_number, otp_code):
        """Verify OTP code"""
        try:
            query = '''
                SELECT * FROM otp_verification 
                WHERE mobile_number = %s AND otp_code = %s AND is_used = FALSE
                ORDER BY created_at DESC LIMIT 1
            '''
            result = db.execute_query(query, (mobile_number, otp_code))
            
            if not result:
                return False, "Invalid OTP"
            
            otp_record = result[0]
            
            # Check if OTP is expired
            if datetime.now() > otp_record['expires_at']:
                return False, "OTP expired"
            
            # Mark OTP as used
            update_query = '''
                UPDATE otp_verification SET is_used = TRUE 
                WHERE id = %s
            '''
            db.execute_query(update_query, (otp_record['id'],))
            
            return True, "OTP verified successfully"
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False, "Error verifying OTP"

    def register_user(self, name, enrollment_no, mobile_number, role='student'):
        """Register new user"""
        try:
            # Check if user already exists
            check_query = '''
                SELECT id FROM users WHERE enrollment_no = %s OR mobile_number = %s
            '''
            existing = db.execute_query(check_query, (enrollment_no, mobile_number))
            
            if existing:
                return False, "User already exists with this enrollment number or mobile"
            
            # Insert new user
            insert_query = '''
                INSERT INTO users (name, enrollment_no, mobile_number, role)
                VALUES (%s, %s, %s, %s)
            '''
            result = db.execute_query(insert_query, (name, enrollment_no, mobile_number, role))
            
            if result:
                return True, "User registered successfully"
            else:
                return False, "Failed to register user"
                
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False, "Error registering user"

    def authenticate_user(self, identifier, password):
        """Authenticate user with enrollment number/faculty_id/mobile and password"""
        try:
            query = '''
                SELECT * FROM users 
                WHERE (enrollment_no = %s OR faculty_id = %s OR mobile_number = %s) AND is_verified = TRUE
            '''
            result = db.execute_query(query, (identifier, identifier, identifier))
            
            if not result:
                return False, None, "User not found or not verified"
            
            user = result[0]
            
            if user['password_hash'] and self.verify_password(password, user['password_hash']):
                return True, user, "Authentication successful"
            else:
                return False, None, "Invalid credentials"
                
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return False, None, "Authentication error"

    def verify_user_registration(self, enrollment_no):
        """Verify user registration and mark as verified"""
        try:
            query = '''
                UPDATE users SET is_verified = TRUE 
                WHERE enrollment_no = %s
            '''
            result = db.execute_query(query, (enrollment_no,))
            
            if result:
                return True, "User verified successfully"
            else:
                return False, "Failed to verify user"
                
        except Exception as e:
            logger.error(f"Error verifying user: {e}")
            return False, "Error verifying user"

# Initialize authentication manager
auth_manager = AuthenticationManager()