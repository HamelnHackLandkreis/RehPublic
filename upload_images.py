#!/usr/bin/env python3
"""Upload all images from a directory to the Wildlife Camera API.

Usage:
    python upload_images.py <DIRECTORY_PATH> [--api-base URL] [--location-id UUID]
"""

import argparse
import random
import sys
from pathlib import Path
from typing import List, Optional

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

    locations = response.json()
    if not locations:
        print("Error: No locations found. Please create at least one location first.")
        sys.exit(1)

    return locations


def upload_image(api_base: str, location_id: str, image_path: Path) -> Optional[dict]:
    """Upload an image to a location.

    Args:
        api_base: Base URL of the API
        location_id: UUID of the location
        image_path: Path to the image file

    Returns:
        Upload response dictionary if successful, None otherwise
    """
    url = f"{api_base}/locations/{location_id}/image"

    with open(image_path, "rb") as f:
        files = {"file": (image_path.name, f, "image/jpeg")}
        response = requests.post(url, files=files, timeout=300)

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
        List of image file paths
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    image_files = []

    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)

    return sorted(image_files)


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

    print("=== Uploading images ===")
    successful = 0
    failed = 0
    location_uploads = {
        loc["id"]: {"name": loc["name"], "count": 0} for loc in locations
    }

    for i, image_path in enumerate(image_files, 1):
        if use_random:
            selected_location = random.choice(locations)
            selected_location_id = selected_location["id"]
            selected_location_name = selected_location["name"]
        else:
            selected_location_id = location_id
            selected_location_name = location["name"]

        print(
            f"[{i}/{len(image_files)}] Uploading {image_path.name} "
            f"to {selected_location_name}...",
            end=" ",
        )

        result = upload_image(args.api_base, selected_location_id, image_path)

        if result:
            detections_count = result.get("detections_count", 0)
            detected_species = result.get("detected_species", [])
            print(
                f"✓ Success (detections: {detections_count}, "
                f"species: {', '.join(detected_species) if detected_species else 'none'})"
            )
            successful += 1
            location_uploads[selected_location_id]["count"] += 1
        else:
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
