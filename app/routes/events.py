from flask import Blueprint, jsonify

from app.models.event import Event

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/", methods=["GET"])
def list_events():
    events = Event.select().order_by(Event.id)
    return jsonify([e.to_dict() for e in events]), 200
