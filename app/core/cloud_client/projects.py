from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from app.core.cloud_client.base import CloudAPIBaseClient
from app.schemas.proyecto import ProyectoCreate

logger = logging.getLogger(__name__)


class CloudProjectClientMixin(CloudAPIBaseClient):
    """Project-related endpoints proxied to the Cloud API."""

    async def list_project_etapas(
        self,
        project_id: str,
        access_token: str,
        estado: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], int]:
        """
        Retrieve etapas for a project with optional estado filter.
        Returns the parsed payload + upstream status code.
        """
        try:
            url = f"{self.base_url}/api/v1/projects/{project_id}/etapas"
            params = {"estado": estado} if estado else None

            resp = await self.client.get(
                url, params=params, headers=self._headers(access_token)
            )

            if resp.status_code == 200:
                return resp.json(), resp.status_code

            logger.error(
                "Cloud API list etapas error: %s - %s",
                resp.status_code,
                resp.text[:500],
            )
            return None, resp.status_code

        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout fetching etapas for project {project_id} after {self.timeout}s: {e}"
            )
            return None, 504
        except httpx.RequestError as e:
            logger.error(f"Network error fetching etapas for project {project_id}: {e}")
            return None, 502
        except Exception as e:
            logger.exception(f"Unexpected error fetching etapas for project {project_id}: {e}")
            return None, 500

    async def list_project_observaciones(
        self,
        project_id: str,
        access_token: str,
        estado: Optional[str] = None,
    ) -> Tuple[Optional[Any], int]:
        """List observaciones for a project with optional estado filter."""
        try:
            url = f"{self.base_url}/api/v1/projects/{project_id}/observaciones"
            params = {"estado": estado} if estado else None
            resp = await self.client.get(
                url, params=params, headers=self._headers(access_token)
            )
            if resp.status_code == 200:
                return resp.json(), resp.status_code

            logger.error(
                "Cloud API list observaciones error: %s - %s",
                resp.status_code,
                resp.text[:500],
            )
            return None, resp.status_code
        except httpx.TimeoutException as e:
            logger.error(
                "Timeout listing observaciones for project %s after %ss: %s",
                project_id,
                self.timeout,
                e,
            )
            return None, 504
        except httpx.RequestError as e:
            logger.error("Network error listing observaciones for project %s: %s", project_id, e)
            return None, 502
        except Exception as e:
            logger.exception(
                "Unexpected error listing observaciones for project %s: %s", project_id, e
            )
            return None, 500

    async def list_projects(
        self,
        access_token: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        List projects with pagination/filter params.
        """
        try:
            url = f"{self.base_url}/api/v1/projects"
            logger.info("Listing proyectos from Cloud API with params %s", params)

            resp = await self.client.get(
                url, params=params or {}, headers=self._headers(access_token)
            )

            if resp.status_code == 200:
                return resp.json()

            logger.error(
                "Cloud API list projects error: %s - %s",
                resp.status_code,
                resp.text[:500],
            )
            return None

        except httpx.TimeoutException as e:
            logger.error(f"Timeout listing projects after {self.timeout}s: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Network error listing projects: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error listing projects: {e}")
            return None

    async def create_project(
        self,
        proyecto_data: ProyectoCreate,
        access_token: str,
        bonita_case_id: Optional[str] = None,
        bonita_process_instance_id: Optional[int] = None,
        estado: str = "en_planificacion",
    ) -> Optional[Dict[str, Any]]:
        """
        Create a project in the Cloud API and return the persisted payload.
        """
        try:
            url = f"{self.base_url}/api/v1/projects"

            payload = proyecto_data.model_dump()
            payload["bonita_case_id"] = bonita_case_id
            payload["bonita_process_instance_id"] = bonita_process_instance_id
            payload["estado"] = estado

            logger.info(
                f"Sending proyecto to Cloud API: {url} (titulo: {proyecto_data.titulo})"
            )

            resp = await self.client.post(
                url, json=payload, headers=self._headers(access_token)
            )

            if resp.status_code == 201:
                data = resp.json()
                logger.info(
                    f"Successfully persisted proyecto in Cloud API. ID: {data.get('id')}"
                )
                return data

            logger.error(
                f"Cloud API returned error: {resp.status_code} - {resp.text[:500]}"
            )
            return None

        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling Cloud API after {self.timeout}s: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Network error calling Cloud API: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error calling Cloud API: {e}")
            return None

    async def get_project(
        self, project_id: str, access_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a project by UUID from the Cloud API.
        """
        try:
            url = f"{self.base_url}/api/v1/projects/{project_id}"

            logger.info(f"Fetching proyecto from Cloud API: {project_id}")

            resp = await self.client.get(url, headers=self._headers(access_token))

            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Successfully fetched proyecto {project_id} from Cloud API")
                return data
            if resp.status_code == 404:
                logger.warning(f"Proyecto {project_id} not found in Cloud API")
                return None

            logger.error(
                f"Cloud API returned error: {resp.status_code} - {resp.text[:500]}"
            )
            return None

        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling Cloud API after {self.timeout}s: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Network error calling Cloud API: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error calling Cloud API: {e}")
            return None

    async def delete_project(
        self, project_id: str, access_token: str
    ) -> bool:
        """
        Delete a project (used for rollbacks) from the Cloud API.
        """
        try:
            url = f"{self.base_url}/api/v1/projects/{project_id}"

            logger.info(f"Deleting proyecto from Cloud API (rollback): {project_id}")

            resp = await self.client.delete(url, headers=self._headers(access_token))

            if resp.status_code in (200, 204):
                logger.info(f"Successfully deleted proyecto {project_id} from Cloud API")
                return True
            if resp.status_code == 404:
                logger.warning(
                    f"Proyecto {project_id} not found in Cloud API (already deleted?)"
                )
                return True

            logger.error(
                f"Cloud API delete failed: {resp.status_code} - {resp.text[:500]}"
            )
            return False

        except httpx.TimeoutException as e:
            logger.error(f"Timeout deleting from Cloud API after {self.timeout}s: {e}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Network error deleting from Cloud API: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error deleting from Cloud API: {e}")
            return False

    async def update_project_bonita_info(
        self,
        project_id: str,
        bonita_case_id: str,
        bonita_process_instance_id: int,
        access_token: str,
    ) -> bool:
        """
        Update Bonita metadata for a stored project.
        """
        try:
            url = f"{self.base_url}/api/v1/projects/{project_id}"

            logger.info(
                f"Updating proyecto {project_id} with Bonita info: case_id={bonita_case_id}"
            )

            payload = {
                "bonita_case_id": bonita_case_id,
                "bonita_process_instance_id": bonita_process_instance_id,
            }

            resp = await self.client.patch(
                url, json=payload, headers=self._headers(access_token)
            )

            if resp.status_code == 200:
                logger.info(
                    f"Successfully updated proyecto {project_id} with Bonita info"
                )
                return True

            logger.error(
                f"Cloud API update failed: {resp.status_code} - {resp.text[:500]}"
            )
            return False

        except httpx.TimeoutException as e:
            logger.error(f"Timeout updating Cloud API after {self.timeout}s: {e}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Network error updating Cloud API: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error updating Cloud API: {e}")
            return False
