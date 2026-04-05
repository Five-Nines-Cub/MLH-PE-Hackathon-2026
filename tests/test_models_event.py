import os
import json
import pytest
from datetime import datetime, timezone

os.environ.setdefault("SKIP_DB_INIT", "1")
pytestmark = pytest.mark.unit

from app.models.event import Event


def test_event_to_dict_full():
    ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
    details = {"referrer": "https://google.com"}
    ev = Event(
        id=1,
        url_id=2,
        user_id=3,
        event_type="click",
        timestamp=ts,
        details=json.dumps(details),
    )
    d = ev.to_dict()
    assert d["id"] == 1
    assert d["url_id"] == 2
    assert d["user_id"] == 3
    assert d["event_type"] == "click"
    assert d["timestamp"] == ts.isoformat()
    assert d["details"] == details


def test_event_to_dict_nulls():
    ev = Event(id=5, url_id=7, user_id=None, event_type="view", timestamp=None, details=None)
    d = ev.to_dict()
    assert d["id"] == 5
    assert d["url_id"] == 7
    assert d["user_id"] is None
    assert d["timestamp"] is None
    assert d["details"] == {}
