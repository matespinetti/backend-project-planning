import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.oferta import (
    OfertaCompromisoResponse,
    OfertaConfirmationResponse,
    OfertaCreate,
    OfertaResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_detail(payload: Optional[object], default: str) -> object:
    if isinstance(payload, (dict, list)):
        return payload
    if isinstance(payload, str):
        return {"detail": payload}
    return {"detail": default}


@router.post(
    "/pedidos/{pedido_id}/ofertas",
    response_model=OfertaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_oferta_for_pedido(
    pedido_id: UUID,
    oferta_data: OfertaCreate,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.create_oferta(
            pedido_id=str(pedido_id),
            oferta_data=oferta_data,
            access_token=auth.token,
        )
        if status_code == status.HTTP_201_CREATED and data:
            return OfertaResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to create oferta"),
        )
    finally:
        await cloud_client.aclose()


@router.get(
    "/pedidos/{pedido_id}/ofertas",
    response_model=List[OfertaResponse],
)
async def list_ofertas_for_pedido(
    pedido_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> List[OfertaResponse]:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.list_pedido_ofertas(
            pedido_id=str(pedido_id), access_token=auth.token
        )
        if status_code == status.HTTP_200_OK and isinstance(data, list):
            return [OfertaResponse.model_validate(item) for item in data]

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to list ofertas"),
        )
    finally:
        await cloud_client.aclose()


@router.post(
    "/ofertas/{oferta_id}/accept",
    response_model=OfertaResponse,
)
async def accept_oferta(
    oferta_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.accept_oferta(
            oferta_id=str(oferta_id), access_token=auth.token
        )
        if status_code == status.HTTP_200_OK and data:
            return OfertaResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to accept oferta"),
        )
    finally:
        await cloud_client.aclose()


@router.post(
    "/ofertas/{oferta_id}/reject",
    response_model=OfertaResponse,
)
async def reject_oferta(
    oferta_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.reject_oferta(
            oferta_id=str(oferta_id), access_token=auth.token
        )
        if status_code == status.HTTP_200_OK and data:
            return OfertaResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to reject oferta"),
        )
    finally:
        await cloud_client.aclose()


@router.post(
    "/ofertas/{oferta_id}/confirmar-realizacion",
    response_model=OfertaConfirmationResponse,
)
async def confirm_oferta_realizacion(
    oferta_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaConfirmationResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.confirm_oferta_realizacion(
            oferta_id=str(oferta_id), access_token=auth.token
        )
        if status_code == status.HTTP_200_OK and data:
            return OfertaConfirmationResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to confirm oferta realization"),
        )
    finally:
        await cloud_client.aclose()


@router.get(
    "/ofertas/mis-compromisos",
    response_model=List[OfertaCompromisoResponse],
)
async def list_my_compromisos(
    estado_pedido: Optional[str] = Query(
        None,
        regex="^(COMPROMETIDO|COMPLETADO)$",
        description="Filter commitments by pedido state",
    ),
    auth: AuthenticatedUser = Depends(get_current_user),
) -> List[OfertaCompromisoResponse]:
    cloud_client = CloudAPIClient()
    try:
        estado_param = estado_pedido.upper() if estado_pedido else None
        data, status_code = await cloud_client.list_mis_compromisos(
            access_token=auth.token,
            estado_pedido=estado_param,
        )
        if status_code == status.HTTP_200_OK and isinstance(data, list):
            return [OfertaCompromisoResponse.model_validate(item) for item in data]

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to list compromisos"),
        )
    finally:
        await cloud_client.aclose()
