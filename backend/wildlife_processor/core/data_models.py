"""Core data models for wildlife camera processing."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BoundingBox:
    """Bounding box coordinates for detected animals."""
    x: int
    y: int
    width: int
    height: int


@dataclass
class AnimalDetection:
    """Individual animal detection result."""
    species: str
    confidence: float
    bounding_box: BoundingBox
    classification_model: str
    is_uncertain: bool  # confidence < 0.5
    alternative_species: Optional[List[str]] = None  # Alternative species suggestions
    enhancement_metadata: Optional[Dict[str, Any]] = None  # Enhancement details


@dataclass
class DetectionResult:
    """Complete detection result for a single image."""
    image_path: Path
    camera_reference: str
    timestamp: datetime
    detections: List[AnimalDetection]
    processing_time: float
    model_version: str


@dataclass
class ModelInfo:
    """Information about the models used for processing."""
    detection_model: str
    classification_model: str
    region: str
    model_versions: Dict[str, str]


@dataclass
class ProcessingResults:
    """Complete results from processing a directory of images."""
    total_images: int
    successful_detections: int
    failed_images: List[str]
    processing_duration: float
    results_by_camera: Dict[str, List[DetectionResult]]
    model_info: ModelInfo


@dataclass
class ImageMetadata:
    """Metadata extracted from image file and directory structure."""
    file_path: Path
    location: str
    timestamp: datetime
    camera_reference: str


@dataclass
class ModelConfig:
    """Configuration for regional models."""
    region: str
    classification_model_class: str
    model_name: str
    geographic_coverage: str