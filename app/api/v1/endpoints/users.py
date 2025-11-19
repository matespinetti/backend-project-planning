import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.auth import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_detail(payload: Optional[object], default: str) -> object:
    if isinstance(payload, (dict, list)):
        return payload
    if isinstance(payload, str):
        return {"detail": payload}
    return {"detail": default}


@router.get("/users/me", response_model=UserResponse)
async def get_authenticated_profile(
    auth: AuthenticatedUser = Depends(get_current_user),
) -> UserResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.get_authenticated_user(auth.token)
        if status_code == status.HTTP_200_OK and data:
            return UserResponse.model_validate(data)

        logger.warning("Failed to fetch /users/me from Cloud API: %s", status_code)
        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to fetch user profile"),
        )
    finally:
        await cloud_client.aclose()
