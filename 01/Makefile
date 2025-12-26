.PHONY: install lint format typecheck test coverage run

install:
	poetry install

lint:
	poetry run ruff check .
	poetry run black --check .
	poetry run isort --check-only .

format:
	poetry run black .
	poetry run isort .

typecheck:
	poetry run mypy src tests

test:
	poetry run pytest

coverage:
	poetry run pytest --cov=log_analyzer --cov-report=term-missing

run:
	poetry run python log_analyzer.py
