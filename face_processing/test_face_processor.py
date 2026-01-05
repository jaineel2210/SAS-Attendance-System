import os
import sys
import logging
import base64
import cv2
import numpy as np
from enhanced_face_processor import EnhancedFaceProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_face_processor():
    """Test the EnhancedFaceProcessor functionality"""
    try:
        # Initialize the face processor
        logger.info("Initializing EnhancedFaceProcessor...")
        processor = EnhancedFaceProcessor()
        logger.info("Initialization successful")

        # Test image path (using a sample image from static/face_images if available)
        face_images_dir = os.path.join('static', 'face_images')
        if os.path.exists(face_images_dir) and os.listdir(face_images_dir):
            test_image_path = os.path.join(face_images_dir, os.listdir(face_images_dir)[0])
        else:
            logger.info("No existing face images found, will use webcam for testing")
            test_image_path = None

        # If no test image, capture from webcam
        if test_image_path is None:
            logger.info("Attempting to capture image from webcam...")
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("Could not open webcam")
                return False

            logger.info("Please look at the camera...")
            # Wait for a moment to let the camera adjust
            for _ in range(10):
                ret, frame = cap.read()
                if not ret:
                    logger.error("Could not read frame from webcam")
                    cap.release()
                    return False
                cv2.imshow('Camera Test', frame)
                cv2.waitKey(100)

            # Capture final frame
            ret, frame = cap.read()
            cap.release()
            cv2.destroyAllWindows()

            if not ret:
                logger.error("Failed to capture image from webcam")
                return False

            # Save test image
            os.makedirs('test_images', exist_ok=True)
            test_image_path = os.path.join('test_images', 'test_capture.jpg')
            cv2.imwrite(test_image_path, frame)
            logger.info(f"Saved test image to {test_image_path}")

        # Read and encode test image
        logger.info(f"Reading test image from {test_image_path}")
        with open(test_image_path, 'rb') as img_file:
            img_bytes = img_file.read()
        img_base64 = f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}"

        # Test image quality assessment
        logger.info("Testing image quality assessment...")
        img = cv2.imread(test_image_path)
        if img is None:
            logger.error("Failed to read test image")
            return False

        quality_ok, quality_message = processor.assess_image_quality(img)
        logger.info(f"Image quality assessment result: {quality_message}")

        # Test face encoding
        logger.info("Testing face encoding extraction...")
        encoding, error = processor.get_face_encoding(img)
        if error:
            logger.error(f"Face encoding error: {error}")
            return False
        logger.info("Successfully extracted face encoding")

        # Test face verification
        logger.info("Testing face verification...")
        success, user_data, message = processor.verify_face(img_base64)
        logger.info(f"Face verification result: {message}")
        if user_data:
            logger.info(f"User data: {user_data}")

        logger.info("All tests completed successfully")
        return True

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting face processor tests...")
    success = test_face_processor()
    if success:
        logger.info("All tests completed successfully")
        sys.exit(0)
    else:
        logger.error("Tests failed")
        sys.exit(1)
