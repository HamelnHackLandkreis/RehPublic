# RehPublic - Wildlife Monitoring Platform

RehPublic is a full-stack web application designed for monitoring wildlife through camera traps. It provides a platform to upload images, automatically detect and classify animals using a machine learning backend, and visualize the results on an interactive map.

## Features

- **Wildlife Detection:** Automatically detects and classifies animals in uploaded images using a PyTorch-based model.
- **Interactive Map:** Visualizes camera locations and animal spottings on a Leaflet map.
- **Data Visualization:** Presents statistics on animal spottings over different time periods.
- **Scalable Architecture:** Uses a containerized setup with Docker Compose for easy deployment and scaling.
- **Modern Frontend:** A responsive and interactive user interface built with Nuxt.js and Tailwind CSS.
- **RESTful API:** A robust backend API built with FastAPI, providing endpoints for managing locations, images, and spottings.

## Architecture

The application is composed of the following services:

- **Frontend:** A Nuxt.js application that provides the user interface.
- **Backend:** A FastAPI application that serves the API and handles image processing.
- **Database:** A PostgreSQL database to store data about locations, images, and spottings.
- **Load Balancer:** An NGINX load balancer to distribute traffic between multiple backend instances.

All services are containerized using Docker and orchestrated with Docker Compose.

## Getting Started

You can run the application using either Docker Compose (recommended for production) or by running the frontend and backend separately for development.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Node.js](https://nodejs.org/) (v18 or later)
- [Python](https://www.python.org/downloads/) (v3.9 or later) and `uv`

### Using Docker Compose

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd RehPublic
    ```

2.  **Build and start the services:**
    ```bash
    docker-compose up --build
    ```

3.  **Access the application:**
    -   Frontend: [http://localhost:9001](http://localhost:9001)
    -   API: [http://localhost:9002](http://localhost:9002)

### Local Development

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd RehPublic
    ```

2.  **Set up the backend:**
    ```bash
    cd backend
    uv sync
    uv run uvicorn api.main:app --reload --port 8000
    ```

3.  **Set up the frontend:**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

4.  **Access the application:**
    -   Frontend: [http://localhost:3000](http://localhost:3000)
    -   Backend API: [http://localhost:8000](http://localhost:8000)

## Project Structure

```
.
├── backend/            # FastAPI backend application
│   ├── api/            # API logic, endpoints, and services
│   ├── models/         # Machine learning models
│   └── wildlife_processor/ # Image processing logic
├── frontend/           # Nuxt.js frontend application
│   ├── app/            # Main application components and pages
│   └── public/         # Static assets
├── nginx/              # NGINX configuration
├── docker-compose.yml  # Docker Compose configuration
└── Makefile            # Make commands for development
```

## Make Commands

The project includes several convenient Make commands for development:

### Backend Commands
- `make backend-sync`: Install/sync backend dependencies
- `make backend-run`: Start the backend server in development mode
- `make backend-run-workers`: Start the backend with multiple workers
- `make backend-run-celery`: Start the Celery worker for background tasks
- `make backend-test`: Run backend tests in parallel
- `make backend-download-models`: Download the wildlife detection models
- `make backend-sync-images`: **Manually trigger image sync from external sources (default: 10 files/source)**
- `make backend-sync-images-all`: **Manually trigger image sync with higher limit (100 files/source)**

### Frontend Commands
- `make frontend-prep`: Install frontend dependencies
- `make frontend-run`: Start the frontend development server

### Other Commands
- `make redis-start`: Start Redis server (required for Celery)
- `make run`: Start all services (backend, celery, frontend)
- `make lint`: Run linting checks
- `make lint-fix`: Fix linting issues automatically

### Image Pull Synchronization

RehPublic supports automated polling of images from external HTTP directory sources (e.g., wildlife camera APIs). Images are automatically fetched hourly by Celery Beat, but you can also trigger manual synchronization:

```bash
# Sync up to 10 files per source (default)
make backend-sync-images

# Sync up to 100 files per source
make backend-sync-images-all

# Or use the Python script directly with custom limits
cd backend
PYTHONPATH=src uv run python trigger_image_sync.py --max-files 50
```

For more details on setting up image pull sources, see the [Image Pull Sources documentation](backend/src/api/image_pull_sources/README.md).

## API Endpoints

The backend provides a RESTful API with the following main endpoints:

-   `GET /locations`: Get all camera locations.
-   `POST /locations`: Create a new camera location.
-   `GET /locations/{location_id}`: Get a specific location.
-   `POST /locations/{location_id}/image`: Upload an image to a location.
-   `GET /images/{image_id}`: Get image details and detections.
-   `GET /spottings`: Search for spottings within a geographic area.
-   `GET /statistics`: Get statistics on animal spottings.

For a full list of endpoints and their details, see the Swagger documentation at `http://localhost:8000/docs` when the backend is running.

## Technologies Used

-   **Frontend:** [Nuxt.js](https://nuxt.com/), [Vue.js](https://vuejs.org/), [Tailwind CSS](https://tailwindcss.com/), [Leaflet](https://leafletjs.com/)
-   **Backend:** [FastAPI](https://fastapi.tiangolo.com/), [Python](https://www.python.org/), [PyTorch](https://pytorch.org/), [SQLAlchemy](https://www.sqlalchemy.org/)
-   **Database:** [PostgreSQL](https://www.postgresql.org/)
-   **Containerization:** [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/)
-   **Load Balancing:** [NGINX](https://www.nginx.com/)
