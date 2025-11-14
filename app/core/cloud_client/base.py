from __future__ import annotations

import logging
from typing import Dict, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CloudAPIBaseClient:
    """
    Shared httpx.AsyncClient wrapper with common configuration helpers.

    All domain-specific Cloud API mixins should inherit from this base
    to ensure a single configured AsyncClient plus lifecycle helpers.
    """

    def __init__(self, timeout: Optional[float] = None):
        self.base_url = settings.CLOUD_API_URL.rstrip("/")
        self.timeout = timeout or settings.CLOUD_API_TIMEOUT
        self.client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)

    def _headers(self, access_token: Optional[str] = None) -> Dict[str, str]:
        """Return default JSON headers + optional bearer token."""
        headers = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def aclose(self) -> None:
        """Close the underlying async client."""
        await self.client.aclose()

    async def __aenter__(self) -> CloudAPIBaseClient:
        """Support async context manager usage."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Ensure the httpx client is closed on exit."""
        await self.aclose()
