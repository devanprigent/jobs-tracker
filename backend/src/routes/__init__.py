from __future__ import annotations

from .applications import applications_bp
from .auth import auth_bp
from .companies import companies_bp
from .health import health_bp
from .listings import listings_bp


__all__ = [
    "applications_bp",
    "auth_bp",
    "companies_bp",
    "health_bp",
    "listings_bp",
]
