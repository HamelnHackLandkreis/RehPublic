---
inclusion: always
---

# RehPublic - Wildlife Monitoring Platform

RehPublic is a full-stack wildlife monitoring platform for camera trap management and analysis. The system automatically detects and classifies animals in uploaded images using PyTorch-based ML models, visualizes spottings on an interactive map, and provides statistical insights.

## Core Features

- **Automated Wildlife Detection**: Uses MegaDetectorV6 for animal detection and regional classification models (Amazon, Europe, Hamelin)
- **Interactive Mapping**: Leaflet-based visualization of camera locations and animal spottings
- **User Contributions**: Allows manual species identification and comparison with automated detections
- **Statistics & Analytics**: Time-based aggregation of spottings with configurable granularity
- **Wikipedia Integration**: Fetches species information and images from Wikipedia API

## Key Workflows

1. **Image Upload**: Upload images to camera locations → automatic detection → store results with bounding boxes
2. **Spotting Search**: Query images by geographic range, time period, and species filter
3. **User Detection**: Manual species identification by users, tracked separately from automated detections
4. **Statistics**: Aggregate spottings by time periods (hourly/daily/weekly) with species counts

## Architecture

- **Frontend**: Nuxt.js SPA with Tailwind CSS and Leaflet maps
- **Backend**: FastAPI REST API with SQLAlchemy ORM
- **Database**: PostgreSQL (SQLite for development)
- **ML Processing**: PyTorch Wildlife with regional classification models
- **Deployment**: Docker Compose with NGINX load balancer for multiple backend instances
