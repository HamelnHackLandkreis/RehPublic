.PHONY: backend-sync backend-run backend-run-workers backend-run-celery backend-test backend-download-models backend-sync-images frontend-prep frontend-run redis-start run pre-commit-install pre-commit-run pre-commit-update lint lint-fix types

backend-sync:
	cd backend && uv sync --extra dev

backend-run:
	cd backend && uv run python download_deepfaune_model.py
	cd backend && PYTHONPATH=src uv run uvicorn api.main:app --reload --port 8000

backend-run-workers:
	cd backend && uv run python download_deepfaune_model.py
	cd backend && PYTHONPATH=src uv run uvicorn api.main:app --port 8000 --workers 4

backend-run-celery:
	cd backend && PYTHONPATH=src uv run celery -A src.celery_app worker --loglevel=info --concurrency=1

backend-test:
	cd backend && PYTHONPATH=src uv run pytest tests/ -v -n auto

backend-test-serial:
	cd backend && PYTHONPATH=src uv run pytest tests/ -v

backend-download-models:
	cd backend && uv run python download_deepfaune_model.py

backend-sync-images:
	cd backend && PYTHONPATH=src uv run python trigger_image_sync.py

backend-sync-images-all:
	cd backend && PYTHONPATH=src uv run python trigger_image_sync.py --max-files 100

frontend-prep:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev

redis-start:
	@echo "Starting Redis..."
	@docker-compose up -d redis || docker run -d --name rehpublic-redis -p 6379:6379 redis:7-alpine || echo "Redis already running or Docker not available"

pre-commit-install:
	cd backend && uv sync --extra dev
	cd backend && uv run pre-commit install

pre-commit-run:
	cd backend && uv run pre-commit run --all-files

pre-commit-update:
	cd backend && uv run pre-commit autoupdate

lint:
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .

lint-fix:
	cd backend && uv run ruff check --fix .
	cd backend && uv run ruff format .

types:
	cd backend && uv run mypy api/ --ignore-missing-imports

run: backend-sync frontend-prep redis-start
	@echo "Starting backend, celery, and frontend..."
	@echo "Backend: http://127.0.0.1:8000"
	@echo "Frontend: Check terminal output for URL"
	@sleep 2
	@cd backend && uv run python download_deepfaune_model.py && PYTHONPATH=src uv run uvicorn api.main:app --reload --port 8000 & \
	cd backend && PYTHONPATH=src uv run celery -A src.celery_app worker --loglevel=info --concurrency=1 & \
	cd frontend && npm run dev
