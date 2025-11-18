"""Adapter for wildlife_processor core image processing."""

import io
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import numpy as np
from PIL import Image
from PIL.Image import Image as ImageType

from wildlife_processor.core.models import ModelManager, get_model_manager
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
        """Ensure model manager is initialized and models are loaded.

        Uses singleton ModelManager to keep models hot in memory across celery tasks.
        """
        if self.model_manager is None:
            logger.info(
                f"Getting singleton ModelManager with region: {self.model_region}"
            )
            self.model_manager = get_model_manager(region=self.model_region)

    def process_image_data(
        self,
        image_bytes: bytes,
        timestamp: Optional[datetime] = None,
    ) -> List[Dict]:
        """Process image bytes and return detection results synchronously.

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

    def process_image_async(
        self,
        image_id: UUID,
        image_base64: str,
        model_region: str = "europe",
        timestamp: Optional[datetime] = None,
    ) -> str:
        """Dispatch image processing to Celery task queue.

        Args:
            image_id: UUID of the image
            image_base64: Base64-encoded image data
            model_region: Regional model to use for classification
            timestamp: Optional timestamp for temporal context

        Returns:
            Celery task ID
        """
        # avoid cyclic import
        from src.api.images.images_tasks import process_image_task

        timestamp_str = timestamp.isoformat() if timestamp else None

        task = process_image_task.delay(
            image_id=str(image_id),
            image_base64=image_base64,
            model_region=model_region,
            timestamp=timestamp_str,
        )

        logger.info(f"Dispatched async processing task {task.id} for image {image_id}")

        return task.id
