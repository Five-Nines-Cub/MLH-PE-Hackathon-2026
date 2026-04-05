from flask import Blueprint, jsonify
import os

metrics_bp = Blueprint("metrics", __name__, url_prefix="/metrics")


@metrics_bp.route("/", methods=["GET"])
def metrics():
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        return jsonify(
            cpu_percent=cpu,
            ram_percent=mem.percent,
            ram_used=mem.used,
            ram_total=mem.total,
        )
    except Exception:
        return jsonify(error="psutil not available"), 500
