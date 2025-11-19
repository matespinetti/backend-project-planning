import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.pedido import PedidoCreate, PedidoResponse, PedidoUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_detail(payload: Optional[object], default: str) -> object:
    if isinstance(payload, (dict, list)):
        return payload
    if isinstance(payload, str):
        return {"detail": payload}
    return {"detail": default}


@router.post(
    "/projects/{project_id}/etapas/{etapa_id}/pedidos",
    response_model=PedidoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pedido_for_etapa(
    project_id: UUID,
    etapa_id: UUID,
    pedido_data: PedidoCreate,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> PedidoResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.create_pedido(
            project_id=str(project_id),
            etapa_id=str(etapa_id),
            pedido_data=pedido_data,
            access_token=auth.token,
        )
        if status_code == status.HTTP_201_CREATED and data:
            return PedidoResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to create pedido"),
        )
    finally:
        await cloud_client.aclose()


@router.get(
    "/projects/{project_id}/pedidos",
    response_model=List[PedidoResponse],
)
async def list_project_pedidos(
    project_id: UUID,
    estado: Optional[str] = Query(
        None,
        regex="^(PENDIENTE|COMPROMETIDO|COMPLETADO)$",
        description="Filter pedidos by estado",
    ),
    auth: AuthenticatedUser = Depends(get_current_user),
) -> List[PedidoResponse]:
    cloud_client = CloudAPIClient()
    try:
        estado_param = estado.upper() if estado else None
        data, status_code = await cloud_client.list_project_pedidos(
            project_id=str(project_id),
            access_token=auth.token,
            estado=estado_param,
        )
        if status_code == status.HTTP_200_OK and isinstance(data, list):
            return [PedidoResponse.model_validate(item) for item in data]

        if status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_to_detail(data, f"Proyecto with id {project_id} not found"),
            )

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to list pedidos"),
        )
    finally:
        await cloud_client.aclose()


@router.delete(
    "/pedidos/{pedido_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_pedido(
    pedido_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.delete_pedido(
            pedido_id=str(pedido_id), access_token=auth.token
        )

        if status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT):
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to delete pedido"),
        )
    finally:
        await cloud_client.aclose()


@router.get(
    "/pedidos/{pedido_id}",
    response_model=PedidoResponse,
)
async def get_pedido(
    pedido_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> PedidoResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.get_pedido(
            pedido_id=str(pedido_id), access_token=auth.token
        )
        if status_code == status.HTTP_200_OK and data:
            return PedidoResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to fetch pedido"),
        )
    finally:
        await cloud_client.aclose()


@router.patch(
    "/pedidos/{pedido_id}",
    response_model=PedidoResponse,
)
async def update_pedido(
    pedido_id: UUID,
    updates: PedidoUpdate,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> PedidoResponse:
    update_payload = updates.model_dump(exclude_unset=True, exclude_none=True)
    if not update_payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "At least one field must be provided"},
        )

    cloud_client = CloudAPIClient()
    try:
        # rebuild model with trimmed payload to avoid sending null values
        trimmed_updates = PedidoUpdate(**update_payload)
        data, status_code = await cloud_client.update_pedido(
            pedido_id=str(pedido_id),
            pedido_data=trimmed_updates,
            access_token=auth.token,
        )
        if status_code == status.HTTP_200_OK and data:
            return PedidoResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to update pedido"),
        )
    finally:
        await cloud_client.aclose()
