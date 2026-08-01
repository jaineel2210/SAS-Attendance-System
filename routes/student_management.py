"""
Student Management Routes
Handles CSV import, student data management, and advanced analytics
Author: SecureAttend Pro Team
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from functools import wraps
from werkzeug.utils import secure_filename
import logging
import csv
import io
from datetime import datetime, timedelta
from utils.student_analytics import student_analytics_service

logger = logging.getLogger(__name__)

# Create Blueprint
student_management_bp = Blueprint('student_management', __name__)

# ========================== DECORATORS ==========================

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def faculty_or_admin_required(f):
    """Decorator to require faculty or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        if session.get('role') not in ['admin', 'faculty']:
            flash('Access denied. Faculty or Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ========================== CSV IMPORT ROUTES ==========================

@student_management_bp.route('/import-students')
@admin_required
def import_students_page():
    """Render CSV import page"""
    return render_template('admin/import_students.html')


@student_management_bp.route('/upload-csv', methods=['POST'])
@admin_required
def upload_csv():
    """Handle CSV file upload and process student data"""
    try:
        # Check if file is present
        if 'csv_file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'})
        
        file = request.files['csv_file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        # Validate file extension
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': 'Only CSV files are allowed'})
        
        # Process the CSV file
        success_count, duplicate_count, error_count, messages = student_analytics_service.process_csv_data(file)
        
        # Prepare response
        total_processed = success_count + duplicate_count + error_count
        
        response_data = {
            'success': True,
            'total_processed': total_processed,
            'success_count': success_count,
            'duplicate_count': duplicate_count,
            'error_count': error_count,
            'messages': messages[:10]  # Limit messages to first 10
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'})


# ========================== ADMIN ANALYTICS ROUTES ==========================

@student_management_bp.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Admin analytics dashboard"""
    try:
        # Get all analytics data
        basic_stats = student_analytics_service.get_admin_basic_stats()
        institute_analytics = student_analytics_service.get_institute_analytics()
        surname_analytics = student_analytics_service.get_surname_analytics(limit=5)
        year_distribution = student_analytics_service.get_year_wise_distribution()
        risk_data = student_analytics_service.get_risk_detection_data()
        monthly_trend = student_analytics_service.get_monthly_trend(months=6)
        
        # Categorize risk data
        high_risk = [s for s in risk_data if s['risk_level'] == 'High Risk']
        medium_risk = [s for s in risk_data if s['risk_level'] == 'Medium Risk']
        safe = [s for s in risk_data if s['risk_level'] == 'Safe']
        
        return render_template('admin/admin_analytics_dashboard.html',
                             basic_stats=basic_stats,
                             institute_analytics=institute_analytics,
                             surname_analytics=surname_analytics,
                             year_distribution=year_distribution,
                             high_risk=high_risk,
                             medium_risk=medium_risk,
                             safe=safe,
                             monthly_trend=monthly_trend)
    except Exception as e:
        logger.error(f"Error in admin analytics: {e}")
        flash('Error loading analytics dashboard', 'error')
        return redirect(url_for('dashboard'))


@student_management_bp.route('/api/admin/analytics/stats')
@admin_required
def api_admin_analytics_stats():
    """API endpoint for admin analytics stats (for AJAX updates)"""
    try:
        basic_stats = student_analytics_service.get_admin_basic_stats()
        return jsonify({'success': True, 'data': basic_stats})
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({'success': False, 'message': str(e)})


@student_management_bp.route('/api/admin/analytics/monthly-trend')
@admin_required
def api_monthly_trend():
    """API endpoint for monthly attendance trend"""
    try:
        months = request.args.get('months', 6, type=int)
        trend_data = student_analytics_service.get_monthly_trend(months=months)
        return jsonify({'success': True, 'data': trend_data})
    except Exception as e:
        logger.error(f"Error getting monthly trend: {e}")
        return jsonify({'success': False, 'message': str(e)})


# ========================== FACULTY ANALYTICS ROUTES ==========================

@student_management_bp.route('/faculty/analytics')
@faculty_or_admin_required
def faculty_analytics():
    """Faculty analytics dashboard"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        subject_name = request.args.get('subject')
        search_enrollment = request.args.get('search_enrollment')
        search_surname = request.args.get('search_surname')
        date_filter = request.args.get('date')
        
        # Get available subjects
        subjects = student_analytics_service.get_available_subjects()
        
        # Get students list with pagination
        students_data = student_analytics_service.get_faculty_students_list(
            subject_name=subject_name,
            page=page,
            per_page=20,
            search_enrollment=search_enrollment,
            search_surname=search_surname
        )
        
        # Get top regular students
        top_students = student_analytics_service.get_top_regular_students(
            subject_name=subject_name, limit=5
        )
        
        # Get students below 75%
        below_75 = student_analytics_service.get_students_below_threshold(
            threshold=75, subject_name=subject_name
        )
        
        # Get daily attendance summary
        target_date = datetime.strptime(date_filter, '%Y-%m-%d').date() if date_filter else datetime.now().date()
        daily_summary = student_analytics_service.get_daily_attendance_summary(
            date=target_date, subject_name=subject_name
        )
        
        return render_template('faculty/faculty_analytics_dashboard.html',
                             students=students_data['students'],
                             page=students_data['page'],
                             total_pages=students_data['total_pages'],
                             total_students=students_data['total'],
                             subjects=subjects,
                             selected_subject=subject_name,
                             top_students=top_students,
                             below_75=below_75,
                             daily_summary=daily_summary,
                             selected_date=target_date,
                             search_enrollment=search_enrollment,
                             search_surname=search_surname)
    except Exception as e:
        logger.error(f"Error in faculty analytics: {e}")
        flash('Error loading analytics dashboard', 'error')
        return redirect(url_for('dashboard'))


@student_management_bp.route('/api/faculty/students')
@faculty_or_admin_required
def api_faculty_students():
    """API endpoint for faculty students list (for AJAX)"""
    try:
        page = request.args.get('page', 1, type=int)
        subject_name = request.args.get('subject')
        search_enrollment = request.args.get('search_enrollment')
        search_surname = request.args.get('search_surname')
        
        students_data = student_analytics_service.get_faculty_students_list(
            subject_name=subject_name,
            page=page,
            per_page=20,
            search_enrollment=search_enrollment,
            search_surname=search_surname
        )
        
        return jsonify({'success': True, 'data': students_data})
    except Exception as e:
        logger.error(f"Error getting faculty students: {e}")
        return jsonify({'success': False, 'message': str(e)})


# ========================== EXPORT ROUTES ==========================

@student_management_bp.route('/export/attendance-report')
@faculty_or_admin_required
def export_attendance_report():
    """Export attendance report as CSV"""
    try:
        # Get filter parameters
        subject_name = request.args.get('subject')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Convert dates if provided
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date() if from_date else None
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date() if to_date else None
        
        # Get attendance data
        data = student_analytics_service.export_attendance_report(
            subject_name=subject_name,
            from_date=from_date_obj,
            to_date=to_date_obj
        )
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Enrollment No', 'Student Name', 'Subject', 'Faculty', 'Date', 'Status', 'Timestamp'])
        
        # Write data rows
        for row in data:
            writer.writerow([
                row['enrollment_no'],
                row['full_name'],
                row['subject_name'],
                row['faculty_name'],
                row['date'],
                row['status'],
                row['timestamp']
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=attendance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting attendance report: {e}")
        flash('Error exporting report', 'error')
        return redirect(request.referrer or url_for('dashboard'))


@student_management_bp.route('/export/students-list')
@admin_required
def export_students_list():
    """Export complete students list as CSV"""
    try:
        from database.database import db
        
        query = """
            SELECT 
                sr_no, institute, enrollment_no, full_name, 
                first_name, middle_name, last_name, department, year, created_at
            FROM students
            ORDER BY enrollment_no
        """
        students = db.execute_query(query)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Sr No', 'Institute', 'Enrollment No', 'Full Name', 
                        'First Name', 'Middle Name', 'Last Name', 'Department', 'Year', 'Created At'])
        
        # Write data rows
        for student in students:
            writer.writerow([
                student['sr_no'],
                student['institute'],
                student['enrollment_no'],
                student['full_name'],
                student['first_name'],
                student['middle_name'],
                student['last_name'],
                student['department'],
                student['year'],
                student['created_at']
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=students_list_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting students list: {e}")
        flash('Error exporting students list', 'error')
        return redirect(request.referrer or url_for('dashboard'))
