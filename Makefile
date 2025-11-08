.PHONY: backend-sync backend-run frontend-prep frontend-run run

backend-sync:
	cd backend && uv sync

backend-run:
	cd backend && uvicorn api.main:app --reload --port 8000

frontend-prep:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev

run: backend-sync frontend-prep
	@echo "Starting backend and frontend..."
	@echo "Backend: http://127.0.0.1:8000"
	@echo "Frontend: Check terminal output for URL"
	@cd backend && uvicorn api.main:app --reload --port 8000 & \
	cd frontend && npm run dev
