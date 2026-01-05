"""
Script to create faculty members from timetable
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import db
from database.timetable_data import FACULTY_MAPPING
import bcrypt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FACULTY_DATA = [
    {
        'name': 'Ms. Purvi Patel',
        'faculty_id': 'FAC001',
        'mobile': '9876543001',
        'email': 'purvi.patel@college.edu',
        'department': 'Computer Engineering',
        'password': 'faculty123'
    },
    {
        'name': 'Mr. Parth Desai',
        'faculty_id': 'FAC002',
        'mobile': '9876543002',
        'email': 'parth.desai@college.edu',
        'department': 'Computer Engineering',
        'password': 'faculty123'
    },
    {
        'name': 'Ms. Deepika Shrivastav',
        'faculty_id': 'FAC003',
        'mobile': '9876543003',
        'email': 'deepika.s@college.edu',
        'department': 'Computer Engineering',
        'password': 'faculty123'
    },
    {
        'name': 'Mr. Viral Mishra',
        'faculty_id': 'FAC004',
        'mobile': '9876543004',
        'email': 'viral.mishra@college.edu',
        'department': 'Computer Engineering',
        'password': 'faculty123'
    },
    {
        'name': 'Mr. Vishal Patel',
        'faculty_id': 'FAC005',
        'mobile': '9876543005',
        'email': 'vishal.patel@college.edu',
        'department': 'Computer Engineering',
        'password': 'faculty123'
    },
    {
        'name': 'Ms. Bhoomi Parmar',
        'faculty_id': 'FAC006',
        'mobile': '9876543006',
        'email': 'bhoomi.parmar@college.edu',
        'department': 'Training & Placement',
        'password': 'faculty123'
    }
]

def create_faculty():
    """Create faculty members"""
    try:
        db.connect()
        
        for faculty in FACULTY_DATA:
            # Check if faculty exists
            check_query = "SELECT id FROM users WHERE faculty_id = %s"
            existing = db.execute_query(check_query, (faculty['faculty_id'],))
            
            if existing:
                logger.info(f"Faculty {faculty['faculty_id']} - {faculty['name']} already exists, skipping...")
                continue
            
            # Hash password
            password_hash = bcrypt.hashpw(faculty['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insert faculty
            insert_query = """
                INSERT INTO users 
                (name, faculty_id, mobile_number, role, password_hash, department, is_verified, is_approved)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            db.execute_query(insert_query, (
                faculty['name'],
                faculty['faculty_id'],
                faculty['mobile'],
                'faculty',
                password_hash,
                faculty['department'],
                True,
                True
            ))
            logger.info(f"✅ Created faculty: {faculty['faculty_id']} - {faculty['name']}")
        
        logger.info("\n✅ All faculty members created successfully!")
        print("\n" + "="*80)
        print("📋 FACULTY LOGIN CREDENTIALS")
        print("="*80)
        print("\nDefault password for all faculty: faculty123\n")
        for faculty in FACULTY_DATA:
            print(f"Faculty ID: {faculty['faculty_id']}")
            print(f"Name: {faculty['name']}")
            print(f"Department: {faculty['department']}")
            print(f"Password: {faculty['password']}")
            print("-" * 40)
        print("\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating faculty: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "="*80)
    print("👨‍🏫 FACULTY CREATION SYSTEM")
    print("="*80 + "\n")
    
    if create_faculty():
        print("✅ SUCCESS! Faculty members created and ready to use.")
    else:
        print("❌ FAILED! Could not create faculty members.")
