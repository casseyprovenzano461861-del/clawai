.PHONY: help install dev lint format test test-cov test-integration security docker-build docker-run clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

dev: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

lint: ## Run linters (ruff + mypy)
	ruff check .
	mypy src

format: ## Auto-format code with ruff
	ruff check --fix .
	ruff format .

test: ## Run unit tests (skip slow/perf)
	pytest -m "not slow and not perf"

test-cov: ## Run tests with coverage report
	pytest --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=30 -m "not slow and not perf"

test-integration: ## Run integration tests
	pytest -m integration

security: ## Run security scans
	bandit -r src -ll -ii
	pip-audit --desc

docker-build: ## Build Docker image
	docker build -t clawai:latest .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env clawai:latest

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .eggs/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage coverage.xml bandit-report.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
