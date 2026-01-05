from database.database import db
import logging
import traceback

logger = logging.getLogger(__name__)

def get_total_students():
    """Get total number of students"""
    try:
        result = db.execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
        return result[0]['count'] if result else 0
    except Exception as e:
        logger.error(f"Error getting total students: {str(e)}")
        return 0

def get_attendance_overview():
    """Get overall attendance statistics"""
    try:
        result = db.execute_query("""
            SELECT 
                COUNT(DISTINCT session_id) as total_sessions,
                ROUND(AVG(CASE WHEN status = 'P' THEN 100 ELSE 0 END), 2) as attendance_rate
            FROM attendance
        """)
        return result[0] if result else {'total_sessions': 0, 'attendance_rate': 0}
    except Exception as e:
        logger.error(f"Error getting attendance overview: {str(e)}")
        return {'total_sessions': 0, 'attendance_rate': 0}

def get_todays_stats():
    """Get today's attendance statistics"""
    try:
        result = db.execute_query("""
            SELECT 
                COUNT(DISTINCT session_id) as total_classes,
                COUNT(DISTINCT CASE WHEN status = 'P' THEN user_id END) as students_present,
                ROUND(AVG(CASE WHEN status = 'P' THEN 100 ELSE 0 END), 2) as attendance_rate
            FROM attendance 
            WHERE DATE(timestamp) = CURRENT_DATE
        """)
        return result[0] if result else {
            'total_classes': 0,
            'students_present': 0,
            'attendance_rate': 0
        }
    except Exception as e:
        logger.error(f"Error getting today's stats: {str(e)}")
        return {
            'total_classes': 0,
            'students_present': 0,
            'attendance_rate': 0
        }

def get_subject_stats():
    """Get subject-wise attendance statistics"""
    try:
        return db.execute_query("""
            SELECT 
                COALESCE(subject, 'Unknown') as name,
                COUNT(DISTINCT session_id) as total_sessions,
                ROUND(AVG(CASE WHEN status = 'P' THEN 100 ELSE 0 END), 2) as attendance_rate
            FROM attendance
            GROUP BY subject
            HAVING subject IS NOT NULL
            ORDER BY attendance_rate DESC
            LIMIT 5
        """) or []
    except Exception as e:
        logger.error(f"Error getting subject stats: {str(e)}")
        return []

def get_recent_activity():
    """Get recent attendance activities"""
    try:
        results = db.execute_query("""
            SELECT 
                timestamp as time,
                COALESCE(subject, 'Unknown') as subject,
                ROUND(AVG(CASE WHEN status = 'P' THEN 100 ELSE 0 END), 2) as attendance_rate
            FROM attendance
            GROUP BY timestamp, subject
            ORDER BY timestamp DESC
            LIMIT 5
        """) or []
        
        return [{
            'time': row['time'].strftime('%H:%M'),
            'subject': row['subject'],
            'attendance_rate': row['attendance_rate']
        } for row in results]
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        return []

def get_attendance_trends():
    """Get attendance trends for the last 7 days"""
    try:
        results = db.execute_query("""
            SELECT 
                DATE(timestamp) as date,
                ROUND(AVG(CASE WHEN status = 'P' THEN 100 ELSE 0 END), 2) as attendance_rate
            FROM attendance
            WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        """) or []
        
        return {
            'labels': [row['date'].strftime('%Y-%m-%d') for row in results],
            'data': [row['attendance_rate'] for row in results]
        }
    except Exception as e:
        logger.error(f"Error getting attendance trends: {str(e)}")
        return {'labels': [], 'data': []}
