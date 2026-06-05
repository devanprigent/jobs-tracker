from __future__ import annotations

import os

from flask import Flask, Response, jsonify, request
from pathlib import Path

from dotenv import load_dotenv
from .database import init_db
from .routes import applications_bp, auth_bp, companies_bp, health_bp, listings_bp

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ["SECRET_KEY"]
    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")

    init_db()
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(listings_bp)


    @app.after_request
    def add_cors_headers(response: Response) -> Response:
        origin = request.headers.get("Origin")
        response.headers["Access-Control-Allow-Origin"] = origin if origin == FRONTEND_ORIGIN else FRONTEND_ORIGIN
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
        return response


    @app.route("/api/<path:_path>", methods=["OPTIONS"])
    def options(_path: str) -> tuple[str, int]:
        return ("", 204)


    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError) -> tuple[Response, int]:
        return jsonify({"error": str(error)}), 400


    @app.errorhandler(404)
    def handle_not_found(_error: Exception) -> tuple[Response, int]:
        return jsonify({"error": "Not found"}), 404


    @app.errorhandler(PermissionError)
    def handle_permission_error(error: PermissionError) -> tuple[Response, int]:
        return jsonify({"error": str(error)}), 401
    
    return app

