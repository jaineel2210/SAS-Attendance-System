"""
Student Analytics Service
Provides advanced analytics for Admin and Faculty dashboards
Author: SecureAttend Pro Team
"""

from database.database import db
import logging
from datetime import datetime, timedelta
import csv
import io

logger = logging.getLogger(__name__)


class StudentAnalyticsService:
    """Handles all student analytics and data processing"""

    def __init__(self):
        self.db = db

    # ========================== CSV PROCESSING ==========================
    
    def parse_full_name(self, full_name):
        """
        Parse full name into first, middle, last name
        Handles various formats with proper capitalization
        """
        if not full_name:
            return None, None, None
        
        # Clean and split name
        parts = [p.strip().title() for p in full_name.strip().split() if p.strip()]
        
        if len(parts) == 0:
            return None, None, None
        elif len(parts) == 1:
            return parts[0], None, None
        elif len(parts) == 2:
            return parts[0], None, parts[1]
        else:
            # First word is first name, last word is last name, rest is middle
            return parts[0], ' '.join(parts[1:-1]), parts[-1]

    def extract_year_from_enrollment(self, enrollment_no):
        """
        Extract admission year from enrollment number
        Format: YYXXXXXXXX (YY = year, e.g., 2201031000001 -> 22 -> 2022)
        """
        try:
            if not enrollment_no or len(enrollment_no) < 2:
                return None
            
            year_prefix = str(enrollment_no)[:2]
            year = int(year_prefix)
            
            # Convert 2-digit year to 4-digit (21 -> 2021, 22 -> 2022)
            if year >= 0 and year <= 99:
                full_year = 2000 + year
                return full_year
            return None
        except:
            return None

    def process_csv_data(self, csv_file):
        """
        Process uploaded CSV file and insert into database
        Returns: (success_count, duplicate_count, error_count, messages)
        """
        success_count = 0
        duplicate_count = 0
        error_count = 0
        messages = []

        try:
            # Read CSV file
            stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            
            # Normalize column names (remove spaces, lowercase)
            rows = []
            for row in csv_input:
                normalized_row = {}
                for key, value in row.items():
                    clean_key = key.strip().lower().replace(' ', '_')
                    normalized_row[clean_key] = value.strip() if value else None
                rows.append(normalized_row)
            
            # Process each row
            for idx, row in enumerate(rows, start=2):  # Start from 2 (1 is header)
                try:
                    sr_no = row.get('srno') or row.get('sr_no')
                    institute = row.get('institute', 'SOCET')
                    enrollment_no = row.get('enrollment_no') or row.get('enrollment')
                    full_name = row.get('student_full_name') or row.get('full_name') or row.get('name')
                    
                    # Validate required fields
                    if not enrollment_no or not full_name:
                        error_count += 1
                        messages.append(f"Row {idx}: Missing enrollment number or name")
                        continue
                    
                    # Parse name
                    first_name, middle_name, last_name = self.parse_full_name(full_name)
                    
                    # Extract year
                    year = self.extract_year_from_enrollment(enrollment_no)
                    
                    # Check if student already exists
                    check_query = "SELECT id FROM students WHERE enrollment_no = %s"
                    existing = self.db.execute_query(check_query, (enrollment_no,))
                    
                    if existing and len(existing) > 0:
                        duplicate_count += 1
                        continue
                    
                    # Insert new student
                    insert_query = """
                        INSERT INTO students 
                        (sr_no, institute, enrollment_no, full_name, first_name, middle_name, last_name, department, year)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    params = (
                        sr_no, institute, enrollment_no, full_name,
                        first_name, middle_name, last_name, institute, year
                    )
                    
                    result = self.db.execute_query(insert_query, params)
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                        messages.append(f"Row {idx}: Failed to insert")
                        
                except Exception as e:
                    error_count += 1
                    messages.append(f"Row {idx}: {str(e)}")
                    logger.error(f"Error processing row {idx}: {e}")
            
            return success_count, duplicate_count, error_count, messages
            
        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            return 0, 0, 1, [f"CSV processing error: {str(e)}"]

    # ========================== ADMIN ANALYTICS ==========================
    
    def get_admin_basic_stats(self):
        """Get basic statistics for admin dashboard"""
        try:
            query = """
                SELECT 
                    (SELECT COUNT(*) FROM students) as total_students,
                    (SELECT COUNT(*) FROM attendance_records) as total_attendance_records,
                    (SELECT COUNT(DISTINCT enrollment_no) FROM attendance_records) as students_with_attendance
            """
            result = self.db.execute_query(query)
            
            if result and len(result) > 0:
                stats = result[0]
                
                # Calculate average attendance percentage
                avg_query = """
                    SELECT 
                        ROUND(AVG(attendance_percentage), 2) as avg_attendance
                    FROM (
                        SELECT 
                            s.enrollment_no,
                            COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) * 100.0 / 
                            NULLIF(COUNT(ar.id), 0) as attendance_percentage
                        FROM students s
                        LEFT JOIN attendance_records ar ON s.enrollment_no = ar.enrollment_no
                        GROUP BY s.enrollment_no
                        HAVING COUNT(ar.id) > 0
                    ) as student_attendance
                """
                avg_result = self.db.execute_query(avg_query)
                avg_attendance = avg_result[0]['avg_attendance'] if avg_result and avg_result[0]['avg_attendance'] else 0
                
                # Students below 75%
                below_75_query = """
                    SELECT COUNT(*) as count
                    FROM (
                        SELECT 
                            s.enrollment_no,
                            COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) * 100.0 / 
                            NULLIF(COUNT(ar.id), 0) as attendance_percentage
                        FROM students s
                        JOIN attendance_records ar ON s.enrollment_no = ar.enrollment_no
                        GROUP BY s.enrollment_no
                        HAVING attendance_percentage < 75
                    ) as low_attendance
                """
                below_result = self.db.execute_query(below_75_query)
                below_75 = below_result[0]['count'] if below_result else 0
                
                return {
                    'total_students': stats['total_students'],
                    'total_attendance_records': stats['total_attendance_records'],
                    'average_attendance': avg_attendance,
                    'students_below_75': below_75
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting admin basic stats: {e}")
            return {}

    def get_institute_analytics(self):
        """Get institute-based analytics"""
        try:
            query = """
                SELECT 
                    s.institute,
                    COUNT(DISTINCT s.enrollment_no) as total_students,
                    ROUND(AVG(CASE WHEN ar.status = 'Present' THEN 100 ELSE 0 END), 2) as attendance_percentage
                FROM students s
                LEFT JOIN attendance_records ar ON s.enrollment_no = ar.enrollment_no
                GROUP BY s.institute
            """
            result = self.db.execute_query(query)
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting institute analytics: {e}")
            return []

    def get_surname_analytics(self, limit=5):
        """Get most common surnames"""
        try:
            query = """
                SELECT 
                    last_name,
                    COUNT(*) as count
                FROM students
                WHERE last_name IS NOT NULL
                GROUP BY last_name
                ORDER BY count DESC
                LIMIT %s
            """
            result = self.db.execute_query(query, (limit,))
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting surname analytics: {e}")
            return []

    def get_year_wise_distribution(self):
        """Get year-wise student distribution"""
        try:
            query = """
                SELECT 
                    year,
                    COUNT(*) as count
                FROM students
                WHERE year IS NOT NULL
                GROUP BY year
                ORDER BY year DESC
            """
            result = self.db.execute_query(query)
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting year-wise distribution: {e}")
            return []

    def get_risk_detection_data(self):
        """
        Get students categorized by attendance risk level
        <60% → High Risk (Red)
        60–75% → Medium Risk (Orange)
        >75% → Safe (Green)
        """
        try:
            query = """
                SELECT 
                    s.enrollment_no,
                    s.full_name,
                    COUNT(ar.id) as total_sessions,
                    COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) as attended,
                    ROUND(
                        COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(ar.id), 0), 2
                    ) as attendance_percentage,
                    CASE 
                        WHEN COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) * 100.0 / 
                             NULLIF(COUNT(ar.id), 0) < 60 THEN 'High Risk'
                        WHEN COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) * 100.0 / 
                             NULLIF(COUNT(ar.id), 0) BETWEEN 60 AND 75 THEN 'Medium Risk'
                        ELSE 'Safe'
                    END as risk_level
                FROM students s
                LEFT JOIN attendance_records ar ON s.enrollment_no = ar.enrollment_no
                GROUP BY s.enrollment_no, s.full_name
                HAVING COUNT(ar.id) > 0
                ORDER BY attendance_percentage ASC
            """
            result = self.db.execute_query(query)
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting risk detection data: {e}")
            return []

    def get_monthly_trend(self, months=6):
        """Get monthly attendance trend"""
        try:
            query = """
                SELECT 
                    DATE_FORMAT(date, '%%Y-%%m') as month,
                    ROUND(AVG(CASE WHEN status = 'Present' THEN 100 ELSE 0 END), 2) as attendance_percentage
                FROM attendance_records
                WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
                GROUP BY DATE_FORMAT(date, '%%Y-%%m')
                ORDER BY month ASC
            """
            result = self.db.execute_query(query, (months,))
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting monthly trend: {e}")
            return []

    # ========================== FACULTY ANALYTICS ==========================
    
    def get_faculty_students_list(self, subject_name=None, page=1, per_page=20, search_enrollment=None, search_surname=None):
        """
        Get students list for faculty with pagination and filters
        """
        try:
            offset = (page - 1) * per_page
            
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if subject_name:
                where_conditions.append("ar.subject_name = %s")
                params.append(subject_name)
            
            if search_enrollment:
                where_conditions.append("s.enrollment_no LIKE %s")
                params.append(f"%{search_enrollment}%")
            
            if search_surname:
                where_conditions.append("s.last_name LIKE %s")
                params.append(f"%{search_surname}%")
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Get students with attendance percentage
            query = f"""
                SELECT 
                    s.enrollment_no,
                    s.full_name,
                    COUNT(ar.id) as total_sessions,
                    COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) as attended,
                    ROUND(
                        COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(ar.id), 0), 2
                    ) as attendance_percentage
                FROM students s
                LEFT JOIN attendance_records ar ON s.enrollment_no = ar.enrollment_no
                {where_clause}
                GROUP BY s.enrollment_no, s.full_name
                ORDER BY s.full_name
                LIMIT %s OFFSET %s
            """
            params.extend([per_page, offset])
            
            result = self.db.execute_query(query, tuple(params))
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(DISTINCT s.enrollment_no) as total
                FROM students s
                LEFT JOIN attendance_records ar ON s.enrollment_no = ar.enrollment_no
                {where_clause}
            """
            count_params = params[:-2] if where_conditions else []
            count_result = self.db.execute_query(count_query, tuple(count_params) if count_params else ())
            total = count_result[0]['total'] if count_result else 0
            
            return {
                'students': result if result else [],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting faculty students list: {e}")
            return {'students': [], 'total': 0, 'page': page, 'per_page': per_page, 'total_pages': 0}

    def get_top_regular_students(self, subject_name=None, limit=5):
        """Get top 5 most regular students"""
        try:
            where_clause = "WHERE ar.subject_name = %s" if subject_name else ""
            params = (subject_name, limit) if subject_name else (limit,)
            
            query = f"""
                SELECT 
                    s.enrollment_no,
                    s.full_name,
                    COUNT(ar.id) as total_sessions,
                    COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) as attended,
                    ROUND(
                        COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(ar.id), 0), 2
                    ) as attendance_percentage
                FROM students s
                JOIN attendance_records ar ON s.enrollment_no = ar.enrollment_no
                {where_clause}
                GROUP BY s.enrollment_no, s.full_name
                HAVING COUNT(ar.id) > 0
                ORDER BY attendance_percentage DESC, attended DESC
                LIMIT %s
            """
            result = self.db.execute_query(query, params)
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting top regular students: {e}")
            return []

    def get_students_below_threshold(self, threshold=75, subject_name=None):
        """Get students below attendance threshold"""
        try:
            where_clause = "WHERE ar.subject_name = %s" if subject_name else ""
            params = (subject_name,) if subject_name else ()
            
            query = f"""
                SELECT 
                    s.enrollment_no,
                    s.full_name,
                    COUNT(ar.id) as total_sessions,
                    COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) as attended,
                    ROUND(
                        COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(ar.id), 0), 2
                    ) as attendance_percentage
                FROM students s
                JOIN attendance_records ar ON s.enrollment_no = ar.enrollment_no
                {where_clause}
                GROUP BY s.enrollment_no, s.full_name
                HAVING attendance_percentage < {threshold}
                ORDER BY attendance_percentage ASC
            """
            result = self.db.execute_query(query, params)
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting students below threshold: {e}")
            return []

    def get_daily_attendance_summary(self, date=None, subject_name=None):
        """Get daily attendance summary"""
        try:
            target_date = date if date else datetime.now().date()
            
            where_conditions = ["ar.date = %s"]
            params = [target_date]
            
            if subject_name:
                where_conditions.append("ar.subject_name = %s")
                params.append(subject_name)
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
                SELECT 
                    ar.subject_name,
                    COUNT(ar.id) as total_students,
                    COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) as present_count,
                    COUNT(CASE WHEN ar.status = 'Absent' THEN 1 END) as absent_count,
                    ROUND(
                        COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(ar.id), 0), 2
                    ) as attendance_percentage
                FROM attendance_records ar
                WHERE {where_clause}
                GROUP BY ar.subject_name
            """
            result = self.db.execute_query(query, tuple(params))
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting daily attendance summary: {e}")
            return []

    def get_available_subjects(self):
        """Get list of all subjects with attendance records"""
        try:
            query = """
                SELECT DISTINCT subject_name
                FROM attendance_records
                ORDER BY subject_name
            """
            result = self.db.execute_query(query)
            return [row['subject_name'] for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting available subjects: {e}")
            return []

    # ========================== EXPORT FUNCTIONALITY ==========================
    
    def export_attendance_report(self, subject_name=None, from_date=None, to_date=None):
        """Export attendance report as CSV data"""
        try:
            where_conditions = []
            params = []
            
            if subject_name:
                where_conditions.append("ar.subject_name = %s")
                params.append(subject_name)
            
            if from_date:
                where_conditions.append("ar.date >= %s")
                params.append(from_date)
            
            if to_date:
                where_conditions.append("ar.date <= %s")
                params.append(to_date)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            query = f"""
                SELECT 
                    s.enrollment_no,
                    s.full_name,
                    ar.subject_name,
                    ar.faculty_name,
                    ar.date,
                    ar.status,
                    ar.timestamp
                FROM students s
                JOIN attendance_records ar ON s.enrollment_no = ar.enrollment_no
                {where_clause}
                ORDER BY ar.date DESC, s.enrollment_no
            """
            result = self.db.execute_query(query, tuple(params) if params else ())
            return result if result else []
        except Exception as e:
            logger.error(f"Error exporting attendance report: {e}")
            return []


# Create singleton instance
student_analytics_service = StudentAnalyticsService()
