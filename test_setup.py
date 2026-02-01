#!/usr/bin/env python3
"""
Quick test script to verify the application setup
"""

import sys
import os

def test_imports():
    """Test that all critical imports work"""
    print("🔍 Testing imports...")
    
    tests = [
        ("Flask", "flask"),
        ("PyMySQL", "pymysql"),
        ("OpenCV", "cv2"),
        ("NumPy", "numpy"),
        ("QR Code", "qrcode"),
        ("Cryptography", "cryptography"),
        ("Bcrypt", "bcrypt"),
        ("Pandas", "pandas"),
        ("Matplotlib", "matplotlib"),
    ]
    
    failed = []
    for name, module in tests:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: {e}")
            failed.append(name)
    
    # Test face_recognition separately (it's optional)
    try:
        __import__("face_recognition")
        print(f"  ✅ Face Recognition")
    except ImportError:
        print(f"  ⚠️  Face Recognition (optional - app will work without full face recognition features)")
    
    return len(failed) == 0, failed

def test_database():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        from database.database import db
        if db.connect():
            print("  ✅ Database connection successful")
            return True
        else:
            print("  ❌ Database connection failed")
            return False
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_app_import():
    """Test that the app imports correctly"""
    print("\n🔍 Testing app import...")
    
    try:
        from app import app
        print("  ✅ App imported successfully")
        return True
    except Exception as e:
        print(f"  ❌ App import failed: {e}")
        return False

def main():
    print("="*50)
    print("  SecureAttend Pro - System Check")
    print("="*50)
    print()
    
    # Test imports
    imports_ok, failed_imports = test_imports()
    
    # Test database
    db_ok = test_database()
    
    # Test app
    app_ok = test_app_import()
    
    # Summary
    print("\n" + "="*50)
    print("  Summary")
    print("="*50)
    
    if imports_ok and db_ok and app_ok:
        print("✅ All tests passed! Application is ready to run.")
        print("\nStart the server with:")
        print("  python run.py")
        print("  or")
        print("  START_SERVER.bat")
        return 0
    else:
        print("❌ Some tests failed:")
        if not imports_ok:
            print(f"  - Missing packages: {', '.join(failed_imports)}")
        if not db_ok:
            print("  - Database connection failed")
        if not app_ok:
            print("  - App import failed")
        
        print("\nTry:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
