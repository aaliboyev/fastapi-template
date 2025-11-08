# FastAPI Template - Production-Ready API
# ==========================================
# Comprehensive Makefile for development, testing, and deployment
# Run 'make' or 'make help' to see available commands

.PHONY: help list setup install sync update dev dev-port dev-debug serve shell ishell
.PHONY: check format lint fix fix-unsafe typecheck
.PHONY: test test-cov test-watch test-file test-pattern test-verbose
.PHONY: db-migrate db-upgrade db-downgrade db-downgrade-to db-current db-history db-reset db-shell
.PHONY: build up up-logs down logs logs-service ps restart rebuild exec
.PHONY: clean clean-all destroy deps-tree deps-outdated deps-export
.PHONY: all ci pre-push deploy-prep

# Include .env file if it exists
-include .env
export

# Default target shows help
.DEFAULT_GOAL := help

# ================================
# Help & Documentation
# ================================

help: ## Show this help message
	@echo "FastAPI Template - Production-Ready API"
	@echo "========================================"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  setup              - Initial project setup (create .env, install deps)"
	@echo "  install            - Install Python dependencies with uv"
	@echo "  sync               - Sync dependencies (including dev)"
	@echo "  update             - Update dependencies to latest versions"
	@echo ""
	@echo "Development Server:"
	@echo "  dev                - Run development server with hot reload"
	@echo "  dev-port PORT=3000 - Run dev server on custom port"
	@echo "  dev-debug          - Run dev server with debugger enabled"
	@echo "  serve              - Run production server via entrypoint"
	@echo "  shell              - Open Python shell with app context"
	@echo "  ishell             - Open IPython shell (if installed)"
	@echo ""
	@echo "Code Quality:"
	@echo "  check              - Run all checks (format, lint, typecheck)"
	@echo "  format             - Format code with Ruff"
	@echo "  lint               - Run linting with Ruff"
	@echo "  fix                - Auto-fix linting issues"
	@echo "  fix-unsafe         - Auto-fix with unsafe fixes"
	@echo "  typecheck          - Run type checking with mypy"
	@echo ""
	@echo "Testing:"
	@echo "  test               - Run all tests with pytest"
	@echo "  test-cov           - Run tests with coverage report"
	@echo "  test-watch         - Run tests in watch mode"
	@echo "  test-file FILE=... - Run specific test file"
	@echo "  test-pattern PAT=...- Run tests matching pattern"
	@echo "  test-verbose       - Run tests with verbose output"
	@echo ""
	@echo "Database:"
	@echo "  db-migrate MSG=\"...\"- Generate new migration"
	@echo "  db-upgrade         - Apply pending migrations"
	@echo "  db-downgrade       - Rollback last migration"
	@echo "  db-current         - Show current migration revision"
	@echo "  db-history         - Show migration history"
	@echo "  db-reset           - Reset database (drop all, upgrade)"
	@echo "  db-shell           - Open PostgreSQL shell"
	@echo ""
	@echo "Docker:"
	@echo "  build              - Build Docker images"
	@echo "  up                 - Start Docker containers"
	@echo "  up-logs            - Start containers with logs"
	@echo "  down               - Stop Docker containers"
	@echo "  logs               - Show Docker logs"
	@echo "  ps                 - Show running containers"
	@echo "  restart            - Restart all containers"
	@echo "  rebuild            - Rebuild and restart containers"
	@echo ""
	@echo "Utilities:"
	@echo "  clean              - Clean cache files and artifacts"
	@echo "  clean-all          - Deep clean (cache, venv, docker)"
	@echo "  destroy            - Destroy everything (use with caution!)"
	@echo "  deps-tree          - Show dependency tree"
	@echo "  deps-outdated      - Show outdated dependencies"
	@echo "  deps-export        - Export deps to requirements.txt"
	@echo ""
	@echo "Workflows:"
	@echo "  all                - Run complete workflow (setup, check, test)"
	@echo "  ci                 - Run CI pipeline locally"
	@echo "  pre-push           - Run checks before pushing"
	@echo "  deploy-prep        - Prepare for production deployment"
	@echo ""

list: ## Show all available targets
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$$@$$'

# ================================
# Setup & Installation
# ================================

