from flask import Blueprint, jsonify, current_app
import json
import os

from app.models.event import Event
from app.database import cache

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/", methods=["GET"])
def list_events():
    events = Event.select().order_by(Event.id)
    data = [e.to_dict() for e in events]

    return jsonify(data), 200
