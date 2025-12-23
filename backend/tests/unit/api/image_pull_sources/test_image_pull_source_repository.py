"""Unit tests for ImagePullSourceRepository."""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.api.image_pull_sources.image_pull_source_repository import (
    ImagePullSourceRepository,
)


@pytest.fixture
def mock_session() -> Mock:
    """Create mock database session.

    Returns:
        Mock Session object
    """
    session = Mock()
    session.query = Mock(return_value=session)
    session.filter = Mock(return_value=session)
    session.first = Mock()
    session.all = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    return session


@pytest.fixture
def sample_pull_source() -> Mock:
    """Create sample pull source object.

    Returns:
        Mock ImagePullSource object
    """
    source = Mock()
    source.id = str(uuid4())
    source.name = "Test Pull Source"
    source.user_id = str(uuid4())
    source.location_id = str(uuid4())
    source.base_url = "https://example.com/images/"
    source.auth_type = "basic"
    source.auth_username = "user"
    source.auth_password = "pass"
    source.is_active = True
    source.last_pulled_filename = None
    source.last_pull_timestamp = None
    source.created_at = datetime(2024, 1, 15, 10, 0, 0)
    source.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    return source


@pytest.fixture
def repository() -> ImagePullSourceRepository:
    """Create ImagePullSourceRepository instance.

    Returns:
        ImagePullSourceRepository instance
    """
    return ImagePullSourceRepository()


