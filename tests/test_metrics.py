import os
import sys
import types
import pytest

os.environ.setdefault("SKIP_DB_INIT", "1")
pytestmark = pytest.mark.unit

from app import create_app


def test_metrics_with_psutil(monkeypatch):
    fake = types.SimpleNamespace()
    fake.cpu_percent = lambda interval: 12.3

    class VM:
        percent = 45.6
        used = 123
        total = 456

    fake.virtual_memory = lambda: VM()
    monkeypatch.setitem(sys.modules, "psutil", fake)

    app = create_app()
    with app.test_client() as c:
        res = c.get("/metrics/")
    assert res.status_code == 200
    j = res.get_json()
    assert "cpu_percent" in j and "ram_percent" in j


def test_metrics_without_psutil(monkeypatch):
    # Simulate missing psutil by inserting None into sys.modules
    monkeypatch.setitem(sys.modules, "psutil", None)

    app = create_app()
    with app.test_client() as c:
        res = c.get("/metrics/")
    assert res.status_code == 500
    assert res.get_json().get("error")
