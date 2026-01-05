# Copyright © 2025
# Jaineel Pandya
# Dhwanil Patel
# All rights reserved.

# app.py (corrected)
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, make_response, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from database.database import db
from auth.authentication import auth_manager
import traceback
import sys
from face_processing.face_processor import face_processor
from rfid.rfid_reader import rfid_reader
# from utils.analytics import analytics  # Temporarily disabled due to matplotlib issues
from utils.otp_service import otp_service

# Try to import qr_service, use mock if not available
try:
    from utils.qr_service import qr_service
except ImportError:
    print("Warning: qrcode module not found. QR functionality will be disabled.")
    class MockQRService:
        def generate_qr_code(self, *args, **kwargs):
            return None
        def verify_qr_scan(self, *args, **kwargs):
            return False, "QR service not available"
    qr_service = MockQRService()

from enhanced_registration import enhanced_registration
from config import Config
import os
from datetime import datetime, timedelta
import logging
import hashlib
from functools import wraps

# Temporary mock analytics class (kept as-is since original file provided it)
class MockAnalytics:
    def get_class_summary(self, user_id, date):
        return [
            {
                'subject': 'No Classes',
                'session_type': 'lecture',
                'present_students': 0,
                'total_students': 0,
                'percentage': 0
            }
        ]
    def get_student_attendance_data(self, user_id):
        return []
    def calculate_attendance_percentage(self, user_id):
        return {
            'percentage': 0.0,
            'total_sessions': 0,
            'attended_sessions': 0
        }
    def get_subject_wise_attendance(self, user_id):
        return []
    def get_weekly_attendance_data(self, user_id):
        return []
    def get_monthly_attendance_data(self, user_id):
        return []
    def create_attendance_chart(self, data, chart_type):
        return ""

analytics = MockAnalytics()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Generate a unique server instance ID on startup
# This changes every time the server restarts, invalidating old sessions
import uuid
SERVER_INSTANCE_ID = str(uuid.uuid4())
logger.info(f"Server started with instance ID: {SERVER_INSTANCE_ID}")

# Ensure upload directories exist (use config values if present)
os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
os.makedirs(app.config.get('FACE_IMAGES_FOLDER', 'face_images'), exist_ok=True)

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevent CSRF
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Session expires after 30 minutes
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session on each request

# Session validation - Auto logout on server restart
@app.before_request
def validate_session():
    """
    Validate session before each request.
    Auto-logout if server was restarted (session from old server instance).
    """
    # Skip validation for static files and public routes
    public_routes = ['login', 'enhanced_registration.register_role', 'enhanced_registration.register_home',
                     'enhanced_registration.handle_registration', 'index', 'static', 'favicon', 
                     'handle_options', 'enhanced_registration.resend_otp']
    
    # Check if this is a public route
    if request.endpoint in public_routes or request.path.startswith('/static/'):
        return None
    
    # If user is logged in, check if session is from current server instance
    if 'user_id' in session:
        # Check if session has server instance ID
        session_instance_id = session.get('server_instance_id')
        
        # If session doesn't have instance ID or it doesn't match current server
        if not session_instance_id or session_instance_id != SERVER_INSTANCE_ID:
            # Clear the session
            session.clear()
            flash('Your session has expired due to server restart. Please login again.', 'warning')
            logger.info("Session invalidated due to server restart")
            return redirect(url_for('login'))
        
        # Update last activity timestamp
        session['last_activity'] = datetime.now().timestamp()
        session.modified = True
    
    return None

# CORS / headers handling: single consolidated after_request and OPTIONS handler
@app.after_request
def set_response_headers(response):
    """
    Single after_request handler to add CORS and default Content-Type when missing.
    (Replaces multiple duplicate handlers present previously.)
    """
    # If template render produced a response with a Content-Type, keep it.
    if not response.headers.get('Content-Type'):
        # Default to JSON when no content-type is set (safe fallback)
        response.headers['Content-Type'] = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, Authorization'
    return response

