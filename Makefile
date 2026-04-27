.PHONY: help install dev test lint format clean docker-up docker-down docker-logs

# Default target
help:
	@echo "Twitter Scraping SaaS Platform - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install all dependencies (backend + frontend)"
	@echo "  make dev           - Start development servers (backend + frontend + worker)"
	@echo "  make docker-up     - Start all services with Docker Compose"
	@echo "  make docker-down   - Stop all Docker services"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests (unit + property + integration)"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-property - Run property-based tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make test-watch    - Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run all linters (backend + frontend)"
	@echo "  make lint-backend  - Run backend linters (flake8, black, mypy)"
	@echo "  make lint-frontend - Run frontend linters (eslint, tsc)"
	@echo "  make format        - Auto-format code (black + prettier)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Remove build artifacts and cache files"
	@echo "  make clean-docker  - Remove Docker volumes and images"

# Installation
install:
	@echo "📦 Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Installation complete!"

# Development
dev:
	@echo "🚀 Starting development servers..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:5173"
	@echo "Press Ctrl+C to stop all servers"
	@make -j3 dev-backend dev-frontend dev-worker

dev-backend:
	cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev-worker:
	cd backend && celery -A src.workers.celery_app worker --loglevel=info

# Docker
docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "Frontend: http://localhost"
	@echo "Backend: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-build:
	@echo "🔨 Building Docker images..."
	docker-compose build

# Testing
test:
	@echo "🧪 Running all tests..."
	cd backend && pytest tests/ --ignore=tests/e2e/ -v --tb=short

test-unit:
	@echo "🧪 Running unit tests..."
	cd backend && pytest tests/ --ignore=tests/integration/ --ignore=tests/e2e/ -v

test-property:
	@echo "🧪 Running property-based tests..."
	cd backend && HYPOTHESIS_PROFILE=ci pytest tests/ -k "properties" -v

test-integration:
	@echo "🧪 Running integration tests..."
	cd backend && pytest tests/integration/ -v

test-e2e:
	@echo "🧪 Running end-to-end tests..."
	cd backend && pytest tests/e2e/ -v

test-coverage:
	@echo "📊 Running tests with coverage..."
	cd backend && pytest tests/ --ignore=tests/e2e/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report: backend/htmlcov/index.html"

test-watch:
	@echo "👀 Running tests in watch mode..."
	cd backend && pytest-watch tests/ -- --ignore=tests/integration/ --ignore=tests/e2e/ -v

# Linting
lint: lint-backend lint-frontend

lint-backend:
	@echo "🔍 Linting backend..."
	cd backend && flake8 src/ tests/
	cd backend && black --check src/ tests/
	cd backend && mypy src/ --ignore-missing-imports

lint-frontend:
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint
	cd frontend && npm run type-check

# Formatting
format:
	@echo "✨ Formatting code..."
	cd backend && black src/ tests/
	cd frontend && npm run lint -- --fix
	@echo "✅ Code formatted!"

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".hypothesis" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf dist/ node_modules/.vite/ 2>/dev/null || true
	@echo "✅ Cleanup complete!"

clean-docker:
	@echo "🧹 Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Docker cleanup complete!"

# Database
db-migrate:
	@echo "🗄️  Running database migrations..."
	cd backend && python -m src.core.database
	@echo "✅ Migrations complete!"

# CI/CD simulation
ci:
	@echo "🤖 Running CI/CD checks locally..."
	@make lint
	@make test-coverage
	@echo "✅ All CI/CD checks passed!"
