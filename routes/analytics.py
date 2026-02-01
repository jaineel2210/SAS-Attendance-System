from flask import Blueprint, render_template, session, redirect, url_for, flash
from functools import wraps

# Try to import analytics, use mock if not available
try:
    from utils.analytics import analytics
except ImportError:
    # Mock analytics class if real one fails to import
    class MockAnalytics:
        def get_class_summary(self, user_id, date):
            return []
        def get_student_attendance_data(self, user_id):
            return []
        def calculate_attendance_percentage(self, user_id):
            return {'percentage': 0.0, 'total_sessions': 0, 'attended_sessions': 0}
        def get_subject_wise_attendance(self, user_id):
            return []
        def get_weekly_attendance_data(self, user_id):
            return []
        def get_monthly_attendance_data(self, user_id):
            return []
        def create_attendance_chart(self, data, chart_type):
            return ""
    analytics = MockAnalytics()

from utils.safe_query import safe_execute_query
from database.database import db
import logging
import traceback

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@analytics_bp.route('/analytics')
@login_required
def analytics_page():
    """Analytics page"""
    user_role = session.get('role')
    user_id = session.get('user_id')
    
    if user_role == 'student':
        # Student analytics
        weekly_data = analytics.get_weekly_attendance_data(user_id)
        monthly_data = analytics.get_monthly_attendance_data(user_id)
        subject_data = analytics.get_subject_wise_attendance(user_id)
        
        # Create charts
        weekly_chart = analytics.create_attendance_chart(weekly_data, 'weekly')
        monthly_chart = analytics.create_attendance_chart(monthly_data, 'monthly')
        subject_chart = analytics.create_attendance_chart(subject_data, 'subject')
        
        return render_template('analytics/student_analytics.html',
                             weekly_chart=weekly_chart,
                             monthly_chart=monthly_chart,
                             subject_chart=subject_chart,
                             weekly_data=weekly_data,
                             monthly_data=monthly_data,
                             subject_data=subject_data)
    
    elif user_role in ['admin', 'faculty']:
        from utils.safe_query import safe_execute_query
        try:
            # Initialize default stats
            stats = {
                'overall_attendance': 0,
                'total_sessions': 0,
                'active_students': 0,
                'today': {'total_classes': 0, 'students_present': 0, 'attendance_rate': 0},
                'subjects': [],
                'departments': [],
                'recent_activity': [],
                'trends': {'labels': [], 'data': []}
            }
            
            # Overall statistics
            total_students = safe_execute_query(
                "SELECT COUNT(id) as count FROM users WHERE role = 'student'",
                {'count': 0}
            )
            stats['active_students'] = total_students['count']
            
            # Attendance overview
            overview = safe_execute_query("""
                SELECT 
                    COUNT(DISTINCT session_id) as total_sessions,
                    ROUND(AVG(CASE WHEN status = 'P' THEN 100 ELSE 0 END), 2) as attendance_rate
                FROM attendance
            """, {'total_sessions': 0, 'attendance_rate': 0})
            stats['total_sessions'] = overview['total_sessions']
            stats['overall_attendance'] = overview['attendance_rate']
            
            # Today's statistics
            today = safe_execute_query("""
                SELECT 
                    COUNT(DISTINCT session_id) as total_classes,
                    COUNT(DISTINCT CASE WHEN status = 'P' THEN user_id END) as students_present,
                    ROUND(AVG(CASE WHEN status = 'P' THEN 100 ELSE 0 END), 2) as attendance_rate
                FROM attendance 
                WHERE DATE(timestamp) = CURRENT_DATE
            """, {'total_classes': 0, 'students_present': 0, 'attendance_rate': 0})
            stats['today'] = {
                'total_classes': today['total_classes'],
                'students_present': today['students_present'],
                'attendance_rate': today['attendance_rate']
            }
            
            # Subject-wise statistics
            subjects = db.execute_query("""
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
            stats['subjects'] = [dict(row) for row in subjects]
            
            # Recent activity
            activities = db.execute_query("""
                SELECT 
                    timestamp as time,
                    COALESCE(subject, 'Unknown') as subject,
                    ROUND(AVG(CASE WHEN status = 'P' THEN 100 ELSE 0 END), 2) as attendance_rate
                FROM attendance
                GROUP BY timestamp, subject
                ORDER BY timestamp DESC
                LIMIT 5
            """) or []
            stats['recent_activity'] = [{
                'time': row['time'].strftime('%H:%M'),
                'subject': row['subject'],
                'attendance_rate': row['attendance_rate']
            } for row in activities]
            
            # Attendance trends
            trends = db.execute_query("""
                SELECT 
                    DATE(timestamp) as date,
                    ROUND(AVG(CASE WHEN status = 'P' THEN 100 ELSE 0 END), 2) as attendance_rate
                FROM attendance
                WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            """) or []
            stats['trends'] = {
                'labels': [row['date'].strftime('%Y-%m-%d') for row in trends],
                'data': [row['attendance_rate'] for row in trends]
            }
            
            return render_template('analytics/admin_analytics.html', stats=stats)
            
        except Exception as e:
            logger.error(f"Error in analytics page: {str(e)}")
            logger.error(traceback.format_exc())
            flash('Error loading analytics data', 'error')
            return redirect(url_for('dashboard'))
    
    # Default fallback
    return redirect(url_for('dashboard'))
