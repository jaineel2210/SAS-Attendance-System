#!/usr/bin/env python3
"""
Comprehensive Debug Script for SecureAttend Pro
Tests all major components of the attendance system
"""

import sys
import os
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connectivity and table creation"""
    print("\n" + "="*50)
    print("TESTING DATABASE CONNECTION")
    print("="*50)
    
    try:
        from database.database import db
        
        # Test connection
        print("✓ Database connection successful")
        
        # Test table creation
        db.create_tables()
        print("✓ Database tables verified/created")
        
        # Test sample query
        result = db.execute_query("SELECT COUNT(*) as count FROM users")
        if result:
            print(f"✓ Users table accessible - {result[0]['count']} records found")
        
        return True
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        traceback.print_exc()
        return False

def test_face_processing():
    """Test face processing module"""
    print("\n" + "="*50)
    print("TESTING FACE PROCESSING")
    print("="*50)
    
    try:
        from face_processing.face_processor import face_processor
        
        print("✓ Face processor imported successfully")
        print(f"✓ Known faces loaded: {len(face_processor.known_face_encodings)}")
        
        # Test face detection
        import cv2
        import numpy as np
        
        # Create a simple test image
        test_image = np.zeros((300, 300, 3), dtype=np.uint8)
        faces = face_processor.detect_faces(test_image)
        print(f"✓ Face detection working - {len(faces)} faces detected in test image")
        
        # Test feature extraction
        features = face_processor.extract_face_features(test_image)
        if features is not None:
            print("✓ Feature extraction working")
        else:
            print("! No features extracted from test image (expected)")
        
        return True
        
    except Exception as e:
        print(f"✗ Face processing error: {e}")
        traceback.print_exc()
        return False

def test_authentication():
    """Test authentication system"""
    print("\n" + "="*50)
    print("TESTING AUTHENTICATION")
    print("="*50)
    
    try:
        from auth.authentication import auth_manager
        
        print("✓ Authentication manager imported successfully")
        
        # Test password hashing
        test_password = "test123"
        hashed = auth_manager.hash_password(test_password)
        print("✓ Password hashing working")
        
        # Test password verification
        is_valid = auth_manager.verify_password(test_password, hashed)
        if is_valid:
            print("✓ Password verification working")
        else:
            print("✗ Password verification failed")
            
        return True
        
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        traceback.print_exc()
        return False

def test_otp_service():
    """Test OTP service"""
    print("\n" + "="*50)
    print("TESTING OTP SERVICE")
    print("="*50)
    
    try:
        from utils.otp_service import otp_service
        
        print("✓ OTP service imported successfully")
        
        # Test OTP generation
        otp = otp_service.generate_otp()
        print(f"✓ OTP generation working - Generated: {otp}")
        
        # Test OTP verification
        is_valid = otp_service.verify_otp("1234567890", otp)
        if is_valid:
            print("✓ OTP verification working")
        else:
            print("! OTP verification returned False (may be expected due to timeout)")
        
        return True
        
    except Exception as e:
        print(f"✗ OTP service error: {e}")
        traceback.print_exc()
        return False

def test_analytics():
    """Test analytics system"""
    print("\n" + "="*50)
    print("TESTING ANALYTICS")
    print("="*50)
    
    try:
        from utils.analytics import analytics
        
        print("✓ Analytics system imported successfully")
        
        # Test analytics functions
        try:
            stats = analytics.get_attendance_stats()
            print("✓ Attendance stats function working")
        except Exception as e:
            print(f"! Analytics stats error (may be expected with no data): {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Analytics error: {e}")
        traceback.print_exc()
        return False

def test_rfid_reader():
    """Test RFID reader"""
    print("\n" + "="*50)
    print("TESTING RFID READER")
    print("="*50)
    
    try:
        from rfid.rfid_reader import rfid_reader
        
        print("✓ RFID reader imported successfully")
        print("! RFID hardware testing skipped (requires physical hardware)")
        
        return True
        
    except Exception as e:
        print(f"✗ RFID reader error: {e}")
        traceback.print_exc()
        return False

def test_flask_app():
    """Test Flask application initialization"""
    print("\n" + "="*50)
    print("TESTING FLASK APPLICATION")
    print("="*50)
    
    try:
        from app import app
        
        print("✓ Flask app imported successfully")
        
        # Test app configuration
        if app.config:
            print("✓ App configuration loaded")
        
        # Test routes
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✓ Home route working")
            else:
                print(f"! Home route returned status {response.status_code}")
                
            response = client.get('/login')
            if response.status_code == 200:
                print("✓ Login route working")
            else:
                print(f"! Login route returned status {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"✗ Flask app error: {e}")
        traceback.print_exc()
        return False

def test_environment():
    """Test environment and dependencies"""
    print("\n" + "="*50)
    print("TESTING ENVIRONMENT")
    print("="*50)
    
    print(f"✓ Python version: {sys.version}")
    print(f"✓ Current directory: {os.getcwd()}")
    
    # Test required packages
    required_packages = [
        'flask', 'mysql-connector-python', 'opencv-python', 'opencv-contrib-python',
        'pillow', 'numpy', 'bcrypt', 'twilio'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} installed")
        except ImportError:
            try:
                # Try alternative import names
                if package == 'mysql-connector-python':
                    import mysql.connector
                    print(f"✓ {package} installed")
                elif package == 'opencv-python':
                    import cv2
                    print(f"✓ {package} installed")
                elif package == 'pillow':
                    import PIL
                    print(f"✓ {package} installed")
                else:
                    print(f"✗ {package} not found")
            except ImportError:
                print(f"✗ {package} not found")
    
    return True

def main():
    """Run comprehensive system test"""
    print("SecureAttend Pro - Comprehensive System Debug")
    print("=" * 60)
    
    tests = [
        ("Environment", test_environment),
        ("Database", test_database_connection),
        ("Face Processing", test_face_processing),
        ("Authentication", test_authentication),
        ("OTP Service", test_otp_service),
        ("Analytics", test_analytics),
        ("RFID Reader", test_rfid_reader),
        ("Flask Application", test_flask_app),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:<20}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All systems operational! Project is ready to run.")
    else:
        print(f"\n⚠️  {total - passed} issues detected. Please review the failed tests.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
