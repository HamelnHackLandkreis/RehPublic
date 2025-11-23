"""Base SQLAlchemy model for wildlife camera API."""

from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JWTUser(BaseModel):
    """Pydantic model for validated JWT payload from Auth0."""

    sub: str  # Auth0 user ID (subject)
    email: Optional[str] = None
    name: Optional[str] = None
    aud: str  # Audience
    iss: str  # Issuer
    exp: int  # Expiration timestamp
