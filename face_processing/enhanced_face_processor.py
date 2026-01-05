import os
import sys
import logging
import pickle
import base64
import io
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check and import required dependencies"""
    missing_deps = []
    
    try:
        import numpy as np
        globals()['np'] = np
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import cv2
        globals()['cv2'] = cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import dlib
        globals()['dlib'] = dlib
    except ImportError:
        missing_deps.append("dlib")
    
    try:
        from PIL import Image
        globals()['Image'] = Image
    except ImportError:
        missing_deps.append("Pillow")
    
    if missing_deps:
        error_msg = f"Missing required dependencies: {', '.join(missing_deps)}"
        logger.error(error_msg)
        logger.error("Please install missing dependencies using:")
        logger.error(f"pip install {' '.join(missing_deps)}")
        sys.exit(1)
    
    logger.info("All required dependencies are installed")

# Check dependencies
check_dependencies()

# Import numpy, cv2, dlib, and PIL (already verified by check_dependencies)
import numpy as np
import cv2
import dlib
from PIL import Image

# Local imports
try:
    from database.database import db
except ImportError:
    logger.error("Failed to import database module. Make sure the database package is in your Python path")
    sys.exit(1)

logger = logging.getLogger(__name__)

class EnhancedFaceProcessor:
    def __init__(self):
        # Initialize face detection and facial landmarks models
        self.face_detector = dlib.get_frontal_face_detector()
        
        # Load face recognition model
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        shape_predictor_path = os.path.join(models_dir, 'shape_predictor_68_face_landmarks.dat')
        face_rec_model_path = os.path.join(models_dir, 'dlib_face_recognition_resnet_model_v1.dat')
        
        # Download models if they don't exist
        if not os.path.exists(shape_predictor_path):
            logger.info("Downloading face landmarks model...")
            # You would need to implement model download here
            
        if not os.path.exists(face_rec_model_path):
            logger.info("Downloading face recognition model...")
            # You would need to implement model download here
        
        self.shape_predictor = dlib.shape_predictor(shape_predictor_path)
        self.face_recognizer = dlib.face_recognition_model_v1(face_rec_model_path)
        
        # Load known faces
        self.known_face_encodings = []
        self.known_face_ids = []
        self.load_known_faces()
        
        # Quality assessment parameters - adjusted for more lenient detection
        self.min_face_size = 60  # Reduced minimum face width/height
        self.brightness_range = (30, 240)  # Wider acceptable brightness range
        self.min_sharpness = 30  # Reduced minimum sharpness threshold
        self.center_tolerance = 0.3  # Increased tolerance for face centering (30% of image size)
        
        logger.info("Enhanced Face Processor initialized successfully")

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
                        encoding = pickle.loads(base64.b64decode(user['face_encoding']))
                        self.known_face_encodings.append(encoding)
                        self.known_face_ids.append(user['id'])
                    except Exception as e:
                        logger.error(f"Error loading face encoding for user {user['id']}: {e}")
                
                logger.info(f"Loaded {len(self.known_face_encodings)} face encodings")
            
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")

    def assess_image_quality(self, image):
        """Assess the quality of the captured image"""
        try:
            # Convert to grayscale for some calculations
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Check brightness with more detailed feedback
            brightness = np.mean(gray)
            logger.info(f"Image brightness: {brightness:.1f} (acceptable range: {self.brightness_range})")
            if not (self.brightness_range[0] <= brightness <= self.brightness_range[1]):
                if brightness < self.brightness_range[0]:
                    return False, "Image is too dark. Please add more light."
                else:
                    return False, "Image is too bright. Please reduce lighting."
            
            # Check contrast with more detailed feedback
            contrast = np.std(gray)
            logger.info(f"Image contrast: {contrast:.1f}")
            if contrast < 30:
                return False, "Image contrast is too low. Please ensure good lighting conditions."
            
            # Check sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            logger.info(f"Image sharpness: {laplacian_var:.1f}")
            if laplacian_var < self.min_sharpness:
                return False, "Image is blurry. Please hold still and ensure good focus."
            
            # Detect faces with detailed feedback
            faces = self.face_detector(image)
            if len(faces) == 0:
                return False, "No face detected. Please look directly at the camera."
            if len(faces) > 1:
                return False, "Multiple faces detected. Please ensure only one face is visible."
            
            # Check face size and position with detailed feedback
            face = faces[0]
            face_width = face.right() - face.left()
            face_height = face.bottom() - face.top()
            
            logger.info(f"Face size: {face_width}x{face_height} (minimum: {self.min_face_size})")
            if face_width < self.min_face_size or face_height < self.min_face_size:
                return False, "Face is too small. Please move closer to the camera."
            
            # Check if face is centered with more tolerance
            center_x = (face.left() + face.right()) / 2
            center_y = (face.top() + face.bottom()) / 2
            img_center_x = image.shape[1] / 2
            img_center_y = image.shape[0] / 2
            
            x_offset = abs(center_x - img_center_x) / image.shape[1]
            y_offset = abs(center_y - img_center_y) / image.shape[0]
            
            logger.info(f"Face offset from center: {x_offset:.2%} horizontal, {y_offset:.2%} vertical")
            if x_offset > self.center_tolerance or y_offset > self.center_tolerance:
                if x_offset > self.center_tolerance:
                    return False, "Please center your face horizontally in the frame."
                else:
                    return False, "Please center your face vertically in the frame."
            
            return True, "Image quality checks passed"
            
        except Exception as e:
            logger.error(f"Error assessing image quality: {e}")
            return False, f"Error assessing image quality: {str(e)}"

    def get_face_encoding(self, image):
        """Extract face encoding from image"""
        try:
            # Detect faces
            faces = self.face_detector(image)
            if len(faces) == 0:
                return None, "No face detected"
            if len(faces) > 1:
                return None, "Multiple faces detected"
            
            # Get facial landmarks
            shape = self.shape_predictor(image, faces[0])
            
            # Get face encoding
            face_encoding = np.array(self.face_recognizer.compute_face_descriptor(image, shape))
            
            return face_encoding, None
            
        except Exception as e:
            logger.error(f"Error getting face encoding: {e}")
            return None, f"Error getting face encoding: {str(e)}"

    def verify_face(self, image_data, expected_user_id=None):
        """Verify face from image data"""
        try:
            # Convert base64 to image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(io.BytesIO(image_bytes))
            image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Check image quality
            quality_ok, quality_message = self.assess_image_quality(image_array)
            if not quality_ok:
                return False, None, quality_message
            
            # Get face encoding
            face_encoding, error = self.get_face_encoding(image_array)
            if error:
                return False, None, error
            
            if expected_user_id:
                # Verify against specific user
                try:
                    user_index = self.known_face_ids.index(expected_user_id)
                    distance = np.linalg.norm(face_encoding - self.known_face_encodings[user_index])
                    if distance < 0.6:  # Adjust threshold as needed
                        return True, {"id": expected_user_id}, f"Face verified with confidence {1 - distance:.2%}"
                    return False, None, f"Face verification failed (confidence: {1 - distance:.2%})"
                except ValueError:
                    return False, None, "User's face encoding not found"
            else:
                # Find best match among all known faces
                if not self.known_face_encodings:
                    return False, None, "No known faces in database"
                
                distances = [np.linalg.norm(face_encoding - enc) for enc in self.known_face_encodings]
                best_match_index = np.argmin(distances)
                best_match_distance = distances[best_match_index]
                
                if best_match_distance < 0.6:  # Adjust threshold as needed
                    user_id = self.known_face_ids[best_match_index]
                    # Get user details
                    query = "SELECT * FROM users WHERE id = %s"
                    user_result = db.execute_query(query, (user_id,))
                    if user_result:
                        return True, user_result[0], f"Face recognized with confidence {1 - best_match_distance:.2%}"
                
                return False, None, "No matching face found"
                
        except Exception as e:
            logger.error(f"Error in face verification: {e}")
            return False, None, f"Error during verification: {str(e)}"

    def store_face_encoding(self, enrollment_no, image_data):
        """Store face encoding for a new user"""
        try:
            # Convert base64 to image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(io.BytesIO(image_bytes))
            image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Check image quality
            quality_ok, quality_message = self.assess_image_quality(image_array)
            if not quality_ok:
                return False, quality_message
            
            # Get face encoding
            face_encoding, error = self.get_face_encoding(image_array)
            if error:
                return False, error
            
            # Store encoding in database
            encoded_face = base64.b64encode(pickle.dumps(face_encoding)).decode('utf-8')
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

# Initialize face processor
enhanced_face_processor = EnhancedFaceProcessor()
