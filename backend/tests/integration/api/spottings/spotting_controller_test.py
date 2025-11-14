"""Integration tests for spotting controller endpoints."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_image_bytes():
    """Load sample image from file."""
    image_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "bilder"
        / "Aufnahme_250608_0753_BYWP9.jpg"
    )
    with open(image_path, "rb") as f:
        return f.read()


def test_get_spottings_aggregated(client, sample_image_bytes):
    """Test getting aggregated spotting data."""
    # Create multiple locations
    locations = []
    for i in range(2):
        location_data = {
            "name": f"Location {i}",
            "longitude": 10.0 + i,
            "latitude": 50.0 + i,
        }
        response = client.post("/locations", json=location_data)
        assert response.status_code == 201
        locations.append(response.json())

    # Upload images to each location
    for location in locations:
        files = {"file": ("test_image.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post(f"/locations/{location['id']}/image", files=files)
        assert response.status_code == 201

    # Get spottings (using coordinates from first location and large distance range)
    response = client.get(
        "/spottings",
        params={
            "latitude": locations[0]["latitude"],
            "longitude": locations[0]["longitude"],
            "distance_range": 1000.0,
        },
    )
    assert response.status_code == 200

    spottings_data = response.json()
    assert "locations" in spottings_data
    assert "total_unique_species" in spottings_data
    assert "total_spottings" in spottings_data
    assert isinstance(spottings_data["locations"], list)

    # If there are locations, verify structure
    for location in spottings_data["locations"]:
        assert "id" in location
        assert "name" in location
        assert "longitude" in location
        assert "latitude" in location
        assert "images" in location
        assert "total_images_with_animals" in location
        assert isinstance(location["images"], list)
        assert isinstance(location["total_images_with_animals"], int)
        assert location["total_images_with_animals"] >= 0


def test_get_spottings(client, sample_image_bytes):
    """Test GET /spottings endpoint with location and distance filters."""
    # Create multiple locations at different coordinates
    location1_data = {
        "name": "Forest Location",
        "longitude": 10.5,
        "latitude": 52.3,
        "description": "Forest camera location",
    }
    location2_data = {
        "name": "Meadow Location",
        "longitude": 11.0,
        "latitude": 52.5,
        "description": "Meadow camera location",
    }

    response = client.post("/locations", json=location1_data)
    assert response.status_code == 201
    location1 = response.json()

    response = client.post("/locations", json=location2_data)
    assert response.status_code == 201
    location2 = response.json()

    # Upload images to both locations
    files = {"file": ("test_image.jpg", sample_image_bytes, "image/jpeg")}
    response = client.post(f"/locations/{location1['id']}/image", files=files)
    assert response.status_code == 201

    response = client.post(f"/locations/{location2['id']}/image", files=files)
    assert response.status_code == 201

    # Test GET /spottings with parameters centered on location1
    response = client.get(
        "/spottings",
        params={
            "latitude": location1_data["latitude"],
            "longitude": location1_data["longitude"],
            "distance_range": 100.0,
        },
    )
    assert response.status_code == 200

    spottings_data = response.json()
    assert "locations" in spottings_data
    assert "total_unique_species" in spottings_data
    assert "total_spottings" in spottings_data
    assert isinstance(spottings_data["locations"], list)
    assert isinstance(spottings_data["total_unique_species"], int)
    assert isinstance(spottings_data["total_spottings"], int)
    assert spottings_data["total_unique_species"] >= 0
    assert spottings_data["total_spottings"] >= 0

    # Verify location structure
    assert len(spottings_data["locations"]) > 0
    for location in spottings_data["locations"]:
        assert "id" in location
        assert "name" in location
        assert "longitude" in location
        assert "latitude" in location
        assert "description" in location
        assert "images" in location
        assert "total_images_with_animals" in location
        assert isinstance(location["images"], list)
        assert isinstance(location["total_images_with_animals"], int)
        assert location["total_images_with_animals"] >= 0
        assert len(location["images"]) <= 5  # Max 5 images per location

        # Verify image structure
        for image in location["images"]:
            assert "image_id" in image
            assert "location_id" in image
            assert "upload_timestamp" in image
            assert "detections" in image
            assert isinstance(image["detections"], list)

            # Verify detection structure if present
            for detection in image["detections"]:
                assert "species" in detection
                assert "confidence" in detection
                assert "bounding_box" in detection
                assert "classification_model" in detection
                assert "is_uncertain" in detection
                assert isinstance(detection["confidence"], (int, float))
                assert 0 <= detection["confidence"] <= 1

    # Verify that total_images_with_animals matches actual count
    for location in spottings_data["locations"]:
        actual_count = sum(
            1 for image in location["images"] if len(image["detections"]) > 0
        )
        assert location["total_images_with_animals"] == actual_count

    # Test with smaller distance range (should return fewer or no locations)
    response = client.get(
        "/spottings",
        params={
            "latitude": location1_data["latitude"],
            "longitude": location1_data["longitude"],
            "distance_range": 0.1,  # Very small range
        },
    )
    assert response.status_code == 200
    spottings_small_range = response.json()
    assert "locations" in spottings_small_range
    assert isinstance(spottings_small_range["locations"], list)
