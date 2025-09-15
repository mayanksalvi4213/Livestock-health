"""
Image utility functions for validation and preprocessing
"""
import os
import logging
from PIL import Image
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('image_utils')

def validate_image(img_path):
    """
    Validate that an image file is not corrupted and can be processed
    Returns (is_valid, error_message)
    """
    try:
        # Check if file exists and is not empty
        if not os.path.exists(img_path):
            return False, "Image file does not exist"
            
        if os.path.getsize(img_path) == 0:
            return False, "Image file is empty"
            
        # Read file and check for null bytes
        with open(img_path, 'rb') as f:
            img_data = f.read()
            if img_data.startswith(b'\x00'):
                return False, "Image file contains null bytes and may be corrupted"
            
            if len(img_data) < 100:  # Most valid images are larger than 100 bytes
                return False, "Image file is too small to be valid"
        
        # Try to open and verify with PIL
        try:
            img = Image.open(img_path)
            img.verify()  # Verify it's a valid image
            img.close()
            
            # Reopen to check it can be properly loaded
            img = Image.open(img_path)
            img.load()
            img.close()
            
            return True, ""
        except Exception as e:
            error_msg = f"Invalid image format: {str(e)}"
            logger.error(f"Image validation failed: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error validating image: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def preprocess_for_model(img_path, target_size=(224, 224), normalize=True):
    """
    Preprocess an image for model prediction
    Returns (success, result) where result is either preprocessed image array or error message
    """
    try:
        # First validate the image
        is_valid, error_msg = validate_image(img_path)
        if not is_valid:
            return False, error_msg
        
        # Open and process the image
        img = Image.open(img_path).convert('RGB')
        img = img.resize(target_size)
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        # Normalize if requested
        if normalize:
            img_array = img_array / 255.0
            
        return True, img_array
        
    except Exception as e:
        error_msg = f"Error preprocessing image: {str(e)}"
        logger.error(error_msg)
        return False, error_msg 