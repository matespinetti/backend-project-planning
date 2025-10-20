import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.core.bonita import BonitaClient
from app.core.cloud_client import CloudAPIClient
from app.schemas.proyecto import (
    ProyectoCreate,
    ProyectoCreateResponse,
    ProyectoResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/projects/{project_id}", response_model=ProyectoResponse)
async def get_project(project_id: UUID):
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
        proyecto_data = await cloud_client.get_project(str(project_id))

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


@router.post(
    "/projects",
    response_model=ProyectoCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    proyecto_data: ProyectoCreate,
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
            deleted = await cloud_client.delete_project(str(project_id))

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
                deleted = await cloud_client.delete_project(str(project_id))
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
