"""
Attendance Prediction Module
Light ML using Logistic Regression to predict at-risk students
"""

import numpy as np
from datetime import datetime, timedelta
from database.database import db
import logging
import pickle
import os

logger = logging.getLogger(__name__)


class AttendancePredictor:
    """Predict students at risk of falling below 75% attendance"""
    
    RISK_LEVELS = {
        'SAFE': {'min': 80, 'max': 100, 'color': '#28a745'},
        'WARNING': {'min': 70, 'max': 80, 'color': '#ffc107'},
        'CRITICAL': {'min': 0, 'max': 70, 'color': '#dc3545'}
    }
    
    THRESHOLD = 75  # Minimum required attendance percentage
    
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.model_path = 'static/models/attendance_predictor.pkl'
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model if exists"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.is_trained = True
                logger.info("Loaded pre-trained attendance prediction model")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
    
    def _save_model(self):
        """Save trained model"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info("Saved attendance prediction model")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def extract_features(self, user_id, days=60):
        """Extract features for a student"""
        try:
            start_date = datetime.now().date() - timedelta(days=days)
            
            # Get attendance data
            query = """
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count,
                    SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                    SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late_count
                FROM attendance
                WHERE user_id = %s AND DATE(timestamp) >= %s
            """
            result = db.execute_query(query, (user_id, start_date))
            
            if not result or not result[0]['total_sessions']:
                return None
            
            data = result[0]
            total = data['total_sessions'] or 1
            present = data['present_count'] or 0
            absent = data['absent_count'] or 0
            late = data['late_count'] or 0
            
            # Get recent trend (last 2 weeks vs previous)
            recent_query = """
                SELECT 
                    COUNT(*) as sessions,
                    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present
                FROM attendance
                WHERE user_id = %s AND DATE(timestamp) >= %s
            """
            recent_start = datetime.now().date() - timedelta(days=14)
            recent_result = db.execute_query(recent_query, (user_id, recent_start))
            
            recent_data = recent_result[0] if recent_result else {'sessions': 0, 'present': 0}
            recent_sessions = recent_data['sessions'] or 1
            recent_present = recent_data['present'] or 0
            recent_percentage = (recent_present / recent_sessions) * 100
            
            # Calculate features
            features = {
                'current_percentage': (present / total) * 100,
                'total_sessions': total,
                'absent_count': absent,
                'late_count': late,
                'recent_percentage': recent_percentage,
                'absent_streak': self._get_absent_streak(user_id),
                'sessions_remaining': self._estimate_remaining_sessions(),
                'required_attendance': self._calculate_required_attendance(user_id)
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    def _get_absent_streak(self, user_id):
        """Get current consecutive absent days"""
        query = """
            SELECT status, DATE(timestamp) as date
            FROM attendance
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT 20
        """
        try:
            results = db.execute_query(query, (user_id,))
            if not results:
                return 0
            
            streak = 0
            for record in results:
                if record['status'] == 'absent':
                    streak += 1
                else:
                    break
            return streak
        except:
            return 0
    
    def _estimate_remaining_sessions(self):
        """Estimate remaining sessions in semester"""
        # Assume 15-week semester with 5 sessions per week
        current_week = datetime.now().isocalendar()[1]
        semester_start_week = 1  # Adjust based on actual semester
        weeks_passed = current_week - semester_start_week
        total_weeks = 15
        remaining_weeks = max(0, total_weeks - weeks_passed)
        return remaining_weeks * 5  # 5 sessions per week estimate
    
    def _calculate_required_attendance(self, user_id):
        """Calculate required attendance rate to reach 75%"""
        features = self.extract_features(user_id, days=120)
        if not features:
            return 100
        
        current = features['current_percentage']
        attended = (current / 100) * features['total_sessions']
        remaining = features['sessions_remaining']
        total_expected = features['total_sessions'] + remaining
        
        needed_total = 0.75 * total_expected
        needed_remaining = needed_total - attended
        
        if remaining <= 0:
            return 100 if current < 75 else 0
        
        required_rate = (needed_remaining / remaining) * 100
        return min(100, max(0, required_rate))
    
    def train_model(self):
        """Train the prediction model using historical data"""
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
            
            # Get all students with sufficient data
            query = """
                SELECT DISTINCT user_id FROM attendance
                GROUP BY user_id
                HAVING COUNT(*) >= 20
            """
            students = db.execute_query(query)
            
            if not students or len(students) < 10:
                logger.warning("Insufficient data for training")
                return False
            
            X = []
            y = []
            
            for student in students:
                features = self.extract_features(student['user_id'])
                if features:
                    # Create feature vector
                    feature_vector = [
                        features['current_percentage'],
                        features['absent_count'],
                        features['late_count'],
                        features['recent_percentage'],
                        features['absent_streak']
                    ]
                    X.append(feature_vector)
                    # Label: 1 if at risk (below 75%), 0 if safe
                    y.append(1 if features['current_percentage'] < 75 else 0)
            
            if len(X) < 10:
                logger.warning("Insufficient training samples")
                return False
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model = LogisticRegression(random_state=42)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            self._save_model()
            logger.info(f"Model trained with {len(X)} samples")
            return True
            
        except ImportError:
            logger.warning("sklearn not available, using rule-based prediction")
            return False
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False
    
    def predict_risk(self, user_id):
        """Predict risk level for a student"""
        features = self.extract_features(user_id)
        
        if not features:
            return {
                'risk_level': 'UNKNOWN',
                'probability': 0,
                'message': 'Insufficient data',
                'recommendations': []
            }
        
        current_pct = features['current_percentage']
        
        # Rule-based prediction (works without ML)
        if current_pct >= 85:
            risk_level = 'SAFE'
            probability = 0.1
        elif current_pct >= 75:
            # Check trend
            if features['recent_percentage'] < features['current_percentage']:
                risk_level = 'WARNING'
                probability = 0.4
            else:
                risk_level = 'SAFE'
                probability = 0.2
        elif current_pct >= 65:
            risk_level = 'WARNING'
            probability = 0.6
        else:
            risk_level = 'CRITICAL'
            probability = 0.9
        
        # Adjust based on absent streak
        if features['absent_streak'] >= 3:
            if risk_level == 'SAFE':
                risk_level = 'WARNING'
                probability += 0.2
            elif risk_level == 'WARNING':
                risk_level = 'CRITICAL'
                probability += 0.2
        
        # Generate recommendations
        recommendations = self._generate_recommendations(features, risk_level)
        
        return {
            'user_id': user_id,
            'risk_level': risk_level,
            'probability': min(1.0, probability),
            'current_attendance': round(current_pct, 2),
            'sessions_attended': int((current_pct / 100) * features['total_sessions']),
            'total_sessions': features['total_sessions'],
            'required_future_attendance': round(features['required_attendance'], 2),
            'absent_streak': features['absent_streak'],
            'color': self.RISK_LEVELS[risk_level]['color'],
            'message': self._get_risk_message(risk_level, current_pct),
            'recommendations': recommendations,
            'prediction_date': datetime.now().isoformat()
        }
    
    def _get_risk_message(self, risk_level, current_pct):
        """Get human-readable risk message"""
        messages = {
            'SAFE': f"Good standing with {current_pct:.1f}% attendance. Keep it up!",
            'WARNING': f"Attention needed! Current attendance is {current_pct:.1f}%. Risk of falling below 75%.",
            'CRITICAL': f"Critical! Only {current_pct:.1f}% attendance. Immediate action required to avoid consequences."
        }
        return messages.get(risk_level, "Unable to determine risk level")
    
    def _generate_recommendations(self, features, risk_level):
        """Generate personalized recommendations"""
        recommendations = []
        
        if risk_level == 'CRITICAL':
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Attend all remaining sessions',
                'reason': f"You need {features['required_attendance']:.0f}% attendance in remaining sessions"
            })
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Meet with academic advisor immediately',
                'reason': 'Discuss attendance improvement plan'
            })
        
        if features['absent_streak'] >= 2:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': f"Break your {features['absent_streak']}-day absence streak",
                'reason': 'Consecutive absences significantly impact attendance'
            })
        
        if features['late_count'] > 3:
            recommendations.append({
                'priority': 'LOW',
                'action': 'Improve punctuality',
                'reason': f"You have been late {features['late_count']} times"
            })
        
        if risk_level == 'WARNING':
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Maintain consistent attendance',
                'reason': 'You are close to the minimum requirement'
            })
        
        return recommendations
    
    def get_all_at_risk_students(self, risk_levels=['WARNING', 'CRITICAL']):
        """Get all students at specified risk levels"""
        query = "SELECT id, name, enrollment_no FROM users WHERE role = 'student'"
        students = db.execute_query(query)
        
        at_risk = []
        
        for student in students or []:
            prediction = self.predict_risk(student['id'])
            if prediction['risk_level'] in risk_levels:
                at_risk.append({
                    'id': student['id'],
                    'name': student['name'],
                    'enrollment_no': student['enrollment_no'],
                    **prediction
                })
        
        # Sort by risk (CRITICAL first, then by attendance)
        at_risk.sort(key=lambda x: (
            0 if x['risk_level'] == 'CRITICAL' else 1,
            x['current_attendance']
        ))
        
        return at_risk
    
    def get_class_risk_summary(self):
        """Get risk summary for entire class"""
        query = "SELECT id FROM users WHERE role = 'student'"
        students = db.execute_query(query)
        
        summary = {
            'total_students': len(students) if students else 0,
            'safe': 0,
            'warning': 0,
            'critical': 0,
            'unknown': 0,
            'average_attendance': 0,
            'at_risk_percentage': 0
        }
        
        total_attendance = 0
        count = 0
        
        for student in students or []:
            prediction = self.predict_risk(student['id'])
            risk_level = prediction['risk_level'].lower()
            summary[risk_level] = summary.get(risk_level, 0) + 1
            
            if prediction['current_attendance'] > 0:
                total_attendance += prediction['current_attendance']
                count += 1
        
        if count > 0:
            summary['average_attendance'] = round(total_attendance / count, 2)
        
        if summary['total_students'] > 0:
            at_risk = summary['warning'] + summary['critical']
            summary['at_risk_percentage'] = round((at_risk / summary['total_students']) * 100, 2)
        
        return summary


# Global instance
attendance_predictor = AttendancePredictor()
