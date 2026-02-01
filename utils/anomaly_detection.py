"""
Attendance Anomaly Detection Module
Rule-based detection for proxy attendance and suspicious patterns
"""

from datetime import datetime, timedelta
from database.database import db
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detect anomalies in attendance records for proxy detection"""
    
    ANOMALY_TYPES = {
        'MULTI_METHOD_SAME_SESSION': 'Multiple attendance methods used in same session',
        'OUTSIDE_SCHEDULE': 'Attendance marked outside scheduled time',
        'DUPLICATE_RFID': 'Same RFID used by multiple users',
        'RAPID_ATTENDANCE': 'Attendance marked too quickly after previous',
        'LOCATION_MISMATCH': 'Location mismatch detected',
        'FACE_QR_MISMATCH': 'Face and QR mismatch in same session',
        'IMPOSSIBLE_TIMING': 'Physically impossible timing between locations',
        'DUPLICATE_ATTENDANCE': 'Duplicate attendance in same session'
    }
    
    def __init__(self):
        self.anomalies = []
        
    def detect_all_anomalies(self, date=None):
        """Run all anomaly detection rules and return flagged records"""
        if date is None:
            date = datetime.now().date()
        
        self.anomalies = []
        
        # Run all detection rules
        self.anomalies.extend(self._detect_multi_method_attendance(date))
        self.anomalies.extend(self._detect_outside_schedule(date))
        self.anomalies.extend(self._detect_duplicate_rfid())
        self.anomalies.extend(self._detect_rapid_attendance(date))
        self.anomalies.extend(self._detect_duplicate_attendance(date))
        
        return self.anomalies
    
    def _detect_multi_method_attendance(self, date):
        """Detect same student marked via multiple methods in same session"""
        anomalies = []
        
        query = """
            SELECT 
                a.user_id,
                u.name,
                u.enrollment_no,
                a.session_id,
                a.subject,
                GROUP_CONCAT(DISTINCT a.method) as methods,
                COUNT(DISTINCT a.method) as method_count,
                MIN(a.timestamp) as first_mark,
                MAX(a.timestamp) as last_mark
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE DATE(a.timestamp) = %s
            GROUP BY a.user_id, a.session_id, a.subject
            HAVING method_count > 1
        """
        
        try:
            results = db.execute_query(query, (date,))
            if results:
                for row in results:
                    anomalies.append({
                        'type': 'MULTI_METHOD_SAME_SESSION',
                        'severity': 'HIGH',
                        'description': self.ANOMALY_TYPES['MULTI_METHOD_SAME_SESSION'],
                        'user_id': row['user_id'],
                        'student_name': row['name'],
                        'enrollment_no': row['enrollment_no'],
                        'subject': row['subject'],
                        'details': f"Methods used: {row['methods']}",
                        'timestamp': row['first_mark'],
                        'detected_at': datetime.now().isoformat()
                    })
        except Exception as e:
            logger.error(f"Error detecting multi-method attendance: {e}")
        
        return anomalies
    
    def _detect_outside_schedule(self, date):
        """Detect attendance marked outside scheduled class time"""
        anomalies = []
        
        # Get all attendance with session info
        query = """
            SELECT 
                a.id,
                a.user_id,
                u.name,
                u.enrollment_no,
                a.subject,
                a.timestamp,
                a.session_id,
                s.start_time,
                s.end_time
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN sessions s ON a.session_id = s.id
            WHERE DATE(a.timestamp) = %s
            AND s.id IS NOT NULL
        """
        
        try:
            results = db.execute_query(query, (date,))
            if results:
                for row in results:
                    if row['start_time'] and row['end_time']:
                        attendance_time = row['timestamp'].time() if isinstance(row['timestamp'], datetime) else row['timestamp']
                        
                        # Allow 15 min before and 30 min after scheduled time
                        buffer_before = timedelta(minutes=15)
                        buffer_after = timedelta(minutes=30)
                        
                        if attendance_time < (datetime.combine(date, row['start_time']) - buffer_before).time() or \
                           attendance_time > (datetime.combine(date, row['end_time']) + buffer_after).time():
                            anomalies.append({
                                'type': 'OUTSIDE_SCHEDULE',
                                'severity': 'MEDIUM',
                                'description': self.ANOMALY_TYPES['OUTSIDE_SCHEDULE'],
                                'user_id': row['user_id'],
                                'student_name': row['name'],
                                'enrollment_no': row['enrollment_no'],
                                'subject': row['subject'],
                                'details': f"Marked at {attendance_time}, Schedule: {row['start_time']}-{row['end_time']}",
                                'timestamp': row['timestamp'],
                                'detected_at': datetime.now().isoformat()
                            })
        except Exception as e:
            logger.error(f"Error detecting outside schedule: {e}")
        
        return anomalies
    
    def _detect_duplicate_rfid(self):
        """Detect same RFID UID used by multiple users"""
        anomalies = []
        
        query = """
            SELECT 
                rfid_uid,
                COUNT(*) as user_count,
                GROUP_CONCAT(name) as users,
                GROUP_CONCAT(id) as user_ids
            FROM users
            WHERE rfid_uid IS NOT NULL AND rfid_uid != ''
            GROUP BY rfid_uid
            HAVING user_count > 1
        """
        
        try:
            results = db.execute_query(query)
            if results:
                for row in results:
                    anomalies.append({
                        'type': 'DUPLICATE_RFID',
                        'severity': 'CRITICAL',
                        'description': self.ANOMALY_TYPES['DUPLICATE_RFID'],
                        'rfid_uid': row['rfid_uid'],
                        'details': f"RFID shared by: {row['users']}",
                        'affected_users': row['user_ids'],
                        'detected_at': datetime.now().isoformat()
                    })
        except Exception as e:
            logger.error(f"Error detecting duplicate RFID: {e}")
        
        return anomalies
    
    def _detect_rapid_attendance(self, date, min_interval_seconds=30):
        """Detect attendance marked too quickly (possible automated attack)"""
        anomalies = []
        
        query = """
            SELECT 
                a1.user_id,
                u.name,
                u.enrollment_no,
                a1.timestamp as time1,
                a2.timestamp as time2,
                a1.subject as subject1,
                a2.subject as subject2,
                TIMESTAMPDIFF(SECOND, a1.timestamp, a2.timestamp) as seconds_diff
            FROM attendance a1
            JOIN attendance a2 ON a1.user_id = a2.user_id AND a1.id < a2.id
            JOIN users u ON a1.user_id = u.id
            WHERE DATE(a1.timestamp) = %s
            AND DATE(a2.timestamp) = %s
            AND TIMESTAMPDIFF(SECOND, a1.timestamp, a2.timestamp) < %s
            AND a1.subject != a2.subject
        """
        
        try:
            results = db.execute_query(query, (date, date, min_interval_seconds))
            if results:
                for row in results:
                    anomalies.append({
                        'type': 'RAPID_ATTENDANCE',
                        'severity': 'HIGH',
                        'description': self.ANOMALY_TYPES['RAPID_ATTENDANCE'],
                        'user_id': row['user_id'],
                        'student_name': row['name'],
                        'enrollment_no': row['enrollment_no'],
                        'details': f"Two attendances within {row['seconds_diff']} seconds",
                        'subjects': f"{row['subject1']} → {row['subject2']}",
                        'timestamp': row['time1'],
                        'detected_at': datetime.now().isoformat()
                    })
        except Exception as e:
            logger.error(f"Error detecting rapid attendance: {e}")
        
        return anomalies
    
    def _detect_duplicate_attendance(self, date):
        """Detect duplicate attendance entries in same session"""
        anomalies = []
        
        query = """
            SELECT 
                a.user_id,
                u.name,
                u.enrollment_no,
                a.subject,
                a.session_id,
                COUNT(*) as entry_count,
                MIN(a.timestamp) as first_entry,
                MAX(a.timestamp) as last_entry
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE DATE(a.timestamp) = %s
            GROUP BY a.user_id, a.session_id, a.subject
            HAVING entry_count > 1
        """
        
        try:
            results = db.execute_query(query, (date,))
            if results:
                for row in results:
                    anomalies.append({
                        'type': 'DUPLICATE_ATTENDANCE',
                        'severity': 'MEDIUM',
                        'description': self.ANOMALY_TYPES['DUPLICATE_ATTENDANCE'],
                        'user_id': row['user_id'],
                        'student_name': row['name'],
                        'enrollment_no': row['enrollment_no'],
                        'subject': row['subject'],
                        'details': f"{row['entry_count']} entries in same session",
                        'timestamp': row['first_entry'],
                        'detected_at': datetime.now().isoformat()
                    })
        except Exception as e:
            logger.error(f"Error detecting duplicate attendance: {e}")
        
        return anomalies
    
    def get_anomaly_summary(self, date=None):
        """Get summary of anomalies by type and severity"""
        if not self.anomalies:
            self.detect_all_anomalies(date)
        
        summary = {
            'total_anomalies': len(self.anomalies),
            'by_severity': {
                'CRITICAL': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'by_type': {},
            'detection_date': date.isoformat() if date else datetime.now().date().isoformat()
        }
        
        for anomaly in self.anomalies:
            severity = anomaly.get('severity', 'LOW')
            anomaly_type = anomaly.get('type', 'UNKNOWN')
            
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            summary['by_type'][anomaly_type] = summary['by_type'].get(anomaly_type, 0) + 1
        
        return summary
    
    def get_student_anomaly_history(self, user_id, days=30):
        """Get anomaly history for a specific student"""
        start_date = datetime.now().date() - timedelta(days=days)
        all_anomalies = []
        
        current_date = start_date
        while current_date <= datetime.now().date():
            daily_anomalies = self.detect_all_anomalies(current_date)
            student_anomalies = [a for a in daily_anomalies if a.get('user_id') == user_id]
            all_anomalies.extend(student_anomalies)
            current_date += timedelta(days=1)
        
        return all_anomalies
    
    def flag_suspicious_students(self, threshold=3):
        """Identify students with multiple anomalies"""
        if not self.anomalies:
            self.detect_all_anomalies()
        
        student_counts = {}
        for anomaly in self.anomalies:
            user_id = anomaly.get('user_id')
            if user_id:
                if user_id not in student_counts:
                    student_counts[user_id] = {
                        'name': anomaly.get('student_name'),
                        'enrollment_no': anomaly.get('enrollment_no'),
                        'count': 0,
                        'types': set()
                    }
                student_counts[user_id]['count'] += 1
                student_counts[user_id]['types'].add(anomaly.get('type'))
        
        suspicious = [
            {
                'user_id': uid,
                'name': data['name'],
                'enrollment_no': data['enrollment_no'],
                'anomaly_count': data['count'],
                'anomaly_types': list(data['types'])
            }
            for uid, data in student_counts.items()
            if data['count'] >= threshold
        ]
        
        return sorted(suspicious, key=lambda x: x['anomaly_count'], reverse=True)


# Global instance
anomaly_detector = AnomalyDetector()
