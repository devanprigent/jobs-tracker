from __future__ import annotations

from flask import Blueprint, Response, jsonify

from ..services import list_companies
from .shared import login_required, require_user_id


companies_bp = Blueprint("companies", __name__, url_prefix="/api/companies")


@companies_bp.get("")
@login_required
def get_companies() -> Response:
    return jsonify(list_companies(require_user_id()))
