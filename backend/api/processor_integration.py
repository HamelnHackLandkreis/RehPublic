"""Integration with wildlife_processor core for image processing."""

import io
import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
from PIL import Image

from wildlife_processor.core.models import ModelManager
from wildlife_processor.utils.image_utils import preprocess_image_for_pytorch_wildlife

logger = logging.getLogger(__name__)


class ProcessorClient:
    """Client for processing images using wildlife_processor core."""

    def __init__(self, model_region: str = "general"):
        """Initialize processor client.

        Args:
            model_region: Regional model to use for classification
        """
        self.model_region = model_region
        self.model_manager: Optional[ModelManager] = None

    def _ensure_model_loaded(self):
        """Ensure model manager is initialized and models are loaded."""
        if self.model_manager is None:
            logger.info(f"Initializing ModelManager with region: {self.model_region}")
            self.model_manager = ModelManager(region=self.model_region)
            self.model_manager.ensure_models_loaded()

    def process_image_data(
        self,
        image_bytes: bytes,
        location_name: str,
        timestamp: Optional[datetime] = None,
    ) -> List[Dict]:
        """Process image bytes and return detection results.

        Args:
            image_bytes: Raw image bytes
            location_name: Name of the location where image was taken
            timestamp: Optional timestamp for temporal context

        Returns:
            List of detection dictionaries with species, confidence, and bounding box
        """
        try:
            # Ensure models are loaded
            self._ensure_model_loaded()

            # Convert bytes to PIL Image
            image_pil = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if image_pil.mode != "RGB":
                image_pil = image_pil.convert("RGB")

            # Convert to numpy array
            image_array = np.array(image_pil)

            # Preprocess for PyTorch Wildlife
            processed_image = preprocess_image_for_pytorch_wildlife(image_array)

            # Convert timestamp to string if provided
            timestamp_str = timestamp.isoformat() if timestamp else None

            # Process image
            if self.model_manager is None:
                raise RuntimeError("Model manager not initialized")
            detections, processing_time = self.model_manager.process_image(
                processed_image, timestamp_str
            )

            logger.info(
                f"Processed image for location '{location_name}': "
                f"found {len(detections)} detections in {processing_time:.2f}s"
            )

            # Convert detections to dictionary format
            detection_dicts = []
            for detection in detections:
                detection_dict = {
                    "species": detection.species,
                    "confidence": detection.confidence,
                    "bounding_box": {
                        "x": detection.bounding_box.x,
                        "y": detection.bounding_box.y,
                        "width": detection.bounding_box.width,
                        "height": detection.bounding_box.height,
                    },
                    "classification_model": detection.classification_model,
                    "is_uncertain": detection.is_uncertain,
                }
                detection_dicts.append(detection_dict)

            return detection_dicts

        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            # Return empty list on failure (don't fail the upload)
            return []
