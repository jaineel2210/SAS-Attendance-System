#!/usr/bin/env python3
"""Check database schema for QR-related columns"""

from database.database import db

def check_attendance_schema():
    if db.connect():
        # Check if QR columns exist by trying to select them
        qr_columns = ['qr_session_id', 'marked_by_qr']
        existing_columns = []
        
        for col in qr_columns:
            try:
                # Try to select the column - if it exists, no error
                result = db.execute_query(f'SELECT {col} FROM attendance LIMIT 1')
                if result is not None:
                    existing_columns.append(col)
                    print(f"✅ Column '{col}' exists")
            except Exception as e:
                print(f"❌ Column '{col}' missing: {str(e)}")
        
        missing_columns = [col for col in qr_columns if col not in existing_columns]
        
        if missing_columns:
            print('\n🔧 Adding missing QR columns to attendance table...')
            for col in missing_columns:
                try:
                    if col == 'qr_session_id':
                        query = 'ALTER TABLE attendance ADD COLUMN qr_session_id VARCHAR(255) NULL'
                        result = db.execute_query(query)
                        print(f"✅ Added column: {col}")
                    elif col == 'marked_by_qr':
                        query = 'ALTER TABLE attendance ADD COLUMN marked_by_qr TINYINT(1) DEFAULT 0'
                        result = db.execute_query(query)
                        print(f"✅ Added column: {col}")
                except Exception as e:
                    print(f"❌ Failed to add column {col}: {str(e)}")
        
        # Verify all columns exist now
        print('\n📋 Final verification:')
        all_exist = True
        for col in qr_columns:
            try:
                result = db.execute_query(f'SELECT {col} FROM attendance LIMIT 1')
                if result is not None:
                    print(f"✅ {col}: Ready")
                else:
                    print(f"❌ {col}: Still missing")
                    all_exist = False
            except Exception as e:
                print(f"❌ {col}: Error - {str(e)}")
                all_exist = False
        
        return all_exist
    else:
        print('❌ Failed to connect to database')
        return False

if __name__ == '__main__':
    check_attendance_schema()