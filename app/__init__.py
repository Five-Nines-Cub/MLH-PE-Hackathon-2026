from dotenv import load_dotenv
from flask import Flask, jsonify, redirect

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

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    from app.models.url import Url

    @app.route("/<short_code>")
    def redirect_short_url(short_code):
        from app.models.event import Event
        import json as _json
        try:
            url = Url.get(Url.short_code == short_code, Url.is_active == True)
        except Url.DoesNotExist:
            return jsonify({"error": "URL not found"}), 404

        Event.create(
            url=url,
            user=None,
            event_type="redirect",
            details=_json.dumps({"short_code": short_code}),
        )

        return redirect(url.original_url, code=301)

    return app
