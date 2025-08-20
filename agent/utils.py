import cv2
import numpy as np
from PIL import Image
import logging
from typing import Union


def compute_iou(image1_path: str, image2_path: str, threshold: int = 128) -> float:
    try:
        # Load images
        img1 = load_and_preprocess_image(image1_path)
        img2 = load_and_preprocess_image(image2_path)
        
        # Ensure images are the same size
        if img1.shape != img2.shape:
            # Resize img2 to match img1
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # Convert to binary masks
        mask1 = (img1 > threshold).astype(np.uint8)
        mask2 = (img2 > threshold).astype(np.uint8)
        
        # Calculate intersection and union
        intersection = np.logical_and(mask1, mask2).sum()
        union = np.logical_or(mask1, mask2).sum()
        
        # Calculate IoU
        if union == 0:
            return 1.0 if intersection == 0 else 0.0
        
        iou = intersection / union
        return float(iou)
        
    except Exception as e:
        logging.error(f"Error calculating IoU: {e}")
        return 0.0


def load_and_preprocess_image(image_path: str) -> np.ndarray:
    # Try loading with PIL first
    try:
        img = Image.open(image_path)
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Convert to numpy array
        img_array = np.array(img)
        # Convert to grayscale
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        return img_array
    except Exception as e1:
        # Fallback to OpenCV
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            return img
        except Exception as e2:
            logging.error(f"Failed to load image {image_path}: {e1}, {e2}")
            raise