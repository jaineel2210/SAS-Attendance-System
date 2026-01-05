from datetime import datetime, time
from database.database import db

class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_name = db.Column(db.String(20))  # e.g., "1st Period", "Lunch", etc.

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), nullable=False, unique=True)
    building = db.Column(db.String(50))
    capacity = db.Column(db.Integer)
    has_projector = db.Column(db.Boolean, default=False)
    has_smart_board = db.Column(db.Boolean, default=False)

class Faculty(db.Model):
    __tablename__ = 'faculty'
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(15))
    specialization = db.Column(db.String(100))
    designation = db.Column(db.String(50))
    joining_date = db.Column(db.Date)
    rfid_tag = db.Column(db.String(50), unique=True)

class CourseSchedule(db.Model):
    __tablename__ = 'course_schedules'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'))
    day_of_week = db.Column(db.Integer)  # 0=Monday, 6=Sunday
    semester = db.Column(db.Integer)
    academic_year = db.Column(db.String(10))
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    course = db.relationship('Course', backref='schedules')
    faculty = db.relationship('Faculty', backref='schedules')
    room = db.relationship('Room', backref='schedules')
    time_slot = db.relationship('TimeSlot', backref='schedules')

    def __init__(self, course_id, faculty_id, room_id, time_slot_id, day_of_week, 
                 semester, academic_year, is_active=True):
        self.course_id = course_id
        self.faculty_id = faculty_id
        self.room_id = room_id
        self.time_slot_id = time_slot_id
        self.day_of_week = day_of_week
        self.semester = semester
        self.academic_year = academic_year
        self.is_active = is_active

    @staticmethod
    def get_current_schedule():
        """Get the current active schedule based on time and day"""
        current_time = datetime.now().time()
        current_day = datetime.now().weekday()
        
        return CourseSchedule.query.join(TimeSlot).filter(
            CourseSchedule.day_of_week == current_day,
            CourseSchedule.is_active == True,
            TimeSlot.start_time <= current_time,
            TimeSlot.end_time >= current_time
        ).first()

    @staticmethod
    def get_day_schedule(department_id, semester, day_of_week):
        """Get complete schedule for a specific day"""
        return CourseSchedule.query\
            .join(Course)\
            .filter(
                Course.department_id == department_id,
                CourseSchedule.semester == semester,
                CourseSchedule.day_of_week == day_of_week,
                CourseSchedule.is_active == True
            )\
            .order_by(TimeSlot.start_time)\
            .all()

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    hod_id = db.Column(db.Integer, db.ForeignKey('faculty.id'))
    building = db.Column(db.String(50))
    total_semesters = db.Column(db.Integer, default=8)  # For 4-year program

    # Relationships
    courses = db.relationship('Course', backref='department')
    faculty = db.relationship('Faculty', backref='department', foreign_keys=[Faculty.department_id])
    hod = db.relationship('Faculty', foreign_keys=[hod_id])

class Holiday(db.Model):
    __tablename__ = 'holidays'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    holiday_type = db.Column(db.String(50))  # National, Religious, Institute specific
    
class AcademicCalendar(db.Model):
    __tablename__ = 'academic_calendar'
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    event_type = db.Column(db.String(50))  # Exam, Workshop, Seminar, etc.
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    semester = db.Column(db.Integer)
