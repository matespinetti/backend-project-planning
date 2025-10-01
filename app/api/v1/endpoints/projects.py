import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.bonita import BonitaClient
from app.crud import proyecto as crud_proyecto
from app.db.session import get_db
from app.schemas.proyecto import (
    ProyectoCreate,
    ProyectoCreateResponse,
    ProyectoResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/projects/{project_id}", response_model=ProyectoResponse)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get full project details by ID.

    Used by Bonita process to fetch project information when needed.
    Returns proyecto with all nested etapas and pedidos.
    """
    logger.info(f"Fetching proyecto {project_id}")
    db_proyecto = await crud_proyecto.get_proyecto(db, project_id)
    if not db_proyecto:
        logger.warning(f"Proyecto {project_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proyecto with id {project_id} not found",
        )

    return ProyectoResponse.model_validate(db_proyecto)


@router.post(
    "/projects",
    response_model=ProyectoCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    proyecto_data: ProyectoCreate,
    db: AsyncSession = Depends(get_db),
) -> ProyectoCreateResponse:
    """
    Create a new proyecto with nested etapas and pedidos.
    Also starts a Bonita BPM process instance.

    Request Flow (CORRECTED TRANSACTION HANDLING):
    1. Validate incoming data with Pydantic
    2. Create proyecto, etapas, and pedidos in database (NO COMMIT)
    3. Start Bonita process instance (can fail)
    4. If Bonita fails → automatic rollback (proyecto not persisted)
    5. If Bonita succeeds → update proyecto with Bonita info → COMMIT
    6. Return complete proyecto with Bonita info
    """
    bonita_client = None
    try:
        # Step 1: Create proyecto in database (NOT COMMITTED YET)
        logger.info(f"Creating proyecto: {proyecto_data.titulo}")
        db_proyecto = await crud_proyecto.create_proyecto(db, proyecto_data)

        # Step 2: Initialize Bonita process (CRITICAL - can fail)
        bonita_client = BonitaClient()
        bonita_contract = {"project_id": str(db_proyecto.id)}

        logger.info(f"Starting Bonita process for proyecto {db_proyecto.id}")
        bonita_result = await bonita_client.start_process(
            contract_inputs=bonita_contract, initial_variables=None
        )

        if not bonita_result:
            # Bonita failed - rollback transaction (proyecto won't be persisted)
            logger.error("Failed to start Bonita process - rolling back transaction")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start Bonita process. Proyecto was not created.",
            )

        # Step 3: Bonita succeeded - update proyecto with Bonita info
        bonita_case_id = str(bonita_result.get("caseId"))  # Convert to string
        bonita_process_instance_id = bonita_result.get("id")

        logger.info(f"Updating proyecto with Bonita case_id: {bonita_case_id}")
        db_proyecto = await crud_proyecto.update_proyecto_bonita_info(
            db, db_proyecto.id, bonita_case_id, bonita_process_instance_id
        )

        # Step 4: Commit transaction (proyecto + bonita info persisted)
        await db.commit()
        await db.refresh(db_proyecto)

        # Step 5: Build response
        bonita_process_url = f"{settings.BONITA_URL}/portal/resource/processInstance/{bonita_case_id}/content/"

        response = ProyectoCreateResponse(
            proyecto=ProyectoResponse.model_validate(db_proyecto),
            bonita_case_id=bonita_case_id,  # Already a string
            bonita_process_url=bonita_process_url,
            message="Proyecto creado exitosamente e iniciado en Bonita",
        )

        logger.info(
            f"Successfully created proyecto {db_proyecto.id} with Bonita case {bonita_case_id}"
        )
        return response

    except HTTPException:
        # HTTPException already logged - just rollback and re-raise
        await db.rollback()
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error creating proyecto: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating proyecto: {str(e)}",
        )
    finally:
        # Clean up Bonita client
        if bonita_client:
            await bonita_client.aclose()