setup: ## Initial project setup (create .env, install dependencies)
	@echo "🚀 Setting up FastAPI Template project..."
	@bash scripts/setup.sh --env local -p 8000
	@echo "✅ Setup complete!"

install: ## Install Python dependencies
	@echo "📦 Installing dependencies..."
	@uv sync
	@echo "✅ Dependencies installed!"

sync: ## Sync dependencies (including dev groups)
	@echo "🔄 Syncing all dependencies..."
	@uv sync --all-groups
	@echo "✅ Dependencies synced!"

update: ## Update dependencies to latest versions
	@echo "⬆️  Updating dependencies..."
	@uv lock --upgrade
	@uv sync
	@echo "✅ Dependencies updated!"

# ================================
# Development Server
# ================================

dev: ## Run development server with hot reload
	@echo "🔥 Starting development server..."
	@uv run uvicorn src.main:app --reload --host localhost --port 8000

dev-port: ## Run development server on custom port (usage: make dev-port PORT=3000)
	@echo "🔥 Starting development server on port $(PORT)..."
	@uv run uvicorn src.main:app --reload --host localhost --port $(PORT)

dev-debug: ## Run development server with debugger enabled
	@echo "🐛 Starting development server with debugger..."
	@ENABLE_DEBUG=true DEBUG_PORT=5678 ./scripts/entrypoint.sh

serve: ## Run production server via entrypoint
	@echo "🚀 Starting production server..."
	@./scripts/entrypoint.sh

shell: ## Open Python shell with app context
	@echo "🐍 Opening Python shell..."
	@uv run python

ishell: ## Open IPython shell with app context (if installed)
	@echo "🐍 Opening IPython shell..."
	@uv run ipython

# ================================
# Code Quality
# ================================

check: format lint typecheck ## Run all checks (format, lint, typecheck)
	@echo "✅ All checks passed!"

format: ## Format code with Ruff
	@echo "🎨 Formatting code..."
	@uv run ruff format .
	@echo "✅ Code formatted!"

lint: ## Run linting with Ruff
	@echo "🔍 Running linter..."
	@uv run ruff check .
	@echo "✅ Linting complete!"

fix: ## Auto-fix linting issues
	@echo "🔧 Auto-fixing linting issues..."
	@uv run ruff check --fix .
	@echo "✅ Issues fixed!"

fix-unsafe: ## Auto-fix with unsafe fixes
	@echo "🔧 Auto-fixing with unsafe fixes..."
	@uv run ruff check --fix --unsafe-fixes .
	@echo "✅ Issues fixed!"

typecheck: ## Run type checking with mypy
	@echo "🔎 Running type checker..."
	@uv run mypy .
	@echo "✅ Type checking complete!"

# ================================
# Testing
# ================================

test: ## Run all tests with pytest
	@echo "🧪 Running tests..."
	@uv run pytest
	@echo "✅ Tests complete!"

test-cov: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	@uv run coverage run -m pytest
	@uv run coverage report
	@uv run coverage html
	@echo "✅ Coverage report generated! Open htmlcov/index.html"

test-watch: ## Run tests in watch mode (requires pytest-watch)
	@echo "👀 Running tests in watch mode..."
	@uv run ptw

test-file: ## Run specific test file (usage: make test-file FILE=tests/test_users.py)
	@echo "🧪 Running tests in $(FILE)..."
	@uv run pytest $(FILE)

test-pattern: ## Run tests matching pattern (usage: make test-pattern PATTERN=user)
	@echo "🧪 Running tests matching '$(PATTERN)'..."
	@uv run pytest -k "$(PATTERN)"

test-verbose: ## Run tests with verbose output
	@echo "🧪 Running tests (verbose)..."
	@uv run pytest -vv

# ================================
# Database
# ================================

db-migrate: ## Generate new migration (usage: make db-migrate MSG="add users table")
	@echo "📝 Generating migration: $(MSG)..."
	@uv run alembic revision --autogenerate -m "$(MSG)"
	@echo "✅ Migration created!"

db-upgrade: ## Apply pending migrations
	@echo "⬆️  Applying migrations..."
	@uv run alembic upgrade head
	@echo "✅ Database upgraded!"

db-downgrade: ## Rollback last migration
	@echo "⬇️  Rolling back migration..."
	@uv run alembic downgrade -1
	@echo "✅ Migration rolled back!"

