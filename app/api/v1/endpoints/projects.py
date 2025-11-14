import logging
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import get_settings
from app.core.bonita import BonitaClient
from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.etapa import EtapasListResponse
from app.schemas.proyecto import (
    PaginatedProyectoResponse,
    ProyectoCreate,
    ProyectoCreateResponse,
    ProyectoResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/projects", response_model=PaginatedProyectoResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    estado: Optional[str] = Query(
        None,
        regex="^(pendiente|en_ejecucion|finalizado)$",
        description="Filter by project status",
    ),
    tipo: Optional[str] = Query(
        None,
        max_length=100,
        description="Filter by project type (partial match, case-insensitive)",
    ),
    pais: Optional[str] = Query(
        None,
        max_length=100,
        description="Filter by country (partial match, case-insensitive)",
    ),
    provincia: Optional[str] = Query(
        None,
        max_length=100,
        description="Filter by province (partial match, case-insensitive)",
    ),
    ciudad: Optional[str] = Query(
        None,
        max_length=100,
        description="Filter by city (partial match, case-insensitive)",
    ),
    search: Optional[str] = Query(
        None,
        description="Search in title and description (case-insensitive)",
    ),
    user_id: Optional[UUID] = Query(
        None, description="Filter by project owner (user ID)"
    ),
    my_projects: bool = Query(
        False, description="Only show current user's projects (overrides user_id)"
    ),
    sort_by: Literal["created_at", "updated_at", "titulo"] = Query(
        "created_at", description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query(
        "desc", description="Sort direction (asc or desc)"
    ),
    auth: AuthenticatedUser = Depends(get_current_user),
):
    """Proxy list of projects with pagination, filters, and sorting."""
    cloud_client = None
    try:
        logger.info(
            "Listing proyectos via Cloud API (page=%s, size=%s, estado=%s, tipo=%s, search=%s, my_projects=%s)",
            page,
            page_size,
            estado,
            tipo,
            search,
            my_projects,
        )
        params = {
            "page": page,
            "page_size": page_size,
            "estado": estado,
            "tipo": tipo,
            "pais": pais,
            "provincia": provincia,
            "ciudad": ciudad,
            "search": search,
            "user_id": str(user_id) if user_id else None,
            "my_projects": my_projects,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        # Remove None values to avoid overriding Cloud defaults
        params = {k: v for k, v in params.items() if v is not None}

        cloud_client = CloudAPIClient()
        paginated = await cloud_client.list_projects(
            access_token=auth.token, params=params
        )
        if not paginated:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch proyectos from Cloud API",
            )

        return PaginatedProyectoResponse.model_validate(paginated)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error listing proyectos: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing proyectos",
        ) from e
    finally:
        if cloud_client:
            await cloud_client.aclose()


