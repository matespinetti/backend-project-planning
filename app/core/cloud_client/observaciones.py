from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from app.core.cloud_client.base import CloudAPIBaseClient
from app.schemas.observacion import ObservacionCreate, ObservacionResolveRequest

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

    async def get_observacion(
        self, observacion_id: str, access_token: str
    ) -> Tuple[Optional[Any], int]:
        """Fetch a single observacion by ID."""
        url = f"{self.base_url}/api/v1/observaciones/{observacion_id}"
        try:
            resp = await self.client.get(url, headers=self._headers(access_token))
            return self._parse_json_response(resp)
        except httpx.TimeoutException as exc:
            logger.error(
                "Timeout fetching observacion %s after %ss: %s",
                observacion_id,
                self.timeout,
                exc,
            )
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as exc:
            logger.error("Network error fetching observacion %s: %s", observacion_id, exc)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected error fetching observacion %s: %s", observacion_id, exc)
            return {"detail": "Unexpected error fetching observacion"}, 500

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

    async def create_observacion(
        self,
        project_id: str,
        observacion_data: ObservacionCreate,
        access_token: str,
    ) -> Tuple[Optional[Any], int]:
        """
        Create a new observacion in the Cloud API for a project in ejecucion.

        This endpoint is restricted to COUNCIL members only.
        Fecha límite is set automatically to +5 days.
        Initial estado is `pendiente`.

        Returns the parsed response payload plus the upstream status code.
        """
        url = f"{self.base_url}/api/v1/projects/{project_id}/observaciones"
        payload = observacion_data.model_dump()

        try:
            resp = await self.client.post(
                url,
                json=payload,
                headers=self._headers(access_token),
            )

            if resp.status_code in (200, 201):
                return resp.json(), resp.status_code

            logger.error(
                "Cloud API create observacion error: %s - %s",
                resp.status_code,
                resp.text[:500],
            )
            return self._parse_json_response(resp)

        except httpx.TimeoutException as exc:
            logger.error(
                "Timeout creating observacion for project %s after %ss: %s",
                project_id,
                self.timeout,
                exc,
            )
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as exc:
            logger.error("Network error creating observacion for project %s: %s", project_id, exc)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "Unexpected error creating observacion for project %s: %s", project_id, exc
            )
            return {"detail": "Unexpected error creating observacion"}, 500

    async def update_observacion_bonita_info(
        self,
        observacion_id: str,
        bonita_case_id: str,
        bonita_process_instance_id: int,
        access_token: str,
    ) -> bool:
        """
        Update Bonita metadata for a stored observacion.
        """
        try:
            url = f"{self.base_url}/api/v1/observaciones/{observacion_id}"

            logger.info(
                f"Updating observacion {observacion_id} with Bonita info: "
                f"case_id={bonita_case_id}, instance_id={bonita_process_instance_id}"
            )

            payload = {
                "bonita_case_id": bonita_case_id,
                "bonita_process_instance_id": bonita_process_instance_id,
            }

            resp = await self.client.patch(
                url, json=payload, headers=self._headers(access_token)
            )

            if resp.status_code == 200:
                logger.info(f"Successfully updated observacion {observacion_id} with Bonita info")
                return True

            logger.error(
                f"Cloud API update observacion failed: {resp.status_code} - {resp.text[:500]}"
            )
            return False

        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout updating observacion {observacion_id} after {self.timeout}s: {e}"
            )
            return False
        except httpx.RequestError as e:
            logger.error(f"Network error updating observacion {observacion_id}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error updating observacion {observacion_id}: {e}")
            return False

    async def delete_observacion(
        self, observacion_id: str, access_token: str
    ) -> bool:
        """
        Delete an observacion (used for rollbacks) from the Cloud API.
        """
        try:
            url = f"{self.base_url}/api/v1/observaciones/{observacion_id}"

            logger.info(f"Deleting observacion from Cloud API (rollback): {observacion_id}")

            resp = await self.client.delete(url, headers=self._headers(access_token))

            if resp.status_code in (200, 204):
                logger.info(f"Successfully deleted observacion {observacion_id} from Cloud API")
                return True
            if resp.status_code == 404:
                logger.warning(
                    f"Observacion {observacion_id} not found in Cloud API (already deleted?)"
                )
                return True

            logger.error(
                f"Cloud API delete observacion failed: {resp.status_code} - {resp.text[:500]}"
            )
            return False

        except httpx.TimeoutException as e:
            logger.error(f"Timeout deleting observacion from Cloud API after {self.timeout}s: {e}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Network error deleting observacion from Cloud API: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error deleting observacion from Cloud API: {e}")
            return False

    @staticmethod
    def _parse_json_response(resp: httpx.Response) -> Tuple[Optional[Any], int]:
        if resp.content:
            try:
                return resp.json(), resp.status_code
            except ValueError:
                return {"detail": resp.text[:500] if resp.text else None}, resp.status_code
        return None, resp.status_code
