from __future__ import annotations

from flask import Blueprint, Response, jsonify, request, session

from ..services import authenticate_user, create_user, get_user_by_id, validate_auth_payload
from .shared import current_user_id


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register() -> tuple[Response, int]:
    payload = validate_auth_payload(request.get_json(silent=True) or {})
    user = create_user(payload)
    session["user_id"] = user["id"]
    return jsonify({"user": user}), 201


@auth_bp.post("/login")
def login() -> Response | tuple[Response, int]:
    payload = validate_auth_payload(request.get_json(silent=True) or {})
    user = authenticate_user(payload)
    if user is None:
        return jsonify({"error": "Invalid email or password"}), 401
    session["user_id"] = user["id"]
    return jsonify({"user": user})


@auth_bp.post("/logout")
def logout() -> tuple[str, int]:
    session.clear()
    return ("", 204)


@auth_bp.get("/me")
def me() -> Response | tuple[Response, int]:
    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401
    user = get_user_by_id(user_id)
    if user is None:
        session.clear()
        return jsonify({"error": "Authentication required"}), 401
    return jsonify({"user": user})
