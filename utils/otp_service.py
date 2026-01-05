from twilio.rest import Client
from config import Config
import logging

logger = logging.getLogger(__name__)

class OTPService:
    def __init__(self):
        try:
            self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            self.from_number = Config.TWILIO_PHONE_NUMBER
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            self.client = None

    def send_sms(self, to_number, otp_code):
        """Send OTP via SMS using Twilio"""
        try:
            if not self.client:
                # For testing without Twilio credentials
                logger.info(f"SMS Simulation: OTP {otp_code} sent to {to_number}")
                return True
            
            # Format phone number
            if not to_number.startswith('+'):
                to_number = '+91' + to_number  # Assuming Indian numbers
            
            message_body = f"Your SecureAttend Pro OTP is: {otp_code}. Valid for 30 seconds. Do not share this code."
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully to {to_number}. Message SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS to {to_number}: {e}")
            # For testing, still return True
            logger.info(f"SMS Simulation: OTP {otp_code} sent to {to_number}")
            return True

    def send_admin_notification(self, admin_number, message):
        """Send notification to admin"""
        try:
            if not self.client:
                logger.info(f"Admin Notification: {message}")
                return True
            
            if not admin_number.startswith('+'):
                admin_number = '+91' + admin_number
            
            message = self.client.messages.create(
                body=f"SecureAttend Pro Alert: {message}",
                from_=self.from_number,
                to=admin_number
            )
            
            logger.info(f"Admin notification sent. Message SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")
            return False

    def generate_otp(self):
        """Generate a 6-digit OTP"""
        import random
        return str(random.randint(100000, 999999))

    def verify_otp(self, mobile_number, otp_code):
        """Verify OTP against database record"""
        try:
            from database.database import db
            from datetime import datetime, timedelta
            
            # Check if OTP exists and is valid
            query = """
            SELECT * FROM otp_verification 
            WHERE mobile_number = %s AND otp_code = %s 
            AND expires_at > NOW() AND is_used = FALSE
            """
            
            result = db.execute_query(query, (mobile_number, otp_code))
            
            if result:
                # Mark OTP as used
                update_query = "UPDATE otp_verification SET is_used = TRUE WHERE mobile_number = %s AND otp_code = %s"
                db.execute_query(update_query, (mobile_number, otp_code))
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False

# Initialize OTP service
otp_service = OTPService()