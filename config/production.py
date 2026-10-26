from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

if (
    not os.getenv("SECRET_KEY")
    or len(SECRET_KEY) < 50
    or SECRET_KEY.startswith(("replace-", "development-", "django-insecure-"))
):
    raise ImproperlyConfigured("Production requires a SECRET_KEY of at least 50 characters")
configured_hosts = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "").split(",") if host.strip()]
render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_hostname:
    configured_hosts.append(render_hostname)
ALLOWED_HOSTS = list(dict.fromkeys(configured_hosts))
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Production requires explicit ALLOWED_HOSTS")
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured("Production requires a PostgreSQL DATABASE_URL")
DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
# Render terminates TLS at its trusted edge and forwards the original scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
render_url = os.getenv("RENDER_EXTERNAL_URL", "").strip()
if render_url:
    parsed_render_url = urlsplit(render_url)
    if parsed_render_url.scheme == "https" and parsed_render_url.netloc in ALLOWED_HOSTS:
        CSRF_TRUSTED_ORIGINS.append(f"https://{parsed_render_url.netloc}")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
