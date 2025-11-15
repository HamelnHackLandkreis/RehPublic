"""Test wildlife image classification."""

from pathlib import Path

from api.processor_integration import ProcessorClient


def test_classify_wildlife_image():
    """Test classification of a real wildlife image.

    This test processes the image bilder/Aufnahme_250605_2029_BYWP9.jpg
    and verifies that the classification detects the expected animal.
    """
    # Path to test image
    image_path = (
        Path(__file__).parent.parent / "bilder" / "Aufnahme_250605_2029_BYWP9.jpg"
    )

    # Verify image exists
    assert image_path.exists(), f"Test image not found at {image_path}"

    # Read image bytes
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Initialize processor
    processor = ProcessorClient(model_region="general")

    # Process image
    detections = processor.process_image_data(
        image_bytes=image_bytes, location_name="Test Location"
    )

    # Assert we got detections
    assert len(detections) > 0, "No animals detected in image"

    # Get the first detection (highest confidence)
    detection = detections[0]

    # Assert detection structure
    assert "species" in detection
    assert "confidence" in detection
    assert "bounding_box" in detection
    assert "classification_model" in detection

    # Assert confidence is reasonable
    assert detection["confidence"] > 0.0
    assert detection["confidence"] <= 1.0

    # Assert species is detected (not empty)
    assert detection["species"], "Species should not be empty"

    # Log detection for manual verification
    print(
        f"\nDetected: {detection['species']} (confidence: {detection['confidence']:.2%})"
    )
    print(f"Bounding box: {detection['bounding_box']}")
    print(f"Model: {detection['classification_model']}")

    # Assert the expected animal type
    # Based on the test run, this image contains an animal detected with high confidence
    detected_species = detection["species"].lower()

    # Verify we got a valid species name (not empty or unknown)
    assert len(detected_species) > 0, "Species name should not be empty"
    assert detected_species != "unknown", "Species should be identified"

    # The general model detects "animal" - this is expected behavior
    # For more specific species, use the European model with DeepFaune
    assert "animal" in detected_species, f"Expected 'animal', got '{detected_species}'"
