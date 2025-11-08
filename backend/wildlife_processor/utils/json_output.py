"""JSON output formatting and file handling for wildlife camera processing results."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from wildlife_processor.core.data_models import ProcessingResults

logger = logging.getLogger(__name__)


class JSONOutputHandler:
    """Handles JSON output formatting and file operations."""
    
    def __init__(self):
        """Initialize JSON output handler."""
        pass
    
    def save_results(self, results: ProcessingResults, output_path: Path) -> None:
        """Save processing results to JSON file.
        
        Args:
            results: ProcessingResults object to save
            output_path: Path where to save the JSON file
        """
        try:
            # Convert results to JSON-serializable format
            json_data = self._convert_results_to_json(results)
            
            # Validate JSON structure
            self._validate_json_structure(json_data)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save results to {output_path}: {e}")
            raise
    
    def _convert_results_to_json(self, results: ProcessingResults) -> Dict[str, Any]:
        """Convert ProcessingResults to JSON-serializable dictionary.
        
        Args:
            results: ProcessingResults object
            
        Returns:
            JSON-serializable dictionary
        """
        # Convert results by camera
        results_by_camera = {}
        
        for camera_ref, detection_results in results.results_by_camera.items():
            camera_results = []
            
            for detection_result in detection_results:
                # Convert detections
                detections = []
                for detection in detection_result.detections:
                    detection_dict = {
                        "species": detection.species,
                        "confidence": detection.confidence,
                        "bounding_box": {
                            "x": detection.bounding_box.x,
                            "y": detection.bounding_box.y,
                            "width": detection.bounding_box.width,
                            "height": detection.bounding_box.height
                        },
                        "classification_model": detection.classification_model,
                        "is_uncertain": detection.is_uncertain
                    }
                    
                    # Add European species enhancement metadata if available
                    if detection.alternative_species:
                        detection_dict["alternative_species"] = detection.alternative_species
                    
                    if detection.enhancement_metadata:
                        detection_dict["enhancement_metadata"] = detection.enhancement_metadata
                    detections.append(detection_dict)
                
                # Convert detection result
                result_dict = {
                    "image_path": str(detection_result.image_path),
                    "camera_reference": detection_result.camera_reference,
                    "timestamp": detection_result.timestamp.isoformat(),
                    "detections": detections,
                    "processing_time": detection_result.processing_time,
                    "model_version": detection_result.model_version
                }
                
                camera_results.append(result_dict)
            
            results_by_camera[camera_ref] = camera_results
        
        # Create processing metadata
        processing_metadata = {
            "total_images": results.total_images,
            "successful_detections": results.successful_detections,
            "failed_images": results.failed_images,
            "processing_duration": results.processing_duration,
            "model_info": {
                "detection_model": results.model_info.detection_model,
                "classification_model": results.model_info.classification_model,
                "region": results.model_info.region,
                "model_versions": results.model_info.model_versions
            },
            "generated_at": datetime.now().isoformat(),
            "format_version": "1.0"
        }
        
        # Combine into final structure
        json_data = {
            "processing_metadata": processing_metadata,
            "results_by_camera": results_by_camera
        }
        
        return json_data
    
    def _validate_json_structure(self, json_data: Dict[str, Any]) -> None:
        """Validate that JSON structure is well-formed.
        
        Args:
            json_data: Dictionary to validate
            
        Raises:
            ValueError: If JSON structure is invalid
        """
        required_top_level = ["processing_metadata", "results_by_camera"]
        
        for key in required_top_level:
            if key not in json_data:
                raise ValueError(f"Missing required top-level key: {key}")
        
        # Validate processing metadata
        metadata = json_data["processing_metadata"]
        required_metadata = [
            "total_images", "successful_detections", "failed_images",
            "processing_duration", "model_info", "generated_at"
        ]
        
        for key in required_metadata:
            if key not in metadata:
                raise ValueError(f"Missing required metadata key: {key}")
        
        # Validate model info
        model_info = metadata["model_info"]
        required_model_info = ["detection_model", "classification_model", "region"]
        
        for key in required_model_info:
            if key not in model_info:
                raise ValueError(f"Missing required model_info key: {key}")
        
        # Validate results structure
        results_by_camera = json_data["results_by_camera"]
        if not isinstance(results_by_camera, dict):
            raise ValueError("results_by_camera must be a dictionary")
        
        # Validate individual results
        for camera_ref, camera_results in results_by_camera.items():
            if not isinstance(camera_results, list):
                raise ValueError(f"Camera results for {camera_ref} must be a list")
            
            for i, result in enumerate(camera_results):
                self._validate_detection_result(result, f"{camera_ref}[{i}]")
    
    def _validate_detection_result(self, result: Dict[str, Any], context: str) -> None:
        """Validate individual detection result structure.
        
        Args:
            result: Detection result dictionary to validate
            context: Context string for error messages
        """
        required_fields = [
            "image_path", "camera_reference", "timestamp", 
            "detections", "processing_time", "model_version"
        ]
        
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field '{field}' in {context}")
        
        # Validate detections
        detections = result["detections"]
        if not isinstance(detections, list):
            raise ValueError(f"Detections must be a list in {context}")
        
        for j, detection in enumerate(detections):
            self._validate_detection(detection, f"{context}.detections[{j}]")
    
    def _validate_detection(self, detection: Dict[str, Any], context: str) -> None:
        """Validate individual detection structure.
        
        Args:
            detection: Detection dictionary to validate
            context: Context string for error messages
        """
        required_fields = [
            "species", "confidence", "bounding_box", 
            "classification_model", "is_uncertain"
        ]
        
        for field in required_fields:
            if field not in detection:
                raise ValueError(f"Missing required field '{field}' in {context}")
        
        # Validate bounding box
        bbox = detection["bounding_box"]
        if not isinstance(bbox, dict):
            raise ValueError(f"Bounding box must be a dictionary in {context}")
        
        required_bbox_fields = ["x", "y", "width", "height"]
        for field in required_bbox_fields:
            if field not in bbox:
                raise ValueError(f"Missing bounding box field '{field}' in {context}")
    
    def load_results(self, input_path: Path) -> Dict[str, Any]:
        """Load processing results from JSON file.
        
        Args:
            input_path: Path to JSON file to load
            
        Returns:
            Loaded JSON data as dictionary
        """
        try:
            if not input_path.exists():
                raise FileNotFoundError(f"JSON file does not exist: {input_path}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Validate loaded structure
            self._validate_json_structure(json_data)
            
            logger.info(f"Successfully loaded results from {input_path}")
            return json_data
            
        except Exception as e:
            logger.error(f"Failed to load results from {input_path}: {e}")
            raise
    
    def create_summary_report(self, json_data: Dict[str, Any]) -> str:
        """Create a text summary report from JSON results.
        
        Args:
            json_data: JSON results data
            
        Returns:
            Formatted text summary
        """
        metadata = json_data["processing_metadata"]
        results_by_camera = json_data["results_by_camera"]
        
        # Calculate statistics
        total_detections = sum(
            len(result["detections"])
            for camera_results in results_by_camera.values()
            for result in camera_results
        )
        
        species_counts = {}
        for camera_results in results_by_camera.values():
            for result in camera_results:
                for detection in result["detections"]:
                    species = detection["species"]
                    species_counts[species] = species_counts.get(species, 0) + 1
        
        # Generate report
        report_lines = [
            "Wildlife Camera Processing Summary",
            "=" * 40,
            "",
            f"Processing Date: {metadata['generated_at']}",
            f"Total Images: {metadata['total_images']}",
            f"Successful Detections: {metadata['successful_detections']}",
            f"Failed Images: {len(metadata['failed_images'])}",
            f"Processing Duration: {metadata['processing_duration']:.2f}s",
            f"Cameras: {len(results_by_camera)}",
            f"Total Animal Detections: {total_detections}",
            "",
            "Models Used:",
            f"  Detection: {metadata['model_info']['detection_model']}",
            f"  Classification: {metadata['model_info']['classification_model']}",
            f"  Region: {metadata['model_info']['region']}",
            "",
        ]
        
        if species_counts:
            report_lines.extend([
                "Species Detected:",
                "-" * 20,
            ])
            
            # Sort species by count (descending)
            sorted_species = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)
            for species, count in sorted_species:
                report_lines.append(f"  {species}: {count}")
            
            report_lines.append("")
        
        # Camera breakdown
        if results_by_camera:
            report_lines.extend([
                "Results by Camera:",
                "-" * 20,
            ])
            
            for camera_ref, camera_results in results_by_camera.items():
                camera_detections = sum(len(result["detections"]) for result in camera_results)
                report_lines.append(f"  {camera_ref}: {len(camera_results)} images, {camera_detections} detections")
        
        return "\n".join(report_lines)