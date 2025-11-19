# Use bash for nicer scripting
SHELL := /bin/bash

# Default environment variables
UV := uv
PYTHON := uv run python

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
	TESTING=1 $(UV) run pytest -q

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
	$(UV) run celery -A app.workers.celery_app.celery_app worker --loglevel=INFO

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
