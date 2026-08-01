import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()


class Config:
    """
    SecureAttend Pro Configuration
    """

    # =========================
    # Database Configuration
    # =========================
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'attendance_system')

    # Optional SQLite support
    USE_SQLITE = os.getenv('USE_SQLITE', 'false').lower() == 'true'
    DATABASE_URL = os.getenv('DATABASE_URL', '')

    # =========================
    # Flask Configuration
    # =========================
    SECRET_KEY = os.getenv(
        'SECRET_KEY',
        'secureattend-pro-secret-key-2026'
    )

    DEBUG = os.getenv(
        'DEBUG',
        'True'
    ).lower() == 'true'

    # =========================
    # Session Configuration
    # =========================
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Enable this only if using HTTPS
    SESSION_COOKIE_SECURE = False

    # =========================
    # CSRF Protection
    # =========================
    CSRF_SESSION_KEY = 'csrf_token'

    CSRF_TOKEN_LENGTH = 32

    # =========================
    # OTP / Security
    # =========================
    OTP_EXPIRY_SECONDS = 60
    PASSWORD_RESET_OTP_EXPIRY_SECONDS = int(os.getenv('PASSWORD_RESET_OTP_EXPIRY_SECONDS', '60'))

    MAX_LOGIN_ATTEMPTS = 5

    FACE_RECOGNITION_TOLERANCE = 0.6

    # =========================
    # Twilio Configuration
    # (Future Work)
    # =========================
    TWILIO_ACCOUNT_SID = os.getenv(
        'TWILIO_ACCOUNT_SID',
        'your_twilio_sid'
    )

    TWILIO_AUTH_TOKEN = os.getenv(
        'TWILIO_AUTH_TOKEN',
        'your_twilio_token'
    )

    TWILIO_PHONE_NUMBER = os.getenv(
        'TWILIO_PHONE_NUMBER',
        '+919898656532'
    )

    # =========================
    # File Upload Configuration
    # =========================
    UPLOAD_FOLDER = 'static/uploads'

    FACE_IMAGES_FOLDER = 'static/face_images'

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # =========================
    # RFID Configuration
    # (Future Work)
    # =========================
    RFID_PORT = os.getenv(
        'RFID_PORT',
        'COM3'
    )

    RFID_BAUDRATE = 9600