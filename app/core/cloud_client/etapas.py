from __future__ import annotations

import logging
from typing import Any, Optional, Tuple

import httpx

from app.core.cloud_client.base import CloudAPIBaseClient

logger = logging.getLogger(__name__)


class CloudEtapaClientMixin(CloudAPIBaseClient):
    """Etapa-centric helpers proxied to the Cloud API."""

    async def get_etapa(
        self, etapa_id: str, access_token: str
    ) -> Tuple[Optional[Any], int]:
        url = f"{self.base_url}/api/v1/etapas/{etapa_id}"
        try:
            resp = await self.client.get(url, headers=self._headers(access_token))
            return self._parse_json_response(resp)
        except httpx.TimeoutException as exc:
            logger.error("Timeout fetching etapa %s after %ss: %s", etapa_id, self.timeout, exc)
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as exc:
            logger.error("Network error fetching etapa %s: %s", etapa_id, exc)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as exc:
            logger.exception("Unexpected error fetching etapa %s: %s", etapa_id, exc)
            return {"detail": "Unexpected error fetching etapa"}, 500
