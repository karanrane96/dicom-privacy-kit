# Makefile for DICOM Privacy Kit

.PHONY: help install install-dev test test-cov lint format clean docs

help:
	@echo "DICOM Privacy Kit - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install package"
	@echo "  make install-dev      Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Format code with black/isort"
	@echo "  make test             Run tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Remove build artifacts"
	@echo "  make pre-commit       Run pre-commit hooks"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=dicom_privacy_kit --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

lint:
	ruff check dicom_privacy_kit tests
	black --check dicom_privacy_kit tests
	isort --check-only dicom_privacy_kit tests

format:
	black dicom_privacy_kit tests
	isort dicom_privacy_kit tests
	ruff check --fix dicom_privacy_kit tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build dist .eggs *.egg-info
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf .mypy_cache .ruff_cache

pre-commit:
	pre-commit run --all-files
