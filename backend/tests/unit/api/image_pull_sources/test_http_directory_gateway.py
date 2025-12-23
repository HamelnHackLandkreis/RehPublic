"""Unit tests for HttpDirectoryGateway."""

from unittest.mock import Mock, patch

import pytest
import requests

from src.api.image_pull_sources.gateways.base import ImageFile
from src.api.image_pull_sources.gateways.http_directory import HttpDirectoryGateway


@pytest.fixture
def sample_html_directory() -> str:
    """Create sample HTML directory listing.

    Returns:
        HTML string of directory listing
    """
    return """
    <html>
    <body>
    <table>
        <tr><td><a href="../">Parent Directory</a></td></tr>
        <tr>
            <td><a href="image_001.jpg">image_001.jpg</a></td>
            <td align="right">2024-01-15 10:00:00</td>
            <td align="right">245678</td>
        </tr>
        <tr>
            <td><a href="image_002.jpg">image_002.jpg</a></td>
            <td align="right">2024-01-15 11:00:00</td>
            <td align="right">367890</td>
        </tr>
        <tr>
            <td><a href="image_003.png">image_003.png</a></td>
            <td align="right">2024-01-15 12:00:00</td>
            <td align="right">456789</td>
        </tr>
        <tr>
            <td><a href="readme.txt">readme.txt</a></td>
            <td align="right">2024-01-15 09:00:00</td>
            <td align="right">1234</td>
        </tr>
    </table>
    </body>
    </html>
    """


class TestHttpDirectoryGatewayInit:
    """Test cases for HttpDirectoryGateway initialization."""

    def test_init_with_basic_auth(self) -> None:
        """Test initialization with basic authentication."""
        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images",
            auth_type="basic",
            auth_username="user",
            auth_password="pass",
        )

        assert gateway.base_url == "https://example.com/images/"
        assert gateway.auth_type == "basic"
        assert gateway.auth_username == "user"
        assert gateway.auth_password == "pass"
        assert gateway._session.auth == ("user", "pass")

    def test_init_with_header_auth(self) -> None:
        """Test initialization with header authentication."""
        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/",
            auth_type="header",
            auth_header="Bearer token123",
        )

        assert gateway.base_url == "https://example.com/images/"
        assert gateway.auth_type == "header"
        assert gateway.auth_header == "Bearer token123"
        assert gateway._session.headers["Authorization"] == "Bearer token123"

    def test_init_without_auth(self) -> None:
        """Test initialization without authentication."""
        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        assert gateway.base_url == "https://example.com/images/"
        assert gateway.auth_type == "none"
        assert not hasattr(gateway._session, "auth") or gateway._session.auth is None

    def test_init_normalizes_base_url(self) -> None:
        """Test that base_url is normalized with trailing slash."""
        gateway1 = HttpDirectoryGateway(
            base_url="https://example.com/images", auth_type="none"
        )
        gateway2 = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        assert gateway1.base_url == "https://example.com/images/"
        assert gateway2.base_url == "https://example.com/images/"


class TestHttpDirectoryGatewayListFiles:
    """Test cases for list_files method."""

    @patch("requests.Session.get")
    def test_list_files_success(
        self, mock_get: Mock, sample_html_directory: str
    ) -> None:
        """Test listing files from directory successfully.

        Args:
            mock_get: Mock requests.Session.get
            sample_html_directory: Sample HTML content
        """
        mock_response = Mock()
        mock_response.text = sample_html_directory
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        files = gateway.list_files()

        assert len(files) == 3
        assert files[0].filename == "image_001.jpg"
        assert files[1].filename == "image_002.jpg"
        assert files[2].filename == "image_003.png"
        assert files[0].url == "https://example.com/images/image_001.jpg"
        assert files[0].last_modified == "245678"

        mock_get.assert_called_once_with("https://example.com/images/", timeout=30)

    @patch("requests.Session.get")
    def test_list_files_filters_non_images(self, mock_get: Mock) -> None:
        """Test that non-image files are filtered out.

        Args:
            mock_get: Mock requests.Session.get
        """
        html = """
        <html><body><table>
        <tr><td><a href="image.jpg">image.jpg</a></td></tr>
        <tr><td><a href="document.pdf">document.pdf</a></td></tr>
        <tr><td><a href="photo.png">photo.png</a></td></tr>
        <tr><td><a href="script.js">script.js</a></td></tr>
        </table></body></html>
        """

        mock_response = Mock()
        mock_response.text = html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        files = gateway.list_files()

        assert len(files) == 2
        assert all(file.filename in ["image.jpg", "photo.png"] for file in files)

    @patch("requests.Session.get")
    def test_list_files_http_error(self, mock_get: Mock) -> None:
        """Test handling of HTTP errors during listing.

        Args:
            mock_get: Mock requests.Session.get
        """
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        with pytest.raises(requests.HTTPError):
            gateway.list_files()

    @patch("requests.Session.get")
    def test_list_files_empty_directory(self, mock_get: Mock) -> None:
        """Test listing files from empty directory.

        Args:
            mock_get: Mock requests.Session.get
        """
        html = "<html><body><table></table></body></html>"

        mock_response = Mock()
        mock_response.text = html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        files = gateway.list_files()

        assert len(files) == 0

    @patch("requests.Session.get")
    def test_list_files_sorted_by_filename(self, mock_get: Mock) -> None:
        """Test that files are sorted by filename.

        Args:
            mock_get: Mock requests.Session.get
        """
        html = """
        <html><body><table>
        <tr><td><a href="zebra.jpg">zebra.jpg</a></td></tr>
        <tr><td><a href="alpha.jpg">alpha.jpg</a></td></tr>
        <tr><td><a href="beta.png">beta.png</a></td></tr>
        </table></body></html>
        """

        mock_response = Mock()
        mock_response.text = html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        files = gateway.list_files()

        assert len(files) == 3
        assert files[0].filename == "alpha.jpg"
        assert files[1].filename == "beta.png"
        assert files[2].filename == "zebra.jpg"


