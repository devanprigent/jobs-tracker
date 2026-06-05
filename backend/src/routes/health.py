from __future__ import annotations

from flask import Blueprint, Response, jsonify

from ..schemas import APPLICATION_STATES


health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health() -> Response:
    return jsonify({"ok": True, "states": APPLICATION_STATES})
