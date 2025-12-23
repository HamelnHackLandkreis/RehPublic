"""HTTP directory listing gateway for pulling images from web directories."""

import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.api.image_pull_sources.gateways.base import ImageFile, ImagePullGateway

logger = logging.getLogger(__name__)


class HttpDirectoryGateway(ImagePullGateway):
    """Gateway for pulling images from HTTP directory listings.

    This gateway parses HTML directory listings (like nginx autoindex)
    and downloads image files using HTTP requests with authentication.
    """

    def __init__(
        self,
        base_url: str,
        auth_type: str = "basic",
        auth_username: str | None = None,
        auth_password: str | None = None,
        auth_header: str | None = None,
    ) -> None:
        """Initialize HTTP directory gateway.

        Args:
            base_url: Base URL of the directory (e.g., https://example.com/images/)
            auth_type: Type of authentication (basic, header, none)
            auth_username: Username for basic authentication
            auth_password: Password for basic authentication
            auth_header: Pre-encoded authorization header value
        """
        self.base_url = base_url.rstrip("/") + "/"
        self.auth_type = auth_type
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.auth_header = auth_header
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with authentication configured.

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        if self.auth_type == "basic" and self.auth_username and self.auth_password:
            session.auth = (self.auth_username, self.auth_password)
        elif self.auth_type == "header" and self.auth_header:
            session.headers["Authorization"] = self.auth_header

        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            }
        )

        return session

    def list_files(self) -> list[ImageFile]:
        """List all image files from the HTTP directory.

        Returns:
            List of ImageFile objects

        Raises:
            requests.RequestException: If the HTTP request fails
        """
        logger.info(f"Listing files from {self.base_url}")

        response = self._session.get(self.base_url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        image_files = []
        for row in soup.find_all("tr"):
            link = row.find("a")
            if not link:
                continue

            href = link.get("href")
            if not href or href == "../":
                continue

            filename = link.text.strip()
            if not self._is_image_file(filename):
                continue

            full_url = urljoin(self.base_url, href)

            last_modified = None
            cells = row.find_all("td")
            if len(cells) >= 3:
                last_modified = cells[2].text.strip()

            image_files.append(
                ImageFile(filename=filename, url=full_url, last_modified=last_modified)
            )

        logger.info(f"Found {len(image_files)} image files")
        return sorted(image_files, key=lambda f: f.filename)

    def download_file(self, image_file: ImageFile) -> bytes:
        """Download a specific image file.

        Args:
            image_file: ImageFile object with download details

        Returns:
            Raw bytes of the image file

        Raises:
            requests.RequestException: If the download fails
        """
        logger.info(f"Downloading {image_file.filename} from {image_file.url}")

        response = self._session.get(image_file.url, timeout=60)
        response.raise_for_status()

        logger.info(
            f"Successfully downloaded {image_file.filename} ({len(response.content)} bytes)"
        )
        return response.content

    @staticmethod
    def _is_image_file(filename: str) -> bool:
        """Check if a filename represents an image file.

        Args:
            filename: Name of the file

        Returns:
            True if the file is an image, False otherwise
        """
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
        return any(filename.lower().endswith(ext) for ext in image_extensions)

    @classmethod
    def from_pull_source(cls, pull_source: object) -> "HttpDirectoryGateway":
        """Factory method to create gateway from ImagePullSource model.

        Args:
            pull_source: ImagePullSource model instance

        Returns:
            Configured HttpDirectoryGateway instance
        """
        return cls(
            base_url=pull_source.base_url,  # type: ignore[attr-defined]
            auth_type=pull_source.auth_type,  # type: ignore[attr-defined]
            auth_username=pull_source.auth_username,  # type: ignore[attr-defined]
            auth_password=pull_source.auth_password,  # type: ignore[attr-defined]
            auth_header=pull_source.auth_header,  # type: ignore[attr-defined]
        )
