"""Core data models for wildlife camera processing."""

from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected animals."""

    x: int
    y: int
    width: int
    height: int

    @classmethod
    def from_xyxy(cls, x1: float, y1: float, x2: float, y2: float) -> "BoundingBox":
        """Create BoundingBox from xyxy coordinates.

        Args:
            x1: Left x coordinate
            y1: Top y coordinate
            x2: Right x coordinate
            y2: Bottom y coordinate

        Returns:
            BoundingBox instance
        """
        return cls(
            x=int(x1),
            y=int(y1),
            width=int(x2 - x1),
            height=int(y2 - y1),
        )


class ClassificationConfidence(BaseModel):
    """Individual species confidence from classification model."""

    species: str
    confidence: float = Field(ge=0.0, le=1.0)

    @classmethod
    def from_list(cls, data: List[Any]) -> "ClassificationConfidence":
        """Create from nested list format [[species], confidence].

        Args:
            data: Nested list with [[species_name], confidence_value]

        Returns:
            ClassificationConfidence instance
        """
        species = data[0][0] if isinstance(data[0], list) else str(data[0])
        confidence = float(data[1])
        return cls(species=species, confidence=confidence)


class ClassificationResult(BaseModel):
    """Result from single image classification."""

    img_id: str
    prediction: List[str]
    class_id: int
    confidence: float = Field(ge=0.0, le=1.0)
    all_confidences: List[ClassificationConfidence]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClassificationResult":
        """Parse classification result from dictionary.

        Args:
            data: Raw classification result dictionary

        Returns:
            ClassificationResult instance
        """
        all_confidences = [
            ClassificationConfidence.from_list(item)
            for item in data.get("all_confidences", [])
        ]

        return cls(
            img_id=str(data.get("img_id", "None")),
            prediction=data.get("prediction", []),
            class_id=int(data.get("class_id", 0)),
            confidence=float(data.get("confidence", 0.0)),
            all_confidences=all_confidences,
        )

    def get_class_name(self) -> str:
        """Get the primary predicted class name.

        Returns:
            Primary species name
        """
        return self.prediction[0] if self.prediction else "unknown"


class ClassificationPipeline(BaseModel):
    """Results from classification pipeline with multiple predictions."""

    predictions: List[ClassificationResult]


class DetectionBox(BaseModel):
    """Raw detection box from MegaDetectorV6."""

    bbox: List[float] = Field(min_length=4, max_length=4)
    confidence: float = Field(ge=0.0, le=1.0)
    class_id: int

    @classmethod
    def extract_from_result(
        cls, detection_result: Dict[str, Any]
    ) -> List["DetectionBox"]:
        """Extract detection boxes from MegaDetectorV6 result.

        Args:
            detection_result: Raw detection result

        Returns:
            List of DetectionBox instances
        """
        det_boxes: List[DetectionBox] = []

        if not detection_result or "detections" not in detection_result:
            return det_boxes

        detections_obj = detection_result["detections"]

        if not (
            hasattr(detections_obj, "xyxy")
            and hasattr(detections_obj, "confidence")
            and hasattr(detections_obj, "class_id")
        ):
            return det_boxes

        boxes = detections_obj.xyxy
        confidences = detections_obj.confidence
        class_ids = detections_obj.class_id

        # Convert to numpy if needed
        if hasattr(boxes, "cpu"):
            boxes = boxes.cpu().numpy()
        if hasattr(confidences, "cpu"):
            confidences = confidences.cpu().numpy()
        if hasattr(class_ids, "cpu"):
            class_ids = class_ids.cpu().numpy()

        # Combine into detection objects
        for i in range(len(boxes)):
            if i < len(confidences) and i < len(class_ids):
                box = boxes[i]
                det_boxes.append(
                    cls(
                        bbox=[
                            float(box[0]),
                            float(box[1]),
                            float(box[2]),
                            float(box[3]),
                        ],
                        confidence=float(confidences[i]),
                        class_id=int(class_ids[i]),
                    )
                )

        return det_boxes


class AnimalDetection(BaseModel):
    """Individual animal detection result."""

    species: str
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: BoundingBox
    classification_model: str
    is_uncertain: bool
    alternative_species: Optional[List[str]] = None
    enhancement_metadata: Optional[Dict[str, Any]] = None

    @field_validator("is_uncertain", mode="before")
    @classmethod
    def validate_is_uncertain(cls, v: Any, info: Any) -> bool:
        """Validate is_uncertain based on confidence if not provided."""
        if v is None and hasattr(info, "data") and "confidence" in info.data:
            confidence = info.data["confidence"]
            return bool(confidence < 0.5)
        return bool(v) if v is not None else False

    def to_dict(self) -> Dict[str, Any]:
        """Convert AnimalDetection to dictionary format.

        Returns:
            Dictionary representation of the detection
        """
        return {
            "species": self.species,
            "confidence": self.confidence,
            "bounding_box": {
                "x": self.bounding_box.x,
                "y": self.bounding_box.y,
                "width": self.bounding_box.width,
                "height": self.bounding_box.height,
            },
            "classification_model": self.classification_model,
            "is_uncertain": self.is_uncertain,
        }

    @classmethod
    def combine_results(
        cls,
        detection_boxes: List[DetectionBox],
        classification_results: ClassificationPipeline,
        classification_model_version: str,
        min_confidence: float = 0.2,
    ) -> List["AnimalDetection"]:
        """Combine detection and classification results into AnimalDetection objects.

        Args:
            detection_boxes: List of DetectionBox instances
            classification_results: ClassificationPipeline with predictions
            classification_model_version: Version string of classification model
            min_confidence: Minimum confidence threshold

        Returns:
            List of AnimalDetection objects
        """
        detections = []

        for i, detection_box in enumerate(detection_boxes):
            if i >= len(classification_results.predictions):
                continue

            classification = classification_results.predictions[i]

            bbox = BoundingBox.from_xyxy(
                x1=detection_box.bbox[0],
                y1=detection_box.bbox[1],
                x2=detection_box.bbox[2],
                y2=detection_box.bbox[3],
            )

            species = classification.get_class_name()
            confidence = classification.confidence

            if confidence < min_confidence:
                logger.debug(f"Skipping detection with low confidence {confidence}")
                continue

            animal_detection = cls(
                species=species,
                confidence=confidence,
                bounding_box=bbox,
                classification_model=classification_model_version,
                is_uncertain=confidence < 0.5,
            )

            detections.append(animal_detection)

        return detections


class DetectionResult(BaseModel):
    """Complete detection result for a single image."""

    image_path: Path
    camera_reference: str
    timestamp: datetime
    detections: List[AnimalDetection]
    model_version: str


class ModelInfo(BaseModel):
    """Information about the models used for processing."""

    detection_model: str
    classification_model: str
    region: str
    model_versions: Dict[str, str]


class ProcessingResults(BaseModel):
    """Complete results from processing a directory of images."""

    total_images: int
    successful_detections: int
    failed_images: List[str]
    processing_duration: float
    results_by_camera: Dict[str, List[DetectionResult]]
    model_info: ModelInfo


class ImageMetadata(BaseModel):
    """Metadata extracted from image file and directory structure."""

    file_path: Path
    location: str
    timestamp: datetime
    camera_reference: str


class ModelConfig(BaseModel):
    """Configuration for regional models."""

    region: str
    classification_model_class: str
    model_name: str
    geographic_coverage: str
