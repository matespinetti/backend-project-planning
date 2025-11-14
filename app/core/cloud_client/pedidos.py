from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from app.core.cloud_client.base import CloudAPIBaseClient
from app.schemas.oferta import OfertaCreate
from app.schemas.pedido import PedidoCreate

logger = logging.getLogger(__name__)


class CloudPedidoClientMixin(CloudAPIBaseClient):
    """Pedidos and ofertas endpoints proxied to the Cloud API."""

    async def create_pedido(
        self,
        project_id: str,
        etapa_id: str,
        pedido_data: PedidoCreate,
        access_token: str,
    ) -> Tuple[Optional[Any], int]:
        url = f"{self.base_url}/api/v1/projects/{project_id}/etapas/{etapa_id}/pedidos"
        try:
            resp = await self.client.post(
                url,
                json=pedido_data.model_dump(),
                headers=self._headers(access_token),
            )
            return self._parse_json_response(resp)
        except httpx.TimeoutException as e:
            logger.error("Timeout creating pedido after %ss: %s", self.timeout, e)
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as e:
            logger.error("Network error creating pedido: %s", e)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as e:
            logger.exception("Unexpected error creating pedido: %s", e)
            return {"detail": "Unexpected error creating pedido"}, 500

    async def list_project_pedidos(
        self,
        project_id: str,
        access_token: str,
        estado: Optional[str] = None,
    ) -> Tuple[Optional[Any], int]:
        url = f"{self.base_url}/api/v1/projects/{project_id}/pedidos"
        try:
            params = {"estado": estado} if estado else None
            resp = await self.client.get(
                url, params=params, headers=self._headers(access_token)
            )
            return self._parse_json_response(resp)
        except httpx.TimeoutException as e:
            logger.error("Timeout listing pedidos after %ss: %s", self.timeout, e)
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as e:
            logger.error("Network error listing pedidos: %s", e)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as e:
            logger.exception("Unexpected error listing pedidos: %s", e)
            return {"detail": "Unexpected error listing pedidos"}, 500

    async def delete_pedido(
        self, pedido_id: str, access_token: str
    ) -> Tuple[Optional[Any], int]:
        url = f"{self.base_url}/api/v1/pedidos/{pedido_id}"
        try:
            resp = await self.client.delete(url, headers=self._headers(access_token))
            return self._parse_json_response(resp)
        except httpx.TimeoutException as e:
            logger.error("Timeout deleting pedido after %ss: %s", self.timeout, e)
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as e:
            logger.error("Network error deleting pedido: %s", e)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as e:
            logger.exception("Unexpected error deleting pedido: %s", e)
            return {"detail": "Unexpected error deleting pedido"}, 500

    async def create_oferta(
        self,
        pedido_id: str,
        oferta_data: OfertaCreate,
        access_token: str,
    ) -> Tuple[Optional[Any], int]:
        url = f"{self.base_url}/api/v1/pedidos/{pedido_id}/ofertas"
        try:
            resp = await self.client.post(
                url,
                json=oferta_data.model_dump(),
                headers=self._headers(access_token),
            )
            return self._parse_json_response(resp)
        except httpx.TimeoutException as e:
            logger.error("Timeout creating oferta after %ss: %s", self.timeout, e)
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as e:
            logger.error("Network error creating oferta: %s", e)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as e:
            logger.exception("Unexpected error creating oferta: %s", e)
            return {"detail": "Unexpected error creating oferta"}, 500

    async def list_pedido_ofertas(
        self, pedido_id: str, access_token: str
    ) -> Tuple[Optional[Any], int]:
        url = f"{self.base_url}/api/v1/pedidos/{pedido_id}/ofertas"
        try:
            resp = await self.client.get(url, headers=self._headers(access_token))
            return self._parse_json_response(resp)
        except httpx.TimeoutException as e:
            logger.error("Timeout listing ofertas after %ss: %s", self.timeout, e)
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as e:
            logger.error("Network error listing ofertas: %s", e)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as e:
            logger.exception("Unexpected error listing ofertas: %s", e)
            return {"detail": "Unexpected error listing ofertas"}, 500

    async def accept_oferta(
        self, oferta_id: str, access_token: str
    ) -> Tuple[Optional[Any], int]:
        url = f"{self.base_url}/api/v1/ofertas/{oferta_id}/accept"
        return await self._simple_post(url, access_token)

    async def reject_oferta(
        self, oferta_id: str, access_token: str
    ) -> Tuple[Optional[Any], int]:
        url = f"{self.base_url}/api/v1/ofertas/{oferta_id}/reject"
        return await self._simple_post(url, access_token)

    async def confirm_oferta_realizacion(
        self, oferta_id: str, access_token: str
    ) -> Tuple[Optional[Any], int]:
        url = f"{self.base_url}/api/v1/ofertas/{oferta_id}/confirmar-realizacion"
        return await self._simple_post(url, access_token)

    async def list_mis_compromisos(
        self,
        access_token: str,
        estado_pedido: Optional[str] = None,
    ) -> Tuple[Optional[Any], int]:
        url = f"{self.base_url}/api/v1/ofertas/mis-compromisos"
        try:
            params = {"estado_pedido": estado_pedido} if estado_pedido else None
            resp = await self.client.get(
                url, params=params, headers=self._headers(access_token)
            )
            return self._parse_json_response(resp)
        except httpx.TimeoutException as e:
            logger.error("Timeout listing compromisos after %ss: %s", self.timeout, e)
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as e:
            logger.error("Network error listing compromisos: %s", e)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as e:
            logger.exception("Unexpected error listing compromisos: %s", e)
            return {"detail": "Unexpected error listing compromisos"}, 500

    async def _simple_post(
        self, url: str, access_token: str
    ) -> Tuple[Optional[Any], int]:
        try:
            resp = await self.client.post(url, headers=self._headers(access_token))
            return self._parse_json_response(resp)
        except httpx.TimeoutException as e:
            logger.error("Timeout calling %s after %ss: %s", url, self.timeout, e)
            return {"detail": "Timeout contacting Cloud API"}, 504
        except httpx.RequestError as e:
            logger.error("Network error calling %s: %s", url, e)
            return {"detail": "Failed to reach Cloud API"}, 502
        except Exception as e:
            logger.exception("Unexpected error calling %s: %s", url, e)
            return {"detail": "Unexpected error contacting Cloud API"}, 500

    @staticmethod
    def _parse_json_response(resp: httpx.Response) -> Tuple[Optional[Any], int]:
        if resp.content:
            try:
                return resp.json(), resp.status_code
            except ValueError:
                return {"detail": resp.text[:500] if resp.text else None}, resp.status_code
        return None, resp.status_code
