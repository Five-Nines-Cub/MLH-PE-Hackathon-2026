import csv
import io

from flask import Blueprint, jsonify, request
from peewee import chunked, IntegrityError

from app.database import db
from app.models.user import User

users_bp = Blueprint("users", __name__, url_prefix="/users")


def _validate_user_fields(data):
    errors = {}
    for field in ("username", "email"):
        if field in data:
            val = data[field]
            if not isinstance(val, str) or isinstance(val, bool):
                errors[field] = f"{field} must be a string"
    return errors


@users_bp.route("/bulk", methods=["POST"])
def bulk_import():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    content = file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    if not rows:
        return jsonify({"imported": 0}), 200

    with db.atomic():
        for batch in chunked(rows, 100):
            User.insert_many(batch).execute()

    # Reset sequence so future auto-inserts don't conflict
    db.execute_sql(
        "SELECT setval(pg_get_serial_sequence('users', 'id'), "
        "COALESCE((SELECT MAX(id) FROM users), 1))"
    )

    return jsonify({"imported": len(rows)}), 201


@users_bp.route("/", methods=["GET"])
def list_users():
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)

    query = User.select().order_by(User.id)

    if page and per_page:
        query = query.paginate(page, per_page)

    return jsonify([u.to_dict() for u in query]), 200


@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


@users_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json(silent=True) or {}

    errors = {}
    for field in ("username", "email"):
        if field not in data:
            errors[field] = f"{field} is required"
        elif not isinstance(data[field], str) or isinstance(data[field], bool):
            errors[field] = f"{field} must be a string"

    if errors:
        return jsonify({"error": errors}), 422

    try:
        user = User.create(username=data["username"], email=data["email"])
    except IntegrityError:
        return jsonify({"error": "username or email already exists"}), 409

    return jsonify(user.to_dict()), 201


@users_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    errors = _validate_user_fields(data)
    if errors:
        return jsonify({"error": errors}), 422

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]

    try:
        user.save()
    except IntegrityError:
        return jsonify({"error": "username or email already exists"}), 409

    return jsonify(user.to_dict()), 200
