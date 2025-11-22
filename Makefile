# Use bash for nicer scripting
SHELL := /bin/bash

# Default environment variables
UV := uv
PYTHON := uv run python
PYTEST_ARGS ?= -q --cov=app --cov-report=term-missing
REVIEW_WORKER_CONCURRENCY ?= 1

# --------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------

.PHONY: install
install:
	$(UV) sync --all-extras --dev

.PHONY: upgrade
upgrade:
	$(UV) lock --upgrade
	$(UV) sync --all-extras --dev

# --------------------------------------------------------------------
# Code quality
# --------------------------------------------------------------------

.PHONY: lint
lint:
	$(UV) run ruff check app tests

.PHONY: fix
fix:
	$(UV) run ruff check app tests --fix
	$(UV) run ruff format app tests

# Legacy "format" target → now uses Ruff (Google style)
.PHONY: format
format:
	$(UV) run ruff format app tests

.PHONY: typecheck
typecheck:
	$(UV) run mypy app

.PHONY: test
test:
	TESTING=1 $(UV) run pytest $(PYTEST_ARGS)

.PHONY: check
check: lint typecheck test

# --------------------------------------------------------------------
# App / workers
# --------------------------------------------------------------------

.PHONY: run-api
run-api:
	$(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: worker
worker:
	$(UV) run celery -A app.workers.celery_app.celery_app worker --loglevel=INFO --concurrency=$(REVIEW_WORKER_CONCURRENCY)

# --------------------------------------------------------------------
# DB / Alembic
# --------------------------------------------------------------------

.PHONY: db-upgrade
db-upgrade:
	$(UV) run alembic upgrade head

.PHONY: db-revision
db-revision:
	@if [ -z "$$msg" ]; then \
		echo "Usage: make db-revision msg=\"message\""; \
		exit 1; \
	fi
	$(UV) run alembic revision -m "$$msg"

.PHONY: db-downgrade
db-downgrade:
	@if [ -z "$$rev" ]; then \
		echo "Usage: make db-downgrade rev=\"base\"|\"-1\"|\"<revision>\""; \
		exit 1; \
	fi
	$(UV) run alembic downgrade "$$rev"

# --------------------------------------------------------------------
# Misc
# --------------------------------------------------------------------

.PHONY: clean
clean:
	find . -name '__pycache__' -type d -exec rm -rf {} +
	find . -name '*.pyc' -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

.PHONY: dev
dev: install

# --------------------------------------------------------------------
# Docker Dev Environment
# --------------------------------------------------------------------

DEV_COMPOSE := docker compose -f docker-compose.dev.yml

.PHONY: dev-up
dev-up:
	$(DEV_COMPOSE) up --build -d
	@echo "🚀 Dev environment is up!"
	@echo "API:    http://localhost:8000"
	@echo "Debug:  localhost:5678 (API), localhost:5679 (Worker)"

.PHONY: dev-down
dev-down:
	$(DEV_COMPOSE) down --remove-orphans
	@echo "🛑 Dev environment stopped"

.PHONY: dev-build
dev-build:
	$(DEV_COMPOSE) build
	@echo "🔨 Dev images rebuilt"

.PHONY: dev-logs
dev-logs:
	$(DEV_COMPOSE) logs -f

.PHONY: dev-api-shell
dev-api-shell:
	$(DEV_COMPOSE) exec api-dev /bin/bash || $(DEV_COMPOSE) exec api-dev /bin/sh

.PHONY: dev-worker-shell
dev-worker-shell:
	$(DEV_COMPOSE) exec worker-dev /bin/bash || $(DEV_COMPOSE) exec worker-dev /bin/sh

.PHONY: dev-ps
dev-ps:
	$(DEV_COMPOSE) ps
