"""Repository for user data access."""

from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.users.user_models import User


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @classmethod
    def factory(cls, session: Session = Depends(get_db)) -> "UserRepository":
        return cls(session=session)

    def get_user(self, user_id: UUID) -> User | None:
        """
        Get user by ID.

        Args:
            user_id: The UUID of the user to retrieve.

        Returns:
            User object if found, None otherwise.
        """
        return self._session.query(User).filter(User.id == str(user_id)).first()

    def create_user(self, user_id: UUID, email: str, name: str) -> User:
        """
        Create a new user.

        Args:
            user_id: The UUID of the user.
            email: User's email address.
            name: User's name.

        Returns:
            Created User object.
        """
        user = User(id=str(user_id), email=email, name=name, privacy_public=True)
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def update_user(self, user: User) -> User:
        """
        Update an existing user.

        Args:
            user: User object with updated fields.

        Returns:
            Updated User object.
        """
        self._session.commit()
        self._session.refresh(user)
        return user

    def get_or_create_user(self, user_id: UUID, email: str, name: str) -> User:
        """
        Get existing user or create new one.

        Args:
            user_id: The UUID of the user.
            email: User's email address.
            name: User's name.

        Returns:
            User object (existing or newly created).
        """
        user = self.get_user(user_id=user_id)
        if not user:
            user = self.create_user(user_id=user_id, email=email, name=name)
        return user
