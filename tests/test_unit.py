import pytest
import string
from datetime import datetime, timezone

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


# --- redirect ---

def test_redirect_url_active(monkeypatch):
    from app import create_app
    from app.models.url import Url

    url = Url(short_code="abc123", original_url="https://example.com", is_active=True)
    monkeypatch.setattr(Url, "get", staticmethod(lambda *_: url))

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
