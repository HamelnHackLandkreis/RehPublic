"""Integration tests for image controller endpoints."""

import base64
from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def sample_image_bytes():
    """Load sample image from file."""
    # Go up from tests/integration/api/images/ to backend/
    image_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "bilder"
        / "Aufnahme_250608_0753_BYWP9.jpg"
    )
    with open(image_path, "rb") as f:
        return f.read()


def test_upload_image_to_location(client, sample_image_bytes):
    """Test uploading an image to a location."""
    # Create a location first
    location_data = {
        "name": "Meadow Cam",
        "longitude": 11.2,
        "latitude": 53.1,
        "description": "Meadow camera",
    }
    response = client.post("/locations", json=location_data)
    assert response.status_code == 201
    location_id = response.json()["id"]

    # Upload image
    files = {"file": ("test_image.jpg", sample_image_bytes, "image/jpeg")}
    response = client.post(f"/locations/{location_id}/image", files=files)

    assert response.status_code == 201
    upload_response = response.json()
    assert "image_id" in upload_response
    assert upload_response["location_id"] == location_id
    assert "upload_timestamp" in upload_response
    assert "detections_count" in upload_response
    assert upload_response["detections_count"] >= 0  # May be 0 if no animals detected
    assert "roe deer" in upload_response["detected_species"]

    # Get specific location
    response = client.get(f"/locations/{location_id}")
    assert response.status_code == 200
    location = response.json()
    assert location["id"] == location_id
    assert location["name"] == location_data["name"]
    assert "total_unique_species" in location
    assert "total_spottings" in location
    assert location["total_unique_species"] > 0
    assert location["total_spottings"] > 0

    response = client.get("/locations")
    assert response.status_code == 200
    locations_data = response.json()
    assert "locations" in locations_data


def test_upload_image_invalid_location(client, sample_image_bytes):
    """Test uploading image to non-existent location returns 404."""
    # Use a random UUID that doesn't exist
    fake_location_id = str(uuid4())

    files = {"file": ("test_image.jpg", sample_image_bytes, "image/jpeg")}
    response = client.post(f"/locations/{fake_location_id}/image", files=files)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_image_with_detections(client, sample_image_bytes):
    """Test retrieving an image with its detection data."""
    # Create location
    location_data = {"name": "River Crossing", "longitude": 12.0, "latitude": 54.0}
    response = client.post("/locations", json=location_data)
    location_id = response.json()["id"]

    # Upload image
    files = {"file": ("test_image.jpg", sample_image_bytes, "image/jpeg")}
    response = client.post(f"/locations/{location_id}/image", files=files)
    assert response.status_code == 201
    image_id = response.json()["image_id"]

    # Get image details
    response = client.get(f"/images/{image_id}")
    assert response.status_code == 200

    image_data = response.json()
    assert image_data["image_id"] == image_id
    assert image_data["location_id"] == location_id
    assert "raw" in image_data  # base64 encoded image
    assert "upload_timestamp" in image_data
    assert "detections" in image_data
    assert isinstance(image_data["detections"], list)

    # Verify base64 data is valid
    try:
        base64.b64decode(image_data["raw"])
    except Exception:
        pytest.fail("Invalid base64 data in response")

    # Expect red_deer to be detected in this image
    species_detected = [detection["species"] for detection in image_data["detections"]]
    assert "red_deer" in species_detected, (
        f"Expected red_deer to be detected, but found: {species_detected}"
    )


def test_get_image_not_found(client):
    """Test getting non-existent image returns 404."""
    fake_image_id = str(uuid4())

    response = client.get(f"/images/{fake_image_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
