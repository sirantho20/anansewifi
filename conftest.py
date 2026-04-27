"""
Pytest: set env before Django settings import (pytest-django).

Ensures Celery does not need a real Redis in Docker/CI for tests.
Test DB (SQLite) is set in ananseWifi.settings when `pytest` is in sys.modules;
see also Makefile `test` and PYTEST_USE_POSTGRES in settings.
"""
import os

os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "1")
