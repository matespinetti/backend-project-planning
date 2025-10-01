from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from typing import List, Optional, TYPE_CHECKING
import enum
import uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.etapa import Etapa


class EstadoProyecto(str, enum.Enum):
    """Estado del proyecto."""
    BORRADOR = "borrador"
    EN_PLANIFICACION = "en_planificacion"
    BUSCANDO_FINANCIAMIENTO = "buscando_financiamiento"
    EN_EJECUCION = "en_ejecucion"
    COMPLETO = "completo"


class Proyecto(Base):
    """Modelo de proyecto con integración de Bonita BPM."""

    __tablename__ = "proyectos"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    pais: Mapped[str] = mapped_column(String(100), nullable=False)
    provincia: Mapped[str] = mapped_column(String(100), nullable=False)
    ciudad: Mapped[str] = mapped_column(String(100), nullable=False)
    barrio: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Bonita BPM tracking fields
    bonita_case_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bonita_process_instance_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Estado del proyecto
    estado: Mapped[EstadoProyecto] = mapped_column(
        SQLAlchemyEnum(EstadoProyecto, values_callable=lambda x: [e.value for e in x]),
        default=EstadoProyecto.EN_PLANIFICACION,
        nullable=False,
    )

    # Timestamps
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    etapas: Mapped[List["Etapa"]] = relationship(
        "Etapa",
        back_populates="proyecto",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
