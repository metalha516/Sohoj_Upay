.PHONY: help setup up down test lint format typecheck seed clean

help:
	@echo "Available commands:"
	@echo "  make setup      - Install Python dependencies and pre-commit hooks"
	@echo "  make up         - Start all services with docker compose"
	@echo "  make down       - Stop all docker compose services"
	@echo "  make test       - Run backend test suite"
	@echo "  make lint       - Run ruff linter check"
	@echo "  make format     - Run ruff code formatting"
	@echo "  make typecheck  - Run mypy static type checking"
	@echo "  make seed       - Seed synthetic data (Phase 4)"
	@echo "  make clean      - Clean cache and temporary files"

setup:
	python -m pip install --upgrade pip
	python -m pip install -e backend/.[dev]
	python -m pip install pre-commit
	pre-commit install || true

up:
	docker compose up -d

down:
	docker compose down

test:
	python -m pytest backend/tests

lint:
	python -m ruff check .

format:
	python -m ruff format .

typecheck:
	python -m mypy --config-file mypy.ini backend/app data/synthetic

seed:
	python -m data.synthetic.cli generate --users 600 --seed 42

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]" || true
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache')]" || true
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.mypy_cache')]" || true
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.ruff_cache')]" || true
