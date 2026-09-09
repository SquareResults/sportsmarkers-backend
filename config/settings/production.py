import os

from .base import *  # noqa: F403

if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("unsafe-"):  # noqa: F405
    raise RuntimeError("Set a random DJANGO_SECRET_KEY of at least 50 characters in production")
if not os.getenv("DATABASE_URL", "").startswith(("postgres://", "postgresql://")):
    raise RuntimeError("Production requires a PostgreSQL DATABASE_URL")
if os.getenv("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])  # noqa: F405
if "*" in ALLOWED_HOSTS:  # noqa: F405
    raise RuntimeError("Production ALLOWED_HOSTS must not contain a wildcard")
CSRF_TRUSTED_ORIGINS = [
    value for value in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if value
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r"^api/v1/health/$"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
