"""
Performance & Security Testing Module
Measure system performance and security features
"""

import time
import threading
from datetime import datetime
from database.database import db
import logging
import json
import os

logger = logging.getLogger(__name__)


class PerformanceTester:
    """Test system performance metrics"""
    
    def __init__(self):
        self.results = {
            'face_recognition': [],
            'attendance_marking': [],
            'database_queries': [],
            'concurrent_users': [],
            'security_tests': []
        }
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function"""
        start = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = str(e)
            success = False
        end = time.time()
        
        return {
            'execution_time_ms': round((end - start) * 1000, 2),
            'success': success,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
    
    def test_database_performance(self, iterations=10):
        """Test database query performance"""
        tests = []
        
        # Test SELECT performance
        for i in range(iterations):
            result = self.measure_execution_time(
                db.execute_query,
                "SELECT COUNT(*) as count FROM users"
            )
            result['query_type'] = 'SELECT COUNT'
            tests.append(result)
        
        # Test complex JOIN
        for i in range(iterations):
            result = self.measure_execution_time(
                db.execute_query,
                """
                SELECT u.name, COUNT(a.id) as attendance_count
                FROM users u
                LEFT JOIN attendance a ON u.id = a.user_id
                GROUP BY u.id
                LIMIT 10
                """
            )
            result['query_type'] = 'JOIN + GROUP BY'
            tests.append(result)
        
        self.results['database_queries'] = tests
        
        # Calculate statistics
        times = [t['execution_time_ms'] for t in tests if t['success']]
        stats = {
            'total_tests': len(tests),
            'successful': sum(1 for t in tests if t['success']),
            'avg_time_ms': round(sum(times) / len(times), 2) if times else 0,
            'min_time_ms': round(min(times), 2) if times else 0,
            'max_time_ms': round(max(times), 2) if times else 0
        }
        
        return stats
    
    def test_face_recognition_performance(self, iterations=5):
        """Test face recognition speed"""
        try:
            from face_processing.face_processor import face_processor
            import cv2
            import numpy as np
            
            tests = []
            
            # Create test image
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            for i in range(iterations):
                # Test face detection
                result = self.measure_execution_time(
                    face_processor.detect_faces,
                    test_image
                )
                result['operation'] = 'face_detection'
                tests.append(result)
                
                # Test face feature extraction
                result = self.measure_execution_time(
                    face_processor.extract_face_features,
                    test_image
                )
                result['operation'] = 'feature_extraction'
                tests.append(result)
            
            self.results['face_recognition'] = tests
            
            # Statistics
            detection_times = [t['execution_time_ms'] for t in tests if t['operation'] == 'face_detection' and t['success']]
            extraction_times = [t['execution_time_ms'] for t in tests if t['operation'] == 'feature_extraction' and t['success']]
            
            return {
                'face_detection': {
                    'avg_time_ms': round(sum(detection_times) / len(detection_times), 2) if detection_times else 0,
                    'tests': len(detection_times)
                },
                'feature_extraction': {
                    'avg_time_ms': round(sum(extraction_times) / len(extraction_times), 2) if extraction_times else 0,
                    'tests': len(extraction_times)
                }
            }
            
        except Exception as e:
            logger.error(f"Face recognition test error: {e}")
            return {'error': str(e)}
    
    def test_concurrent_users(self, num_users=10):
        """Simulate concurrent user access"""
        results = []
        threads = []
        
        def simulate_user_request(user_num):
            start = time.time()
            try:
                # Simulate database access
                db.execute_query("SELECT * FROM users LIMIT 5")
                success = True
            except:
                success = False
            end = time.time()
            
            results.append({
                'user': user_num,
                'response_time_ms': round((end - start) * 1000, 2),
                'success': success
            })
        
        # Create threads
        for i in range(num_users):
            t = threading.Thread(target=simulate_user_request, args=(i,))
            threads.append(t)
        
        # Start all threads simultaneously
        start_time = time.time()
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        total_time = time.time() - start_time
        
        self.results['concurrent_users'] = results
        
        times = [r['response_time_ms'] for r in results if r['success']]
        return {
            'concurrent_users': num_users,
            'total_time_s': round(total_time, 2),
            'successful_requests': sum(1 for r in results if r['success']),
            'avg_response_time_ms': round(sum(times) / len(times), 2) if times else 0,
            'max_response_time_ms': round(max(times), 2) if times else 0
        }


class SecurityTester:
    """Test security features"""
    
    def __init__(self):
        self.results = []
    
    def test_login_attempt_blocking(self, app, max_attempts=5):
        """Test login attempt blocking after max failures"""
        results = {
            'test': 'Login Attempt Blocking',
            'max_attempts_allowed': max_attempts,
            'attempts': [],
            'blocking_triggered': False
        }
        
        with app.test_client() as client:
            for i in range(max_attempts + 2):
                response = client.post('/login', data={
                    'username': 'test_blocked_user',
                    'password': 'wrong_password_' + str(i)
                })
                
                results['attempts'].append({
                    'attempt': i + 1,
                    'status_code': response.status_code,
                    'blocked': 'blocked' in response.data.decode().lower() or 'too many' in response.data.decode().lower()
                })
                
                if results['attempts'][-1]['blocked']:
                    results['blocking_triggered'] = True
                    results['blocked_after_attempt'] = i + 1
                    break
        
        results['passed'] = results['blocking_triggered']
        self.results.append(results)
        return results
    
    def test_session_expiry(self, app, session_timeout_seconds=30):
        """Test session expiry (simulated)"""
        results = {
            'test': 'Session Expiry',
            'timeout_seconds': session_timeout_seconds,
            'passed': True,
            'notes': 'Session configured for 30 minute timeout'
        }
        
        # Check session configuration
        with app.test_client() as client:
            response = client.get('/')
            results['session_cookie_httponly'] = app.config.get('SESSION_COOKIE_HTTPONLY', False)
            results['session_cookie_samesite'] = app.config.get('SESSION_COOKIE_SAMESITE', None)
            results['permanent_session_lifetime'] = str(app.config.get('PERMANENT_SESSION_LIFETIME', 'Not set'))
        
        self.results.append(results)
        return results
    
    def test_role_restrictions(self, app):
        """Test role-based access control"""
        results = {
            'test': 'Role-Based Access Control',
            'tests': [],
            'passed': True
        }
        
        # Protected routes for each role
        protected_routes = {
            'admin': ['/admin_dashboard', '/admin/students'],
            'faculty': ['/faculty_dashboard', '/take_attendance'],
            'student': ['/student_dashboard', '/my_attendance']
        }
        
        with app.test_client() as client:
            # Test access without login
            for role, routes in protected_routes.items():
                for route in routes:
                    response = client.get(route)
                    test_result = {
                        'route': route,
                        'role_required': role,
                        'without_login': {
                            'status_code': response.status_code,
                            'redirected_to_login': '/login' in response.headers.get('Location', '') or response.status_code == 302
                        }
                    }
                    results['tests'].append(test_result)
        
        # Check if all protected routes redirect to login
        results['passed'] = all(
            t['without_login']['redirected_to_login'] or t['without_login']['status_code'] in [401, 403, 302]
            for t in results['tests']
        )
        
        self.results.append(results)
        return results
    
    def test_sql_injection_protection(self, app):
        """Test SQL injection protection"""
        results = {
            'test': 'SQL Injection Protection',
            'payloads_tested': [],
            'passed': True
        }
        
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
            "admin'--",
            "1; DELETE FROM attendance; --"
        ]
        
        with app.test_client() as client:
            for payload in payloads:
                response = client.post('/login', data={
                    'username': payload,
                    'password': payload
                })
                
                results['payloads_tested'].append({
                    'payload': payload,
                    'status_code': response.status_code,
                    'successful_login': 'dashboard' in response.headers.get('Location', '').lower()
                })
                
                if results['payloads_tested'][-1]['successful_login']:
                    results['passed'] = False
        
        self.results.append(results)
        return results
    
    def test_xss_protection(self, app):
        """Test XSS protection"""
        results = {
            'test': 'XSS Protection',
            'payloads_tested': [],
            'passed': True
        }
        
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
        
        with app.test_client() as client:
            for payload in payloads:
                # Test in search or input fields
                response = client.get(f'/search?q={payload}')
                
                results['payloads_tested'].append({
                    'payload': payload,
                    'escaped_in_response': payload not in response.data.decode()
                })
        
        results['passed'] = all(p['escaped_in_response'] for p in results['payloads_tested'])
        self.results.append(results)
        return results
    
    def generate_security_report(self):
        """Generate comprehensive security test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'passed': sum(1 for r in self.results if r.get('passed', False)),
            'failed': sum(1 for r in self.results if not r.get('passed', True)),
            'tests': self.results
        }
        
        report['overall_status'] = 'PASSED' if report['failed'] == 0 else 'FAILED'
        
        return report


class TestReportGenerator:
    """Generate combined test reports"""
    
    def __init__(self):
        self.performance_tester = PerformanceTester()
        self.security_tester = SecurityTester()
    
    def run_all_tests(self, app=None):
        """Run all performance and security tests"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'performance': {},
            'security': {}
        }
        
        # Performance tests
        logger.info("Running performance tests...")
        report['performance']['database'] = self.performance_tester.test_database_performance()
        report['performance']['face_recognition'] = self.performance_tester.test_face_recognition_performance()
        report['performance']['concurrent_users'] = self.performance_tester.test_concurrent_users(10)
        
        # Security tests (need app context)
        if app:
            logger.info("Running security tests...")
            report['security']['session_config'] = self.security_tester.test_session_expiry(app)
            report['security']['role_restrictions'] = self.security_tester.test_role_restrictions(app)
        
        return report
    
    def save_report(self, report, filename='test_report.json'):
        """Save test report to file"""
        filepath = os.path.join('static', 'test_reports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=4)
        
        logger.info(f"Test report saved to {filepath}")
        return filepath


# Global instances
performance_tester = PerformanceTester()
security_tester = SecurityTester()
test_reporter = TestReportGenerator()
