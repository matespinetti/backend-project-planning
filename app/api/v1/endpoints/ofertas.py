import asyncio
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.bonita import BonitaClient
from app.core.cloud_client import CloudAPIClient
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.oferta import (
    OfertaConfirmationResponse,
    OfertaCreate,
    OfertaDetailedResponse,
    OfertaEstadoFilter,
    OfertaEvaluationRequest,
    OfertaResponse,
    OfertaUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_detail(payload: Optional[object], default: str) -> object:
    if isinstance(payload, (dict, list)):
        return payload
    if isinstance(payload, str):
        return {"detail": payload}
    return {"detail": default}


VALID_OFERTA_FILTERS = {estado.value for estado in OfertaEstadoFilter}


@router.post(
    "/pedidos/{pedido_id}/ofertas",
    response_model=OfertaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_oferta_for_pedido(
    pedido_id: UUID,
    oferta_data: OfertaCreate,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.create_oferta(
            pedido_id=str(pedido_id),
            oferta_data=oferta_data,
            access_token=auth.token,
        )
        if status_code == status.HTTP_201_CREATED and data:
            return OfertaResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to create oferta"),
        )
    finally:
        await cloud_client.aclose()


@router.get(
    "/pedidos/{pedido_id}/ofertas",
    response_model=List[OfertaResponse],
)
async def list_ofertas_for_pedido(
    pedido_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> List[OfertaResponse]:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.list_pedido_ofertas(
            pedido_id=str(pedido_id), access_token=auth.token
        )
        if status_code == status.HTTP_200_OK and isinstance(data, list):
            return [OfertaResponse.model_validate(item) for item in data]

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to list ofertas"),
        )
    finally:
        await cloud_client.aclose()


@router.get(
    "/ofertas/mis-ofertas",
    response_model=List[OfertaDetailedResponse],
)
async def list_my_ofertas(
    estado_oferta: Optional[str] = Query(
        None,
        description="Filter by oferta state (pendiente, aceptada, rechazada).",
    ),
    auth: AuthenticatedUser = Depends(get_current_user),
) -> List[OfertaDetailedResponse]:
    cloud_client = CloudAPIClient()
    try:
        estado_param = None
        if estado_oferta:
            normalized = estado_oferta.lower()
            if normalized not in VALID_OFERTA_FILTERS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "detail": "estado_oferta must be one of pendiente, aceptada or rechazada"
                    },
                )
            estado_param = normalized

        data, status_code = await cloud_client.list_mis_ofertas(
            access_token=auth.token,
            estado_oferta=estado_param,
        )
        if status_code == status.HTTP_200_OK and isinstance(data, list):
            return [OfertaDetailedResponse.model_validate(item) for item in data]

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to list ofertas"),
        )
    finally:
        await cloud_client.aclose()


@router.get(
    "/ofertas/{oferta_id}",
    response_model=OfertaResponse,
)
async def get_oferta(
    oferta_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.get_oferta(
            oferta_id=str(oferta_id), access_token=auth.token
        )
        if status_code == status.HTTP_200_OK and data:
            return OfertaResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to fetch oferta"),
        )
    finally:
        await cloud_client.aclose()


@router.patch(
    "/ofertas/{oferta_id}",
    response_model=OfertaResponse,
)
async def update_oferta(
    oferta_id: UUID,
    oferta_updates: OfertaUpdate,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaResponse:
    update_payload = oferta_updates.model_dump(exclude_unset=True, exclude_none=True)
    if not update_payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "At least one field must be provided"},
        )

    cloud_client = CloudAPIClient()
    try:
        trimmed_updates = OfertaUpdate(**update_payload)
        data, status_code = await cloud_client.update_oferta(
            oferta_id=str(oferta_id),
            oferta_data=trimmed_updates,
            access_token=auth.token,
        )
        if status_code == status.HTTP_200_OK and data:
            return OfertaResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to update oferta"),
        )
    finally:
        await cloud_client.aclose()


@router.delete(
    "/ofertas/{oferta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_oferta(
    oferta_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.delete_oferta(
            oferta_id=str(oferta_id), access_token=auth.token
        )
        if status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT):
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to delete oferta"),
        )
    finally:
        await cloud_client.aclose()


