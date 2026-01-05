import cv2
import numpy as np
import pickle
import os
from database.database import db
import logging
import base64
import io
from PIL import Image

logger = logging.getLogger(__name__)

class FaceProcessor:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_ids = []
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.load_known_faces()

    def load_known_faces(self):
        """Load all known face encodings from database"""
        try:
            query = "SELECT id, face_encoding FROM users WHERE face_encoding IS NOT NULL"
            results = db.execute_query(query)
            
            if results:
                self.known_face_encodings = []
                self.known_face_ids = []
                
                for user in results:
                    try:
                        # Decode face encoding from database
                        encoding = pickle.loads(base64.b64decode(user['face_encoding']))
                        self.known_face_encodings.append(encoding)
                        self.known_face_ids.append(user['id'])
                    except Exception as e:
                        logger.error(f"Error loading face encoding for user {user['id']}: {e}")
                
                logger.info(f"Loaded {len(self.known_face_encodings)} face encodings")
            
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")

    def detect_faces(self, image):
        """Detect faces in image using OpenCV"""
        try:
            # Convert to grayscale for face detection
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            return faces
        except Exception as e:
            logger.error(f"Error detecting faces: {e}")
            return []

    def extract_face_features(self, image):
        """Extract face features using OpenCV"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Detect faces
            faces = self.detect_faces(image)
            
            if len(faces) == 0:
                return None
            
            # Use the largest face
            face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = face
            
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Resize to standard size
            face_roi = cv2.resize(face_roi, (200, 200))
            
            # Compute LBP features
            lbp_features = self.compute_lbp_features(face_roi)
            
            return lbp_features
            
        except Exception as e:
            logger.error(f"Error extracting face features: {e}")
            return None

    def compute_lbp_features(self, face_image):
        """Compute Local Binary Pattern features"""
        try:
            # Simple LBP implementation
            height, width = face_image.shape
            lbp_image = np.zeros((height-2, width-2), dtype=np.uint8)
            
            for i in range(1, height-1):
                for j in range(1, width-1):
                    center = face_image[i, j]
                    code = 0
                    code |= (face_image[i-1, j-1] >= center) << 7
                    code |= (face_image[i-1, j] >= center) << 6
                    code |= (face_image[i-1, j+1] >= center) << 5
                    code |= (face_image[i, j+1] >= center) << 4
                    code |= (face_image[i+1, j+1] >= center) << 3
                    code |= (face_image[i+1, j] >= center) << 2
                    code |= (face_image[i+1, j-1] >= center) << 1
                    code |= (face_image[i, j-1] >= center) << 0
                    lbp_image[i-1, j-1] = code
            
            # Compute histogram
            hist, _ = np.histogram(lbp_image.ravel(), bins=256, range=(0, 256))
            return hist.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error computing LBP features: {e}")
            return None

    def recognize_face_from_camera(self):
        """Recognize face from camera feed using OpenCV"""
        try:
            logger.info("Starting camera-based face recognition")
            
            if not self.known_face_encodings:
                logger.warning("No known faces in database")
                return False, None, "No known faces in database"
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("Camera not available")
                return False, None, "Camera not available"
            
            recognized_user_id = None
            recognition_confidence = 0
            attempts = 0
            max_attempts = 60  # 60 frames to recognize
            
            logger.info("Camera opened successfully, starting recognition process...")
            print("Look at the camera for face recognition. Press ESC to cancel.")
            
            while attempts < max_attempts and recognized_user_id is None:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    break
                
                # Detect faces using OpenCV
                faces = self.detect_faces(frame)
                
                # Draw face rectangles
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Extract features from detected faces
                if len(faces) > 0:
                    # Use the largest face
                    face = max(faces, key=lambda x: x[2] * x[3])
                    x, y, w, h = face
                    
                    # Extract face region
                    face_roi = frame[y:y+h, x:x+w]
                    if face_roi.size > 0:
                        # Extract features
                        face_features = self.extract_face_features(frame)
                        if face_features is not None:
                            # Compare with known faces
                            correlations, matches = self.compare_faces(self.known_face_encodings, face_features, threshold=0.7)
                            
                            if any(matches):
                                best_match_index = np.argmax(correlations)
                                if matches[best_match_index]:
                                    recognized_user_id = self.known_face_ids[best_match_index]
                                    recognition_confidence = correlations[best_match_index]
                                    cv2.putText(frame, f"Recognized! Confidence: {recognition_confidence:.2f}", 
                                              (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                cv2.putText(frame, f"Attempts: {attempts}/{max_attempts}", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.imshow('Face Recognition', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key
                    break
                
                attempts += 1
            
            cap.release()
            cv2.destroyAllWindows()
            
            if recognized_user_id:
                # Get user details
                query = "SELECT * FROM users WHERE id = %s"
                user_result = db.execute_query(query, (recognized_user_id,))
                if user_result:
                    logger.info(f"✅ Face recognition successful: {user_result[0]['name']} ({user_result[0]['enrollment_no']}) with confidence {recognition_confidence:.2f}")
                    return True, user_result[0], f"Face recognized with {recognition_confidence:.2f} confidence"
                else:
                    logger.error(f"User {recognized_user_id} not found in database")
                    return False, None, "User not found in database"
            else:
                logger.warning("Face recognition failed - no match found")
                return False, None, "Face not recognized"
                
        except Exception as e:
            logger.error(f"Error in camera face recognition: {e}")
            return False, None, f"Error during recognition: {str(e)}"
    
    def verify_face_from_image(self, image_data, expected_user_id):
        """Verify that the face in the image matches the expected user"""
        try:
            if not self.known_face_encodings:
                return False, None, "No known faces in database"
            
            # Convert base64 image to OpenCV format
            image_bytes = base64.b64decode(image_data.split(',')[1])  # Remove data:image/jpeg;base64, prefix
            image = Image.open(io.BytesIO(image_bytes))
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Extract features from the image
            face_features = self.extract_face_features(opencv_image)
            if face_features is None:
                return False, None, "No face detected in the image"
            
            # Find the expected user's face encoding
            try:
                expected_user_index = self.known_face_ids.index(expected_user_id)
                expected_encoding = self.known_face_encodings[expected_user_index]
            except ValueError:
                return False, None, "User face encoding not found in database"
            
            # Compare with the expected user's face only
            correlation = cv2.compareHist(face_features, expected_encoding, cv2.HISTCMP_CORREL)
            threshold = 0.7  # Adjust this threshold as needed
            
            if correlation >= threshold:
                # Get user details
                query = "SELECT * FROM users WHERE id = %s"
                user_result = db.execute_query(query, (expected_user_id,))
                if user_result:
                    return True, user_result[0], f"Face verified with {correlation:.2f} confidence"
                else:
                    return False, None, "User not found in database"
            else:
                return False, None, f"Face verification failed. Confidence: {correlation:.2f} (threshold: {threshold})"
                
        except Exception as e:
            logger.error(f"Error in image face verification: {e}")
            return False, None, f"Error during verification: {str(e)}"

    def store_face_encoding(self, enrollment_no, captured_image_data):
        """Store face encoding for a new user during registration"""
        try:
            # Decode captured image
            image_data = base64.b64decode(captured_image_data.split(',')[1])
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Get face encoding from captured image using OpenCV
            face_features = self.extract_face_features(image_array)
            if face_features is None:
                return False, "No face detected in captured image. Please ensure your face is clearly visible and well-lit."
            
            # Store face encoding in database
            encoded_face = base64.b64encode(pickle.dumps(face_features)).decode('utf-8')
            query = "UPDATE users SET face_encoding = %s WHERE enrollment_no = %s"
            result = db.execute_query(query, (encoded_face, enrollment_no))
            
            if result:
                # Save the face image for reference
                os.makedirs('static/face_images', exist_ok=True)
                face_image_path = f'static/face_images/{enrollment_no}.jpg'
                image.save(face_image_path)
                
                self.load_known_faces()  # Reload known faces
                logger.info(f"Face encoding stored successfully for {enrollment_no}")
                return True, "Face encoding stored successfully"
            else:
                return False, "Failed to save face encoding to database"
                
        except Exception as e:
            logger.error(f"Error storing face encoding: {e}")
            return False, f"Error storing face encoding: {str(e)}"

    def verify_face_match(self, enrollment_no, captured_image_data):
        """Verify if captured image matches stored face encoding"""
        try:
            # Get stored face encoding
            query = "SELECT face_encoding FROM users WHERE enrollment_no = %s"
            result = db.execute_query(query, (enrollment_no,))
            
            if not result or not result[0]['face_encoding']:
                return False, "No stored face encoding found"
            
            stored_features = pickle.loads(base64.b64decode(result[0]['face_encoding']))
            
            # Decode captured image
            image_data = base64.b64decode(captured_image_data.split(',')[1])
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Get face features from captured image
            captured_features = self.extract_face_features(image_array)
            if captured_features is None:
                return False, "No face detected in captured image"
            
            # Compare features using correlation
            correlation = cv2.compareHist(stored_features, captured_features, cv2.HISTCMP_CORREL)
            
            if correlation > 0.7:  # Recognition threshold for correlation
                return True, f"Face verified with {correlation:.2f} confidence"
            else:
                return False, f"Face does not match stored encoding (correlation: {correlation:.2f})"
                
        except Exception as e:
            logger.error(f"Error verifying face match: {e}")
            return False, f"Error verifying face: {e}"

    def compare_faces(self, known_features, test_features, threshold=0.7):
        """Compare face features using histogram correlation"""
        try:
            correlations = []
            for features in known_features:
                correlation = cv2.compareHist(features, test_features, cv2.HISTCMP_CORREL)
                correlations.append(correlation)
            
            return correlations, [corr > threshold for corr in correlations]
        except Exception as e:
            logger.error(f"Error comparing faces: {e}")
            return [], []

# Initialize face processor
face_processor = FaceProcessor()