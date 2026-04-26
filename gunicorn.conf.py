"""Gunicorn config; LOG_NAMESPACE prefixes access lines (set per service in docker-compose)."""
import os

log_namespace = os.environ.get("LOG_NAMESPACE", "base.django")
bind = "0.0.0.0:8000"
accesslog = "-"
errorlog = "-"
access_log_format = (
    f'{log_namespace} %(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" %(a)s %(D)s'
)
