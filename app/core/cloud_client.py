import logging
from typing import Any, Dict, Optional

import httpx

from app.config import get_settings
from app.schemas.proyecto import ProyectoCreate

logger = logging.getLogger(__name__)
settings = get_settings()


class CloudAPIClient:
    """
    Async client for interacting with the Cloud Persistence API.

    This client is responsible for forwarding proyecto data to the cloud-hosted
    FastAPI service for persistence. The cloud API handles all database operations
    while this proxy API focuses on Bonita BPM integration.

    Key points:
    - Sends full proyecto data (with nested etapas and pedidos)
    - Includes Bonita process information (case_id, process_instance_id)
    - Returns persisted proyecto with database-generated UUIDs
    - Must be used as async context manager or manually closed
    """

    def __init__(self, timeout: Optional[float] = None):
        self.base_url = settings.CLOUD_API_URL.rstrip("/")
        self.timeout = timeout or settings.CLOUD_API_TIMEOUT

        # Persist connection across requests
        self.client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)

    def _headers(self) -> Dict[str, str]:
        """Common headers for Cloud API requests."""
        return {
            "Content-Type": "application/json",
            # Add authentication headers here if needed in the future
            # "Authorization": f"Bearer {self.api_key}",
        }

    async def create_project(
        self,
        proyecto_data: ProyectoCreate,
        bonita_case_id: Optional[str] = None,
        bonita_process_instance_id: Optional[int] = None,
        estado: str = "en_planificacion",
    ) -> Optional[Dict[str, Any]]:
        """
        Create a project in the cloud persistence API.

        Args:
            proyecto_data: Validated proyecto data from frontend
            bonita_case_id: Case ID from Bonita BPM (optional, can be None initially)
            bonita_process_instance_id: Process instance ID from Bonita (optional, can be None initially)
            estado: Project status (default: "en_planificacion")

        Returns:
            Dict with persisted proyecto data including generated UUIDs, or None if failed

        Expected Cloud API Request (initial creation, before Bonita):
        {
            "titulo": "...",
            "descripcion": "...",
            "tipo": "...",
            "pais": "...",
            "provincia": "...",
            "ciudad": "...",
            "barrio": "...",
            "bonita_case_id": null,
            "bonita_process_instance_id": null,
            "estado": "en_planificacion",
            "etapas": [
                {
                    "nombre": "...",
                    "descripcion": "...",
                    "fecha_inicio": "2024-01-01",
                    "fecha_fin": "2024-12-31",
                    "pedidos": [...]
                }
            ]
        }

        Expected Cloud API Response:
        {
            "id": "uuid",
            "titulo": "...",
            "descripcion": "...",
            "tipo": "...",
            "pais": "...",
            "provincia": "...",
            "ciudad": "...",
            "barrio": "...",
            "estado": "en_planificacion",
            "bonita_case_id": "12345",
            "bonita_process_instance_id": 67890,
            "fecha_creacion": "2024-01-01T12:00:00",
            "fecha_actualizacion": "2024-01-01T12:00:00",
            "etapas": [
                {
                    "id": "uuid",
                    "proyecto_id": "uuid",
                    "nombre": "...",
                    "descripcion": "...",
                    "fecha_inicio": "2024-01-01",
                    "fecha_fin": "2024-12-31",
                    "pedidos": [
                        {
                            "id": "uuid",
                            "etapa_id": "uuid",
                            "tipo": "economico",
                            "descripcion": "...",
                            "monto": 1000.0,
                            "moneda": "USD",
                            "cantidad": null,
                            "unidad": null
                        }
                    ]
                }
            ]
        }
        """
        try:
            url = f"{self.base_url}/api/v1/projects"

            # Build request payload
            payload = proyecto_data.model_dump()
            payload["bonita_case_id"] = bonita_case_id
            payload["bonita_process_instance_id"] = bonita_process_instance_id
            payload["estado"] = estado

            logger.info(
                f"Sending proyecto to Cloud API: {url} (titulo: {proyecto_data.titulo})"
            )

            resp = await self.client.post(url, json=payload, headers=self._headers())

            if resp.status_code == 201:
                data = resp.json()
                logger.info(
                    f"Successfully persisted proyecto in Cloud API. ID: {data.get('id')}"
                )
                return data

            # Log error response for debugging
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

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a project from the cloud persistence API by ID.

        Args:
            project_id: UUID of the project

        Returns:
            Dict with proyecto data, or None if not found or error occurred
        """
        try:
            url = f"{self.base_url}/api/v1/projects/{project_id}"

            logger.info(f"Fetching proyecto from Cloud API: {project_id}")

            resp = await self.client.get(url, headers=self._headers())

            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Successfully fetched proyecto {project_id} from Cloud API")
                return data
            elif resp.status_code == 404:
                logger.warning(f"Proyecto {project_id} not found in Cloud API")
                return None
            else:
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

    async def delete_project(self, project_id: str) -> bool:
        """
        Delete a project from the cloud persistence API (used for rollback).

        Args:
            project_id: UUID of the project to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/projects/{project_id}"

            logger.info(f"Deleting proyecto from Cloud API (rollback): {project_id}")

            resp = await self.client.delete(url, headers=self._headers())

            if resp.status_code == 204 or resp.status_code == 200:
                logger.info(f"Successfully deleted proyecto {project_id} from Cloud API")
                return True
            elif resp.status_code == 404:
                logger.warning(
                    f"Proyecto {project_id} not found in Cloud API (already deleted?)"
                )
                return True  # Consider this success - project doesn't exist
            else:
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
    ) -> bool:
        """
        Update a project with Bonita BPM information after process starts.

        Args:
            project_id: UUID of the project to update
            bonita_case_id: Case ID from Bonita BPM
            bonita_process_instance_id: Process instance ID from Bonita

        Returns:
            True if updated successfully, False otherwise
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

            # Try PATCH first (partial update), fall back to PUT if needed
            resp = await self.client.patch(url, json=payload, headers=self._headers())

            if resp.status_code == 200:
                logger.info(
                    f"Successfully updated proyecto {project_id} with Bonita info"
                )
                return True
            else:
                logger.error(
                    f"Cloud API update failed: {resp.status_code} - {resp.text[:500]}"
                )
                return False

        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout updating Cloud API after {self.timeout}s: {e}"
            )
            return False
        except httpx.RequestError as e:
            logger.error(f"Network error updating Cloud API: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error updating Cloud API: {e}")
            return False

    async def aclose(self):
        """Close the async client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()
