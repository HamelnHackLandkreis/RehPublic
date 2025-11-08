"""PyTorch Wildlife model management for detection and classification."""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Optional PyTorch Wildlife imports
try:
    from PytorchWildlife.models import detection as pw_detection
    from PytorchWildlife.models import classification as pw_classification
    PYTORCH_WILDLIFE_AVAILABLE = True
except ImportError:
    pw_detection = None
    pw_classification = None
    PYTORCH_WILDLIFE_AVAILABLE = False

from wildlife_processor.config.models_config import get_model_config
from wildlife_processor.core.data_models import (
    AnimalDetection,
    BoundingBox,
    ModelConfig,
    ModelInfo,
)
from wildlife_processor.core.species_mapper import SpeciesMapper

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages PyTorch Wildlife models for detection and classification."""
    
    def __init__(self, region: str = "general"):
        """Initialize model manager with specified region.
        
        Args:
            region: Regional model to use (amazon, europe, hamelin, general)
        """
        self.region = region
        self.model_config = get_model_config(region)
        self.detection_model: Optional[Any] = None
        self.classification_model: Optional[Any] = None
        self._model_versions: Dict[str, str] = {}
        
        # Initialize European species mapper for enhancement
        self.species_mapper = SpeciesMapper(region)
        self.enable_european_enhancement = region.lower() in ['europe', 'european']
        
    def load_detection_model(self) -> None:
        """Load MegaDetectorV6 for animal detection."""
        if not PYTORCH_WILDLIFE_AVAILABLE:
            raise RuntimeError("PyTorch Wildlife is not installed. Install with: uv add PytorchWildlife")
        
        try:
            logger.info("Loading MegaDetectorV6...")
            # Initialize with valid MDV6-yolov9-c version
            self.detection_model = pw_detection.MegaDetectorV6(
                weights=None, 
                device='cpu', 
                pretrained=True, 
                version='MDV6-yolov9-c'
            )
            self._model_versions["detection"] = "MegaDetectorV6-yolov9c"
            logger.info("MegaDetectorV6 loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load MegaDetectorV6: {e}")
            raise RuntimeError(f"Could not load detection model: {e}")
    
    def load_classification_model(self) -> None:
        """Load regional classification model."""
        if not PYTORCH_WILDLIFE_AVAILABLE:
            raise RuntimeError("PyTorch Wildlife is not installed. Install with: uv add PytorchWildlife")
        
        try:
            logger.info(f"Loading classification model for region: {self.region}")
            
            # Load the appropriate classification model based on region
            if self.model_config.classification_model_class == "AI4GAmazonRainforest":
                self.classification_model = pw_classification.AI4GAmazonRainforest()
                self._model_versions["classification"] = "AI4GAmazonRainforest"
            else:
                # Fallback to Amazon model for unsupported regions
                logger.warning(f"Model {self.model_config.classification_model_class} not available, using AI4GAmazonRainforest")
                self.classification_model = pw_classification.AI4GAmazonRainforest()
                self._model_versions["classification"] = "AI4GAmazonRainforest"
                
            logger.info(f"Classification model loaded: {self._model_versions['classification']}")
        except Exception as e:
            logger.error(f"Failed to load classification model: {e}")
            raise RuntimeError(f"Could not load classification model: {e}")
    
    def ensure_models_loaded(self) -> None:
        """Ensure both detection and classification models are loaded."""
        if self.detection_model is None:
            self.load_detection_model()
        if self.classification_model is None:
            self.load_classification_model()
    
    def run_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """Run animal detection on image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Detection results from MegaDetectorV6
        """
        if self.detection_model is None:
            raise RuntimeError("Detection model not loaded")
            
        try:
            start_time = time.time()
            result = self.detection_model.single_image_detection(image)
            processing_time = time.time() - start_time
            
            logger.debug(f"Detection completed in {processing_time:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            raise RuntimeError(f"Detection inference failed: {e}")
    
    def run_classification(self, image: np.ndarray) -> Dict[str, Any]:
        """Run animal classification on image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Classification results from regional model
        """
        if self.classification_model is None:
            raise RuntimeError("Classification model not loaded")
            
        try:
            start_time = time.time()
            result = self.classification_model.single_image_classification(image)
            processing_time = time.time() - start_time
            
            logger.debug(f"Classification completed in {processing_time:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise RuntimeError(f"Classification inference failed: {e}")
    
    def process_image(self, image: np.ndarray, timestamp: Optional[str] = None) -> Tuple[List[AnimalDetection], float]:
        """Process image with both detection and classification.
        
        Args:
            image: Input image as numpy array
            timestamp: Optional timestamp for temporal context in species enhancement
            
        Returns:
            Tuple of (list of animal detections, total processing time)
        """
        self.ensure_models_loaded()
        
        start_time = time.time()
        detections = []
        
        try:
            # Run detection first
            detection_result = self.run_detection(image)
            
            # Run enhanced classification pipeline
            logger.debug(f"Running classification pipeline for European enhancement (enabled: {self.enable_european_enhancement})")
            classification_result = self.run_classification_pipeline(image, detection_result, timestamp)
            
            # Combine results
            detections = self._combine_results(detection_result, classification_result, image, timestamp)
            
            total_time = time.time() - start_time
            logger.debug(f"Total processing time: {total_time:.2f}s, found {len(detections)} detections")
            
            return detections, total_time
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            # Return empty results on failure
            return [], time.time() - start_time
    
    def _combine_results(
        self, 
        detection_result: Dict[str, Any], 
        classification_result: Dict[str, Any],
        image: Optional[np.ndarray] = None,
        timestamp: Optional[str] = None
    ) -> List[AnimalDetection]:
        """Combine detection and classification results into AnimalDetection objects.
        
        Args:
            detection_result: Results from MegaDetectorV6
            classification_result: Results from classification model
            image: Original image for European species enhancement
            timestamp: Optional timestamp for temporal context
            
        Returns:
            List of AnimalDetection objects
        """
        detections = []
        
        try:
            # Debug: log the structure of results
            logger.debug(f"Detection result keys: {list(detection_result.keys()) if detection_result else 'None'}")
            logger.debug(f"Classification result keys: {list(classification_result.keys()) if classification_result else 'None'}")
            
            # Debug detection object structure
            if detection_result and 'detections' in detection_result:
                detections_obj = detection_result['detections']
                logger.debug(f"Detections object type: {type(detections_obj)}")
                logger.debug(f"Detections object attributes: {dir(detections_obj)}")
                if hasattr(detections_obj, 'xyxy'):
                    logger.debug(f"xyxy shape: {detections_obj.xyxy.shape if hasattr(detections_obj.xyxy, 'shape') else 'no shape'}")
                    logger.debug(f"xyxy content: {detections_obj.xyxy}")
                if hasattr(detections_obj, 'confidence'):
                    logger.debug(f"confidence shape: {detections_obj.confidence.shape if hasattr(detections_obj.confidence, 'shape') else 'no shape'}")
                    logger.debug(f"confidence content: {detections_obj.confidence}")
                if hasattr(detections_obj, 'class_id'):
                    logger.debug(f"class_id shape: {detections_obj.class_id.shape if hasattr(detections_obj.class_id, 'shape') else 'no shape'}")
                    logger.debug(f"class_id content: {detections_obj.class_id}")
            
            # PyTorch Wildlife MegaDetectorV6 returns results with 'detections' key
            # The detections object has xyxy, confidence, and class_id attributes
            
            # Extract detection boxes - PyTorch Wildlife format
            det_boxes = []
            if detection_result and 'detections' in detection_result:
                detections_obj = detection_result['detections']
                
                # Extract arrays from the detections object
                if hasattr(detections_obj, 'xyxy') and hasattr(detections_obj, 'confidence') and hasattr(detections_obj, 'class_id'):
                    boxes = detections_obj.xyxy
                    confidences = detections_obj.confidence
                    class_ids = detections_obj.class_id
                    
                    # Convert to numpy if needed
                    if hasattr(boxes, 'cpu'):
                        boxes = boxes.cpu().numpy()
                    if hasattr(confidences, 'cpu'):
                        confidences = confidences.cpu().numpy()
                    if hasattr(class_ids, 'cpu'):
                        class_ids = class_ids.cpu().numpy()
                    
                    # Combine into detection objects
                    for i in range(len(boxes)):
                        if i < len(confidences) and i < len(class_ids):
                            box = boxes[i]
                            det_boxes.append({
                                'bbox': [float(box[0]), float(box[1]), float(box[2]), float(box[3])],
                                'confidence': float(confidences[i]),
                                'class_id': int(class_ids[i])
                            })
            
            # Extract classification information
            classifications = []
            if classification_result:
                # Handle enhanced classification result format
                if 'class_name' in classification_result or 'species' in classification_result:
                    classifications = [classification_result]
                elif 'predictions' in classification_result:
                    classifications = classification_result['predictions']
                else:
                    # Try to extract from other possible formats
                    classifications = []
            
            # Combine detection boxes with classifications
            for i, detection in enumerate(det_boxes):
                # Get classification for this detection (or use first available)
                if i < len(classifications):
                    classification = classifications[i]
                elif len(classifications) > 0:
                    classification = classifications[0]  # Use first classification as fallback
                else:
                    # Create default classification based on detection class_id
                    class_id = detection.get('class_id', 0)
                    # MegaDetector classes: 1=animal, 2=person, 3=vehicle
                    # Note: class_id 0 might be background/empty, but if we have a detection with good confidence, treat it as animal
                    class_names = {1: 'animal', 2: 'person', 3: 'vehicle'}
                    
                    # If class_id is 0 but we have a detection with reasonable confidence, assume it's an animal
                    if class_id == 0 and detection.get('confidence', 0.0) > 0.3:
                        species_name = 'animal'
                    else:
                        species_name = class_names.get(class_id, 'unknown')
                    
                    classification = {
                        'class_name': species_name,
                        'confidence': detection.get('confidence', 0.0)
                    }
                
                # Extract bounding box
                bbox_data = detection['bbox']
                bbox = BoundingBox(
                    x=int(bbox_data[0]),
                    y=int(bbox_data[1]),
                    width=int(bbox_data[2] - bbox_data[0]),
                    height=int(bbox_data[3] - bbox_data[1])
                )
                
                # Extract confidence and species from enhanced classification
                confidence = float(classification.get('confidence', detection.get('confidence', 0.0)))
                species = str(classification.get('class_name', classification.get('species', 'unknown')))
                
                # Determine classification method
                if classification.get('enhancement_applied', False):
                    classification_method = classification.get('classification_method', 'enhanced_european_mapping')
                else:
                    classification_method = self._model_versions.get('classification', 'unknown')
                
                # Skip detections with very low confidence or unknown species
                if confidence < 0.2 or species == 'unknown':
                    logger.debug(f"Skipping detection with low confidence {confidence} or unknown species {species}")
                    continue
                
                # Extract alternative species and enhancement metadata
                alternative_species = classification.get('alternative_species', [])
                enhancement_metadata = {}
                
                if classification.get('enhancement_applied', False):
                    enhancement_metadata = {
                        'original_classification': classification.get('original_classification'),
                        'size_category': classification.get('size_category'),
                        'enhancement_factors': classification.get('enhancement_factors', {}),
                        'confidence_multiplier': classification.get('confidence', 0.0) / detection.get('confidence', 1.0) if detection.get('confidence', 0.0) > 0 else 1.0
                    }
                
                animal_detection = AnimalDetection(
                    species=species,
                    confidence=confidence,
                    bounding_box=bbox,
                    classification_model=classification_method,
                    is_uncertain=confidence < 0.5,
                    alternative_species=alternative_species if alternative_species else None,
                    enhancement_metadata=enhancement_metadata if enhancement_metadata else None
                )
                
                detections.append(animal_detection)
            
        except Exception as e:
            logger.error(f"Failed to combine detection and classification results: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            # Return empty list on error
            detections = []
        
        return detections
    
    def _is_generic_result(self, classification_result: Dict[str, Any]) -> bool:
        """Check if classification result should be enhanced for European species.
        
        For European regions, we enhance Amazon rainforest classifications to European species.
        
        Args:
            classification_result: Classification result from model
            
        Returns:
            True if result should be enhanced, False if specific enough
        """
        # Get the prediction from different possible fields
        species = classification_result.get('prediction', 
                  classification_result.get('class_name', 
                  classification_result.get('species', '')))
        
        # Generic terms that should always be enhanced
        generic_terms = ['animal', 'unknown', 'mammal', 'creature']
        if species.lower() in generic_terms:
            return True
        
        # For European regions, enhance Amazon rainforest species to European equivalents
        if self.region == "europe" and self.enable_european_enhancement:
            # Amazon species that should be mapped to European species
            amazon_species = ['bos', 'equus', 'capra', 'mazama', 'pecari', 'tapirus', 'sylvilagus', 'dasyprocta']
            if species.lower() in amazon_species:
                logger.debug(f"Amazon species '{species}' will be enhanced to European equivalent")
                return True
        
        return False
    
    def enhance_generic_classification(
        self, 
        detection: Dict[str, Any], 
        classification: Dict[str, Any], 
        image: np.ndarray,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhance generic animal classifications with European species context.
        
        Args:
            detection: Detection result with bounding box information
            classification: Generic classification result
            image: Original image for analysis
            timestamp: Optional timestamp for temporal context
            
        Returns:
            Enhanced classification with European species information
        """
        if not self.enable_european_enhancement:
            return classification
        
        try:
            return self.species_mapper.map_to_european_species(
                detection, classification, image, timestamp
            )
        except Exception as e:
            logger.error(f"Failed to enhance classification: {e}")
            return classification
    
    def run_classification_pipeline(
        self, 
        image: np.ndarray, 
        detection_result: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run multi-layered classification pipeline with European enhancement.
        
        This implements the classification strategy:
        1. Try European-specific model (if available)
        2. Fall back to regional model with enhancement
        3. Final fallback to generic classification
        
        Args:
            image: Input image as numpy array
            detection_result: Detection results for context
            timestamp: Optional timestamp for temporal context
            
        Returns:
            Enhanced classification result
        """
        try:
            # Step 1: Try European-specific model if available
            if self.region == "europe":
                try:
                    # Check if European-specific model is available
                    # For now, this is a placeholder as European models aren't available in PyTorch Wildlife
                    european_result = self._try_european_model(image)
                    if european_result and not self._is_generic_result(european_result):
                        logger.debug("Using European-specific model result")
                        return european_result
                except Exception as e:
                    logger.debug(f"European-specific model not available: {e}")
            
            # Step 2: Use regional model with enhancement
            classification_result = self.run_classification(image)
            
            # Step 3: Apply enhancement if result is generic
            # Check if enhancement is needed
            if self._is_generic_result(classification_result):
                logger.debug(f"Classification '{classification_result.get('prediction', 'unknown')}' will be enhanced for European species")
            if self._is_generic_result(classification_result):
                logger.debug("Applying European species enhancement to generic result")
                
                # Create detection context for enhancement
                detection_context = self._extract_detection_context(detection_result)
                
                enhanced_result = self.enhance_generic_classification(
                    detection_context, classification_result, image, timestamp
                )
                
                # Add enhancement metadata
                enhanced_result['enhancement_applied'] = True
                enhanced_result['original_model'] = self._model_versions.get('classification', 'unknown')
                
                return enhanced_result
            else:
                # Result is already specific, return as-is
                classification_result['enhancement_applied'] = False
                return classification_result
                
        except Exception as e:
            logger.error(f"Classification pipeline failed: {e}")
            # Return minimal fallback result
            return {
                'class_name': 'unknown',
                'confidence': 0.1,
                'enhancement_applied': False,
                'error': str(e)
            }
    
    def _try_european_model(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """Try to use European-specific classification model.
        
        This is a placeholder for future European-specific models.
        Currently returns None as no European models are available in PyTorch Wildlife.
        
        Args:
            image: Input image
            
        Returns:
            Classification result or None if model not available
        """
        # Placeholder for European-specific model
        # In the future, this could load and use European wildlife models
        logger.debug("European-specific model not yet available")
        return None
    
    def _extract_detection_context(self, detection_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detection context for species enhancement.
        
        Args:
            detection_result: Raw detection result from MegaDetectorV6
            
        Returns:
            Simplified detection context for enhancement
        """
        try:
            if detection_result and 'detections' in detection_result:
                detections_obj = detection_result['detections']
                
                if hasattr(detections_obj, 'xyxy') and len(detections_obj.xyxy) > 0:
                    # Use first detection for context
                    box = detections_obj.xyxy[0]
                    confidence = detections_obj.confidence[0] if hasattr(detections_obj, 'confidence') else 0.5
                    
                    # Convert to numpy if needed
                    if hasattr(box, 'cpu'):
                        box = box.cpu().numpy()
                    if hasattr(confidence, 'cpu'):
                        confidence = confidence.cpu().numpy()
                    
                    return {
                        'bbox': [float(box[0]), float(box[1]), float(box[2]), float(box[3])],
                        'confidence': float(confidence)
                    }
            
            # Fallback context
            return {
                'bbox': [0, 0, 100, 100],  # Default bbox
                'confidence': 0.5
            }
            
        except Exception as e:
            logger.debug(f"Could not extract detection context: {e}")
            return {
                'bbox': [0, 0, 100, 100],  # Default bbox
                'confidence': 0.5
            }
    
    def get_enhancement_statistics(self) -> Dict[str, Any]:
        """Get statistics about classification enhancements applied.
        
        Returns:
            Dictionary with enhancement statistics
        """
        return {
            'european_enhancement_enabled': self.enable_european_enhancement,
            'region': self.region,
            'species_mapper_available': self.species_mapper is not None,
            'enhancement_applicable': self.species_mapper.is_enhancement_applicable(self.region) if self.species_mapper else False
        }
    
    def get_model_info(self) -> ModelInfo:
        """Get information about loaded models.
        
        Returns:
            ModelInfo object with model details
        """
        return ModelInfo(
            detection_model=self._model_versions.get('detection', 'Not loaded'),
            classification_model=self._model_versions.get('classification', 'Not loaded'),
            region=self.region,
            model_versions=self._model_versions.copy()
        )
    
    def validate_models(self) -> bool:
        """Validate that models can be loaded and are working.
        
        Returns:
            True if models are valid, False otherwise
        """
        try:
            self.ensure_models_loaded()
            
            # Create a small test image
            test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            
            # Test detection
            self.run_detection(test_image)
            
            # Test classification
            self.run_classification(test_image)
            
            logger.info("Model validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            return False