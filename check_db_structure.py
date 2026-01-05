#!/usr/bin/env python3
"""
Check the actual database table structure
"""

from database.database import DatabaseManager

def check_table_structure():
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Failed to connect to database")
        return False
        
    print("✅ Connected to database")
    
    try:
        # Check actual table structure
        describe_query = "DESCRIBE users"
        columns = db.execute_query(describe_query)
        
        print(f"\n📋 Query result type: {type(columns)}")
        print(f"📋 Query result: {columns}")
        
        if isinstance(columns, list) and columns:
            print("\n📋 Current 'users' table structure:")
            print("Field | Type | Null | Key | Default | Extra")
            print("-" * 60)
            for col in columns:
                print(f"{col['Field']} | {col['Type']} | {col['Null']} | {col['Key']} | {col['Default']} | {col['Extra']}")
        else:
            print("❌ Could not get table structure")
        
        # Check existing users
        users_query = "SELECT * FROM users LIMIT 3"
        users = db.execute_query(users_query)
        
        print(f"\n👥 Users query result: {users}")
        print(f"👥 Found {len(users) if users and isinstance(users, list) else 0} existing users:")
        if users and isinstance(users, list):
            for user in users:
                print(f"  ID: {user.get('id')} | Name: {user.get('name')} | Role: {user.get('role')} | Enrollment: {user.get('enrollment_no')}")
                
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
        return False
    finally:
        db.disconnect()
        
    return True

if __name__ == "__main__":
    check_table_structure()
