"""Unit tests for Celery image processing tasks."""

from datetime import datetime
from typing import Dict, List
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest
from celery.exceptions import Retry


@pytest.fixture
def mock_session() -> Mock:
    """Create mock database session.

    Returns:
        Mock Session object
    """
    session = Mock()
    session.commit = Mock()
    session.close = Mock()
    return session


@pytest.fixture
def mock_image_service() -> Mock:
    """Create mock ImageService.

    Returns:
        Mock ImageService object
    """
    service = Mock()
    service.process_image = Mock()
    service.mark_as_processed = Mock()
    service.spotting_service = Mock()
    service.spotting_service.save_detections = Mock()
    return service


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


class TestProcessImageTask:
    """Test cases for process_image_task Celery task."""

    def test_process_image_task_success(
        self,
        mock_session: Mock,
        mock_image_service: Mock,
        sample_detections: List[Dict],
    ) -> None:
        """Test successful image processing task execution.

        Args:
            mock_session: Mock database session
            mock_image_service: Mock ImageService
            sample_detections: Sample detection results
        """
        from src.api.images import images_tasks

        image_id = str(uuid4())
        image_base64 = "base64encodedimagedata"
        model_region = "europe"
        timestamp = "2024-01-15T10:30:00"

        # Configure mock service to return detections
        mock_image_service.process_image.return_value = sample_detections

        # Mock dependencies
        with patch.object(images_tasks, "SessionLocal", return_value=mock_session):
            with patch.object(
                images_tasks.ImageService, "factory", return_value=mock_image_service
            ):
                # Create mock self for bound task
                mock_self = Mock()
                mock_self.request = Mock(retries=0)
                mock_self.retry = Mock()

                # Call the task function directly
                result = images_tasks.process_image_task(
                    mock_self,
                    image_id=image_id,
                    image_base64=image_base64,
                    model_region=model_region,
                    timestamp=timestamp,
                )

        # Verify process_image was called with correct image
        assert mock_image_service.process_image.called
        call_args = mock_image_service.process_image.call_args
        assert call_args.kwargs["db"] == mock_session
        processed_image = call_args.kwargs["image"]
        assert processed_image.id == image_id
        assert processed_image.base64_data == image_base64

        # Verify save_detections was called
        assert mock_image_service.spotting_service.save_detections.called
        save_call_args = mock_image_service.spotting_service.save_detections.call_args
        assert save_call_args.kwargs["db"] == mock_session
        assert save_call_args.kwargs["image_id"] == UUID(image_id)
        assert save_call_args.kwargs["detections"] == sample_detections
        assert isinstance(save_call_args.kwargs["detection_timestamp"], datetime)

        # Verify mark_as_processed was called
        assert mock_image_service.mark_as_processed.called
        mark_call_args = mock_image_service.mark_as_processed.call_args
        assert mark_call_args.kwargs["db"] == mock_session
        assert mark_call_args.kwargs["image_id"] == UUID(image_id)

        # Verify session was committed and closed
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

        # Verify result
        assert result["image_id"] == image_id
        assert result["detections_count"] == 2
        assert result["detected_species"] == [
            "Capreolus capreolus",
            "Sus scrofa",
        ]
        assert result["success"] is True

    def test_process_image_task_no_detections(
        self,
        mock_session: Mock,
        mock_image_service: Mock,
    ) -> None:
        """Test task execution when no animals are detected.

        Args:
            mock_session: Mock database session
            mock_image_service: Mock ImageService
        """
        from src.api.images import images_tasks

        image_id = str(uuid4())
        image_base64 = "base64encodedimagedata"

        # Configure mock service to return empty detections
        mock_image_service.process_image.return_value = []

        # Mock dependencies
        with patch.object(images_tasks, "SessionLocal", return_value=mock_session):
            with patch.object(
                images_tasks.ImageService, "factory", return_value=mock_image_service
            ):
                mock_self = Mock()
                mock_self.request = Mock(retries=0)

                # Execute task
                result = images_tasks.process_image_task(
                    mock_self,
                    image_id=image_id,
                    image_base64=image_base64,
                )

        # Verify save_detections was not called (no detections)
        assert not mock_image_service.spotting_service.save_detections.called

        # Verify mark_as_processed was still called
        assert mock_image_service.mark_as_processed.called

        # Verify result
        assert result["detections_count"] == 0
        assert result["detected_species"] == []
        assert result["success"] is True

    def test_process_image_task_without_timestamp(
        self,
        mock_session: Mock,
        mock_image_service: Mock,
        sample_detections: List[Dict],
    ) -> None:
        """Test task execution without timestamp parameter.

        Args:
            mock_session: Mock database session
            mock_image_service: Mock ImageService
            sample_detections: Sample detection results
        """
        from src.api.images import images_tasks

        image_id = str(uuid4())
        image_base64 = "base64encodedimagedata"

        # Configure mock service
        mock_image_service.process_image.return_value = sample_detections

        # Mock dependencies
        with patch.object(images_tasks, "SessionLocal", return_value=mock_session):
            with patch.object(
                images_tasks.ImageService, "factory", return_value=mock_image_service
            ):
                mock_self = Mock()
                mock_self.request = Mock(retries=0)

                # Execute task without timestamp
                result = images_tasks.process_image_task(
                    mock_self,
                    image_id=image_id,
                    image_base64=image_base64,
                    timestamp=None,
                )

        # Verify save_detections was called with None timestamp
        save_call_args = mock_image_service.spotting_service.save_detections.call_args
        assert save_call_args.kwargs["detection_timestamp"] is None

        # Verify success
        assert result["success"] is True

    def test_process_image_task_retry_on_error(
        self,
        mock_session: Mock,
        mock_image_service: Mock,
    ) -> None:
        """Test task retry mechanism on processing error.

        Args:
            mock_session: Mock database session
            mock_image_service: Mock ImageService
        """
        from src.api.images import images_tasks

        image_id = str(uuid4())
        image_base64 = "base64encodedimagedata"

        # Configure mock service to raise exception
        processing_error = ValueError("Model loading failed")
        mock_image_service.process_image.side_effect = processing_error

        # Create mock task with retry method
        mock_self = Mock()
        mock_self.request = Mock(retries=0)
        mock_self.retry = Mock(side_effect=Retry())

        # Mock dependencies
        with patch.object(images_tasks, "SessionLocal", return_value=mock_session):
            with patch.object(
                images_tasks.ImageService, "factory", return_value=mock_image_service
            ):
                # Execute task and expect Retry exception
                with pytest.raises(Retry):
                    images_tasks.process_image_task(
                        mock_self,
                        image_id=image_id,
                        image_base64=image_base64,
                    )

        # Verify retry was called with correct parameters
        mock_self.retry.assert_called_once()
        retry_call_args = mock_self.retry.call_args
        assert retry_call_args.kwargs["exc"] == processing_error
        assert retry_call_args.kwargs["countdown"] == 1  # 2^0

        # Verify session was closed even on error
        mock_session.close.assert_called_once()

    def test_process_image_task_exponential_backoff(
        self,
        mock_session: Mock,
        mock_image_service: Mock,
    ) -> None:
        """Test exponential backoff on retries.

        Args:
            mock_session: Mock database session
            mock_image_service: Mock ImageService
        """
        from src.api.images import images_tasks

        image_id = str(uuid4())
        image_base64 = "base64encodedimagedata"

        # Configure mock service to raise exception
        mock_image_service.process_image.side_effect = ValueError("Error")

        # Test different retry counts
        for retry_count in [0, 1, 2]:
            mock_self = Mock()
            mock_self.request = Mock(retries=retry_count)
            mock_self.retry = Mock(side_effect=Retry())

            with patch.object(images_tasks, "SessionLocal", return_value=mock_session):
                with patch.object(
                    images_tasks.ImageService,
                    "factory",
                    return_value=mock_image_service,
                ):
                    with pytest.raises(Retry):
                        images_tasks.process_image_task(
                            mock_self,
                            image_id=image_id,
                            image_base64=image_base64,
                        )

            # Verify countdown follows exponential backoff: 2^retries
            retry_call_args = mock_self.retry.call_args
            expected_countdown = 2**retry_count
            assert retry_call_args.kwargs["countdown"] == expected_countdown

    def test_process_image_task_session_cleanup_on_error(
        self,
        mock_session: Mock,
        mock_image_service: Mock,
    ) -> None:
        """Test database session is properly closed on error.

        Args:
            mock_session: Mock database session
            mock_image_service: Mock ImageService
        """
        from src.api.images import images_tasks

        image_id = str(uuid4())
        image_base64 = "base64encodedimagedata"

        # Configure mock service to raise exception
        mock_image_service.process_image.side_effect = RuntimeError("DB error")

        # Create mock task
        mock_self = Mock()
        mock_self.request = Mock(retries=0)
        mock_self.retry = Mock(side_effect=Retry())

        # Mock dependencies
        with patch.object(images_tasks, "SessionLocal", return_value=mock_session):
            with patch.object(
                images_tasks.ImageService, "factory", return_value=mock_image_service
            ):
                # Execute task
                with pytest.raises(Retry):
                    images_tasks.process_image_task(
                        mock_self,
                        image_id=image_id,
                        image_base64=image_base64,
                    )

        # Verify session was closed despite error
        mock_session.close.assert_called_once()

        # Verify commit was not called due to error
        assert not mock_session.commit.called

    def test_process_image_task_different_regions(
        self,
        mock_session: Mock,
        mock_image_service: Mock,
        sample_detections: List[Dict],
    ) -> None:
        """Test task execution with different model regions.

        Args:
            mock_session: Mock database session
            mock_image_service: Mock ImageService
            sample_detections: Sample detection results
        """
        from src.api.images import images_tasks

        image_id = str(uuid4())
        image_base64 = "base64encodedimagedata"

        mock_image_service.process_image.return_value = sample_detections

        # Test with different regions
        for region in ["europe", "amazon", "hamelin"]:
            with patch.object(images_tasks, "SessionLocal", return_value=mock_session):
                with patch.object(
                    images_tasks.ImageService,
                    "factory",
                    return_value=mock_image_service,
                ):
                    mock_self = Mock()
                    mock_self.request = Mock(retries=0)

                    result = images_tasks.process_image_task(
                        mock_self,
                        image_id=image_id,
                        image_base64=image_base64,
                        model_region=region,
                    )

                    assert result["success"] is True
