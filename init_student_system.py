"""
Initialize Student Analytics System
Creates necessary tables and optionally imports CSV data
Author: SecureAttend Pro Team
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_student_tables():
    """Create students and attendance_records tables"""
    try:
        logger.info("Connecting to database...")
        if not db.connect():
            logger.error("Failed to connect to database")
            return False
        
        logger.info("Creating/verifying tables...")
        db.create_tables()
        
        logger.info("✓ Student analytics tables created successfully!")
        logger.info("\nTables created:")
        logger.info("  - students (for student master data)")
        logger.info("  - attendance_records (for attendance tracking)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing tables: {e}")
        return False
    finally:
        db.disconnect()


def import_csv_file(csv_path):
    """Import student data from CSV file"""
    try:
        from utils.student_analytics import student_analytics_service
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False
        
        logger.info(f"Processing CSV file: {csv_path}")
        
        # Connect to database
        if not db.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Open and process file
        class MockFile:
            """Mock file object for CSV processing"""
            def __init__(self, filepath):
                self.filepath = filepath
                self.stream = open(filepath, 'rb')
        
        mock_file = MockFile(csv_path)
        success, duplicates, errors, messages = student_analytics_service.process_csv_data(mock_file)
        mock_file.stream.close()
        
        total = success + duplicates + errors
        
        logger.info("\n" + "="*50)
        logger.info("CSV IMPORT RESULTS")
        logger.info("="*50)
        logger.info(f"Total Records Processed: {total}")
        logger.info(f"Successfully Inserted:   {success}")
        logger.info(f"Duplicates Skipped:      {duplicates}")
        logger.info(f"Errors:                  {errors}")
        logger.info("="*50)
        
        if messages:
            logger.info("\nMessages:")
            for msg in messages[:10]:  # Show first 10 messages
                logger.info(f"  - {msg}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error importing CSV: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.disconnect()


def main():
    """Main function"""
    print("\n" + "="*60)
    print("SecureAttend Pro - Student Analytics System Initialization")
    print("="*60 + "\n")
    
    # Step 1: Create tables
    print("Step 1: Creating database tables...")
    if not init_student_tables():
        print("\n❌ Failed to create tables. Please check your database configuration.")
        return
    
    print("\n" + "="*60)
    
    # Step 2: Ask about CSV import
    import_csv = input("\nDo you want to import student data from CSV? (y/n): ").strip().lower()
    
    if import_csv == 'y':
        csv_path = input("Enter CSV file path (or press Enter for 'student_data_sas.csv'): ").strip()
        if not csv_path:
            csv_path = 'student_data_sas.csv'
        
        print(f"\nImporting data from: {csv_path}")
        if import_csv_file(csv_path):
            print("\n✓ CSV import completed!")
        else:
            print("\n❌ CSV import failed. Please check the error messages above.")
    
    print("\n" + "="*60)
    print("Initialization Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("  1. Start your Flask application")
    print("  2. Login as admin")
    print("  3. Navigate to /admin/analytics to view analytics dashboard")
    print("  4. Use /import-students to upload more CSV files")
    print("\n")


if __name__ == '__main__':
    main()
