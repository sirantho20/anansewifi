"""Lightweight end-to-end smoke: URLConf + DB-backed views without mocks."""

import pytest
from django.test import Client
from rest_framework.test import APIClient

from tests.factories import PlanFactory


@pytest.mark.django_db
def test_healthz_ok():
    client = Client()
    response = client.get("/healthz/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_public_plans_list_after_seed_plan():
    PlanFactory()
    client = APIClient()
    response = client.get("/api/plans/")
    assert response.status_code == 200
    assert response.data["count"] >= 1
    first = response.data["results"][0]
    assert "id" in first
    assert "name" in first
    assert "code" not in first
