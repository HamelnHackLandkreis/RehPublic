import os
import sys
import base64
import logging
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.database import DATABASE_URL, Base
from src.api.images.image_models import Image
from src.api.images.s3_service import S3Service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_images(clear_base64: bool = False):
    """
    Migrate images from base64 storage to S3.

    Args:
        clear_base64: If True, set base64_data to NULL after successful upload.
    """
    logger.info("Starting S3 migration...")

    # Initialize S3 Service
    try:
        s3_service = S3Service()
    except Exception as e:
        logger.error(f"Failed to initialize S3 Service: {e}")
        return

    # Database connection
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Find images that need migration (s3_key is NULL but base64_data exists)
        images = (
            db.query(Image)
            .filter(Image.s3_key == None, Image.base64_data != None)
            .all()
        )

        logger.info(f"Found {len(images)} images to migrate.")

        success_count = 0
        error_count = 0

        for image in images:
            try:
                logger.info(f"Migrating image {image.id}...")

                # Decode base64
                image_bytes = base64.b64decode(image.base64_data)

                # Generate Key
                timestamp_str = (image.upload_timestamp).strftime("%Y%m%d_%H%M%S")
                user_part = f"_{image.user_id}" if image.user_id else ""
                s3_key = f"location_{image.location_id}/{timestamp_str}{user_part}.jpg"

                # Upload
                if s3_service.upload_file(
                    image_bytes, s3_key, content_type="image/jpeg"
                ):
                    image.s3_key = s3_key
                    if clear_base64:
                        image.base64_data = None
                    success_count += 1
                else:
                    logger.error(f"Failed to upload image {image.id} to S3")
                    error_count += 1

            except Exception as e:
                logger.error(f"Error migrating image {image.id}: {e}")
                error_count += 1

        db.commit()
        logger.info(
            f"Migration completed. Success: {success_count}, Errors: {error_count}"
        )

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate images to S3")
    parser.add_argument(
        "--clear-base64", action="store_true", help="Clear base64 data after upload"
    )
    args = parser.parse_args()

    migrate_images(clear_base64=args.clear_base64)
