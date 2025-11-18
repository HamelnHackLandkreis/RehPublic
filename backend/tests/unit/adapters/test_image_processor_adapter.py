"""Unit tests for image processor adapter."""

from datetime import datetime
from typing import Dict, List
from unittest.mock import Mock
from uuid import uuid4

import numpy as np
import pytest
from PIL import Image

from src.adapters.image_processor_adapter import ProcessorClient


@pytest.fixture
def mock_model_manager() -> Mock:
    """Create mock ModelManager.

    Returns:
        Mock ModelManager object
    """
    manager = Mock()
    manager.ensure_models_loaded = Mock()
    manager.process_image = Mock()
    return manager


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Create sample image bytes.

    Returns:
        PNG image bytes
    """
    # Create a simple 100x100 RGB image
    img = Image.new("RGB", (100, 100), color="red")
    import io

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


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
        }
    ]


class TestProcessorClientInit:
    """Test cases for ProcessorClient initialization."""

    def test_init_default_region(self) -> None:
        """Test initialization with default region.

        Returns:
            None
        """
        client = ProcessorClient()

        assert client.model_region == "general"
        assert client.model_manager is None

    def test_init_custom_region(self) -> None:
        """Test initialization with custom region.

        Returns:
            None
        """
        client = ProcessorClient(model_region="europe")

        assert client.model_region == "europe"
        assert client.model_manager is None


class TestProcessorClientEnsureModelLoaded:
    """Test cases for model loading."""

    def test_ensure_model_loaded_first_call(
        self, monkeypatch: pytest.MonkeyPatch, mock_model_manager: Mock
    ) -> None:
        """Test model loading on first call.

        Args:
            monkeypatch: Pytest monkeypatch fixture
            mock_model_manager: Mock ModelManager
        """
        # Mock ModelManager constructor
        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.ModelManager",
            Mock(return_value=mock_model_manager),
        )

        client = ProcessorClient(model_region="europe")
        client._ensure_model_loaded()

        # Verify ModelManager was created with correct region
        assert client.model_manager is mock_model_manager
        mock_model_manager.ensure_models_loaded.assert_called_once()

    def test_ensure_model_loaded_subsequent_calls(
        self, monkeypatch: pytest.MonkeyPatch, mock_model_manager: Mock
    ) -> None:
        """Test model loading is only done once.

        Args:
            monkeypatch: Pytest monkeypatch fixture
            mock_model_manager: Mock ModelManager
        """
        model_manager_constructor = Mock(return_value=mock_model_manager)
        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.ModelManager",
            model_manager_constructor,
        )

        client = ProcessorClient(model_region="europe")

        # Call multiple times
        client._ensure_model_loaded()
        client._ensure_model_loaded()
        client._ensure_model_loaded()

        # Verify ModelManager was only created once
        model_manager_constructor.assert_called_once_with(region="europe")
        mock_model_manager.ensure_models_loaded.assert_called_once()


class TestProcessorClientProcessImageData:
    """Test cases for synchronous image processing."""

    def test_process_image_data_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_model_manager: Mock,
        sample_image_bytes: bytes,
        sample_detections: List[Dict],
    ) -> None:
        """Test successful image processing.

        Args:
            monkeypatch: Pytest monkeypatch fixture
            mock_model_manager: Mock ModelManager
            sample_image_bytes: Sample image bytes
            sample_detections: Sample detection results
        """
        # Mock ModelManager
        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.ModelManager",
            Mock(return_value=mock_model_manager),
        )

        # Mock detection objects with to_dict method
        mock_detection_objs = []
        for detection in sample_detections:
            mock_det = Mock()
            mock_det.to_dict = Mock(return_value=detection)
            mock_detection_objs.append(mock_det)

        mock_model_manager.process_image.return_value = mock_detection_objs

        # Mock preprocess function
        mock_preprocess = Mock(return_value=np.zeros((100, 100, 3)))
        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.preprocess_image_for_pytorch_wildlife",
            mock_preprocess,
        )

        client = ProcessorClient(model_region="europe")
        result = client.process_image_data(image_bytes=sample_image_bytes)

        # Verify model was loaded
        mock_model_manager.ensure_models_loaded.assert_called_once()

        # Verify preprocessing was called
        assert mock_preprocess.called

        # Verify model processing was called
        assert mock_model_manager.process_image.called

        # Verify result
        assert result == sample_detections

    def test_process_image_data_with_timestamp(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_model_manager: Mock,
        sample_image_bytes: bytes,
        sample_detections: List[Dict],
    ) -> None:
        """Test image processing with timestamp parameter.

        Args:
            monkeypatch: Pytest monkeypatch fixture
            mock_model_manager: Mock ModelManager
            sample_image_bytes: Sample image bytes
            sample_detections: Sample detection results
        """
        # Mock ModelManager
        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.ModelManager",
            Mock(return_value=mock_model_manager),
        )

        # Mock detection objects
        mock_detection_objs = []
        for detection in sample_detections:
            mock_det = Mock()
            mock_det.to_dict = Mock(return_value=detection)
            mock_detection_objs.append(mock_det)

        mock_model_manager.process_image.return_value = mock_detection_objs

        # Mock preprocess function
        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.preprocess_image_for_pytorch_wildlife",
            Mock(return_value=np.zeros((100, 100, 3))),
        )

        client = ProcessorClient(model_region="europe")
        timestamp = datetime(2024, 1, 15, 10, 30, 0)

        result = client.process_image_data(
            image_bytes=sample_image_bytes, timestamp=timestamp
        )

        # Verify result (timestamp is currently not used in processing)
        assert result == sample_detections

    def test_process_image_data_converts_rgba_to_rgb(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_model_manager: Mock,
    ) -> None:
        """Test RGBA image is converted to RGB.

        Args:
            monkeypatch: Pytest monkeypatch fixture
            mock_model_manager: Mock ModelManager
        """
        # Create RGBA image
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        import io

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        rgba_bytes = buffer.getvalue()

        # Mock ModelManager
        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.ModelManager",
            Mock(return_value=mock_model_manager),
        )

        mock_model_manager.process_image.return_value = []

        # Mock preprocess function
        mock_preprocess = Mock(return_value=np.zeros((100, 100, 3)))
        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.preprocess_image_for_pytorch_wildlife",
            mock_preprocess,
        )

        client = ProcessorClient(model_region="europe")
        client.process_image_data(image_bytes=rgba_bytes)

        # Verify preprocessing was called (image was converted)
        assert mock_preprocess.called
        call_args = mock_preprocess.call_args
        processed_array = call_args[0][0]

        # Verify array has 3 channels (RGB)
        assert processed_array.shape[2] == 3

    def test_process_image_data_no_detections(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_model_manager: Mock,
        sample_image_bytes: bytes,
    ) -> None:
        """Test processing when no animals are detected.

        Args:
            monkeypatch: Pytest monkeypatch fixture
            mock_model_manager: Mock ModelManager
            sample_image_bytes: Sample image bytes
        """
        # Mock ModelManager
        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.ModelManager",
            Mock(return_value=mock_model_manager),
        )

        mock_model_manager.process_image.return_value = []

        # Mock preprocess function
        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.preprocess_image_for_pytorch_wildlife",
            Mock(return_value=np.zeros((100, 100, 3))),
        )

        client = ProcessorClient(model_region="europe")
        result = client.process_image_data(image_bytes=sample_image_bytes)

        # Verify empty result
        assert result == []


class TestProcessorClientProcessImageAsync:
    """Test cases for asynchronous image processing."""

    def test_process_image_async_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test async task dispatch.

        Args:
            monkeypatch: Pytest monkeypatch fixture
        """
        image_id = uuid4()
        image_base64 = "base64encodeddata"
        model_region = "europe"
        timestamp = datetime(2024, 1, 15, 10, 30, 0)

        # Mock Celery task
        mock_task = Mock()
        mock_task.id = "celery-task-id-123"
        mock_delay = Mock(return_value=mock_task)

        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.process_image_task.delay",
            mock_delay,
        )

        client = ProcessorClient(model_region="general")
        task_id = client.process_image_async(
            image_id=image_id,
            image_base64=image_base64,
            model_region=model_region,
            timestamp=timestamp,
        )

        # Verify task was dispatched with correct parameters
        mock_delay.assert_called_once_with(
            image_id=str(image_id),
            image_base64=image_base64,
            model_region=model_region,
            timestamp_str=timestamp.isoformat(),
        )

        # Verify task ID was returned
        assert task_id == "celery-task-id-123"

    def test_process_image_async_without_timestamp(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test async task dispatch without timestamp.

        Args:
            monkeypatch: Pytest monkeypatch fixture
        """
        image_id = uuid4()
        image_base64 = "base64encodeddata"

        # Mock Celery task
        mock_task = Mock()
        mock_task.id = "celery-task-id-456"
        mock_delay = Mock(return_value=mock_task)

        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.process_image_task.delay",
            mock_delay,
        )

        client = ProcessorClient()
        task_id = client.process_image_async(
            image_id=image_id,
            image_base64=image_base64,
            timestamp=None,
        )

        # Verify task was dispatched with None timestamp
        call_args = mock_delay.call_args
        assert call_args.kwargs["timestamp_str"] is None

        # Verify task ID was returned
        assert task_id == "celery-task-id-456"

    def test_process_image_async_default_region(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test async task dispatch uses provided region parameter.

        Args:
            monkeypatch: Pytest monkeypatch fixture
        """
        image_id = uuid4()
        image_base64 = "base64encodeddata"

        # Mock Celery task
        mock_task = Mock()
        mock_task.id = "celery-task-id-789"
        mock_delay = Mock(return_value=mock_task)

        monkeypatch.setattr(
            "src.adapters.image_processor_adapter.process_image_task.delay",
            mock_delay,
        )

        # Client initialized with one region
        client = ProcessorClient(model_region="amazon")

        # But async call uses different region
        client.process_image_async(
            image_id=image_id,
            image_base64=image_base64,
            model_region="hamelin",
        )

        # Verify task was dispatched with the provided region
        call_args = mock_delay.call_args
        assert call_args.kwargs["model_region"] == "hamelin"
