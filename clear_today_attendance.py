#!/usr/bin/env python3
"""
Clear today's attendance records for testing
"""
from database.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_today_attendance():
    """Clear all attendance records for today"""
    try:
        # Clear today's attendance
        delete_query = "DELETE FROM attendance WHERE DATE(attendance_date) = CURDATE()"
        result = db.execute_query(delete_query)
        
        if result is not None:
            logger.info("Successfully cleared today's attendance records")
            
            # Check remaining records
            count_query = "SELECT COUNT(*) as count FROM attendance WHERE DATE(attendance_date) = CURDATE()"
            count_result = db.execute_query(count_query)
            
            if count_result:
                logger.info(f"Remaining today's attendance records: {count_result[0]['count']}")
            
            return True
        else:
            logger.error("Failed to clear attendance records")
            return False
            
    except Exception as e:
        logger.error(f"Error clearing attendance records: {e}")
        return False

def show_current_attendance():
    """Show current attendance records"""
    try:
        query = """
            SELECT u.name, u.enrollment_no, a.attendance_date, a.attendance_time, 
                   a.subject, a.marked_by_face, a.marked_by_rfid
            FROM attendance a 
            JOIN users u ON a.user_id = u.id 
            WHERE DATE(a.attendance_date) = CURDATE()
            ORDER BY a.attendance_time DESC
        """
        result = db.execute_query(query)
        
        if result:
            logger.info(f"Current attendance records for today ({len(result)} records):")
            for record in result:
                method = "Face" if record['marked_by_face'] else "RFID" if record['marked_by_rfid'] else "Manual"
                logger.info(f"  - {record['name']} ({record['enrollment_no']}) - {record['subject']} - {record['attendance_time']} - {method}")
        else:
            logger.info("No attendance records found for today")
            
    except Exception as e:
        logger.error(f"Error showing attendance records: {e}")

if __name__ == "__main__":
    logger.info("=== Current Attendance Records ===")
    show_current_attendance()
    
    logger.info("\n=== Clearing Today's Attendance ===")
    if clear_today_attendance():
        logger.info("Attendance records cleared successfully!")
        
        logger.info("\n=== Verifying Clear ===")
        show_current_attendance()
    else:
        logger.error("Failed to clear attendance records")
