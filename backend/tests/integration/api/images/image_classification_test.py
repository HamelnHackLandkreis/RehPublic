"""Integration tests for image classification."""

from pathlib import Path

import pytest

from api.processor_integration import ProcessorClient


@pytest.fixture
def processor_client():
    """Create processor client for testing."""
    return ProcessorClient(model_region="europe")


def test_roe_deer_classification(processor_client):
    """Test classification of image containing roe deer.

    Tests the specific image: bilder/Aufnahme_250610_0727_BYWP9.jpg
    Expected to detect a roe deer with reasonable confidence.
    """
    # Path to test image
    image_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "bilder"
        / "Aufnahme_250610_0727_BYWP9.jpg"
    )

    # Verify image exists
    assert image_path.exists(), f"Test image not found: {image_path}"

    # Read image bytes
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Process image
    detections = processor_client.process_image_data(
        image_bytes=image_bytes, location_name="Test Location"
    )

    # Assert we got detections
    assert len(detections) > 0, "No detections found in image"

    # Assert roe deer was detected
    species_detected = [d["species"] for d in detections]
    assert "roe_deer" in species_detected, f"Expected roe_deer, got: {species_detected}"

    # Get the roe deer detection
    roe_deer_detection = next(d for d in detections if d["species"] == "roe_deer")

    # Assert confidence is reasonable (above 0.5)
    assert roe_deer_detection["confidence"] > 0.5, (
        f"Low confidence: {roe_deer_detection['confidence']}"
    )

    # Assert bounding box exists and has valid dimensions
    bbox = roe_deer_detection["bounding_box"]
    assert bbox["width"] > 0, "Invalid bounding box width"
    assert bbox["height"] > 0, "Invalid bounding box height"
    assert bbox["x"] >= 0, "Invalid bounding box x coordinate"
    assert bbox["y"] >= 0, "Invalid bounding box y coordinate"

    # Assert classification model is set
    assert roe_deer_detection["classification_model"] is not None

    # Log detection details for debugging
    print("\nDetection results:")
    print(f"  Species: {roe_deer_detection['species']}")
    print(f"  Confidence: {roe_deer_detection['confidence']:.3f}")
    print(f"  Bounding box: {bbox}")
    print(f"  Model: {roe_deer_detection['classification_model']}")
