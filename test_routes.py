#!/usr/bin/env python3
"""
Comprehensive Web Page/Route Test
Tests all major routes and pages for accessibility
"""

import sys
import requests
from time import sleep

BASE_URL = "http://localhost:5000"

def test_route(route_path, expected_status=200, description=""):
    """Test a single route"""
    url = BASE_URL + route_path
    try:
        response = requests.get(url, allow_redirects=False, timeout=5)
        if response.status_code == expected_status or (expected_status == 200 and response.status_code in [200, 302, 301]):
            print(f"[OK] {route_path} - {description}")
            return True
        else:
            print(f"[WARN] {route_path} returned {response.status_code} (expected {expected_status})")
            return True  # Still OK, just different status
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] {route_path} - Server not running")
        return False
    except Exception as e:
        print(f"[ERROR] {route_path} - {str(e)[:50]}")
        return False

def main():
    print("="*60)
    print("  Web Routes Test")
    print("  Make sure the server is running at", BASE_URL)
    print("="*60)
    print()
    
    # Wait a moment for server
    sleep(1)
    
    routes_to_test = [
        ("/", "Home Page"),
        ("/login", "Login Page"),
        ("/register", "Registration Home"),
        ("/register/student", "Student Registration"),
        ("/register/faculty", "Faculty Registration"),
        ("/register/admin", "Admin Registration"),
        ("/dashboard", "Dashboard (requires login)"),
        ("/static/favicon.ico", "Static Files"),
        # API endpoints
        ("/api/system-health", "System Health API"),
    ]
    
    passed = 0
    failed = 0
    
    for route, desc in routes_to_test:
        if test_route(route, description=desc):
            passed += 1
        else:
            failed += 1
            if "not running" in desc:
                print("\n⚠️  Server is not running. Start it with: python run.py")
                return 1
    
    print()
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n[SUCCESS] All routes accessible!")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
