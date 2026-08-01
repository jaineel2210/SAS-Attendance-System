"""
Populate Sample Attendance Data
Adds sample attendance records for testing analytics
Author: SecureAttend Pro Team
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def populate_sample_attendance():
    """Add sample attendance records for all students"""
    try:
        logger.info("Connecting to database...")
        if not db.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Get all students
        students = db.execute_query("SELECT enrollment_no, full_name FROM students")
        
        if not students or len(students) == 0:
            logger.error("No students found. Please import students first using init_student_system.py")
            return False
        
        logger.info(f"Found {len(students)} students")
        
        # Sample subjects and faculty
        subjects = [
            ('Mathematics', 'Prof. Sharma'),
            ('Physics', 'Prof. Kumar'),
            ('Chemistry', 'Prof. Patel'),
            ('Computer Science', 'Prof. Singh'),
            ('English', 'Prof. Verma')
        ]
        
        # Generate attendance for last 30 days
        today = datetime.now().date()
        start_date = today - timedelta(days=30)
        
        total_records = 0
        
        logger.info("Generating attendance records...")
        
        # For each student
        for student in students:
            enrollment_no = student['enrollment_no']
            
            # Randomly determine student's attendance pattern
            # 70% students are regular (75-95% attendance)
            # 20% students are average (60-75% attendance)
            # 10% students are irregular (<60% attendance)
            
            rand = random.random()
            if rand < 0.7:
                # Regular student
                attendance_probability = random.uniform(0.75, 0.95)
            elif rand < 0.9:
                # Average student
                attendance_probability = random.uniform(0.60, 0.75)
            else:
                # Irregular student
                attendance_probability = random.uniform(0.30, 0.60)
            
            # Generate attendance for each subject
            for subject_name, faculty_name in subjects:
                # Random number of classes (15-25 in last 30 days)
                num_classes = random.randint(15, 25)
                
                for _ in range(num_classes):
                    # Random date within last 30 days
                    days_ago = random.randint(0, 30)
                    attendance_date = today - timedelta(days=days_ago)
                    
                    # Determine if present or absent based on probability
                    status = 'Present' if random.random() < attendance_probability else 'Absent'
                    
                    # Insert attendance record
                    query = """
                        INSERT INTO attendance_records 
                        (enrollment_no, subject_name, faculty_name, date, status)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    
                    db.execute_query(query, (enrollment_no, subject_name, faculty_name, attendance_date, status))
                    total_records += 1
        
        logger.info(f"\n✓ Successfully created {total_records} attendance records!")
        logger.info(f"  Students: {len(students)}")
        logger.info(f"  Subjects: {len(subjects)}")
        logger.info(f"  Date Range: {start_date} to {today}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error populating attendance data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.disconnect()


def main():
    """Main function"""
    print("\n" + "="*60)
    print("SecureAttend Pro - Sample Attendance Data Generator")
    print("="*60 + "\n")
    
    print("This script will create sample attendance records for all students.")
    print("This is useful for testing the analytics dashboard.\n")
    
    confirm = input("Do you want to continue? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Aborted.")
        return
    
    print("\nGenerating sample attendance data...\n")
    
    if populate_sample_attendance():
        print("\n" + "="*60)
        print("Sample Data Created Successfully!")
        print("="*60)
        print("\nYou can now:")
        print("  1. Start your Flask application")
        print("  2. Login as admin")
        print("  3. Navigate to /admin/analytics to view analytics")
        print("  4. Login as faculty to view /faculty/analytics")
        print("\n")
    else:
        print("\n❌ Failed to create sample data. Please check the error messages above.")


if __name__ == '__main__':
    main()
