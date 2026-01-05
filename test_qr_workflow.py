#!/usr/bin/env python3
"""
Complete QR workflow test script
Tests QR generation, uniqueness, and multi-user functionality
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_USERS = {
    "faculty": {"email": "faculty@example.com", "password": "faculty123"},
    "student": {"email": "student@example.com", "password": "student123"}, 
    "admin": {"email": "admin@example.com", "password": "admin123"}
}

def create_session():
    """Create a requests session"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    return session

def login_user(session, user_type):
    """Login a user and return success status"""
    try:
        # Get login page first to establish session
        response = session.get(f"{BASE_URL}/login")
        print(f"Login page status for {user_type}: {response.status_code}")
        
        # Attempt login
        login_data = TEST_USERS[user_type]
        response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
        
        if response.status_code in [302, 200]:
            print(f"✅ {user_type.title()} login successful")
            return True
        else:
            print(f"❌ {user_type.title()} login failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error logging in {user_type}: {str(e)}")
        return False

def test_faculty_session_creation(faculty_session):
    """Test faculty session creation"""
    try:
        # Start attendance session
        session_data = {
            "subject": "Python",
            "sessionType": "lab"
        }
        
        response = faculty_session.post(
            f"{BASE_URL}/start_attendance_session",
            json=session_data,
            headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
        )
        
        print(f"Session creation status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                session_id = result.get('session_id')
                print(f"✅ Session created successfully: {session_id}")
                return session_id
            else:
                print(f"❌ Session creation failed: {result.get('message')}")
                return None
        else:
            print(f"❌ Session creation error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating session: {str(e)}")
        return None

def test_qr_generation(faculty_session, session_id):
    """Test QR code generation and uniqueness"""
    try:
        qr_data = {
            "session_id": session_id,
            "duration_minutes": 10
        }
        
        print("\\nTesting QR code generation...")
        
        # Generate first QR
        response1 = faculty_session.post(
            f"{BASE_URL}/generate_attendance_qr",
            json=qr_data,
            headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
        )
        
        print(f"First QR generation status: {response1.status_code}")
        
        time.sleep(2)  # Wait 2 seconds
        
        # Generate second QR
        response2 = faculty_session.post(
            f"{BASE_URL}/generate_attendance_qr",
            json=qr_data,
            headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
        )
        
        print(f"Second QR generation status: {response2.status_code}")
        
        if response1.status_code == 200 and response2.status_code == 200:
            result1 = response1.json()
            result2 = response2.json()
            
            if result1.get('success') and result2.get('success'):
                qr_id1 = result1.get('qr_session_id')
                qr_id2 = result2.get('qr_session_id')
                
                if qr_id1 != qr_id2:
                    print(f"✅ QR uniqueness verified!")
                    print(f"   QR 1 ID: {qr_id1}")
                    print(f"   QR 2 ID: {qr_id2}")
                    return True
                else:
                    print(f"❌ QR uniqueness failed - same IDs: {qr_id1}")
                    return False
            else:
                print(f"❌ QR generation failed:")
                print(f"   Result 1: {result1}")
                print(f"   Result 2: {result2}")
                return False
        else:
            print(f"❌ QR generation HTTP errors:")
            print(f"   Response 1: {response1.text[:200]}")
            print(f"   Response 2: {response2.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing QR generation: {str(e)}")
        return False

def test_multi_user_sessions():
    """Test simultaneous multi-user login"""
    print("\\n" + "="*60)
    print("TESTING MULTI-USER SIMULTANEOUS LOGIN")
    print("="*60)
    
    sessions = {}
    login_results = {}
    
    # Create sessions for each user type
    for user_type in ["faculty", "student", "admin"]:
        print(f"\\nTesting {user_type} login...")
        sessions[user_type] = create_session()
        login_results[user_type] = login_user(sessions[user_type], user_type)
    
    # Check if all users can be logged in simultaneously
    successful_logins = sum(login_results.values())
    print(f"\\n📊 Multi-user login results: {successful_logins}/3 successful")
    
    if successful_logins == 3:
        print("✅ All user types can login simultaneously!")
        return sessions
    else:
        print("❌ Multi-user login has issues")
        return sessions

def main():
    """Main test function"""
    print("🚀 Starting Comprehensive System Test")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Multi-user simultaneous login
    sessions = test_multi_user_sessions()
    
    # Test 2: Faculty workflow (if faculty login successful)
    if 'faculty' in sessions and sessions['faculty']:
        print("\\n" + "="*60)
        print("TESTING FACULTY QR WORKFLOW")
        print("="*60)
        
        # Create session
        session_id = test_faculty_session_creation(sessions['faculty'])
        
        if session_id:
            # Test QR generation
            qr_test_result = test_qr_generation(sessions['faculty'], session_id)
            
            if qr_test_result:
                print("\\n✅ QR generation and uniqueness tests PASSED")
            else:
                print("\\n❌ QR generation tests FAILED")
        else:
            print("\\n❌ Cannot test QR generation - session creation failed")
    
    # Test Summary
    print("\\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\\nFor manual testing:")
    print("1. Open http://127.0.0.1:5000 in 3 different browser tabs")
    print("2. Login as faculty, student, and admin in separate tabs")
    print("3. Faculty: Start session → Generate QR → Verify uniqueness")
    print("4. Student: Scan QR → Face verification")
    print("5. Admin: Monitor analytics across all sessions")

if __name__ == "__main__":
    main()