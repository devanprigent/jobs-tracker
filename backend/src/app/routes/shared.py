from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import jsonify, session


F = TypeVar("F", bound=Callable[..., Any])


def current_user_id() -> int | None:
    user_id = session.get("user_id")
    return user_id if isinstance(user_id, int) else None


def require_user_id() -> int:
    user_id = current_user_id()
    if user_id is None:
        raise PermissionError("Authentication required")
    return user_id


def login_required(view: F) -> F:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if current_user_id() is None:
            return jsonify({"error": "Authentication required"}), 401
        return view(*args, **kwargs)

    return cast(F, wrapped)
