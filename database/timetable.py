"""
DEPRECATED: This module uses SQLAlchemy ORM which is incompatible with the current
PyMySQL-based database implementation. 

TODO: Rewrite using raw SQL queries compatible with database.database.DatabaseManager

For now, timetable functionality is handled through direct SQL queries in app.py
"""

from datetime import datetime, time
from database.database import db

# Note: These classes are currently non-functional as they require SQLAlchemy
# The main app uses raw SQL queries for timetable operations instead

def get_student_timetable(department, day, current_time):
    """Get student timetable using raw SQL"""
    query = '''
        SELECT * FROM student_timetable 
        WHERE department = %s AND day_of_week = %s 
        AND start_time <= %s AND end_time >= %s
        LIMIT 1
    '''
    return db.execute_query(query, (department, day, current_time, current_time))

def get_faculty_schedule(faculty_id, date):
    """Get faculty schedule for a given date"""
    query = '''
        SELECT s.*, u.name as faculty_name 
        FROM sessions s
        JOIN users u ON s.faculty_id = u.id
        WHERE s.faculty_id = %s AND s.session_date = %s
        ORDER BY s.start_time
    '''
    return db.execute_query(query, (faculty_id, date))

# Legacy SQLAlchemy model stubs were removed to avoid parser/runtime issues.
# Timetable operations in this project use raw SQL helper functions above.
