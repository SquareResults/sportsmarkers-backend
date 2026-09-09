# SportsMarkers Backend

Backend API for SportsMarkers, a platform where student-athletes build verified, data-backed portfolios for coaches and recruiters.

## Technology

- Python 3.12
- Django 5.2 and Django REST Framework
- PostgreSQL
- Redis and Celery
- JWT authentication
- OpenAPI documentation with Swagger UI
- Docker Compose

## Project structure

The application is a modular monolith. Each domain lives in an independent Django app while sharing one deployment and database.

```text
apps/
├── accounts/       # Identity, authentication, verification, security
├── athletes/       # Athlete profile and onboarding
├── sports/         # Sports, positions, stat definitions and values
├── education/      # Schools, GPA, graduation and eligibility
├── careers/        # Teams, seasons, events, results and awards
├── media_library/  # Photos and highlight videos
├── portfolios/     # Portfolio completion and publishing
├── recruiting/     # Preferences, contact requests and opportunities
├── analytics/      # Portfolio visits and engagement
├── notifications/  # Alerts and delivery preferences
├── subscriptions/  # Plans, billing state and entitlements
└── common/         # Shared base models and utilities
```

## Local setup with uv

1. Install [uv](https://docs.astral.sh/uv/).
2. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

3. For development without Docker, change `DATABASE_URL` in `.env` to:

   ```text
   sqlite:///db.sqlite3
   ```

4. Install dependencies and prepare the database:

   ```bash
   uv sync --all-groups
   uv run python manage.py migrate
   uv run python manage.py createsuperuser
   ```

5. Start the API:

   ```bash
   uv run python manage.py runserver
   ```

The API is available at `http://localhost:8000`, and Swagger UI is at `http://localhost:8000/api/docs/`.

## Docker setup

```bash
cp .env.example .env
docker compose up --build
docker compose exec api uv run python manage.py migrate
```

## Initial endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health/` | Database-backed health check |
| `POST` | `/api/v1/auth/register/` | Create an athlete account |
| `POST` | `/api/v1/auth/token/` | Obtain JWT access and refresh tokens |
| `POST` | `/api/v1/auth/token/refresh/` | Rotate an access token |
| `GET/PATCH` | `/api/v1/auth/me/` | Read or update the authenticated account |
| `GET` | `/api/schema/` | OpenAPI schema |
| `GET` | `/api/docs/` | Swagger UI |

## Quality checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest
```

## Configuration

Never commit `.env`. Production requires a unique `DJANGO_SECRET_KEY`, PostgreSQL `DATABASE_URL`, Redis URL, explicit allowed hosts, and approved frontend origins.

