from __future__ import annotations

import logging
from typing import Any, Optional, Tuple

import httpx

from app.core.cloud_client.base import CloudAPIBaseClient

logger = logging.getLogger(__name__)


class CloudUserClientMixin(CloudAPIBaseClient):
    """User-focused Cloud API operations."""

    async def get_authenticated_user(
        self, access_token: str
    ) -> Tuple[Optional[Any], int]:
        """Fetch the current user profile from the Cloud API."""
        url = f"{self.base_url}/api/v1/users/me"
        try:
            resp = await self.client.get(url, headers=self._headers(access_token))
            return self._parse_json_response(resp)
        except httpx.TimeoutException as exc:
            logger.error("Timeout fetching current user after %ss: %s", self.timeout, exc)
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as exc:
            logger.error("Network error fetching current user: %s", exc)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as exc:
            logger.exception("Unexpected error fetching current user: %s", exc)
            return {"detail": "Unexpected error fetching current user"}, 500