db-downgrade-to: ## Rollback to specific revision (usage: make db-downgrade-to REV=abc123)
	@echo "⬇️  Rolling back to $(REV)..."
	@uv run alembic downgrade $(REV)
	@echo "✅ Rolled back to $(REV)!"

db-current: ## Show current migration revision
	@echo "📍 Current migration:"
	@uv run alembic current

db-history: ## Show migration history
	@echo "📜 Migration history:"
	@uv run alembic history

db-reset: ## Reset database (drop all, upgrade)
	@echo "⚠️  Resetting database..."
	@echo "This will drop all data! Press Ctrl+C within 3 seconds to cancel..."
	@sleep 3
	@uv run alembic downgrade base
	@uv run alembic upgrade head
	@echo "✅ Database reset complete!"

db-shell: ## Open PostgreSQL shell
	@echo "💾 Opening PostgreSQL shell..."
	@psql $${DATABASE_URL:-postgresql://localhost/fastapi_template}

# ================================
# Docker
# ================================

build: ## Build Docker images
	@echo "🏗️  Building Docker images..."
	@docker buildx bake
	@echo "✅ Build complete!"

up: ## Start Docker containers
	@echo "🚀 Starting Docker containers..."
	@docker compose up -d
	@echo "✅ Containers started!"

up-logs: ## Start Docker containers with logs
	@echo "🚀 Starting Docker containers with logs..."
	@docker compose up

down: ## Stop Docker containers
	@echo "🛑 Stopping Docker containers..."
	@docker compose down -v
	@echo "✅ Containers stopped!"

logs: ## Show Docker logs
	@docker compose logs -f

logs-service: ## Show logs for specific service (usage: make logs-service SVC=api)
	@docker compose logs -f $(SVC)

ps: ## Show running containers
	@docker compose ps

restart: ## Restart all containers
	@echo "🔄 Restarting containers..."
	@docker compose restart
	@echo "✅ Containers restarted!"

rebuild: ## Rebuild and restart containers
	@echo "🔄 Rebuilding and restarting..."
	@docker compose down
	@docker compose build
	@docker compose up -d
	@echo "✅ Rebuild complete!"

exec: ## Execute command in running container (usage: make exec SVC=api CMD=bash)
	@docker compose exec $(SVC) $(CMD)

# ================================
# Utilities
# ================================

clean: ## Clean cache files and artifacts
	@echo "🧹 Cleaning cache files..."
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@rm -rf .ruff_cache
	@rm -rf .mypy_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@rm -rf *.egg-info
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

clean-all: clean ## Deep clean (cache, venv, docker volumes)
	@echo "🧹 Deep cleaning..."
	@rm -rf .venv
	@docker compose down -v 2>/dev/null || true
	@echo "✅ Deep clean complete!"

destroy: ## Destroy everything (use with caution!)
	@echo "⚠️  DESTROYING EVERYTHING! This cannot be undone!"
	@echo "Press Ctrl+C within 5 seconds to cancel..."
	@sleep 5
	-@docker compose down -v
	-@rm .env
	-@rm -rf data
	-@rm -rf .venv
	-@rm -rf __pycache__
	-@rm -rf .pytest_cache
	-@rm -rf .ruff_cache
	-@rm -rf .mypy_cache
	@echo "💥 Project destroyed!"

deps-tree: ## Show dependency tree
	@echo "🌳 Dependency tree:"
	@uv tree

deps-outdated: ## Show outdated dependencies
	@echo "📊 Checking for outdated dependencies..."
	@uv pip list --outdated

deps-export: ## Export dependencies to requirements.txt
	@echo "📋 Exporting dependencies..."
	@uv export --no-dev > requirements.txt
	@echo "✅ Exported to requirements.txt"

# ================================
# Workflows
# ================================

all: sync check test ## Run complete workflow (setup, check, test)
	@echo "✅ Complete workflow finished!"

ci: check test-cov ## Run CI pipeline locally
	@echo "✅ CI pipeline complete!"

pre-push: format fix typecheck test ## Run checks before pushing
	@echo "✅ Ready to push!"

deploy-prep: check test-cov ## Prepare for production deployment
	@echo "✅ Ready for deployment!"
