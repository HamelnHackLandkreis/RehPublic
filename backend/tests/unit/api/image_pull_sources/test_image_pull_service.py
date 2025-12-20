"""Unit tests for ImagePullService."""

from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from src.api.image_pull_sources.gateways.base import ImageFile
from src.api.image_pull_sources.image_pull_service import ImagePullService


@pytest.fixture
def mock_session() -> Mock:
    """Create mock database session.

    Returns:
        Mock Session object
    """
    return Mock()


@pytest.fixture
def mock_repository() -> Mock:
    """Create mock ImagePullSourceRepository.

    Returns:
        Mock ImagePullSourceRepository object
    """
    repository = Mock()
    repository.get_by_id = Mock()
    repository.get_all_active = Mock()
    repository.update_last_pulled = Mock()
    return repository


@pytest.fixture
def mock_image_service() -> Mock:
    """Create mock ImageService.

    Returns:
        Mock ImageService object
    """
    service = Mock()
    service.upload_and_process_image = Mock()
    return service


@pytest.fixture
def mock_gateway() -> Mock:
    """Create mock ImagePullGateway.

    Returns:
        Mock ImagePullGateway object
    """
    gateway = Mock()
    gateway.get_new_files = Mock()
    gateway.download_file = Mock()
    return gateway


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
    return source


@pytest.fixture
def sample_image_files() -> list[ImageFile]:
    """Create sample image files.

    Returns:
        List of ImageFile objects
    """
    return [
        ImageFile(
            filename="image_001.jpg",
            url="https://example.com/images/image_001.jpg",
            last_modified="2024-01-15T10:00:00",
        ),
        ImageFile(
            filename="image_002.jpg",
            url="https://example.com/images/image_002.jpg",
            last_modified="2024-01-15T11:00:00",
        ),
        ImageFile(
            filename="image_003.jpg",
            url="https://example.com/images/image_003.jpg",
            last_modified="2024-01-15T12:00:00",
        ),
    ]


@pytest.fixture
def image_pull_service(
    mock_repository: Mock, mock_image_service: Mock
) -> ImagePullService:
    """Create ImagePullService with mocked dependencies.

    Args:
        mock_repository: Mock repository
        mock_image_service: Mock image service

    Returns:
        ImagePullService instance
    """
    return ImagePullService(
        repository=mock_repository, image_service=mock_image_service
    )


class TestImagePullServiceFactory:
    """Test cases for ImagePullService factory method."""

    def test_factory(self) -> None:
        """Test factory creates service instance."""
        service = ImagePullService.factory()
        assert service is not None
        assert isinstance(service, ImagePullService)


