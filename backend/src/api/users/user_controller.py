"""Controller for user endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.models import auth0_sub_to_uuid
from src.api.users.user_schemas import PrivacyUpdateRequest, UserResponse
from src.api.users.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    tags=["users"],
)
def get_current_user(
    request: Request,
    user_service: UserService = Depends(UserService.factory),
) -> UserResponse:
    """Get current authenticated user's profile.

    Returns the authenticated user's profile including privacy settings.

    Args:
        request: FastAPI request object (contains authenticated user)
        user_service: User service instance

    Returns:
        User profile with privacy settings

    Raises:
        HTTPException: 401 if not authenticated, 404 if user not found
    """
    # Extract user from request state (set by authentication middleware)
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    jwt_user = request.state.user

    # Convert Auth0 sub to UUID
    user_id = auth0_sub_to_uuid(jwt_user.sub)

    # Get or create user from JWT data
    user = user_service.get_or_create_user(
        user_id=user_id,
        email=jwt_user.email or "",
        name=jwt_user.name or "",
    )

    return UserResponse.model_validate(user)


@router.patch(
    "/me/privacy",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    tags=["users"],
)
def update_privacy_setting(
    request: Request,
    privacy_update: PrivacyUpdateRequest,
    user_service: UserService = Depends(UserService.factory),
) -> UserResponse:
    """Update current user's privacy setting.

    Updates whether the user's images are visible to other users.

    Args:
        request: FastAPI request object (contains authenticated user)
        privacy_update: Privacy update request with new setting
        user_service: User service instance

    Returns:
        Updated user profile

    Raises:
        HTTPException: 401 if not authenticated, 403 if unauthorized, 404 if user not found
    """
    # Extract user from request state (set by authentication middleware)
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    auth0_sub = request.state.user.sub
    user_id = auth0_sub_to_uuid(auth0_sub)

    # Update privacy setting with authorization check
    user = user_service.update_privacy_setting(
        user_id=user_id,
        requesting_user_id=user_id,
        privacy_public=privacy_update.privacy_public,
    )

    return UserResponse.model_validate(user)
