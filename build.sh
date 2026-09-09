#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail
uv sync --frozen --no-dev
.venv/bin/python manage.py collectstatic --noinput
