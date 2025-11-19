import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.oferta import (
    OfertaCompromisoResponse,
    OfertaConfirmationResponse,
    OfertaCreate,
    OfertaDetailedResponse,
    OfertaEstadoFilter,
    OfertaResponse,
    OfertaUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_detail(payload: Optional[object], default: str) -> object:
    if isinstance(payload, (dict, list)):
        return payload
    if isinstance(payload, str):
        return {"detail": payload}
    return {"detail": default}


VALID_OFERTA_FILTERS = {estado.value for estado in OfertaEstadoFilter}


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


@router.get(
    "/ofertas/mis-ofertas",
    response_model=List[OfertaDetailedResponse],
)
async def list_my_ofertas(
    estado_oferta: Optional[str] = Query(
        None,
        description="Filter by oferta state (pendiente, aceptada, rechazada).",
    ),
    auth: AuthenticatedUser = Depends(get_current_user),
) -> List[OfertaDetailedResponse]:
    cloud_client = CloudAPIClient()
    try:
        estado_param = None
        if estado_oferta:
            normalized = estado_oferta.lower()
            if normalized not in VALID_OFERTA_FILTERS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "detail": "estado_oferta must be one of pendiente, aceptada or rechazada"
                    },
                )
            estado_param = normalized

        data, status_code = await cloud_client.list_mis_ofertas(
            access_token=auth.token,
            estado_oferta=estado_param,
        )
        if status_code == status.HTTP_200_OK and isinstance(data, list):
            return [OfertaDetailedResponse.model_validate(item) for item in data]

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to list ofertas"),
        )
    finally:
        await cloud_client.aclose()


@router.get(
    "/ofertas/{oferta_id}",
    response_model=OfertaResponse,
)
async def get_oferta(
    oferta_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.get_oferta(
            oferta_id=str(oferta_id), access_token=auth.token
        )
        if status_code == status.HTTP_200_OK and data:
            return OfertaResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to fetch oferta"),
        )
    finally:
        await cloud_client.aclose()


@router.patch(
    "/ofertas/{oferta_id}",
    response_model=OfertaResponse,
)
async def update_oferta(
    oferta_id: UUID,
    oferta_updates: OfertaUpdate,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaResponse:
    update_payload = oferta_updates.model_dump(exclude_unset=True, exclude_none=True)
    if not update_payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "At least one field must be provided"},
        )

    cloud_client = CloudAPIClient()
    try:
        trimmed_updates = OfertaUpdate(**update_payload)
        data, status_code = await cloud_client.update_oferta(
            oferta_id=str(oferta_id),
            oferta_data=trimmed_updates,
            access_token=auth.token,
        )
        if status_code == status.HTTP_200_OK and data:
            return OfertaResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to update oferta"),
        )
    finally:
        await cloud_client.aclose()


@router.delete(
    "/ofertas/{oferta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_oferta(
    oferta_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.delete_oferta(
            oferta_id=str(oferta_id), access_token=auth.token
        )
        if status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT):
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to delete oferta"),
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


@router.get(
    "/ofertas/mis-ofertas",
    response_model=List[OfertaDetailedResponse],
)
async def list_my_ofertas(
    estado_oferta: Optional[str] = Query(
        None,
        description="Filter by oferta state (pendiente, aceptada, rechazada).",
    ),
    auth: AuthenticatedUser = Depends(get_current_user),
) -> List[OfertaDetailedResponse]:
    cloud_client = CloudAPIClient()
    try:
        estado_param = None
        if estado_oferta:
            normalized = estado_oferta.lower()
            if normalized not in VALID_OFERTA_FILTERS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "detail": "estado_oferta must be one of pendiente, aceptada or rechazada"
                    },
                )
            estado_param = normalized

        data, status_code = await cloud_client.list_mis_ofertas(
            access_token=auth.token,
            estado_oferta=estado_param,
        )
        if status_code == status.HTTP_200_OK and isinstance(data, list):
            return [OfertaDetailedResponse.model_validate(item) for item in data]

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to list ofertas"),
        )
    finally:
        await cloud_client.aclose()
