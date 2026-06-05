from __future__ import annotations

import json
from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


APPLICATION_STATES = (
    "Applied",
    "Interview",
    "Technical test",
    "Offer",
    "Rejected",
)


class AuthPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str = ""
    password: str = ""

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, value: object) -> str:
        return str(value or "").strip().casefold()

    @field_validator("password", mode="before")
    @classmethod
    def coerce_password(cls, value: object) -> str:
        return str(value or "")

    @field_validator("email")
    @classmethod
    def require_email(cls, value: str) -> str:
        if not value:
            raise ValueError("email is required")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("password must be at least 6 characters")
        return value


class ApplicationPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    position: str = ""
    company: str = ""
    country: str = ""
    city: str = ""
    state: str = "Applied"
    candidature_date: str = ""
    favorite: bool = False

    @field_validator("position", "company", "country", "city", "state", "candidature_date", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> str:
        return str(value or "").strip()

    @field_validator("position")
    @classmethod
    def require_position(cls, value: str) -> str:
        if not value:
            raise ValueError("position is required")
        return value

    @field_validator("company")
    @classmethod
    def require_company(cls, value: str) -> str:
        if not value:
            raise ValueError("company is required")
        return value

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        if value not in APPLICATION_STATES:
            raise ValueError(f"state must be one of: {', '.join(APPLICATION_STATES)}")
        return value

    @field_validator("candidature_date")
    @classmethod
    def validate_candidature_date(cls, value: str) -> str:
        if not value:
            raise ValueError("candidature_date is required")
        validate_iso_date(value, "candidature_date")
        return value


class FavoritePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    favorite: bool = False


class ListingPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    position: str = ""
    company: str = ""
    location: str | None = None
    source_url: str | None = None
    date_found: str | None = None
    raw_payload: str

    @model_validator(mode="before")
    @classmethod
    def map_listing_fields(cls, payload: object) -> dict[str, object]:
        if not isinstance(payload, dict):
            raise ValueError("Each listing must be a JSON object")

        raw_payload = dict(payload)
        return {
            **raw_payload,
            "position": raw_payload.get("position") or raw_payload.get("title") or "",
            "company": raw_payload.get("company") or raw_payload.get("organizationName") or "",
            "location": raw_payload.get("location") or None,
            "source_url": raw_payload.get("source_url")
            or raw_payload.get("url")
            or raw_payload.get("link")
            or None,
            "date_found": raw_payload.get("date_found") or raw_payload.get("publicationDate") or None,
            "raw_payload": json.dumps(raw_payload, ensure_ascii=False),
        }

    @field_validator("position", "company", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> str:
        return str(value or "").strip()

    @field_validator("location", "source_url", "date_found", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> str | None:
        cleaned = str(value or "").strip()
        return cleaned or None

    @field_validator("position")
    @classmethod
    def require_listing_position(cls, value: str) -> str:
        if not value:
            raise ValueError("listing position is required")
        return value

    @field_validator("company")
    @classmethod
    def require_listing_company(cls, value: str) -> str:
        if not value:
            raise ValueError("listing company is required")
        return value

    @field_validator("date_found")
    @classmethod
    def validate_date_found(cls, value: str | None) -> str | None:
        if value:
            validate_iso_date(value, "date_found")
        return value


def validate_iso_date(value: str, field_name: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format") from exc
