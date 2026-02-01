#!/usr/bin/env python3
"""
Comprehensive module testing script
Tests all project modules for import errors and runtime issues
"""

import sys
import traceback

def test_module(module_name, display_name):
    """Test a single module import"""
    try:
        __import__(module_name)
        print(f"[OK] {display_name}")
        return True
    except Exception as e:
        print(f"[ERROR] {display_name}: {str(e)[:100]}")
        return False

def main():
    print("="*60)
    print("  Comprehensive Module Test")
    print("="*60)
    print()
    
    modules_to_test = [
        ('config', 'Config'),
        ('database.database', 'Database Core'),
        ('auth.authentication', 'Authentication'),
        ('enhanced_registration', 'Registration Blueprint'),
        ('face_processing.face_processor', 'Face Processing'),
        ('rfid.rfid_reader', 'RFID Reader'),
        ('utils.otp_service', 'OTP Service'),
        ('utils.qr_service', 'QR Service'),
        ('utils.safe_query', 'Safe Query'),
        ('utils.analytics_queries', 'Analytics Queries'),
        ('utils.analytics', 'Analytics'),
        ('routes.analytics', 'Analytics Routes'),
        ('routes.iot_attendance', 'IoT Attendance'),
        ('routes.timetable', 'Timetable Routes'),
        ('app', 'Main Application'),
    ]
    
    failed = []
    passed = 0
    
    for module_name, display_name in modules_to_test:
        if test_module(module_name, display_name):
            passed += 1
        else:
            failed.append(display_name)
    
    print()
    print("="*60)
    print(f"Results: {passed} passed, {len(failed)} failed")
    print("="*60)
    
    if failed:
        print("\nWarning: Modules with issues:")
        for name in failed:
            print(f"  - {name}")
        return 1
    else:
        print("\n[SUCCESS] All modules OK!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
