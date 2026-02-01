"""
SecureAttend Pro - Setup and Database Creation Script
This script initializes the database and creates necessary tables
"""

import pymysql
from pymysql import Error
import os
from config import Config

def create_database():
    """Create the attendance_system database if it doesn't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        if connection.open:
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE}")
            print(f"Database '{Config.MYSQL_DATABASE}' created or already exists")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"Error creating database: {e}")
        return False
                
        except Error as e2:
            print(f"Error creating database: {e2}")
            print("\n💡 Troubleshooting tips:")
            print("1. Make sure MySQL server is running")
            print("2. Check your MySQL credentials in .env file")
            print("3. Ensure the user has database creation privileges")
            print("4. Try connecting manually: mysql -u root -p")
            return False
    
    return False

def setup_project():
    """Setup the complete project"""
    print("🚀 Setting up SecureAttend Pro...")
    
    # Step 1: Create database
    print("\n📊 Creating database...")
    if create_database():
        print("✅ Database setup completed")
    else:
        print("❌ Database setup failed")
        return False
    
    # Step 2: Initialize database tables
    print("\n📋 Creating tables...")
    try:
        from database.database import db
        
        if db.connect():
            db.create_tables()
            db.insert_sample_data()
            print("✅ Tables created and sample data inserted")
        else:
            print("❌ Failed to connect to database")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up tables: {e}")
        return False
    
    # Step 3: Create necessary directories
    print("\n📁 Creating directories...")
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/face_images', exist_ok=True)
    print("✅ Directories created")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Update .env file with your actual credentials")
    print("2. If using Twilio, add your account credentials")
    print("3. For RFID, connect your hardware and update COM port")
    print("4. Run 'python app.py' to start the application")
    print("\n🔑 Default admin login:")
    print("   Enrollment: ADMIN001")
    print("   Password: admin123")
    print("   Mobile: 9999999999 (for OTP)")
    
    return True

if __name__ == "__main__":
    setup_project()
