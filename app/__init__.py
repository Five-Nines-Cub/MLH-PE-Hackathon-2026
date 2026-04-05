from dotenv import load_dotenv
from flask import Flask, jsonify, redirect

from app.database import init_db
from app.routes import register_routes
from app.cache import _cache_get, _cache_set


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.url_map.strict_slashes = False

    import logging
    import sys
    
    # Send app logs to stdout so Docker picks them up
    if not app.debug:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO)

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

    from app.models.url import Url

    @app.route("/<short_code>")
    def redirect_short_url(short_code):
        cache_key = f"short_code:{short_code}"

        cached_url = _cache_get(cache_key)
        if cached_url:
            app.logger.info("Cache hit for %s", cache_key)
            return redirect(cached_url, code=301)

        try:
            url = Url.get(Url.short_code == short_code, Url.is_active == True)
        except Url.DoesNotExist:
            return jsonify({"error": "URL not found"}), 404

        app.logger.info("Caching %s", cache_key)
        _cache_set(cache_key, url.original_url)

        return redirect(url.original_url, code=301)

    return app
