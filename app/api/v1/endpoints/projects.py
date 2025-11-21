import asyncio
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


def _to_detail(payload: Optional[object], default: str) -> object:
    """Normalize Cloud API payloads into FastAPI detail objects."""
    if isinstance(payload, (dict, list)):
        return payload
    if isinstance(payload, str):
        return {"detail": payload}
    return {"detail": default}


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
    logger.info(f"[ROUTE DEBUG] GET /projects/{project_id} endpoint called")
    logger.info(f"[ROUTE DEBUG] Authenticated user: {auth.user_id}")

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
        regex="^(pendiente|financiada|esperando_ejecucion|en_ejecucion|completada)$",
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
    "/projects/{project_id}/start",
    response_model=ProyectoResponse,
    status_code=status.HTTP_200_OK,
)
async def start_project(
    project_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> ProyectoResponse:
    """
    Start a project by executing the ConfirmStartProject task in Bonita.

    Flow:
    1. Get proyecto from Cloud API (extract bonita_case_id)
    2. Find pending "ConfirmStartProject" task in Bonita for that case
    3. Execute task (Bonita will call Cloud API to update project status via connectors)
    4. Return updated proyecto from Cloud API

    Called from frontend with empty body. Transitions project from pendiente to en_ejecucion
    when all etapas are fully funded (validated by Cloud API via Bonita connectors).
    """
    cloud_client = None
    bonita_client = None

    try:
        # Step 1: Get proyecto from Cloud API to extract bonita_case_id
        logger.info(f"Fetching proyecto {project_id} to get Bonita context")
        cloud_client = CloudAPIClient()

        proyecto_data = await cloud_client.get_project(str(project_id), auth.token)

        if not proyecto_data:
            logger.warning(f"Proyecto {project_id} not found in Cloud API")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto with id {project_id} not found",
            )

        bonita_case_id = proyecto_data.get("bonita_case_id")

        if not bonita_case_id:
            logger.error(
                f"Proyecto {project_id} is not associated with a Bonita process. "
                f"Cannot execute ConfirmStartProject task."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "Proyecto is not associated with a Bonita process. Cannot start project."
                },
            )

        logger.info(f"Found Bonita case {bonita_case_id} for proyecto {project_id}")

        # Step 2: Find pending "ConfirmStartProject" task in Bonita
        bonita_client = BonitaClient()
        bonita_task_name = "ConfirmStartProject"

        logger.info(f"Searching for pending task '{bonita_task_name}' in Bonita case {bonita_case_id}")
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
                if task_name_val == bonita_task_name:
                    matched_task = task
                    break

        if not matched_task:
            logger.warning(
                "Pending tasks for case %s did not match expected task name. Raw task data: %s",
                bonita_case_id,
                tasks,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "No pending 'ConfirmStartProject' task found in Bonita for this project"
                },
            )

        task_id = matched_task["id"]
        logger.info(
            f"Found pending task {task_id} (name={matched_task.get('name')}) for case {bonita_case_id}"
        )

        # Step 3: Assign task to current user if needed
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

        # Step 4: Execute task with empty contract
        contract_inputs = {}

        logger.info(f"Executing Bonita task {task_id} (ConfirmStartProject)")
        success = await bonita_client.execute_user_task(task_id, contract_inputs)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"detail": "Failed to execute Bonita task"},
            )

        # Step 5: Wait briefly for Bonita connectors to complete
        # Bonita will call Cloud API start_project via OUT connectors
        logger.info("Waiting for Bonita connectors to update Cloud API...")
        await asyncio.sleep(2)

        # Step 6: Get updated proyecto from Cloud API
        logger.info(f"Fetching updated proyecto {project_id} from Cloud API")
        updated_data = await cloud_client.get_project(str(project_id), auth.token)

        if updated_data:
            logger.info(
                f"Successfully started proyecto {project_id} via Bonita task execution"
            )
            return ProyectoResponse.model_validate(updated_data)

        # Task executed but couldn't fetch updated proyecto
        logger.warning(
            f"Bonita task executed but failed to fetch updated proyecto {project_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": "Bonita task executed but failed to fetch updated proyecto. Check Cloud API logs."
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error starting proyecto {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting proyecto: {str(e)}",
        ) from e
    finally:
        if bonita_client:
            await bonita_client.aclose()
        if cloud_client:
            await cloud_client.aclose()


@router.post(
    "/projects/{project_id}/complete",
    response_model=ProyectoResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_project(
    project_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> ProyectoResponse:
    """
    Complete a project by executing the FinishProject task in Bonita.

    Flow:
    1. Get proyecto from Cloud API (extract bonita_case_id)
    2. Find pending "FinishProject" task in Bonita for that case
    3. Execute task (Bonita will call Cloud API to update proyecto status via connectors)
    4. Return updated proyecto from Cloud API

    Called from frontend with empty body. Transitions project from en_ejecucion to finalizado.
    Cloud API automatically handles state transitions via Bonita connectors.
    The main ProjectExecution process ends when FinishProject task is executed.
    """
    cloud_client = None
    bonita_client = None

    try:
        # Step 1: Get proyecto from Cloud API to extract bonita_case_id
        logger.info(f"Fetching proyecto {project_id} to get Bonita context")
        cloud_client = CloudAPIClient()

        proyecto_data = await cloud_client.get_project(str(project_id), auth.token)

        if not proyecto_data:
            logger.warning(f"Proyecto {project_id} not found in Cloud API")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto with id {project_id} not found",
            )

        bonita_case_id = proyecto_data.get("bonita_case_id")

        if not bonita_case_id:
            logger.error(
                f"Proyecto {project_id} is not associated with a Bonita process. "
                f"Cannot execute FinishProject task (missing bonita_case_id)."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "Proyecto is not associated with a Bonita process. Cannot complete project."
                },
            )

        logger.info(f"Found Bonita case {bonita_case_id} for proyecto {project_id}")

        # Step 2: Find pending "FinishProject" task in Bonita
        bonita_client = BonitaClient()
        bonita_task_name = "FinishProject"

        # First, fetch ALL pending tasks for this case
        logger.info(f"Fetching ALL pending tasks for case {bonita_case_id}...")
        all_tasks = await bonita_client.get_pending_tasks(case_id=bonita_case_id)

        if all_tasks:
            logger.info(f"Found {len(all_tasks)} pending task(s) in case {bonita_case_id}:")
            for idx, task in enumerate(all_tasks, 1):
                logger.info(f"Task {idx}: {task}")
        else:
            logger.warning(f"No pending tasks found in case {bonita_case_id}. Fetching ALL tasks in Bonita with state=ready...")
            # If no tasks in this case, fetch ALL pending tasks in Bonita to see what's available
            try:
                await bonita_client._ensure_session()
                url = f"{bonita_client.base_url}/API/bpm/humanTask"
                query_params = [
                    ("p", 0),
                    ("c", 50),
                    ("f", "state=ready"),
                ]
                resp = await bonita_client.client.get(
                    url, params=query_params, headers=bonita_client._headers()
                )
                if resp.status_code == 200:
                    all_bonita_tasks = resp.json()
                    logger.info(f"Total pending tasks in entire Bonita system: {len(all_bonita_tasks)}")
                    for idx, task in enumerate(all_bonita_tasks, 1):
                        logger.info(f"RAW TASK DATA [{idx}]: {task}")
            except Exception as e:
                logger.error(f"Error fetching all Bonita tasks: {e}")

        # Now search specifically for FinishProject task in the case
        logger.info(
            f"Searching for pending task '{bonita_task_name}' in Bonita case {bonita_case_id}"
        )
        tasks = await bonita_client.get_pending_tasks(
            case_id=bonita_case_id,
            task_name=bonita_task_name,
            task_name_field="name",
        )

        if not tasks or len(tasks) == 0:
            # Fallback: use all_tasks already fetched
            logger.info(
                "No tasks found with name filter. Using all pending tasks from case (or Bonita-wide if case was empty)."
            )
            tasks = all_tasks if all_tasks else []

        matched_task = None

        def _normalize(value: Optional[str]) -> Optional[str]:
            if isinstance(value, str):
                return value.strip()
            return value

        if tasks:
            logger.info(f"Available tasks: {len(tasks)} total")
            for idx, task in enumerate(tasks, 1):
                task_name_val = _normalize(task.get("name"))
                logger.info(
                    f"  Task {idx}: id={task.get('id')}, name={task.get('name')}, "
                    f"displayName={task.get('displayName')}, state={task.get('state')}"
                )
                if task_name_val == bonita_task_name:
                    matched_task = task
                    logger.info(f"  -> MATCHED!")
                    break

        if not matched_task:
            logger.warning(
                "Pending tasks for case %s did not match expected task name 'FinishProject'. Raw task data: %s",
                bonita_case_id,
                tasks,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "No pending 'FinishProject' task found in Bonita for this project"
                },
            )

        task_id = matched_task["id"]
        logger.info(
            f"✅ Found pending task {task_id} (name='{matched_task.get('name')}', "
            f"displayName='{matched_task.get('displayName')}') for case {bonita_case_id}"
        )

        # Step 3: Assign task to current user if needed
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

        # Step 4: Execute task with empty contract
        contract_inputs = {}

        logger.info(f"Executing Bonita task {task_id} (FinishProject)")
        success = await bonita_client.execute_user_task(task_id, contract_inputs)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"detail": "Failed to execute Bonita task"},
            )

        # Step 5: Wait briefly for Bonita connectors to complete
        # Bonita will call Cloud API complete_project via OUT connectors
        logger.info("Waiting for Bonita connectors to update Cloud API...")
        await asyncio.sleep(2)

        # Step 6: Get updated proyecto from Cloud API
        logger.info(f"Fetching updated proyecto {project_id} from Cloud API")
        updated_data = await cloud_client.get_project(str(project_id), auth.token)

        if updated_data:
            logger.info(
                f"Successfully completed proyecto {project_id} via Bonita task execution"
            )
            return ProyectoResponse.model_validate(updated_data)

        # Task executed but couldn't fetch updated proyecto
        logger.warning(
            f"Bonita task executed but failed to fetch updated proyecto {project_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": "Bonita task executed but failed to fetch updated proyecto. Check Cloud API logs."
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error completing proyecto {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing proyecto: {str(e)}",
        ) from e
    finally:
        if bonita_client:
            await bonita_client.aclose()
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
