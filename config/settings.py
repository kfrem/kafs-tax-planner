"""
Django settings for the UK Tax Planner project.

Architecture reference: Tax_Planner_Architecture_and_Stack_Recommendation.docx
(Section 3: Django / PostgreSQL / server-rendered monolith).
"""

import os
import sys
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

if sys.platform == "win32":
    # WeasyPrint needs GTK's native libs (Pango/cairo/gobject) on PATH.
    # Installed via: winget install tschoonj.GTKForWindows
    _gtk_bin = r"C:\Program Files\GTK3-Runtime Win64\bin"
    if os.path.isdir(_gtk_bin) and _gtk_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _gtk_bin + os.pathsep + os.environ.get("PATH", "")

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Origins trusted for CSRF-protected POSTs (login, forms). Django requires the
# scheme, e.g. https://app.example.com. Needed once the app is served over a
# public HTTPS hostname behind a proxy (Railway/Render/Fly).
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Railway (and similar PaaS) expose the app's public hostname as an env var.
# Auto-trust it so a deploy works without hand-listing the generated domain in
# two places. Harmless elsewhere (the var is simply absent).
_railway_domain = env("RAILWAY_PUBLIC_DOMAIN", default="")
if _railway_domain:
    for _host in (_railway_domain, ".railway.app"):  # exact domain + healthcheck subdomain
        if _host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(_host)
    _railway_origin = f"https://{_railway_domain}"
    if _railway_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_railway_origin)

# Render exposes the service's public hostname the same way.
_render_host = env("RENDER_EXTERNAL_HOSTNAME", default="")
if _render_host:
    if _render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_render_host)
    _render_origin = f"https://{_render_host}"
    if _render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_render_origin)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django_htmx",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "firms",
    "authority",
    "ruleengine",
    "clients",
    "advice",
    "reports",
    "monitoring",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Serves collected static files from the app process in the container
    # deployment (no separate web server needed at MVP scale).
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # MFA: attaches request.user.is_verified(); the enforcement middleware
    # below requires verification for any user with a confirmed device.
    "django_otp.middleware.OTPMiddleware",
    "firms.mfa.MfaEnforcementMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "firms.middleware.FirmRowLevelSecurityMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "monitoring.context_processors.open_alert_count",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

AUTH_USER_MODEL = "firms.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "firms:login"
LOGIN_REDIRECT_URL = "clients:client-list"
LOGOUT_REDIRECT_URL = "firms:login"

# --- Product-specific, non-negotiable settings (see architecture Section 11) ---
# Minimum retention for advice records, in years, per Section 6.3.
ADVICE_RECORD_MIN_RETENTION_YEARS = 6

SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 hour session per Section 7.2 session controls
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

if not DEBUG:
    # UK-region hosting with TLS 1.2+ in transit (Section 7.2) — these only
    # bite once a real deployment terminates TLS in front of the app.
    #
    # Railway/Render/Fly terminate TLS at their edge and forward plain HTTP to
    # the container with an X-Forwarded-Proto header. Without this, Django sees
    # "http", and SECURE_SSL_REDIRECT below redirects to https forever (loop).
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
