import logging
import os


class LogNamespaceFilter(logging.Filter):
    """Injects ``record.log_namespace`` from ``LOG_NAMESPACE`` for formatters."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.log_namespace = os.environ.get("LOG_NAMESPACE", "base.django")
        return True
