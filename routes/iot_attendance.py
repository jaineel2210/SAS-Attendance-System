"""
Enhanced Faculty Dashboard for IoT Attendance System
===================================================

This module provides an enhanced faculty interface for managing IoT-based
automatic attendance sessions with real-time monitoring and control.

Features:
- Start/stop IoT scanning sessions
- Real-time attendance monitoring
- Device management and status
- Session analytics and reports
- Location-based session management

Author: SecureAttend Pro Team
Date: September 2025
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.database import db
from auth.authentication import auth_manager
import json
import logging
from datetime import datetime, timedelta
import requests
import os
from functools import wraps

logger = logging.getLogger(__name__)

# Define faculty_required decorator locally since it's not exported from auth
def faculty_required(f):
    """Decorator to require faculty role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'faculty':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

logger = logging.getLogger(__name__)

# Create blueprint for IoT attendance routes
iot_routes = Blueprint('iot_routes', __name__)

class IoTAttendanceManager:
    def __init__(self):
        self.active_sessions = {}
        self.registered_devices = {}
        self.load_device_registry()

    def load_device_registry(self):
        """Load registered IoT devices"""
        try:
            registry_file = "iot_attendance/device_registry.json"
            if os.path.exists(registry_file):
                with open(registry_file, 'r') as f:
                    self.registered_devices = json.load(f)
            else:
                self.registered_devices = {}
        except Exception as e:
            logger.error(f"Error loading device registry: {e}")
            self.registered_devices = {}

    def get_available_devices(self):
        """Get list of available IoT devices"""
        available_devices = []
        for device_id, device_info in self.registered_devices.items():
            # Check device status (you can implement actual status checking)
            device_info['status'] = 'online'  # Simplified for now
            available_devices.append(device_info)
        return available_devices

    def start_iot_session(self, session_data, device_id):
        """Start IoT attendance session on specified device"""
        try:
            if device_id not in self.registered_devices:
                return False, "Device not found"

            device_info = self.registered_devices[device_id]
            device_url = f"http://{device_info.get('ip_address', 'localhost')}:{device_info.get('port', 5001)}"

            # Send start session command to device
            response = requests.post(
                f"{device_url}/device/start_session",
                json=session_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Store active session
                    session_id = session_data.get('session_id')
                    self.active_sessions[session_id] = {
                        'device_id': device_id,
                        'session_data': session_data,
                        'start_time': datetime.now().isoformat(),
                        'status': 'active'
                    }
                    return True, "Session started successfully"

            return False, "Failed to start session on device"

        except Exception as e:
            logger.error(f"Error starting IoT session: {e}")
            return False, str(e)

    def stop_iot_session(self, session_id):
        """Stop IoT attendance session"""
        try:
            if session_id not in self.active_sessions:
                return False, "Session not found"

            session_info = self.active_sessions[session_id]
            device_id = session_info['device_id']
            device_info = self.registered_devices.get(device_id)

            if not device_info:
                return False, "Device not found"

            device_url = f"http://{device_info.get('ip_address', 'localhost')}:{device_info.get('port', 5001)}"

            # Send stop session command to device
            response = requests.post(
                f"{device_url}/device/stop_session",
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Update session status
                    self.active_sessions[session_id]['status'] = 'stopped'
                    self.active_sessions[session_id]['end_time'] = datetime.now().isoformat()
                    return True, "Session stopped successfully"

            return False, "Failed to stop session on device"

        except Exception as e:
            logger.error(f"Error stopping IoT session: {e}")
            return False, str(e)

    def get_session_stats(self, session_id):
        """Get real-time session statistics from IoT device"""
        try:
            if session_id not in self.active_sessions:
                return None

            session_info = self.active_sessions[session_id]
            device_id = session_info['device_id']
            device_info = self.registered_devices.get(device_id)

            if not device_info:
                return None

            device_url = f"http://{device_info.get('ip_address', 'localhost')}:{device_info.get('port', 5001)}"

            # Get session stats from device
            response = requests.get(
                f"{device_url}/device/session_stats",
                timeout=5
            )

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return None

# Initialize IoT manager
iot_manager = IoTAttendanceManager()

@iot_routes.route('/iot_dashboard')
@faculty_required
def iot_dashboard():
    """IoT Attendance Dashboard for Faculty"""
    try:
        faculty_id = session.get('user_id')
        
        # Get faculty information
        faculty_query = "SELECT name, department FROM users WHERE id = %s"
        faculty_info = db.execute_query(faculty_query, (faculty_id,))
        
        if not faculty_info:
            return redirect(url_for('auth.login'))
        
        faculty = faculty_info[0]
        
        # Get available IoT devices
        devices = iot_manager.get_available_devices()
        
        # Get active sessions for this faculty
        active_sessions_query = """
            SELECT id, subject, session_type, location, start_time, is_active
            FROM attendance_sessions 
            WHERE faculty_id = %s AND is_active = TRUE
            ORDER BY start_time DESC
        """
        active_sessions = db.execute_query(active_sessions_query, (faculty_id,)) or []
        
        # Get recent sessions
        recent_sessions_query = """
            SELECT id, subject, session_type, location, start_time, end_time, 
                   (SELECT COUNT(*) FROM attendance WHERE session_id = attendance_sessions.id) as attendance_count
            FROM attendance_sessions 
            WHERE faculty_id = %s 
            ORDER BY start_time DESC 
            LIMIT 10
        """
        recent_sessions = db.execute_query(recent_sessions_query, (faculty_id,)) or []
        
        return render_template('iot_attendance/iot_dashboard.html',
                             faculty=faculty,
                             devices=devices,
                             active_sessions=active_sessions,
                             recent_sessions=recent_sessions)
        
    except Exception as e:
        logger.error(f"Error in IoT dashboard: {e}")
        return render_template('error.html', error="Failed to load IoT dashboard")

@iot_routes.route('/start_iot_session', methods=['POST'])
@faculty_required
def start_iot_session():
    """Start IoT attendance session"""
    try:
        data = request.get_json() or request.form.to_dict()
        faculty_id = session.get('user_id')
        
        # Validate required fields
        required_fields = ['subject', 'session_type', 'location', 'device_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'})
        
        # Create session in database
        create_session_query = """
            INSERT INTO attendance_sessions 
            (faculty_id, subject, session_type, location, start_time, is_active, session_mode)
            VALUES (%s, %s, %s, %s, NOW(), TRUE, 'iot_automatic')
        """
        session_id = db.execute_query(create_session_query, (
            faculty_id,
            data['subject'],
            data['session_type'],
            data['location']
        ), fetch_last_id=True)
        
        if not session_id:
            return jsonify({'success': False, 'message': 'Failed to create session'})
        
        # Prepare session data for IoT device
        session_data = {
            'session_id': session_id,
            'faculty_id': faculty_id,
            'subject': data['subject'],
            'session_type': data['session_type'],
            'location': data['location'],
            'expected_duration': data.get('expected_duration', 60),  # minutes
            'auto_mark_threshold': data.get('auto_mark_threshold', 0.7),
            'start_time': datetime.now().isoformat()
        }
        
        # Start session on IoT device
        success, message = iot_manager.start_iot_session(session_data, data['device_id'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'IoT session started successfully',
                'session_id': session_id
            })
        else:
            # Clean up database session if IoT start failed
            cleanup_query = "DELETE FROM attendance_sessions WHERE id = %s"
            db.execute_query(cleanup_query, (session_id,))
            
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        logger.error(f"Error starting IoT session: {e}")
        return jsonify({'success': False, 'message': 'Failed to start IoT session'})

@iot_routes.route('/stop_iot_session', methods=['POST'])
@faculty_required
def stop_iot_session():
    """Stop IoT attendance session"""
    try:
        data = request.get_json() or request.form.to_dict()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'message': 'Session ID required'})
        
        # Stop session on IoT device
        success, message = iot_manager.stop_iot_session(session_id)
        
        if success:
            # Update session in database
            update_query = """
                UPDATE attendance_sessions 
                SET is_active = FALSE, end_time = NOW() 
                WHERE id = %s
            """
            db.execute_query(update_query, (session_id,))
            
            return jsonify({
                'success': True,
                'message': 'IoT session stopped successfully'
            })
        else:
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        logger.error(f"Error stopping IoT session: {e}")
        return jsonify({'success': False, 'message': 'Failed to stop IoT session'})

