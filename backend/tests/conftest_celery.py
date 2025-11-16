"""Pytest configuration for Celery tests.

This module provides fixtures and configuration for testing Celery tasks.
"""

import pytest
from celery import Celery
from unittest.mock import Mock


@pytest.fixture
def celery_config() -> dict:
    """Celery configuration for testing.

    Returns:
        Dictionary with Celery test configuration
    """
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": True,  # Execute tasks synchronously
        "task_eager_propagates": True,  # Propagate exceptions
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "UTC",
        "enable_utc": True,
    }


@pytest.fixture
def celery_app(celery_config: dict) -> Celery:
    """Create Celery app for testing.

    Args:
        celery_config: Celery configuration

    Returns:
        Configured Celery app instance
    """
    app = Celery("test_app")
    app.conf.update(celery_config)
    return app


@pytest.fixture
def mock_celery_task() -> Mock:
    """Create mock Celery task for testing.

    Returns:
        Mock task object with common Celery task attributes
    """
    task = Mock()
    task.request = Mock()
    task.request.retries = 0
    task.request.id = "test-task-id"
    task.retry = Mock()
    task.apply_async = Mock()
    return task
