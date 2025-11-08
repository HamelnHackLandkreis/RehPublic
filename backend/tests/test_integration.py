"""Integration tests for Wildlife Camera API."""

import base64
from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def sample_image_bytes():
    """Load sample image from file."""
    image_path = (
        Path(__file__).parent.parent / "bilder" / "Aufnahme_250608_0753_BYWP9.jpg"
    )
    with open(image_path, "rb") as f:
        return f.read()


def test_create_and_get_locations(client):
    """Test creating and retrieving locations."""
    # Create a location
    location_data = {
        "name": "Forest Trail 1",
        "longitude": 10.5,
        "latitude": 52.3,
        "description": "Trail camera in forest",
    }

    response = client.post("/locations", json=location_data)
    assert response.status_code == 201
    created_location = response.json()
    assert created_location["name"] == location_data["name"]
    assert created_location["longitude"] == location_data["longitude"]
    assert created_location["latitude"] == location_data["latitude"]
    assert "id" in created_location
    assert "total_unique_species" in created_location
    assert "total_spottings" in created_location
    assert created_location["total_unique_species"] == 0
    assert created_location["total_spottings"] == 0

    location_id = created_location["id"]

    # Get all locations
    response = client.get("/locations")
    assert response.status_code == 200
    locations_data = response.json()
    assert "locations" in locations_data
    assert "total_unique_species" in locations_data
    assert "total_spottings" in locations_data
    locations = locations_data["locations"]
    assert len(locations) == 1
    assert locations[0]["id"] == location_id
    assert isinstance(locations_data["total_unique_species"], int)
    assert isinstance(locations_data["total_spottings"], int)
    # Check that each location has its own totals
    assert "total_unique_species" in locations[0]
    assert "total_spottings" in locations[0]
    assert isinstance(locations[0]["total_unique_species"], int)
    assert isinstance(locations[0]["total_spottings"], int)

    # Get specific location
    response = client.get(f"/locations/{location_id}")
    assert response.status_code == 200
    location = response.json()
    assert location["id"] == location_id
    assert location["name"] == location_data["name"]
    assert "total_unique_species" in location
    assert "total_spottings" in location
    assert isinstance(location["total_unique_species"], int)
    assert isinstance(location["total_spottings"], int)


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
        assert len(location["images"]) <= 3  # Max 3 images per location

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


def test_root_endpoint(client):
    """Test root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data
