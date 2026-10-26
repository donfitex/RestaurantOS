from .base import *  # noqa: F403
from django.core.exceptions import ImproperlyConfigured
if not os.getenv("SECRET_KEY") or len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("Production requires a SECRET_KEY of at least 50 characters")
if not os.getenv("ALLOWED_HOSTS") or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Production requires explicit ALLOWED_HOSTS")
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured("Production requires a PostgreSQL DATABASE_URL")
DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if os.getenv("CSRF_TRUSTED_ORIGINS") else []
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
