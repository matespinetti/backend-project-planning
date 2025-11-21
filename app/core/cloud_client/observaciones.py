from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from app.core.cloud_client.base import CloudAPIBaseClient
from app.schemas.observacion import ObservacionResolveRequest

logger = logging.getLogger(__name__)


class CloudObservacionClientMixin(CloudAPIBaseClient):
    """Observaciones endpoints proxied to the Cloud API."""

    async def list_observaciones(
        self,
        access_token: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Any], int]:
        """
        List observaciones with pagination/filters sorted by the Cloud API.

        Returns the parsed response payload plus the upstream status code to allow
        the router to translate errors consistently.
        """
        url = f"{self.base_url}/api/v1/observaciones"
        try:
            resp = await self.client.get(
                url, params=params or {}, headers=self._headers(access_token)
            )

            payload: Optional[Any]
            if resp.content:
                try:
                    payload = resp.json()
                except ValueError:
                    payload = {"detail": resp.text[:500]}
            else:
                payload = None

            if resp.status_code == 200:
                return payload, resp.status_code

            logger.error(
                "Cloud API list observaciones error: %s - %s",
                resp.status_code,
                resp.text[:500],
            )
            return payload, resp.status_code

        except httpx.TimeoutException as exc:
            logger.error("Timeout listing observaciones after %ss: %s", self.timeout, exc)
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as exc:
            logger.error("Network error listing observaciones: %s", exc)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected error listing observaciones: %s", exc)
            return {"detail": "Unexpected error listing observaciones"}, 500

    async def resolve_observacion(
        self,
        observacion_id: str,
        payload: ObservacionResolveRequest,
        access_token: str,
    ) -> Tuple[Optional[Any], int]:
        """Resolve an observacion by forwarding the response to the Cloud API."""
        url = f"{self.base_url}/api/v1/observaciones/{observacion_id}/resolve"
        try:
            resp = await self.client.post(
                url,
                json=payload.model_dump(),
                headers=self._headers(access_token),
            )
            return self._parse_json_response(resp)
        except httpx.TimeoutException as exc:
            logger.error(
                "Timeout resolving observacion %s after %ss: %s",
                observacion_id,
                self.timeout,
                exc,
            )
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as exc:
            logger.error("Network error resolving observacion %s: %s", observacion_id, exc)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected error resolving observacion %s: %s", observacion_id, exc)
            return {"detail": "Unexpected error resolving observacion"}, 500

    @staticmethod
    def _parse_json_response(resp: httpx.Response) -> Tuple[Optional[Any], int]:
        if resp.content:
            try:
                return resp.json(), resp.status_code
            except ValueError:
                return {"detail": resp.text[:500] if resp.text else None}, resp.status_code
        return None, resp.status_code