@iot_routes.route('/iot_session_stats/<int:session_id>')
@faculty_required
def iot_session_stats(session_id):
    """Get real-time IoT session statistics"""
    try:
        # Get stats from IoT device
        device_stats = iot_manager.get_session_stats(session_id)
        
        # Get database stats
        db_stats_query = """
            SELECT 
                COUNT(*) as total_attendance,
                COUNT(DISTINCT user_id) as unique_students,
                MIN(attendance_time) as first_detection,
                MAX(attendance_time) as last_detection
            FROM attendance 
            WHERE session_id = %s
        """
        db_stats = db.execute_query(db_stats_query, (session_id,))
        
        # Get recent detections
        recent_detections_query = """
            SELECT u.name, u.enrollment_no, a.attendance_time
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE a.session_id = %s
            ORDER BY a.attendance_time DESC
            LIMIT 10
        """
        recent_detections = db.execute_query(recent_detections_query, (session_id,)) or []
        
        # Combine stats
        combined_stats = {
            'session_id': session_id,
            'device_stats': device_stats,
            'database_stats': db_stats[0] if db_stats else {},
            'recent_detections': recent_detections,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(combined_stats)
        
    except Exception as e:
        logger.error(f"Error getting IoT session stats: {e}")
        return jsonify({'error': 'Failed to get session statistics'})

@iot_routes.route('/iot_session_attendance/<int:session_id>')
@faculty_required
def iot_session_attendance(session_id):
    """Get detailed attendance list for IoT session"""
    try:
        attendance_query = """
            SELECT 
                u.name,
                u.enrollment_no,
                u.department,
                a.attendance_time,
                a.marked_by_iot,
                a.location
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE a.session_id = %s
            ORDER BY a.attendance_time DESC
        """
        attendance_records = db.execute_query(attendance_query, (session_id,)) or []
        
        return jsonify({
            'session_id': session_id,
            'attendance_records': attendance_records,
            'total_count': len(attendance_records)
        })
        
    except Exception as e:
        logger.error(f"Error getting IoT session attendance: {e}")
        return jsonify({'error': 'Failed to get attendance records'})

@iot_routes.route('/device_status')
@faculty_required
def device_status():
    """Get status of all IoT devices"""
    try:
        devices = iot_manager.get_available_devices()
        
        # Check actual device status
        for device in devices:
            try:
                device_url = f"http://{device.get('ip_address', 'localhost')}:{device.get('port', 5001)}"
                response = requests.get(f"{device_url}/device/status", timeout=5)
                
                if response.status_code == 200:
                    device_status = response.json()
                    device.update(device_status)
                else:
                    device['status'] = 'offline'
                    
            except:
                device['status'] = 'offline'
        
        return jsonify(devices)
        
    except Exception as e:
        logger.error(f"Error getting device status: {e}")
        return jsonify({'error': 'Failed to get device status'})

@iot_routes.route('/configure_device', methods=['POST'])
@faculty_required
def configure_device():
    """Configure IoT device settings"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        config = data.get('configuration')
        
        if not device_id or not config:
            return jsonify({'success': False, 'message': 'Device ID and configuration required'})
        
        device_info = iot_manager.registered_devices.get(device_id)
        if not device_info:
            return jsonify({'success': False, 'message': 'Device not found'})
        
        device_url = f"http://{device_info.get('ip_address', 'localhost')}:{device_info.get('port', 5001)}"
        
        # Send configuration to device
        response = requests.post(
            f"{device_url}/device/configure",
            json=config,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify(result)
        else:
            return jsonify({'success': False, 'message': 'Failed to configure device'})
            
    except Exception as e:
        logger.error(f"Error configuring device: {e}")
        return jsonify({'success': False, 'message': 'Configuration failed'})

# API Routes for IoT devices to communicate with main system

@iot_routes.route('/api/device/register', methods=['POST'])
def register_device():
    """Register a new IoT device"""
    try:
        device_info = request.get_json()
        
        if not device_info or not device_info.get('device_id'):
            return jsonify({'success': False, 'message': 'Invalid device information'})
        
        # Add device to registry
        device_id = device_info['device_id']
        iot_manager.registered_devices[device_id] = {
            **device_info,
            'registered_at': datetime.now().isoformat(),
            'ip_address': request.remote_addr,
            'status': 'registered'
        }
        
        # Save registry
        registry_file = "iot_attendance/device_registry.json"
        os.makedirs(os.path.dirname(registry_file), exist_ok=True)
        with open(registry_file, 'w') as f:
            json.dump(iot_manager.registered_devices, f, indent=2)
        
        logger.info(f"IoT device registered: {device_id}")
        
        return jsonify({'success': True, 'message': 'Device registered successfully'})
        
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        return jsonify({'success': False, 'message': 'Registration failed'})

@iot_routes.route('/api/device/heartbeat', methods=['POST'])
def device_heartbeat():
    """Receive heartbeat from IoT devices"""
    try:
        heartbeat_data = request.get_json()
        device_id = heartbeat_data.get('device_id')
        
        if device_id and device_id in iot_manager.registered_devices:
            # Update device status
            iot_manager.registered_devices[device_id].update({
                'last_heartbeat': datetime.now().isoformat(),
                'status': 'online',
                **heartbeat_data
            })
            
            return jsonify({'success': True, 'message': 'Heartbeat received'})
        
        return jsonify({'success': False, 'message': 'Device not registered'})
        
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        return jsonify({'success': False, 'message': 'Heartbeat failed'})

@iot_routes.route('/api/device/attendance', methods=['POST'])
def receive_attendance():
    """Receive attendance data from IoT devices"""
    try:
        attendance_data = request.get_json()
        
        # Validate attendance data
        required_fields = ['device_id', 'session_id', 'student_id', 'detection_time']
        for field in required_fields:
            if field not in attendance_data:
                return jsonify({'success': False, 'message': f'Missing field: {field}'})
        
        # Insert attendance record
        insert_query = """
            INSERT INTO attendance 
            (user_id, session_id, attendance_date, attendance_time, 
             marked_by_face, marked_by_iot, location, confidence_score)
            VALUES (%s, %s, %s, %s, TRUE, TRUE, %s, %s)
        """
        
        detection_time = datetime.fromisoformat(attendance_data['detection_time'])
        
        result = db.execute_query(insert_query, (
            attendance_data['student_id'],
            attendance_data['session_id'],
            detection_time.date(),
            detection_time.time(),
            attendance_data.get('location', 'IoT Device'),
            attendance_data.get('confidence', 0.85)
        ))
        
        if result:
            logger.info(f"IoT attendance recorded: Student {attendance_data['student_id']}, Session {attendance_data['session_id']}")
            return jsonify({'success': True, 'message': 'Attendance recorded'})
        else:
            return jsonify({'success': False, 'message': 'Failed to record attendance'})
            
    except Exception as e:
        logger.error(f"Error receiving attendance: {e}")
        return jsonify({'success': False, 'message': 'Attendance recording failed'})
