"""Main processing engine for wildlife camera images."""

import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional


from wildlife_processor.core.data_models import (
    DetectionResult,
    ImageMetadata,
    ProcessingResults,
)
from wildlife_processor.core.directory_scanner import DirectoryScanner
from wildlife_processor.core.models import ModelManager
from wildlife_processor.utils.image_utils import (
    load_image,
    preprocess_image_for_pytorch_wildlife,
)

logger = logging.getLogger(__name__)


class WildlifeProcessor:
    """Main orchestration class for wildlife camera image processing."""

    def __init__(self, model_region: str = "general", timeout_per_image: float = 30.0):
        """Initialize wildlife processor.

        Args:
            model_region: Regional model to use for classification
            timeout_per_image: Maximum processing time per image in seconds
        """
        self.model_region = model_region
        self.timeout_per_image = timeout_per_image

        # Initialize components
        self.model_manager = ModelManager(model_region)
        self.directory_scanner = DirectoryScanner()

        # Processing statistics
        self.failed_images: List[str] = []

    def _process_single_image_with_timeout(
        self, metadata: ImageMetadata
    ) -> Optional[DetectionResult]:
        """Process a single image with timeout protection.

        Args:
            metadata: Image metadata containing file path and extracted info

        Returns:
            DetectionResult object or None if processing failed
        """
        try:
            start_time = time.time()

            # Load and preprocess image
            image = load_image(metadata.file_path)
            if image is None:
                logger.error(f"Failed to load image: {metadata.file_path}")
                self.failed_images.append(str(metadata.file_path))
                return None

            # Preprocess for PyTorch Wildlife
            processed_image = preprocess_image_for_pytorch_wildlife(image)

            # Run detection and classification with timeout check
            detections = self.model_manager.process_image(processed_image)

            total_time = time.time() - start_time

            # Check timeout
            if total_time > self.timeout_per_image:
                logger.warning(
                    f"Image processing exceeded timeout ({self.timeout_per_image}s): {metadata.file_path}"
                )
                self.failed_images.append(str(metadata.file_path))
                return None

            # Create detection result
            result = DetectionResult(
                image_path=metadata.file_path,
                camera_reference=metadata.camera_reference,
                timestamp=metadata.timestamp,
                detections=detections,
                model_version=self.model_manager.get_model_info().detection_model,
            )

            return result

        except Exception as e:
            logger.error(f"Error processing image {metadata.file_path}: {e}")
            self.failed_images.append(str(metadata.file_path))
            return None

    def _compile_results(
        self,
        detection_results: List[DetectionResult],
        total_images: int,
        processing_duration: float,
    ) -> ProcessingResults:
        """Compile detection results into final ProcessingResults object.

        Args:
            detection_results: List of successful detection results
            total_images: Total number of images processed
            processing_duration: Total processing time in seconds

        Returns:
            ProcessingResults object
        """
        # Group results by camera reference
        results_by_camera = defaultdict(list)
        for result in detection_results:
            results_by_camera[result.camera_reference].append(result)

        # Convert to regular dict
        results_by_camera = dict(results_by_camera)  # type: ignore[assignment]

        # Get model information
        model_info = self.model_manager.get_model_info()

        # Add scanner failed files to our failed list
        scanner_summary = self.directory_scanner.get_scan_summary()
        all_failed_files = self.failed_images + scanner_summary["failed_file_list"]

        return ProcessingResults(
            total_images=total_images,
            successful_detections=len(detection_results),
            failed_images=all_failed_files,
            processing_duration=processing_duration,
            results_by_camera=results_by_camera,
            model_info=model_info,
        )

    def _create_empty_results(self) -> ProcessingResults:
        """Create empty ProcessingResults for when no images are found.

        Returns:
            Empty ProcessingResults object
        """
        model_info = self.model_manager.get_model_info()

        return ProcessingResults(
            total_images=0,
            successful_detections=0,
            failed_images=[],
            processing_duration=0.0,
            results_by_camera={},
            model_info=model_info,
        )

    def get_processing_statistics(self) -> Dict[str, float]:
        """Get processing performance statistics.

        Returns:
            Dictionary with processing statistics
        """
        return {
            "total_images_processed": 0,
        }
