#!/usr/bin/env python3
"""Validation script for wildlife camera processor installation."""

import sys
import logging
from pathlib import Path

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def validate_imports():
    """Validate that all required modules can be imported."""
    logger.info("Validating imports...")
    
    try:
        # Test core imports
        from wildlife_processor.core.data_models import DetectionResult, AnimalDetection
        from wildlife_processor.core.models import ModelManager
        from wildlife_processor.core.processor import WildlifeProcessor
        from wildlife_processor.core.directory_scanner import DirectoryScanner
        
        # Test CLI imports
        from wildlife_processor.cli.main import app
        
        # Test utility imports
        from wildlife_processor.utils.image_utils import load_image, is_supported_format
        from wildlife_processor.utils.json_output import JSONOutputHandler
        from wildlife_processor.utils.error_handler import ErrorHandler
        
        # Test config imports
        from wildlife_processor.config.models_config import list_available_regions
        
        # Test postprocessing imports
        from wildlife_processor.postprocessing.location_enricher import LocationEnricher
        
        logger.info("✓ All imports successful")
        return True
        
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def validate_dependencies():
    """Validate that external dependencies are available."""
    logger.info("Validating dependencies...")
    
    dependencies = [
        ('typer', 'Typer CLI framework'),
        ('rich', 'Rich terminal formatting'),
        ('PIL', 'Pillow image processing'),
        ('numpy', 'NumPy arrays'),
        ('dateutil', 'Python dateutil'),
    ]
    
    all_good = True
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            logger.info(f"✓ {description}")
        except ImportError:
            logger.error(f"✗ {description} not available")
            all_good = False
    
    # Test PyTorch Wildlife separately (may not be installed yet)
    try:
        import PytorchWildlife
        logger.info("✓ PyTorch Wildlife available")
    except ImportError:
        logger.warning("⚠ PyTorch Wildlife not available - install with: uv add PytorchWildlife")
        logger.info("  This is required for actual processing but not for basic validation")
    
    return all_good

def validate_cli():
    """Validate that CLI can be invoked."""
    logger.info("Validating CLI...")
    
    try:
        from wildlife_processor.cli.main import app
        
        # Test that we can create the app (basic validation)
        if app is not None:
            logger.info("✓ CLI app created successfully")
            return True
        else:
            logger.error("✗ CLI app is None")
            return False
            
    except Exception as e:
        logger.error(f"✗ CLI validation failed: {e}")
        return False

def validate_sample_structure():
    """Validate sample data structure."""
    logger.info("Validating sample data structure...")
    
    sample_dir = Path("sample_data")
    
    if not sample_dir.exists():
        logger.warning("⚠ Sample data directory not found")
        return False
    
    expected_cameras = ["forest_trail_1", "meadow_cam_2", "river_crossing"]
    
    for camera in expected_cameras:
        camera_dir = sample_dir / camera
        if camera_dir.exists():
            logger.info(f"✓ Found camera directory: {camera}")
        else:
            logger.warning(f"⚠ Missing camera directory: {camera}")
    
    return True

def main():
    """Run all validation checks."""
    logger.info("Wildlife Camera Processor - Installation Validation")
    logger.info("=" * 55)
    
    checks = [
        ("Import validation", validate_imports),
        ("Dependency validation", validate_dependencies),
        ("CLI validation", validate_cli),
        ("Sample structure validation", validate_sample_structure),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        logger.info(f"\n{check_name}:")
        logger.info("-" * len(check_name))
        
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"✗ {check_name} failed with exception: {e}")
            results.append((check_name, False))
    
    # Summary
    logger.info("\n" + "=" * 55)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 55)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        logger.info(f"{symbol} {check_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("🎉 All validations passed! The installation looks good.")
        logger.info("\nNext steps:")
        logger.info("1. Install PyTorch Wildlife: uv add PytorchWildlife")
        logger.info("2. Add wildlife camera images to sample_data directories")
        logger.info("3. Test processing: uv run wildlife-processor sample_data")
        return 0
    else:
        logger.error("❌ Some validations failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())