# Handle preflight OPTIONS requests globally
@app.route('/<path:_>', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def handle_options(_=""):
    resp = make_response()
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, PUT, DELETE'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, Authorization'
    return resp

# Add favicon route to prevent 405 errors
@app.route('/favicon.ico')
def favicon():
    """Serve favicon.ico or return empty response if not found"""
    try:
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    except:
        # Return empty response if favicon doesn't exist
        return '', 204

# Initialize database when app starts
def initialize_database():
    """Initialize database connection and create tables"""
    try:
        if db.connect():
            db.create_tables()
            # optional: db.insert_sample_data()  # kept out if undesired in production
            logger.info("Database initialized successfully")
        else:
            logger.error("Failed to initialize database")
    except Exception as e:
        logger.error(f"Exception while initializing database: {e}")
        logger.error(traceback.format_exc())

# Initialize database within app context
with app.app_context():
    initialize_database()

# Helper decorators
def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def faculty_required(f):
    """Decorator to require faculty or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['admin', 'faculty']:
            flash('Faculty access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Register blueprint(s)
try:
    app.register_blueprint(enhanced_registration)
except Exception as e:
    logger.warning(f"Could not register enhanced_registration blueprint: {e}")

# before_request: session expiry tracking
@app.before_request
def track_session_activity():
    """Update and validate last activity timestamp for session expiry"""
    if 'user_id' in session:
        if 'last_activity' in session:
            try:
                last_activity = datetime.fromtimestamp(session['last_activity'])
                if datetime.now() - last_activity > timedelta(minutes=30):
                    session.clear()
                    return redirect(url_for('login'))
            except Exception:
                # If parsing fails, clear session and redirect to login
                session.clear()
                return redirect(url_for('login'))
        session['last_activity'] = datetime.now().timestamp()

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with OTP support for admins"""
    if request.method == 'GET':
        session.pop('temp_admin_mobile', None)
        session.pop('temp_admin_password', None)
        session.pop('temp_admin_identifier', None)
        session.pop('temp_role', None)
        return render_template('login.html')
    
    def error_response(message):
        flash(message, 'error')
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': message})
        return render_template('login.html')
    
    def success_response(redirect_url):
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'redirect': redirect_url})
        return redirect(redirect_url)

    if request.method == 'POST':
        try:
            logger.info("Login attempt received")
            identifier = request.form.get('identifier')
            password = request.form.get('password')
            role = request.form.get('role', 'student')
            mobile_number = request.form.get('mobile_number')  # For admin OTP login
            otp_code = request.form.get('otp_code')  # OTP verification
            
            logger.info(f"Login attempt - Role: {role}, Identifier: {identifier}")

            # Handle Admin OTP Login Flow
            if role == 'admin':
                # Case 1: Admin requesting OTP (no OTP code provided yet)
                if mobile_number and not otp_code:
                    # Validate identifier and password first
                    if not identifier or not identifier.strip():
                        return error_response('Please enter your admin ID')
                    if not password or not password.strip():
                        return error_response('Please enter your password')
                    
                    # Authenticate with password first
                    success, user, message = auth_manager.authenticate_user(identifier, password)
                    
                    if not success:
                        return error_response(f'Invalid credentials: {message}')
                    
                    if user['role'] != 'admin':
                        return error_response('This account is not an admin account')
                    
                    # Check if mobile number matches
                    if user.get('mobile_number') != mobile_number:
                        return error_response('Mobile number does not match your registered number')
                    
                    # Send OTP
                    otp_success, otp_message = auth_manager.send_otp(mobile_number)
                    
                    if otp_success:
                        # Store temp data in session for OTP verification
                        session['temp_admin_mobile'] = mobile_number
                        session['temp_admin_password'] = password
                        session['temp_admin_identifier'] = identifier
                        session['temp_role'] = role
                        session.modified = True
                        
                        flash('OTP sent to your mobile number. Please enter it to continue.', 'info')
                        return render_template('login.html')
                    else:
                        return error_response(f'Failed to send OTP: {otp_message}')
                
                # Case 2: Admin verifying OTP
                elif otp_code and session.get('temp_admin_mobile'):
                    mobile_number = session.get('temp_admin_mobile')
                    password = session.get('temp_admin_password')
                    identifier = session.get('temp_admin_identifier')
                    
                    # Verify OTP
                    otp_success, otp_message = auth_manager.verify_otp(mobile_number, otp_code)
                    
                    if not otp_success:
                        flash(f'Invalid OTP: {otp_message}', 'error')
                        return render_template('login.html')
                    
                    # OTP verified, authenticate user
                    success, user, message = auth_manager.authenticate_user(identifier, password)
                    
                    if success and user['role'] == 'admin':
                        # Clear temp session data
                        session.pop('temp_admin_mobile', None)
                        session.pop('temp_admin_password', None)
                        session.pop('temp_admin_identifier', None)
                        session.pop('temp_role', None)
                        
                        # Set actual session data
                        session['user_id'] = user['id']
                        session['username'] = user['name']
                        session['role'] = user['role']
                        session['enrollment_no'] = user.get('enrollment_no', '')
                        session['faculty_id'] = user.get('faculty_id', '')  # Add faculty_id for faculty users
                        session['last_activity'] = datetime.now().timestamp()
                        session['server_instance_id'] = SERVER_INSTANCE_ID  # Track server instance
                        session.permanent = True  # Make session permanent (respects PERMANENT_SESSION_LIFETIME)
                        session.modified = True

                        logger.info(f"Admin {user['name']} logged in successfully with OTP")

                        # Update last login
                        try:
                            db.execute_query("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user['id'],))
                        except Exception as e:
                            logger.error(f"Failed to update last login: {str(e)}")

                        flash('Login successful', 'success')
                        return success_response(url_for('dashboard'))
                    else:
                        # Clear temp session
                        session.pop('temp_admin_mobile', None)
                        session.pop('temp_admin_password', None)
                        session.pop('temp_admin_identifier', None)
                        session.pop('temp_role', None)
                        return error_response('Authentication failed after OTP verification')
                
                else:
                    return error_response('Please provide mobile number to receive OTP')
            
            # Regular login for students and faculty (password only)
            else:
                # Validate required fields
                if not identifier or not identifier.strip():
                    return error_response('Please enter your ID/enrollment number')
                if not password or not password.strip():
                    return error_response('Please enter your password')

                # Authenticate user
                success, user, message = auth_manager.authenticate_user(identifier, password)
                logger.info(f"Authentication result: success={success}, message={message}")

                if success:
                    if user['role'] != role:
                        logger.warning(f"Role mismatch: expected {role}, got {user['role']}")
                        return error_response(f'Invalid login attempt. This account is registered as {user["role"]}')

                    # Set session data
                    session.clear()
                    session['user_id'] = user['id']
                    session['username'] = user['name']
                    session['role'] = user['role']
                    session['enrollment_no'] = user.get('enrollment_no', '')
                    session['faculty_id'] = user.get('faculty_id', '')  # Add faculty_id for faculty users
                    session['last_activity'] = datetime.now().timestamp()
                    session['server_instance_id'] = SERVER_INSTANCE_ID  # Track server instance
                    session.permanent = True  # Make session permanent (respects PERMANENT_SESSION_LIFETIME)
                    session.modified = True

                    logger.info(f"User {user['name']} ({user['role']}) logged in successfully")

                    # Update last login
                    try:
                        db.execute_query("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user['id'],))
                    except Exception as e:
                        logger.error(f"Failed to update last login: {str(e)}")

                    flash('Login successful', 'success')
                    return success_response(url_for('dashboard'))
                else:
                    return error_response(f'Login failed: {message}')

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            logger.error(traceback.format_exc())
            return error_response('An error occurred during login. Please try again.')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Redirect to enhanced registration home page"""
    return redirect(url_for('enhanced_registration.register_home'))

@app.route('/capture_face', methods=['POST'])
def capture_face():
    """Capture and store face encoding"""
    try:
        # Accept both JSON and form-encoded (if necessary)
        data = request.get_json(silent=True) or request.form.to_dict()
        enrollment_no = data.get('enrollment_no')
        image_data = data.get('image_data')

        if not enrollment_no or not image_data:
            return jsonify({'success': False, 'message': 'Missing data'})

        success, message = face_processor.store_face_encoding(enrollment_no, image_data)

        if success:
            try:
                auth_manager.verify_user_registration(enrollment_no)
            except Exception as e:
                logger.warning(f"verify_user_registration failed: {e}")
            try:
                rfid_success, rfid_data = rfid_reader.register_card(enrollment_no)
            except Exception as e:
                logger.warning(f"rfid register_card failed: {e}")
                rfid_success, rfid_data = False, None

            return jsonify({
                'success': True,
                'message': 'Face captured successfully',
                'rfid_registered': rfid_success,
                'rfid_uid': rfid_data if rfid_success else None
            })
        else:
            return jsonify({'success': False, 'message': message})

    except Exception as e:
        logger.error(f"Error in face capture: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': 'Face capture failed'})

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    user_role = session.get('role')
    user_id = session.get('user_id')

    try:
        if user_role == 'admin':
            stats_query = '''
                SELECT 
                    (SELECT COUNT(*) FROM users WHERE role = 'student') as total_students,
                    (SELECT COUNT(*) FROM users WHERE role = 'faculty') as total_faculty,
                    (SELECT COUNT(*) FROM attendance WHERE attendance_date = CURDATE()) as today_attendance,
                    (SELECT COUNT(DISTINCT subject) FROM sessions) as total_subjects
            '''
            stats = db.execute_query(stats_query)
            dashboard_stats = stats[0] if stats else {}
            return render_template('dashboard/admin_dashboard.html', stats=dashboard_stats)

        elif user_role == 'faculty':
            today = datetime.now().date()
            class_summary = analytics.get_class_summary(user_id, today)
            return render_template('dashboard/faculty_dashboard.html', 
                                 class_summary=class_summary, today=today)
        else:
            attendance_data = analytics.get_student_attendance_data(user_id)
            attendance_percentage = analytics.calculate_attendance_percentage(user_id)
            subject_wise_data = analytics.get_subject_wise_attendance(user_id)
            return render_template('dashboard/student_dashboard.html',
                                 attendance_data=attendance_data,
                                 attendance_percentage=attendance_percentage,
                                 subject_wise_data=subject_wise_data)
    except Exception as e:
        logger.error(f"Error in dashboard rendering: {e}")
        logger.error(traceback.format_exc())
        # Fallback to simple dashboard or error page
        return render_template('dashboard/error_dashboard.html'), 500

@app.route('/mark_attendance')
@login_required
def mark_attendance():
    """Attendance marking interface for students"""
    if session.get('role') != 'student':
        flash('Only students can mark attendance', 'error')
        return redirect(url_for('dashboard'))
    return render_template('attendance/mark_attendance.html')

@app.route('/mark_student_attendance', methods=['POST'])
@login_required
def mark_student_attendance():
    """Process student's own attendance marking (face recognition)"""
    try:
        # Accept both JSON and form data
        data = request.get_json(silent=True) or request.form.to_dict()
        method = data.get('method')  # 'face' or 'rfid'
        current_user_id = session.get('user_id')

        if session.get('role') != 'student':
            return jsonify({'success': False, 'message': 'Only students can use this endpoint'})

        # Get student's department info
        user_query = "SELECT name, enrollment_no, department FROM users WHERE id = %s"
        user_info = db.execute_query(user_query, (current_user_id,))
        
        if not user_info:
            return jsonify({'success': False, 'message': 'User information not found'})

        user = user_info[0]
        department = user.get('department', 'Computer Science')  # Default if not set
        
        # Get current time and day
        from datetime import datetime, time as dt_time
        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime('%A')
        
        # Find current period from timetable
        timetable_query = '''
            SELECT period_number, start_time, end_time, subject, session_type
            FROM student_timetable 
            WHERE department = %s 
            AND day_of_week = %s 
            AND start_time <= %s 
            AND end_time >= %s
            AND is_active = TRUE
            ORDER BY period_number
            LIMIT 1
        '''
        
        current_period = db.execute_query(timetable_query, (department, current_day, current_time, current_time))
        
        if not current_period:
            # If no current period, allow marking for any available period today
            available_periods_query = '''
                SELECT period_number, start_time, end_time, subject, session_type
                FROM student_timetable 
                WHERE department = %s 
                AND day_of_week = %s 
                AND is_active = TRUE
                ORDER BY period_number
            '''
            available_periods = db.execute_query(available_periods_query, (department, current_day))
            
            if not available_periods:
                return jsonify({'success': False, 'message': f'No classes scheduled for {current_day}. Please check your timetable.'})
            
            # Find the next period that hasn't been marked
            for period in available_periods:
                check_query = '''
                    SELECT id FROM attendance 
                    WHERE user_id = %s 
                    AND attendance_date = CURDATE()
                    AND period_number = %s
                    AND subject = %s
                '''
                existing = db.execute_query(check_query, (current_user_id, period['period_number'], period['subject']))
                
                if not existing:
                    current_period = [period]
                    break
            
            if not current_period:
                return jsonify({'success': False, 'message': 'You have already marked attendance for all today\'s classes.'})

        period_info = current_period[0]
        
        # Check if already marked for this period
        check_query = '''
            SELECT id FROM attendance 
            WHERE user_id = %s 
            AND attendance_date = CURDATE()
            AND period_number = %s
            AND subject = %s
        '''
        existing = db.execute_query(check_query, (current_user_id, period_info['period_number'], period_info['subject']))

        if existing:
            return jsonify({
                'success': False, 
                'message': f'You have already marked attendance for {period_info["subject"]} (Period {period_info["period_number"]}) today.'
            })

        if method == 'face':
            image_data = data.get('image_data')
            if not image_data:
                return jsonify({'success': False, 'message': 'No image data provided'})

            success, recognized_user, message = face_processor.verify_face_from_image(image_data, current_user_id)

            if success:
                insert_query = '''
                    INSERT INTO attendance 
                    (user_id, faculty_id, attendance_date, attendance_time, marked_by_face, 
                     subject, session_type, period_number, period_start_time, period_end_time)
                    VALUES (%s, %s, CURDATE(), CURTIME(), TRUE, %s, %s, %s, %s, %s)
                '''
                try:
                    result = db.execute_query(insert_query, (
                        current_user_id, current_user_id, 
                        period_info['subject'], period_info['session_type'], 
                        period_info['period_number'], period_info['start_time'], period_info['end_time']
                    ))
                    
                    if result:
                        # Emit Socket.IO event for real-time analytics update
                        socketio.emit('attendance_marked', {
                            'student_name': user['name'],
                            'enrollment_no': user['enrollment_no'],
                            'subject': period_info['subject'],
                            'period': period_info['period_number'],
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                        return jsonify({
                            'success': True, 
                            'message': f'Attendance marked successfully for {period_info["subject"]} (Period {period_info["period_number"]})!',
                            'student_name': user['name'],
                            'enrollment_no': user['enrollment_no'],
                            'subject': period_info['subject'],
                            'period': period_info['period_number'],
                            'session_type': period_info['session_type']
                        })
                    else:
                        logger.error(f'Failed to save attendance record for user {current_user_id}')
                        return jsonify({'success': False, 'message': 'Failed to save attendance record'})
                except Exception as e:
                    logger.error(f'Database error while saving attendance: {str(e)}')
                    logger.error(traceback.format_exc())
                    return jsonify({'success': False, 'message': f'Database error: {str(e)}'})
            else:
                return jsonify({'success': False, 'message': message})

        elif method == 'rfid':
            rfid_uid = data.get('rfid_uid')
            if not rfid_uid:
                return jsonify({'success': False, 'message': 'RFID UID not provided'})

            verify_query = "SELECT id, name, enrollment_no FROM users WHERE id = %s AND rfid_uid = %s"
            user_verify = db.execute_query(verify_query, (current_user_id, rfid_uid))

            if not user_verify:
                return jsonify({'success': False, 'message': 'RFID card does not match your account'})

            insert_query = '''
                INSERT INTO attendance 
                (user_id, attendance_date, attendance_time, marked_by_rfid, 
                 subject, session_type, period_number, period_start_time, period_end_time)
                VALUES (%s, CURDATE(), CURTIME(), TRUE, %s, %s, %s, %s, %s)
            '''
            result = db.execute_query(insert_query, (
                current_user_id, 
                period_info['subject'], period_info['session_type'], 
                period_info['period_number'], period_info['start_time'], period_info['end_time']
            ))

            if result:
                # Emit Socket.IO event for real-time analytics update
                socketio.emit('attendance_marked', {
                    'student_name': user['name'],
                    'enrollment_no': user['enrollment_no'],
                    'subject': period_info['subject'],
                    'period': period_info['period_number'],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                return jsonify({
                    'success': True, 
                    'message': f'Attendance marked successfully for {period_info["subject"]} (Period {period_info["period_number"]})!',
                    'student_name': user['name'],
                    'enrollment_no': user['enrollment_no'],
                    'subject': period_info['subject'],
                    'period': period_info['period_number'],
                    'session_type': period_info['session_type']
                })
            else:
                return jsonify({'success': False, 'message': 'Failed to save attendance record'})

        return jsonify({'success': False, 'message': 'Invalid method specified'})

    except Exception as e:
        logger.error(f"Error in mark_student_attendance: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/get_student_schedule', methods=['GET'])
@login_required
def get_student_schedule():
    """Get today's schedule and current period for logged-in student"""
    try:
        if session.get('role') != 'student':
            return jsonify({'success': False, 'message': 'Only students can access this endpoint'})
        
        current_user_id = session.get('user_id')
        
        # Get student's department
        user_query = "SELECT department FROM users WHERE id = %s"
        user_info = db.execute_query(user_query, (current_user_id,))
        
        if not user_info:
            return jsonify({'success': False, 'message': 'User information not found'})
        
        department = user_info[0].get('department', 'Computer Science')
        
        # Get current time and day
        from datetime import datetime
        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime('%A')
        
        # Get today's complete schedule
        schedule_query = '''
            SELECT period_number, start_time, end_time, subject, session_type
            FROM student_timetable 
            WHERE department = %s 
            AND day_of_week = %s 
            AND is_active = TRUE
            ORDER BY period_number
        '''
        
        today_schedule = db.execute_query(schedule_query, (department, current_day))
        
        if not today_schedule:
            return jsonify({
                'success': True,
                'message': f'No classes scheduled for {current_day}',
                'schedule': [],
                'current_period': None
            })
        
        # Find current period
        current_period = None
        for period in today_schedule:
            if period['start_time'] <= current_time <= period['end_time']:
                current_period = period
                break
        
        # Check attendance status for each period
        for period in today_schedule:
            check_query = '''
                SELECT id FROM attendance 
                WHERE user_id = %s 
                AND attendance_date = CURDATE()
                AND period_number = %s
                AND subject = %s
            '''
            existing = db.execute_query(check_query, (current_user_id, period['period_number'], period['subject']))
            period['marked'] = bool(existing)
            
            # Format times for display
            period['start_time_str'] = period['start_time'].strftime('%H:%M')
            period['end_time_str'] = period['end_time'].strftime('%H:%M')
        
        return jsonify({
            'success': True,
            'schedule': today_schedule,
            'current_period': current_period,
            'current_day': current_day
        })
        
    except Exception as e:
        logger.error(f"Error in get_student_schedule: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/get_student_attendance_history', methods=['GET'])
@login_required
def get_student_attendance_history():
    """Get attendance history for the logged-in student"""
    try:
        if session.get('role') != 'student':
            return jsonify({'success': False, 'message': 'Only students can access this endpoint'})
        
        current_user_id = session.get('user_id')
        days = request.args.get('days', 30, type=int)  # Default to last 30 days
        
        # Get attendance history
        history_query = '''
            SELECT attendance_date, attendance_time, subject, session_type, 
                   period_number, period_start_time, period_end_time,
                   marked_by_face, marked_by_rfid, status
            FROM attendance 
            WHERE user_id = %s 
            AND attendance_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY attendance_date DESC, period_number ASC
        '''
        
        history = db.execute_query(history_query, (current_user_id, days))
        
        if history:
            for record in history:
                # Format times and dates for display
                record['attendance_date_str'] = record['attendance_date'].strftime('%Y-%m-%d (%A)')
                record['attendance_time_str'] = record['attendance_time'].strftime('%H:%M')
                if record['period_start_time']:
                    record['period_start_time_str'] = record['period_start_time'].strftime('%H:%M')
                if record['period_end_time']:
                    record['period_end_time_str'] = record['period_end_time'].strftime('%H:%M')
                
                # Determine marking method
                if record['marked_by_face']:
                    record['marking_method'] = 'Face Recognition'
                elif record['marked_by_rfid']:
                    record['marking_method'] = 'RFID Card'
                else:
                    record['marking_method'] = 'Manual'
        
        return jsonify({
            'success': True,
            'history': history or [],
            'total_records': len(history) if history else 0
        })
        
    except Exception as e:
        logger.error(f"Error in get_student_attendance_history: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/generate_attendance_qr', methods=['POST'])
@login_required
def generate_attendance_qr():
    """Generate QR code for attendance session (Faculty only)"""
    try:
        if session.get('role') != 'faculty':
            return jsonify({'success': False, 'message': 'Only faculty can generate QR codes'})
        
        data = request.get_json() or request.form.to_dict()
        subject = data.get('subject')
        session_type = data.get('session_type', 'lecture')
        duration_minutes = int(data.get('duration_minutes', 10))  # Default 10 minutes
        
        if not subject or subject == 'None':
            return jsonify({'success': False, 'message': 'Please select a subject'})
        
        faculty_id = session.get('user_id')
        
        # Get client IP for location verification
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        location_hash = hashlib.sha256(f"{client_ip}:{subject}".encode()).hexdigest()[:16]
        
        # Generate QR code
        qr_result = qr_service.generate_session_qr(
            faculty_id=faculty_id,
            subject=subject,
            session_type=session_type,
            location_hash=location_hash,
            duration_minutes=duration_minutes
        )
        
        if qr_result['success']:
            # Store session in database
            session_query = '''
                INSERT INTO sessions 
                (faculty_id, subject, session_type, session_date, start_time, is_active, qr_session_id)
                VALUES (%s, %s, %s, CURDATE(), CURTIME(), TRUE, %s)
            '''
            
            # Add qr_session_id column to sessions table if it doesn't exist
            try:
                db.execute_query("ALTER TABLE sessions ADD COLUMN qr_session_id VARCHAR(255) UNIQUE")
            except:
                pass  # Column might already exist
            
            db_result = db.execute_query(session_query, (
                faculty_id, subject, session_type, qr_result['session_id']
            ))
            
            if db_result:
                # Emit real-time update to admin dashboard
                socketio.emit('new_session_started', {
                    'faculty_id': faculty_id,
                    'subject': subject,
                    'session_type': session_type,
                    'session_id': qr_result['session_id']
                }, room='admin_room')
                
                return jsonify({
                    'success': True,
                    'qr_code': qr_result['qr_code_base64'],
                    'session_id': qr_result['session_id'],
                    'expires_at': qr_result['expires_at'],
                    'subject': subject,
                    'session_type': session_type,
                    'duration_minutes': duration_minutes
                })
            else:
                return jsonify({'success': False, 'message': 'Failed to save session to database'})
        else:
            return jsonify({'success': False, 'message': qr_result.get('error', 'Failed to generate QR code')})
            
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/scan_attendance_qr', methods=['POST'])
@login_required
def scan_attendance_qr():
    """Scan QR code for attendance (Students only)"""
    try:
        if session.get('role') != 'student':
            return jsonify({'success': False, 'message': 'Only students can scan QR codes'})
        
        data = request.get_json() or request.form.to_dict()
        qr_data = data.get('qr_data')
        face_image = data.get('face_image')  # Base64 encoded image
        
        if not qr_data:
            return jsonify({'success': False, 'message': 'QR code data not provided'})
        
        if not face_image:
            return jsonify({'success': False, 'message': 'Face image not provided'})
        
        student_id = session.get('user_id')
        
        # First, verify face recognition
        success, recognized_user, face_message = face_processor.verify_face_from_image(face_image, student_id)
        
        if not success:
            return jsonify({'success': False, 'message': f'Face verification failed: {face_message}'})
        
        # Get client IP for location verification
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Validate QR code
        qr_result = qr_service.validate_qr_scan(
            qr_data=qr_data,
            student_id=student_id,
            client_ip=client_ip
        )
        
        if not qr_result['success']:
            return jsonify({'success': False, 'message': qr_result['error']})
        
        # Get student info
        student_query = "SELECT name, enrollment_no, department FROM users WHERE id = %s"
        student_info = db.execute_query(student_query, (student_id,))
        
        if not student_info:
            return jsonify({'success': False, 'message': 'Student information not found'})
        
        student = student_info[0]
        
        # Check if already marked attendance for this session
        check_query = '''
            SELECT id FROM attendance 
            WHERE user_id = %s 
            AND attendance_date = CURDATE()
            AND subject = %s
            AND qr_session_id = %s
        '''
        existing = db.execute_query(check_query, (student_id, qr_result['subject'], qr_result['session_id']))
        
        if existing:
            return jsonify({'success': False, 'message': 'You have already marked attendance for this session'})
        
        # Mark attendance
        attendance_query = '''
            INSERT INTO attendance 
            (user_id, faculty_id, attendance_date, attendance_time, 
             subject, session_type, marked_by_face, marked_by_qr, qr_session_id, status)
            VALUES (%s, %s, CURDATE(), CURTIME(), %s, %s, TRUE, TRUE, %s, 'P')
        '''
        
        # Add qr_session_id and marked_by_qr columns if they don't exist
        try:
            db.execute_query("ALTER TABLE attendance ADD COLUMN marked_by_qr BOOLEAN DEFAULT FALSE")
            db.execute_query("ALTER TABLE attendance ADD COLUMN qr_session_id VARCHAR(255)")
        except:
            pass  # Columns might already exist
        
        attendance_result = db.execute_query(attendance_query, (
            student_id, qr_result['faculty_id'], qr_result['subject'], 
            qr_result['session_type'], qr_result['session_id']
        ))
        
        if attendance_result:
            # Emit real-time update to faculty
            socketio.emit('student_marked_attendance', {
                'student_id': student_id,
                'student_name': student['name'],
                'enrollment_no': student['enrollment_no'],
                'subject': qr_result['subject'],
                'session_id': qr_result['session_id'],
                'total_scanned': qr_result['scanned_students']
            }, room=f"faculty_{qr_result['faculty_id']}")
            
            return jsonify({
                'success': True,
                'message': f'Attendance marked successfully for {qr_result["subject"]}!',
                'student_name': student['name'],
                'enrollment_no': student['enrollment_no'],
                'subject': qr_result['subject'],
                'session_type': qr_result['session_type']
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to mark attendance in database'})
            
    except Exception as e:
        logger.error(f"Error scanning QR code: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

# SocketIO Event Handlers for Real-time Updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    user_id = session.get('user_id')
    role = session.get('role')
    
    if user_id and role:
        # Join role-specific room
        join_room(f"{role}_room")
        
        if role == 'faculty':
            join_room(f"faculty_{user_id}")
        elif role == 'admin':
            join_room('admin_room')
        
        logger.info(f"User {user_id} ({role}) connected to SocketIO")
        emit('connected', {'status': 'Connected successfully'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user_id = session.get('user_id')
    role = session.get('role')
    
    if user_id and role:
        leave_room(f"{role}_room")
        if role == 'faculty':
            leave_room(f"faculty_{user_id}")
        elif role == 'admin':
            leave_room('admin_room')
        
        logger.info(f"User {user_id} ({role}) disconnected from SocketIO")

@socketio.on('join_session_room')
def handle_join_session_room(data):
    """Faculty joins their session room for real-time updates"""
    if session.get('role') == 'faculty':
        session_id = data.get('session_id')
        if session_id:
            join_room(f"session_{session_id}")
            emit('joined_session_room', {'session_id': session_id})

@socketio.on('request_session_update')
def handle_session_update_request(data):
    """Handle request for session attendance update"""
    if session.get('role') == 'faculty':
        session_id = data.get('session_id')
        faculty_id = session.get('user_id')
        
        # Get current session info
        session_info = qr_service.get_session_info(session_id)
        if session_info and session_info['faculty_id'] == faculty_id:
            emit('session_update', {
                'session_id': session_id,
                'students_scanned': len(session_info.get('students_scanned', [])),
                'is_active': session_info.get('is_active', False)
            })

# Update the main function to use SocketIO

@app.route('/start_attendance_session', methods=['POST'])
@faculty_required
def start_attendance_session():
    """Start attendance session for faculty (accepts JSON or form data)"""
    try:
        # Log incoming request for debugging
        logger.info(f"Request Content-Type: {request.content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request data: {request.get_data(as_text=True)}")

        # Accept both JSON and form data
        data = request.get_json(silent=True)
        if not data:
            # fallback to form or urlencoded body
            data = request.form.to_dict() or {}

        # Validate required fields
        if not isinstance(data, dict):
            return jsonify({'success': False, 'message': 'Request body must be a JSON object or form data'}), 400

        subject = data.get('subject')
        session_type = data.get('session_type')

        if not subject or not session_type:
            return jsonify({'success': False, 'message': 'Subject and session type are required'}), 400

        faculty_id = session.get('user_id')
        session_date = datetime.now().date()
        start_time = datetime.now().time()

        # Insert the new session
        query = '''
            INSERT INTO sessions (faculty_id, subject, session_type, session_date, start_time)
            VALUES (%s, %s, %s, %s, %s)
        '''
        session_id = db.execute_query(
            query,
            (faculty_id, subject, session_type, session_date, start_time),
            fetch_last_id=True
        )

        # Emit Socket.IO event for real-time analytics update
        socketio.emit('session_started', {
            'session_id': session_id,
            'subject': subject,
            'session_type': session_type,
            'faculty_id': faculty_id,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        return jsonify({
            'success': True,
            'message': 'Session started successfully',
            'session_id': session_id
        })

    except Exception as e:
        logger.error(f"Error in start_attendance_session: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': 'An error occurred while starting the session'}), 500

@app.route('/take_attendance')
@faculty_required
def take_attendance():
    """Take attendance interface for faculty"""
    return render_template('attendance/take_attendance.html')

@app.route('/process_attendance', methods=['POST'])
def process_attendance():
    """Process attendance marking (face + RFID)"""
    try:
        logger.info("Processing attendance request")
        
        # Accept JSON or form; prefer JSON
        data = request.get_json(silent=True) or request.form.to_dict()
        method = data.get('method') if isinstance(data, dict) else None
        if not method:
            logger.warning("Invalid method in attendance request")
            return jsonify({'success': False, 'message': 'Invalid method'}), 400

        logger.info(f"Attendance method: {method}")

        if method == 'face':
            logger.info("Starting face recognition process")
            success, user, message = face_processor.recognize_face_from_camera()
            logger.info(f"Face recognition result: success={success}, message={message}")

            if success:
                user_id = user['id']
                faculty_id = session.get('user_id')
                subject = data.get('subject', 'General')
                session_type = data.get('session_type', 'lecture')

                logger.info(f"Attempting to mark attendance for user {user_id} ({user['name']}) in {subject}")

                check_query = '''
                    SELECT id FROM attendance 
                    WHERE user_id = %s AND attendance_date = CURDATE() 
                    AND subject = %s AND session_type = %s
                '''
                existing = db.execute_query(check_query, (user_id, subject, session_type))

                if existing:
                    logger.warning(f"Attendance already marked for user {user_id} today")
                    return jsonify({'success': False, 'message': 'Attendance already marked for today'})

                insert_query = '''
                    INSERT INTO attendance 
                    (user_id, faculty_id, subject, session_type, attendance_date, attendance_time, marked_by_face)
                    VALUES (%s, %s, %s, %s, CURDATE(), CURTIME(), TRUE)
                '''
                result = db.execute_query(insert_query, (user_id, faculty_id, subject, session_type))

                if result:
                    logger.info(f"✅ Attendance marked successfully for {user['name']} ({user['enrollment_no']})")
                    return jsonify({
                        'success': True, 
                        'message': f'Attendance marked for {user["name"]} ({user["enrollment_no"]})',
                        'student_name': user['name'],
                        'enrollment_no': user['enrollment_no']
                    })
                else:
                    logger.error(f"Failed to insert attendance record for user {user_id}")
                    return jsonify({'success': False, 'message': 'Failed to mark attendance'})
            else:
                logger.warning(f"Face recognition failed: {message}")
                return jsonify({'success': False, 'message': message})

        elif method == 'rfid':
            rfid_uid = data.get('rfid_uid')
            if not rfid_uid:
                return jsonify({'success': False, 'message': 'RFID UID not provided'})

            success, user = rfid_reader.verify_card(rfid_uid)

            if success:
                user_id = user['id']
                faculty_id = session.get('user_id')
                subject = data.get('subject', 'General')
                session_type = data.get('session_type', 'lecture')

                check_query = '''
                    SELECT id FROM attendance 
                    WHERE user_id = %s AND attendance_date = CURDATE() 
                    AND subject = %s AND session_type = %s
                '''
                existing = db.execute_query(check_query, (user_id, subject, session_type))

                if existing:
                    return jsonify({'success': False, 'message': 'Attendance already marked for today'})

                insert_query = '''
                    INSERT INTO attendance 
                    (user_id, faculty_id, subject, session_type, attendance_date, attendance_time, marked_by_rfid)
                    VALUES (%s, %s, %s, %s, CURDATE(), CURTIME(), TRUE)
                '''
                result = db.execute_query(insert_query, (user_id, faculty_id, subject, session_type))

                if result:
                    return jsonify({
                        'success': True,
                        'message': f'Attendance marked for {user["name"]} ({user["enrollment_no"]})',
                        'student_name': user['name'],
                        'enrollment_no': user['enrollment_no']
                    })
                else:
                    return jsonify({'success': False, 'message': 'Failed to mark attendance'})
            else:
                return jsonify({'success': False, 'message': 'Invalid RFID card'})
        else:
            return jsonify({'success': False, 'message': 'Invalid method'})

    except Exception as e:
        logger.error(f"Error processing attendance: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': 'Error processing attendance'}), 500

@app.route('/get_session_stats/<int:session_id>', methods=['GET'])
@faculty_required
def get_session_stats(session_id):
    """Get real-time statistics for a session"""
    try:
        # Get session details
        session_query = '''
            SELECT * FROM sessions 
            WHERE id = %s AND faculty_id = %s
        '''
        session_data = db.execute_query(session_query, (session_id, session.get('user_id')))
        
        if not session_data:
            return jsonify({'success': False, 'message': 'Session not found'}), 404
        
        # Get attendance statistics for this session
        stats_query = '''
            SELECT 
                COUNT(*) as present_count,
                COUNT(DISTINCT u.enrollment_no) as unique_students,
                MAX(a.attendance_time) as last_attendance_time
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE a.faculty_id = %s 
            AND a.subject = %s 
            AND a.session_type = %s
            AND a.attendance_date = CURDATE()
        '''
        stats = db.execute_query(stats_query, (
            session.get('user_id'), 
            session_data[0]['subject'],
            session_data[0]['session_type']
        ))
        
        # Get total expected students (this is a simplified approach - you might want to adjust based on class enrollment)
        total_students_query = '''
            SELECT COUNT(*) as total_students 
            FROM users 
            WHERE role = 'student'
        '''
        total_data = db.execute_query(total_students_query)
        
        present_count = stats[0]['present_count'] if stats else 0
        total_students = total_data[0]['total_students'] if total_data else 0
        absent_count = total_students - present_count
        attendance_percentage = round((present_count / total_students * 100), 2) if total_students > 0 else 0
        
        # Format last_attendance_time for JSON serialization
        last_attendance_time = None
        if stats and stats[0]['last_attendance_time']:
            last_attendance_time = str(stats[0]['last_attendance_time'])
        
        return jsonify({
            'success': True,
            'stats': {
                'total_students': total_students,
                'present_count': present_count,
                'absent_count': absent_count,
                'attendance_percentage': attendance_percentage,
                'last_attendance_time': last_attendance_time
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        return jsonify({'success': False, 'message': 'Error getting session statistics'}), 500

@app.route('/get_session_attendance/<int:session_id>', methods=['GET'])
@faculty_required
def get_session_attendance(session_id):
    """Get attendance records for a session, ordered by enrollment number"""
    try:
        # Get session details
        session_query = '''
            SELECT * FROM sessions 
            WHERE id = %s AND faculty_id = %s
        '''
        session_data = db.execute_query(session_query, (session_id, session.get('user_id')))
        
        if not session_data:
            return jsonify({'success': False, 'message': 'Session not found'}), 404
        
        # Get attendance records ordered by enrollment number (ascending)
        attendance_query = '''
            SELECT 
                u.name as student_name,
                u.enrollment_no,
                a.attendance_time,
                CASE 
                    WHEN a.marked_by_face = 1 THEN 'Face Recognition'
                    WHEN a.marked_by_rfid = 1 THEN 'RFID'
                    ELSE 'Manual'
                END as method,
                'Present' as status
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE a.faculty_id = %s 
            AND a.subject = %s 
            AND a.session_type = %s
            AND a.attendance_date = CURDATE()
            ORDER BY u.enrollment_no ASC
        '''
        
        attendance_records = db.execute_query(attendance_query, (
            session.get('user_id'),
            session_data[0]['subject'],
            session_data[0]['session_type']
        ))
        
        # Convert timedelta objects to string format for JSON serialization
        if attendance_records:
            for record in attendance_records:
                if record.get('attendance_time'):
                    record['attendance_time'] = str(record['attendance_time'])
        
        return jsonify({
            'success': True,
            'attendance_records': attendance_records or []
        })
        
    except Exception as e:
        logger.error(f"Error getting session attendance: {e}")
        return jsonify({'success': False, 'message': 'Error getting attendance records'}), 500

@app.route('/end_attendance_session/<int:session_id>', methods=['POST'])
@faculty_required
def end_attendance_session(session_id):
    """End an attendance session"""
    try:
        # Update session with end time
        update_query = '''
            UPDATE sessions 
            SET end_time = CURTIME()
            WHERE id = %s AND faculty_id = %s
        '''
        result = db.execute_query(update_query, (session_id, session.get('user_id')))
        
        if result:
            # Get session details for the event
            session_query = "SELECT subject, session_type FROM sessions WHERE id = %s"
            session_info = db.execute_query(session_query, (session_id,))
            
            if session_info:
                # Emit Socket.IO event for real-time analytics update
                socketio.emit('session_ended', {
                    'session_id': session_id,
                    'subject': session_info[0].get('subject'),
                    'session_type': session_info[0].get('session_type'),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return jsonify({
                'success': True,
                'message': 'Session ended successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to end session'
            }), 400
            
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        return jsonify({'success': False, 'message': 'Error ending session'}), 500

@app.route('/students')
@admin_required
def students():
    """Student management page"""
    try:
        query = '''
            SELECT u.*, 
                   COALESCE(att_stats.total_classes, 0) as total_classes,
                   COALESCE(att_stats.attended_classes, 0) as attended_classes,
                   CASE 
                       WHEN COALESCE(att_stats.total_classes, 0) > 0 
                       THEN ROUND((COALESCE(att_stats.attended_classes, 0) / att_stats.total_classes) * 100, 2)
                       ELSE 0 
                   END as attendance_percentage
            FROM users u
            LEFT JOIN (
                SELECT user_id,
                       COUNT(*) as total_classes,
                       SUM(CASE WHEN status = 'P' THEN 1 ELSE 0 END) as attended_classes
                FROM attendance
                GROUP BY user_id
            ) att_stats ON u.id = att_stats.user_id
            WHERE u.role = 'student'
            ORDER BY u.enrollment_no
        '''
        students_data = db.execute_query(query)
        return render_template('admin/students.html', students=students_data)
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
        logger.error(traceback.format_exc())
        flash('Error fetching students', 'error')
        return redirect(url_for('dashboard'))

@app.route('/add_student', methods=['POST'])
@admin_required
def add_student():
    """Add new student or faculty member"""
    try:
        name = request.form['name']
        enrollment_no = request.form['enrollment_no']
        mobile_number = request.form['mobile_number']
        role = request.form.get('role', 'student')  # Get role from form, default to student
        
        # Validate role
        if role not in ['student', 'faculty']:
            flash(f'Invalid role: {role}', 'error')
            return redirect(url_for('dashboard'))

        success, message = auth_manager.register_user(name, enrollment_no, mobile_number, role)

        if success:
            user_type = 'Faculty' if role == 'faculty' else 'Student'
            flash(f'{user_type} added successfully', 'success')
        else:
            user_type = 'faculty' if role == 'faculty' else 'student'
            flash(f'Failed to add {user_type}: {message}', 'error')

    except Exception as e:
        logger.error(f"Error adding user: {e}")
        logger.error(traceback.format_exc())
        flash('Error adding user', 'error')

    return redirect(url_for('dashboard'))

@app.route('/api/analytics/dashboard')
@login_required
def api_analytics_dashboard():
    """API endpoint for real-time analytics dashboard data"""
    try:
        time_filter = request.args.get('filter', 'today')
        user_role = session.get('role')
        user_id = session.get('user_id')
        
        # Date filtering based on filter parameter
        date_condition = "DATE(a.timestamp) = CURRENT_DATE"
        if time_filter == 'week':
            date_condition = "a.timestamp >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)"
        elif time_filter == 'month':
            date_condition = "a.timestamp >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)"
        elif time_filter == 'semester':
            date_condition = "1=1"  # All data
        
        # 1. Overall Statistics
        stats_query = f'''
            SELECT 
                COUNT(DISTINCT u.user_id) as total_students,
                COUNT(DISTINCT DATE(a.timestamp)) as total_sessions,
                ROUND(AVG(CASE WHEN a.status = 'P' THEN 100 ELSE 0 END), 2) as avg_attendance,
                COUNT(DISTINCT CASE WHEN att_pct.percentage < 75 THEN u.user_id END) as low_attendance_count
            FROM users u
            LEFT JOIN attendance a ON u.user_id = a.user_id AND {date_condition}
            LEFT JOIN (
                SELECT user_id, 
                       ROUND(AVG(CASE WHEN status = 'P' THEN 100 ELSE 0 END), 2) as percentage
                FROM attendance
                GROUP BY user_id
            ) att_pct ON u.user_id = att_pct.user_id
            WHERE u.role = 'student'
        '''
        
        stats_result = db.execute_query(stats_query)
        stats = stats_result[0] if stats_result else {
            'total_students': 0,
            'total_sessions': 0,
            'avg_attendance': 0,
            'low_attendance_count': 0
        }
        
        # 2. Attendance Trend (Last 7 days)
        trend_query = f'''
            SELECT 
                DATE(a.timestamp) as date,
                ROUND(AVG(CASE WHEN a.status = 'P' THEN 100 ELSE 0 END), 2) as attendance_percentage
            FROM attendance a
            WHERE {date_condition}
            GROUP BY DATE(a.timestamp)
            ORDER BY DATE(a.timestamp) ASC
            LIMIT 10
        '''
        
        trend_result = db.execute_query(trend_query)
        trend_labels = []
        trend_data = []
        
        if trend_result:
            for row in trend_result:
                date_str = row['date'].strftime('%b %d') if isinstance(row['date'], datetime) else str(row['date'])
                trend_labels.append(date_str)
                trend_data.append(float(row['attendance_percentage']) if row['attendance_percentage'] else 0)
        
        # 3. Subject-wise Distribution
        subject_query = f'''
            SELECT 
                c.course_name as subject,
                COUNT(DISTINCT a.user_id) as student_count,
                ROUND(AVG(CASE WHEN a.status = 'P' THEN 100 ELSE 0 END), 2) as attendance_percentage
            FROM attendance a
            LEFT JOIN courses c ON a.subject = c.course_name
            WHERE {date_condition}
            GROUP BY c.course_name
            ORDER BY attendance_percentage DESC
            LIMIT 5
        '''
        
        subject_result = db.execute_query(subject_query)
        subject_labels = []
        subject_data = []
        
        if subject_result:
            for row in subject_result:
                subject_labels.append(row['subject'] if row['subject'] else 'Unknown')
                subject_data.append(float(row['attendance_percentage']) if row['attendance_percentage'] else 0)
        
        # 4. Time-wise Attendance
        time_query = f'''
            SELECT 
                HOUR(a.timestamp) as hour,
                ROUND(AVG(CASE WHEN a.status = 'P' THEN 100 ELSE 0 END), 2) as attendance_percentage
            FROM attendance a
            WHERE {date_condition}
            GROUP BY HOUR(a.timestamp)
            ORDER BY hour ASC
        '''
        
        time_result = db.execute_query(time_query)
        time_labels = []
        time_data = []
        
        if time_result:
            for row in time_result:
                hour = int(row['hour']) if row['hour'] else 0
                time_label = f"{hour:02d}:00"
                time_labels.append(time_label)
                time_data.append(float(row['attendance_percentage']) if row['attendance_percentage'] else 0)
        
        # 5. Department-wise (if department table exists)
        department_labels = ['CSE', 'IT', 'ECE', 'MECH']
        department_data = [85, 78, 82, 75]  # Mock data for now
        
        # 6. Recent Activity
        activity_query = f'''
            SELECT 
                u.name as student_name,
                a.subject,
                a.timestamp,
                a.status
            FROM attendance a
            JOIN users u ON a.user_id = u.user_id
            WHERE {date_condition}
            ORDER BY a.timestamp DESC
            LIMIT 10
        '''
        
        activity_result = db.execute_query(activity_query)
        recent_activity = []
        
        if activity_result:
            for row in activity_result:
                timestamp = row['timestamp']
                if isinstance(timestamp, datetime):
                    time_str = timestamp.strftime('%I:%M %p')
                else:
                    time_str = str(timestamp)
                
                recent_activity.append({
                    'student': row['student_name'],
                    'subject': row['subject'] if row['subject'] else 'General',
                    'time': time_str,
                    'status': row['status']
                })
        
        # Prepare response
        response_data = {
            'stats': {
                'total_students': int(stats['total_students']) if stats['total_students'] else 0,
                'avg_attendance': float(stats['avg_attendance']) if stats['avg_attendance'] else 0,
                'total_sessions': int(stats['total_sessions']) if stats['total_sessions'] else 0,
                'low_attendance_count': int(stats['low_attendance_count']) if stats['low_attendance_count'] else 0
            },
            'charts': {
                'attendance_trend': {
                    'labels': trend_labels,
                    'data': trend_data
                },
                'subject_data': {
                    'labels': subject_labels,
                    'data': subject_data
                },
                'time_data': {
                    'labels': time_labels,
                    'data': time_data
                },
                'department_data': {
                    'labels': department_labels,
                    'data': department_data
                }
            },
            'recent_activity': recent_activity,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in analytics dashboard API: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'stats': {'total_students': 0, 'avg_attendance': 0, 'total_sessions': 0, 'low_attendance_count': 0},
            'charts': {
                'attendance_trend': {'labels': [], 'data': []},
                'subject_data': {'labels': [], 'data': []},
                'time_data': {'labels': [], 'data': []},
                'department_data': {'labels': [], 'data': []}
            },
            'recent_activity': []
        }), 500

@app.route('/analytics')
@login_required
def analytics_page():
    """Analytics page"""
    user_role = session.get('role')
    user_id = session.get('user_id')

    if user_role == 'student':
        weekly_data = analytics.get_weekly_attendance_data(user_id)
        monthly_data = analytics.get_monthly_attendance_data(user_id)
        subject_data = analytics.get_subject_wise_attendance(user_id)

        weekly_chart = analytics.create_attendance_chart(weekly_data, 'weekly')
        monthly_chart = analytics.create_attendance_chart(monthly_data, 'monthly')
        subject_chart = analytics.create_attendance_chart(subject_data, 'subject')

        return render_template('analytics/student_analytics.html',
                             weekly_chart=weekly_chart,
                             monthly_chart=monthly_chart,
                             subject_chart=subject_chart,
                             weekly_data=weekly_data,
                             monthly_data=monthly_data,
                             subject_data=subject_data)

    elif user_role in ['admin', 'faculty']:
        # Use the new real-time analytics dashboard
        return render_template('analytics/real_time_analytics.html')

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

# API Routes
@app.route('/api/student/<int:student_id>')
@admin_required
def get_student_details(student_id):
    """Get student details via API"""
    try:
        student_query = "SELECT * FROM users WHERE id = %s AND role = 'student'"
        student_result = db.execute_query(student_query, (student_id,))
        if not student_result:
            return jsonify({'success': False, 'message': 'Student not found'})
        student = student_result[0]
        attendance_data = analytics.calculate_attendance_percentage(student_id)
        return jsonify({'success': True, 'student': student, 'attendance_data': attendance_data})
    except Exception as e:
        logger.error(f"Error getting student details: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': 'Error retrieving student details'})

@app.route('/api/student/<int:student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    """Delete student via API"""
    try:
        delete_query = "DELETE FROM users WHERE id = %s AND role = 'student'"
        result = db.execute_query(delete_query, (student_id,))
        if result:
            return jsonify({'success': True, 'message': 'Student deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete student'})
    except Exception as e:
        logger.error(f"Error deleting student: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': 'Error deleting student'})

@app.route('/api/students/export')
@admin_required
def export_students():
    """Export students data as CSV"""
    import csv
    import io

    try:
        query = '''
            SELECT u.enrollment_no, u.name, u.mobile_number, u.created_at,
                   COALESCE(att_stats.total_classes, 0) as total_classes,
                   COALESCE(att_stats.attended_classes, 0) as attended_classes,
                   CASE 
                       WHEN COALESCE(att_stats.total_classes, 0) > 0 
                       THEN ROUND((COALESCE(att_stats.attended_classes, 0) / att_stats.total_classes) * 100, 2)
                       ELSE 0 
                   END as attendance_percentage
            FROM users u
            LEFT JOIN (
                SELECT user_id,
                       COUNT(*) as total_classes,
                       SUM(CASE WHEN status = 'P' THEN 1 ELSE 0 END) as attended_classes
                FROM attendance
                GROUP BY user_id
            ) att_stats ON u.id = att_stats.user_id
            WHERE u.role = 'student'
            ORDER BY u.enrollment_no
        '''
        students = db.execute_query(query)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Enrollment No', 'Name', 'Mobile', 'Joined Date', 'Total Classes', 'Attended', 'Attendance %'])
        for student in students:
            writer.writerow([
                student.get('enrollment_no'),
                student.get('name'),
                student.get('mobile_number'),
                student.get('created_at'),
                student.get('total_classes'),
                student.get('attended_classes'),
                student.get('attendance_percentage')
            ])
        output.seek(0)
        return Response(output.getvalue(), mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=students_export.csv'})
    except Exception as e:
        logger.error(f"Error exporting students: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': 'Error exporting data'})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error.html', error_code=403, error_message="Access forbidden"), 403

if __name__ == '__main__':
    try:
        # Initialize database
        if db.connect():
            db.create_tables()
            db.insert_sample_data()
            logger.info("Database initialized successfully")
        else:
            logger.error("Failed to initialize database")
            sys.exit(1)
        
        logger.info("Starting SecureAttend Pro with QR-based attendance system...")
        
        # Start the SocketIO server
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=5000, 
                    debug=True,
                    allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