@router.get("/projects/{project_id}", response_model=ProyectoResponse)
async def get_project(
    project_id: UUID, auth: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get full project details by ID (proxied from Cloud API).

    This endpoint acts as a proxy to the Cloud Persistence API.
    Used by Bonita process or frontend to fetch project information.
    Returns proyecto with all nested etapas and pedidos.
    """
    cloud_client = None
    try:
        logger.info(f"Proxying request to Cloud API for proyecto {project_id}")

        cloud_client = CloudAPIClient()
        proyecto_data = await cloud_client.get_project(str(project_id), auth.token)

        if not proyecto_data:
            logger.warning(f"Proyecto {project_id} not found in Cloud API")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto with id {project_id} not found",
            )

        logger.info(f"Successfully fetched proyecto {project_id} from Cloud API")
        return ProyectoResponse.model_validate(proyecto_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching proyecto from Cloud API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching proyecto: {str(e)}",
        )
    finally:
        if cloud_client:
            await cloud_client.aclose()


@router.get(
    "/projects/{project_id}/etapas",
    response_model=EtapasListResponse,
)
async def list_project_etapas(
    project_id: UUID,
    estado: Optional[str] = Query(
        None,
        regex="^(pendiente|financiada|en_ejecucion|completada)$",
        description="Filter etapas by estado",
    ),
    auth: AuthenticatedUser = Depends(get_current_user),
):
    """List etapas for a project via Cloud API proxy."""
    cloud_client = None
    try:
        cloud_client = CloudAPIClient()
        data, status_code = await cloud_client.list_project_etapas(
            project_id=str(project_id),
            access_token=auth.token,
            estado=estado,
        )

        if status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto with id {project_id} not found",
            )
        if not data:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch etapas from Cloud API",
            )

        return EtapasListResponse.model_validate(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Unexpected error listing etapas for proyecto %s: %s", project_id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing etapas for proyecto",
        ) from e
    finally:
        if cloud_client:
            await cloud_client.aclose()




@router.post(
    "/projects",
    response_model=ProyectoCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    proyecto_data: ProyectoCreate,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> ProyectoCreateResponse:
    """
    Create a new proyecto - acts as proxy between frontend and external services.

    Request Flow (Cloud API First, Then Bonita):
    1. Validate incoming data with Pydantic
    2. Persist proyecto in Cloud API (get real UUID)
    3. Start Bonita BPM process with real project UUID
    4. If Bonita fails: rollback (delete project from Cloud API)
    5. If both succeed: return combined response

    This API acts as an orchestration layer, coordinating between:
    - Cloud Persistence API (data storage) - FIRST
    - Bonita BPM (process automation) - SECOND
    """
    bonita_client = None
    cloud_client = None
    project_id = None  # Track project ID for rollback

    try:
        # Step 1: Persist in Cloud API FIRST (get real UUID)
        logger.info(f"Creating proyecto in Cloud API: {proyecto_data.titulo}")
        cloud_client = CloudAPIClient()

        cloud_proyecto = await cloud_client.create_project(
            proyecto_data=proyecto_data,
            access_token=auth.token,
            bonita_case_id=None,  # No Bonita info yet
            bonita_process_instance_id=None,
            estado="en_planificacion",
        )

        if not cloud_proyecto:
            logger.error("Cloud API failed to persist proyecto")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist project in Cloud API.",
            )

        project_id = cloud_proyecto.get("id")  # Real UUID from Cloud API
        logger.info(f"Proyecto persisted in Cloud API with ID: {project_id}")

        # Step 2: Start Bonita process with REAL project ID
        logger.info(f"Starting Bonita process for proyecto {project_id}")
        bonita_client = BonitaClient()
        bonita_contract = {"project_id": str(project_id)}  # Real UUID

        bonita_result = await bonita_client.start_process(
            contract_inputs=bonita_contract, initial_variables=None
        )

        if not bonita_result:
            # Bonita failed - ROLLBACK: delete project from Cloud API
            logger.error(
                f"Bonita process failed for project {project_id}. Initiating rollback..."
            )

            # Attempt to delete the project
            deleted = await cloud_client.delete_project(str(project_id), auth.token)

            if deleted:
                logger.info(f"Successfully rolled back project {project_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to start Bonita process. Project was rolled back.",
                )
            else:
                logger.error(
                    f"ROLLBACK FAILED for project {project_id} - manual cleanup needed!"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "Failed to start Bonita process and rollback failed",
                        "project_id": str(project_id),
                        "message": "Manual cleanup required. Project exists in Cloud API but Bonita process was not started.",
                    },
                )

        bonita_case_id = str(bonita_result.get("caseId", ""))
        bonita_process_instance_id = int(bonita_result.get("id", 0))

        logger.info(
            f"Bonita process started successfully. Case ID: {bonita_case_id}, Instance ID: {bonita_process_instance_id}"
        )

        # Step 3: Update Cloud API with Bonita information
        logger.info(f"Updating proyecto {project_id} in Cloud API with Bonita info")
        updated = await cloud_client.update_project_bonita_info(
            project_id=str(project_id),
            bonita_case_id=bonita_case_id,
            bonita_process_instance_id=bonita_process_instance_id,
            access_token=auth.token,
        )

        if not updated:
            # Update failed - log warning but don't rollback
            # Project exists, Bonita process is running, just missing the link
            logger.warning(
                f"Failed to update proyecto {project_id} with Bonita info. "
                f"Project exists and Bonita is running (case_id: {bonita_case_id}), but link was not saved."
            )
            # Continue anyway - this is not critical enough to rollback

        # Step 4: Build response (use original cloud_proyecto or updated data)
        bonita_process_url = f"{settings.BONITA_URL}/portal/resource/processInstance/{bonita_case_id}/content/"

        # Update the cloud_proyecto dict with Bonita info for response
        cloud_proyecto["bonita_case_id"] = bonita_case_id
        cloud_proyecto["bonita_process_instance_id"] = bonita_process_instance_id

        response = ProyectoCreateResponse(
            proyecto=ProyectoResponse.model_validate(cloud_proyecto),
            bonita_case_id=bonita_case_id,
            bonita_process_url=bonita_process_url,
            message="Proyecto creado exitosamente e iniciado en Bonita",
        )

        logger.info(
            f"Successfully created proyecto {project_id} with Bonita case {bonita_case_id}"
        )
        return response

    except HTTPException:
        # HTTPException already logged - just re-raise
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error creating proyecto: {e}")

        # If we have a project_id, attempt rollback
        if project_id and cloud_client:
            logger.error(
                f"Unexpected error occurred. Attempting rollback for project {project_id}"
            )
            try:
                deleted = await cloud_client.delete_project(str(project_id), auth.token)
                if deleted:
                    logger.info(
                        f"Rolled back project {project_id} after unexpected error"
                    )
                else:
                    logger.error(
                        f"Rollback failed for project {project_id} after unexpected error"
                    )
            except Exception as rollback_error:
                logger.exception(f"Error during rollback: {rollback_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating proyecto: {str(e)}",
        )
    finally:
        # Clean up clients
        if bonita_client:
            await bonita_client.aclose()
        if cloud_client:
            await cloud_client.aclose()
