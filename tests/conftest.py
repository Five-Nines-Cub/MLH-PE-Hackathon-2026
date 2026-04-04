import os

import pytest

os.environ.setdefault("DATABASE_NAME", "hackathon_test_db")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_PORT", "5433")
os.environ.setdefault("DATABASE_USER", "postgres")
os.environ.setdefault("DATABASE_PASSWORD", "postgres")

from app.database import db  # noqa: E402
from app.models.event import Event  # noqa: E402
from app.models.url import Url  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest.fixture
def client():
    from app import create_app

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with db.connection_context():
        db.drop_tables([Event, Url, User], safe=True)
        db.create_tables([User, Url, Event], safe=True)

    with flask_app.test_client() as c:
        yield c

    with db.connection_context():
        db.drop_tables([Event, Url, User], safe=True)
