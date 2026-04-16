"""Regression tests for LOG_NAMESPACE / Docker namespaced logging."""

import importlib.util
import logging
from pathlib import Path

import pytest

from core.log_filters import LogNamespaceFilter


def test_log_namespace_filter_injects_from_env(monkeypatch):
    monkeypatch.setenv("LOG_NAMESPACE", "base.test.filter")
    flt = LogNamespaceFilter()
    record = logging.LogRecord("m", logging.INFO, __file__, 99, "hello", (), None)
    assert flt.filter(record) is True
    assert record.log_namespace == "base.test.filter"


def test_log_namespace_filter_default_when_unset(monkeypatch):
    monkeypatch.delenv("LOG_NAMESPACE", raising=False)
    flt = LogNamespaceFilter()
    record = logging.LogRecord("m", logging.INFO, __file__, 99, "hello", (), None)
    assert flt.filter(record) is True
    assert record.log_namespace == "base.django"


def test_gunicorn_conf_access_log_format_prefix(monkeypatch):
    monkeypatch.setenv("LOG_NAMESPACE", "base.test.gunicorn")
    repo_root = Path(__file__).resolve().parent.parent
    conf_path = repo_root / "gunicorn.conf.py"
    spec = importlib.util.spec_from_file_location("gunicorn_conf_test", conf_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert mod.access_log_format.startswith("base.test.gunicorn ")
    assert mod.bind == "0.0.0.0:8000"


@pytest.mark.django_db
def test_django_log_line_contains_namespace(caplog, monkeypatch):
    monkeypatch.setenv("LOG_NAMESPACE", "base.test.django")
    log = logging.getLogger("test_log_namespace_probe")
    log.setLevel(logging.INFO)
    with caplog.at_level(logging.INFO, logger="test_log_namespace_probe"):
        log.info("namespaced-probe-message")
    assert "namespaced-probe-message" in caplog.text
    assert any(
        getattr(r, "log_namespace", None) == "base.test.django" for r in caplog.records
    )
