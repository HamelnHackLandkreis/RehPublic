"""Unit tests for image pull tasks."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.api.image_pull_sources.image_pull_tasks import pull_all_sources_task


@pytest.fixture
def mock_session_local(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock SessionLocal for database sessions.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Mock SessionLocal
    """
    mock_session = Mock()
    mock_session.close = Mock()

    mock_session_factory = Mock(return_value=mock_session)

    monkeypatch.setattr(
        "src.api.image_pull_sources.image_pull_tasks.SessionLocal",
        mock_session_factory,
    )

    return mock_session


@pytest.fixture
def mock_image_pull_service(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock ImagePullService.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Mock ImagePullService
    """
    mock_service = Mock()
    mock_service.process_all_sources = Mock()

    mock_service_class = Mock()
    mock_service_class.factory.return_value = mock_service

    monkeypatch.setattr(
        "src.api.image_pull_sources.image_pull_tasks.ImagePullService",
        mock_service_class,
    )

    return mock_service


class TestPullAllSourcesTask:
    """Test cases for pull_all_sources_task."""

    def test_pull_all_sources_task_success(
        self,
        mock_session_local: Mock,
        mock_image_pull_service: Mock,
    ) -> None:
        """Test successful execution of pull_all_sources_task.

        Args:
            mock_session_local: Mock SessionLocal
            mock_image_pull_service: Mock ImagePullService
        """
        source_results = [
            {
                "source_id": str(uuid4()),
                "source_name": "Source 1",
                "processed_count": 5,
                "status": "success",
            },
            {
                "source_id": str(uuid4()),
                "source_name": "Source 2",
                "processed_count": 3,
                "status": "success",
            },
        ]

        mock_image_pull_service.process_all_sources.return_value = source_results

        result = pull_all_sources_task(max_files_per_source=10)

        assert result["total_sources"] == 2
        assert result["total_images_processed"] == 8
        assert result["success"] is True
        assert len(result["sources"]) == 2

        mock_image_pull_service.process_all_sources.assert_called_once()
        call_kwargs = mock_image_pull_service.process_all_sources.call_args.kwargs
        assert call_kwargs["max_files_per_source"] == 10

        mock_session_local.close.assert_called_once()

    def test_pull_all_sources_task_no_sources(
        self,
        mock_session_local: Mock,
        mock_image_pull_service: Mock,
    ) -> None:
        """Test task execution when no sources exist.

        Args:
            mock_session_local: Mock SessionLocal
            mock_image_pull_service: Mock ImagePullService
        """
        mock_image_pull_service.process_all_sources.return_value = []

        result = pull_all_sources_task(max_files_per_source=10)

        assert result["total_sources"] == 0
        assert result["total_images_processed"] == 0
        assert result["success"] is True
        assert len(result["sources"]) == 0

        mock_session_local.close.assert_called_once()

    def test_pull_all_sources_task_with_errors(
        self,
        mock_session_local: Mock,
        mock_image_pull_service: Mock,
    ) -> None:
        """Test task execution when service raises exception.

        Args:
            mock_session_local: Mock SessionLocal
            mock_image_pull_service: Mock ImagePullService
        """
        mock_image_pull_service.process_all_sources.side_effect = Exception(
            "Service failed"
        )

        result = pull_all_sources_task(max_files_per_source=10)

        assert result["total_sources"] == 0
        assert result["total_images_processed"] == 0
        assert result["success"] is False
        assert "error" in result
        assert "Service failed" in result["error"]

        mock_session_local.close.assert_called_once()

    def test_pull_all_sources_task_closes_session_on_error(
        self,
        mock_session_local: Mock,
        mock_image_pull_service: Mock,
    ) -> None:
        """Test that session is closed even when error occurs.

        Args:
            mock_session_local: Mock SessionLocal
            mock_image_pull_service: Mock ImagePullService
        """
        mock_image_pull_service.process_all_sources.side_effect = Exception(
            "Unexpected error"
        )

        result = pull_all_sources_task(max_files_per_source=5)

        assert result["success"] is False
        mock_session_local.close.assert_called_once()

    def test_pull_all_sources_task_calculates_totals(
        self,
        mock_session_local: Mock,
        mock_image_pull_service: Mock,
    ) -> None:
        """Test that task correctly calculates totals from source results.

        Args:
            mock_session_local: Mock SessionLocal
            mock_image_pull_service: Mock ImagePullService
        """
        source_results = [
            {
                "source_id": str(uuid4()),
                "source_name": "Source 1",
                "processed_count": 10,
                "status": "success",
            },
            {
                "source_id": str(uuid4()),
                "source_name": "Source 2",
                "processed_count": 0,
                "status": "no_new_files",
            },
            {
                "source_id": str(uuid4()),
                "source_name": "Source 3",
                "processed_count": 7,
                "status": "success",
            },
        ]

        mock_image_pull_service.process_all_sources.return_value = source_results

        result = pull_all_sources_task(max_files_per_source=15)

        assert result["total_sources"] == 3
        assert result["total_images_processed"] == 17
        assert result["success"] is True
