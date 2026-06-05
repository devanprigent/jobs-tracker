from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from .database import session_scope
from .models import ApplicationModel, CompanyModel, ParsedListingModel, UserModel
from .schemas import APPLICATION_STATES, ApplicationPayload, AuthPayload, FavoritePayload, ListingPayload
from .types import UserPayload


def create_user(payload: AuthPayload) -> UserPayload:
    with session_scope() as session:
        existing = session.scalar(select(UserModel).where(UserModel.email == payload.email))
        if existing is not None and existing.password_hash:
            raise ValueError("An account already exists for this email")

        user = existing or UserModel(email=payload.email)
        user.password_hash = generate_password_hash(payload.password)
        session.add(user)
        session.flush()
        seed_companies(session, user.id)
        return user.to_dict()


def authenticate_user(payload: AuthPayload) -> UserPayload | None:
    with session_scope() as session:
        user = session.scalar(select(UserModel).where(UserModel.email == payload.email))
        if user is None or not user.password_hash:
            return None
        if not check_password_hash(user.password_hash, payload.password):
            return None
        return user.to_dict()


def get_user_by_id(user_id: int) -> UserPayload | None:
    with session_scope() as session:
        user = session.get(UserModel, user_id)
        return user.to_dict() if user else None


def get_user_by_email(email: str) -> UserPayload | None:
    with session_scope() as session:
        user = session.scalar(select(UserModel).where(UserModel.email == email.strip().casefold()))
        return user.to_dict() if user else None


def seed_companies(session: Session, user_id: int) -> None:
    application_companies = session.scalars(
        select(ApplicationModel.company).where(ApplicationModel.user_id == user_id)
    ).all()
    listing_companies = session.scalars(
        select(ParsedListingModel.company).where(ParsedListingModel.user_id == user_id)
    ).all()
    upsert_companies(session, user_id, [*application_companies, *listing_companies])


def seed_all_companies(session: Session) -> None:
    for user_id in session.scalars(select(UserModel.id)).all():
        seed_companies(session, user_id)


def upsert_companies(session: Session, user_id: int, names: list[str]) -> None:
    clean_names = sorted({name.strip() for name in names if name and name.strip()}, key=str.casefold)
    for name in clean_names:
        existing = session.scalar(
            select(CompanyModel).where(CompanyModel.user_id == user_id, CompanyModel.name == name)
        )
        if existing:
            existing.updated_at = func.current_timestamp()
            continue

        session.add(CompanyModel(user_id=user_id, name=name))


def list_companies(user_id: int) -> list[str]:
    with session_scope() as session:
        company_names = set(
            session.scalars(
                select(CompanyModel.name).where(CompanyModel.user_id == user_id).order_by(CompanyModel.name)
            ).all()
        )
        application_names = set(
            session.scalars(select(ApplicationModel.company).where(ApplicationModel.user_id == user_id)).all()
        )
        listing_names = set(
            session.scalars(select(ParsedListingModel.company).where(ParsedListingModel.user_id == user_id)).all()
        )
        return sorted(company_names | application_names | listing_names, key=str.casefold)


def list_applications(user_id: int, favorite_only: bool = False) -> list[dict[str, Any]]:
    with session_scope() as session:
        statement = (
            select(ApplicationModel)
            .where(ApplicationModel.user_id == user_id)
            .order_by(
                ApplicationModel.candidature_date.desc(),
                ApplicationModel.created_at.desc(),
            )
        )
        if favorite_only:
            statement = statement.where(ApplicationModel.favorite.is_(True))
        applications = session.scalars(statement).all()
        return [application.to_dict() for application in applications]


def create_application(user_id: int, payload: ApplicationPayload) -> dict[str, Any]:
    with session_scope() as session:
        application = ApplicationModel(user_id=user_id, **payload.model_dump())
        session.add(application)
        session.flush()
        upsert_companies(session, user_id, [payload.company])
        return application.to_dict()


def update_application(user_id: int, application_id: int, payload: ApplicationPayload) -> dict[str, Any] | None:
    with session_scope() as session:
        application = session.scalar(
            select(ApplicationModel).where(ApplicationModel.id == application_id, ApplicationModel.user_id == user_id)
        )
        if application is None:
            return None

        for key, value in payload.model_dump().items():
            setattr(application, key, value)
        upsert_companies(session, user_id, [payload.company])
        session.flush()
        return application.to_dict()


def update_application_favorite(user_id: int, application_id: int, favorite: bool) -> dict[str, Any] | None:
    with session_scope() as session:
        application = session.scalar(
            select(ApplicationModel).where(ApplicationModel.id == application_id, ApplicationModel.user_id == user_id)
        )
        if application is None:
            return None

        application.favorite = favorite
        session.flush()
        return application.to_dict()


def delete_application(user_id: int, application_id: int) -> bool:
    with session_scope() as session:
        application = session.scalar(
            select(ApplicationModel).where(ApplicationModel.id == application_id, ApplicationModel.user_id == user_id)
        )
        if application is None:
            return False
        session.delete(application)
        return True


def list_parsed_listings(user_id: int) -> list[dict[str, Any]]:
    with session_scope() as session:
        listings = session.scalars(
            select(ParsedListingModel)
            .where(ParsedListingModel.user_id == user_id)
            .order_by(
                func.coalesce(ParsedListingModel.date_found, ParsedListingModel.created_at).desc(),
                ParsedListingModel.created_at.desc(),
            )
        ).all()
        return [listing.to_dict() for listing in listings]


def replace_parsed_listings(user_id: int, listings: list[dict[str, Any]]) -> int:
    normalized_listings = [normalize_listing_payload(listing) for listing in listings]
    with session_scope() as session:
        session.query(ParsedListingModel).filter(ParsedListingModel.user_id == user_id).delete()
        session.add_all(
            ParsedListingModel(user_id=user_id, **listing.model_dump()) for listing in normalized_listings
        )
        upsert_companies(session, user_id, [listing.company for listing in normalized_listings])
    return len(normalized_listings)


def track_listing(user_id: int, listing_id: int) -> dict[str, Any] | None:
    with session_scope() as session:
        listing = session.scalar(
            select(ParsedListingModel).where(ParsedListingModel.id == listing_id, ParsedListingModel.user_id == user_id)
        )
        if listing is None:
            return None

        application = ApplicationModel(
            user_id=user_id,
            position=listing.position,
            company=listing.company,
            country="",
            city=listing.location or "",
            state="Applied",
            candidature_date=listing.date_found or date.today().isoformat(),
            favorite=False,
        )
        session.add(application)
        session.flush()
        upsert_companies(session, user_id, [listing.company])
        return application.to_dict()


def validate_application_payload(payload: dict[str, Any]) -> ApplicationPayload:
    try:
        return ApplicationPayload.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(format_validation_error(exc)) from exc


def validate_auth_payload(payload: dict[str, Any]) -> AuthPayload:
    try:
        return AuthPayload.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(format_validation_error(exc)) from exc


def validate_favorite_payload(payload: dict[str, Any]) -> FavoritePayload:
    try:
        return FavoritePayload.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(format_validation_error(exc)) from exc


def normalize_listing_payload(payload: dict[str, Any]) -> ListingPayload:
    try:
        return ListingPayload.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(format_validation_error(exc)) from exc


def format_validation_error(error: ValidationError) -> str:
    first_error = error.errors()[0]
    message = str(first_error.get("msg") or "Invalid payload")
    return message.removeprefix("Value error, ")
