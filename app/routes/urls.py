import json
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from peewee import IntegrityError

from app.models.event import Event
from app.models.url import Url, generate_short_code
from app.models.user import User

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
        return jsonify({"error": {"original_url": "original_url is required"}}), 422

    user_id = data.get("user_id")
    if user_id is None:
        return jsonify({"error": {"user_id": "user_id is required"}}), 422

    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
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

    return jsonify(url.to_dict()), 201


@urls_bp.route("/", methods=["GET"])
def list_urls():
    query = Url.select().order_by(Url.id)

    user_id = request.args.get("user_id", type=int)
    if user_id is not None:
        query = query.where(Url.user == user_id)

    return jsonify([u.to_dict() for u in query]), 200


@urls_bp.route("/<short_code>/redirect", methods=["GET"])
def redirect_url(short_code):
    try:
        url = Url.get(Url.short_code == short_code)
    except Url.DoesNotExist:
        return jsonify({"error": "Short code not found"}), 404

    if not url.is_active:
        return jsonify({"error": "URL is inactive"}), 410

    from flask import redirect as flask_redirect
    return flask_redirect(url.original_url, code=302)


@urls_bp.route("/<int:url_id>", methods=["GET"])
def get_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404
    return jsonify(url.to_dict()), 200


@urls_bp.route("/<int:url_id>", methods=["PUT"])
def update_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

    data = request.get_json(silent=True) or {}

    if "title" in data:
        url.title = data["title"]
    if "is_active" in data:
        url.is_active = data["is_active"]

    url.updated_at = datetime.now(timezone.utc)
    url.save()

    return jsonify(url.to_dict()), 200
