import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, status

from app.core.cloud_client import CloudAPIClient
from app.schemas.auth import (
    TokenPair,
    TokenRefreshRequest,
    UserCreate,
    UserLogin,
    UserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _extract_cloud_error(resp: httpx.Response) -> Any:
    """Parse Cloud API error payloads safely."""
    try:
        data = resp.json()
        return data.get("detail") or data
    except ValueError:
        return resp.text[:500]


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user_data: UserCreate) -> UserResponse:
    """Register a new user through the Cloud API."""
    cloud_client = CloudAPIClient()
    try:
        resp = await cloud_client.register_user(user_data)
        if resp.status_code != status.HTTP_201_CREATED:
            detail = _extract_cloud_error(resp)
            logger.error("Cloud API register error: %s", detail)
            raise HTTPException(status_code=resp.status_code, detail=detail)

        return UserResponse.model_validate(resp.json())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during user registration: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user",
        ) from exc
    finally:
        await cloud_client.aclose()


@router.post("/auth/login", response_model=TokenPair)
async def login_user(credentials: UserLogin) -> TokenPair:
    """Perform login against the Cloud API and return the token pair."""
    cloud_client = CloudAPIClient()
    try:
        resp = await cloud_client.login_user(credentials)
        if resp.status_code != status.HTTP_200_OK:
            detail = _extract_cloud_error(resp)
            logger.warning("Cloud API login error: %s", detail)
            raise HTTPException(status_code=resp.status_code, detail=detail)

        return TokenPair.model_validate(resp.json())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during user login: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging in user",
        ) from exc
    finally:
        await cloud_client.aclose()


@router.post("/auth/refresh", response_model=TokenPair)
async def refresh_token(payload: TokenRefreshRequest) -> TokenPair:
    """Exchange a refresh token for a new access token via the Cloud API."""
    cloud_client = CloudAPIClient()
    try:
        resp = await cloud_client.refresh_access_token(payload)
        if resp.status_code != status.HTTP_200_OK:
            detail = _extract_cloud_error(resp)
            logger.warning("Cloud API refresh error: %s", detail)
            raise HTTPException(status_code=resp.status_code, detail=detail)

        return TokenPair.model_validate(resp.json())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during token refresh: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing authentication token",
        ) from exc
    finally:
        await cloud_client.aclose()
