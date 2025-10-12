set dotenv-load := true  # auto-load .env

default: all

all: setup

setup:
    scripts/setup.sh --env local -p 8000

build:
    docker buildx bake

up:
    docker compose up -d

serve:
    exec ./scripts/entrypoint.sh

# Run all checks
check: format lint typecheck

# ---------------------------------------------------

# Format code with Ruff
format:
    uv run ruff format .

# Run linting with Ruff
lint:
    uv run ruff check .

# Run type checking with mypy
typecheck:
    uv run mypy .

# Run linting with Ruff
fix:
    uv run ruff check --fix .

# ---------------------------------------------------

# Clean up cache files
clean:
    rm -rf __pycache__
    rm -rf .pytest_cache
    rm -rf .ruff_cache
    rm -rf .mypy_cache
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

destroy:
    - docker compose down -v
    - rm .env
    - rm -rf data
    - rm -rf .venv
