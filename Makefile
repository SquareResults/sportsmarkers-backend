.PHONY: install migrate run test lint format check

install:
	uv sync --all-groups

migrate:
	uv run python manage.py migrate

run:
	uv run python manage.py runserver

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

check: lint test
	uv run python manage.py check
	uv run python manage.py makemigrations --check --dry-run

