.PHONY: install install-dev sync test test-verbose coverage clean docs example-scripts build lint format check benchmark test-large upgrade

install:
	uv sync --no-dev --python-preference managed

install-dev:
	uv sync --all-extras --python-preference managed

sync:
	uv sync --all-extras --python-preference managed

test:
	uv run --python-preference managed pytest

build:
	uv build

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

lint:
	uv run ruff check pymzml

format:
	uv run ruff check --select I --fix pymzml
	uv run ruff format pymzml

check: lint test
	@echo "All checks passed!"

ty: 
	uv run --python-preference managed ty check pymzml

upgrade:
	@echo "Upgrading Python syntax to 3.11+..."
	@find pymzml tests example_scripts -name "*.py" -type f -exec uv run --python-preference managed pyupgrade --py311-plus {} +
	@echo "Python syntax upgraded to 3.11+"
