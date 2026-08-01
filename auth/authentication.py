import bcrypt
import secrets
import re
from datetime import datetime, timedelta
from database.database import db
from utils.otp_service import OTPService
from config import Config
import logging

logger = logging.getLogger(__name__)

PASSWORD_RULES = re.compile(
    r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};:\"\\|,.<>/?]).{8,}$'
)

class AuthenticationManager:
    def __init__(self):
        self.otp_service = OTPService()

    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def is_strong_password(self, password):
        """Validate the password strength rules."""
        return bool(PASSWORD_RULES.match(password))

    def generate_otp(self):
        """Generate 6-digit OTP"""
        return str(secrets.randbelow(900000) + 100000)

    def find_user_for_password_reset(self, identifier, role=None):
        """Find a user by enrollment number, faculty/admin ID, or mobile number."""
        if not identifier:
            return None

        query = '''
            SELECT * FROM users
            WHERE (enrollment_no = %s OR faculty_id = %s OR mobile_number = %s OR email = %s)
        '''
        params = (identifier, identifier, identifier, identifier)
        if role:
            query += ' AND role = %s'
            params = (*params, role)

        result = db.execute_query(query, params)
        return result[0] if result else None

    def send_password_reset_otp(self, user, request_ip=None):
        """Send password reset OTP to the user's registered mobile number."""
        if not user or not user.get('mobile_number'):
            return False, 'User not found or missing registered mobile number'

        otp_code = self.generate_otp()
        expires_at = datetime.now() + timedelta(seconds=Config.PASSWORD_RESET_OTP_EXPIRY_SECONDS)

        query = '''
            INSERT INTO password_reset_otp 
            (user_id, mobile_number, role, identifier, otp_code, expires_at, request_ip)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        '''
        params = (
            user['id'],
            user['mobile_number'],
            user.get('role'),
            user.get('enrollment_no') or user.get('faculty_id') or user.get('mobile_number'),
            otp_code,
            expires_at,
            request_ip
        )
        result = db.execute_query(query, params)

        if not result:
            return False, 'Failed to store OTP request'

        success = self.otp_service.send_sms(user['mobile_number'], otp_code)
        if success:
            logger.info(f'Password reset OTP sent to {user["mobile_number"]}')
            return True, 'OTP sent to your registered mobile number'

        logger.warning(f'OTP fallback mode engaged for {user["mobile_number"]}')
        return True, 'OTP sent in local fallback mode'

    def verify_password_reset_otp(self, mobile_number, otp_code):
        """Verify password reset OTP"""
        try:
            query = '''
                SELECT * FROM password_reset_otp
                WHERE mobile_number = %s AND otp_code = %s AND is_used = FALSE
                ORDER BY created_at DESC LIMIT 1
            '''
            result = db.execute_query(query, (mobile_number, otp_code))
            if not result:
                return False, 'Invalid OTP'

            otp_record = result[0]
            if datetime.now() > otp_record['expires_at']:
                return False, 'OTP expired'

            update_query = '''
                UPDATE password_reset_otp SET is_used = TRUE WHERE id = %s
            '''
            db.execute_query(update_query, (otp_record['id'],))
            return True, 'OTP verified successfully'
        except Exception as e:
            logger.error(f'Error verifying password reset OTP: {e}')
            return False, 'Error verifying OTP'

    def reset_user_password(self, user_id, new_password):
        """Reset the user's password with a secure hash."""
        if not self.is_strong_password(new_password):
            return False, 'Password must be at least 8 characters long and include uppercase, lowercase, number, and special character'

        password_hash = self.hash_password(new_password)
        query = 'UPDATE users SET password_hash = %s WHERE id = %s'
        result = db.execute_query(query, (password_hash, user_id))
        if result:
            return True, 'Password updated successfully'
        return False, 'Failed to update password'

    def send_otp(self, mobile_number):
        """Send OTP to mobile number"""
        try:
            # Generate OTP
            otp_code = self.generate_otp()
            expires_at = datetime.now() + timedelta(seconds=Config.PASSWORD_RESET_OTP_EXPIRY_SECONDS)
            
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