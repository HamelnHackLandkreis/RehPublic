"""Base SQLAlchemy model for wildlife camera API."""

from typing import Union
from uuid import UUID, uuid5, NAMESPACE_URL

from pydantic import BaseModel
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def auth0_sub_to_uuid(auth0_sub: str) -> UUID:
    """Convert Auth0 sub (user ID) string to a deterministic UUID.

    Uses UUID5 to generate a deterministic UUID from the Auth0 sub string.
    The same Auth0 sub will always generate the same UUID.

    Args:
        auth0_sub: Auth0 user ID (sub claim) as string

    Returns:
        UUID generated from the Auth0 sub
    """
    return uuid5(NAMESPACE_URL, auth0_sub)


class JWTUser(BaseModel):
    """Pydantic model for validated JWT payload from Auth0."""

    sub: str  # Auth0 user ID (subject)
    email: str | None = None
    name: str | None = None
    aud: Union[str, list[str]]  # Audience (can be string or list)
    iss: str  # Issuer
    exp: int  # Expiration timestamp