@router.post(
    "/ofertas/{oferta_id}/evaluate",
    response_model=OfertaResponse,
    status_code=status.HTTP_200_OK,
)
async def evaluate_oferta(
    oferta_id: UUID,
    evaluation: OfertaEvaluationRequest,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaResponse:
    """
    Evaluate an oferta by executing Bonita user task.

    Flow:
    1. Get oferta details from Cloud API (includes nested pedido and proyecto info)
    2. Extract bonita_case_id from the proyecto
    3. Find pending "Evaluate Offer" task in Bonita for that case
    4. Execute task with decision (accept/reject)
    5. Bonita process advances and calls Cloud API accept/reject via connectors
    6. Return updated oferta
    """
    cloud_client = CloudAPIClient()
    bonita_client = BonitaClient()

    try:
        # Step 1: Get oferta with nested proyecto info
        logger.info(f"Fetching oferta {oferta_id} with nested project data")
        oferta_data, status_code = await cloud_client.get_oferta(
            oferta_id=str(oferta_id), access_token=auth.token
        )

        if status_code != status.HTTP_200_OK or not oferta_data:
            raise HTTPException(
                status_code=status_code,
                detail=_to_detail(oferta_data, "Failed to fetch oferta"),
            )

        # Step 2: Resolve proyecto + Bonita metadata with the new enriched payload
        embedded_pedido = (oferta_data.get("pedido") or {}) if isinstance(oferta_data, dict) else {}
        embedded_proyecto = (
            oferta_data.get("proyecto") or {} if isinstance(oferta_data, dict) else {}
        )

        pedido_id = embedded_pedido.get("id") or oferta_data.get("pedido_id")
        if not pedido_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"detail": "Oferta is not associated with a pedido"},
            )

        proyecto_id = embedded_proyecto.get("id") or embedded_pedido.get("proyecto_id")
        bonita_case_id = embedded_proyecto.get("bonita_case_id")
        etapa_id = embedded_pedido.get("etapa_id")

        # Fallback to Cloud API lookups only when context was not provided
        pedido_data = None
        if not proyecto_id or not etapa_id or embedded_pedido == {}:
            logger.info(f"Fetching pedido {pedido_id} to complete context data")
            pedido_data, pedido_status = await cloud_client.get_pedido(
                pedido_id=str(pedido_id), access_token=auth.token
            )

            if pedido_status != status.HTTP_200_OK or not pedido_data:
                raise HTTPException(
                    status_code=pedido_status,
                    detail=_to_detail(pedido_data, "Failed to fetch pedido"),
                )

            etapa_id = etapa_id or pedido_data.get("etapa_id")
            proyecto_id = proyecto_id or pedido_data.get("proyecto_id")
        else:
            pedido_data = embedded_pedido

        if not proyecto_id and not etapa_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"detail": "Pedido data is missing proyecto context"},
            )

        if not proyecto_id and etapa_id:
            logger.info(f"Fetching etapa {etapa_id} to resolve proyecto info")
            etapa_data, etapa_status = await cloud_client.get_etapa(
                etapa_id=str(etapa_id), access_token=auth.token
            )

            if etapa_status != status.HTTP_200_OK or not etapa_data:
                raise HTTPException(
                    status_code=etapa_status,
                    detail=_to_detail(etapa_data, "Failed to fetch etapa"),
                )

            proyecto_id = etapa_data.get("proyecto_id")

        if not proyecto_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"detail": "Unable to resolve proyecto for the oferta"},
            )

        if not bonita_case_id:
            logger.info(f"Fetching proyecto {proyecto_id} to get bonita_case_id")
            proyecto_data = await cloud_client.get_project(
                project_id=str(proyecto_id), access_token=auth.token
            )

            if not proyecto_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "detail": f"Proyecto with id {proyecto_id} not found while evaluating oferta"
                    },
                )

            bonita_case_id = proyecto_data.get("bonita_case_id")

        if not bonita_case_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "Proyecto is not associated with a Bonita process. Cannot evaluate oferta."
                },
            )

        logger.info(f"Found Bonita case {bonita_case_id} for proyecto {proyecto_id}")

        # Step 3: Find pending "Evaluate Offer" task in Bonita
        bonita_task_name = "EvaluateOffer"
        bonita_display_name = "Evaluate Offer"
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
            logger.warning(
                "Pending tasks for case %s did not match expected identifiers. Raw task data: %s",
                bonita_case_id,
                tasks,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "No pending 'Evaluate Offer' task found in Bonita for this project"
                },
            )

        task_id = matched_task["id"]
        logger.info(
            f"Found pending task {task_id} (name={matched_task.get('name')}) for case {bonita_case_id}"
        )

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

        # Step 4: Execute task with contract inputs
        contract_inputs = {
            "decision": evaluation.decision,
            "oferta_id": str(oferta_id),
        }

        logger.info(
            f"Executing Bonita task {task_id} with decision: {evaluation.decision}"
        )
        success = await bonita_client.execute_user_task(task_id, contract_inputs)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"detail": "Failed to execute Bonita task"},
            )

        # Step 5: Wait briefly for Bonita connectors to complete
        # Bonita will call Cloud API accept/reject via OUT connectors
        logger.info("Waiting for Bonita connectors to update Cloud API...")
        await asyncio.sleep(2)

        # Step 6: Get updated oferta from Cloud API
        updated_data, updated_status = await cloud_client.get_oferta(
            oferta_id=str(oferta_id), access_token=auth.token
        )

        if updated_status == status.HTTP_200_OK and updated_data:
            logger.info(
                f"Successfully evaluated oferta {oferta_id} via Bonita. Decision: {evaluation.decision}"
            )
            return OfertaResponse.model_validate(updated_data)

        # Task executed but couldn't fetch updated oferta
        logger.warning(
            f"Bonita task executed but failed to fetch updated oferta: {updated_status}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": "Bonita task executed but failed to fetch updated oferta. Check Cloud API logs."
            },
        )

    finally:
        await cloud_client.aclose()
        await bonita_client.aclose()


