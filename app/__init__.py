import os

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
    from app.logging import JSONFormatter
    import sys
    
    # Configure logger
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    app.logger.handlers = []
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False

    #initalize database
    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee

    from app.database import db
    from app.models.user import User
    from app.models.url import Url
    from app.models.event import Event

    if not os.environ.get("SKIP_DB_INIT"):
        with db.connection_context():
            db.create_tables([User, Url, Event], safe=True)


    register_routes(app)
    app.logger.info("Registered routes")


    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error("Internal server error: %s", e)
        return jsonify({"error": "Internal server error"}), 500

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    from app.models.url import Url

    @app.route("/<short_code>")
    def redirect_short_url(short_code):
        from app.models.event import Event
        import json as _json
        
        url = None
  
        cache_key = f"short_code:{short_code}"
        cached_url = _cache_get(cache_key)
        if cached_url:
            return redirect(cached_url, code=301)

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

        app.logger.info("Caching %s", cache_key)
        _cache_set(cache_key, url.original_url)
        return redirect(url.original_url, code=301)

    app.logger.info("App finished initializing")
    return app
