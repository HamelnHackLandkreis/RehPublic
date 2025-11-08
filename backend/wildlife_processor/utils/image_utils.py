"""Image loading and preprocessing utilities."""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}


def is_supported_format(file_path: Path) -> bool:
    """Check if image format is supported.
    
    Args:
        file_path: Path to image file
        
    Returns:
        True if format is supported, False otherwise
    """
    return file_path.suffix.lower() in SUPPORTED_FORMATS


def load_image(file_path: Path) -> Optional[np.ndarray]:
    """Load image file as numpy array.
    
    Args:
        file_path: Path to image file
        
    Returns:
        Image as numpy array (H, W, C) or None if loading failed
    """
    try:
        if not file_path.exists():
            logger.error(f"Image file does not exist: {file_path}")
            return None
            
        if not is_supported_format(file_path):
            logger.warning(f"Unsupported image format: {file_path.suffix}")
            return None
        
        # Load image with PIL
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(img)
            
            logger.debug(f"Loaded image {file_path}: shape {img_array.shape}")
            return img_array
            
    except Exception as e:
        logger.error(f"Failed to load image {file_path}: {e}")
        return None


def preprocess_image_for_pytorch_wildlife(image: np.ndarray, max_size: int = 1280) -> np.ndarray:
    """Preprocess image for PyTorch Wildlife models.
    
    Args:
        image: Input image as numpy array (H, W, C)
        max_size: Maximum dimension size for resizing
        
    Returns:
        Preprocessed image array
    """
    try:
        # Ensure image is in correct format (H, W, C)
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError(f"Expected image shape (H, W, 3), got {image.shape}")
        
        # Resize if image is too large
        height, width = image.shape[:2]
        if max(height, width) > max_size:
            scale = max_size / max(height, width)
            new_height = int(height * scale)
            new_width = int(width * scale)
            
            # Use PIL for high-quality resizing
            pil_image = Image.fromarray(image)
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            image = np.array(pil_image)
            
            logger.debug(f"Resized image from ({width}, {height}) to ({new_width}, {new_height})")
        
        # Ensure data type is uint8
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)
        
        # PyTorch Wildlife expects (C, H, W) format for some models
        # We'll keep it as (H, W, C) and let the models handle conversion
        return image
        
    except Exception as e:
        logger.error(f"Image preprocessing failed: {e}")
        raise


def validate_image_file(file_path: Path) -> bool:
    """Validate that an image file can be loaded and processed.
    
    Args:
        file_path: Path to image file
        
    Returns:
        True if image is valid, False otherwise
    """
    try:
        if not file_path.exists():
            return False
            
        if not is_supported_format(file_path):
            return False
        
        # Try to load the image
        image = load_image(file_path)
        if image is None:
            return False
        
        # Check minimum size requirements
        height, width = image.shape[:2]
        if height < 32 or width < 32:
            logger.warning(f"Image too small: {width}x{height}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Image validation failed for {file_path}: {e}")
        return False


def get_image_info(file_path: Path) -> Optional[Tuple[int, int, str]]:
    """Get basic information about an image file.
    
    Args:
        file_path: Path to image file
        
    Returns:
        Tuple of (width, height, format) or None if failed
    """
    try:
        with Image.open(file_path) as img:
            return img.width, img.height, img.format
    except Exception as e:
        logger.error(f"Failed to get image info for {file_path}: {e}")
        return None