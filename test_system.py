#!/usr/bin/env python3
"""
Quick Test Script for SecureAttend Pro
Tests all major components before running the server
"""

import sys
import os
import traceback
from datetime import datetime

def test_component(component_name, test_func):
    """Test a component and return result"""
    try:
        print(f"Testing {component_name}...", end=" ")
        result = test_func()
        if result:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_imports():
    """Test all critical imports"""
    try:
        from flask import Flask
        from database.database import db
        from auth.authentication import auth_manager
        from face_processing.face_processor import face_processor
        from utils.otp_service import otp_service
        from enhanced_registration import enhanced_registration
        return True
    except ImportError as e:
        print(f"\nImport error: {e}")
        return False

def test_database():
    """Test database connection"""
    try:
        from database.database import db
        result = db.connect()
        return result if result else False
    except Exception as e:
        print(f"\nDatabase error: {e}")
        return False

def test_flask_app():
    """Test Flask app creation"""
    try:
        from app import app
        return app is not None
    except Exception:
        return False

def test_templates():
    """Test template files exist"""
    required_templates = [
        'base.html',
        'index.html', 
        'login.html',
        'register.html',
        'enhanced_registration.html'
    ]
    
    templates_dir = 'templates'
    if not os.path.exists(templates_dir):
        return False
    
    for template in required_templates:
        template_path = os.path.join(templates_dir, template)
        if not os.path.exists(template_path):
            print(f"\nMissing template: {template}")
            return False
    
    return True

def test_static_files():
    """Test static directory structure"""
    required_dirs = [
        'static',
        'static/face_images',
        'static/uploads'
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception:
                return False
    
    return True

def main():
    print("="*50)
    print("  SecureAttend Pro - System Test")
    print("="*50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    print(f"Working directory: {project_dir}")
    print()
    
    tests = [
        ("Python Imports", test_imports),
        ("Database Connection", test_database),
        ("Flask Application", test_flask_app),
        ("Template Files", test_templates),
        ("Static Directories", test_static_files),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_component(test_name, test_func):
            passed += 1
    
    print()
    print("="*50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to run.")
        print()
        print("To start the server, run:")
        print("  python run.py")
        print("  or")
        print("  start_server.bat")
        print()
        print("Application will be available at: http://localhost:5000")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        print("\nTroubleshooting:")
        print("1. Ensure MySQL is running")
        print("2. Install missing dependencies: pip install -r requirements.txt")
        print("3. Check database configuration in .env file")
    
    print("="*50)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)