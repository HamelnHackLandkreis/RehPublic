"""Unit tests for ImageService Celery integration."""

from datetime import datetime
from typing import Dict, List
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from src.api.images.image_service import ImageService


@pytest.fixture
def mock_session() -> Mock:
    """Create mock database session.

    Returns:
        Mock Session object
    """
    return Mock()


@pytest.fixture
def mock_image_repository() -> Mock:
    """Create mock ImageRepository.

    Returns:
        Mock ImageRepository object
    """
    repository = Mock()
    repository.create = Mock()
    repository.get_by_id = Mock()
    repository.update_processed = Mock()
    return repository


@pytest.fixture
def mock_location_repository() -> Mock:
    """Create mock LocationRepository.

    Returns:
        Mock LocationRepository object
    """
    repository = Mock()
    repository.get_by_id = Mock()
    return repository


@pytest.fixture
def mock_spotting_service() -> Mock:
    """Create mock SpottingService.

    Returns:
        Mock SpottingService object
    """
    service = Mock()
    service.save_detections = Mock()
    return service


@pytest.fixture
def mock_processor_client() -> Mock:
    """Create mock ProcessorClient.

    Returns:
        Mock ProcessorClient object
    """
    client = Mock()
    client.process_image_data = Mock()
    client.process_image_async = Mock()
    return client


@pytest.fixture
def sample_location() -> Mock:
    """Create sample location object.

    Returns:
        Mock Location object
    """
    location = Mock()
    location.id = str(uuid4())
    location.name = "Test Camera Location"
    location.latitude = 48.1351
    location.longitude = 11.5820
    return location


@pytest.fixture
def sample_image() -> Mock:
    """Create sample image object.

    Returns:
        Mock Image object
    """
    image = Mock()
    image.id = str(uuid4())
    image.location_id = str(uuid4())
    image.base64_data = "base64encodedimagedata"
    image.upload_timestamp = datetime(2024, 1, 15, 10, 30, 0)
    image.processed = False
    return image


@pytest.fixture
def sample_detections() -> List[Dict]:
    """Create sample detection results.

    Returns:
        List of detection dictionaries
    """
    return [
        {
            "species": "Capreolus capreolus",
            "confidence": 0.95,
            "bbox": {"x": 100, "y": 150, "width": 200, "height": 250},
            "classification_model": "AI4GEurope",
            "is_uncertain": False,
        },
        {
            "species": "Sus scrofa",
            "confidence": 0.87,
            "bbox": {"x": 300, "y": 200, "width": 180, "height": 220},
            "classification_model": "AI4GEurope",
            "is_uncertain": False,
        },
    ]


