from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from ..services import (
    create_application as db_create_application,
    delete_application as db_delete_application,
    list_applications as db_list_applications,
    update_application as db_update_application,
    update_application_favorite,
    validate_application_payload,
    validate_favorite_payload,
)
from .shared import login_required, require_user_id


applications_bp = Blueprint("applications", __name__, url_prefix="/api/applications")


@applications_bp.get("")
@login_required
def list_applications() -> Response:
    favorite_only = request.args.get("favorite") == "true"
    return jsonify(db_list_applications(require_user_id(), favorite_only=favorite_only))


@applications_bp.post("")
@login_required
def create_application() -> tuple[Response, int]:
    payload = validate_application_payload(request.get_json(silent=True) or {})
    return jsonify(db_create_application(require_user_id(), payload)), 201


@applications_bp.put("/<int:application_id>")
@login_required
def update_application(application_id: int) -> Response | tuple[Response, int]:
    payload = validate_application_payload(request.get_json(silent=True) or {})
    application = db_update_application(require_user_id(), application_id, payload)
    if application is None:
        return jsonify({"error": "Application not found"}), 404
    return jsonify(application)


@applications_bp.patch("/<int:application_id>/favorite")
@login_required
def update_favorite(application_id: int) -> Response | tuple[Response, int]:
    payload = validate_favorite_payload(request.get_json(silent=True) or {})
    application = update_application_favorite(require_user_id(), application_id, payload.favorite)
    if application is None:
        return jsonify({"error": "Application not found"}), 404
    return jsonify(application)


@applications_bp.delete("/<int:application_id>")
@login_required
def delete_application(application_id: int) -> tuple[str, int] | tuple[Response, int]:
    if not db_delete_application(require_user_id(), application_id):
        return jsonify({"error": "Application not found"}), 404
    return ("", 204)
