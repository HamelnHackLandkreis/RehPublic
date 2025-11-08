"""Service layer for business logic."""

import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.models import Image, Location, Spotting
from api.processor_integration import ProcessorClient

logger = logging.getLogger(__name__)


class LocationService:
    """Service for location-related operations."""

    @staticmethod
    def get_all_locations(db: Session) -> List[Location]:
        """Retrieve all locations.

        Args:
            db: Database session

        Returns:
            List of all locations
        """
        return db.query(Location).all()

    @staticmethod
    def get_location_by_id(db: Session, location_id: UUID) -> Optional[Location]:
        """Get specific location by ID.

        Args:
            db: Database session
            location_id: UUID of the location

        Returns:
            Location object or None if not found
        """
        return db.query(Location).filter(Location.id == str(location_id)).first()

    @staticmethod
    def create_location(
        db: Session,
        name: str,
        longitude: float,
        latitude: float,
        description: Optional[str] = None
    ) -> Location:
        """Create new location.

        Args:
            db: Database session
            name: Location name
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            description: Optional description

        Returns:
            Created Location object
        """
        location = Location(
            name=name,
            longitude=longitude,
            latitude=latitude,
            description=description
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        return location


class ImageService:
    """Service for image-related operations."""

    def __init__(self, processor_client: Optional[ProcessorClient] = None):
        """Initialize image service.

        Args:
            processor_client: Optional processor client (will create default if not provided)
        """
        self.processor_client = processor_client or ProcessorClient(model_region="general")

    def save_image(
        self,
        db: Session,
        location_id: UUID,
        file_bytes: bytes
    ) -> Image:
        """Save uploaded image as base64.

        Args:
            db: Database session
            location_id: UUID of the location
            file_bytes: Raw image bytes

        Returns:
            Created Image object
        """
        # Encode to base64
        base64_data = base64.b64encode(file_bytes).decode('utf-8')

        # Create image record
        image = Image(
            location_id=str(location_id),
            base64_data=base64_data,
            processed=False
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    def get_image_by_id(self, db: Session, image_id: UUID) -> Optional[Image]:
        """Retrieve image with detections.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            Image object or None if not found
        """
        return db.query(Image).filter(Image.id == str(image_id)).first()

    def process_image(
        self,
        db: Session,
        image: Image,
        location_name: str
    ) -> List[Dict]:
        """Trigger wildlife processor on image.

        Args:
            db: Database session
            image: Image object to process
            location_name: Name of the location

        Returns:
            List of detection dictionaries
        """
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image.base64_data)

        # Process image
        detections = self.processor_client.process_image_data(
            image_bytes=image_bytes,
            location_name=location_name,
            timestamp=image.upload_timestamp
        )

        return detections


class SpottingService:
    """Service for spotting-related operations."""

    @staticmethod
    def save_detections(
        db: Session,
        image_id: UUID,
        detections: List[Dict]
    ) -> List[Spotting]:
        """Store detection results.

        Args:
            db: Database session
            image_id: UUID of the image
            detections: List of detection dictionaries

        Returns:
            List of created Spotting objects
        """
        spottings = []
        for detection in detections:
            bbox = detection['bounding_box']
            spotting = Spotting(
                image_id=str(image_id),
                species=detection['species'],
                confidence=detection['confidence'],
                bbox_x=bbox['x'],
                bbox_y=bbox['y'],
                bbox_width=bbox['width'],
                bbox_height=bbox['height'],
                classification_model=detection['classification_model'],
                is_uncertain=detection['is_uncertain']
            )
            db.add(spotting)
            spottings.append(spotting)

        db.commit()
        return spottings

    @staticmethod
    def get_aggregated_spottings(db: Session) -> List[Dict]:
        """Get spotting summary grouped by location.

        Returns aggregated data with:
        - Location coordinates
        - Unique list of species detected at that location
        - Most recent spotting timestamp
        - Most recent image timestamp
        - Most recent image_id

        Args:
            db: Database session

        Returns:
            List of aggregated spotting dictionaries
        """
        # Query to get aggregated data per location
        results = (
            db.query(
                Location.id,
                Location.longitude,
                Location.latitude,
                func.max(Spotting.detection_timestamp).label('ts_last_spotting'),
                func.max(Image.upload_timestamp).label('ts_last_image')
            )
            .join(Image, Location.id == Image.location_id)
            .join(Spotting, Image.id == Spotting.image_id)
            .group_by(Location.id, Location.longitude, Location.latitude)
            .all()
        )

        aggregated_spottings = []
        for result in results:
            location_id = result.id

            # Get unique species for this location
            species_list = (
                db.query(Spotting.species)
                .join(Image, Spotting.image_id == Image.id)
                .filter(Image.location_id == location_id)
                .distinct()
                .all()
            )
            animals = [species[0] for species in species_list]

            # Get most recent image_id for this location
            most_recent_image = (
                db.query(Image.id)
                .filter(Image.location_id == location_id)
                .order_by(Image.upload_timestamp.desc())
                .first()
            )

            spotting_data = {
                'pos': {
                    'longitude': result.longitude,
                    'latitude': result.latitude
                },
                'animals': animals,
                'ts_last_spotting': result.ts_last_spotting,
                'ts_last_image': result.ts_last_image,
                'image_id': most_recent_image[0] if most_recent_image else None
            }
            aggregated_spottings.append(spotting_data)

        return aggregated_spottings


class WikipediaService:
    """Service for fetching Wikipedia article data."""

    WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    WIKIPEDIA_BASE_URL = "https://en.wikipedia.org/wiki/"

    async def fetch_article(self, title: str) -> Optional[Dict]:
        """Fetch a single Wikipedia article summary.

        Args:
            title: Article title

        Returns:
            Dictionary with article data or None if not found
        """
        try:
            # Wikipedia requires a User-Agent header to prevent abuse
            headers = {
                "User-Agent": "WildlifeCameraAPI/0.1 (Educational project; contact: your-email@example.com)"
            }
            
            async with httpx.AsyncClient(headers=headers) as client:
                # Encode title for URL
                encoded_title = title.replace(" ", "_")
                url = f"{self.WIKIPEDIA_API_URL}{encoded_title}"
                
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 404:
                    logger.warning(f"Wikipedia article not found: {title}")
                    return None
                
                response.raise_for_status()
                data = response.json()
                
                # Extract relevant fields - use extract for longer text content
                article_data = {
                    "title": data.get("title", title),
                    "description": data.get("extract"),  # This contains the full paragraph(s)
                    "image_url": data.get("thumbnail", {}).get("source") if "thumbnail" in data else None,
                    "article_url": data.get("content_urls", {}).get("desktop", {}).get("page", f"{self.WIKIPEDIA_BASE_URL}{encoded_title}")
                }
                
                return article_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Wikipedia article '{title}': {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching Wikipedia article '{title}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching Wikipedia article '{title}': {e}")
            return None

    async def fetch_articles(self, titles: List[str]) -> List[Dict]:
        """Fetch multiple Wikipedia articles.

        Args:
            titles: List of article titles

        Returns:
            List of article data dictionaries (excluding failed fetches)
        """
        results = []
        
        for title in titles:
            article_data = await self.fetch_article(title)
            if article_data:
                results.append(article_data)
        
        return results
