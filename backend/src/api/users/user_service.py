"""Service layer for user business logic."""

from typing import Optional

from fastapi import Depends, HTTPException
from starlette import status

from src.api.users.user_models import User
from src.api.users.user_repository import UserRepository


class UserService:
    """Service for user business logic."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    @classmethod
    def factory(
        cls, user_repository: UserRepository = Depends(UserRepository.factory)
    ) -> "UserService":
        return cls(user_repository=user_repository)

    def get_or_create_user(self, user_id: str, email: str, name: str) -> User:
        """
        Get existing user or create new one from JWT data.

        Args:
            user_id: The Auth0 user ID.
            email: User's email address.
            name: User's name.

        Returns:
            User object (existing or newly created).
        """
        return self._user_repository.get_or_create_user(
            user_id=user_id, email=email, name=name
        )

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Retrieve user by ID.

        Args:
            user_id: The user ID to retrieve.

        Returns:
            User object if found, None otherwise.
        """
        return self._user_repository.get_user(user_id=user_id)

    def update_privacy_setting(
        self, user_id: str, requesting_user_id: str, privacy_public: bool
    ) -> User:
        """
        Update user's privacy preference with authorization check.

        Args:
            user_id: The user ID to update.
            requesting_user_id: The ID of the user making the request.
            privacy_public: New privacy setting value.

        Returns:
            Updated User object.

        Raises:
            HTTPException: If user not found or unauthorized.
        """
        # Authorization check: user can only update their own settings
        if user_id != requesting_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this user's settings",
            )

        user = self._user_repository.get_user(user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user.privacy_public = privacy_public
        return self._user_repository.update_user(user=user)
