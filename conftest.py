"""
Pytest: set env before Django settings import (pytest-django).

Ensures Celery does not need a real Redis in Docker/CI for tests.
"""
import os

os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "1")
