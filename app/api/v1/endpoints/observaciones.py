import asyncio
import logging
from datetime import date
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import get_settings
from app.core.bonita import BonitaClient
from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.observacion import (
    ObservacionCreate,
    ObservacionResolveRequest,
    ObservacionResponse,
    ObservacionesPaginatedResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def _to_detail(payload: Optional[object], default: str) -> object:
    """Normalize Cloud API payloads into FastAPI detail objects."""
    if isinstance(payload, (dict, list)):
        return payload
    if isinstance(payload, str):
        return {"detail": payload}
    return {"detail": default}


@router.post(
    "/projects/{project_id}/observaciones",
    response_model=ObservacionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_observacion(
    project_id: UUID,
    payload: ObservacionCreate,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> ObservacionResponse:
    """
    Create a new observacion for a project - acts as orchestration between frontend and external services.

    Request Flow (Cloud API First, Then Bonita):
    1. Validate incoming data with Pydantic
    2. Persist observacion in Cloud API (get real UUID)
    3. Start Bonita ProjectMonitoring process with real observacion UUID
    4. If Bonita fails: rollback (delete observacion from Cloud API)
    5. If both succeed: return combined response

    This API acts as an orchestration layer, coordinating between:
    - Cloud Persistence API (data storage) - FIRST
    - Bonita BPM (process automation) - SECOND

    Only COUNCIL members can create observaciones. Fecha límite is set automatically to +5 days.
    """
    bonita_client = None
    cloud_client = None
    observacion_id = None  # Track observacion ID for rollback

    try:
        # Step 1: Persist in Cloud API FIRST (get real UUID)
        logger.info(f"Creating observacion in Cloud API for proyecto {project_id}")
        cloud_client = CloudAPIClient()

        cloud_observacion = await cloud_client.create_observacion(
            project_id=str(project_id),
            observacion_data=payload,
            access_token=auth.token,
        )

        if not cloud_observacion or cloud_observacion[1] not in (200, 201):
            logger.error("Cloud API failed to persist observacion")
            raise HTTPException(
                status_code=cloud_observacion[1] if cloud_observacion else 500,
                detail="Failed to persist observacion in Cloud API.",
            )

        observacion_data = cloud_observacion[0]
        observacion_id = observacion_data.get("id")  # Real UUID from Cloud API
        logger.info(f"Observacion persisted in Cloud API with ID: {observacion_id}")

        # Step 2: Start Bonita ObservationsReviewal process with REAL observacion ID
        logger.info(f"Starting Bonita ObservationsReviewal process for observacion {observacion_id}")
        bonita_client = BonitaClient(process_name="ObservationsReviewal")
        bonita_contract = {"observacion_id": str(observacion_id)}  # Real UUID

        bonita_result = await bonita_client.start_process(
            contract_inputs=bonita_contract, initial_variables=None
        )

        if not bonita_result:
            # Bonita failed - ROLLBACK: delete observacion from Cloud API
            logger.error(
                f"Bonita ProjectMonitoring process failed for observacion {observacion_id}. Initiating rollback..."
            )

            # Attempt to delete the observacion
            deleted = await cloud_client.delete_observacion(str(observacion_id), auth.token)

            if deleted:
                logger.info(f"Successfully rolled back observacion {observacion_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to start Bonita process. Observacion was rolled back.",
                )
            else:
                logger.error(
                    f"ROLLBACK FAILED for observacion {observacion_id} - manual cleanup needed!"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "Failed to start Bonita process and rollback failed",
                        "observacion_id": str(observacion_id),
                        "message": "Manual cleanup required. Observacion exists in Cloud API but Bonita process was not started.",
                    },
                )

        bonita_case_id = str(bonita_result.get("caseId", ""))
        bonita_process_instance_id = int(bonita_result.get("id", 0))

        logger.info(
            f"Bonita ProjectMonitoring process started successfully. Case ID: {bonita_case_id}, Instance ID: {bonita_process_instance_id}"
        )

        # Step 3: Update Cloud API with Bonita information
        logger.info(f"Updating observacion {observacion_id} in Cloud API with Bonita info")
        updated = await cloud_client.update_observacion_bonita_info(
            observacion_id=str(observacion_id),
            bonita_case_id=bonita_case_id,
            bonita_process_instance_id=bonita_process_instance_id,
            access_token=auth.token,
        )

        if not updated:
            # Update failed - log warning but don't rollback
            # Observacion exists, Bonita process is running, just missing the link
            logger.warning(
                f"Failed to update observacion {observacion_id} with Bonita info. "
                f"Observacion exists and Bonita is running (case_id: {bonita_case_id}), but link was not saved."
            )
            # Continue anyway - this is not critical enough to rollback

        # Step 4: Fetch updated observacion from Cloud API
        logger.info(f"Fetching updated observacion {observacion_id} from Cloud API")
        updated_data, updated_status = await cloud_client.list_project_observaciones(
            project_id=str(project_id),
            access_token=auth.token,
            estado=None,
        )

        if updated_status == status.HTTP_200_OK and updated_data:
            # Find our observacion in the list
            for obs in updated_data:
                if str(obs.get("id")) == str(observacion_id):
                    observacion_data = obs
                    break

        # Update the local object with Bonita info if not retrieved from Cloud API
        if not ("bonita_case_id" in observacion_data and observacion_data["bonita_case_id"]):
            observacion_data["bonita_case_id"] = bonita_case_id
            observacion_data["bonita_process_instance_id"] = bonita_process_instance_id

        logger.info(
            f"Successfully created observacion {observacion_id} with Bonita case {bonita_case_id}"
        )
        return ObservacionResponse.model_validate(observacion_data)

    except HTTPException:
        # HTTPException already logged - just re-raise
        raise
    except Exception as e:
        logger.exception(f"Unexpected error creating observacion: {e}")

        # If we have an observacion_id, attempt rollback
        if observacion_id and cloud_client:
            logger.error(
                f"Unexpected error occurred. Attempting rollback for observacion {observacion_id}"
            )
            try:
                deleted = await cloud_client.delete_observacion(str(observacion_id), auth.token)
                if deleted:
                    logger.info(
                        f"Rolled back observacion {observacion_id} after unexpected error"
                    )
                else:
                    logger.error(
                        f"Rollback failed for observacion {observacion_id} after unexpected error"
                    )
            except Exception as rollback_error:
                logger.exception(f"Error during rollback: {rollback_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating observacion: {str(e)}",
        )
    finally:
        # Clean up clients
        if bonita_client:
            await bonita_client.aclose()
        if cloud_client:
            await cloud_client.aclose()


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
    status_code=status.HTTP_200_OK,
)
async def resolve_observacion(
    observacion_id: UUID,
    payload: ObservacionResolveRequest,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> ObservacionResponse:
    """
    Resolve an observacion by executing Bonita SolveObservation task.

    Flow:
    1. Get observacion details from Cloud API (includes proyecto + Bonita metadata)
    2. Resolve observacion in Cloud API (updates estado/respuesta)
    3. Find pending "SolveObservation" task in Bonita for that case
    4. Assign task to user if needed
    5. Execute task with respuesta in contract
    6. Wait for connectors (~2s)
    7. Return updated observacion from Cloud API
    """
    cloud_client = CloudAPIClient()
    bonita_client = BonitaClient()

    try:
        # Step 1: Get observacion to extract proyecto + Bonita context
        observacion_data, fetch_status = await cloud_client.get_observacion(
            observacion_id=str(observacion_id), access_token=auth.token
        )

        if fetch_status != status.HTTP_200_OK or not observacion_data:
            raise HTTPException(
                status_code=fetch_status,
                detail=_to_detail(
                    observacion_data, "Failed to fetch observacion before resolving"
                ),
            )

        proyecto_id = observacion_data.get("proyecto_id")
        bonita_case_id = observacion_data.get("bonita_case_id")

        if not proyecto_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"detail": "Observacion is missing proyecto_id context"},
            )

        if not bonita_case_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "Observacion is not associated with a Bonita process. Cannot resolve observacion."
                },
            )

        # Step 2: Resolve observacion in Cloud API
        resolved_data, resolve_status = await cloud_client.resolve_observacion(
            observacion_id=str(observacion_id),
            payload=payload,
            access_token=auth.token,
        )

        if resolve_status != status.HTTP_200_OK or not resolved_data:
            raise HTTPException(
                status_code=resolve_status,
                detail=_to_detail(
                    resolved_data, "Failed to resolve observacion in Cloud API"
                ),
            )

        # Step 3: Find pending "SolveObservation" task in Bonita
        bonita_task_name = "SolveObservation"
        bonita_display_name = "Solve Observation"

        tasks = await bonita_client.get_pending_tasks(
            case_id=bonita_case_id,
            task_name=bonita_task_name,
            task_name_field="name",
        )

        if not tasks or len(tasks) == 0:
            # Fallback: fetch tasks without filter and match client-side
            logger.info(
                "No tasks found using Bonita name filter. Falling back to unfiltered search."
            )
            tasks = await bonita_client.get_pending_tasks(case_id=bonita_case_id)

        matched_task = None

        def _normalize(value: Optional[str]) -> Optional[str]:
            if isinstance(value, str):
                return value.strip()
            return value

        if tasks:
            for task in tasks:
                task_name_val = _normalize(task.get("name"))
                task_display_val = _normalize(task.get("displayName"))
                if task_name_val == bonita_task_name:
                    matched_task = task
                    break
                if task_display_val == bonita_display_name:
                    matched_task = task
                    break

        if not matched_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "No pending 'SolveObservation' task found in Bonita for this observacion"
                },
            )

        task_id = matched_task["id"]

        # Step 4: Assign task to current user if needed
        assigned_to = (matched_task.get("assigned_id") or "").strip()
        bonita_user_id = await bonita_client.ensure_user_context()

        if not bonita_user_id:
            logger.error("Bonita user_id not available after authentication")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"detail": "Bonita authentication failed to provide user context"},
            )

        if not assigned_to or assigned_to != bonita_user_id:
            logger.info(
                f"Assigning task {task_id} to Bonita user {bonita_user_id} before execution"
            )
            assigned = await bonita_client.assign_user_task(
                task_id=task_id, user_id=bonita_user_id
            )
            if not assigned:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"detail": "Failed to assign Bonita task before execution"},
            )

        # Step 5: Execute task with contract inputs
        contract_inputs = {
            "respuesta": payload.respuesta,
        }

        success = await bonita_client.execute_user_task(task_id, contract_inputs)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"detail": "Failed to execute Bonita task"},
            )

        # Step 5: Wait briefly for Bonita connectors to complete
        # Bonita will call Cloud API to update observacion status via OUT connectors
        logger.info("Waiting for Bonita connectors to update Cloud API...")
        await asyncio.sleep(2)

        # Step 7: Get updated observacion from Cloud API
        updated_data, updated_status = await cloud_client.get_observacion(
            observacion_id=str(observacion_id), access_token=auth.token
        )

        if updated_status == status.HTTP_200_OK and updated_data:
            return ObservacionResponse.model_validate(updated_data)

        # Task executed but couldn't fetch updated observacion
        logger.warning(
            f"Bonita task executed but failed to fetch updated observacion {observacion_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": "Bonita task executed but failed to fetch updated observacion. Check Cloud API logs."
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error resolving observacion {observacion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resolving observacion: {str(e)}",
        ) from e
    finally:
        await cloud_client.aclose()
        await bonita_client.aclose()
