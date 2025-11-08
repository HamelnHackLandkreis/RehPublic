#!/usr/bin/env python3
"""Test script for end-to-end workflow validation."""

import logging
import tempfile
from pathlib import Path
from PIL import Image
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_test_image(output_path: Path, width: int = 640, height: int = 480):
    """Create a simple test image for processing.
    
    Args:
        output_path: Where to save the test image
        width: Image width
        height: Image height
    """
    # Create a simple test image with random noise
    # This simulates a wildlife camera image
    image_array = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    
    # Add some structure to make it more realistic
    # Add a "ground" area (brown-ish)
    image_array[height//2:, :] = np.random.randint(80, 120, (height//2, width, 3), dtype=np.uint8)
    
    # Add a "sky" area (blue-ish)
    image_array[:height//4, :] = np.random.randint(100, 180, (height//4, width, 3), dtype=np.uint8)
    image_array[:height//4, :, 2] = np.random.randint(150, 255, (height//4, width), dtype=np.uint8)  # More blue
    
    # Add some "vegetation" (green-ish)
    vegetation_mask = np.random.random((height, width)) > 0.7
    image_array[vegetation_mask, 1] = np.random.randint(100, 200, np.sum(vegetation_mask), dtype=np.uint8)  # More green
    
    # Convert to PIL Image and save
    pil_image = Image.fromarray(image_array)
    pil_image.save(output_path, 'JPEG', quality=85)
    
    logger.info(f"Created test image: {output_path}")

def create_test_data_structure(base_dir: Path):
    """Create a test data structure with sample images.
    
    Args:
        base_dir: Base directory for test data
    """
    logger.info(f"Creating test data structure in: {base_dir}")
    
    # Define test structure
    test_structure = {
        "test_camera_1": [
            "2024-01-15_08-30",
            "2024-01-15_14-22"
        ],
        "test_camera_2": [
            "2024-01-16_06-45",
            "2024-01-16_18-30"
        ]
    }
    
    image_count = 0
    
    for camera_name, datetime_dirs in test_structure.items():
        for datetime_dir in datetime_dirs:
            # Create directory structure
            dir_path = base_dir / camera_name / datetime_dir
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Create 1-2 test images per directory
            num_images = np.random.randint(1, 3)
            
            for i in range(num_images):
                image_name = f"IMG_{image_count:03d}.jpg"
                image_path = dir_path / image_name
                
                create_test_image(image_path)
                image_count += 1
    
    logger.info(f"Created {image_count} test images in test data structure")
    return image_count

def test_directory_scanner():
    """Test the directory scanner component."""
    logger.info("Testing directory scanner...")
    
    try:
        from wildlife_processor.core.directory_scanner import DirectoryScanner
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test data
            create_test_data_structure(temp_path)
            
            # Test scanner
            scanner = DirectoryScanner()
            metadata_list = scanner.scan_directory(temp_path)
            
            logger.info(f"✓ Scanner found {len(metadata_list)} images")
            
            # Validate metadata
            for metadata in metadata_list[:3]:  # Check first 3
                logger.info(f"  - {metadata.camera_reference}: {metadata.file_path.name} at {metadata.timestamp}")
            
            return len(metadata_list) > 0
            
    except Exception as e:
        logger.error(f"✗ Directory scanner test failed: {e}")
        return False

def test_image_utils():
    """Test image utility functions."""
    logger.info("Testing image utilities...")
    
    try:
        from wildlife_processor.utils.image_utils import load_image, is_supported_format, validate_image_file
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a test image
            test_image_path = temp_path / "test.jpg"
            create_test_image(test_image_path)
            
            # Test format checking
            if not is_supported_format(test_image_path):
                logger.error("✗ Format check failed for JPEG")
                return False
            
            # Test image loading
            image_array = load_image(test_image_path)
            if image_array is None:
                logger.error("✗ Image loading failed")
                return False
            
            # Test validation
            if not validate_image_file(test_image_path):
                logger.error("✗ Image validation failed")
                return False
            
            logger.info(f"✓ Image utilities working (loaded {image_array.shape} image)")
            return True
            
    except Exception as e:
        logger.error(f"✗ Image utilities test failed: {e}")
        return False

def test_json_output():
    """Test JSON output functionality."""
    logger.info("Testing JSON output...")
    
    try:
        from wildlife_processor.utils.json_output import JSONOutputHandler
        from wildlife_processor.core.data_models import ProcessingResults, ModelInfo
        
        # Create mock results
        model_info = ModelInfo(
            detection_model="TestDetector",
            classification_model="TestClassifier",
            region="test",
            model_versions={"detection": "1.0", "classification": "1.0"}
        )
        
        results = ProcessingResults(
            total_images=5,
            successful_detections=4,
            failed_images=["failed.jpg"],
            processing_duration=10.5,
            results_by_camera={},
            model_info=model_info
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_results.json"
            
            handler = JSONOutputHandler()
            handler.save_results(results, output_path)
            
            if not output_path.exists():
                logger.error("✗ JSON file was not created")
                return False
            
            # Test loading
            loaded_data = handler.load_results(output_path)
            
            if loaded_data["processing_metadata"]["total_images"] != 5:
                logger.error("✗ JSON data validation failed")
                return False
            
            logger.info("✓ JSON output working correctly")
            return True
            
    except Exception as e:
        logger.error(f"✗ JSON output test failed: {e}")
        return False

def test_model_config():
    """Test model configuration."""
    logger.info("Testing model configuration...")
    
    try:
        from wildlife_processor.config.models_config import (
            list_available_regions, 
            validate_region, 
            get_model_config
        )
        
        # Test region listing
        regions = list_available_regions()
        if not regions:
            logger.error("✗ No regions available")
            return False
        
        # Test validation
        if not validate_region("general"):
            logger.error("✗ Region validation failed for 'general'")
            return False
        
        # Test config retrieval
        config = get_model_config("general")
        if not config.region == "general":
            logger.error("✗ Config retrieval failed")
            return False
        
        logger.info(f"✓ Model config working (found {len(regions)} regions)")
        return True
        
    except Exception as e:
        logger.error(f"✗ Model config test failed: {e}")
        return False

def main():
    """Run end-to-end workflow validation tests."""
    logger.info("Wildlife Camera Processor - Workflow Validation")
    logger.info("=" * 50)
    
    tests = [
        ("Model Configuration", test_model_config),
        ("Image Utilities", test_image_utils),
        ("Directory Scanner", test_directory_scanner),
        ("JSON Output", test_json_output),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{test_name}:")
        logger.info("-" * len(test_name))
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("WORKFLOW VALIDATION SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        logger.info(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All workflow tests passed!")
        logger.info("\nThe core components are working correctly.")
        logger.info("Note: Full end-to-end testing requires PyTorch Wildlife installation.")
        return 0
    else:
        logger.error("❌ Some workflow tests failed.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())