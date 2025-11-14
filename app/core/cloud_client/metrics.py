from __future__ import annotations

import logging
from typing import Any, Tuple

import httpx

from app.core.cloud_client.base import CloudAPIBaseClient

logger = logging.getLogger(__name__)


class CloudMetricsClientMixin(CloudAPIBaseClient):
    """Metrics endpoints proxied to the Cloud API."""

    async def get_metrics_dashboard(
        self, access_token: str
    ) -> Tuple[Any | None, int]:
        return await self._get_metrics_endpoint(
            "/api/v1/metrics/dashboard", access_token
        )

    async def get_metrics_project_tracking(
        self, project_id: str, access_token: str
    ) -> Tuple[Any | None, int]:
        path = f"/api/v1/metrics/projects/{project_id}/tracking"
        return await self._get_metrics_endpoint(path, access_token)

    async def get_metrics_commitments(
        self, access_token: str
    ) -> Tuple[Any | None, int]:
        return await self._get_metrics_endpoint(
            "/api/v1/metrics/commitments", access_token
        )

    async def get_metrics_performance(
        self, access_token: str
    ) -> Tuple[Any | None, int]:
        return await self._get_metrics_endpoint(
            "/api/v1/metrics/performance", access_token
        )

    async def _get_metrics_endpoint(
        self, path: str, access_token: str
    ) -> Tuple[Any | None, int]:
        url = f"{self.base_url}{path}"
        try:
            resp = await self.client.get(url, headers=self._headers(access_token))
            if resp.status_code == 200:
                return resp.json(), resp.status_code
            logger.error("Metrics endpoint %s failed: %s - %s", path, resp.status_code, resp.text[:500])
            return None, resp.status_code
        except httpx.TimeoutException as e:
            logger.error("Timeout calling metrics endpoint %s after %ss: %s", path, self.timeout, e)
            return None, 504
        except httpx.RequestError as e:
            logger.error("Network error calling metrics endpoint %s: %s", path, e)
            return None, 502
        except Exception as e:
            logger.exception("Unexpected error calling metrics endpoint %s: %s", path, e)
            return None, 500