class TestImagePullServicePullAndProcessSource:
    """Test cases for pull_and_process_source method."""

    def test_pull_and_process_source_success(
        self,
        mock_session: Mock,
        mock_repository: Mock,
        mock_image_service: Mock,
        mock_gateway: Mock,
        sample_pull_source: Mock,
        sample_image_files: list[ImageFile],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test successful pull and process of images.

        Args:
            mock_session: Mock database session
            mock_repository: Mock repository
            mock_image_service: Mock image service
            mock_gateway: Mock gateway
            sample_pull_source: Sample pull source
            sample_image_files: Sample image files
            monkeypatch: Pytest monkeypatch fixture
        """
        source_id = UUID(sample_pull_source.id)

        mock_repository.get_by_id.return_value = sample_pull_source
        mock_gateway.get_new_files.return_value = sample_image_files[:2]
        mock_gateway.download_file.return_value = b"fake_image_data"

        upload_result = Mock()
        upload_result.image_id = uuid4()
        upload_result.detections_count = 2
        mock_image_service.upload_and_process_image.return_value = upload_result

        service = ImagePullService(
            repository=mock_repository, image_service=mock_image_service
        )
        monkeypatch.setattr(service, "create_gateway", Mock(return_value=mock_gateway))

        result = service.pull_and_process_source(
            db=mock_session, source_id=source_id, max_files=10
        )

        mock_repository.get_by_id.assert_called_once_with(mock_session, source_id)
        mock_gateway.get_new_files.assert_called_once_with(None)
        assert mock_gateway.download_file.call_count == 2
        assert mock_image_service.upload_and_process_image.call_count == 2

        mock_repository.update_last_pulled.assert_called_once_with(
            mock_session, source_id, "image_002.jpg"
        )

        assert result["source_id"] == str(source_id)
        assert result["source_name"] == sample_pull_source.name
        assert result["processed_count"] == 2
        assert result["status"] == "success"
        assert len(result["processed_images"]) == 2

    def test_pull_and_process_source_not_found(
        self,
        mock_session: Mock,
        mock_repository: Mock,
        mock_image_service: Mock,
    ) -> None:
        """Test error when source not found.

        Args:
            mock_session: Mock database session
            mock_repository: Mock repository
            mock_image_service: Mock image service
        """
        source_id = uuid4()
        mock_repository.get_by_id.return_value = None

        service = ImagePullService(
            repository=mock_repository, image_service=mock_image_service
        )

        with pytest.raises(ValueError, match="Image pull source .* not found"):
            service.pull_and_process_source(
                db=mock_session, source_id=source_id, max_files=10
            )

    def test_pull_and_process_source_inactive(
        self,
        mock_session: Mock,
        mock_repository: Mock,
        mock_image_service: Mock,
        sample_pull_source: Mock,
    ) -> None:
        """Test skipping inactive source.

        Args:
            mock_session: Mock database session
            mock_repository: Mock repository
            mock_image_service: Mock image service
            sample_pull_source: Sample pull source
        """
        source_id = UUID(sample_pull_source.id)
        sample_pull_source.is_active = False

        mock_repository.get_by_id.return_value = sample_pull_source

        service = ImagePullService(
            repository=mock_repository, image_service=mock_image_service
        )

        result = service.pull_and_process_source(
            db=mock_session, source_id=source_id, max_files=10
        )

        assert result["status"] == "inactive"
        assert result["processed_count"] == 0
        assert not mock_image_service.upload_and_process_image.called

    def test_pull_and_process_source_no_new_files(
        self,
        mock_session: Mock,
        mock_repository: Mock,
        mock_image_service: Mock,
        mock_gateway: Mock,
        sample_pull_source: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test handling no new files available.

        Args:
            mock_session: Mock database session
            mock_repository: Mock repository
            mock_image_service: Mock image service
            mock_gateway: Mock gateway
            sample_pull_source: Sample pull source
            monkeypatch: Pytest monkeypatch fixture
        """
        source_id = UUID(sample_pull_source.id)

        mock_repository.get_by_id.return_value = sample_pull_source
        mock_gateway.get_new_files.return_value = []

        service = ImagePullService(
            repository=mock_repository, image_service=mock_image_service
        )
        monkeypatch.setattr(service, "create_gateway", Mock(return_value=mock_gateway))

        result = service.pull_and_process_source(
            db=mock_session, source_id=source_id, max_files=10
        )

        assert result["status"] == "no_new_files"
        assert result["processed_count"] == 0
        assert not mock_image_service.upload_and_process_image.called

    def test_pull_and_process_source_max_files_limit(
        self,
        mock_session: Mock,
        mock_repository: Mock,
        mock_image_service: Mock,
        mock_gateway: Mock,
        sample_pull_source: Mock,
        sample_image_files: list[ImageFile],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test max_files limit is respected.

        Args:
            mock_session: Mock database session
            mock_repository: Mock repository
            mock_image_service: Mock image service
            mock_gateway: Mock gateway
            sample_pull_source: Sample pull source
            sample_image_files: Sample image files
            monkeypatch: Pytest monkeypatch fixture
        """
        source_id = UUID(sample_pull_source.id)

        mock_repository.get_by_id.return_value = sample_pull_source
        mock_gateway.get_new_files.return_value = sample_image_files
        mock_gateway.download_file.return_value = b"fake_image_data"

        upload_result = Mock()
        upload_result.image_id = uuid4()
        upload_result.detections_count = 1
        mock_image_service.upload_and_process_image.return_value = upload_result

        service = ImagePullService(
            repository=mock_repository, image_service=mock_image_service
        )
        monkeypatch.setattr(service, "create_gateway", Mock(return_value=mock_gateway))

        result = service.pull_and_process_source(
            db=mock_session, source_id=source_id, max_files=2
        )

        assert result["processed_count"] == 2
        assert mock_image_service.upload_and_process_image.call_count == 2

    def test_pull_and_process_source_error_handling(
        self,
        mock_session: Mock,
        mock_repository: Mock,
        mock_image_service: Mock,
        mock_gateway: Mock,
        sample_pull_source: Mock,
        sample_image_files: list[ImageFile],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test error handling stops processing but updates last pulled.

        Args:
            mock_session: Mock database session
            mock_repository: Mock repository
            mock_image_service: Mock image service
            mock_gateway: Mock gateway
            sample_pull_source: Sample pull source
            sample_image_files: Sample image files
            monkeypatch: Pytest monkeypatch fixture
        """
        source_id = UUID(sample_pull_source.id)

        mock_repository.get_by_id.return_value = sample_pull_source
        mock_gateway.get_new_files.return_value = sample_image_files
        mock_gateway.download_file.side_effect = [
            b"fake_image_data",
            Exception("Download failed"),
        ]

        upload_result = Mock()
        upload_result.image_id = uuid4()
        upload_result.detections_count = 1
        mock_image_service.upload_and_process_image.return_value = upload_result

        service = ImagePullService(
            repository=mock_repository, image_service=mock_image_service
        )
        monkeypatch.setattr(service, "create_gateway", Mock(return_value=mock_gateway))

        result = service.pull_and_process_source(
            db=mock_session, source_id=source_id, max_files=10
        )

        assert result["processed_count"] == 1
        assert mock_image_service.upload_and_process_image.call_count == 1

        mock_repository.update_last_pulled.assert_called_once_with(
            mock_session, source_id, "image_001.jpg"
        )


class TestImagePullServiceProcessAllSources:
    """Test cases for process_all_sources method."""

    def test_process_all_sources_success(
        self,
        mock_session: Mock,
        mock_repository: Mock,
        mock_image_service: Mock,
        sample_pull_source: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test processing all active sources.

        Args:
            mock_session: Mock database session
            mock_repository: Mock repository
            mock_image_service: Mock image service
            sample_pull_source: Sample pull source
            monkeypatch: Pytest monkeypatch fixture
        """
        source2 = Mock()
        source2.id = str(uuid4())
        source2.name = "Source 2"
        source2.is_active = True

        mock_repository.get_all_active.return_value = [sample_pull_source, source2]

        service = ImagePullService(
            repository=mock_repository, image_service=mock_image_service
        )

        mock_result = {
            "source_id": str(uuid4()),
            "source_name": "Test",
            "processed_count": 5,
            "status": "success",
        }
        mock_pull_and_process = Mock(return_value=mock_result)
        monkeypatch.setattr(service, "pull_and_process_source", mock_pull_and_process)

        results = service.process_all_sources(db=mock_session, max_files_per_source=10)

        assert len(results) == 2
        assert mock_pull_and_process.call_count == 2

    def test_process_all_sources_no_active(
        self, mock_session: Mock, mock_repository: Mock, mock_image_service: Mock
    ) -> None:
        """Test processing when no active sources exist.

        Args:
            mock_session: Mock database session
            mock_repository: Mock repository
            mock_image_service: Mock image service
        """
        mock_repository.get_all_active.return_value = []

        service = ImagePullService(
            repository=mock_repository, image_service=mock_image_service
        )

        results = service.process_all_sources(db=mock_session, max_files_per_source=10)

        assert len(results) == 0

    def test_process_all_sources_with_error(
        self,
        mock_session: Mock,
        mock_repository: Mock,
        mock_image_service: Mock,
        sample_pull_source: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test processing continues after one source fails.

        Args:
            mock_session: Mock database session
            mock_repository: Mock repository
            mock_image_service: Mock image service
            sample_pull_source: Sample pull source
            monkeypatch: Pytest monkeypatch fixture
        """
        source2 = Mock()
        source2.id = str(uuid4())
        source2.name = "Source 2"
        source2.is_active = True

        mock_repository.get_all_active.return_value = [sample_pull_source, source2]

        service = ImagePullService(
            repository=mock_repository, image_service=mock_image_service
        )

        def mock_pull_side_effect(db, source_id, max_files):
            if str(source_id) == sample_pull_source.id:
                raise Exception("Processing failed")
            return {
                "source_id": str(source_id),
                "source_name": "Source 2",
                "processed_count": 3,
                "status": "success",
            }

        monkeypatch.setattr(
            service, "pull_and_process_source", Mock(side_effect=mock_pull_side_effect)
        )

        results = service.process_all_sources(db=mock_session, max_files_per_source=10)

        assert len(results) == 2
        assert results[0]["status"] == "error"
        assert "error" in results[0]
        assert results[1]["status"] == "success"


class TestImagePullServiceProcessSingleFile:
    """Test cases for _process_single_file method."""

    def test_process_single_file_success(
        self,
        mock_session: Mock,
        mock_repository: Mock,
        mock_image_service: Mock,
        mock_gateway: Mock,
        sample_pull_source: Mock,
    ) -> None:
        """Test processing a single file successfully.

        Args:
            mock_session: Mock database session
            mock_repository: Mock repository
            mock_image_service: Mock image service
            mock_gateway: Mock gateway
            sample_pull_source: Sample pull source
        """
        image_file = ImageFile(
            filename="test.jpg",
            url="https://example.com/test.jpg",
        )

        file_bytes = b"fake_image_data"
        mock_gateway.download_file.return_value = file_bytes

        upload_result = Mock()
        upload_result.image_id = uuid4()
        upload_result.detections_count = 3
        mock_image_service.upload_and_process_image.return_value = upload_result

        service = ImagePullService(
            repository=mock_repository, image_service=mock_image_service
        )

        result = service._process_single_file(
            db=mock_session,
            source=sample_pull_source,
            gateway=mock_gateway,
            image_file=image_file,
        )

        mock_gateway.download_file.assert_called_once_with(image_file)

        mock_image_service.upload_and_process_image.assert_called_once()
        call_kwargs = mock_image_service.upload_and_process_image.call_args.kwargs
        assert call_kwargs["db"] == mock_session
        assert call_kwargs["location_id"] == UUID(sample_pull_source.location_id)
        assert call_kwargs["file_bytes"] == file_bytes
        assert call_kwargs["user_id"] == UUID(sample_pull_source.user_id)
        assert call_kwargs["async_processing"] is True

        assert result["filename"] == "test.jpg"
        assert result["image_id"] == str(upload_result.image_id)
        assert result["detections_count"] == 3
