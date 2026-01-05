"""
Debug script to check faculty user in database
"""
import pymysql
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_faculty_user():
    """Check if faculty user exists and is verified"""
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        cursor = connection.cursor()
        
        # Check all faculty users
        query = """
            SELECT id, name, enrollment_no, faculty_id, mobile_number, 
                   role, is_verified, is_approved, password_hash
            FROM users 
            WHERE role = 'faculty'
            ORDER BY created_at DESC
        """
        
        cursor.execute(query)
        faculty_users = cursor.fetchall()
        
        print("\n" + "="*80)
        print("FACULTY USERS IN DATABASE:")
        print("="*80)
        
        if not faculty_users:
            print("❌ No faculty users found in database!")
        else:
            for i, user in enumerate(faculty_users, 1):
                print(f"\n{i}. Faculty User:")
                print(f"   ID: {user['id']}")
                print(f"   Name: {user['name']}")
                print(f"   Faculty ID: {user['faculty_id']}")
                print(f"   Enrollment No: {user['enrollment_no']}")
                print(f"   Mobile: {user['mobile_number']}")
                print(f"   Role: {user['role']}")
                print(f"   Is Verified: {user['is_verified']}")
                print(f"   Is Approved: {user['is_approved']}")
                print(f"   Has Password: {'Yes' if user['password_hash'] else 'No'}")
                
                # Test authentication query
                test_identifier = user['faculty_id'] or user['enrollment_no']
                test_query = """
                    SELECT id, name, faculty_id, enrollment_no, is_verified 
                    FROM users 
                    WHERE (enrollment_no = %s OR faculty_id = %s OR mobile_number = %s) 
                    AND is_verified = TRUE
                """
                cursor.execute(test_query, (test_identifier, test_identifier, test_identifier))
                result = cursor.fetchone()
                
                print(f"\n   🔍 Test Login Query:")
                print(f"      Identifier: {test_identifier}")
                print(f"      Query Found User: {'✅ YES' if result else '❌ NO'}")
                if result:
                    print(f"      Found: {result['name']} (ID: {result['id']})")
        
        print("\n" + "="*80)
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        logger.error(f"Error checking faculty users: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_faculty_user()
