"""Location enrichment for wildlife camera detection results."""

import logging
from typing import Dict, List, Optional, Tuple

from wildlife_processor.core.data_models import DetectionResult

logger = logging.getLogger(__name__)


class LocationEnricher:
    """Enriches detection results with camera location metadata and geographic information."""
    
    def __init__(self):
        """Initialize location enricher."""
        # Camera location database (in a real implementation, this could be loaded from a file)
        self.camera_locations: Dict[str, Dict[str, any]] = {}
        self.geographic_contexts: Dict[str, Dict[str, str]] = {}
    
    def enrich_results(self, results: List[DetectionResult]) -> List[DetectionResult]:
        """Enrich detection results with location metadata.
        
        Args:
            results: List of detection results to enrich
            
        Returns:
            List of enriched detection results
        """
        logger.info(f"Enriching {len(results)} detection results with location metadata")
        
        enriched_results = []
        
        for result in results:
            try:
                enriched_result = self.enrich_detection_result(result)
                enriched_results.append(enriched_result)
            except Exception as e:
                logger.error(f"Failed to enrich result for {result.image_path}: {e}")
                # Add original result if enrichment fails
                enriched_results.append(result)
        
        logger.info(f"Successfully enriched {len(enriched_results)} results")
        return enriched_results
    
    def enrich_detection_result(self, result: DetectionResult) -> DetectionResult:
        """Enrich a single detection result with location metadata.
        
        Args:
            result: Detection result to enrich
            
        Returns:
            Enriched detection result (currently returns original as enrichment is optional)
        """
        # For now, we'll return the original result
        # In a full implementation, this would add GPS coordinates, 
        # geographic context, and other location-based metadata
        
        camera_ref = result.camera_reference
        
        # Look up GPS coordinates if available
        coordinates = self.lookup_camera_coordinates(camera_ref)
        if coordinates:
            logger.debug(f"Found coordinates for camera {camera_ref}: {coordinates}")
        
        # Add geographic context
        geo_context = self.add_geographic_context(camera_ref)
        if geo_context:
            logger.debug(f"Added geographic context for {camera_ref}: {geo_context}")
        
        # For this implementation, we return the original result
        # In a full version, we would create an EnrichedDetectionResult class
        # that extends DetectionResult with additional location fields
        
        return result
    
    def lookup_camera_coordinates(self, camera_reference: str) -> Optional[Tuple[float, float]]:
        """Look up GPS coordinates for a camera reference.
        
        Args:
            camera_reference: Camera identifier
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        if camera_reference in self.camera_locations:
            location_data = self.camera_locations[camera_reference]
            lat = location_data.get('latitude')
            lon = location_data.get('longitude')
            
            if lat is not None and lon is not None:
                return (float(lat), float(lon))
        
        # In a real implementation, this could query a database or API
        logger.debug(f"No GPS coordinates found for camera: {camera_reference}")
        return None
    
    def add_geographic_context(self, location: str) -> Optional[Dict[str, str]]:
        """Add geographic context information for a location.
        
        Args:
            location: Location identifier
            
        Returns:
            Dictionary with geographic context or None if not available
        """
        if location in self.geographic_contexts:
            return self.geographic_contexts[location].copy()
        
        # Generate basic geographic context based on location name
        context = self._generate_basic_context(location)
        
        if context:
            # Cache the context for future use
            self.geographic_contexts[location] = context
            return context
        
        return None
    
    def _generate_basic_context(self, location: str) -> Optional[Dict[str, str]]:
        """Generate basic geographic context from location name.
        
        Args:
            location: Location name
            
        Returns:
            Dictionary with basic context information
        """
        location_lower = location.lower()
        
        # Basic habitat type inference from location name
        habitat_keywords = {
            'forest': 'Forest',
            'woods': 'Forest',
            'tree': 'Forest',
            'meadow': 'Grassland',
            'field': 'Grassland',
            'prairie': 'Grassland',
            'river': 'Wetland',
            'stream': 'Wetland',
            'pond': 'Wetland',
            'lake': 'Wetland',
            'mountain': 'Mountain',
            'hill': 'Mountain',
            'desert': 'Desert',
            'trail': 'Mixed'
        }
        
        habitat_type = 'Unknown'
        for keyword, habitat in habitat_keywords.items():
            if keyword in location_lower:
                habitat_type = habitat
                break
        
        context = {
            'habitat_type': habitat_type,
            'location_name': location,
            'context_source': 'inferred_from_name'
        }
        
        logger.debug(f"Generated context for {location}: {context}")
        return context
    
    def add_camera_location(self, camera_reference: str, latitude: float, 
                           longitude: float, **additional_metadata) -> None:
        """Add GPS coordinates and metadata for a camera.
        
        Args:
            camera_reference: Camera identifier
            latitude: GPS latitude
            longitude: GPS longitude
            **additional_metadata: Additional metadata fields
        """
        self.camera_locations[camera_reference] = {
            'latitude': latitude,
            'longitude': longitude,
            **additional_metadata
        }
        
        logger.info(f"Added location data for camera {camera_reference}: "
                   f"({latitude}, {longitude})")
    
    def load_camera_locations_from_file(self, file_path: str) -> None:
        """Load camera locations from a configuration file.
        
        Args:
            file_path: Path to camera locations file (JSON, CSV, etc.)
        """
        # This would be implemented to load from various file formats
        # For now, it's a placeholder
        logger.info(f"Loading camera locations from {file_path} (not implemented)")
        pass
    
    def get_enrichment_summary(self) -> Dict[str, int]:
        """Get summary of available enrichment data.
        
        Returns:
            Dictionary with enrichment statistics
        """
        return {
            'cameras_with_coordinates': len(self.camera_locations),
            'locations_with_context': len(self.geographic_contexts)
        }