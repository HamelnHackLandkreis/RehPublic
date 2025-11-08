"""Main processing engine for wildlife camera images."""

import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from rich.progress import Progress, TaskID

from wildlife_processor.core.data_models import (
    DetectionResult,
    ImageMetadata,
    ProcessingResults,
)
from wildlife_processor.core.directory_scanner import DirectoryScanner
from wildlife_processor.core.models import ModelManager
from wildlife_processor.postprocessing.location_enricher import LocationEnricher
from wildlife_processor.utils.image_utils import load_image, preprocess_image_for_pytorch_wildlife

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
        self.location_enricher = LocationEnricher()
        
        # Processing statistics
        self.failed_images: List[str] = []
        self.processing_times: List[float] = []
    
    def process_directory(self, directory_path: Path, show_progress: bool = True) -> ProcessingResults:
        """Process a directory of wildlife camera images.
        
        Args:
            directory_path: Path to directory containing images
            show_progress: Whether to show progress indicators
            
        Returns:
            ProcessingResults object with all detection results and metadata
        """
        start_time = time.time()
        
        logger.info(f"Starting processing of directory: {directory_path}")
        
        # Validate models before processing
        if not self.model_manager.validate_models():
            raise RuntimeError("Model validation failed. Please check PyTorch Wildlife installation.")
        
        # Scan directory for images
        logger.info("Scanning directory for images...")
        image_metadata_list = self.directory_scanner.scan_directory(directory_path)
        
        if not image_metadata_list:
            logger.warning("No valid images found in directory")
            return self._create_empty_results()
        
        logger.info(f"Found {len(image_metadata_list)} images to process")
        
        # Process images with progress tracking
        detection_results = []
        self.failed_images = []
        self.processing_times = []
        
        if show_progress:
            with Progress() as progress:
                task = progress.add_task("Processing images...", total=len(image_metadata_list))
                
                for metadata in image_metadata_list:
                    result = self._process_single_image_with_timeout(metadata)
                    if result:
                        detection_results.append(result)
                    
                    progress.update(task, advance=1)
        else:
            for metadata in image_metadata_list:
                result = self._process_single_image_with_timeout(metadata)
                if result:
                    detection_results.append(result)
        
        # Enrich results with location metadata
        logger.info("Enriching results with location metadata...")
        enriched_results = self.location_enricher.enrich_results(detection_results)
        
        # Compile final results
        total_time = time.time() - start_time
        results = self._compile_results(
            enriched_results, 
            len(image_metadata_list), 
            total_time
        )
        
        logger.info(f"Processing completed in {total_time:.2f}s. "
                   f"Successful: {results.successful_detections}, "
                   f"Failed: {len(results.failed_images)}")
        
        return results
    
    def _process_single_image_with_timeout(self, metadata: ImageMetadata) -> DetectionResult:
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
            # Convert timestamp to string for species enhancement
            timestamp_str = metadata.timestamp.isoformat() if metadata.timestamp else None
            detections, processing_time = self.model_manager.process_image(processed_image, timestamp_str)
            
            total_time = time.time() - start_time
            
            # Check timeout
            if total_time > self.timeout_per_image:
                logger.warning(f"Image processing exceeded timeout ({self.timeout_per_image}s): {metadata.file_path}")
                self.failed_images.append(str(metadata.file_path))
                return None
            
            # Create detection result
            result = DetectionResult(
                image_path=metadata.file_path,
                camera_reference=metadata.camera_reference,
                timestamp=metadata.timestamp,
                detections=detections,
                processing_time=total_time,
                model_version=self.model_manager.get_model_info().detection_model
            )
            
            self.processing_times.append(total_time)
            logger.debug(f"Processed {metadata.file_path} in {total_time:.2f}s, found {len(detections)} detections")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image {metadata.file_path}: {e}")
            self.failed_images.append(str(metadata.file_path))
            return None
    
    def _compile_results(self, detection_results: List[DetectionResult], 
                        total_images: int, processing_duration: float) -> ProcessingResults:
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
        results_by_camera = dict(results_by_camera)
        
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
            model_info=model_info
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
            model_info=model_info
        )
    
    def get_processing_statistics(self) -> Dict[str, float]:
        """Get processing performance statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        if not self.processing_times:
            return {
                "average_time_per_image": 0.0,
                "min_time": 0.0,
                "max_time": 0.0,
                "total_images_processed": 0
            }
        
        return {
            "average_time_per_image": sum(self.processing_times) / len(self.processing_times),
            "min_time": min(self.processing_times),
            "max_time": max(self.processing_times),
            "total_images_processed": len(self.processing_times)
        }