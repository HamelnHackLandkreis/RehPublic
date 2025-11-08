"""Service layer for business logic."""

import base64
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from api.models import Image, Location, Spotting
from api.processor_integration import ProcessorClient


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

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on Earth in kilometers.
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            
        Returns:
            Distance in kilometers
        """
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c

    @staticmethod
    def get_images_in_range(
        db: Session,
        latitude: float,
        longitude: float,
        distance_range: float,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None
    ) -> List[Image]:
        """Get all images within a distance range from a location and optional time range.
        
        Args:
            db: Database session
            latitude: Center latitude in decimal degrees
            longitude: Center longitude in decimal degrees
            distance_range: Maximum distance in kilometers (km) from center location
            time_start: Optional start timestamp in ISO 8601 format (inclusive)
            time_end: Optional end timestamp in ISO 8601 format (inclusive)
            
        Returns:
            List of Image objects within the specified range
        """
        # Get all locations
        all_locations = db.query(Location).all()
        
        # Filter locations within distance range
        locations_in_range = []
        for location in all_locations:
            distance = ImageService.haversine_distance(
                latitude, longitude,
                location.latitude, location.longitude
            )
            if distance <= distance_range:
                locations_in_range.append(location.id)
        
        if not locations_in_range:
            return []
        
        # Query images from locations in range
        query = db.query(Image).filter(Image.location_id.in_(locations_in_range))
        
        # Apply time range filters if provided
        if time_start is not None:
            query = query.filter(Image.upload_timestamp >= time_start)
        if time_end is not None:
            query = query.filter(Image.upload_timestamp <= time_end)
        
        return query.order_by(Image.upload_timestamp.desc()).all()


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
