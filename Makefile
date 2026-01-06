.PHONY: help install install-dev sync test test-verbose coverage clean docs example-scripts build lint format check benchmark test-large upgrade

# Default target
help:
	@echo "pymzML - Makefile commands"
	@echo ""
	@echo "Setup commands:"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install all dependencies including dev"
	@echo "  make sync             - Sync dependencies with uv.lock"
	@echo ""
	@echo "Testing commands:"
	@echo "  make test             - Run tests with pytest"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make coverage         - Run tests with coverage report"
	@echo "  make example-scripts  - Run example scripts"
	@echo "  make benchmark        - Run performance benchmarks"
	@echo "  make test-large       - Test centroiding on a large mzML file"
	@echo ""
	@echo "Documentation commands:"
	@echo "  make docs             - Build documentation with Sphinx"
	@echo ""
	@echo "Build commands:"
	@echo "  make build            - Build the package"
	@echo "  make clean            - Clean build artifacts and cache files"
	@echo ""
	echo "Code quality commands:"
	echo "  make lint             - Run linters (if configured)"
	echo "  make format           - Format code (if configured)"
	echo "  make check            - Run all checks"
	echo "  make ty               - Run type checking with ty"
	echo "  make upgrade          - Upgrade Python syntax with pyupgrade"

# Installation
install:
	uv sync --no-dev --python-preference managed

install-dev:
	uv sync --all-extras --python-preference managed

sync:
	uv sync --all-extras --python-preference managed

# Testing
test:
	uv run --python-preference managed pytest

test-verbose:
	uv run --python-preference managed pytest -v

coverage:
	uv run --python-preference managed coverage erase
	uv run --python-preference managed coverage run -m pytest
	uv run --python-preference managed coverage report --omit=".venv/*","tests/*"
	uv run --python-preference managed coverage html
	@echo "Coverage report generated in htmlcov/index.html"

example-scripts:
	uv run --python-preference managed python example_scripts/access_run_info.py
	uv run --python-preference managed python example_scripts/access_spectra_and_chromatograms.py
	uv run --python-preference managed python example_scripts/compare_spectra.py
	uv run --python-preference managed python example_scripts/extract_ion_chromatogram.py
	uv run --python-preference managed python example_scripts/extreme_values.py
	uv run --python-preference managed python example_scripts/get_precursors.py
	uv run --python-preference managed python example_scripts/has_peak.py
	uv run --python-preference managed python example_scripts/highest_peaks.py

# Benchmarking
benchmark:
	uv run --python-preference managed python benchmark_centroiding.py

test-large:
	uv run --python-preference managed python test_centroiding_performance.py

# Documentation
docs:
	cd docs && uv run sphinx-build source build
	@echo "Documentation built in docs/build/"

# Build
build:
	uv build

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*.so' -delete
	@echo "Cleaned build artifacts and cache files"

# Code quality (placeholders - customize based on your tools)
lint:
	@echo "Add your linting commands here (e.g., ruff, flake8, pylint)"
	# uv run ruff check pymzml tests

format:
	uv run ruff format pymzml tests

check: lint test
	@echo "All checks passed!"

ty: 
	uv run --python-preference managed ty check pymzml

upgrade:
	@echo "Upgrading Python syntax to 3.11+..."
	@find pymzml tests example_scripts -name "*.py" -type f -exec uv run --python-preference managed pyupgrade --py311-plus {} +
	@echo "Python syntax upgraded to 3.11+"
