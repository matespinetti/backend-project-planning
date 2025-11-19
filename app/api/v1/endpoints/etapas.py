import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.etapa import EtapaDetailResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_detail(payload: Optional[object], default: str) -> object:
    if isinstance(payload, (dict, list)):
        return payload
    if isinstance(payload, str):
        return {"detail": payload}
    return {"detail": default}


@router.get("/etapas/{etapa_id}", response_model=EtapaDetailResponse)
async def get_etapa(
    etapa_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> EtapaDetailResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.get_etapa(
            etapa_id=str(etapa_id),
            access_token=auth.token,
        )
        if status_code == status.HTTP_200_OK and data:
            return EtapaDetailResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to fetch etapa"),
        )
    finally:
        await cloud_client.aclose()
