"""Deprecated: Pydantic schemas have been moved to domain-specific modules.

This file is kept for backward compatibility and will be removed in a future version.
Please import schemas from their respective domain modules:

- api.images.images_schemas
- api.locations.locations_schemas
- api.statistics.statistics_schemas
- api.user_detections.user_detections_schemas
- api.wikipedia.wikipedia_schemas
"""

import warnings

# Re-export all schemas for backward compatibility
from api.images.images_schemas import (
    BoundingBoxResponse,
    DetectionResponse,
    ImageBase64Response,
    ImageDetailResponse,
    ImageUploadResponse,
    SpottingImageResponse,
)
from api.locations.locations_schemas import (
    AnimalSpottingResponse,
    AnimalSpottingsResponse,
    LocationCreate,
    LocationResponse,
    LocationsResponse,
    LocationWithImagesResponse,
    SpottingLocationResponse,
    SpottingsResponse,
)
from api.statistics.statistics_schemas import (
    SpeciesCountResponse,
    StatisticsResponse,
    TimePeriodStatisticsResponse,
)
from api.user_detections.user_detections_schemas import (
    UserDetectionCreate,
    UserDetectionResponse,
    UserDetectionStatsResponse,
)
from api.wikipedia.wikipedia_schemas import (
    WikipediaArticleResponse,
    WikipediaArticlesRequest,
)

# Emit deprecation warning when this module is imported
warnings.warn(
    "Importing from api.schemas is deprecated. "
    "Please import from domain-specific schema modules instead: "
    "api.images.images_schemas, api.locations.locations_schemas, "
    "api.statistics.statistics_schemas, api.user_detections.user_detections_schemas, "
    "api.wikipedia.wikipedia_schemas",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    # Image schemas
    "BoundingBoxResponse",
    "DetectionResponse",
    "ImageBase64Response",
    "ImageDetailResponse",
    "ImageUploadResponse",
    "SpottingImageResponse",
    # Location schemas
    "AnimalSpottingResponse",
    "AnimalSpottingsResponse",
    "LocationCreate",
    "LocationResponse",
    "LocationsResponse",
    "LocationWithImagesResponse",
    "SpottingLocationResponse",
    "SpottingsResponse",
    # Statistics schemas
    "SpeciesCountResponse",
    "StatisticsResponse",
    "TimePeriodStatisticsResponse",
    # User detection schemas
    "UserDetectionCreate",
    "UserDetectionResponse",
    "UserDetectionStatsResponse",
    # Wikipedia schemas
    "WikipediaArticleResponse",
    "WikipediaArticlesRequest",
]
