#!/usr/bin/env python3
"""
Example script to create an image pull source for the Hameln-Pyrmont camera API.

This script demonstrates how to:
1. Create or find a location
2. Create an image pull source configuration
3. Test the pull source

Usage:
    python create_hameln_source.py --user-id YOUR_UUID --location-id LOCATION_UUID

Or to create a new location:
    python create_hameln_source.py --user-id YOUR_UUID --create-location
"""

import argparse
import sys
from uuid import UUID

from sqlalchemy.orm import Session

from src.api.database import SessionLocal
from src.api.image_pull_sources.image_pull_source_repository import (
    ImagePullSourceRepository,
)
from src.api.locations.location_repository import LocationRepository


def create_location(db: Session) -> UUID:
    """Create a location for Hameln-Pyrmont camera.

    Args:
        db: Database session

    Returns:
        UUID of the created location
    """
    location_repo = LocationRepository()

    location = location_repo.create(
        db=db,
        name="Hameln-Pyrmont Wildlife Camera",
        latitude=52.1035,
        longitude=9.3476,
        description="Automated wildlife camera from Hameln-Pyrmont region",
    )

    print(f"✓ Created location: {location.name} (ID: {location.id})")
    return UUID(location.id)


def create_pull_source(
    db: Session, user_id: UUID, location_id: UUID, test_mode: bool = False
) -> UUID:
    """Create the image pull source for Hameln-Pyrmont.

    Args:
        db: Database session
        user_id: UUID of the user to associate images with
        location_id: UUID of the location to associate images with
        test_mode: If True, set is_active to False for testing

    Returns:
        UUID of the created pull source
    """
    repo = ImagePullSourceRepository()

    source = repo.create(
        db=db,
        name="Hameln-Pyrmont Camera Feed",
        user_id=user_id,
        location_id=location_id,
        base_url="https://assets.hameln-pyrmont.digital/image-api/",
        auth_type="basic",
        auth_username="mitwirker",
        auth_password="gtdbGDfzCcUDQs2CK6FHYLq34",
        is_active=not test_mode,
    )

    status = "INACTIVE (test mode)" if test_mode else "ACTIVE"
    print(f"✓ Created pull source: {source.name} (ID: {source.id}) [{status}]")
    return UUID(source.id)


def test_pull_source(db: Session, source_id: UUID, max_files: int = 2) -> None:
    """Test the pull source by processing a few files.

    Args:
        db: Database session
        source_id: UUID of the pull source
        max_files: Maximum number of files to test with
    """
    from src.api.image_pull_sources.image_pull_service import ImagePullService

    service = ImagePullService.factory()

    print(
        "\n🔍 Testing pull source with max {max_files} files...".format(
            max_files=max_files
        )
    )

    result = service.pull_and_process_source(
        db=db, source_id=source_id, max_files=max_files
    )

    print("\n📊 Test Results:")
    print("  Status: {status}".format(status=result["status"]))
    print("  Files processed: {count}".format(count=result["processed_count"]))

    if result.get("processed_images"):
        print("\n  Processed images:")
        for img in result["processed_images"]:
            print(
                "    - {filename}: {count} detections (ID: {image_id})".format(
                    filename=img["filename"],
                    count=img["detections_count"],
                    image_id=img["image_id"],
                )
            )


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Create image pull source for Hameln-Pyrmont camera"
    )
    parser.add_argument(
        "--user-id", required=True, help="UUID of the user to associate images with"
    )
    parser.add_argument(
        "--location-id", help="UUID of the location (or use --create-location)"
    )
    parser.add_argument(
        "--create-location",
        action="store_true",
        help="Create a new location for Hameln-Pyrmont",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Create in test mode (inactive) and run a test pull",
    )
    parser.add_argument(
        "--test-files",
        type=int,
        default=2,
        help="Number of files to test with (default: 2)",
    )

    args = parser.parse_args()

    try:
        user_id = UUID(args.user_id)
    except ValueError:
        print(f"❌ Error: Invalid user ID format: {args.user_id}")
        sys.exit(1)

    db = SessionLocal()
    try:
        if args.create_location:
            location_id = create_location(db)
        elif args.location_id:
            try:
                location_id = UUID(args.location_id)
            except ValueError:
                print(f"❌ Error: Invalid location ID format: {args.location_id}")
                sys.exit(1)
        else:
            print("❌ Error: Must provide either --location-id or --create-location")
            sys.exit(1)

        source_id = create_pull_source(
            db=db, user_id=user_id, location_id=location_id, test_mode=args.test
        )

        if args.test:
            test_pull_source(db=db, source_id=source_id, max_files=args.test_files)

            print("\n⚠️  Note: Source is INACTIVE (test mode).")
            print("   To activate for hourly polling, use:")
            print(f"   PATCH /image-pull-sources/{source_id}/toggle?is_active=true")
        else:
            print(
                "\n✅ Pull source is ACTIVE and will be processed hourly by Celery Beat"
            )

        print("\n📝 Summary:")
        print(f"   User ID:     {user_id}")
        print(f"   Location ID: {location_id}")
        print(f"   Source ID:   {source_id}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
