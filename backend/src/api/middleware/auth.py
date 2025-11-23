"""Authentication middleware for JWT validation."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

import jwt
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from jwt import InvalidTokenError
from jwt.algorithms import RSAAlgorithm
from pydantic import ValidationError
from starlette import status
from starlette.responses import Response

from src.api.models import JWTUser
from src.api.config import AUTH0_DOMAIN, AUTH0_AUDIENCE

logger = logging.getLogger(__name__)

# Paths that don't require authentication
AUTH_IGNORE_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


def get_jwks() -> dict[str, Any]:
    """
    Fetch JWKS (JSON Web Key Set) from Auth0.

    Returns:
        Dictionary containing the JWKS data.

    Raises:
        HTTPException: If JWKS cannot be fetched.
    """
    import httpx

    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"

    try:
        response = httpx.get(jwks_url, timeout=5.0)
        response.raise_for_status()
        return response.json()
    except Exception as error:
        logger.error(f"Failed to fetch JWKS from {jwks_url}: {error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify authentication token",
        ) from error


def get_public_key(token: str) -> Any:
    """
    Get the public key from JWKS for the given token.

    Args:
        token: JWT token to extract the key ID from.

    Returns:
        RSA public key object.

    Raises:
        HTTPException: If the key cannot be found or extracted.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing key ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        jwks = get_jwks()
        key = None

        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = RSAAlgorithm.from_jwk(jwk)
                break

        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return key

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to get public key: {error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def create_authentication_middleware(app: FastAPI) -> None:
    """Register the authentication middleware."""

    @app.middleware("http")
    async def authentication_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Middleware to extract and validate user info from Authorization header.

        This middleware expects the 'Authorization' header with a Bearer token
        containing JWT user information.
        The header format should be: 'Authorization: Bearer <jwt_token>'
        """
        # Skip authentication for ignored paths and OPTIONS requests (CORS preflight)
        if request.url.path in AUTH_IGNORE_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        try:
            authorization = request.headers.get("Authorization")
            if not authorization:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Extract token from "Bearer <token>" format
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization header format",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            token = authorization[7:]  # Remove "Bearer " prefix

            # Get public key from Auth0 JWKS
            try:
                public_key = get_public_key(token)
            except HTTPException as http_exc:
                return JSONResponse(
                    status_code=http_exc.status_code,
                    content={"detail": http_exc.detail},
                    headers=http_exc.headers,
                )

            # Decode and validate JWT
            user_info = jwt.decode(
                jwt=token,
                key=public_key,
                audience=AUTH0_AUDIENCE,
                algorithms=["RS256"],
                issuer=f"https://{AUTH0_DOMAIN}/",
            )

            # Validate and create JWTUser object
            jwt_user = JWTUser.model_validate(user_info)

            # Attach user info to request state for endpoints to use
            request.state.user = jwt_user

        except HTTPException as http_exc:
            return JSONResponse(
                status_code=http_exc.status_code,
                content={"detail": http_exc.detail},
                headers=http_exc.headers,
            )
        except jwt.ExpiredSignatureError as error:
            logger.warning(f"Expired token: {error}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token expired"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (InvalidTokenError, ValidationError) as error:
            logger.warning(f"Invalid token: {error}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Continue with the request
        response = await call_next(request)
        return response
