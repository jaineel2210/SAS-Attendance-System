"""
Timetable Data for Semester VII, Class A
Based on the provided timetable image
"""

TIMETABLE_DATA = {
    'semester': 'VII',
    'class_name': 'A',
    'class_room': '',
    'effective_date': '23/6/2025',
    'schedule': [
        # Monday
        {
            'day': 'Monday',
            'time_slot': '08:20-09:10',
            'courses': [
                {'course_code': '1010103417', 'section': 'A1', 'faculty': 'Ms. Purvi Patel(PCP)'},
                {'course_code': '1010103436', 'section': 'A2', 'faculty': 'Ms. Deepika Shrivastav(DPS)'},
                {'course_code': '1010043439', 'section': 'A3', 'faculty': 'Mr. Viral Mishra(VM)'},
                {'course_code': '1010043441', 'section': 'A4', 'faculty': 'Mr. Vishal Patel(VP)'}
            ]
        },
        {
            'day': 'Monday',
            'time_slot': '09:10-10:00',
            'courses': [
                {'course_code': '1010043439', 'section': 'A4', 'faculty': 'Mr. Viral Mishra(VM)'}
            ]
        },
        {
            'day': 'Monday',
            'time_slot': '10:10-11:00',
            'courses': [
                {'course_code': '1010103417', 'section': 'ALL', 'faculty': 'Ms. Purvi Patel(PCP)'}
            ]
        },
        {
            'day': 'Monday',
            'time_slot': '11:00-11:50',
            'courses': [
                {'course_code': '1010103436', 'section': 'ALL', 'faculty': 'Ms. Deepika Shrivastav(DPS)'}
            ]
        },
        {
            'day': 'Monday',
            'time_slot': '12:20-01:10',
            'courses': [
                {'course_code': '1010043439', 'section': 'ALL', 'faculty': 'Mr. Viral Mishra(VM)'}
            ]
        },
        {
            'day': 'Monday',
            'time_slot': '01:10-02:00',
            'courses': [
                {'course_code': '1010103417', 'section': 'ALL', 'faculty': 'Mr. Parth Desai(PAD)'}
            ]
        },
        {
            'day': 'Monday',
            'time_slot': '02:10-03:00',
            'courses': [
                {'course_code': '1010043441', 'section': 'ALL', 'faculty': 'Mr. Vishal Patel(VP)'}
            ]
        },
        
        # Tuesday
        {
            'day': 'Tuesday',
            'time_slot': '08:20-09:10',
            'courses': [
                {'course_code': 'LIBRARY', 'section': 'A1', 'faculty': 'LIBRARY'},
                {'course_code': '1010103436', 'section': 'A2', 'faculty': 'Ms. Deepika Shrivastav(DPS)'},
                {'course_code': 'LIBRARY', 'section': 'A3', 'faculty': 'LIBRARY'},
                {'course_code': '1010103417', 'section': 'A4', 'faculty': 'Ms. Purvi Patel(PCP)'}
            ]
        },
        {
            'day': 'Tuesday',
            'time_slot': '10:10-11:00',
            'courses': [
                {'course_code': '1010043439', 'section': 'A1', 'faculty': 'Mr. Viral Mishra(VM)'},
                {'course_code': '1010043439', 'section': 'A2', 'faculty': 'Mr. Viral Mishra(VM)'}
            ]
        },
        {
            'day': 'Tuesday',
            'time_slot': '11:00-11:50',
            'courses': [
                {'course_code': '1010103417', 'section': 'A3', 'faculty': 'Ms. Purvi Patel(PCP)'},
                {'course_code': '1010103436', 'section': 'A4', 'faculty': 'Ms. Deepika Shrivastav(DPS)'}
            ]
        },
        {
            'day': 'Tuesday',
            'time_slot': '12:20-01:10',
            'courses': [
                {'course_code': '1010103436', 'section': 'ALL', 'faculty': 'Ms. Deepika Shrivastav(DPS)'}
            ]
        },
        {
            'day': 'Tuesday',
            'time_slot': '01:10-02:00',
            'courses': [
                {'course_code': '1010043439', 'section': 'ALL', 'faculty': 'Mr. Viral Mishra(VM)'}
            ]
        },
        {
            'day': 'Tuesday',
            'time_slot': '02:10-03:00',
            'courses': [
                {'course_code': '1010043441', 'section': 'ALL', 'faculty': 'Mr. Vishal Patel(VP)'}
            ]
        },
        
        # Wednesday
        {
            'day': 'Wednesday',
            'time_slot': '08:20-09:10',
            'courses': [
                {'course_code': '1010103417', 'section': 'A1', 'faculty': 'Ms. Purvi Patel(PCP)'},
                {'course_code': 'LIBRARY', 'section': 'A2', 'faculty': 'LIBRARY'},
                {'course_code': '1010103436', 'section': 'A3', 'faculty': 'Ms. Deepika Shrivastav(DPS)'},
                {'course_code': 'LIBRARY', 'section': 'A4', 'faculty': 'LIBRARY'}
            ]
        },
        {
            'day': 'Wednesday',
            'time_slot': '10:10-11:00',
            'courses': [
                {'course_code': '1010103436', 'section': 'ALL', 'faculty': 'Ms. Deepika Shrivastav(DPS)'}
            ]
        },
        {
            'day': 'Wednesday',
            'time_slot': '11:00-11:50',
            'courses': [
                {'course_code': '1010043439', 'section': 'ALL', 'faculty': 'Mr. Viral Mishra(VM)'}
            ]
        },
        {
            'day': 'Wednesday',
            'time_slot': '12:20-01:10',
            'courses': [
                {'course_code': '1010103417', 'section': 'ALL', 'faculty': 'Ms. Purvi Patel(PCP)'}
            ]
        },
        {
            'day': 'Wednesday',
            'time_slot': '01:10-02:00',
            'courses': [
                {'course_code': 'LIBRARY', 'section': 'ALL', 'faculty': 'LIBRARY'}
            ]
        },
        {
            'day': 'Wednesday',
            'time_slot': '03:00-04:00',
            'courses': [
                {'course_code': '1010343481', 'section': 'ALL', 'faculty': 'Ms. Bhoomi Parmar(BP)', 'mode': 'ONLINE'}
            ]
        },
        
        # Saturday
        {
            'day': 'Saturday',
            'time_slot': '2:00-2:50',
            'courses': [
                {'course_code': '1010043441', 'section': 'ALL', 'faculty': 'Mr. Vishal Patel(VP)'}
            ]
        }
    ]
}

