import logging
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa
from app.models.pedido import Pedido, TipoPedido
from app.schemas.proyecto import ProyectoCreate

logger = logging.getLogger(__name__)


async def create_proyecto(db: AsyncSession, proyecto_data: ProyectoCreate) -> Proyecto:
    """
    Create a proyecto with nested etapas and pedidos.
    This handles the complete nested object creation.

    NOTE: Does NOT commit - caller must commit or rollback the transaction.
    """
    try:
        # Create proyecto
        db_proyecto = Proyecto(
            titulo=proyecto_data.titulo,
            descripcion=proyecto_data.descripcion,
            tipo=proyecto_data.tipo,
            pais=proyecto_data.pais,
            provincia=proyecto_data.provincia,
            ciudad=proyecto_data.ciudad,
            barrio=proyecto_data.barrio,
            estado=EstadoProyecto.EN_PLANIFICACION,
        )

        db.add(db_proyecto)
        await db.flush()  # Get the proyecto.id without committing

        # Create etapas
        for etapa_data in proyecto_data.etapas:
            db_etapa = Etapa(
                nombre=etapa_data.nombre,
                descripcion=etapa_data.descripcion,
                fecha_inicio=date.fromisoformat(etapa_data.fecha_inicio),
                fecha_fin=date.fromisoformat(etapa_data.fecha_fin),
                proyecto_id=db_proyecto.id,
            )

            db.add(db_etapa)
            await db.flush()  # Get the etapa.id without committing

            # Create pedidos for this etapa
            for pedido_data in etapa_data.pedidos:
                db_pedido = Pedido(
                    tipo=TipoPedido(pedido_data.tipo),
                    descripcion=pedido_data.descripcion,
                    monto=pedido_data.monto,
                    moneda=pedido_data.moneda,
                    cantidad=pedido_data.cantidad,
                    unidad=pedido_data.unidad,
                    etapa_id=db_etapa.id,
                )

                db.add(db_pedido)

        # DO NOT commit - let the caller handle transaction
        await db.flush()  # Ensure all objects have IDs

        logger.info(f"Created proyecto with id: {db_proyecto.id} (not committed)")
        return db_proyecto

    except Exception as e:
        logger.error(f"Error creating proyecto: {e}")
        raise


async def update_proyecto_bonita_info(
    db: AsyncSession,
    proyecto_id: UUID,
    bonita_case_id: str,
    bonita_process_instance_id: Optional[int] = None,
) -> Proyecto:
    """
    Update proyecto with Bonita process information.

    NOTE: Does NOT commit - caller must commit the transaction.
    """
    try:
        stmt = select(Proyecto).where(Proyecto.id == proyecto_id)
        result = await db.execute(stmt)
        db_proyecto = result.scalar_one_or_none()

        if not db_proyecto:
            raise ValueError(f"Proyecto with id {proyecto_id} not found")

        db_proyecto.bonita_case_id = bonita_case_id
        if bonita_process_instance_id:
            db_proyecto.bonita_process_instance_id = bonita_process_instance_id

        await db.flush()

        logger.info(f"Updated proyecto {proyecto_id} with Bonita info (not committed)")
        return db_proyecto

    except Exception as e:
        logger.error(f"Error updating proyecto Bonita info: {e}")
        raise


async def get_proyecto(db: AsyncSession, proyecto_id: UUID) -> Optional[Proyecto]:
    """Get a proyecto by ID with all nested relationships."""
    stmt = (
        select(Proyecto)
        .where(Proyecto.id == proyecto_id)
        .options(selectinload(Proyecto.etapas).selectinload(Etapa.pedidos))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
