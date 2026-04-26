"""Django settings for the Ananse WiFi platform."""
from pathlib import Path
import os
from datetime import timedelta

import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

_csrf_trusted = os.getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:18080,http://localhost:18080,"
    "http://127.0.0.1:8080,http://localhost:8080",
)
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_trusted.split(",") if o.strip()]

# Reverse proxy (Coolify, Traefik, etc.): trust X-Forwarded-* from the proxy
if os.getenv("DJANGO_BEHIND_PROXY", "0") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    "django_daisy",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "rest_framework",
    "django_filters",
    "core",
    "accounts",
    "customers",
    "plans",
    "vouchers",
    "payments",
    "sessions",
    "radius_integration",
    "portal",
    "network",
    "audit",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ananseWifi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "ananseWifi.wsgi.application"

DJANGO_USE_SQLITE = os.getenv("DJANGO_USE_SQLITE", "0") == "1"
if DJANGO_USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
elif os.getenv("DATABASE_URL"):
    _conn_max_age = int(os.getenv("DATABASE_CONN_MAX_AGE", "0"))
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ["DATABASE_URL"],
            conn_max_age=_conn_max_age,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "ananse_wifi"),
            "USER": os.getenv("POSTGRES_USER", "ananse"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "ananse"),
            "HOST": os.getenv("POSTGRES_HOST", "db"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")

USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "0") == "1"
CELERY_BEAT_SCHEDULE = {
    "sync-radacct-records": {
        "task": "radius_integration.tasks.sync_radacct_task",
        "schedule": timedelta(seconds=int(os.getenv("RADIUS_ACCT_SYNC_INTERVAL_SECONDS", "30"))),
    },
}

_log_ns = os.getenv("LOG_NAMESPACE", "base.django")
CELERY_WORKER_LOG_FORMAT = (
    f"[{_log_ns}] %(levelname)s/%(processName)s %(message)s"
)
CELERY_WORKER_TASK_LOG_FORMAT = (
    f"[{_log_ns}] %(task_name)s[%(task_id)s]: %(message)s"
)

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "log_namespace": {
            "()": "core.log_filters.LogNamespaceFilter",
        },
    },
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s [%(log_namespace)s] %(name)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
            "filters": ["log_namespace"],
        }
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
}

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_BASE_URL = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")
PAYSTACK_CALLBACK_URL = os.getenv(
    "PAYSTACK_CALLBACK_URL", "http://localhost:18080/portal/purchase/callback/"
)
PAYMENT_CURRENCY = os.getenv("PAYMENT_CURRENCY", "GHS")

HUBTEL_CLIENT_ID = os.getenv("HUBTEL_CLIENT_ID", "")
HUBTEL_CLIENT_SECRET = os.getenv("HUBTEL_CLIENT_SECRET", "")
HUBTEL_SENDER_ID = os.getenv("HUBTEL_SENDER_ID", "AnanseWiFi")
HUBTEL_BASE_URL = os.getenv("HUBTEL_BASE_URL", "https://smsc.hubtel.com")
HUBTEL_SMS_SEND_PATH = os.getenv("HUBTEL_SMS_SEND_PATH", "/v1/messages/send")
HUBTEL_TIMEOUT_SECONDS = int(os.getenv("HUBTEL_TIMEOUT_SECONDS", "20"))

RADIUS_ACCOUNTING_INGEST_TOKEN = os.getenv("RADIUS_ACCOUNTING_INGEST_TOKEN", "")

DAISY_SETTINGS = {
    "SITE_TITLE": "Ananse WiFi",
    "SITE_HEADER": "Ananse WiFi administration",
    "INDEX_TITLE": "Site administration",
}
