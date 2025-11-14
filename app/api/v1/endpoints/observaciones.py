import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.observacion import ObservacionResponse

logger = logging.getLogger(__name__)
router = APIRouter()


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
