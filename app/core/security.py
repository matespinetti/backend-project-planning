from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

from app.config import get_settings
from app.schemas.auth import UserRole

logger = logging.getLogger(__name__)
settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    """Authenticated user extracted from a JWT token."""

    user_id: UUID
    email: EmailStr
    role: UserRole
    expires_at: datetime
    token: str


def decode_access_token(token: str) -> AuthenticatedUser:
    """
    Decode and validate a JWT access token signed by the Cloud API.
    """
    try:
        payload = jwt.decode(
            token,
            settings.CLOUD_API_JWT_SECRET,
            algorithms=[settings.CLOUD_API_JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        logger.warning("Access token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid JWT token received from client")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    sub = payload.get("sub")
    email = payload.get("email")
    role_value = payload.get("role", UserRole.MEMBER.value)
    exp_timestamp = payload.get("exp")

    if not sub or not email or not exp_timestamp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication token",
        )

    try:
        user_id = UUID(str(sub))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in token",
        ) from exc

    try:
        role = UserRole(role_value)
    except ValueError:
        logger.warning("Unknown user role '%s' in token. Defaulting to MEMBER.", role_value)
        role = UserRole.MEMBER

    expires_at = datetime.fromtimestamp(int(exp_timestamp), tz=timezone.utc)

    return AuthenticatedUser(
        user_id=user_id,
        email=email,
        role=role,
        expires_at=expires_at,
        token=token,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    """
    FastAPI dependency that validates the Authorization header and
    returns the authenticated user context.
    """
    logger.info(f"[AUTH DEBUG] get_current_user called. Has credentials: {credentials is not None}")

    if not credentials:
        logger.warning("[AUTH DEBUG] Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    logger.info(f"[AUTH DEBUG] Token received (first 20 chars): {credentials.credentials[:20]}...")
    try:
        user = decode_access_token(credentials.credentials)
        logger.info(f"[AUTH DEBUG] Token decoded successfully for user: {user.user_id}")
        return user
    except HTTPException as e:
        logger.error(f"[AUTH DEBUG] Token validation failed: {e.detail}")
        raise
