"""Integration tests for Celery task processing workflow."""

import base64
from datetime import datetime
from typing import Any, Dict
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from src.api.database import SessionLocal
from src.api.images.image_models import Image
from src.api.images.image_service import ImageService
from src.api.images.images_tasks import process_image_task
from src.api.locations.location_models import Location, Spotting


@pytest.fixture
def db_session() -> Session:
    """Create database session for integration tests.

    Returns:
        Database session
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_location(db_session: Session) -> Location:
    """Create test location in database.

    Args:
        db_session: Database session

    Returns:
        Created Location object
    """
    location = Location(
        name="Test Camera Location",
        latitude=48.1351,
        longitude=11.5820,
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)
    return location


@pytest.fixture
def test_image(db_session: Session, test_location: Location) -> Image:
    """Create test image in database.

    Args:
        db_session: Database session
        test_location: Test location

    Returns:
        Created Image object
    """
    # Create simple base64 encoded image data
    image_data = base64.b64encode(b"fake_image_data").decode("utf-8")

    image = Image(
        location_id=test_location.id,
        base64_data=image_data,
        upload_timestamp=datetime(2024, 1, 15, 10, 30, 0),
        processed=False,
    )
    db_session.add(image)
    db_session.commit()
    db_session.refresh(image)
    return image


@pytest.fixture
def sample_detections() -> list[Dict[str, Any]]:
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


class TestCeleryTaskIntegration:
    """Integration tests for Celery task processing."""

    def test_process_image_task_full_workflow(
        self,
        db_session: Session,
        test_image: Image,
        sample_detections: list[Dict[str, Any]],
    ) -> None:
        """Test complete image processing workflow through Celery task.

        Args:
            db_session: Database session
            test_image: Test image object
            sample_detections: Sample detection results
        """
        # Mock the processor to avoid loading actual ML models
        with patch(
            "src.api.images.image_service.ProcessorClient"
        ) as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process_image_data.return_value = sample_detections
            mock_processor_class.return_value = mock_processor

            # Execute task
            result = process_image_task(
                Mock(request=Mock(retries=0)),
                image_id=str(test_image.id),
                image_base64=test_image.base64_data,
                model_region="europe",
                timestamp="2024-01-15T10:30:00",
            )

            # Verify task result
            assert result["success"] is True
            assert result["image_id"] == str(test_image.id)
            assert result["detections_count"] == 2
            assert result["detected_species"] == [
                "Capreolus capreolus",
                "Sus scrofa",
            ]

            # Verify image was marked as processed in database
            db_session.refresh(test_image)
            assert test_image.processed is True

            # Verify spottings were saved to database
            spottings = (
                db_session.query(Spotting)
                .filter(Spotting.image_id == test_image.id)
                .all()
            )
            assert len(spottings) == 2

            # Verify first spotting
            spotting1 = spottings[0]
            assert spotting1.species == "Capreolus capreolus"
            assert spotting1.confidence == 0.95
            assert spotting1.bbox_x == 100
            assert spotting1.bbox_y == 150
            assert spotting1.bbox_width == 200
            assert spotting1.bbox_height == 250
            assert spotting1.classification_model == "AI4GEurope"
            assert spotting1.is_uncertain is False

            # Verify second spotting
            spotting2 = spottings[1]
            assert spotting2.species == "Sus scrofa"
            assert spotting2.confidence == 0.87

    def test_process_image_task_no_detections(
        self,
        db_session: Session,
        test_image: Image,
    ) -> None:
        """Test task workflow when no animals are detected.

        Args:
            db_session: Database session
            test_image: Test image object
        """
        # Mock the processor to return no detections
        with patch(
            "src.api.images.image_service.ProcessorClient"
        ) as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process_image_data.return_value = []
            mock_processor_class.return_value = mock_processor

            # Execute task
            result = process_image_task(
                Mock(request=Mock(retries=0)),
                image_id=str(test_image.id),
                image_base64=test_image.base64_data,
            )

            # Verify task result
            assert result["success"] is True
            assert result["detections_count"] == 0
            assert result["detected_species"] == []

            # Verify image was still marked as processed
            db_session.refresh(test_image)
            assert test_image.processed is True

            # Verify no spottings were saved
            spottings = (
                db_session.query(Spotting)
                .filter(Spotting.image_id == test_image.id)
                .all()
            )
            assert len(spottings) == 0

    def test_async_processing_dispatch(
        self,
        db_session: Session,
        test_location: Location,
    ) -> None:
        """Test async processing task dispatch.

        Args:
            db_session: Database session
            test_location: Test location
        """
        file_bytes = b"fake_image_bytes"
        upload_timestamp = datetime(2024, 1, 15, 10, 30, 0)

        # Mock Celery task dispatch
        with patch(
            "src.adapters.image_processor_adapter.process_image_task.delay"
        ) as mock_delay:
            mock_task = Mock()
            mock_task.id = "celery-task-id-123"
            mock_delay.return_value = mock_task

            # Create service and upload image
            service = ImageService.factory()
            result = service.upload_and_process_image(
                db=db_session,
                location_id=UUID(test_location.id),
                file_bytes=file_bytes,
                upload_timestamp=upload_timestamp,
                async_processing=True,
            )

            # Verify task was dispatched
            assert mock_delay.called
            call_args = mock_delay.call_args

            # Verify task parameters
            assert "image_id" in call_args.kwargs
            assert call_args.kwargs["model_region"] == "europe"
            assert call_args.kwargs["timestamp_str"] == upload_timestamp.isoformat()

            # Verify result contains task ID
            assert result.task_id == "celery-task-id-123"
            assert result.detections_count == 0  # Not processed yet

            # Verify image was saved but not processed
            image = (
                db_session.query(Image).filter(Image.id == str(result.image_id)).first()
            )
            assert image is not None
            assert image.processed is False

    def test_sync_processing_immediate(
        self,
        db_session: Session,
        test_location: Location,
        sample_detections: list[Dict[str, Any]],
    ) -> None:
        """Test synchronous processing completes immediately.

        Args:
            db_session: Database session
            test_location: Test location
            sample_detections: Sample detection results
        """
        file_bytes = b"fake_image_bytes"
        upload_timestamp = datetime(2024, 1, 15, 10, 30, 0)

        # Mock the processor
        with patch(
            "src.api.images.image_service.ProcessorClient"
        ) as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process_image_data.return_value = sample_detections
            mock_processor_class.return_value = mock_processor

            # Create service and upload image
            service = ImageService.factory()
            result = service.upload_and_process_image(
                db=db_session,
                location_id=UUID(test_location.id),
                file_bytes=file_bytes,
                upload_timestamp=upload_timestamp,
                async_processing=False,
            )

            # Verify result shows immediate processing
            assert result.task_id is None  # No async task
            assert result.detections_count == 2
            assert result.detected_species == [
                "Capreolus capreolus",
                "Sus scrofa",
            ]

            # Verify image was processed
            image = (
                db_session.query(Image).filter(Image.id == str(result.image_id)).first()
            )
            assert image is not None
            assert image.processed is True

            # Verify spottings were saved
            spottings = (
                db_session.query(Spotting)
                .filter(Spotting.image_id == str(result.image_id))
                .all()
            )
            assert len(spottings) == 2


class TestCeleryTaskErrorHandling:
    """Integration tests for Celery task error handling."""

    def test_task_handles_processing_error(
        self,
        db_session: Session,
        test_image: Image,
    ) -> None:
        """Test task handles processing errors gracefully.

        Args:
            db_session: Database session
            test_image: Test image object
        """
        # Mock the processor to raise an error
        with patch(
            "src.api.images.image_service.ProcessorClient"
        ) as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process_image_data.side_effect = RuntimeError(
                "Model loading failed"
            )
            mock_processor_class.return_value = mock_processor

            # Create mock task with retry
            mock_task = Mock()
            mock_task.request = Mock(retries=0)
            mock_task.retry = Mock(side_effect=Exception("Retry triggered"))

            # Execute task and expect retry
            with pytest.raises(Exception, match="Retry triggered"):
                process_image_task(
                    mock_task,
                    image_id=str(test_image.id),
                    image_base64=test_image.base64_data,
                )

            # Verify retry was called
            assert mock_task.retry.called

            # Verify image was not marked as processed
            db_session.refresh(test_image)
            assert test_image.processed is False

    def test_task_database_rollback_on_error(
        self,
        db_session: Session,
        test_image: Image,
        sample_detections: list[Dict[str, Any]],
    ) -> None:
        """Test database changes are not committed on error.

        Args:
            db_session: Database session
            test_image: Test image object
            sample_detections: Sample detection results
        """
        # Mock the processor to succeed but mark_as_processed to fail
        with patch(
            "src.api.images.image_service.ProcessorClient"
        ) as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process_image_data.return_value = sample_detections
            mock_processor_class.return_value = mock_processor

            with patch(
                "src.api.images.image_service.ImageService.mark_as_processed"
            ) as mock_mark:
                mock_mark.side_effect = RuntimeError("Database error")

                # Create mock task
                mock_task = Mock()
                mock_task.request = Mock(retries=0)
                mock_task.retry = Mock(side_effect=Exception("Retry triggered"))

                # Execute task and expect retry
                with pytest.raises(Exception, match="Retry triggered"):
                    process_image_task(
                        mock_task,
                        image_id=str(test_image.id),
                        image_base64=test_image.base64_data,
                    )

                # Verify no spottings were committed (transaction rolled back)
                spottings_count = (
                    db_session.query(Spotting)
                    .filter(Spotting.image_id == test_image.id)
                    .count()
                )
                # Note: In real scenario, transaction would be rolled back
                # This test demonstrates the error handling flow
                assert spottings_count == 0
