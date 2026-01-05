"""
Script to fix the faculty_id column in the users table
This will add the faculty_id column if it doesn't exist
"""

import pymysql
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_faculty_column():
    """Add faculty_id column to users table if it doesn't exist"""
    try:
        # Connect to database
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4',
            autocommit=False
        )
        
        cursor = connection.cursor()
        
        # Check if faculty_id column exists
        check_query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'faculty_id'
        """
        
        cursor.execute(check_query, (Config.MYSQL_DATABASE,))
        result = cursor.fetchone()
        
        if result:
            logger.info("✅ faculty_id column already exists")
        else:
            logger.info("Adding faculty_id column...")
            
            # Add faculty_id column after enrollment_no
            alter_query = """
                ALTER TABLE users 
                ADD COLUMN faculty_id VARCHAR(20) UNIQUE AFTER enrollment_no
            """
            cursor.execute(alter_query)
            connection.commit()
            logger.info("✅ faculty_id column added successfully")
        
        # Also make enrollment_no nullable if not already
        logger.info("Making enrollment_no nullable...")
        try:
            nullable_query = """
                ALTER TABLE users 
                MODIFY COLUMN enrollment_no VARCHAR(20) UNIQUE NULL
            """
            cursor.execute(nullable_query)
            connection.commit()
            logger.info("✅ enrollment_no is now nullable")
        except Exception as e:
            logger.warning(f"Could not modify enrollment_no: {e}")
        
        # Verify the changes
        verify_query = """
            SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'users' 
            AND COLUMN_NAME IN ('enrollment_no', 'faculty_id')
            ORDER BY ORDINAL_POSITION
        """
        
        cursor.execute(verify_query, (Config.MYSQL_DATABASE,))
        columns = cursor.fetchall()
        
        logger.info("\n📋 Current column structure:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[2]} (Nullable: {col[1]})")
        
        cursor.close()
        connection.close()
        
        logger.info("\n✅ Database schema update completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing faculty_id column: {e}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        return False

if __name__ == '__main__':
    print("\n🔧 Fixing database schema for faculty registration...\n")
    success = fix_faculty_column()
    
    if success:
        print("\n✅ SUCCESS! You can now register faculty members.")
        print("   Try accessing: http://127.0.0.1:5000/register/faculty")
    else:
        print("\n❌ FAILED! Please check the error messages above.")
