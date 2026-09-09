# SportsMarkers Backend

Production MVP built with Django 5.2, Django REST Framework, PostgreSQL, SimpleJWT,
Gunicorn, WhiteNoise, and drf-spectacular. The existing email-based UUID User and
modular Django apps are preserved. There is no Redis/Celery runtime dependency.

## Local Docker setup

Requires Docker Desktop (running) and Docker Compose. From the repository root:

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs -f api
# Once the API is ready, in another terminal:
docker compose exec api python manage.py seed_demo
```

The API container applies migrations before starting the development server.
PostgreSQL data persists in the Compose volume. Source is copied into the image;
after edits, run `docker compose up --build -d` again. Stop with
`docker compose down` (preserves data). `.env` is ignored by Git and Docker.

- API: http://localhost:8000/api/v1/
- Swagger: http://localhost:8000/api/docs/
- OpenAPI: http://localhost:8000/api/schema/
- Health: http://localhost:8000/api/v1/health/
- Admin: http://localhost:8000/admin/ (create an administrator with
  `docker compose exec api python manage.py createsuperuser`)

## Local uv setup and checks

Python 3.12 or 3.13 and uv are required. SQLite is the default for local development.
The application does not implicitly load `.env`; Docker loads it via `env_file`.
For a host PostgreSQL connection, export `DATABASE_URL` explicitly, or use
`uv run --env-file .env ...` with a host-accessible database URL.

```bash
uv sync --all-groups --frozen
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver
```

Run the complete verification suite:

```bash
uv run ruff check .
uv run ruff format --check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate --noinput
uv run python manage.py collectstatic --noinput
uv run pytest
uv run python manage.py spectacular --file /tmp/sportsmarkers-openapi.yaml --validate --fail-on-warn
# With production environment variables set:
uv run python manage.py check --settings=config.settings.production --deploy --fail-level WARNING
```

CI runs the suite against PostgreSQL 17. Tests cover registration/password rules,
case-insensitive email uniqueness, JWT login/refresh/logout, privilege protection,
section updates, cross-sport validation, all record ownership checks and CRUD,
publication/unpublication, public privacy, seed idempotency, and database health failure.

## Models and API

`accounts.User` owns one `athletes.AthleteProfile`, which owns one
`sports.AthleteSportProfile`, `education.Education`, and `portfolios.Portfolio`.
`Sport` has `Position` records; selected positions must match the athlete's primary
sport. `careers` contains achievements and numeric athletic results;
`media_library` contains highlight video URLs; `portfolios` contains social links.
All new models have migrations and admin registrations. Completion percentage is
a computed model property, so edits to related records cannot leave it stale.

All paths below are relative to `/api/v1/`. Private endpoints require
`Authorization: Bearer <access-token>`. Registration always creates an athlete;
roles, ownership, verification state, and calculated progress are not writable.
Account email is read-only after registration (email-change verification is outside
this MVP). Names and account phone numbers can be updated at `auth/me/`.
The onboarding phone number is a separate private athlete contact field.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `health/` | Database readiness; 503 with sanitized error on failure |
| POST | `auth/register/` | `email`, `full_name`, `password`, `confirm_password` |
| POST | `auth/token/` | Email/password login; access and refresh tokens |
| POST | `auth/token/refresh/` | `refresh`; returns rotated access and refresh pair |
| GET, PATCH, PUT | `auth/me/` | Current account |
| POST | `auth/logout/` | Blacklist current user's `refresh`; 204 |
| GET | `sports/`, `sports/{slug}/` | Catalog including positions |
| GET | `positions/`, `positions/{id}/` | Filter list with `?sport={sport_uuid}` |
| GET, PATCH, PUT | `athletes/me/` | Personal onboarding information |
| GET, PATCH, PUT | `athletes/me/sport/` | Primary sport, position UUIDs, jersey, `height_cm`, `weight_kg`, years played |
| GET, PATCH, PUT | `athletes/me/education/` | School, graduation year, GPA (0–4), major, NCAA ID |
| GET | `athletes/me/onboarding/` | Completed/missing sections, step, status, percentage |
| GET, PATCH, PUT | `portfolios/me/` | Own combined portfolio; edit slug, story, goals, recruiting status, `is_published` |
| GET | `portfolios/public/{slug}/` | Anonymous published-only combined portfolio |
| GET, POST | `portfolios/achievements/` | Own achievement records |
| GET, POST | `portfolios/results/` | Own results; optional `?sport={sport_uuid}` |
| GET, POST | `portfolios/social-links/` | Own social links; one per platform |
| GET, POST | `portfolios/highlights/` | Own highlight URLs |
| GET, PATCH, PUT, DELETE | `portfolios/{record-type}/{id}/` | Own record detail, update, deletion |

Lists use `{count, next, previous, results}` pagination (50 records/page).
DRF errors use `{"error":{"status":400,"details":{"field":["message"]}}}`;
authentication and permission errors instead contain a `detail` message inside
`details`. The OpenAPI schema documents the shared envelope. Registration and
login are throttled to 30 requests/minute/IP per worker; use ingress rate limits
for shared production protection. Token refresh rotation invalidates the previous
refresh token. Logout does not revoke an already issued access token; it expires
after 15 minutes. Refresh tokens expire after seven days. Clients should discard
both tokens after logout. Run `python manage.py flushexpiredtokens` periodically
(e.g. daily) to prune expired blacklist records.

### Onboarding and publishing rules

PATCH supports saving partial sections. Progress is calculated, never accepted
from clients. Sections are complete when these fields are present:

- Personal: past date of birth, city, state, gender.
- Sport: primary sport, at least one matching position, height, weight, years played
  (zero is valid).
- Education: school and graduation year.

`onboarding_step` is zero-based: 0 personal, 1 sport, 2 education, 3 complete.
The first missing section determines the next step. Status is `not_started` when
no sections are complete, `in_progress` when some are complete, and `completed`
when all three are complete. Other fields are optional.
Portfolio completion counts eight equally weighted checks: the three sections,
story plus goals, an achievement, a result, a social link, and a highlight.
Publishing requires all onboarding sections and a story; 100% portfolio completion
is not required. Set `is_published: false` to remove public access immediately.
Unpublished and nonexistent public slugs both return 404, even to the owner;
owners preview via `portfolios/me/`.

The combined response includes public athlete information, named sport and
positions, education, achievements, results, highlights, and social links.
Public responses deliberately omit account email, phone numbers, date of birth,
gender, GPA, and NCAA ID. Biography, story, goals, and links are public when
published; avoid putting private contact information in these free-text fields.
Private education and personal data remain available through onboarding endpoints.
URLs are stored only; the server does not fetch, upload, process, or embed media.

## Demonstration flow

`seed_demo` is idempotent, development-only, and preserves existing demo data and
passwords. It creates five sports, positions, and a fictional complete athlete.
Known development-only credentials:

- Email: `demo.athlete@example.com`
- Password: `Development-Demo-2026!`
- Public slug: `jordan-taylor-demo`

```bash
curl http://localhost:8000/api/v1/portfolios/public/jordan-taylor-demo/
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo.athlete@example.com","password":"Development-Demo-2026!"}'
```

Use the returned access token in Swagger's **Authorize** control. Read onboarding
summary (100%), read the combined portfolio (100%), edit the story, create an
achievement, then unpublish and confirm the public URL returns 404. Publish again
and verify the public response. The highlight is explicitly labeled as a sample
video, and the avatar is a placeholder; replace these with real athlete-owned URLs
when entering real data.

`seed_demo` refuses to run with `DEBUG=False`. Never enable debug or use these
credentials on a public production service. Production uses the separate
idempotent `python manage.py seed_sports` catalog command; create real users via
registration and populate their records through the authenticated API.

## Render deployment

The blueprint follows [Render's Django deployment workflow](https://render.com/docs/deploy-django).
`render.yaml` defines a paid Starter web service and a `basic-256mb` PostgreSQL
service (review charges in your account before applying).

1. Merge the feature PR into `main`, then in Render create a Blueprint from
   `SquareResults/sportsmarkers-backend`, selecting `main`.
2. Set `ALLOWED_HOSTS` to the API hostname (comma-separated if multiple; no scheme
   or wildcard). Render's `RENDER_EXTERNAL_HOSTNAME` is also added automatically.
   Set `CORS_ALLOWED_ORIGINS` to exact HTTPS frontend origins and
   `CSRF_TRUSTED_ORIGINS` to exact HTTPS admin/frontend origins. Separate origins
   with commas, without trailing slashes.
3. Render generates `DJANGO_SECRET_KEY` and supplies PostgreSQL `DATABASE_URL`.
   Required settings are `DJANGO_SETTINGS_MODULE=config.settings.production`
   and a random secret of at least 50 characters. Production rejects SQLite and
   wildcard hosts, disables debug, enables HTTPS redirects and secure cookies,
   and trusts Render's forwarded HTTPS header.
4. Build: `bash build.sh` installs frozen runtime dependencies and collects static
   files. Pre-deploy runs migrations and `seed_sports` once before new workers
   start. Startup uses Gunicorn bound to Render's `$PORT`; WhiteNoise serves
   compressed static assets. The HTTP health check is `/api/v1/health/` and is
   exempt from HTTPS redirection so it can check database readiness.
5. After deployment, use Render Shell to run
   `.venv/bin/python manage.py check --deploy --fail-level WARNING` and
   `.venv/bin/python manage.py createsuperuser`. Verify the HTTPS health check,
   Swagger, admin static assets, registration/login, and a real portfolio's
   publish/unpublish flow. Configure the frontend with the HTTPS API base URL.
6. Enable appropriate database backups in your Render account. Existing databases
   with case-insensitive duplicate emails require manual reconciliation before
   the email-uniqueness migration; it aborts rather than deleting accounts.

Do not commit actual credentials or `.env`. OAuth, OTP/email delivery, password
reset, 2FA, payments, recruiter features, analytics, direct media upload, and video
processing are outside this MVP. The Figma reference could not be inspected because
the connected account reached its MCP call limit; API fields follow the locked MVP
requirements.
