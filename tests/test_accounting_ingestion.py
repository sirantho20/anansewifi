import pytest

from sessions.services import ingest_accounting_event


@pytest.mark.django_db
def test_accounting_ingestion_updates_session():
    payload = {
        "event_type": "interim",
        "username": "demo-user",
        "session_id": "sess-123",
        "input_octets": 1200,
        "output_octets": 3400,
        "duration_seconds": 90,
    }
    record = ingest_accounting_event(payload)

    assert record.linked_session is not None
    assert record.linked_session.total_octets == 4600
    assert record.linked_session.duration_seconds == 90
