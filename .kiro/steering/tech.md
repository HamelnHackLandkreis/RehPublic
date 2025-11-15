---
inclusion: always
---

# Technology Stack

## Backend

### Core Framework & Language
- **Python 3.13+** (tested with 3.13)
- **FastAPI** - REST API framework with automatic OpenAPI/Swagger docs
- **Uvicorn** - ASGI server for FastAPI

### Database & ORM
- **SQLAlchemy 2.0+** - ORM with declarative base
- **PostgreSQL 15** - Production database
- **SQLite** - Development/testing database
- **psycopg2-binary** - PostgreSQL adapter

### Machine Learning
- **PyTorch 2.0+** - Deep learning framework
- **PyTorch Wildlife 1.0+** - Wildlife detection and classification
- **MegaDetectorV6** - Animal detection model
- **Regional Models**: AI4GAmazonRainforest, AI4GEurope, AI4GHamelin
- **Pillow** - Image processing
- **NumPy** - Numerical operations

### Validation & Serialization
- **Pydantic 2.0+** - Data validation and serialization
- **python-multipart** - File upload handling

### HTTP & External APIs
- **httpx** - Async HTTP client for Wikipedia API
- **python-dateutil** - Date/time parsing

### CLI & Utilities
- **Typer** - CLI framework with rich output
- **Rich** - Terminal formatting and progress bars

### Development Tools
- **uv** - Fast Python package manager (primary)
- **pytest** - Testing framework
- **mypy** - Static type checking (strict mode enabled)
- **ruff** - Fast Python linter and formatter
- **black** - Code formatter (line-length: 88)
- **isort** - Import sorting (black profile)
- **pre-commit** - Git hooks for code quality

## Frontend

### Core Framework
- **Nuxt.js 4.2+** - Vue.js meta-framework
- **Vue.js 3.5+** - Progressive JavaScript framework
- **TypeScript 5.9+** - Type-safe JavaScript

### UI & Styling
- **Tailwind CSS 4.1+** - Utility-first CSS framework
- **@nuxt/ui 4.1+** - Nuxt UI component library
- **@tailwindcss/vite** - Vite plugin for Tailwind

### Mapping & Visualization
- **Leaflet 1.9+** - Interactive maps
- **Chart.js 4.5+** - Data visualization charts

### Build & Development
- **Vite** - Fast build tool and dev server
- **Node.js 18+** - JavaScript runtime
- **npm** - Package manager

### Additional Features
- **@nuxt/image** - Image optimization
- **@vite-pwa/nuxt** - Progressive Web App support
- **ESLint 9+** - JavaScript/TypeScript linting

## Infrastructure

### Containerization
- **Docker** - Container runtime
- **Docker Compose** - Multi-container orchestration

### Load Balancing
- **NGINX** - Reverse proxy and load balancer (4 backend replicas)

### Deployment
- **Docker Bake** - Advanced Docker build configuration
- **Shell scripts** - Deployment automation (deploy.sh, smart_update.sh)

## Common Commands

### Backend Development

```bash
# Install dependencies
cd backend
uv sync

# Run development server
uv run uvicorn api.main:app --reload --port 8000

# Run tests
uv run pytest

# Type checking
uv run mypy .

# Linting and formatting
uv run ruff check .
uv run ruff format .

# Run pre-commit hooks
pre-commit run --all-files

# CLI tool
uv run wildlife-processor --help
```

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Run development server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Generate static site
npm run generate
```

### Docker Operations

```bash
# Build and start all services
docker-compose up --build

# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild specific service
docker-compose build backend
```

### Database

```bash
# Access PostgreSQL (when running in Docker)
docker exec -it rehpublic-db psql -U rehpublic -d rehpublic

# Database URL format
postgresql://user:password@host:port/database
sqlite:///./wildlife_camera.db
```

## API Documentation

When backend is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Port Configuration

- **Frontend**: 9001 (Docker), 3000 (dev)
- **Backend API**: 9002 (Docker/load balancer), 8000 (dev)
- **PostgreSQL**: 5432
- **Backend replicas**: Internal Docker network (4 instances)
