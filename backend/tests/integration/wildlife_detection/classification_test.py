"""Test wildlife image classification."""

from pathlib import Path

from src.adapters.image_processor_adapter import ProcessorClient


def test_classify_wildlife_image():
    """Test classification of a real wildlife image.

    This test processes the image bilder/Aufnahme_250605_2029_BYWP9.jpg
    and verifies that the classification detects the expected animal.
    """
    image_path = Path("backend/bilder/Aufnahme_250605_2029_BYWP9.jpg")

    # Verify image exists
    assert image_path.exists(), f"Test image not found at {image_path}"

    # Read image bytes
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Initialize processor
    processor = ProcessorClient(model_region="general")

    # Process image
    detections = processor.process_image_data(image_bytes=image_bytes)

    # Assert we got detections
    assert len(detections) > 0, "No animals detected in image"

    detection = detections[0]

    assert "species" in detection
    assert "confidence" in detection
    assert "bounding_box" in detection
    assert "classification_model" in detection

    assert detection["confidence"] > 0.0
    assert detection["confidence"] <= 1.0

    assert detection["species"], "Species should not be empty"

    detected_species = detection["species"].lower()

    assert len(detected_species) > 0, "Species name should not be empty"
    assert detected_species != "unknown", "Species should be identified"
    assert detected_species == "raccoon", (
        f"Expected 'raccoon', got '{detected_species}'"
    )
