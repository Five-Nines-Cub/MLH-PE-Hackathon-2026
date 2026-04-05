import os
import pytest
import string
from datetime import datetime, timezone

os.environ["SKIP_DB_INIT"] = "1"

pytestmark = pytest.mark.unit

from app.models.url import Url, generate_short_code
from app.models.user import User
from app.routes.users import _validate_user_fields


# --- generate_short_code ---

def test_short_code_default_length():
    assert len(generate_short_code()) == 6


def test_short_code_custom_length():
    assert len(generate_short_code(10)) == 10


def test_short_code_charset():
    allowed = set(string.ascii_letters + string.digits)
    for _ in range(50):
        assert all(c in allowed for c in generate_short_code())

# --- _validate_user_fields ---

def test_validate_user_fields_valid():
    assert _validate_user_fields({"username": "alice", "email": "alice@example.com"}) == {}


def test_validate_user_fields_int_username():
    errors = _validate_user_fields({"username": 123})
    assert "username" in errors


def test_validate_user_fields_bool_username():
    # bool is a subclass of int, not str — should be rejected
    errors = _validate_user_fields({"username": True})
    assert "username" in errors


def test_validate_user_fields_int_email():
    errors = _validate_user_fields({"email": 99})
    assert "email" in errors


def test_validate_user_fields_ignores_missing_fields():
    # only validates fields that are present
    assert _validate_user_fields({}) == {}


# --- User.to_dict ---

def test_user_to_dict():
    ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
    user = User(id=1, username="alice", email="alice@example.com", created_at=ts)
    d = user.to_dict()
    assert d["id"] == 1
    assert d["username"] == "alice"
    assert d["email"] == "alice@example.com"
    assert d["created_at"] == ts.isoformat()


def test_user_to_dict_null_timestamp():
    user = User(id=1, username="alice", email="alice@example.com", created_at=None)
    assert user.to_dict()["created_at"] is None


# --- delete_user ---

def test_delete_user_unit(monkeypatch):
    from unittest.mock import MagicMock
    from app import create_app
    from app.models.user import User

    mock_user = MagicMock()
    monkeypatch.setattr(User, "get_by_id", staticmethod(lambda *_: mock_user))

    app = create_app()
    with app.test_client() as c:
        res = c.delete("/users/1")
    assert res.status_code == 204
    mock_user.delete_instance.assert_called_once()


def test_delete_user_not_found_unit(monkeypatch):
    from app import create_app
    from app.models.user import User

    def raise_not_found(*_):
        raise User.DoesNotExist()
    monkeypatch.setattr(User, "get_by_id", staticmethod(raise_not_found))

    app = create_app()
    with app.test_client() as c:
        res = c.delete("/users/999")
    assert res.status_code == 204


# --- list_urls body filtering ---

def test_list_urls_body_user_id_unit(monkeypatch):
    from unittest.mock import MagicMock
    from app import create_app
    from app.models.url import Url

    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.__iter__ = MagicMock(return_value=iter([]))
    monkeypatch.setattr(Url, "select", staticmethod(lambda: mock_query))

    app = create_app()
    with app.test_client() as c:
        res = c.get("/urls", json={"user_id": 1})
    assert res.status_code == 200
    mock_query.where.assert_called()


def test_list_urls_body_is_active_unit(monkeypatch):
    from unittest.mock import MagicMock
    from app import create_app
    from app.models.url import Url

    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.__iter__ = MagicMock(return_value=iter([]))
    monkeypatch.setattr(Url, "select", staticmethod(lambda: mock_query))

    app = create_app()
    with app.test_client() as c:
        res = c.get("/urls", json={"is_active": "true"})
    assert res.status_code == 200
    mock_query.where.assert_called()


# --- list_events body filtering ---

def test_list_events_body_url_id_unit(monkeypatch):
    from unittest.mock import MagicMock
    from app import create_app
    from app.models.event import Event

    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.__iter__ = MagicMock(return_value=iter([]))
    monkeypatch.setattr(Event, "select", staticmethod(lambda: mock_query))

    app = create_app()
    with app.test_client() as c:
        res = c.get("/events", json={"url_id": 1})
    assert res.status_code == 200
    mock_query.where.assert_called()


def test_list_events_body_user_id_unit(monkeypatch):
    from unittest.mock import MagicMock
    from app import create_app
    from app.models.event import Event

    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.__iter__ = MagicMock(return_value=iter([]))
    monkeypatch.setattr(Event, "select", staticmethod(lambda: mock_query))

    app = create_app()
    with app.test_client() as c:
        res = c.get("/events", json={"user_id": 1})
    assert res.status_code == 200
    mock_query.where.assert_called()


def test_list_events_body_event_type_unit(monkeypatch):
    from unittest.mock import MagicMock
    from app import create_app
    from app.models.event import Event

    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.__iter__ = MagicMock(return_value=iter([]))
    monkeypatch.setattr(Event, "select", staticmethod(lambda: mock_query))

    app = create_app()
    with app.test_client() as c:
        res = c.get("/events", json={"event_type": "click"})
    assert res.status_code == 200
    mock_query.where.assert_called()


# --- create_event ---

def test_create_event_details_string_rejected_unit():
    from app import create_app
    app = create_app()
    with app.test_client() as c:
        res = c.post("/events", json={"url_id": 1, "event_type": "click", "details": "bad"})
    assert res.status_code == 422
    assert "details" in res.get_json()["error"]


