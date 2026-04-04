import json
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app.models.event import Event
from app.models.url import Url
from app.models.user import User

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/", methods=["GET"])
def list_events():
    query = Event.select().order_by(Event.id)
    body = request.get_json(silent=True) or {}

    url_id = request.args.get("url_id", type=int) or body.get("url_id")
    if url_id is not None:
        query = query.where(Event.url == url_id)

    event_type = request.args.get("event_type") or body.get("event_type")
    if event_type is not None:
        query = query.where(Event.event_type == event_type)

    user_id = request.args.get("user_id", type=int) or body.get("user_id")
    if user_id is not None:
        query = query.where(Event.user == user_id)

    return jsonify([e.to_dict() for e in query]), 200


@events_bp.route("/", methods=["POST"])
def create_event():
    data = request.get_json(silent=True) or {}

    if "url_id" not in data:
        return jsonify({"error": {"url_id": "url_id is required"}}), 422
    if "event_type" not in data:
        return jsonify({"error": {"event_type": "event_type is required"}}), 422

    details = data.get("details")
    if details is not None and not isinstance(details, dict):
        return jsonify({"error": {"details": "details must be a JSON object"}}), 422

    try:
        url = Url.get_by_id(data["url_id"])
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

    user = None
    if "user_id" in data:
        try:
            user = User.get_by_id(data["user_id"])
        except User.DoesNotExist:
            return jsonify({"error": "User not found"}), 404

    event = Event.create(
        url=url,
        user=user,
        event_type=data["event_type"],
        timestamp=datetime.now(timezone.utc),
        details=json.dumps(details) if details is not None else None,
    )

    return jsonify(event.to_dict()), 201
