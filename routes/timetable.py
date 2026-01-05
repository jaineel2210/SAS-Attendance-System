from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, timedelta
from database.timetable import (
    TimeSlot, Room, Faculty, CourseSchedule, 
    Department, Holiday, AcademicCalendar
)
from database.database import db

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/timetable', methods=['GET'])
def view_timetable():
    # Get selected department and semester
    dept_id = request.args.get('department', type=int)
    semester = request.args.get('semester', type=int)

    # Get all departments
    departments = Department.query.all()
    
    # If no department is selected, use the first one
    if not dept_id and departments:
        dept_id = departments[0].id
    
    # Get selected department
    selected_dept = Department.query.get_or_404(dept_id) if dept_id else None
    
    # If no semester is selected, use 1
    if not semester:
        semester = 1

    # Get all time slots
    time_slots = TimeSlot.query.order_by(TimeSlot.start_time).all()

    # Get schedules for each day
    daily_schedules = {}
    current_time = datetime.now().time()
    current_day = datetime.now().weekday()

    for day in range(6):  # Monday to Saturday
        schedules = CourseSchedule.get_day_schedule(dept_id, semester, day)
        for schedule in schedules:
            key = (day, schedule.time_slot_id)
            schedule.is_current = (
                day == current_day and 
                schedule.time_slot.start_time <= current_time <= schedule.time_slot.end_time
            )
            daily_schedules[key] = schedule

    # Get available rooms
    available_rooms = Room.query\
        .outerjoin(CourseSchedule, (
            (CourseSchedule.room_id == Room.id) & 
            (CourseSchedule.day_of_week == current_day) &
            CourseSchedule.is_active
        ))\
        .filter(CourseSchedule.id.is_(None))\
        .all()

    # Get faculty schedules
    faculty_list = Faculty.query.filter_by(department_id=dept_id).all()
    for faculty in faculty_list:
        # Get current class
        faculty.current_class = CourseSchedule.query\
            .join(TimeSlot)\
            .filter(
                CourseSchedule.faculty_id == faculty.id,
                CourseSchedule.day_of_week == current_day,
                TimeSlot.start_time <= current_time,
                TimeSlot.end_time >= current_time
            ).first()
        
        # Get next class
        faculty.next_class = CourseSchedule.query\
            .join(TimeSlot)\
            .filter(
                CourseSchedule.faculty_id == faculty.id,
                CourseSchedule.day_of_week == current_day,
                TimeSlot.start_time > current_time
            )\
            .order_by(TimeSlot.start_time)\
            .first()

    # Get next holiday
    next_holiday = Holiday.query\
        .filter(Holiday.date > datetime.now().date())\
        .order_by(Holiday.date)\
        .first()

    # Get upcoming events
    upcoming_events = AcademicCalendar.query\
        .filter(
            AcademicCalendar.end_date >= datetime.now().date(),
            AcademicCalendar.department_id.in_([None, dept_id])
        )\
        .order_by(AcademicCalendar.start_date)\
        .limit(5)\
        .all()

    # Determine week type (for alternate week schedules if needed)
    current_week = datetime.now().isocalendar()[1]
    week_type = "Odd" if current_week % 2 else "Even"

    # Get current academic year
    current_month = datetime.now().month
    current_year = datetime.now().year
    academic_year = f"{current_year}-{current_year+1}" if current_month >= 7 else f"{current_year-1}-{current_year}"

    return render_template(
        'timetable/view_timetable.html',
        departments=departments,
        selected_dept=selected_dept,
        selected_semester=semester,
        time_slots=time_slots,
        daily_schedules=daily_schedules,
        available_rooms=available_rooms,
        faculty_schedules=faculty_list,
        next_holiday=next_holiday,
        upcoming_events=upcoming_events,
        week_type=week_type,
        academic_year=academic_year
    )

@timetable_bp.route('/api/room-availability', methods=['GET'])
def room_availability():
    """API endpoint to check room availability"""
    room_id = request.args.get('room_id', type=int)
    date_str = request.args.get('date')
    
    if not room_id or not date_str:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Get all bookings for the room on the specified date
    schedules = CourseSchedule.query\
        .join(TimeSlot)\
        .filter(
            CourseSchedule.room_id == room_id,
            CourseSchedule.day_of_week == date.weekday(),
            CourseSchedule.is_active == True
        )\
        .order_by(TimeSlot.start_time)\
        .all()
    
    availability = []
    for schedule in schedules:
        availability.append({
            'start_time': schedule.time_slot.start_time.strftime('%H:%M'),
            'end_time': schedule.time_slot.end_time.strftime('%H:%M'),
            'course': schedule.course.name,
            'faculty': f"{schedule.faculty.first_name} {schedule.faculty.last_name}"
        })
    
    return jsonify({
        'room_id': room_id,
        'date': date_str,
        'availability': availability
    })

@timetable_bp.route('/api/faculty-schedule', methods=['GET'])
def faculty_schedule():
    """API endpoint to get faculty schedule"""
    faculty_id = request.args.get('faculty_id', type=int)
    date_str = request.args.get('date')
    
    if not faculty_id or not date_str:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Get faculty schedule for the specified date
    schedules = CourseSchedule.query\
        .join(TimeSlot)\
        .filter(
            CourseSchedule.faculty_id == faculty_id,
            CourseSchedule.day_of_week == date.weekday(),
            CourseSchedule.is_active == True
        )\
        .order_by(TimeSlot.start_time)\
        .all()
    
    schedule_list = []
    for schedule in schedules:
        schedule_list.append({
            'start_time': schedule.time_slot.start_time.strftime('%H:%M'),
            'end_time': schedule.time_slot.end_time.strftime('%H:%M'),
            'course': schedule.course.name,
            'room': schedule.room.room_number
        })
    
    return jsonify({
        'faculty_id': faculty_id,
        'date': date_str,
        'schedule': schedule_list
    })
