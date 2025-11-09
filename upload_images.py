#!/usr/bin/env python3
"""Upload all images from a directory to the Wildlife Camera API.

Usage:
    python upload_images.py <DIRECTORY_PATH> [--api-base URL] [--location-id UUID]
"""

import argparse
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import List, Optional, Tuple

import requests


def get_all_locations(api_base: str) -> List[dict]:
    """Get all locations from the API.

    Args:
        api_base: Base URL of the API

    Returns:
        List of location dictionaries

    Raises:
        SystemExit: If the API request fails
    """
    url = f"{api_base}/locations"
    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        print(f"Error: Failed to get locations (HTTP {response.status_code})")
        print(f"Response: {response.text}")
        sys.exit(1)

    locations_data = response.json()
    if "locations" in locations_data:
        locations = locations_data["locations"]
    else:
        locations = locations_data

    if not locations:
        print("Error: No locations found. Please create at least one location first.")
        sys.exit(1)

    return locations


def upload_image(
    api_base: str,
    location_id: str,
    image_path: Path,
    upload_timestamp: Optional[str] = None,
) -> Optional[dict]:
    """Upload an image to a location.

    Args:
        api_base: Base URL of the API
        location_id: UUID of the location
        image_path: Path to the image file
        upload_timestamp: Optional ISO 8601 timestamp string

    Returns:
        Upload response dictionary if successful, None otherwise
    """
    url = f"{api_base}/locations/{location_id}/image"

    params = {
        "upload_timestamp": upload_timestamp,
    }

    with open(image_path, "rb") as f:
        files = {"file": (image_path.name, f, "image/jpeg")}
        response = requests.post(url, files=files, params=params, timeout=300)

    if response.status_code != 201:
        print(
            f"  Error: Failed to upload {image_path.name} (HTTP {response.status_code})"
        )
        print(f"  Response: {response.text}")
        return None

    return response.json()


def get_image_files(directory: Path) -> List[Path]:
    """Get all image files from a directory.

    Args:
        directory: Directory path to search

    Returns:
        List of image file paths (randomly shuffled)
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    image_files = []

    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)

    # Randomly shuffle the order of images
    random.shuffle(image_files)
    return image_files


def main() -> None:
    """Main function to upload images from directory."""
    parser = argparse.ArgumentParser(
        description="Upload all images from a directory to the Wildlife Camera API"
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing image files to upload",
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--location-id",
        type=str,
        default=None,
        help="Specific location ID to upload to (default: uses first location)",
    )

    args = parser.parse_args()

    directory = args.directory
    if not directory.exists():
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)

    if not directory.is_dir():
        print(f"Error: Path is not a directory: {directory}")
        sys.exit(1)

    print(f"=== Getting locations from {args.api_base} ===")
    locations = get_all_locations(args.api_base)

    if args.location_id:
        location_id = args.location_id
        location = next((loc for loc in locations if loc["id"] == location_id), None)
        if not location:
            print(f"Error: Location ID {location_id} not found")
            sys.exit(1)
        print(f"Using specific location: {location['name']} (ID: {location_id})")
        use_random = False
    else:
        print(f"Found {len(locations)} location(s):")
        for loc in locations:
            print(f"  - {loc['name']} (ID: {loc['id']})")
        print("Images will be randomly distributed across these locations")
        use_random = True
    print()

    print(f"=== Scanning directory: {directory} ===")
    image_files = get_image_files(directory)

    if not image_files:
        print(f"No image files found in {directory}")
        sys.exit(0)

    print(f"Found {len(image_files)} image file(s)")
    print()

    # Generate random timestamps spread over the current year
    now = datetime.now()
    year_start = datetime(now.year, 1, 1)
    year_end = datetime(now.year, 12, 31, 23, 59, 59)
    # Use current time as end if we're not at the end of the year yet
    if now < year_end:
        year_end = now

    random_timestamps = []
    for _ in range(len(image_files)):
        random_time = year_start + timedelta(
            seconds=random.randint(0, int((year_end - year_start).total_seconds()))
        )
        random_timestamps.append(random_time.isoformat())

    print("=== Uploading images (10 concurrent requests) ===")
    successful = 0
    failed = 0
    location_uploads = {
        loc["id"]: {"name": loc["name"], "count": 0} for loc in locations
    }
    # Thread-safe counters
    success_lock = Lock()
    failed_lock = Lock()
    location_lock = Lock()
    completed_lock = Lock()

    def upload_single_image(
        image_path: Path, index: int, upload_timestamp: str
    ) -> Tuple[bool, Optional[dict], str, str, str]:
        """Upload a single image and return result.

        Returns:
            Tuple of (success, result_dict, location_name, location_id, image_name)
        """
        if use_random:
            selected_location = random.choice(locations)
            selected_location_id = selected_location["id"]
            selected_location_name = selected_location["name"]
        else:
            selected_location_id = location_id
            selected_location_name = location["name"]

        result = upload_image(
            args.api_base,
            selected_location_id,
            image_path,
            upload_timestamp=upload_timestamp,
        )

        return (
            result is not None,
            result,
            selected_location_name,
            selected_location_id,
            image_path.name,
        )

    # Use ThreadPoolExecutor with max 10 workers
    max_workers = 10
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all upload tasks to the thread pool
        future_to_image = {}
        for i, image_path in enumerate(image_files, 1):
            upload_timestamp = random_timestamps[i - 1]
            future = executor.submit(
                upload_single_image, image_path, i, upload_timestamp
            )
            future_to_image[future] = (i, image_path, upload_timestamp)

        # Process completed uploads as they finish
        completed = 0
        for future in as_completed(future_to_image):
            i, image_path, upload_timestamp = future_to_image[future]
            try:
                success, result, location_name, location_id, image_name = (
                    future.result()
                )

                with completed_lock:
                    completed += 1

                print(
                    f"[{completed}/{len(image_files)}] {image_name} → {location_name}",
                )
                print(f"  Timestamp: {upload_timestamp}", end=" ... ")

                if success:
                    detections_count = result.get("detections_count", 0)
                    detected_species = result.get("detected_species", [])
                    print(
                        f"✓ Success (detections: {detections_count}, "
                        f"species: {', '.join(detected_species) if detected_species else 'none'})"
                    )
                    with success_lock:
                        successful += 1
                    with location_lock:
                        location_uploads[location_id]["count"] += 1
                else:
                    print("✗ Failed")
                    with failed_lock:
                        failed += 1
            except Exception as e:
                with completed_lock:
                    completed += 1
                print(
                    f"[{completed}/{len(image_files)}] {image_path.name}",
                )
                print(f"  Timestamp: {upload_timestamp}", end=" ... ")
                print(f"✗ Error: {e}")
                with failed_lock:
                    failed += 1

    print()
    print("=== Upload Summary ===")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total: {len(image_files)}")
    if use_random:
        print()
        print("=== Distribution by Location ===")
        for loc_id, stats in location_uploads.items():
            if stats["count"] > 0:
                print(f"{stats['name']}: {stats['count']} image(s)")


if __name__ == "__main__":
    main()