# NOTE: Direct accept/reject endpoints have been removed.
# All oferta evaluations must now go through Bonita BPM via the /evaluate endpoint.
# Bonita will call Cloud API's accept/reject endpoints directly via OUT connectors.


@router.post(
    "/ofertas/{oferta_id}/confirmar-realizacion",
    response_model=OfertaConfirmationResponse,
)
async def confirm_oferta_realizacion(
    oferta_id: UUID,
    auth: AuthenticatedUser = Depends(get_current_user),
) -> OfertaConfirmationResponse:
    cloud_client = CloudAPIClient()
    try:
        data, status_code = await cloud_client.confirm_oferta_realizacion(
            oferta_id=str(oferta_id), access_token=auth.token
        )
        if status_code == status.HTTP_200_OK and data:
            return OfertaConfirmationResponse.model_validate(data)

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to confirm oferta realization"),
        )
    finally:
        await cloud_client.aclose()


@router.get(
    "/ofertas/mis-ofertas",
    response_model=List[OfertaDetailedResponse],
)
async def list_my_ofertas(
    estado_oferta: Optional[str] = Query(
        None,
        description="Filter by oferta state (pendiente, aceptada, rechazada).",
    ),
    auth: AuthenticatedUser = Depends(get_current_user),
) -> List[OfertaDetailedResponse]:
    cloud_client = CloudAPIClient()
    try:
        estado_param = None
        if estado_oferta:
            normalized = estado_oferta.lower()
            if normalized not in VALID_OFERTA_FILTERS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "detail": "estado_oferta must be one of pendiente, aceptada or rechazada"
                    },
                )
            estado_param = normalized

        data, status_code = await cloud_client.list_mis_ofertas(
            access_token=auth.token,
            estado_oferta=estado_param,
        )
        if status_code == status.HTTP_200_OK and isinstance(data, list):
            return [OfertaDetailedResponse.model_validate(item) for item in data]

        raise HTTPException(
            status_code=status_code,
            detail=_to_detail(data, "Failed to list ofertas"),
        )
    finally:
        await cloud_client.aclose()
