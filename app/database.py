import os

from peewee import DatabaseProxy, Model, PostgresqlDatabase
import redis
import json

cache = None

db = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = db


def init_db(app):
    database = PostgresqlDatabase(
        os.environ.get("DATABASE_NAME", "hackathon_db"),
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", 5432)),
        user=os.environ.get("DATABASE_USER", "postgres"),
        password=os.environ.get("DATABASE_PASSWORD", "postgres"),
    )
    db.initialize(database)

    # initialize Redis cache client
    global cache
    try:
        redis_host = os.environ.get("REDIS_HOST", "redis")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        redis_db = int(os.environ.get("REDIS_DB", 0))
        cache = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        # smoke test (non-raising): ping
        try:
            cache.ping()
            app.logger.debug("Connected to Redis cache")
        except Exception:
            app.logger.debug("Redis ping failed; continuing without cache")
    except Exception:
        cache = None

    @app.before_request
    def _db_connect():
        if not os.environ.get("SKIP_DB_INIT"):
            db.connect(reuse_if_open=True)

    @app.teardown_appcontext
    def _db_close(exc):
        if not os.environ.get("SKIP_DB_INIT") and not db.is_closed():
            db.close()
