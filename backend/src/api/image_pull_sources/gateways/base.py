"""Abstract gateway interface for image pulling from external sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ImageFile:
    """Represents a file from an external image source.

    Attributes:
        filename: Name of the file
        url: Full URL to download the file
        last_modified: Optional last modified timestamp string
    """

    filename: str
    url: str
    last_modified: str | None = None


class ImagePullGateway(ABC):
    """Abstract base class for pulling images from external sources.

    This interface allows for pluggable implementations for different
    types of image sources (HTTP directory listings, S3, FTP, etc.).
    """

    @abstractmethod
    def list_files(self) -> list[ImageFile]:
        """List all available image files from the source.

        Returns:
            List of ImageFile objects representing available files

        Raises:
            Exception: If the listing operation fails
        """
        pass

    @abstractmethod
    def download_file(self, image_file: ImageFile) -> bytes:
        """Download a specific image file.

        Args:
            image_file: ImageFile object with file details

        Returns:
            Raw bytes of the image file

        Raises:
            Exception: If the download operation fails
        """
        pass

    def get_new_files(self, last_pulled_filename: str | None) -> list[ImageFile]:
        """Get files that are newer than the last pulled file.

        Args:
            last_pulled_filename: Name of the last file that was processed

        Returns:
            List of ImageFile objects that should be processed
        """
        all_files = self.list_files()

        if not last_pulled_filename:
            return all_files

        try:
            last_index = next(
                i for i, f in enumerate(all_files) if f.filename == last_pulled_filename
            )
            return all_files[last_index + 1 :]
        except StopIteration:
            return all_files
