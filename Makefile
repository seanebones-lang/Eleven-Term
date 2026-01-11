.PHONY: install test format lint typecheck security benchmark build clean quality ci help

# Installation
install:
	pip install -r requirements-dev.txt
	pip install -e .

# Testing
test:
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

test-fast:
	pytest tests/ -v --tb=short

test-benchmarks:
	pytest tests/benchmarks/ -v --benchmark-only --benchmark-json=benchmark.json

# Code Quality
format:
	black .
	isort .

lint:
	flake8 . --max-line-length=100 --exclude=tests,htmlcov,.git

typecheck:
	mypy grok_agent.py --ignore-missing-imports

security:
	bandit -r . -f json -o bandit-report.json
	bandit -r . -ll

# Benchmarks
benchmark:
	pytest tests/benchmarks/ -v --benchmark-only --benchmark-json=benchmark.json
	python scripts/generate_performance_report.py benchmark.json

# Build (PyInstaller)
build:
	pyinstaller --onefile --name grok grok_agent.py

# Clean
clean:
	rm -rf build/ dist/ *.egg-info htmlcov/ .pytest_cache/ .coverage .mypy_cache
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -f benchmark.json bandit-report.json

# All quality checks
quality: format lint typecheck security test

# CI pipeline simulation
ci: quality benchmark

# Help
help:
	@echo "Available targets:"
	@echo "  install       - Install dependencies"
	@echo "  test          - Run tests with coverage"
	@echo "  format        - Format code with black and isort"
	@echo "  lint          - Lint code with flake8"
	@echo "  typecheck     - Type check with mypy"
	@echo "  security      - Security scan with bandit"
	@echo "  benchmark     - Run performance benchmarks"
	@echo "  build         - Build binary with PyInstaller"
	@echo "  clean         - Clean build artifacts"
	@echo "  quality       - Run all quality checks"
	@echo "  ci            - Run CI pipeline (quality + benchmarks)"