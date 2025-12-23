"""Integration tests for image pull controller endpoints."""

from typing import Any, Callable, Dict
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def create_test_user(client: TestClient) -> Callable[[], str]:
    """Create fixture to generate test user ID.

    Args:
        client: Test client

    Returns:
        Function that returns a user ID
    """

    def _create_user() -> str:
        return str(uuid4())

    return _create_user


@pytest.fixture
def create_location(client: TestClient) -> Callable[..., Dict[str, Any]]:
    """Create a fixture that returns a function to create test locations.

    Args:
        client: Test client

    Returns:
        Function to create a location
    """

    def _create_location(
        name: str = "Test Location", longitude: float = 10.5, latitude: float = 52.3
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
def mock_auth_user(monkeypatch: pytest.MonkeyPatch) -> str:
    """Mock authenticated user for requests.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        User ID that will be authenticated
    """
    user_id = str(uuid4())
    auth0_sub = f"auth0|{user_id}"

    mock_user = Mock()
    mock_user.sub = auth0_sub

    def mock_middleware(request, call_next):
        request.state.user = mock_user
        return call_next(request)

    from src.api import main

    monkeypatch.setattr(main.app, "middleware", lambda x: mock_middleware)

    return user_id


class TestCreatePullSource:
    """Test cases for POST /image-pull-sources endpoint."""

    def test_create_pull_source_with_basic_auth(
        self,
        client: TestClient,
        create_location: Callable[..., Dict[str, Any]],
        mock_auth_user: str,
    ) -> None:
        """Test creating a pull source with basic authentication.

        Args:
            client: Test client
            create_location: Location creation fixture
            mock_auth_user: Mocked authenticated user ID
        """
        location = create_location()

        pull_source_data = {
            "name": "Test Camera Feed",
            "location_id": location["id"],
            "base_url": "https://example.com/images/",
            "auth_type": "basic",
            "auth_username": "testuser",
            "auth_password": "testpass",
            "is_active": True,
        }

        response = client.post("/image-pull-sources/", json=pull_source_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Camera Feed"
        assert data["location_id"] == location["id"]
        assert data["base_url"] == "https://example.com/images/"
        assert data["auth_type"] == "basic"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_pull_source_with_header_auth(
        self,
        client: TestClient,
        create_location: Callable[..., Dict[str, Any]],
        mock_auth_user: str,
    ) -> None:
        """Test creating a pull source with header authentication.

        Args:
            client: Test client
            create_location: Location creation fixture
            mock_auth_user: Mocked authenticated user ID
        """
        location = create_location()

        pull_source_data = {
            "name": "Header Auth Feed",
            "location_id": location["id"],
            "base_url": "https://example.com/images/",
            "auth_type": "header",
            "auth_header": "Bearer token123",
            "is_active": True,
        }

        response = client.post("/image-pull-sources/", json=pull_source_data)

        assert response.status_code == 201
        data = response.json()
        assert data["auth_type"] == "header"

    def test_create_pull_source_inactive(
        self,
        client: TestClient,
        create_location: Callable[..., Dict[str, Any]],
        mock_auth_user: str,
    ) -> None:
        """Test creating an inactive pull source.

        Args:
            client: Test client
            create_location: Location creation fixture
            mock_auth_user: Mocked authenticated user ID
        """
        location = create_location()

        pull_source_data = {
            "name": "Inactive Feed",
            "location_id": location["id"],
            "base_url": "https://example.com/images/",
            "auth_type": "none",
            "is_active": False,
        }

        response = client.post("/image-pull-sources/", json=pull_source_data)

        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is False

    def test_create_pull_source_without_auth(
        self, client: TestClient, create_location: Callable[..., Dict[str, Any]]
    ) -> None:
        """Test creating pull source without authentication fails.

        Args:
            client: Test client
            create_location: Location creation fixture
        """
        location = create_location()

        pull_source_data = {
            "name": "Test Feed",
            "location_id": location["id"],
            "base_url": "https://example.com/images/",
            "auth_type": "none",
            "is_active": True,
        }

        response = client.post("/image-pull-sources/", json=pull_source_data)

        assert response.status_code == 401


class TestListPullSources:
    """Test cases for GET /image-pull-sources endpoint."""

    def test_list_pull_sources_empty(
        self, client: TestClient, mock_auth_user: str
    ) -> None:
        """Test listing pull sources when none exist.

        Args:
            client: Test client
            mock_auth_user: Mocked authenticated user ID
        """
        response = client.get("/image-pull-sources/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_pull_sources_with_sources(
        self,
        client: TestClient,
        create_location: Callable[..., Dict[str, Any]],
        mock_auth_user: str,
    ) -> None:
        """Test listing pull sources when they exist.

        Args:
            client: Test client
            create_location: Location creation fixture
            mock_auth_user: Mocked authenticated user ID
        """
        location = create_location()

        pull_source_data1 = {
            "name": "Feed 1",
            "location_id": location["id"],
            "base_url": "https://example.com/feed1/",
            "auth_type": "none",
            "is_active": True,
        }
        pull_source_data2 = {
            "name": "Feed 2",
            "location_id": location["id"],
            "base_url": "https://example.com/feed2/",
            "auth_type": "none",
            "is_active": True,
        }

        client.post("/image-pull-sources/", json=pull_source_data1)
        client.post("/image-pull-sources/", json=pull_source_data2)

        response = client.get("/image-pull-sources/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(s["name"] == "Feed 1" for s in data)
        assert any(s["name"] == "Feed 2" for s in data)

    def test_list_pull_sources_without_auth(self, client: TestClient) -> None:
        """Test listing pull sources without authentication fails.

        Args:
            client: Test client
        """
        response = client.get("/image-pull-sources/")

        assert response.status_code == 401


class TestProcessPullSource:
    """Test cases for POST /image-pull-sources/{source_id}/process endpoint."""

    @patch("src.api.image_pull_sources.image_pull_service.ImagePullService")
    def test_process_pull_source_success(
        self,
        mock_service_class: Mock,
        client: TestClient,
        create_location: Callable[..., Dict[str, Any]],
        mock_auth_user: str,
    ) -> None:
        """Test manually processing a pull source.

        Args:
            mock_service_class: Mock ImagePullService class
            client: Test client
            create_location: Location creation fixture
            mock_auth_user: Mocked authenticated user ID
        """
        location = create_location()

        pull_source_data = {
            "name": "Test Feed",
            "location_id": location["id"],
            "base_url": "https://example.com/images/",
            "auth_type": "none",
            "is_active": True,
        }
        create_response = client.post("/image-pull-sources/", json=pull_source_data)
        source_id = create_response.json()["id"]

        mock_service = Mock()
        mock_service.pull_and_process_source.return_value = {
            "source_id": source_id,
            "source_name": "Test Feed",
            "processed_count": 5,
            "status": "success",
            "processed_images": [],
        }
        mock_service_class.factory.return_value = mock_service

        response = client.post(f"/image-pull-sources/{source_id}/process?max_files=5")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["processed_count"] == 5

    def test_process_pull_source_not_found(
        self, client: TestClient, mock_auth_user: str
    ) -> None:
        """Test processing non-existent pull source.

        Args:
            client: Test client
            mock_auth_user: Mocked authenticated user ID
        """
        fake_source_id = str(uuid4())

        response = client.post(f"/image-pull-sources/{fake_source_id}/process")

        assert response.status_code == 404

    def test_process_pull_source_without_auth(self, client: TestClient) -> None:
        """Test processing pull source without authentication fails.

        Args:
            client: Test client
        """
        fake_source_id = str(uuid4())

        response = client.post(f"/image-pull-sources/{fake_source_id}/process")

        assert response.status_code == 401


class TestTogglePullSource:
    """Test cases for PATCH /image-pull-sources/{source_id}/toggle endpoint."""

    def test_toggle_pull_source_to_inactive(
        self,
        client: TestClient,
        create_location: Callable[..., Dict[str, Any]],
        mock_auth_user: str,
    ) -> None:
        """Test toggling pull source to inactive.

        Args:
            client: Test client
            create_location: Location creation fixture
            mock_auth_user: Mocked authenticated user ID
        """
        location = create_location()

        pull_source_data = {
            "name": "Toggle Test Feed",
            "location_id": location["id"],
            "base_url": "https://example.com/images/",
            "auth_type": "none",
            "is_active": True,
        }
        create_response = client.post("/image-pull-sources/", json=pull_source_data)
        source_id = create_response.json()["id"]

        response = client.patch(
            f"/image-pull-sources/{source_id}/toggle?is_active=false"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_toggle_pull_source_to_active(
        self,
        client: TestClient,
        create_location: Callable[..., Dict[str, Any]],
        mock_auth_user: str,
    ) -> None:
        """Test toggling pull source to active.

        Args:
            client: Test client
            create_location: Location creation fixture
            mock_auth_user: Mocked authenticated user ID
        """
        location = create_location()

        pull_source_data = {
            "name": "Toggle Test Feed 2",
            "location_id": location["id"],
            "base_url": "https://example.com/images/",
            "auth_type": "none",
            "is_active": False,
        }
        create_response = client.post("/image-pull-sources/", json=pull_source_data)
        source_id = create_response.json()["id"]

        response = client.patch(
            f"/image-pull-sources/{source_id}/toggle?is_active=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    def test_toggle_pull_source_not_found(
        self, client: TestClient, mock_auth_user: str
    ) -> None:
        """Test toggling non-existent pull source.

        Args:
            client: Test client
            mock_auth_user: Mocked authenticated user ID
        """
        fake_source_id = str(uuid4())

        response = client.patch(
            f"/image-pull-sources/{fake_source_id}/toggle?is_active=false"
        )

        assert response.status_code == 404

    def test_toggle_pull_source_without_auth(self, client: TestClient) -> None:
        """Test toggling pull source without authentication fails.

        Args:
            client: Test client
        """
        fake_source_id = str(uuid4())

        response = client.patch(
            f"/image-pull-sources/{fake_source_id}/toggle?is_active=false"
        )

        assert response.status_code == 401
