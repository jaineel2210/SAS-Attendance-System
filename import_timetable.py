"""
Script to import timetable data into the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import db
from database.timetable_data import TIMETABLE_DATA, COURSES, FACULTY_MAPPING
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_timetable_tables():
    """Create timetable related tables"""
    
    # Courses table
    courses_table = """
        CREATE TABLE IF NOT EXISTS courses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_code VARCHAR(20) UNIQUE NOT NULL,
            course_name VARCHAR(200) NOT NULL,
            credits VARCHAR(20),
            semester VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    
    # Timetable table
    timetable_table = """
        CREATE TABLE IF NOT EXISTS timetable (
            id INT AUTO_INCREMENT PRIMARY KEY,
            day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday') NOT NULL,
            time_slot VARCHAR(20) NOT NULL,
            course_code VARCHAR(20) NOT NULL,
            section VARCHAR(10),
            faculty_id INT,
            class_name VARCHAR(10),
            semester VARCHAR(10),
            room_number VARCHAR(20),
            mode VARCHAR(20) DEFAULT 'OFFLINE',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (faculty_id) REFERENCES users(id),
            INDEX idx_day_time (day_of_week, time_slot),
            INDEX idx_course (course_code),
            INDEX idx_faculty (faculty_id)
        )
    """
    
    # Course-Faculty mapping table
    course_faculty_table = """
        CREATE TABLE IF NOT EXISTS course_faculty (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_code VARCHAR(20) NOT NULL,
            faculty_id INT NOT NULL,
            semester VARCHAR(10),
            is_primary BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (faculty_id) REFERENCES users(id),
            INDEX idx_course_faculty (course_code, faculty_id)
        )
    """
    
    try:
        db.connect()
        
        logger.info("Creating courses table...")
        db.execute_query(courses_table)
        
        logger.info("Creating timetable table...")
        db.execute_query(timetable_table)
        
        logger.info("Creating course_faculty table...")
        db.execute_query(course_faculty_table)
        
        logger.info("✅ All timetable tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False

def import_courses():
    """Import course data"""
    try:
        for course_code, course_info in COURSES.items():
            # Check if course exists
            check_query = "SELECT id FROM courses WHERE course_code = %s"
            existing = db.execute_query(check_query, (course_code,))
            
            if existing:
                logger.info(f"Course {course_code} already exists, skipping...")
                continue
            
            # Insert course
            insert_query = """
                INSERT INTO courses (course_code, course_name, credits, semester)
                VALUES (%s, %s, %s, %s)
            """
            db.execute_query(insert_query, (
                course_code,
                course_info['name'],
                course_info['credits'],
                'VII'
            ))
            logger.info(f"✅ Imported course: {course_code} - {course_info['name']}")
        
        logger.info("✅ All courses imported successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error importing courses: {e}")
        return False

def get_faculty_id(faculty_name):
    """Get faculty ID from faculty name"""
    # Extract faculty code from name like "Ms. Purvi Patel(PCP)"
    if '(' in faculty_name and ')' in faculty_name:
        code = faculty_name.split('(')[1].split(')')[0]
        faculty_id = FACULTY_MAPPING.get(code)
        
        if faculty_id:
            # Check if faculty exists in database
            query = "SELECT id FROM users WHERE faculty_id = %s AND role = 'faculty'"
            result = db.execute_query(query, (faculty_id,))
            if result:
                return result[0]['id']
    
    return None

def import_timetable():
    """Import timetable data"""
    try:
        semester = TIMETABLE_DATA['semester']
        class_name = TIMETABLE_DATA['class_name']
        
        for entry in TIMETABLE_DATA['schedule']:
            day = entry['day']
            time_slot = entry['time_slot']
            
            for course in entry['courses']:
                course_code = course['course_code']
                
                # Skip LIBRARY entries
                if course_code == 'LIBRARY':
                    continue
                
                section = course['section']
                faculty_name = course['faculty']
                mode = course.get('mode', 'OFFLINE')
                
                # Get faculty ID
                faculty_id = get_faculty_id(faculty_name)
                
                if not faculty_id:
                    logger.warning(f"Faculty not found for {faculty_name}, skipping entry...")
                    continue
                
                # Check if timetable entry exists
                check_query = """
                    SELECT id FROM timetable 
                    WHERE day_of_week = %s AND time_slot = %s 
                    AND course_code = %s AND section = %s
                """
                existing = db.execute_query(check_query, (day, time_slot, course_code, section))
                
                if existing:
                    logger.info(f"Timetable entry for {day} {time_slot} {course_code} already exists, skipping...")
                    continue
                
                # Insert timetable entry
                insert_query = """
                    INSERT INTO timetable 
                    (day_of_week, time_slot, course_code, section, faculty_id, class_name, semester, mode)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                db.execute_query(insert_query, (
                    day, time_slot, course_code, section, faculty_id, class_name, semester, mode
                ))
                logger.info(f"✅ Imported: {day} {time_slot} - {course_code} ({section})")
        
        logger.info("✅ All timetable entries imported successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error importing timetable: {e}")
        import traceback
        traceback.print_exc()
        return False

def import_course_faculty_mapping():
    """Import course-faculty mapping"""
    try:
        for course_code, course_info in COURSES.items():
            for idx, faculty_name in enumerate(course_info['faculty']):
                faculty_id = get_faculty_id(faculty_name)
                
                if not faculty_id:
                    logger.warning(f"Faculty not found for {faculty_name}, skipping...")
                    continue
                
                # Check if mapping exists
                check_query = """
                    SELECT id FROM course_faculty 
                    WHERE course_code = %s AND faculty_id = %s
                """
                existing = db.execute_query(check_query, (course_code, faculty_id))
                
                if existing:
                    continue
                
                # Insert mapping
                insert_query = """
                    INSERT INTO course_faculty (course_code, faculty_id, semester, is_primary)
                    VALUES (%s, %s, %s, %s)
                """
                is_primary = (idx == 0)  # First faculty is primary
                db.execute_query(insert_query, (course_code, faculty_id, 'VII', is_primary))
                logger.info(f"✅ Mapped {course_code} to faculty {faculty_id}")
        
        logger.info("✅ All course-faculty mappings imported successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error importing course-faculty mapping: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("🎓 TIMETABLE IMPORT SYSTEM")
    print("="*80 + "\n")
    
    # Step 1: Create tables
    print("📋 Step 1: Creating timetable tables...")
    if not create_timetable_tables():
        print("❌ Failed to create tables!")
        return
    
    # Step 2: Import courses
    print("\n📚 Step 2: Importing courses...")
    if not import_courses():
        print("❌ Failed to import courses!")
        return
    
    # Step 3: Import timetable
    print("\n📅 Step 3: Importing timetable...")
    if not import_timetable():
        print("❌ Failed to import timetable!")
        return
    
    # Step 4: Import course-faculty mapping
    print("\n👥 Step 4: Importing course-faculty mapping...")
    if not import_course_faculty_mapping():
        print("❌ Failed to import course-faculty mapping!")
        return
    
    print("\n" + "="*80)
    print("✅ TIMETABLE IMPORT COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\n📊 Summary:")
    print(f"   - Courses: {len(COURSES)}")
    print(f"   - Timetable Entries: {len(TIMETABLE_DATA['schedule'])}")
    print(f"   - Semester: {TIMETABLE_DATA['semester']}")
    print(f"   - Class: {TIMETABLE_DATA['class_name']}")
    print("\n")

if __name__ == '__main__':
    main()
