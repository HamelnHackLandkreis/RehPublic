"""Centralized error handling system for wildlife camera processor."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for consistent error processing across the application."""
    
    def __init__(self):
        """Initialize error handler."""
        self.error_counts: Dict[str, int] = {
            'image_errors': 0,
            'model_errors': 0,
            'directory_errors': 0,
            'output_errors': 0,
            'timeout_errors': 0
        }
        self.error_messages: List[str] = []
    
    def handle_image_error(self, image_path: Path, error: Exception) -> None:
        """Handle image processing errors.
        
        Args:
            image_path: Path to the problematic image
            error: Exception that occurred
        """
        self.error_counts['image_errors'] += 1
        
        error_msg = f"Image processing failed for {image_path}: {error}"
        self.error_messages.append(error_msg)
        
        logger.error(error_msg)
        
        # Provide specific guidance based on error type
        if "corrupted" in str(error).lower() or "cannot identify image file" in str(error).lower():
            logger.warning(f"Image file appears to be corrupted: {image_path}")
            logger.info("Suggestion: Check if the image file is valid and not truncated")
        elif "permission" in str(error).lower():
            logger.warning(f"Permission denied accessing image: {image_path}")
            logger.info("Suggestion: Check file permissions and ensure read access")
        elif "memory" in str(error).lower() or "out of memory" in str(error).lower():
            logger.warning(f"Memory error processing image: {image_path}")
            logger.info("Suggestion: Try processing smaller batches or reduce image resolution")
    
    def handle_model_error(self, error: Exception) -> None:
        """Handle model loading and inference errors.
        
        Args:
            error: Exception that occurred
        """
        self.error_counts['model_errors'] += 1
        
        error_msg = f"Model error: {error}"
        self.error_messages.append(error_msg)
        
        logger.error(error_msg)
        
        # Provide specific guidance based on error type
        error_str = str(error).lower()
        
        if "no module named" in error_str or "import" in error_str:
            logger.error("PyTorch Wildlife is not properly installed")
            logger.info("Installation instructions:")
            logger.info("  1. Install with UV: uv add PytorchWildlife")
            logger.info("  2. Or with pip: pip install PytorchWildlife")
            logger.info("  3. Ensure PyTorch is installed: uv add torch torchvision")
        elif "cuda" in error_str or "gpu" in error_str:
            logger.warning("GPU/CUDA error detected, falling back to CPU processing")
            logger.info("This may result in slower processing but should still work")
        elif "download" in error_str or "network" in error_str or "connection" in error_str:
            logger.warning("Network error downloading model weights")
            logger.info("Suggestions:")
            logger.info("  1. Check internet connection")
            logger.info("  2. Try again later if servers are busy")
            logger.info("  3. Check firewall settings")
        elif "memory" in error_str or "out of memory" in error_str:
            logger.warning("Insufficient memory for model loading")
            logger.info("Suggestions:")
            logger.info("  1. Close other applications to free memory")
            logger.info("  2. Try processing smaller image batches")
            logger.info("  3. Use CPU instead of GPU if applicable")
    
    def handle_directory_error(self, directory_path: Path, error: Exception) -> None:
        """Handle directory access and scanning errors.
        
        Args:
            directory_path: Path to the problematic directory
            error: Exception that occurred
        """
        self.error_counts['directory_errors'] += 1
        
        error_msg = f"Directory error for {directory_path}: {error}"
        self.error_messages.append(error_msg)
        
        logger.error(error_msg)
        
        # Provide specific guidance
        error_str = str(error).lower()
        
        if "does not exist" in error_str or "no such file" in error_str:
            logger.error(f"Directory does not exist: {directory_path}")
            logger.info("Suggestion: Check the directory path and ensure it exists")
        elif "permission" in error_str:
            logger.error(f"Permission denied accessing directory: {directory_path}")
            logger.info("Suggestion: Check directory permissions and ensure read access")
        elif "not a directory" in error_str:
            logger.error(f"Path is not a directory: {directory_path}")
            logger.info("Suggestion: Ensure the path points to a directory, not a file")
        else:
            logger.info("Suggestions:")
            logger.info("  1. Verify the directory path is correct")
            logger.info("  2. Check that you have read permissions")
            logger.info("  3. Ensure the directory contains wildlife camera images")
    
    def handle_output_error(self, output_path: Path, error: Exception) -> None:
        """Handle output file writing errors.
        
        Args:
            output_path: Path where output was attempted
            error: Exception that occurred
        """
        self.error_counts['output_errors'] += 1
        
        error_msg = f"Output error for {output_path}: {error}"
        self.error_messages.append(error_msg)
        
        logger.error(error_msg)
        
        # Provide specific guidance
        error_str = str(error).lower()
        
        if "permission" in error_str:
            logger.error(f"Permission denied writing to: {output_path}")
            logger.info("Suggestions:")
            logger.info("  1. Check write permissions for the output directory")
            logger.info("  2. Try writing to a different location (e.g., your home directory)")
            logger.info("  3. Run with appropriate permissions")
        elif "no space" in error_str or "disk full" in error_str:
            logger.error("Insufficient disk space for output file")
            logger.info("Suggestions:")
            logger.info("  1. Free up disk space")
            logger.info("  2. Choose a different output location")
            logger.info("  3. Process fewer images at once")
        elif "directory" in error_str:
            logger.error(f"Output directory does not exist: {output_path.parent}")
            logger.info("Suggestion: The output directory will be created automatically")
        else:
            logger.info("Suggestions:")
            logger.info("  1. Check that the output path is valid")
            logger.info("  2. Ensure you have write permissions")
            logger.info("  3. Try a different output location")
    
    def handle_timeout(self, image_path: Path, timeout_seconds: float) -> None:
        """Handle processing timeout errors.
        
        Args:
            image_path: Path to the image that timed out
            timeout_seconds: Timeout duration that was exceeded
        """
        self.error_counts['timeout_errors'] += 1
        
        error_msg = f"Processing timeout ({timeout_seconds}s) for {image_path}"
        self.error_messages.append(error_msg)
        
        logger.warning(error_msg)
        logger.info("Suggestions:")
        logger.info("  1. Increase timeout with --timeout parameter")
        logger.info("  2. Check if image is unusually large or complex")
        logger.info("  3. Ensure system has sufficient resources")
    
    def get_error_summary(self) -> Dict[str, any]:
        """Get summary of all errors encountered.
        
        Returns:
            Dictionary with error statistics and messages
        """
        total_errors = sum(self.error_counts.values())
        
        return {
            'total_errors': total_errors,
            'error_counts': self.error_counts.copy(),
            'error_messages': self.error_messages.copy(),
            'has_errors': total_errors > 0
        }
    
    def get_troubleshooting_guide(self) -> str:
        """Get comprehensive troubleshooting guide based on encountered errors.
        
        Returns:
            Formatted troubleshooting guide string
        """
        guide_lines = [
            "Wildlife Camera Processor - Troubleshooting Guide",
            "=" * 50,
            ""
        ]
        
        if self.error_counts['model_errors'] > 0:
            guide_lines.extend([
                "Model Errors:",
                "- Ensure PyTorch Wildlife is installed: uv add PytorchWildlife",
                "- Check internet connection for model downloads",
                "- Verify PyTorch installation: uv add torch torchvision",
                "- Try CPU processing if GPU errors occur",
                ""
            ])
        
        if self.error_counts['image_errors'] > 0:
            guide_lines.extend([
                "Image Processing Errors:",
                "- Check image file integrity (not corrupted)",
                "- Ensure supported formats: JPEG, PNG, TIFF",
                "- Verify file permissions (read access)",
                "- Try processing smaller image batches",
                ""
            ])
        
        if self.error_counts['directory_errors'] > 0:
            guide_lines.extend([
                "Directory Access Errors:",
                "- Verify directory path exists and is correct",
                "- Check directory permissions (read access)",
                "- Ensure path points to a directory, not a file",
                "- Confirm directory contains wildlife camera images",
                ""
            ])
        
        if self.error_counts['output_errors'] > 0:
            guide_lines.extend([
                "Output File Errors:",
                "- Check write permissions for output directory",
                "- Ensure sufficient disk space",
                "- Try different output location",
                "- Verify output path is valid",
                ""
            ])
        
        if self.error_counts['timeout_errors'] > 0:
            guide_lines.extend([
                "Timeout Errors:",
                "- Increase timeout with --timeout parameter",
                "- Check system resources (CPU, memory)",
                "- Process smaller image batches",
                "- Verify images are not unusually large",
                ""
            ])
        
        guide_lines.extend([
            "General Troubleshooting:",
            "- Run with --verbose for detailed logging",
            "- Use 'wildlife-processor validate-setup' to test installation",
            "- Check system requirements and available memory",
            "- Try processing a single image first to isolate issues",
            ""
        ])
        
        return "\n".join(guide_lines)
    
    def reset_errors(self) -> None:
        """Reset error counters and messages."""
        self.error_counts = {key: 0 for key in self.error_counts}
        self.error_messages = []