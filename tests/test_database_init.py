import os
import pytest

os.environ.setdefault("SKIP_DB_INIT", "1")
pytestmark = pytest.mark.unit

from app import create_app
from app import database as db_module


def test_init_db_skips_when_flag_set(monkeypatch):
    os.environ["SKIP_DB_INIT"] = "1"
    # create_app calls init_db during startup
    app = create_app()
    # when SKIP_DB_INIT is set, db_module.cache should remain as initialized default (None)
    assert getattr(db_module, "cache", None) is None
