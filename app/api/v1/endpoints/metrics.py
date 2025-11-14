import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.metrics import (
    MetricsCommitmentsResponse,
    MetricsDashboardResponse,
    MetricsPerformanceResponse,
    MetricsProjectTrackingResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _raise_from_status(status_code: int, default: str):
    raise HTTPException(
        status_code=status_code,
        detail=default,
    )


@router.get("/metrics/dashboard", response_model=MetricsDashboardResponse)
async def get_metrics_dashboard(
    auth: AuthenticatedUser = Depends(get_current_user),
) -> MetricsDashboardResponse:
    client = CloudAPIClient()
    try:
        data, status_code = await client.get_metrics_dashboard(auth.token)
        if status_code == status.HTTP_200_OK and data:
            return MetricsDashboardResponse.model_validate(data)

        _raise_from_status(status_code, "Failed to fetch dashboard metrics")
    finally:
        await client.aclose()


@router.get(
    "/metrics/projects/{project_id}/tracking",
    response_model=MetricsProjectTrackingResponse,
)
async def get_project_tracking_metrics(
    project_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> MetricsProjectTrackingResponse:
    client = CloudAPIClient()
    try:
        data, status_code = await client.get_metrics_project_tracking(
            project_id=str(project_id), access_token=auth.token
        )
        if status_code == status.HTTP_200_OK and data:
            return MetricsProjectTrackingResponse.model_validate(data)
        if status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto with id {project_id} not found",
            )
        _raise_from_status(status_code, "Failed to fetch project tracking metrics")
    finally:
        await client.aclose()


@router.get(
    "/metrics/commitments",
    response_model=MetricsCommitmentsResponse,
)
async def get_commitments_metrics(
    auth: AuthenticatedUser = Depends(get_current_user),
) -> MetricsCommitmentsResponse:
    client = CloudAPIClient()
    try:
        data, status_code = await client.get_metrics_commitments(auth.token)
        if status_code == status.HTTP_200_OK and data:
            return MetricsCommitmentsResponse.model_validate(data)
        _raise_from_status(status_code, "Failed to fetch commitments metrics")
    finally:
        await client.aclose()


@router.get(
    "/metrics/performance",
    response_model=MetricsPerformanceResponse,
)
async def get_system_performance_metrics(
    auth: AuthenticatedUser = Depends(get_current_user),
) -> MetricsPerformanceResponse:
    client = CloudAPIClient()
    try:
        data, status_code = await client.get_metrics_performance(auth.token)
        if status_code == status.HTTP_200_OK and data:
            return MetricsPerformanceResponse.model_validate(data)
        _raise_from_status(status_code, "Failed to fetch performance metrics")
    finally:
        await client.aclose()
