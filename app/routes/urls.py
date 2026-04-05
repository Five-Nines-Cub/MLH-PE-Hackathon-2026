import json
import os
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, current_app
from peewee import IntegrityError


from app.models.event import Event
from app.models.url import Url, generate_short_code
from app.models.user import User
from app.cache import _cache_get, _cache_delete, _cache_set

urls_bp = Blueprint("urls", __name__, url_prefix="/urls")


def _make_short_code():
    for _ in range(10):
        code = generate_short_code()
        if not Url.select().where(Url.short_code == code).exists():
            return code
    raise RuntimeError("Failed to generate unique short code")

@urls_bp.route("/", methods=["POST"])
def create_url():
    data = request.get_json(silent=True) or {}

    if "original_url" not in data:
        current_app.logger.warning("Create URL missing original_url")
        return jsonify({"error": {"original_url": "original_url is required"}}), 422

    user_id = data.get("user_id")
    if user_id is None:
        current_app.logger.warning("Create URL missing user_id")
        return jsonify({"error": {"user_id": "user_id is required"}}), 422

    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        current_app.logger.warning("Create URL user not found: %s", user_id)
        return jsonify({"error": "User not found"}), 404

    try:
        short_code = _make_short_code()
    except RuntimeError:
        return jsonify({"error": "Could not generate unique short code"}), 500
    now = datetime.now(timezone.utc)

    url = Url.create(
        user=user,
        short_code=short_code,
        original_url=data["original_url"],
        title=data.get("title"),
        is_active=data.get("is_active", True),
        created_at=now,
        updated_at=now,
    )

    Event.create(
        url=url,
        user=user,
        event_type="created",
        timestamp=now,
        details=json.dumps({"short_code": short_code, "original_url": data["original_url"]}),
    )

    current_app.logger.info("Created URL id=%s short_code=%s user_id=%s", url.id, short_code, user_id)
    return jsonify(url.to_dict()), 201


@urls_bp.route("/", methods=["GET"])
def list_urls():
    query = Url.select().order_by(Url.id)

    body = request.get_json(silent=True) or {}

    user_id = request.args.get("user_id", type=int) or body.get("user_id")
    if user_id is not None:
        query = query.where(Url.user == user_id)

    is_active_param = request.args.get("is_active") or body.get("is_active")
    if is_active_param is not None:
        if isinstance(is_active_param, bool):
            query = query.where(Url.is_active == is_active_param)
        else:
            query = query.where(Url.is_active == (str(is_active_param).lower() == "true"))

    return jsonify([u.to_dict() for u in query]), 200



@urls_bp.route("/<int:url_id>", methods=["GET"])
def get_url(url_id):
    cache_key = f"url:{url_id}"
    cached = _cache_get(cache_key)

    if cached is not None:
        current_app.logger.info("Cache hit for %s", cache_key)
        return jsonify(cached), 200

    #cache miss
    try:
        url = Url.get_by_id(url_id)
    except Url.DoesNotExist:
        current_app.logger.warning("URL not found: %s", url_id)
        return jsonify({"error": "URL not found"}), 404

    data = url.to_dict()

    #add to cache
    current_app.logger.info("Caching %s", cache_key)
    _cache_set(cache_key, data)

    return jsonify(data), 200


@urls_bp.route("/<int:url_id>", methods=["DELETE"])
def delete_url(url_id):
    try:
        url = Url.get_by_id(url_id)
        _cache_delete(f"url:{url_id}")
        _cache_delete(f"short_code:{url.short_code}")
        Event.delete().where(Event.url == url).execute()
        url.delete_instance()
    except Url.DoesNotExist:
        current_app.logger.info("Cannot delete %s, url does not exist", url_id)
    return "", 204


@urls_bp.route("/<int:url_id>", methods=["PUT"])
def update_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except Url.DoesNotExist:
        current_app.logger.warning("Update URL not found: %s", url_id)
        return jsonify({"error": "URL not found"}), 404

    data = request.get_json(silent=True) or {}

    if "title" in data:
        url.title = data["title"]
    if "is_active" in data:
        url.is_active = data["is_active"]

    url.updated_at = datetime.now(timezone.utc)
    url.save()

    _cache_delete(f"url:{url_id}")
    _cache_delete(f"short_code:{url.short_code}")

    current_app.logger.info("Updated URL id=%s", url_id)
    return jsonify(url.to_dict()), 200
