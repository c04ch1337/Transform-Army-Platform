.PHONY: help dev test build clean lint format docker-up docker-down db-migrate db-reset install

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "$(CYAN)Transform Army AI - Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Installation
# =============================================================================

install: ## Install all dependencies
	@echo "$(GREEN)Installing Node.js dependencies...$(NC)"
	pnpm install
	@echo "$(GREEN)Installing Python dependencies for adapter...$(NC)"
	cd apps/adapter && poetry install
	@echo "$(GREEN)Installing Python dependencies for evals...$(NC)"
	cd apps/evals && poetry install
	@echo "$(GREEN)Installation complete!$(NC)"

# =============================================================================
# Development
# =============================================================================

dev: ## Start all services in development mode
	@echo "$(GREEN)Starting development environment...$(NC)"
	pnpm dev

dev-web: ## Start only the web application
	@echo "$(GREEN)Starting web application...$(NC)"
	pnpm dev:web

dev-adapter: ## Start only the adapter service
	@echo "$(GREEN)Starting adapter service...$(NC)"
	cd apps/adapter && poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-all: ## Start all services with Docker Compose
	@echo "$(GREEN)Starting all services with Docker Compose...$(NC)"
	docker-compose -f infra/compose/docker-compose.dev.yml up

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	pnpm test

test-web: ## Run web application tests
	@echo "$(GREEN)Running web tests...$(NC)"
	pnpm test:web

test-adapter: ## Run adapter service tests
	@echo "$(GREEN)Running adapter tests...$(NC)"
	cd apps/adapter && poetry run pytest -v

test-evals: ## Run evaluation tests
	@echo "$(GREEN)Running evaluation tests...$(NC)"
	cd apps/evals && poetry run pytest -v

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	cd apps/adapter && poetry run pytest --cov=src --cov-report=html --cov-report=term
	cd apps/evals && poetry run pytest --cov=tests --cov-report=html --cov-report=term

# =============================================================================
# Validation & Testing Scripts
# =============================================================================

test-all: ## Run complete test suite with all validations
	@echo "$(GREEN)Running complete test suite...$(NC)"
	bash scripts/run-all-tests.sh

test-frontend-complete: ## Run comprehensive frontend tests
	@echo "$(GREEN)Running frontend test suite...$(NC)"
	bash scripts/test-frontend-complete.sh

verify-integration: ## Verify all system integrations
	@echo "$(GREEN)Verifying integrations...$(NC)"
	bash scripts/verify-integration.sh

health-report: ## Generate system health report
	@echo "$(GREEN)Generating system health report...$(NC)"
	bash scripts/generate-health-report.sh

validate-env: ## Validate environment configuration
	@echo "$(GREEN)Validating environment...$(NC)"
	bash scripts/validate-env.sh

validate-production: test-all verify-integration health-report ## Complete production readiness validation
	@echo "$(GREEN)Production validation complete!$(NC)"
	@echo "$(CYAN)Review test results in test-results/ directory$(NC)"

generate-report: ## Generate final validation report
	@echo "$(GREEN)Generating final validation report...$(NC)"
	@echo "$(YELLOW)Report generation requires manual review of test results$(NC)"
	@echo "$(CYAN)See FINAL_VALIDATION_REPORT.md for details$(NC)"

# =============================================================================
# Building
# =============================================================================

build: ## Build all services
	@echo "$(GREEN)Building all services...$(NC)"
	pnpm build

build-web: ## Build web application
	@echo "$(GREEN)Building web application...$(NC)"
	pnpm build:web

build-docker: ## Build Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker-compose -f infra/compose/docker-compose.dev.yml build

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linters on all code
	@echo "$(GREEN)Running linters...$(NC)"
	pnpm lint
	cd apps/adapter && poetry run ruff check .
	cd apps/evals && poetry run ruff check .

lint-fix: ## Run linters and auto-fix issues
	@echo "$(GREEN)Running linters with auto-fix...$(NC)"
	pnpm lint:fix
	cd apps/adapter && poetry run ruff check --fix .
	cd apps/evals && poetry run ruff check --fix .

format: ## Format all code
	@echo "$(GREEN)Formatting code...$(NC)"
	pnpm format
	cd apps/adapter && poetry run black .
	cd apps/evals && poetry run black .

format-check: ## Check code formatting
	@echo "$(GREEN)Checking code formatting...$(NC)"
	pnpm format:check
	cd apps/adapter && poetry run black --check .
	cd apps/evals && poetry run black --check .

