.PHONY: install lint format typecheck test check up up-dev down logs samples hooks

install:
	cd backend && pip install -e ".[dev]"
lint:
	cd backend && ruff check . && ruff format --check .
format:
	cd backend && ruff check --fix . && ruff format .
typecheck:
	cd backend && mypy app tests
test:
	cd backend && pytest
check: lint typecheck test
up:
	docker compose up --build -d --wait
up-dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
down:
	docker compose down
logs:
	docker compose logs -f
samples:
	python scripts/download_samples.py
hooks:
	pre-commit install