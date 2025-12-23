"""Integration tests for location controller endpoints."""

from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Load sample image from file.

    Returns:
        Image file bytes
    """
    image_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "bilder"
        / "Aufnahme_250608_0753_BYWP9.jpg"
    )
    with open(image_path, "rb") as f:
        return f.read()


@pytest.fixture
def create_location(
    client: TestClient,
) -> Callable[..., Dict[str, Any]]:
    """Create a fixture that returns a function to create test locations.

    Args:
        client: Test client

    Returns:
        Function to create a location
    """

    def _create_location(
        name: str, longitude: float, latitude: float
    ) -> Dict[str, Any]:
        """Create a test location.

        Args:
            name: Location name
            longitude: Longitude coordinate
            latitude: Latitude coordinate

        Returns:
            Created location data
        """
        location_data: Dict[str, Any] = {
            "name": name,
            "longitude": longitude,
            "latitude": latitude,
        }
        response = client.post("/locations", json=location_data)
        assert response.status_code == 201
        return response.json()  # type: ignore[no-any-return]

    return _create_location


@pytest.fixture
def upload_image(client: TestClient, sample_image_bytes: bytes) -> Callable[..., None]:
    """Create a fixture that returns a function to upload images.

    Args:
        client: Test client
        sample_image_bytes: Image bytes to upload

    Returns:
        Function to upload an image
    """

    def _upload_image(location_id: str) -> None:
        """Upload an image to a location.

        Args:
            location_id: Location ID
        """
        files: Dict[str, tuple[str, bytes, str]] = {
            "file": ("test_image.jpg", sample_image_bytes, "image/jpeg")
        }
        response = client.post(f"/locations/{location_id}/image", files=files)
        assert response.status_code == 201

    return _upload_image


def _validate_spottings_response(spottings_data: Dict[str, Any]) -> None:
    """Validate the structure of spottings response.

    Args:
        spottings_data: Spottings response data
    """
    assert "locations" in spottings_data
    assert "total_unique_species" in spottings_data
    assert "total_spottings" in spottings_data
    assert isinstance(spottings_data["locations"], list)
    assert isinstance(spottings_data["total_unique_species"], int)
    assert isinstance(spottings_data["total_spottings"], int)
    assert spottings_data["total_unique_species"] >= 0
    assert spottings_data["total_spottings"] >= 0


def _validate_location_structure(location: Dict[str, Any]) -> None:
    """Validate the structure of a location in spottings response.

    Args:
        location: Location data from response
    """
    assert "id" in location
    assert "name" in location
    assert "longitude" in location
    assert "latitude" in location
    assert "images" in location
    assert "total_images_with_animals" in location
    assert isinstance(location["images"], list)
    assert isinstance(location["total_images_with_animals"], int)
    assert location["total_images_with_animals"] >= 0
    assert len(location["images"]) <= 5


def _validate_image_structure(image: Dict[str, Any]) -> None:
    """Validate the structure of an image in spottings response.

    Args:
        image: Image data from response
    """
    assert "image_id" in image
    assert "location_id" in image
    assert "upload_timestamp" in image
    assert "detections" in image
    assert isinstance(image["detections"], list)


def _validate_detection_structure(detection: Dict[str, Any]) -> None:
    """Validate the structure of a detection in spottings response.

    Args:
        detection: Detection data from response
    """
    assert "species" in detection
    assert "confidence" in detection
    assert "bounding_box" in detection
    assert "classification_model" in detection
    assert "is_uncertain" in detection
    assert isinstance(detection["confidence"], (int, float))
    assert 0 <= detection["confidence"] <= 1


def test_create_and_get_locations(
    client: TestClient,
    create_location: Callable[..., Dict[str, Any]],
    upload_image: Callable[..., None],
) -> None:
    """Test creating and retrieving locations."""
    location_data = {
        "name": "Forest Trail 1",
        "longitude": 10.5,
        "latitude": 52.3,
    }

    created_location = create_location(
        name=location_data["name"],
        longitude=location_data["longitude"],
        latitude=location_data["latitude"],
    )
    assert created_location["name"] == location_data["name"]
    assert created_location["longitude"] == location_data["longitude"]
    assert created_location["latitude"] == location_data["latitude"]
    assert "id" in created_location
    assert "total_unique_species" in created_location
    assert "total_spottings" in created_location
    assert created_location["total_unique_species"] == 0
    assert created_location["total_spottings"] == 0

    location_id = created_location["id"]

    upload_image(location_id)

    response = client.get(
        "/locations",
        params={
            "latitude": location_data["latitude"],
            "longitude": location_data["longitude"],
            "distance_range": 1000.0,
        },
    )
    assert response.status_code == 200
    locations_data = response.json()
    assert "locations" in locations_data
    assert "total_unique_species" in locations_data
    assert "total_spottings" in locations_data
    locations = locations_data["locations"]
    assert len(locations) >= 1
    location_ids = [loc["id"] for loc in locations]
    assert location_id in location_ids
    assert isinstance(locations_data["total_unique_species"], int)
    assert isinstance(locations_data["total_spottings"], int)
    found_location = next(loc for loc in locations if loc["id"] == location_id)
    assert "total_unique_species" in found_location
    assert "total_spottings" in found_location
    assert isinstance(found_location["total_unique_species"], int)
    assert isinstance(found_location["total_spottings"], int)

    response = client.get(f"/locations/{location_id}")
    assert response.status_code == 200
    location = response.json()
    assert location["id"] == location_id
    assert location["name"] == location_data["name"]
    assert "total_unique_species" in location
    assert "total_spottings" in location
    assert isinstance(location["total_unique_species"], int)
    assert isinstance(location["total_spottings"], int)


class TestGetLocationsWithFilters:
    """Test cases for GET /locations endpoint with filters."""

    def test_get_locations_aggregated(
        self,
        client: TestClient,
        create_location: Callable[..., Dict[str, Any]],
        upload_image: Callable[..., None],
    ) -> None:
        """Test getting aggregated location data with images."""
        locations: List[Dict[str, Any]] = []
        for i in range(2):
            location = create_location(
                name=f"Location {i}",
                longitude=10.0 + i,
                latitude=50.0 + i,
            )
            locations.append(location)

        for location in locations:
            upload_image(location["id"])

        response = client.get(
            "/locations",
            params={
                "latitude": locations[0]["latitude"],
                "longitude": locations[0]["longitude"],
                "distance_range": 1000.0,
            },
        )
        assert response.status_code == 200

        spottings_data: Dict[str, Any] = response.json()
        _validate_spottings_response(spottings_data)

        for location in spottings_data["locations"]:
            _validate_location_structure(location)

    def test_get_locations_with_distance_filters(
        self,
        client: TestClient,
        create_location: Callable[..., Dict[str, Any]],
        upload_image: Callable[..., None],
    ) -> None:
        """Test GET /locations endpoint with location and distance filters."""
        location1 = create_location(
            name="Forest Location",
            longitude=10.5,
            latitude=52.3,
        )
        location2 = create_location(
            name="Meadow Location",
            longitude=11.0,
            latitude=52.5,
        )

        upload_image(location1["id"])
        upload_image(location2["id"])

        response = client.get(
            "/locations",
            params={
                "latitude": 52.3,
                "longitude": 10.5,
                "distance_range": 100.0,
            },
        )
        assert response.status_code == 200

        spottings_data: Dict[str, Any] = response.json()
        _validate_spottings_response(spottings_data)
        assert len(spottings_data["locations"]) > 0

        for location in spottings_data["locations"]:
            _validate_location_structure(location)
            assert "description" in location

            for image in location["images"]:
                _validate_image_structure(image)

                for detection in image["detections"]:
                    _validate_detection_structure(detection)

        for location in spottings_data["locations"]:
            actual_count = sum(
                1 for image in location["images"] if len(image["detections"]) > 0
            )
            assert location["total_images_with_animals"] == actual_count

    def test_get_locations_with_small_distance_range(
        self,
        client: TestClient,
        create_location: Callable[..., Dict[str, Any]],
        upload_image: Callable[..., None],
    ) -> None:
        """Test GET /locations with very small distance range."""
        location = create_location(
            name="Test Location",
            longitude=10.5,
            latitude=52.3,
        )

        upload_image(location["id"])

        response = client.get(
            "/locations",
            params={
                "latitude": 52.3,
                "longitude": 10.5,
                "distance_range": 0.1,
            },
        )
        assert response.status_code == 200

        spottings_data: Dict[str, Any] = response.json()
        assert "locations" in spottings_data
        assert isinstance(spottings_data["locations"], list)
