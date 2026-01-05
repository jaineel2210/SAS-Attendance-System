#!/usr/bin/env python3
"""
Add test data to the attendance system database
"""

from database.database import DatabaseManager
from auth.authentication import AuthenticationManager

def add_test_data():
    db = DatabaseManager()
    auth = AuthenticationManager()
    
    if not db.connect():
        print("❌ Failed to connect to database")
        return False
        
    print("✅ Connected to database")
    
    try:
        # Add a test faculty user
        faculty_password = auth.hash_password("faculty123")
        faculty_query = '''
            INSERT IGNORE INTO users (
                name, email, password, role, faculty_id
            ) VALUES (%s, %s, %s, %s, %s)
        '''
        
        db.execute_query(faculty_query, (
            "Dr. John Smith", 
            "faculty@test.com", 
            faculty_password,
            "faculty",
            "FAC001"
        ))
        print("✅ Added test faculty user: faculty@test.com / faculty123")
        
        # Add test student users
        student_password = auth.hash_password("student123")
        students = [
            ("Alice Johnson", "alice@test.com", "CS001"),
            ("Bob Wilson", "bob@test.com", "CS002"), 
            ("Carol Davis", "carol@test.com", "CS003"),
            ("David Brown", "david@test.com", "CS004"),
            ("Eva Martinez", "eva@test.com", "CS005")
        ]
        
        for name, email, enrollment_no in students:
            student_query = '''
                INSERT IGNORE INTO users (
                    name, email, password, role, enrollment_no
                ) VALUES (%s, %s, %s, %s, %s)
            '''
            db.execute_query(student_query, (
                name, email, student_password, "student", enrollment_no
            ))
            
        print("✅ Added 5 test student users: student123 password for all")
        
        # Add an admin user
        admin_password = auth.hash_password("admin123")
        admin_query = '''
            INSERT IGNORE INTO users (
                name, email, password, role
            ) VALUES (%s, %s, %s, %s)
        '''
        
        db.execute_query(admin_query, (
            "System Administrator",
            "admin@test.com", 
            admin_password,
            "admin"
        ))
        print("✅ Added admin user: admin@test.com / admin123")
        
        print("\n🎉 Test data added successfully!")
        print("\nLogin credentials:")
        print("📚 Faculty: faculty@test.com / faculty123")
        print("👨‍🎓 Student: alice@test.com / student123 (or bob@test.com, carol@test.com, etc.)")
        print("🔧 Admin: admin@test.com / admin123")
        
    except Exception as e:
        print(f"❌ Error adding test data: {e}")
        return False
    finally:
        db.disconnect()
        
    return True

if __name__ == "__main__":
    add_test_data()
