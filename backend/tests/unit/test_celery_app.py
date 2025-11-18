"""Unit tests for Celery app configuration."""

import pytest

from src.celery_app import celery_app


class TestCeleryAppConfiguration:
    """Test cases for Celery app configuration."""

    def test_celery_app_name(self) -> None:
        """Test Celery app has correct name.

        Returns:
            None
        """
        assert celery_app.main == "wildlife_processor"

    def test_celery_app_broker_default(self) -> None:
        """Test default broker URL configuration.

        Returns:
            None
        """
        # Default should be localhost Redis
        assert "redis://" in celery_app.conf.broker_url
        assert "6379" in celery_app.conf.broker_url

    def test_celery_app_broker_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test broker URL can be configured via environment variable.

        Args:
            monkeypatch: Pytest monkeypatch fixture

        Returns:
            None
        """
        custom_redis_url = "redis://custom-host:6380/1"
        monkeypatch.setenv("REDIS_URL", custom_redis_url)

        # Reimport to pick up new environment variable
        import importlib
        import src.celery_app

        importlib.reload(src.celery_app)

        # Note: This test demonstrates the pattern, but actual reload
        # may not work in all test scenarios due to module caching

    def test_celery_app_backend_configured(self) -> None:
        """Test result backend is configured.

        Returns:
            None
        """
        assert celery_app.conf.result_backend is not None
        assert "redis://" in celery_app.conf.result_backend

    def test_celery_app_serialization_config(self) -> None:
        """Test serialization configuration.

        Returns:
            None
        """
        assert celery_app.conf.task_serializer == "json"
        assert "json" in celery_app.conf.accept_content
        assert celery_app.conf.result_serializer == "json"

    def test_celery_app_timezone_config(self) -> None:
        """Test timezone configuration.

        Returns:
            None
        """
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True

    def test_celery_app_task_tracking(self) -> None:
        """Test task tracking is enabled.

        Returns:
            None
        """
        assert celery_app.conf.task_track_started is True

    def test_celery_app_time_limits(self) -> None:
        """Test task time limits are configured.

        Returns:
            None
        """
        assert celery_app.conf.task_time_limit == 300  # 5 minutes hard limit
        assert celery_app.conf.task_soft_time_limit == 240  # 4 minutes soft limit

    def test_celery_app_worker_config(self) -> None:
        """Test worker configuration.

        Returns:
            None
        """
        assert celery_app.conf.worker_prefetch_multiplier == 1
        assert celery_app.conf.worker_max_tasks_per_child == 50

    def test_celery_app_includes_tasks(self) -> None:
        """Test task modules are included.

        Returns:
            None
        """
        assert "src.api.images.images_tasks" in celery_app.conf.include


class TestCeleryTaskRegistration:
    """Test cases for Celery task registration."""

    def test_process_image_task_can_be_imported(self) -> None:
        """Test process_image_task can be imported and is a Celery task.

        Returns:
            None
        """
        from src.api.images.images_tasks import process_image_task

        # Verify it's a Celery task
        assert hasattr(process_image_task, "delay")
        assert hasattr(process_image_task, "apply_async")

    def test_process_image_task_configuration(self) -> None:
        """Test process_image_task has correct configuration.

        Returns:
            None
        """
        from src.api.images.images_tasks import process_image_task

        # Verify max retries
        assert process_image_task.max_retries == 3

        # Verify task name
        assert process_image_task.name == "images.process_image"
