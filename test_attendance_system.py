#!/usr/bin/env python3
"""
Test script to simulate faculty login and session creation
"""

import requests
import json

def test_attendance_system():
    base_url = "http://127.0.0.1:5000"
    
    # Create session to maintain cookies
    session = requests.Session()
    
    print("🧪 Testing Faculty Attendance System")
    print("=" * 50)
    
    # Step 1: Login as faculty
    print("1️⃣  Testing faculty login...")
    login_data = {
        'identifier': 'FAC005',  # From database check
        'password': 'faculty123',  # We need to know the actual password 
        'role': 'faculty'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data)
    print(f"Login Status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        if 'dashboard' in login_response.url:
            print("✅ Login successful - redirected to dashboard")
        else:
            print("❌ Login failed - check credentials")
            print(f"Response: {login_response.text[:200]}...")
            return False
    else:
        print(f"❌ Login failed with status {login_response.status_code}")
        return False
    
    # Step 2: Test attendance session creation
    print("\n2️⃣  Testing attendance session creation...")
    session_data = {
        'subject': 'DBMS',
        'session_type': 'lecture'
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    session_response = session.post(
        f"{base_url}/start_attendance_session", 
        data=json.dumps(session_data), 
        headers=headers
    )
    
    print(f"Session Creation Status: {session_response.status_code}")
    print(f"Response: {session_response.text}")
    
    if session_response.status_code == 200:
        try:
            result = session_response.json()
            if result.get('success'):
                print("✅ Attendance session created successfully!")
                session_id = result.get('session_id')
                print(f"📝 Session ID: {session_id}")
                
                # Step 3: Test getting session stats
                print("\n3️⃣  Testing session statistics...")
                stats_response = session.get(f"{base_url}/get_session_stats/{session_id}")
                print(f"Stats Status: {stats_response.status_code}")
                print(f"Stats Response: {stats_response.text}")
                
                return True
            else:
                print(f"❌ Session creation failed: {result.get('message')}")
                return False
        except json.JSONDecodeError:
            print("❌ Invalid JSON response from session creation")
            return False
    else:
        print(f"❌ Session creation failed with status {session_response.status_code}")
        return False

if __name__ == "__main__":
    test_attendance_system()
