import os

from flask import current_app
from playhouse.pool import PooledPostgresqlDatabase
from peewee import DatabaseProxy, Model
import redis
import json

cache = None

db = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = db


def init_db(app):
    database = PooledPostgresqlDatabase(
        os.environ.get("DATABASE_NAME", "hackathon_db"),
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", 5432)),
        user=os.environ.get("DATABASE_USER", "postgres"),
        password=os.environ.get("DATABASE_PASSWORD", "postgres"),
        max_connections=32,
        stale_timeout=300,
    )
    db.initialize(database)

    # initialize Redis cache client
    global cache
    if os.environ.get("SKIP_DB_INIT"):
        return
    
    try:
        redis_host = os.environ.get("REDIS_HOST", "redis")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        redis_db = int(os.environ.get("REDIS_DB", 0))
        cache = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True, socket_connect_timeout=5, socket_timeout=10)
        # smoke test (non-raising): ping
        try:
            cache.ping()
            app.logger.info("Connected to Redis cache")
        except Exception:
            app.logger.info("Redis ping failed; continuing without cache")
    except Exception:
        cache = None

    @app.before_request
    def _db_connect():
        if not os.environ.get("SKIP_DB_INIT"):
            from flask import request
            db.connect(reuse_if_open=True)
            if request.path != "/health":
                current_app.logger.info("Database connected")

    @app.teardown_appcontext
    def _db_close(exc):
        if not os.environ.get("SKIP_DB_INIT") and not db.is_closed():
            from flask import request
            if request.path != "/health":
                current_app.logger.info("Database closed")
            db.close()

