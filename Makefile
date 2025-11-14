.PHONY: backend-sync backend-run backend-run-workers backend-test backend-download-models frontend-prep frontend-run run pre-commit-install pre-commit-run pre-commit-update lint lint-fix types

backend-sync:
	cd backend && uv sync --extra dev

backend-run:
	cd backend && uv run uvicorn api.main:app --reload --port 8000

backend-run-workers:
	cd backend && uv run uvicorn api.main:app --port 8000 --workers 4

backend-test:
	cd backend && uv run pytest tests/ -v

backend-download-models:
	cd backend && uv run python download_deepfaune_model.py

frontend-prep:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev

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

run: backend-sync frontend-prep
	@echo "Starting backend and frontend..."
	@echo "Backend: http://127.0.0.1:8000"
	@echo "Frontend: Check terminal output for URL"
	@cd backend && uv run uvicorn api.main:app --reload --port 8000 & \
	cd frontend && npm run dev