def test_create_event_details_list_rejected_unit():
    from app import create_app
    app = create_app()
    with app.test_client() as c:
        res = c.post("/events", json={"url_id": 1, "event_type": "click", "details": [1, 2, 3]})
    assert res.status_code == 422
    assert "details" in res.get_json()["error"]


def test_create_event_missing_url_id_unit():
    from app import create_app
    app = create_app()
    with app.test_client() as c:
        res = c.post("/events", json={"event_type": "click"})
    assert res.status_code == 422
    assert "url_id" in res.get_json()["error"]


def test_create_event_missing_event_type_unit():
    from app import create_app
    app = create_app()
    with app.test_client() as c:
        res = c.post("/events", json={"url_id": 1})
    assert res.status_code == 422
    assert "event_type" in res.get_json()["error"]


def test_create_event_url_not_found_unit(monkeypatch):
    from app import create_app
    from app.models.url import Url

    def raise_not_found(*_):
        raise Url.DoesNotExist()
    monkeypatch.setattr(Url, "get_by_id", staticmethod(raise_not_found))

    app = create_app()
    with app.test_client() as c:
        res = c.post("/events", json={"url_id": 999, "event_type": "click"})
    assert res.status_code == 404


def test_create_event_valid_unit(monkeypatch):
    from unittest.mock import MagicMock
    from app import create_app
    from app.models.url import Url
    from app.models.user import User
    from app.models.event import Event

    mock_url = MagicMock()
    mock_user = MagicMock()
    mock_event = MagicMock()
    mock_event.to_dict.return_value = {
        "id": 1, "url_id": 1, "user_id": 1,
        "event_type": "click", "timestamp": "2026-01-01T00:00:00",
        "details": {"referrer": "https://google.com"},
    }
    monkeypatch.setattr(Url, "get_by_id", staticmethod(lambda *_: mock_url))
    monkeypatch.setattr(User, "get_by_id", staticmethod(lambda *_: mock_user))
    monkeypatch.setattr(Event, "create", staticmethod(lambda **_: mock_event))

    app = create_app()
    with app.test_client() as c:
        res = c.post("/events", json={
            "url_id": 1, "user_id": 1,
            "event_type": "click",
            "details": {"referrer": "https://google.com"},
        })
    assert res.status_code == 201
    assert res.get_json()["event_type"] == "click"


# --- delete_url ---

def test_delete_url_cascades_events_unit(monkeypatch):
    from unittest.mock import MagicMock
    from app import create_app
    from app.models.url import Url
    from app.models.event import Event

    mock_url = MagicMock()
    monkeypatch.setattr(Url, "get_by_id", staticmethod(lambda *_: mock_url))

    mock_delete_query = MagicMock()
    mock_delete_query.where.return_value = mock_delete_query
    monkeypatch.setattr(Event, "delete", staticmethod(lambda: mock_delete_query))

    app = create_app()
    with app.test_client() as c:
        res = c.delete("/urls/1")

    assert res.status_code == 204
    mock_delete_query.where.assert_called_once()
    mock_delete_query.execute.assert_called_once()
    mock_url.delete_instance.assert_called_once()


def test_delete_url_not_found_unit(monkeypatch):
    from app import create_app
    from app.models.url import Url

    def raise_not_found(*_):
        raise Url.DoesNotExist()
    monkeypatch.setattr(Url, "get_by_id", staticmethod(raise_not_found))

    app = create_app()
    with app.test_client() as c:
        res = c.delete("/urls/999")
    assert res.status_code == 204


# --- redirect ---

def test_redirect_url_active(monkeypatch):
    from unittest.mock import MagicMock
    from app import create_app
    from app.models.url import Url
    from app.models.event import Event

    url = Url(short_code="abc123", original_url="https://example.com", is_active=True)
    monkeypatch.setattr(Url, "get", staticmethod(lambda *_: url))
    monkeypatch.setattr(Event, "create", staticmethod(lambda **_: MagicMock()))

    app = create_app()
    with app.test_client() as c:
        res = c.get("/abc123")
    assert res.status_code == 301
    assert res.headers["Location"] == "https://example.com"


def test_redirect_url_inactive(monkeypatch):
    from app import create_app
    from app.models.url import Url

    def raise_not_found(*_):
        raise Url.DoesNotExist()
    monkeypatch.setattr(Url, "get", staticmethod(raise_not_found))

    app = create_app()
    with app.test_client() as c:
        res = c.get("/abc123")
    assert res.status_code == 404


def test_redirect_url_not_found(monkeypatch):
    from app import create_app
    from app.models.url import Url

    def raise_not_found(*_):
        raise Url.DoesNotExist()
    monkeypatch.setattr(Url, "get", staticmethod(raise_not_found))

    app = create_app()
    with app.test_client() as c:
        res = c.get("/XXXXXX")
    assert res.status_code == 404


# --- Url.to_dict ---

def test_url_to_dict():
    ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
    url = Url(
        id=1,
        user_id=42,
        short_code="abc123",
        original_url="https://example.com",
        title="Example",
        is_active=True,
        created_at=ts,
        updated_at=ts,
    )
    d = url.to_dict()
    assert d["id"] == 1
    assert d["user_id"] == 42
    assert d["short_code"] == "abc123"
    assert d["original_url"] == "https://example.com"
    assert d["title"] == "Example"
    assert d["is_active"] is True
    assert d["created_at"] == ts.isoformat()
    assert d["updated_at"] == ts.isoformat()
