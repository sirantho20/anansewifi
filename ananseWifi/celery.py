import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ananseWifi.settings")

app = Celery("ananseWifi")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

_log_ns = os.environ.get("LOG_NAMESPACE", "base.django")
app.conf.beat_log_format = f"[{_log_ns}] %(levelname)s %(message)s"