class TestImagePullSourceRepositoryCreate:
    """Test cases for create method."""

    def test_create_with_basic_auth(
        self, mock_session: Mock, repository: ImagePullSourceRepository
    ) -> None:
        """Test creating pull source with basic auth.

        Args:
            mock_session: Mock database session
            repository: Repository instance
        """
        user_id = uuid4()
        location_id = uuid4()

        repository.create(
            db=mock_session,
            name="Test Source",
            user_id=user_id,
            location_id=location_id,
            base_url="https://example.com/images/",
            auth_type="basic",
            auth_username="testuser",
            auth_password="testpass",
            is_active=True,
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

        added_source = mock_session.add.call_args[0][0]
        assert added_source.name == "Test Source"
        assert str(added_source.user_id) == str(user_id)
        assert str(added_source.location_id) == str(location_id)
        assert added_source.base_url == "https://example.com/images/"
        assert added_source.auth_type == "basic"
        assert added_source.auth_username == "testuser"
        assert added_source.auth_password == "testpass"
        assert added_source.is_active is True

    def test_create_with_header_auth(
        self, mock_session: Mock, repository: ImagePullSourceRepository
    ) -> None:
        """Test creating pull source with header auth.

        Args:
            mock_session: Mock database session
            repository: Repository instance
        """
        user_id = uuid4()
        location_id = uuid4()

        repository.create(
            db=mock_session,
            name="Test Source",
            user_id=user_id,
            location_id=location_id,
            base_url="https://example.com/images/",
            auth_type="header",
            auth_header="Bearer token123",
            is_active=True,
        )

        added_source = mock_session.add.call_args[0][0]
        assert added_source.auth_type == "header"
        assert added_source.auth_header == "Bearer token123"
        assert added_source.auth_username is None
        assert added_source.auth_password is None

    def test_create_inactive_source(
        self, mock_session: Mock, repository: ImagePullSourceRepository
    ) -> None:
        """Test creating inactive pull source.

        Args:
            mock_session: Mock database session
            repository: Repository instance
        """
        user_id = uuid4()
        location_id = uuid4()

        repository.create(
            db=mock_session,
            name="Inactive Source",
            user_id=user_id,
            location_id=location_id,
            base_url="https://example.com/images/",
            auth_type="none",
            is_active=False,
        )

        added_source = mock_session.add.call_args[0][0]
        assert added_source.is_active is False


class TestImagePullSourceRepositoryGetById:
    """Test cases for get_by_id method."""

    def test_get_by_id_found(
        self,
        mock_session: Mock,
        repository: ImagePullSourceRepository,
        sample_pull_source: Mock,
    ) -> None:
        """Test getting source by ID when it exists.

        Args:
            mock_session: Mock database session
            repository: Repository instance
            sample_pull_source: Sample pull source
        """
        source_id = uuid4()
        mock_session.first.return_value = sample_pull_source

        result = repository.get_by_id(db=mock_session, source_id=source_id)

        assert result == sample_pull_source
        mock_session.query.assert_called_once()
        mock_session.filter.assert_called_once()
        mock_session.first.assert_called_once()

    def test_get_by_id_not_found(
        self, mock_session: Mock, repository: ImagePullSourceRepository
    ) -> None:
        """Test getting source by ID when it doesn't exist.

        Args:
            mock_session: Mock database session
            repository: Repository instance
        """
        source_id = uuid4()
        mock_session.first.return_value = None

        result = repository.get_by_id(db=mock_session, source_id=source_id)

        assert result is None


class TestImagePullSourceRepositoryGetAllActive:
    """Test cases for get_all_active method."""

    def test_get_all_active_with_sources(
        self,
        mock_session: Mock,
        repository: ImagePullSourceRepository,
        sample_pull_source: Mock,
    ) -> None:
        """Test getting all active sources when they exist.

        Args:
            mock_session: Mock database session
            repository: Repository instance
            sample_pull_source: Sample pull source
        """
        source2 = Mock()
        source2.id = str(uuid4())
        source2.name = "Source 2"
        source2.is_active = True

        mock_session.all.return_value = [sample_pull_source, source2]

        results = repository.get_all_active(db=mock_session)

        assert len(results) == 2
        assert results[0] == sample_pull_source
        assert results[1] == source2
        mock_session.query.assert_called_once()
        mock_session.filter.assert_called_once()
        mock_session.all.assert_called_once()

    def test_get_all_active_empty(
        self, mock_session: Mock, repository: ImagePullSourceRepository
    ) -> None:
        """Test getting all active sources when none exist.

        Args:
            mock_session: Mock database session
            repository: Repository instance
        """
        mock_session.all.return_value = []

        results = repository.get_all_active(db=mock_session)

        assert len(results) == 0


class TestImagePullSourceRepositoryUpdateLastPulled:
    """Test cases for update_last_pulled method."""

    def test_update_last_pulled_success(
        self,
        mock_session: Mock,
        repository: ImagePullSourceRepository,
        sample_pull_source: Mock,
    ) -> None:
        """Test updating last pulled filename.

        Args:
            mock_session: Mock database session
            repository: Repository instance
            sample_pull_source: Sample pull source
        """
        source_id = uuid4()
        mock_session.first.return_value = sample_pull_source

        repository.update_last_pulled(
            db=mock_session, source_id=source_id, filename="image_100.jpg"
        )

        assert sample_pull_source.last_pulled_filename == "image_100.jpg"
        assert sample_pull_source.last_pull_timestamp is not None
        mock_session.commit.assert_called_once()

    def test_update_last_pulled_source_not_found(
        self, mock_session: Mock, repository: ImagePullSourceRepository
    ) -> None:
        """Test updating last pulled when source doesn't exist.

        Args:
            mock_session: Mock database session
            repository: Repository instance
        """
        source_id = uuid4()
        mock_session.first.return_value = None

        repository.update_last_pulled(
            db=mock_session, source_id=source_id, filename="image_100.jpg"
        )

        assert not mock_session.commit.called


class TestImagePullSourceRepositoryUpdateActiveStatus:
    """Test cases for update_active_status method."""

    def test_update_active_status_to_inactive(
        self,
        mock_session: Mock,
        repository: ImagePullSourceRepository,
        sample_pull_source: Mock,
    ) -> None:
        """Test updating source to inactive.

        Args:
            mock_session: Mock database session
            repository: Repository instance
            sample_pull_source: Sample pull source
        """
        source_id = uuid4()
        sample_pull_source.is_active = True
        mock_session.first.return_value = sample_pull_source

        repository.update_active_status(
            db=mock_session, source_id=source_id, is_active=False
        )

        assert sample_pull_source.is_active is False
        mock_session.commit.assert_called_once()

    def test_update_active_status_to_active(
        self,
        mock_session: Mock,
        repository: ImagePullSourceRepository,
        sample_pull_source: Mock,
    ) -> None:
        """Test updating source to active.

        Args:
            mock_session: Mock database session
            repository: Repository instance
            sample_pull_source: Sample pull source
        """
        source_id = uuid4()
        sample_pull_source.is_active = False
        mock_session.first.return_value = sample_pull_source

        repository.update_active_status(
            db=mock_session, source_id=source_id, is_active=True
        )

        assert sample_pull_source.is_active is True
        mock_session.commit.assert_called_once()

    def test_update_active_status_source_not_found(
        self, mock_session: Mock, repository: ImagePullSourceRepository
    ) -> None:
        """Test updating active status when source doesn't exist.

        Args:
            mock_session: Mock database session
            repository: Repository instance
        """
        source_id = uuid4()
        mock_session.first.return_value = None

        repository.update_active_status(
            db=mock_session, source_id=source_id, is_active=False
        )

        assert not mock_session.commit.called
