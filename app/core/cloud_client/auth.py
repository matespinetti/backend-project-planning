from __future__ import annotations

import logging
import httpx

from app.core.cloud_client.base import CloudAPIBaseClient
from app.schemas.auth import TokenRefreshRequest, UserCreate, UserLogin

logger = logging.getLogger(__name__)


class CloudAuthClientMixin(CloudAPIBaseClient):
    """Authentication-related endpoints for the Cloud API."""

    async def register_user(
        self, user_data: UserCreate
    ) -> httpx.Response:
        """Proxy user registration to the Cloud API."""
        url = f"{self.base_url}/api/v1/auth/register"
        logger.info("Forwarding user registration to Cloud API")
        return await self.client.post(
            url,
            json=user_data.model_dump(),
            headers=self._headers(),
        )

    async def login_user(
        self, credentials: UserLogin
    ) -> httpx.Response:
        """Proxy user login and JWT issuance to the Cloud API."""
        url = f"{self.base_url}/api/v1/auth/login"
        logger.info("Forwarding login request to Cloud API")
        return await self.client.post(
            url,
            json=credentials.model_dump(),
            headers=self._headers(),
        )

    async def refresh_access_token(
        self, refresh_payload: TokenRefreshRequest
    ) -> httpx.Response:
        """Proxy refresh token exchange to the Cloud API."""
        url = f"{self.base_url}/api/v1/auth/refresh"
        logger.info("Forwarding refresh token request to Cloud API")
        return await self.client.post(
            url,
            json=refresh_payload.model_dump(),
            headers=self._headers(),
        )
