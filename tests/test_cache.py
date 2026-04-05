import os
import pytest

os.environ.setdefault("SKIP_DB_INIT", "1")
pytestmark = pytest.mark.unit

from app import create_app
from app import database as db_module
from app.cache import _cache_get, _cache_set, _cache_delete


def test_cache_get_set_delete_monkeypatched(monkeypatch):
    app = create_app()
    class DummyCache:
        def __init__(self):
            self.store = {}

        def get(self, k):
            return self.store.get(k)

        def setex(self, k, ttl, v):
            self.store[k] = v

        def delete(self, k):
            self.store.pop(k, None)

    dummy = DummyCache()
    monkeypatch.setattr(db_module, "cache", dummy)

    with app.app_context():
        assert _cache_get("nope") is None
        _cache_set("k", "v")
        assert _cache_get("k") == "v"
        _cache_delete("k")
        assert _cache_get("k") is None


def test_cache_handles_exceptions(monkeypatch):
    app = create_app()

    class BadCache:
        def get(self, k):
            raise RuntimeError("fail")

        def setex(self, k, ttl, v):
            raise RuntimeError("fail")

        def delete(self, k):
            raise RuntimeError("fail")

    bad = BadCache()
    monkeypatch.setattr(db_module, "cache", bad)

    with app.app_context():
        # should not raise
        assert _cache_get("x") is None
        _cache_set("x", "y")
        _cache_delete("x")
