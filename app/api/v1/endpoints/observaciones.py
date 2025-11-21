import logging
from datetime import date
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.observacion import (
    ObservacionResolveRequest,
    ObservacionResponse,
    ObservacionesPaginatedResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_detail(payload: Optional[object], default: str) -> object:
    """Normalize Cloud API payloads into FastAPI detail objects."""
    if isinstance(payload, (dict, list)):
        return payload
    if isinstance(payload, str):
        return {"detail": payload}
    return {"detail": default}


@router.get(
    "/observaciones",
    response_model=ObservacionesPaginatedResponse,
)
async def list_observaciones(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    estado: Optional[str] = Query(
        None,
        regex="^(pendiente|resuelta|vencida)$",
        description="Filter by estado",
    ),
    proyecto_id: Optional[UUID] = Query(
        None, description="Filter by associated project ID"
    ),
    council_user_id: Optional[UUID] = Query(
        None, description="Filter by council member creator"
    ),
    search: Optional[str] = Query(
        None,
        min_length=3,
        description="Search in descripcion/respuesta (min 3 chars)",
    ),
    fecha_desde: Optional[date] = Query(
        None, description="Only include observaciones created after this date"
    ),
    fecha_hasta: Optional[date] = Query(
        None, description="Only include observaciones created before this date"
    ),
    sort_by: Literal[
        "created_at", "fecha_limite", "fecha_resolucion", "updated_at"
    ] = Query("created_at", description="Field used for sorting"),
    sort_order: Literal["asc", "desc"] = Query(
        "desc", description="Sort direction (asc or desc)"
    ),
    auth: AuthenticatedUser = Depends(get_current_user),
) -> ObservacionesPaginatedResponse:
    """Proxy the global observaciones listing endpoint with filters and pagination."""
    params = {
        "page": page,
        "page_size": page_size,
        "estado": estado,
        "proyecto_id": str(proyecto_id) if proyecto_id else None,
        "council_user_id": str(council_user_id) if council_user_id else None,
        "search": search,
        "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
        "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    params = {k: v for k, v in params.items() if v is not None}

    cloud_client = None
    try:
        cloud_client = CloudAPIClient()
        data, status_code = await cloud_client.list_observaciones(
            access_token=auth.token,
            params=params,
        )

        if status_code == status.HTTP_200_OK and isinstance(data, dict):
            return ObservacionesPaginatedResponse.model_validate(data)

        detail = _to_detail(data, "Failed to fetch observaciones")
        raise HTTPException(status_code=status_code, detail=detail)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error listing observaciones: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing observaciones",
        ) from exc
    finally:
        if cloud_client:
            await cloud_client.aclose()


@router.get(
    "/projects/{project_id}/observaciones",
    response_model=List[ObservacionResponse],
)
async def list_project_observaciones(
    project_id: UUID,
    estado: Optional[str] = Query(
        None,
        regex="^(pendiente|resuelta|vencida)$",
        description="Filter observations by estado",
    ),
    auth: AuthenticatedUser = Depends(get_current_user),
) -> List[ObservacionResponse]:
    """Proxy to list project observations with optional estado filter."""
    cloud_client = None
    try:
        cloud_client = CloudAPIClient()
        data, status_code = await cloud_client.list_project_observaciones(
            project_id=str(project_id),
            access_token=auth.token,
            estado=estado,
        )

        if status_code == status.HTTP_200_OK and isinstance(data, list):
            return [ObservacionResponse.model_validate(item) for item in data]

        if status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto with id {project_id} not found",
            )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch observaciones from Cloud API",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Unexpected error listing observaciones for proyecto %s: %s", project_id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing observaciones",
        ) from e
    finally:
        if cloud_client:
            await cloud_client.aclose()


@router.post(
    "/observaciones/{observacion_id}/resolve",
    response_model=ObservacionResponse,
)
async def resolve_observacion(
    observacion_id: UUID,
    payload: ObservacionResolveRequest,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> ObservacionResponse:
    """Resolve an observacion through the Cloud API proxy."""
    cloud_client = None
    try:
        cloud_client = CloudAPIClient()
        data, status_code = await cloud_client.resolve_observacion(
            observacion_id=str(observacion_id),
            payload=payload,
            access_token=auth.token,
        )

        if status_code == status.HTTP_200_OK and isinstance(data, dict):
            return ObservacionResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to resolve observacion"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error resolving observacion %s: %s", observacion_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resolving observacion",
        ) from exc
    finally:
        if cloud_client:
            await cloud_client.aclose()
