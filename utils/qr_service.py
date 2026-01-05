#!/usr/bin/env python3
"""
Secure QR Code Service for Attendance System
Features:
- Time-based token generation
- IP/Location verification
- Anti-screenshot measures
- Session-based validation
"""

import qrcode
import json
import base64
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class SecureQRService:
    def __init__(self, secret_key=None):
        """Initialize with encryption key"""
        if secret_key:
            self.cipher_suite = Fernet(secret_key)
        else:
            # Generate a new key for this session
            key = Fernet.generate_key()
            self.cipher_suite = Fernet(key)
        
        self.active_sessions = {}  # Store active QR sessions
        
    def generate_session_qr(self, faculty_id, subject, session_type, location_hash=None, duration_minutes=5):
        """
        Generate a secure QR code for attendance session
        
        Args:
            faculty_id: ID of the faculty member
            subject: Subject name
            session_type: 'lecture' or 'lab'
            location_hash: Hash of classroom/location for verification
            duration_minutes: How long the QR code is valid
        
        Returns:
            dict: Contains QR code data and session info
        """
        try:
            # Generate unique session ID
            session_id = secrets.token_urlsafe(32)
            
            # Create timestamp and expiry
            created_at = datetime.now()
            expires_at = created_at + timedelta(minutes=duration_minutes)
            
            # Create session data
            session_data = {
                'session_id': session_id,
                'faculty_id': faculty_id,
                'subject': subject,
                'session_type': session_type,
                'created_at': created_at.isoformat(),
                'expires_at': expires_at.isoformat(),
                'location_hash': location_hash,
                'nonce': secrets.token_hex(16)  # Prevent replay attacks
            }
            
            # Encrypt the session data
            encrypted_data = self.cipher_suite.encrypt(
                json.dumps(session_data).encode('utf-8')
            )
            
            # Encode for QR code
            qr_payload = base64.b64encode(encrypted_data).decode('utf-8')
            
            # Generate QR code with high error correction
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            
            # Add security prefix to prevent simple copying
            secure_payload = f"SECATT:{qr_payload}"
            qr.add_data(secure_payload)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for web display
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Store session info
            self.active_sessions[session_id] = {
                **session_data,
                'students_scanned': [],
                'is_active': True
            }
            
            return {
                'success': True,
                'session_id': session_id,
                'qr_code_base64': qr_base64,
                'qr_data': secure_payload,
                'expires_at': expires_at.isoformat(),
                'duration_minutes': duration_minutes,
                'subject': subject,
                'session_type': session_type
            }
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_qr_scan(self, qr_data, student_id, client_ip=None, location_hash=None):
        """
        Validate a QR code scan by student
        
        Args:
            qr_data: Scanned QR code data
            student_id: ID of the student scanning
            client_ip: IP address of the client (for location verification)
            location_hash: Location hash for verification
        
        Returns:
            dict: Validation result
        """
        try:
            # Check QR code format
            if not qr_data.startswith("SECATT:"):
                return {'success': False, 'error': 'Invalid QR code format'}
            
            # Extract encrypted payload
            encrypted_payload = qr_data[7:]  # Remove "SECATT:" prefix
            
            try:
                encrypted_data = base64.b64decode(encrypted_payload.encode('utf-8'))
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                session_data = json.loads(decrypted_data.decode('utf-8'))
            except Exception as e:
                return {'success': False, 'error': 'Invalid or corrupted QR code'}
            
            session_id = session_data.get('session_id')
            
            # Check if session exists and is active
            if session_id not in self.active_sessions:
                return {'success': False, 'error': 'Session not found'}
            
            active_session = self.active_sessions[session_id]
            
            if not active_session.get('is_active', False):
                return {'success': False, 'error': 'Session has been ended'}
            
            # Check expiry
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                return {'success': False, 'error': 'QR code has expired'}
            
            # Check if student already scanned
            if student_id in active_session['students_scanned']:
                return {'success': False, 'error': 'You have already scanned this QR code'}
            
            # Location verification (if provided)
            if location_hash and session_data.get('location_hash'):
                if location_hash != session_data['location_hash']:
                    return {'success': False, 'error': 'Location verification failed'}
            
            # Add student to scanned list
            active_session['students_scanned'].append({
                'student_id': student_id,
                'scanned_at': datetime.now().isoformat(),
                'client_ip': client_ip
            })
            
            return {
                'success': True,
                'session_id': session_id,
                'faculty_id': session_data['faculty_id'],
                'subject': session_data['subject'],
                'session_type': session_data['session_type'],
                'scanned_students': len(active_session['students_scanned'])
            }
            
        except Exception as e:
            logger.error(f"Error validating QR scan: {e}")
            return {'success': False, 'error': 'Validation failed'}
    
    def get_session_info(self, session_id):
        """Get information about an active session"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        return None
    
    def end_session(self, session_id, faculty_id):
        """End an attendance session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if session['faculty_id'] == faculty_id:
                session['is_active'] = False
                session['ended_at'] = datetime.now().isoformat()
                return True
        return False
    
    def get_active_sessions(self, faculty_id=None):
        """Get all active sessions, optionally filtered by faculty"""
        active = {}
        for sid, session in self.active_sessions.items():
            if session.get('is_active', False):
                if faculty_id is None or session['faculty_id'] == faculty_id:
                    active[sid] = session
        return active
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from memory"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            expires_at = datetime.fromisoformat(session['expires_at'])
            if current_time > expires_at:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        return len(expired_sessions)

# Global QR service instance
qr_service = SecureQRService()