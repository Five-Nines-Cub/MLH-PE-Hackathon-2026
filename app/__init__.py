from dotenv import load_dotenv
from flask import Flask, jsonify

from app.database import init_db
from app.routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.url_map.strict_slashes = False

    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee

    from app.database import db
    from app.models.user import User
    from app.models.url import Url
    from app.models.event import Event

    with db.connection_context():
        db.create_tables([User, Url, Event], safe=True)

    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    return app
