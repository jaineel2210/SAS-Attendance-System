"""
Enhanced Registration System for all user roles
Provides signup functionality for Admin, Faculty, and Students
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database.database import db
from auth.authentication import auth_manager
from utils.otp_service import otp_service
import logging

logger = logging.getLogger(__name__)

# Create blueprint for enhanced registration
enhanced_registration = Blueprint('enhanced_registration', __name__)

@enhanced_registration.route('/register')
def register_home():
    """Registration home page - choose role"""
    return render_template('registration_home.html')

@enhanced_registration.route('/register/<role>')
def register_role(role):
    """Multi-role registration page"""
    if role not in ['admin', 'faculty', 'student']:
        flash('Invalid role selected', 'error')
        return redirect(url_for('enhanced_registration.register_home'))
    
    return render_template('enhanced_registration.html', role=role, step=1)

@enhanced_registration.route('/register/<role>', methods=['POST'])
def handle_registration(role):
    """Handle registration for different roles"""
    if role not in ['admin', 'faculty', 'student']:
        flash('Invalid role selected', 'error')
        return redirect(url_for('index'))
    
    step = request.form.get('step', '1')
    
    if step == '1':
        return handle_step1(role)
    elif step == '2':
        return handle_step2(role)
    elif step == '3':
        return handle_step3(role)
    
    return render_template('enhanced_registration.html', role=role, step=1)

def handle_step1(role):
    """Handle step 1: Basic information collection"""
    try:
        # Common fields
        name = request.form['name']
        mobile_number = request.form['mobile_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validate password match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('enhanced_registration.html', role=role, step=1)
        
        # Validate password strength
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('enhanced_registration.html', role=role, step=1)
        
        # Hash password
        import bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Role-specific fields
        if role == 'student':
            enrollment_no = request.form['enrollment_no']
            identifier = enrollment_no
            additional_data = {'enrollment_no': enrollment_no}
        elif role == 'faculty':
            faculty_id = request.form['faculty_id']
            department = request.form.get('department', '')
            identifier = faculty_id
            additional_data = {
                'faculty_id': faculty_id,
                'department': department
            }
        elif role == 'admin':
            admin_id = request.form['admin_id']
            admin_level = request.form.get('admin_level', 'standard')
            identifier = admin_id
            additional_data = {
                'admin_id': admin_id,
                'admin_level': admin_level
            }
        
        # Check if user already exists
        check_query = '''
            SELECT id FROM users WHERE mobile_number = %s 
            OR (role = %s AND enrollment_no = %s)
        '''
        existing = db.execute_query(check_query, (mobile_number, role, identifier))
        
        if existing:
            flash('User already exists with this information', 'error')
            return render_template('enhanced_registration.html', role=role, step=1)
        
        # Store in session
        session['temp_registration'] = {
            'role': role,
            'name': name,
            'identifier': identifier,
            'mobile_number': mobile_number,
            'password_hash': password_hash,  # Store hashed password
            'additional_data': additional_data
        }
        
        # Send OTP
        success, message = auth_manager.send_otp(mobile_number)
        if success:
            flash('OTP sent to your mobile number', 'info')
            return render_template('enhanced_registration.html', role=role, step=2)
        else:
            flash(f'Failed to send OTP: {message}', 'error')
            return render_template('enhanced_registration.html', role=role, step=1)
            
    except Exception as e:
        logger.error(f"Error in step 1 registration for {role}: {e}")
        flash('Registration error occurred', 'error')
        return render_template('enhanced_registration.html', role=role, step=1)

def handle_step2(role):
    """Handle step 2: OTP verification"""
    try:
        otp_code = request.form['otp_code']
        registration_data = session.get('temp_registration')
        
        if not registration_data:
            flash('Registration session expired', 'error')
            return redirect(url_for('enhanced_registration.register_role', role=role))
        
        success, message = auth_manager.verify_otp(registration_data['mobile_number'], otp_code)
        if success:
            # Create user account
            reg_success, reg_message = create_user_account(registration_data)
            
            if reg_success:
                if role == 'student':
                    # Students need face capture
                    flash('OTP verified. Now capture your face for attendance', 'success')
                    return render_template('enhanced_registration.html', 
                                        role=role, step=3, 
                                        identifier=registration_data['identifier'])
                else:
                    # Admin and Faculty don't need face capture
                    flash('Registration completed successfully!', 'success')
                    session.pop('temp_registration', None)
                    return render_template('enhanced_registration.html', role=role, step=4)
            else:
                flash(f'Registration failed: {reg_message}', 'error')
                return render_template('enhanced_registration.html', role=role, step=2)
        else:
            flash(f'OTP verification failed: {message}', 'error')
            return render_template('enhanced_registration.html', role=role, step=2, resend_otp=True)
            
    except Exception as e:
        logger.error(f"Error in step 2 registration for {role}: {e}")
        flash('OTP verification error occurred', 'error')
        return render_template('enhanced_registration.html', role=role, step=2)

def handle_step3(role):
    """Handle step 3: Face capture (students only)"""
    # This step is handled by JavaScript/AJAX
    # Redirect to completion
    return render_template('enhanced_registration.html', role=role, step=4)

def create_user_account(registration_data):
    """Create user account in database with password"""
    try:
        role = registration_data['role']
        name = registration_data['name']
        identifier = registration_data['identifier']
        mobile_number = registration_data['mobile_number']
        password_hash = registration_data['password_hash']  # Get password hash
        additional_data = registration_data['additional_data']
        
        logger.info(f"Creating account for {role}: {name} with identifier: {identifier}")
        
        # Insert user into database with password
        if role == 'student':
            query = '''
                INSERT INTO users (name, enrollment_no, mobile_number, role, password_hash, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s)
            '''
            values = (name, identifier, mobile_number, role, password_hash, False)  # Students need face verification
        elif role == 'faculty':
            query = '''
                INSERT INTO users (name, faculty_id, mobile_number, role, password_hash, department, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            values = (name, identifier, mobile_number, role, password_hash,
                     additional_data.get('department', ''), True)  # Faculty verified immediately
        elif role == 'admin':
            query = '''
                INSERT INTO users (name, enrollment_no, mobile_number, role, password_hash, admin_level, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            values = (name, identifier, mobile_number, role, password_hash,
                     additional_data.get('admin_level', 'standard'), True)  # Admin verified immediately
        
        logger.info(f"Executing query: {query}")
        logger.info(f"With values: {values}")
        
        result = db.execute_query(query, values)
        
        logger.info(f"Query result: {result}")
        
        if result:
            logger.info(f"Successfully created {role} account: {name}")
            return True, "Account created successfully"
        else:
            logger.error(f"Database query failed - result: {result}")
            return False, "Failed to create account in database"
            
    except Exception as e:
        logger.error(f"Error creating user account: {e}")
        error_message = str(e)
        if "Duplicate entry" in error_message and "enrollment_no" in error_message:
            return False, "This enrollment number is already registered. Please use a different enrollment number or try logging in."
        elif "Duplicate entry" in error_message:
            return False, "This account information is already registered. Please check your details or try logging in."
        else:
            return False, f"Error creating account: {error_message}"

@enhanced_registration.route('/capture_face_enhanced', methods=['POST'])
def capture_face_enhanced():
    """Enhanced face capture endpoint"""
    try:
        data = request.json
        identifier = data['identifier']
        image_data = data['image_data']
        
        # Import here to avoid circular imports
        from face_processing.face_processor import face_processor
        
        success, message = face_processor.store_face_encoding(identifier, image_data)
        
        if success:
            # Mark user as verified
            query = "UPDATE users SET is_verified = TRUE WHERE enrollment_no = %s"
            db.execute_query(query, (identifier,))
            
            # Clear session
            session.pop('temp_registration', None)
            
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        logger.error(f"Error in enhanced face capture: {e}")
        return jsonify({'success': False, 'message': f'Face capture failed: {str(e)}'})

@enhanced_registration.route('/resend_otp/<role>', methods=['POST'])
def resend_otp(role):
    """Resend OTP for registration"""
    try:
        registration_data = session.get('temp_registration')
        if not registration_data:
            return jsonify({'success': False, 'message': 'Registration session expired'})
        
        success, message = auth_manager.send_otp(registration_data['mobile_number'])
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"Error resending OTP: {e}")
        return jsonify({'success': False, 'message': 'Failed to resend OTP'})
