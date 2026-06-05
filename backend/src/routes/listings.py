from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from flask import Blueprint, Response, jsonify, request

from ..database import (
    DATA_DIR,
)
from ..services import (
    list_parsed_listings as db_list_parsed_listings,
    replace_parsed_listings,
    track_listing as db_track_listing,
)
from .shared import login_required, require_user_id


SRC_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = SRC_DIR.parent
listings_bp = Blueprint("listings", __name__, url_prefix="/api/listings")


@listings_bp.get("")
@login_required
def list_parsed_listings() -> Response:
    return jsonify(db_list_parsed_listings(require_user_id()))


@listings_bp.post("/import")
@login_required
def import_parsed_listings() -> tuple[Response, int]:
    payload = request.get_json(silent=True)
    listings = _extract_listings(payload)
    imported = replace_parsed_listings(require_user_id(), listings)
    return jsonify({"imported": imported}), 201


@listings_bp.post("/scrape")
@login_required
def scrape_parsed_listings() -> Response | tuple[Response, int]:
    scraper_path = SRC_DIR / "scraper.py"
    output_path = BACKEND_DIR / "jobs.json"
    user_id = require_user_id()

    if not scraper_path.exists():
        return jsonify({"error": "backend/scraper.py was not found"}), 404

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.scraper",
                "--json",
                str(output_path),
                "--csv",
                str(BACKEND_DIR / "jobs.csv"),
            ],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Scraper timed out"}), 504

    if result.returncode != 0:
        return (
            jsonify(
                {
                    "error": "Scraper failed",
                    "details": (result.stderr or result.stdout).strip(),
                }
            ),
            500,
        )

    if not output_path.exists():
        return jsonify({"error": "Scraper did not create jobs.json"}), 500

    listings = _extract_listings(json.loads(output_path.read_text(encoding="utf-8")))
    imported = replace_parsed_listings(user_id, listings)

    return jsonify(
        {
            "imported": imported,
            "output": result.stdout.strip(),
            "listings": db_list_parsed_listings(user_id),
        }
    )


@listings_bp.post("/<int:listing_id>/track")
@login_required
def track_listing(listing_id: int) -> tuple[Response, int]:
    application = db_track_listing(require_user_id(), listing_id)
    if application is None:
        return jsonify({"error": "Listing not found"}), 404
    return jsonify(application), 201


def _extract_listings(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        file_path = DATA_DIR / "listings.json"
        if not file_path.exists():
            raise ValueError("No listings payload provided and backend/data/listings.json was not found")
        payload = json.loads(file_path.read_text(encoding="utf-8"))

    if isinstance(payload, dict):
        payload = payload.get("listings") or payload.get("jobs") or payload.get("results")

    if not isinstance(payload, list):
        raise ValueError("Expected a JSON array or an object with listings/jobs/results")

    if not all(isinstance(item, dict) for item in payload):
        raise ValueError("Each listing must be a JSON object")

    return payload
