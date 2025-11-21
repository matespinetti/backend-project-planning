import asyncio
import logging
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.core.bonita import BonitaClient
from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.etapa import EtapaDetailResponse

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


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


@router.post(
    "/etapas/{etapa_id}/start",
    response_model=EtapaDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def start_etapa(
    etapa_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> EtapaDetailResponse:
    """
    Start an etapa by executing the StartStage task in Bonita.

    Flow:
    1. Get etapa from Cloud API (extract bonita_case_id)
    2. Find pending "StartStage" task in Bonita for that case
    3. Execute task (Bonita will call Cloud API to update etapa status via connectors)
    4. Return updated etapa from Cloud API

    Called from frontend with empty body. Transitions etapa from pendiente, financiada, or esperando_ejecucion to en_ejecucion
    when all pedidos are fully funded (validated by Cloud API via Bonita connectors).
    Each etapa has its own Bonita process instance (StageExecution process).
    """
    cloud_client = None
    bonita_client = None

    try:
        # Step 1: Get etapa from Cloud API to extract bonita_case_id
        logger.info(f"Fetching etapa {etapa_id} to get Bonita context")
        cloud_client = CloudAPIClient()

        etapa_data, status_code = await cloud_client.get_etapa(
            str(etapa_id), auth.token
        )

        if status_code != status.HTTP_200_OK or not etapa_data:
            logger.warning(f"Etapa {etapa_id} not found in Cloud API")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Etapa with id {etapa_id} not found",
            )

        bonita_case_id = etapa_data.get("bonita_case_id")

        if not bonita_case_id:
            logger.error(
                f"Etapa {etapa_id} is not associated with a Bonita process. "
                f"Cannot execute StartStage task (missing bonita_case_id)."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "Etapa is not associated with a Bonita process. Cannot start etapa."
                },
            )

        logger.info(f"Found Bonita case {bonita_case_id} for etapa {etapa_id}")

        # Step 2: Find pending "StartStage" task in Bonita
        bonita_client = BonitaClient()
        bonita_task_name = "StartStage"

        # First, fetch ALL pending tasks for this case (as subprocess)
        logger.info(f"Fetching ALL pending tasks for case {bonita_case_id} (filtering by parentCaseId)...")
        all_tasks = await bonita_client.get_pending_tasks(case_id=bonita_case_id, is_subprocess=True)

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

        # Now search specifically for StartStage task in the case (as subprocess)
        logger.info(
            f"Searching for pending task '{bonita_task_name}' in Bonita case {bonita_case_id}"
        )
        tasks = await bonita_client.get_pending_tasks(
            case_id=bonita_case_id,
            task_name=bonita_task_name,
            task_name_field="name",
            is_subprocess=True,
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
                "Pending tasks for case %s did not match expected task name 'StartStage'. Raw task data: %s",
                bonita_case_id,
                tasks,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "No pending 'StartStage' task found in Bonita for this etapa"
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

        logger.info(f"Executing Bonita task {task_id} (StartStage)")
        success = await bonita_client.execute_user_task(task_id, contract_inputs)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"detail": "Failed to execute Bonita task"},
            )

        # Step 5: Wait briefly for Bonita connectors to complete
        # Bonita will call Cloud API start_etapa via OUT connectors
        logger.info("Waiting for Bonita connectors to update Cloud API...")
        await asyncio.sleep(2)

        # Step 6: Get updated etapa from Cloud API
        logger.info(f"Fetching updated etapa {etapa_id} from Cloud API")
        updated_data, updated_status = await cloud_client.get_etapa(
            str(etapa_id), auth.token
        )

        if updated_status == status.HTTP_200_OK and updated_data:
            logger.info(
                f"Successfully started etapa {etapa_id} via Bonita task execution"
            )
            return EtapaDetailResponse.model_validate(updated_data)

        # Task executed but couldn't fetch updated etapa
        logger.warning(
            f"Bonita task executed but failed to fetch updated etapa {etapa_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": "Bonita task executed but failed to fetch updated etapa. Check Cloud API logs."
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error starting etapa {etapa_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting etapa: {str(e)}",
        ) from e
    finally:
        if bonita_client:
            await bonita_client.aclose()
        if cloud_client:
            await cloud_client.aclose()


@router.post(
    "/etapas/{etapa_id}/complete",
    response_model=EtapaDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_etapa(
    etapa_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> EtapaDetailResponse:
    """
    Complete an etapa by executing the FinishStage task in Bonita.

    Flow:
    1. Get etapa from Cloud API (extract bonita_case_id)
    2. Find pending "FinishStage" task in Bonita for that case
    3. Execute task (Bonita will call Cloud API to update etapa status via connectors)
    4. Return updated etapa from Cloud API

    Called from frontend with empty body. Transitions etapa from en_ejecucion to completada.
    Cloud API automatically sets fecha_completitud via Bonita connectors.
    Each etapa has its own Bonita process instance (StageExecution process).
    """
    cloud_client = None
    bonita_client = None

    try:
        # Step 1: Get etapa from Cloud API to extract bonita_case_id
        logger.info(f"Fetching etapa {etapa_id} to get Bonita context")
        cloud_client = CloudAPIClient()

        etapa_data, status_code = await cloud_client.get_etapa(
            str(etapa_id), auth.token
        )

        if status_code != status.HTTP_200_OK or not etapa_data:
            logger.warning(f"Etapa {etapa_id} not found in Cloud API")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Etapa with id {etapa_id} not found",
            )

        bonita_case_id = etapa_data.get("bonita_case_id")

        if not bonita_case_id:
            logger.error(
                f"Etapa {etapa_id} is not associated with a Bonita process. "
                f"Cannot execute FinishStage task (missing bonita_case_id)."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "Etapa is not associated with a Bonita process. Cannot complete etapa."
                },
            )

        logger.info(f"Found Bonita case {bonita_case_id} for etapa {etapa_id}")

        # Step 2: Find pending "FinishStage" task in Bonita
        bonita_client = BonitaClient()
        bonita_task_name = "FinishStage"

        # First, fetch ALL pending tasks for this case (as subprocess)
        logger.info(f"Fetching ALL pending tasks for case {bonita_case_id} (filtering by parentCaseId)...")
        all_tasks = await bonita_client.get_pending_tasks(case_id=bonita_case_id, is_subprocess=True)

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

        # Now search specifically for FinishStage task in the case (as subprocess)
        logger.info(
            f"Searching for pending task '{bonita_task_name}' in Bonita case {bonita_case_id}"
        )
        tasks = await bonita_client.get_pending_tasks(
            case_id=bonita_case_id,
            task_name=bonita_task_name,
            task_name_field="name",
            is_subprocess=True,
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
                "Pending tasks for case %s did not match expected task name 'FinishStage'. Raw task data: %s",
                bonita_case_id,
                tasks,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "No pending 'FinishStage' task found in Bonita for this etapa"
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

        logger.info(f"Executing Bonita task {task_id} (FinishStage)")
        success = await bonita_client.execute_user_task(task_id, contract_inputs)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"detail": "Failed to execute Bonita task"},
            )

        # Step 5: Wait briefly for Bonita connectors to complete
        # Bonita will call Cloud API complete_etapa via OUT connectors
        logger.info("Waiting for Bonita connectors to update Cloud API...")
        await asyncio.sleep(2)

        # Step 6: Get updated etapa from Cloud API
        logger.info(f"Fetching updated etapa {etapa_id} from Cloud API")
        updated_data, updated_status = await cloud_client.get_etapa(
            str(etapa_id), auth.token
        )

        if updated_status == status.HTTP_200_OK and updated_data:
            logger.info(
                f"Successfully completed etapa {etapa_id} via Bonita task execution"
            )
            return EtapaDetailResponse.model_validate(updated_data)

        # Task executed but couldn't fetch updated etapa
        logger.warning(
            f"Bonita task executed but failed to fetch updated etapa {etapa_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": "Bonita task executed but failed to fetch updated etapa. Check Cloud API logs."
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error completing etapa {etapa_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing etapa: {str(e)}",
        ) from e
    finally:
        if bonita_client:
            await bonita_client.aclose()
        if cloud_client:
            await cloud_client.aclose()
