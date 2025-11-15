---
inclusion: always
---

# Project Structure

## Root Directory

```
.
├── backend/              # FastAPI backend application
├── frontend/             # Nuxt.js frontend application
├── nginx/                # NGINX load balancer configuration
├── processed_images/     # ML processing output directories
├── scripts/              # Utility scripts
├── files/                # Static data files
├── docker-compose.yml    # Multi-container orchestration
├── docker-bake.hcl       # Advanced Docker build config
└── *.sh                  # Deployment and update scripts
```

## Backend Structure

```
backend/
├── api/                           # FastAPI application
│   ├── main.py                    # Application entry point, router registration
│   ├── database.py                # SQLAlchemy engine, session management
│   ├── models.py                  # Base declarative model
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── services.py                # Business logic layer
│   ├── processor_integration.py   # ML model integration client
│   │
│   ├── images/                    # Image management module
│   │   ├── image_models.py        # Image SQLAlchemy model
│   │   └── images_controller.py   # Image endpoints
│   │
│   ├── locations/                 # Location management module
│   │   ├── location_models.py     # Location SQLAlchemy model
│   │   └── locations_controller.py # Location endpoints
│   │
│   ├── spottings/                 # Animal detection module
│   │   ├── spotting_models.py     # Spotting SQLAlchemy model
│   │   └── spottings_controller.py # Spotting endpoints
│   │
│   ├── user_detections/           # User identification module
│   │   ├── user_detection_models.py
│   │   └── user_detections_controller.py
│   │
│   ├── statistics/                # Analytics module
│   │   └── statistics_controller.py
│   │
│   ├── wikipedia/                 # Wikipedia integration module
│   │   └── wikipedia_controller.py
│   │
│   └── root/                      # Root endpoints
│       └── root_controller.py
│
├── wildlife_processor/            # ML processing package
│   ├── cli/                       # CLI interface (Typer)
│   │   └── main.py
│   ├── core/                      # Core processing components
│   │   ├── data_models.py         # Data structures
│   │   ├── models.py              # PyTorch Wildlife integration
│   │   ├── processor.py           # Main processing engine
│   │   └── directory_scanner.py   # Directory scanning
│   ├── postprocessing/            # Result enrichment
│   │   └── location_enricher.py
│   ├── utils/                     # Utilities
│   │   ├── image_utils.py         # Image processing
│   │   ├── json_output.py         # JSON formatting
│   │   └── error_handler.py       # Error handling
│   └── config/                    # Configuration
│       └── models_config.py       # Regional model configs
│
├── tests/                         # Test suite
│   ├── conftest.py                # Pytest fixtures
│   ├── integration/               # Integration tests
│   └── test_*.py                  # Unit tests
│
├── bilder/                        # Sample images for testing
├── pyproject.toml                 # Python project configuration
├── uv.lock                        # UV lock file
├── Dockerfile                     # Backend container definition
└── wildlife_camera.db             # SQLite database (dev)
```

## Frontend Structure

```
frontend/
├── app/                           # Nuxt application
│   ├── app.vue                    # Root component
│   ├── assets/                    # Static assets (CSS, images)
│   │   └── css/
│   │       └── main.css           # Global styles
│   ├── components/                # Vue components
│   │   ├── Map/                   # Map-related components
│   │   ├── Statistics/            # Statistics components
│   │   └── *.vue                  # Reusable components
│   ├── composables/               # Vue composables (shared logic)
│   │   └── useApi.ts              # API client composable
│   └── pages/                     # Route pages
│       ├── index.vue              # Home page
│       ├── map.vue                # Map view
│       └── statistics.vue         # Statistics view
│
├── public/                        # Static files (served as-is)
│   ├── favicon.*                  # Favicon files
│   ├── icon-*.png                 # PWA icons
│   └── RehPublic_Icon.*           # Logo files
│
├── nginx/                         # NGINX configuration for production
│   └── default.conf
│
├── nuxt.config.ts                 # Nuxt configuration
├── tsconfig.json                  # TypeScript configuration
├── package.json                   # Node dependencies
├── Dockerfile                     # Frontend container definition
└── *.py                           # Icon generation scripts
```

## Architecture Patterns

### Backend Module Organization

Each feature module follows this structure:
```
module_name/
├── module_name_models.py          # SQLAlchemy ORM models
├── module_name_controller.py      # FastAPI router with endpoints
└── module_name_schemas.py         # Pydantic schemas (if module-specific)
```

### Service Layer Pattern

- **Controllers** (`*_controller.py`): Handle HTTP requests/responses, validation
- **Services** (`services.py`): Business logic, database operations
- **Models** (`*_models.py`): SQLAlchemy ORM definitions
- **Schemas** (`schemas.py`): Pydantic models for API contracts

### Database Models

All models inherit from `Base` (declarative_base) defined in `api/models.py`:
- `Location`: Camera trap locations with coordinates
- `Image`: Uploaded images with base64 data
- `Spotting`: Animal detections with bounding boxes
- `UserDetection`: Manual user identifications

### API Endpoint Organization

Endpoints are grouped by resource:
- `/locations` - Camera location management
- `/images` - Image upload and retrieval
- `/spottings` - Geographic and temporal queries
- `/statistics` - Aggregated analytics
- `/user-detections` - User contribution tracking
- `/wikipedia` - Species information lookup

### Frontend Composables

Reusable logic extracted into composables:
- `useApi`: Centralized API client with base URL configuration
- Map state management
- Statistics data fetching

### Configuration Management

- **Backend**: Environment variables via `os.getenv()`, defaults in code
- **Frontend**: `runtimeConfig` in `nuxt.config.ts` with `NUXT_PUBLIC_API_URL`
- **Docker**: Build args and environment variables in `docker-compose.yml`

## Key Files

- `backend/api/main.py` - FastAPI app initialization, middleware, router registration
- `backend/api/database.py` - Database connection and session factory
- `backend/api/services.py` - All service classes (LocationService, ImageService, etc.)
- `backend/api/schemas.py` - All Pydantic schemas for API
- `frontend/nuxt.config.ts` - Nuxt configuration, modules, runtime config
- `docker-compose.yml` - Service orchestration with 4 backend replicas
- `nginx/nginx.conf` - Load balancer configuration

## Testing Structure

- `backend/tests/conftest.py` - Shared pytest fixtures (database, sessions, mocks)
- `backend/tests/test_*.py` - Unit tests following naming convention
- `backend/tests/integration/` - Integration tests for API endpoints
- Test fixtures follow the pattern: `some_dependency()` returns Mock objects
- Repository/service fixtures: `some_service(dependency1, dependency2)` returns instance
