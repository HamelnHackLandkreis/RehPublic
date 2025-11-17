"""Simplified unit tests for Celery image processing tasks.

Note: These tests focus on the integration points and mocking rather than
testing the Celery task decorator itself, which is better tested in integration tests.
"""

from unittest.mock import Mock, patch
from uuid import uuid4


class TestProcessImageTaskIntegration:
    """Test cases for process_image_task integration points."""

    def test_task_can_be_dispatched_async(self) -> None:
        """Test that task can be dispatched asynchronously.

        Returns:
            None
        """
        from src.api.images.images_tasks import process_image_task

        # Verify task has async dispatch methods
        assert hasattr(process_image_task, "delay")
        assert hasattr(process_image_task, "apply_async")
        assert callable(process_image_task.delay)
        assert callable(process_image_task.apply_async)

    def test_task_configuration(self) -> None:
        """Test task has correct configuration.

        Returns:
            None
        """
        from src.api.images.images_tasks import process_image_task

        # Verify task configuration
        assert process_image_task.name == "images.process_image"
        assert process_image_task.max_retries == 3

    def test_task_registered_with_celery_app(self) -> None:
        """Test task is registered with Celery app.

        Returns:
            None
        """
        from src.celery_app import celery_app

        # Verify task module is included
        assert "src.api.images.images_tasks" in celery_app.conf.include


class TestImageServiceProcessingLogic:
    """Test the business logic that the Celery task uses."""

    def test_image_service_process_image(self) -> None:
        """Test ImageService.process_image method.

        Returns:
            None
        """
        import base64
        from src.api.images.image_service import ImageService
        from src.api.images.image_models import Image

        # Mock dependencies
        mock_processor = Mock()
        mock_processor.process_image_data.return_value = [
            {
                "species": "Capreolus capreolus",
                "confidence": 0.95,
                "bbox": {"x": 100, "y": 150, "width": 200, "height": 250},
            }
        ]

        service = ImageService(processor_client=mock_processor)

        # Create test image with valid base64 data
        test_image = Image()
        test_image.id = str(uuid4())
        # Use valid base64 encoded data
        test_image.base64_data = base64.b64encode(b"fake_image_data").decode("utf-8")

        mock_db = Mock()

        # Execute
        result = service.process_image(db=mock_db, image=test_image)

        # Verify
        assert len(result) == 1
        assert result[0]["species"] == "Capreolus capreolus"
        mock_processor.process_image_data.assert_called_once()

    def test_image_service_mark_as_processed(self) -> None:
        """Test ImageService.mark_as_processed method.

        Returns:
            None
        """
        from src.api.images.image_service import ImageService

        mock_repository = Mock()
        service = ImageService(repository=mock_repository)

        image_id = uuid4()
        mock_db = Mock()

        # Execute
        service.mark_as_processed(db=mock_db, image_id=image_id)

        # Verify
        mock_repository.update_processed.assert_called_once_with(
            mock_db, image_id, processed=True
        )


class TestProcessorClientIntegration:
    """Test ProcessorClient integration with Celery tasks."""

    def test_processor_client_async_dispatch(self) -> None:
        """Test ProcessorClient.process_image_async dispatches to Celery.

        Returns:
            None
        """
        from src.adapters.image_processor_adapter import ProcessorClient

        with patch(
            "src.adapters.image_processor_adapter.process_image_task.delay"
        ) as mock_delay:
            mock_task = Mock()
            mock_task.id = "test-task-id"
            mock_delay.return_value = mock_task

            client = ProcessorClient()
            image_id = uuid4()

            task_id = client.process_image_async(
                image_id=image_id,
                image_base64="base64data",
                model_region="europe",
            )

            # Verify task was dispatched
            assert task_id == "test-task-id"
            mock_delay.assert_called_once()
            call_args = mock_delay.call_args
            assert call_args.kwargs["image_id"] == str(image_id)
            assert call_args.kwargs["model_region"] == "europe"