class TestImageServiceUploadAndProcessAsync:
    """Test cases for async image upload and processing."""

    def test_upload_and_process_async_success(
        self,
        mock_session: Mock,
        mock_image_repository: Mock,
        mock_location_repository: Mock,
        mock_spotting_service: Mock,
        mock_processor_client: Mock,
        sample_location: Mock,
        sample_image: Mock,
    ) -> None:
        """Test successful async image upload and processing.

        Args:
            mock_session: Mock database session
            mock_image_repository: Mock ImageRepository
            mock_location_repository: Mock LocationRepository
            mock_spotting_service: Mock SpottingService
            mock_processor_client: Mock ProcessorClient
            sample_location: Sample location object
            sample_image: Sample image object
        """
        location_id = UUID(sample_location.id)
        file_bytes = b"fake_image_bytes"
        upload_timestamp = datetime(2024, 1, 15, 10, 30, 0)
        task_id = "celery-task-id-123"

        # Configure mocks
        mock_location_repository.get_by_id.return_value = sample_location
        mock_image_repository.create.return_value = sample_image
        mock_processor_client.process_image_async.return_value = task_id

        # Create service
        service = ImageService(
            repository=mock_image_repository,
            location_repository=mock_location_repository,
            spotting_service=mock_spotting_service,
            processor_client=mock_processor_client,
        )

        # Execute
        result = service.upload_and_process_image(
            db=mock_session,
            location_id=location_id,
            file_bytes=file_bytes,
            upload_timestamp=upload_timestamp,
            async_processing=True,
        )

        # Verify location was checked
        mock_location_repository.get_by_id.assert_called_once_with(
            mock_session, location_id
        )

        # Verify image was saved
        assert mock_image_repository.create.called
        create_call_args = mock_image_repository.create.call_args
        assert create_call_args.kwargs["db"] == mock_session
        assert create_call_args.kwargs["location_id"] == location_id
        assert create_call_args.kwargs["processed"] is False

        # Verify async processing was dispatched
        mock_processor_client.process_image_async.assert_called_once()
        async_call_args = mock_processor_client.process_image_async.call_args
        assert async_call_args.kwargs["image_id"] == UUID(sample_image.id)
        assert async_call_args.kwargs["image_base64"] == sample_image.base64_data
        assert async_call_args.kwargs["model_region"] == "europe"
        assert async_call_args.kwargs["timestamp"] == upload_timestamp

        # Verify synchronous processing was NOT called
        assert not mock_processor_client.process_image_data.called
        assert not mock_spotting_service.save_detections.called

        # Verify result
        assert result.image_id == UUID(sample_image.id)
        assert result.location_id == UUID(sample_image.location_id)
        assert result.upload_timestamp == sample_image.upload_timestamp
        assert result.detections_count == 0  # Not processed yet
        assert result.detected_species == []
        assert result.task_id == task_id

    def test_upload_and_process_sync_success(
        self,
        mock_session: Mock,
        mock_image_repository: Mock,
        mock_location_repository: Mock,
        mock_spotting_service: Mock,
        mock_processor_client: Mock,
        sample_location: Mock,
        sample_image: Mock,
        sample_detections: List[Dict],
    ) -> None:
        """Test successful synchronous image upload and processing.

        Args:
            mock_session: Mock database session
            mock_image_repository: Mock ImageRepository
            mock_location_repository: Mock LocationRepository
            mock_spotting_service: Mock SpottingService
            mock_processor_client: Mock ProcessorClient
            sample_location: Sample location object
            sample_image: Sample image object
            sample_detections: Sample detection results
        """
        location_id = UUID(sample_location.id)
        file_bytes = b"fake_image_bytes"
        upload_timestamp = datetime(2024, 1, 15, 10, 30, 0)

        # Configure mocks
        mock_location_repository.get_by_id.return_value = sample_location
        mock_image_repository.create.return_value = sample_image
        mock_processor_client.process_image_data.return_value = sample_detections

        # Create service
        service = ImageService(
            repository=mock_image_repository,
            location_repository=mock_location_repository,
            spotting_service=mock_spotting_service,
            processor_client=mock_processor_client,
        )

        # Execute
        result = service.upload_and_process_image(
            db=mock_session,
            location_id=location_id,
            file_bytes=file_bytes,
            upload_timestamp=upload_timestamp,
            async_processing=False,
        )

        # Verify async processing was NOT called
        assert not mock_processor_client.process_image_async.called

        # Verify synchronous processing was called
        assert mock_processor_client.process_image_data.called

        # Verify detections were saved
        mock_spotting_service.save_detections.assert_called_once()
        save_call_args = mock_spotting_service.save_detections.call_args
        assert save_call_args[0][0] == mock_session
        assert save_call_args[0][1] == UUID(sample_image.id)
        assert save_call_args[0][2] == sample_detections

        # Verify image was marked as processed
        mock_image_repository.update_processed.assert_called_once_with(
            mock_session, UUID(sample_image.id), processed=True
        )

        # Verify result
        assert result.image_id == UUID(sample_image.id)
        assert result.detections_count == 2
        assert result.detected_species == ["Capreolus capreolus", "Sus scrofa"]
        assert result.task_id is None  # No task ID for sync processing

    def test_upload_and_process_location_not_found(
        self,
        mock_session: Mock,
        mock_image_repository: Mock,
        mock_location_repository: Mock,
        mock_spotting_service: Mock,
        mock_processor_client: Mock,
    ) -> None:
        """Test error when location does not exist.

        Args:
            mock_session: Mock database session
            mock_image_repository: Mock ImageRepository
            mock_location_repository: Mock LocationRepository
            mock_spotting_service: Mock SpottingService
            mock_processor_client: Mock ProcessorClient
        """
        location_id = uuid4()
        file_bytes = b"fake_image_bytes"

        # Configure mock to return None (location not found)
        mock_location_repository.get_by_id.return_value = None

        # Create service
        service = ImageService(
            repository=mock_image_repository,
            location_repository=mock_location_repository,
            spotting_service=mock_spotting_service,
            processor_client=mock_processor_client,
        )

        # Execute and expect error
        with pytest.raises(ValueError, match="Location with id .* not found"):
            service.upload_and_process_image(
                db=mock_session,
                location_id=location_id,
                file_bytes=file_bytes,
                async_processing=True,
            )

        # Verify no image was created
        assert not mock_image_repository.create.called

        # Verify no processing was triggered
        assert not mock_processor_client.process_image_async.called
        assert not mock_processor_client.process_image_data.called

    def test_upload_and_process_async_default_timestamp(
        self,
        mock_session: Mock,
        mock_image_repository: Mock,
        mock_location_repository: Mock,
        mock_spotting_service: Mock,
        mock_processor_client: Mock,
        sample_location: Mock,
        sample_image: Mock,
    ) -> None:
        """Test async processing without explicit timestamp.

        Args:
            mock_session: Mock database session
            mock_image_repository: Mock ImageRepository
            mock_location_repository: Mock LocationRepository
            mock_spotting_service: Mock SpottingService
            mock_processor_client: Mock ProcessorClient
            sample_location: Sample location object
            sample_image: Sample image object
        """
        location_id = UUID(sample_location.id)
        file_bytes = b"fake_image_bytes"

        # Configure mocks
        mock_location_repository.get_by_id.return_value = sample_location
        mock_image_repository.create.return_value = sample_image
        mock_processor_client.process_image_async.return_value = "task-id"

        # Create service
        service = ImageService(
            repository=mock_image_repository,
            location_repository=mock_location_repository,
            spotting_service=mock_spotting_service,
            processor_client=mock_processor_client,
        )

        # Execute without timestamp
        result = service.upload_and_process_image(
            db=mock_session,
            location_id=location_id,
            file_bytes=file_bytes,
            upload_timestamp=None,
            async_processing=True,
        )

        # Verify async processing was called with None timestamp
        async_call_args = mock_processor_client.process_image_async.call_args
        assert async_call_args.kwargs["timestamp"] is None

        # Verify result
        assert result.task_id == "task-id"


class TestImageServiceMarkAsProcessed:
    """Test cases for marking images as processed."""

    def test_mark_as_processed(
        self,
        mock_session: Mock,
        mock_image_repository: Mock,
    ) -> None:
        """Test marking image as processed.

        Args:
            mock_session: Mock database session
            mock_image_repository: Mock ImageRepository
        """
        image_id = uuid4()

        # Create service
        service = ImageService(repository=mock_image_repository)

        # Execute
        service.mark_as_processed(db=mock_session, image_id=image_id)

        # Verify repository method was called
        mock_image_repository.update_processed.assert_called_once_with(
            mock_session, image_id, processed=True
        )
