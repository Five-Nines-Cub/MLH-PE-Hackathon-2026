from flask import current_app
import json
import os
from app import database as db_module



def _cache_get(key: str) -> dict | None:
    """Return a cached dict by key, or None on miss or error."""
    try:
        if db_module.cache is not None:
            value = db_module.cache.get(key)
            if value:
                return value
    except Exception as e:
        current_app.logger.exception("Exception: %s", e)
    return None


def _cache_set(key: str, data: dict) -> None:
    """Store a dict in the cache. Silently ignores errors."""
    try:
        if db_module.cache is not None:
            db_module.cache.setex(key, int(os.environ.get("REDIS_TTL", 60)), data)
    except Exception as e:
        current_app.logger.exception("Exception: %s", e)



def _cache_delete(key: str) -> None:
    """Remove a key from the cache. Silently ignores errors."""
    try:
        if db_module.cache is not None:
            db_module.cache.delete(key)
    except Exception:
        pass
