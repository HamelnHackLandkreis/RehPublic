"""Adapter for wildlife_processor core image processing."""

import io
import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
from PIL import Image
from PIL.Image import Image as ImageType

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

    def _ensure_model_loaded(self) -> None:
        """Ensure model manager is initialized and models are loaded."""
        if self.model_manager is None:
            logger.info(f"Initializing ModelManager with region: {self.model_region}")
            self.model_manager = ModelManager(region=self.model_region)
            self.model_manager.ensure_models_loaded()

    def process_image_data(
        self,
        image_bytes: bytes,
        timestamp: Optional[datetime] = None,
    ) -> List[Dict]:
        """Process image bytes and return detection results.

        Args:
            image_bytes: Raw image bytes

            timestamp: Optional timestamp for temporal context

        Returns:
            List of detection dictionaries with species, confidence, and bounding box
        """

        # Ensure models are loaded
        self._ensure_model_loaded()

        # Convert bytes to PIL Image
        image_pil: ImageType = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary
        if image_pil.mode != "RGB":
            image_pil = image_pil.convert("RGB")

        # Convert to numpy array
        image_array = np.array(image_pil)

        # Preprocess for PyTorch Wildlife
        processed_image: np.ndarray = preprocess_image_for_pytorch_wildlife(image_array)

        # model_manager is guaranteed to be non-None after _ensure_model_loaded
        assert self.model_manager is not None
        detections = self.model_manager.process_image(processed_image)

        return [detection.to_dict() for detection in detections]
