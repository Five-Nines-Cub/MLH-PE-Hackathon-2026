import pytest

from app.database import db
from app.models.event import Event
from app.models.url import Url
from app.models.user import User


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