COURSES = {
    '1010103417': {
        'name': 'Natural Language Processing(NLP)',
        'credits': '3+0+2=4',
        'faculty': ['Ms. Purvi Patel(PCP)', 'Mr. Parth Desai(PAD)']
    },
    '1010103436': {
        'name': 'Big Data Analytics(BDA)',
        'credits': '3+0+2=4',
        'faculty': ['Ms. Deepika Shrivastav(DPS)']
    },
    '1010043439': {
        'name': 'Advanced Full-Stack Web Development(AFSWD)',
        'credits': '3+0+2=4',
        'faculty': ['Mr. Viral Mishra(VM)']
    },
    '1010043441': {
        'name': 'DevOps in Cloud(DOC)',
        'credits': '3+0+2=4',
        'faculty': ['Mr. Vishal Patel(VP)']
    },
    '1010343481': {
        'name': 'Employability Enhancement & Job Skills(EE&JS)',
        'credits': '0+1+0=1',
        'faculty': ['Ms. Bhoomi Parmar(BP)']
    }
}

# Mapping of faculty codes to faculty IDs
FACULTY_MAPPING = {
    'PCP': 'FAC001',
    'PAD': 'FAC002',
    'DPS': 'FAC003',
    'VM': 'FAC004',
    'VP': 'FAC005',
    'BP': 'FAC006'
}
