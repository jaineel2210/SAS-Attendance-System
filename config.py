import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Database Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'attendance_system')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-super-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # Session expires after 30 minutes
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False  # Sessions are not permanent
    
    # Twilio Configuration (for OTP)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'your_twilio_sid') # future work
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'your_twilio_token') # future work
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+919898656532') # Temporary number not for purpose
    
    # Security Configuration
    OTP_EXPIRY_SECONDS = 60
    FACE_RECOGNITION_TOLERANCE = 0.6
    MAX_LOGIN_ATTEMPTS = 5
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'static/uploads'
    FACE_IMAGES_FOLDER = 'static/face_images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # RFID Configuration(future work)
    RFID_PORT = os.getenv('RFID_PORT', 'COM3')  # Change based on your system
    RFID_BAUDRATE = 9600