class TestHttpDirectoryGatewayDownloadFile:
    """Test cases for download_file method."""

    @patch("requests.Session.get")
    def test_download_file_success(self, mock_get: Mock) -> None:
        """Test downloading a file successfully.

        Args:
            mock_get: Mock requests.Session.get
        """
        file_content = b"fake_image_bytes"
        mock_response = Mock()
        mock_response.content = file_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        image_file = ImageFile(
            filename="test.jpg", url="https://example.com/images/test.jpg"
        )

        result = gateway.download_file(image_file)

        assert result == file_content
        mock_get.assert_called_once_with(
            "https://example.com/images/test.jpg", timeout=60
        )

    @patch("requests.Session.get")
    def test_download_file_http_error(self, mock_get: Mock) -> None:
        """Test handling of HTTP errors during download.

        Args:
            mock_get: Mock requests.Session.get
        """
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        image_file = ImageFile(
            filename="test.jpg", url="https://example.com/images/test.jpg"
        )

        with pytest.raises(requests.HTTPError):
            gateway.download_file(image_file)


class TestHttpDirectoryGatewayIsImageFile:
    """Test cases for _is_image_file static method."""

    def test_is_image_file_jpg(self) -> None:
        """Test JPG files are recognized."""
        assert HttpDirectoryGateway._is_image_file("photo.jpg")
        assert HttpDirectoryGateway._is_image_file("photo.JPG")
        assert HttpDirectoryGateway._is_image_file("photo.jpeg")
        assert HttpDirectoryGateway._is_image_file("photo.JPEG")

    def test_is_image_file_png(self) -> None:
        """Test PNG files are recognized."""
        assert HttpDirectoryGateway._is_image_file("image.png")
        assert HttpDirectoryGateway._is_image_file("image.PNG")

    def test_is_image_file_other_formats(self) -> None:
        """Test other image formats are recognized."""
        assert HttpDirectoryGateway._is_image_file("image.gif")
        assert HttpDirectoryGateway._is_image_file("image.webp")
        assert HttpDirectoryGateway._is_image_file("image.bmp")

    def test_is_image_file_non_images(self) -> None:
        """Test non-image files are rejected."""
        assert not HttpDirectoryGateway._is_image_file("document.pdf")
        assert not HttpDirectoryGateway._is_image_file("readme.txt")
        assert not HttpDirectoryGateway._is_image_file("script.js")
        assert not HttpDirectoryGateway._is_image_file("data.json")


class TestHttpDirectoryGatewayFromPullSource:
    """Test cases for from_pull_source factory method."""

    def test_from_pull_source_with_basic_auth(self) -> None:
        """Test creating gateway from pull source with basic auth."""
        pull_source = Mock()
        pull_source.base_url = "https://example.com/images/"
        pull_source.auth_type = "basic"
        pull_source.auth_username = "user"
        pull_source.auth_password = "pass"
        pull_source.auth_header = None

        gateway = HttpDirectoryGateway.from_pull_source(pull_source)

        assert gateway.base_url == "https://example.com/images/"
        assert gateway.auth_type == "basic"
        assert gateway.auth_username == "user"
        assert gateway.auth_password == "pass"

    def test_from_pull_source_with_header_auth(self) -> None:
        """Test creating gateway from pull source with header auth."""
        pull_source = Mock()
        pull_source.base_url = "https://example.com/images/"
        pull_source.auth_type = "header"
        pull_source.auth_username = None
        pull_source.auth_password = None
        pull_source.auth_header = "Bearer token123"

        gateway = HttpDirectoryGateway.from_pull_source(pull_source)

        assert gateway.base_url == "https://example.com/images/"
        assert gateway.auth_type == "header"
        assert gateway.auth_header == "Bearer token123"


class TestHttpDirectoryGatewayGetNewFiles:
    """Test cases for get_new_files method."""

    @patch("requests.Session.get")
    def test_get_new_files_no_last_pulled(
        self, mock_get: Mock, sample_html_directory: str
    ) -> None:
        """Test getting new files when nothing was pulled before.

        Args:
            mock_get: Mock requests.Session.get
            sample_html_directory: Sample HTML content
        """
        mock_response = Mock()
        mock_response.text = sample_html_directory
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        new_files = gateway.get_new_files(last_pulled_filename=None)

        assert len(new_files) == 3

    @patch("requests.Session.get")
    def test_get_new_files_with_last_pulled(
        self, mock_get: Mock, sample_html_directory: str
    ) -> None:
        """Test getting only files after last pulled.

        Args:
            mock_get: Mock requests.Session.get
            sample_html_directory: Sample HTML content
        """
        mock_response = Mock()
        mock_response.text = sample_html_directory
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        new_files = gateway.get_new_files(last_pulled_filename="image_001.jpg")

        assert len(new_files) == 2
        assert new_files[0].filename == "image_002.jpg"
        assert new_files[1].filename == "image_003.png"

    @patch("requests.Session.get")
    def test_get_new_files_last_pulled_not_found(
        self, mock_get: Mock, sample_html_directory: str
    ) -> None:
        """Test getting files when last pulled file doesn't exist anymore.

        Args:
            mock_get: Mock requests.Session.get
            sample_html_directory: Sample HTML content
        """
        mock_response = Mock()
        mock_response.text = sample_html_directory
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        gateway = HttpDirectoryGateway(
            base_url="https://example.com/images/", auth_type="none"
        )

        new_files = gateway.get_new_files(last_pulled_filename="nonexistent.jpg")

        assert len(new_files) == 3
