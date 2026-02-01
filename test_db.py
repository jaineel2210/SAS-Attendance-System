"""
Simple test script to verify database connectivity
"""

import pymysql
from pymysql import Error
import os
from dotenv import load_dotenv

load_dotenv()

def test_mysql_connection():
    """Test MySQL connection with different methods"""
    host = os.getenv('MYSQL_HOST', 'localhost')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', 'Hardik@2005')
    
    print(f"Testing MySQL connection...")
    print(f"Host: {host}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password)}")
    
    # Try with pymysql
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        
        if connection.open:
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            db_info = cursor.fetchone()
            print(f"✅ Connected successfully to MySQL server version {db_info[0]}")
            
            cursor.execute("SELECT DATABASE()")
            record = cursor.fetchone()
            print(f"✅ Current database: {record}")
            
            # Try to create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS attendance_system")
            print("✅ Database 'attendance_system' created or already exists")
            
            cursor.close()
            connection.close()
            print("✅ MySQL connection test passed!")
            return True
            
    except Error as e:
        print(f"❌ Connection failed: {e}")
    
    print("❌ All connection methods failed!")
    print("\n🔧 Troubleshooting:")
    print("1. Check if MySQL server is running")
    print("2. Verify credentials in .env file")
    print("3. Check MySQL service: net start mysql")
    print("4. Try: mysql -u root -p")
    
    return False

if __name__ == "__main__":
    test_mysql_connection()
