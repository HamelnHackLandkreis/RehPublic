"""PyTorch Wildlife model management for detection and classification."""

import logging
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
import numpy as np
import os
from PIL import Image

from PytorchWildlife.models import detection as pw_detection
from wildlife_processor.core.deepfaune_v4 import DeepfauneV4Classifier
from wildlife_processor.core.data_models import (
    AnimalDetection,
    ModelInfo,
    DetectionBox,
    ClassificationPipeline,
)
from wildlife_processor.core.data_models import (
    ClassificationResult,
)

logger = logging.getLogger(__name__)

MODEL_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "models"
    / "deepfaune-vit_large_patch14_dinov2.lvd142m.v4.pt"
)

if model_path := os.getenv("MODEL_PATH", None):
    MODEL_PATH = Path(model_path)

# Module-level singleton ModelManager instance for celery workers
# This keeps models loaded in memory across tasks
_singleton_model_manager: "ModelManager | None" = None


class ModelManager:
    """Manages PyTorch Wildlife models for detection and classification."""

    def __init__(self, region: str = "europe") -> None:
        """Initialize model manager for European wildlife detection.

        Args:
            region: Must be "europe" (other regions not supported)
        """
        self.region = region
        self.detection_model: Any | None = None
        self.classification_model: DeepfauneV4Classifier | None = None
        self._model_versions: Dict[str, str] = {}

    def load_detection_model(self) -> None:
        """Load MegaDetectorV6 for animal detection."""
        import sys

        logger.info("Loading MegaDetectorV6...")

        # Fix for Celery: wget library needs sys.stdout.fileno() which LoggingProxy doesn't have
        original_stdout = sys.stdout
        if not hasattr(sys.stdout, "fileno"):
            sys.stdout = sys.__stdout__

        try:
            self.detection_model = pw_detection.MegaDetectorV6(
                weights=None, device="cpu", pretrained=True, version="MDV6-yolov9-c"
            )
            self._model_versions["detection"] = "MegaDetectorV6-yolov9c"
            logger.info("MegaDetectorV6 loaded successfully")
        finally:
            sys.stdout = original_stdout

    def load_classification_model(self) -> None:
        """Load DeepFaune v4 classification model for European wildlife."""
        logger.info("Loading DeepFaune v4 classification model...")

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

        v4_model_path = MODEL_PATH.resolve()
        logger.info(f"Using DeepFaune v4 model (38 classes): {v4_model_path}")

        self.classification_model = DeepfauneV4Classifier(
            device="cpu",
            weights=str(v4_model_path),
        )
        self._model_versions["classification"] = "DeepfauneClassifier-v4"
        logger.info("DeepFaune v4 classification model loaded successfully")

    def ensure_models_loaded(self) -> None:
        """Ensure both detection and classification models are loaded."""
        if self.detection_model is None:
            self.load_detection_model()
        if self.classification_model is None:
            self.load_classification_model()

    def _save_debug_image(
        self,
        image: np.ndarray,
        subdirectory: str,
        prefix: str,
        index: int | None = None,
    ) -> None:
        """Save image for debugging purposes.

        Args:
            image: Image array to save
            subdirectory: Subdirectory under processed_images (e.g., 'classification_input', 'cropped_detections')
            prefix: Filename prefix (e.g., 'classification_input', 'detection')
            index: Optional index to include in filename
        """
        try:
            output_dir = (
                Path(__file__).parent.parent.parent.parent
                / "processed_images"
                / subdirectory
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            if index is not None:
                filename = f"{prefix}_{index}_{file_timestamp}.jpg"
            else:
                filename = f"{prefix}_{file_timestamp}.jpg"

            output_path = output_dir / filename
            Image.fromarray(image).save(output_path)
            logger.debug(f"Saved debug image to: {output_path}")
        except Exception as e:
            logger.warning(f"Failed to save debug image: {e}")

    def run_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """Run animal detection on image.

        Args:
            image: Input image as numpy array

        Returns:
            Detection results from MegaDetectorV6
        """
        if self.detection_model is None:
            raise RuntimeError("Detection model not loaded")
        result = self.detection_model.single_image_detection(image)
        return result  # type: ignore[no-any-return]

    def process_image(self, image: np.ndarray) -> List[AnimalDetection]:
        """Process image with both detection and classification.

        Args:
            image: Input image as numpy array

        Returns:
            List of animal detections
        """
        self.ensure_models_loaded()
        if self.detection_model is None:
            raise RuntimeError("Detection model not loaded")

        detection_result = self.detection_model.single_image_detection(image)
        classification_results = self.run_classification_pipeline(
            image=image, detection_result=detection_result
        )

        detection_boxes = DetectionBox.extract_from_result(
            detection_result=detection_result
        )
        detections = AnimalDetection.combine_results(
            detection_boxes=detection_boxes,
            classification_results=classification_results,
            classification_model_version=self._model_versions.get(
                "classification", "DeepfauneClassifier-v4"
            ),
            min_confidence=0.2,
        )
        return detections

    def run_classification_pipeline(
        self,
        image: np.ndarray,
        detection_result: Dict[str, Any],
        min_detection_confidence: float = 0.25,
    ) -> "ClassificationPipeline":
        """Run classification on each detected animal region.

        Args:
            image: Input image as numpy array
            detection_result: Detection results with bounding boxes
            min_detection_confidence: Minimum confidence threshold for detections (default: 0.25)

        Returns:
            ClassificationPipeline with list of ClassificationResult objects
        """

        predictions = []
        detection_boxes = DetectionBox.extract_from_result(
            detection_result=detection_result
        )
        if len(detection_boxes) == 0:
            logger.debug("No detection boxes found, returning empty predictions")
            return ClassificationPipeline(predictions=[])

        filtered_boxes = [
            box for box in detection_boxes if box.confidence >= min_detection_confidence
        ]

        if len(filtered_boxes) < len(detection_boxes):
            logger.debug(
                f"Filtered {len(detection_boxes) - len(filtered_boxes)} detections "
                f"below confidence threshold {min_detection_confidence}"
            )

        if len(filtered_boxes) == 0:
            logger.debug(
                "No detections above confidence threshold, returning empty predictions"
            )
            return ClassificationPipeline(predictions=[])

        for i, detection_box in enumerate(filtered_boxes):
            x1, y1, x2, y2 = (
                int(detection_box.bbox[0]),
                int(detection_box.bbox[1]),
                int(detection_box.bbox[2]),
                int(detection_box.bbox[3]),
            )

            height, width = image.shape[:2]
            x1 = max(0, min(x1, width))
            y1 = max(0, min(y1, height))
            x2 = max(x1, min(x2, width))
            y2 = max(y1, min(y2, height))

            cropped_image = image[y1:y2, x1:x2]

            if (
                cropped_image.size == 0
                or cropped_image.shape[0] < 10
                or cropped_image.shape[1] < 10
            ):
                continue

            # self._save_debug_image(
            #     image=cropped_image,
            #     subdirectory="cropped_detections",
            #     prefix="detection",
            #     index=i,
            # )
            if self.classification_model is None:
                raise RuntimeError("Classification model not loaded")

            classification_dict = self.classification_model.single_image_classification(
                cropped_image
            )
            classification_result = ClassificationResult.from_dict(classification_dict)

            predictions.append(classification_result)

        return ClassificationPipeline(predictions=predictions)

    def get_model_info(self) -> ModelInfo:
        """Get information about loaded models.

        Returns:
            ModelInfo object with model details
        """
        return ModelInfo(
            detection_model=self._model_versions.get("detection", "Not loaded"),
            classification_model=self._model_versions.get(
                "classification", "Not loaded"
            ),
            region=self.region,
            model_versions=self._model_versions.copy(),
        )


def get_model_manager(region: str = "europe") -> ModelManager:
    """Get or create singleton ModelManager instance.

    This function ensures models are loaded once and reused across celery tasks,
    keeping them "hot" in memory for better performance.

    Args:
        region: Regional model to use (default: "europe")

    Returns:
        ModelManager instance (singleton)
    """
    global _singleton_model_manager
    if _singleton_model_manager is None:
        logger.info(f"Creating singleton ModelManager with region: {region}")
        _singleton_model_manager = ModelManager(region=region)
        _singleton_model_manager.ensure_models_loaded()
        logger.info("Singleton ModelManager created and models loaded")
    return _singleton_model_manager
