"""Directory scanning and image discovery for wildlife camera images."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from dateutil import parser as date_parser

from wildlife_processor.core.data_models import ImageMetadata
from wildlife_processor.utils.image_utils import (
    is_supported_format,
    validate_image_file,
)

logger = logging.getLogger(__name__)


class DirectoryScanner:
    """Scans directories for wildlife camera images and extracts metadata."""

    def __init__(self):
        """Initialize directory scanner."""
        self.failed_files: List[str] = []
        self.skipped_files: List[str] = []

    def scan_directory(self, root_path: Path) -> List[ImageMetadata]:
        """Scan directory recursively for wildlife camera images.

        Args:
            root_path: Root directory to scan

        Returns:
            List of ImageMetadata objects for discovered images
        """
        if not root_path.exists():
            raise ValueError(f"Directory does not exist: {root_path}")

        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")

        logger.info(f"Scanning directory: {root_path}")

        image_metadata_list = []
        self.failed_files = []
        self.skipped_files = []

        # Walk through all subdirectories
        for root, dirs, files in os.walk(root_path):
            root_path_obj = Path(root)

            for file in files:
                file_path = root_path_obj / file

                # Check if it's a supported image format
                if not is_supported_format(file_path):
                    continue

                # Validate the image file
                if not validate_image_file(file_path):
                    self.failed_files.append(str(file_path))
                    logger.warning(f"Invalid or corrupted image: {file_path}")
                    continue

                # Extract metadata from directory structure
                try:
                    metadata = self._extract_metadata_from_path(file_path, root_path)
                    if metadata:
                        image_metadata_list.append(metadata)
                    else:
                        self.skipped_files.append(str(file_path))

                except Exception as e:
                    logger.error(f"Failed to extract metadata from {file_path}: {e}")
                    self.failed_files.append(str(file_path))

        logger.info(
            f"Found {len(image_metadata_list)} valid images, "
            f"{len(self.failed_files)} failed, {len(self.skipped_files)} skipped"
        )

        return image_metadata_list

    def _extract_metadata_from_path(
        self, file_path: Path, root_path: Path
    ) -> Optional[ImageMetadata]:
        """Extract metadata from file path structure.

        Expected structure: /root/locationName/datetime/image.jpg
        But also handles flat structure: /root/image.jpg

        Args:
            file_path: Full path to image file
            root_path: Root directory being scanned

        Returns:
            ImageMetadata object or None if extraction failed
        """
        try:
            # Get relative path from root
            relative_path = file_path.relative_to(root_path)
            path_parts = relative_path.parts

            if len(path_parts) < 2:
                # Flat structure - extract from filename and EXIF
                logger.debug(f"Flat directory structure detected: {relative_path}")

                # Try to extract location and timestamp from filename
                filename = file_path.stem  # filename without extension
                location, timestamp = self._extract_from_filename(filename)

                if location is None:
                    # Use directory name as location
                    location = root_path.name

                if timestamp is None:
                    # Extract from EXIF or file mtime
                    timestamp = self._extract_timestamp_from_exif_or_mtime(file_path)

                return ImageMetadata(
                    file_path=file_path,
                    location=location,
                    timestamp=timestamp,
                    camera_reference=location,
                )

            # Standard nested structure
            # Extract location (first directory level)
            location = path_parts[0]
            camera_reference = location

            # Extract datetime (second directory level if exists, otherwise use file mtime)
            timestamp = self._extract_timestamp_from_path(file_path, path_parts)

            return ImageMetadata(
                file_path=file_path,
                location=location,
                timestamp=timestamp,
                camera_reference=camera_reference,
            )

        except Exception as e:
            logger.error(f"Metadata extraction failed for {file_path}: {e}")
            return None

    def _extract_timestamp_from_path(
        self, file_path: Path, path_parts: tuple
    ) -> datetime:
        """Extract timestamp from directory structure or file modification time.

        Args:
            file_path: Full path to image file
            path_parts: Tuple of path components

        Returns:
            Datetime object representing when image was captured
        """
        timestamp = None

        # Try to parse datetime from directory name (second level)
        if len(path_parts) >= 2:
            datetime_dir = path_parts[1]
            timestamp = self._parse_datetime_string(datetime_dir)

        # If no valid timestamp from directory, try third level
        if timestamp is None and len(path_parts) >= 3:
            datetime_dir = path_parts[2]
            timestamp = self._parse_datetime_string(datetime_dir)

        # Fallback to file modification time
        if timestamp is None:
            try:
                mtime = file_path.stat().st_mtime
                timestamp = datetime.fromtimestamp(mtime)
                logger.debug(f"Using file mtime for {file_path}: {timestamp}")
            except Exception as e:
                logger.warning(f"Could not get file mtime for {file_path}: {e}")
                # Ultimate fallback to current time
                timestamp = datetime.now()

        # Validate timestamp is reasonable for wildlife monitoring
        if not self._validate_timestamp(timestamp):
            logger.warning(
                f"Timestamp seems unreasonable: {timestamp}, using current time"
            )
            timestamp = datetime.now()

        return timestamp

    def _parse_datetime_string(self, datetime_str: str) -> Optional[datetime]:
        """Parse datetime string from directory name.

        Supports various formats like:
        - 2024-01-15_08-30
        - 2024-01-15T08:30:00
        - 20240115_0830
        - 2024_01_15_08_30

        Args:
            datetime_str: String to parse as datetime

        Returns:
            Datetime object or None if parsing failed
        """
        if not datetime_str:
            return None

        # Common datetime formats in wildlife camera directory names
        formats_to_try = [
            "%Y-%m-%d_%H-%M",
            "%Y-%m-%d_%H-%M-%S",
            "%Y%m%d_%H%M",
            "%Y%m%d_%H%M%S",
            "%Y_%m_%d_%H_%M",
            "%Y_%m_%d_%H_%M_%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

        # Try dateutil parser first (more flexible)
        try:
            # Replace common separators to make parsing easier
            cleaned_str = datetime_str.replace("_", " ").replace("-", " ")
            parsed_dt = date_parser.parse(cleaned_str, fuzzy=True)
            logger.debug(f"Parsed datetime '{datetime_str}' as {parsed_dt}")
            return parsed_dt
        except Exception:
            pass

        # Try specific formats
        for fmt in formats_to_try:
            try:
                parsed_dt = datetime.strptime(datetime_str, fmt)
                logger.debug(
                    f"Parsed datetime '{datetime_str}' with format '{fmt}' as {parsed_dt}"
                )
                return parsed_dt
            except ValueError:
                continue

        logger.debug(f"Could not parse datetime string: '{datetime_str}'")
        return None

    def _validate_timestamp(self, timestamp: datetime) -> bool:
        """Validate that timestamp is reasonable for wildlife monitoring.

        Args:
            timestamp: Datetime to validate

        Returns:
            True if timestamp seems reasonable, False otherwise
        """
        now = datetime.now()

        # Check if timestamp is not too far in the future (allow 1 day)
        if timestamp > now.replace(hour=23, minute=59, second=59):
            return False

        # Check if timestamp is not too far in the past (allow 10 years)
        min_date = now.replace(year=now.year - 10)
        if timestamp < min_date:
            return False

        return True

    def _extract_from_filename(
        self, filename: str
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """Extract location and timestamp from filename.

        Handles formats like: Aufnahme_250612_0001_BYWP9

        Args:
            filename: Filename without extension

        Returns:
            Tuple of (location, timestamp) or (None, None) if extraction failed
        """
        try:
            # Pattern for wildlife camera filenames like "Aufnahme_250612_0001_BYWP9"
            parts = filename.split("_")

            if len(parts) >= 4:
                # Extract camera reference (last part)
                camera_ref = parts[-1]  # BYWP9

                # Extract date (second part) - format like 250612 (YYMMDD)
                date_part = parts[1]  # 250612

                # Extract time (third part) - format like 0001 (HHMM)
                time_part = parts[2]  # 0001

                # Parse date - assuming 2-digit year starting from 2000
                if len(date_part) == 6 and len(time_part) == 4:
                    year = 2000 + int(date_part[:2])
                    month = int(date_part[2:4])
                    day = int(date_part[4:6])
                    hour = int(time_part[:2])
                    minute = int(time_part[2:4])

                    timestamp = datetime(year, month, day, hour, minute)

                    logger.debug(
                        f"Extracted from filename '{filename}': camera={camera_ref}, time={timestamp}"
                    )
                    return camera_ref, timestamp

        except (ValueError, IndexError) as e:
            logger.debug(f"Could not parse filename '{filename}': {e}")

        return None, None

    def _extract_timestamp_from_exif_or_mtime(self, file_path: Path) -> datetime:
        """Extract timestamp from EXIF data or file modification time.

        Args:
            file_path: Path to image file

        Returns:
            Datetime object
        """
        try:
            # Try to extract from EXIF data
            from PIL import Image
            from PIL.ExifTags import TAGS

            with Image.open(file_path) as img:
                exif_data = img._getexif()

                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == "DateTime":
                            # EXIF DateTime format: "YYYY:MM:DD HH:MM:SS"
                            try:
                                timestamp = datetime.strptime(
                                    value, "%Y:%m:%d %H:%M:%S"
                                )
                                logger.debug(
                                    f"Extracted timestamp from EXIF: {timestamp}"
                                )
                                return timestamp
                            except ValueError:
                                pass
        except Exception as e:
            logger.debug(f"Could not extract EXIF timestamp from {file_path}: {e}")

        # Fallback to file modification time
        try:
            mtime = file_path.stat().st_mtime
            timestamp = datetime.fromtimestamp(mtime)
            logger.debug(f"Using file mtime for {file_path}: {timestamp}")
            return timestamp
        except Exception as e:
            logger.warning(f"Could not get file mtime for {file_path}: {e}")
            # Ultimate fallback to current time
            return datetime.now()

    def get_scan_summary(self) -> dict:
        """Get summary of the last scan operation.

        Returns:
            Dictionary with scan statistics
        """
        return {
            "failed_files": len(self.failed_files),
            "skipped_files": len(self.skipped_files),
            "failed_file_list": self.failed_files.copy(),
            "skipped_file_list": self.skipped_files.copy(),
        }