type-check: ## Run type checking
	@echo "$(GREEN)Running type checking...$(NC)"
	pnpm type-check
	cd apps/adapter && poetry run mypy src

# =============================================================================
# Database
# =============================================================================

db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	cd apps/adapter && poetry run alembic upgrade head

db-rollback: ## Rollback last database migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	cd apps/adapter && poetry run alembic downgrade -1

db-reset: ## Reset database (drop and recreate)
	@echo "$(RED)Resetting database...$(NC)"
	cd apps/adapter && poetry run alembic downgrade base && poetry run alembic upgrade head

db-seed: ## Seed database with sample data
	@echo "$(GREEN)Seeding database...$(NC)"
	cd apps/adapter && poetry run python scripts/seed.py

db-shell: ## Open PostgreSQL shell
	@echo "$(GREEN)Opening database shell...$(NC)"
	docker-compose -f infra/compose/docker-compose.dev.yml exec postgres psql -U postgres -d transform_army

# =============================================================================
# Docker
# =============================================================================

docker-up: ## Start Docker Compose services
	@echo "$(GREEN)Starting Docker services...$(NC)"
	docker-compose -f infra/compose/docker-compose.dev.yml up -d

docker-down: ## Stop Docker Compose services
	@echo "$(GREEN)Stopping Docker services...$(NC)"
	docker-compose -f infra/compose/docker-compose.dev.yml down

docker-logs: ## View Docker Compose logs
	@echo "$(GREEN)Viewing Docker logs...$(NC)"
	docker-compose -f infra/compose/docker-compose.dev.yml logs -f

docker-ps: ## List running Docker containers
	@echo "$(GREEN)Listing Docker containers...$(NC)"
	docker-compose -f infra/compose/docker-compose.dev.yml ps

docker-clean: ## Remove Docker containers and volumes
	@echo "$(RED)Cleaning Docker containers and volumes...$(NC)"
	docker-compose -f infra/compose/docker-compose.dev.yml down -v

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean build artifacts
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	pnpm clean
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-all: ## Clean everything including node_modules
	@echo "$(RED)Cleaning everything...$(NC)"
	pnpm clean:all
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd apps/adapter && rm -rf .venv 2>/dev/null || true
	cd apps/evals && rm -rf .venv 2>/dev/null || true
	@echo "$(GREEN)Deep cleanup complete!$(NC)"

# =============================================================================
# Utilities
# =============================================================================

check-env: ## Check if .env file exists
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found!$(NC)"; \
		echo "$(YELLOW)Copy .env.example to .env and fill in your values:$(NC)"; \
		echo "  cp .env.example .env"; \
		exit 1; \
	else \
		echo "$(GREEN).env file exists$(NC)"; \
	fi

setup: install check-env docker-up db-migrate db-seed ## Complete setup for new development environment
	@echo "$(GREEN)Setup complete! Run 'make dev' to start development.$(NC)"

status: ## Show status of all services
	@echo "$(CYAN)Service Status:$(NC)"
	@echo ""
	@docker-compose -f infra/compose/docker-compose.dev.yml ps

logs-web: ## Show web application logs
	@docker-compose -f infra/compose/docker-compose.dev.yml logs -f web

logs-adapter: ## Show adapter service logs
	@docker-compose -f infra/compose/docker-compose.dev.yml logs -f adapter

logs-db: ## Show database logs
	@docker-compose -f infra/compose/docker-compose.dev.yml logs -f postgres

logs-redis: ## Show Redis logs
	@docker-compose -f infra/compose/docker-compose.dev.yml logs -f redis

# =============================================================================
# CI/CD
# =============================================================================

ci-test: ## Run CI test suite
	@echo "$(GREEN)Running CI tests...$(NC)"
	pnpm test
	cd apps/adapter && poetry run pytest --cov=src
	cd apps/evals && poetry run pytest --cov=tests

ci-lint: ## Run CI linting
	@echo "$(GREEN)Running CI linting...$(NC)"
	pnpm lint
	pnpm format:check
	cd apps/adapter && poetry run ruff check .
	cd apps/adapter && poetry run black --check .
	cd apps/evals && poetry run ruff check .
	cd apps/evals && poetry run black --check .

ci-build: ## Run CI build
	@echo "$(GREEN)Running CI build...$(NC)"
	pnpm build

ci: ci-lint ci-test ci-build ## Run full CI pipeline
	@echo "$(GREEN)CI pipeline complete!$(NC)"