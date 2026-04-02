"""Flask web interface for bastion-compat."""

from __future__ import annotations

import os
import time
from collections import defaultdict

from flask import Flask, jsonify, render_template, request

from .checker import check_compatibility, find_compatible_devices
from .database import DeviceDB

_rate_log: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 10
_RATE_WINDOW = 60


def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    _rate_log[ip] = [t for t in _rate_log[ip] if now - t < _RATE_WINDOW]
    if len(_rate_log[ip]) >= _RATE_LIMIT:
        return True
    _rate_log[ip].append(now)
    return False


def create_app() -> Flask:
    app = Flask(__name__)
    is_hosted = os.environ.get("BASTION_HOSTED", "").lower() in ("1", "true", "yes")
    db = DeviceDB()

    @app.route("/")
    def index():
        return render_template("index.html", hosted=is_hosted)

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/api/devices")
    def api_devices():
        return jsonify(db.export_all())

    @app.route("/api/check", methods=["POST"])
    def api_check():
        if is_hosted and _is_rate_limited(request.remote_addr or "unknown"):
            return jsonify({"error": "Too many requests. Please wait a minute."}), 429

        data = request.get_json(silent=True) or {}
        id_a = data.get("device_a", "").strip()
        id_b = data.get("device_b", "").strip()

        if not id_a or not id_b:
            return jsonify({"error": "Both device_a and device_b are required."}), 400
        if id_a == id_b:
            return jsonify({"error": "Please select two different devices."}), 400

        result = check_compatibility(id_a, id_b, db)
        return jsonify({
            "verdict": result.verdict.value,
            "explanation": result.explanation,
            "requirements": result.requirements,
            "limitations": result.limitations,
            "alternatives": result.alternatives,
            "device_a": _device_summary(db.get(id_a)),
            "device_b": _device_summary(db.get(id_b)),
        })

    @app.route("/api/compatible/<device_id>")
    def api_compatible(device_id: str):
        device = db.get(device_id)
        if device is None:
            return jsonify({"error": "Device not found."}), 404

        results = find_compatible_devices(device_id, db)
        return jsonify([
            {
                "device_id": did,
                "display_name": db.get(did).display_name if db.get(did) else did,
                "device_type": db.get(did).device_type if db.get(did) else "",
                "verdict": compat.verdict.value,
                "explanation": compat.explanation,
            }
            for did, compat in results
        ])

    return app


def _device_summary(device) -> dict | None:
    if device is None:
        return None
    return {
        "id": device.id,
        "display_name": device.display_name,
        "device_type": device.device_type,
    }
