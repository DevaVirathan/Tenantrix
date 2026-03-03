# =============================================================================
# Tenantrix — Makefile convenience commands
# =============================================================================

.PHONY: help install dev run test lint format migrate-create migrate-up migrate-down clean docker-up docker-down

# Default target
help:
	@echo ""
	@echo "  Tenantrix — Available commands"
	@echo ""
	@echo "  Setup"
	@echo "    make install        Install runtime dependencies"
	@echo "    make dev            Install all dependencies including dev tools"
	@echo ""
	@echo "  Run"
	@echo "    make run            Start the API server (reload mode)"
	@echo "    make docker-up      Start all Docker services"
	@echo "    make docker-down    Stop all Docker services"
	@echo ""
	@echo "  Database"
	@echo "    make migrate-create msg=\"description\"  Generate a new migration"
	@echo "    make migrate-up     Apply all pending migrations"
	@echo "    make migrate-down   Roll back the last migration"
	@echo ""
	@echo "  Quality"
	@echo "    make test           Run tests with coverage"
	@echo "    make lint           Lint with ruff"
	@echo "    make format         Format with ruff + black"
	@echo ""

# --------------------------------------------------------------------------- #
# Setup                                                                       #
# --------------------------------------------------------------------------- #
install:
	pip install --upgrade pip && pip install .

dev:
	pip install --upgrade pip && pip install ".[dev]"

# --------------------------------------------------------------------------- #
# Run                                                                         #
# --------------------------------------------------------------------------- #
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# --------------------------------------------------------------------------- #
# Database                                                                    #
# --------------------------------------------------------------------------- #
migrate-create:
	alembic revision --autogenerate -m "$(msg)"

migrate-up:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-history:
	alembic history --verbose

# --------------------------------------------------------------------------- #
# Testing                                                                     #
# --------------------------------------------------------------------------- #
test:
	pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

test-fast:
	pytest tests/ -x --tb=short

# --------------------------------------------------------------------------- #
# Lint & format                                                               #
# --------------------------------------------------------------------------- #
lint:
	ruff check app/ tests/

format:
	ruff format app/ tests/
	ruff check --fix app/ tests/

# --------------------------------------------------------------------------- #
# Docker                                                                      #
# --------------------------------------------------------------------------- #
docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-test:
	docker compose --profile test run --rm test

docker-logs:
	docker compose logs -f api

# --------------------------------------------------------------------------- #
# Cleanup                                                                     #
# --------------------------------------------------------------------------- #
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache .mypy_cache dist build *.egg-info
