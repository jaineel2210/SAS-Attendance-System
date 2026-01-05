import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import calendar
import base64
import io
from database.database import db
import logging

logger = logging.getLogger(__name__)

class AttendanceAnalytics:
    def __init__(self):
        plt.style.use('default')
        sns.set_palette("husl")

    def get_student_attendance_data(self, user_id, start_date=None, end_date=None):
        """Get attendance data for a specific student"""
        try:
            # Default to current academic year if no dates provided
            if not start_date:
                start_date = datetime.now().replace(month=7, day=1).date()  # Academic year start
            if not end_date:
                end_date = datetime.now().date()
            
            query = '''
                SELECT a.*, u.name, u.enrollment_no
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE a.user_id = %s AND a.attendance_date BETWEEN %s AND %s
                ORDER BY a.attendance_date DESC
            '''
            
            result = db.execute_query(query, (user_id, start_date, end_date))
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting student attendance data: {e}")
            return []

    def calculate_attendance_percentage(self, user_id, subject=None, session_type=None):
        """Calculate attendance percentage for a student"""
        try:
            # Build query conditions
            where_conditions = ["user_id = %s"]
            params = [user_id]
            
            if subject:
                where_conditions.append("subject = %s")
                params.append(subject)
                
            if session_type:
                where_conditions.append("session_type = %s")
                params.append(session_type)
            
            where_clause = " AND ".join(where_conditions)
            
            # Count total and present attendance
            query = f'''
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN status = 'P' THEN 1 ELSE 0 END) as attended_sessions
                FROM attendance
                WHERE {where_clause}
            '''
            
            result = db.execute_query(query, params)
            
            if result and result[0]['total_sessions'] > 0:
                total = result[0]['total_sessions']
                attended = result[0]['attended_sessions'] if result[0]['attended_sessions'] else 0
                percentage = (attended / total) * 100
                return {
                    'total_sessions': total,
                    'attended_sessions': attended,
                    'percentage': round(percentage, 2)
                }
            else:
                return {
                    'total_sessions': 0,
                    'attended_sessions': 0,
                    'percentage': 0
                }
                
        except Exception as e:
            logger.error(f"Error calculating attendance percentage: {e}")
            return {'total_sessions': 0, 'attended_sessions': 0, 'percentage': 0}

    def get_subject_wise_attendance(self, user_id):
        """Get subject-wise attendance breakdown"""
        try:
            query = '''
                SELECT 
                    subject,
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN status = 'P' THEN 1 ELSE 0 END) as attended_sessions,
                    ROUND((SUM(CASE WHEN status = 'P' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) as percentage
                FROM attendance
                WHERE user_id = %s
                GROUP BY subject
                ORDER BY percentage DESC
            '''
            
            result = db.execute_query(query, (user_id,))
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting subject-wise attendance: {e}")
            return []

    def get_weekly_attendance_data(self, user_id, weeks=8):
        """Get weekly attendance data for charts"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(weeks=weeks)
            
            query = '''
                SELECT 
                    YEAR(attendance_date) as year,
                    WEEK(attendance_date) as week,
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN status = 'P' THEN 1 ELSE 0 END) as attended_sessions
                FROM attendance
                WHERE user_id = %s AND attendance_date BETWEEN %s AND %s
                GROUP BY YEAR(attendance_date), WEEK(attendance_date)
                ORDER BY year, week
            '''
            
            result = db.execute_query(query, (user_id, start_date, end_date))
            
            # Calculate percentages
            if result:
                for row in result:
                    if row['total_sessions'] > 0:
                        attended = row['attended_sessions'] if row['attended_sessions'] else 0
                        row['percentage'] = round((attended / row['total_sessions']) * 100, 2)
                    else:
                        row['percentage'] = 0
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting weekly attendance data: {e}")
            return []

    def get_monthly_attendance_data(self, user_id, months=6):
        """Get monthly attendance data for charts"""
        try:
            end_date = datetime.now().date()
            start_date = end_date.replace(day=1) - timedelta(days=30 * months)
            
            query = '''
                SELECT 
                    YEAR(attendance_date) as year,
                    MONTH(attendance_date) as month,
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN status = 'P' THEN 1 ELSE 0 END) as attended_sessions
                FROM attendance
                WHERE user_id = %s AND attendance_date BETWEEN %s AND %s
                GROUP BY YEAR(attendance_date), MONTH(attendance_date)
                ORDER BY year, month
            '''
            
            result = db.execute_query(query, (user_id, start_date, end_date))
            
            # Add month names and calculate percentages
            if result:
                for row in result:
                    row['month_name'] = calendar.month_name[row['month']]
                    if row['total_sessions'] > 0:
                        attended = row['attended_sessions'] if row['attended_sessions'] else 0
                        row['percentage'] = round((attended / row['total_sessions']) * 100, 2)
                    else:
                        row['percentage'] = 0
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting monthly attendance data: {e}")
            return []

    def get_class_summary(self, faculty_id, date=None):
        """Get class summary for faculty"""
        try:
            if not date:
                date = datetime.now().date()
            
            query = '''
                SELECT 
                    s.subject,
                    s.session_type,
                    s.start_time,
                    s.end_time,
                    COUNT(a.id) as total_attendance_marked,
                    SUM(CASE WHEN a.status = 'P' THEN 1 ELSE 0 END) as present_count
                FROM sessions s
                LEFT JOIN attendance a ON s.faculty_id = a.faculty_id 
                    AND s.subject = a.subject 
                    AND s.session_date = a.attendance_date
                WHERE s.faculty_id = %s AND s.session_date = %s
                GROUP BY s.id, s.subject, s.session_type, s.start_time, s.end_time
                ORDER BY s.start_time
            '''
            
            result = db.execute_query(query, (faculty_id, date))
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting class summary: {e}")
            return []

    def create_attendance_chart(self, data, chart_type='weekly'):
        """Create attendance charts using matplotlib"""
        try:
            if not data:
                return None
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if chart_type == 'weekly':
                weeks = [f"Week {row['week']}" for row in data]
                percentages = [row['percentage'] for row in data]
                ax.plot(weeks, percentages, marker='o', linewidth=2, markersize=8)
                ax.set_title('Weekly Attendance Trend')
                ax.set_xlabel('Week')
                
            elif chart_type == 'monthly':
                months = [row['month_name'] for row in data]
                percentages = [row['percentage'] for row in data]
                ax.bar(months, percentages, color='skyblue', alpha=0.7)
                ax.set_title('Monthly Attendance Distribution')
                ax.set_xlabel('Month')
                plt.xticks(rotation=45)
                
            elif chart_type == 'subject':
                subjects = [row['subject'] for row in data]
                percentages = [row['percentage'] for row in data]
                colors = plt.cm.Set3(range(len(subjects)))
                ax.pie(percentages, labels=subjects, colors=colors, autopct='%1.1f%%', startangle=90)
                ax.set_title('Subject-wise Attendance Distribution')
            
            if chart_type != 'subject':
                ax.set_ylabel('Attendance Percentage (%)')
                ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            return None

    def get_overall_stats(self):
        """Get overall system statistics"""
        try:
            stats_query = '''
                SELECT 
                    (SELECT COUNT(*) FROM users WHERE role = 'student') as total_students,
                    (SELECT COUNT(*) FROM users WHERE role = 'faculty') as total_faculty,
                    (SELECT COUNT(*) FROM attendance WHERE attendance_date = CURDATE()) as today_attendance,
                    (SELECT COUNT(DISTINCT subject) FROM sessions) as total_subjects
            '''
            result = db.execute_query(stats_query)
            return result[0] if result else {}
            
        except Exception as e:
            logger.error(f"Error getting overall stats: {e}")
            return {}
    def get_attendance_stats(self):
        """Get overall attendance statistics - alias for get_overall_stats"""
        return self.get_overall_stats()

# Initialize analytics
analytics = AttendanceAnalytics()
