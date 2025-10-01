from datetime import date
from sqlalchemy import String, Text, Date, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from typing import List, TYPE_CHECKING
import uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.proyecto import Proyecto
    from app.models.pedido import Pedido


class Etapa(Base):
    """Modelo de etapa del proyecto."""

    __tablename__ = "etapas"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)

    # Foreign key to proyecto
    proyecto_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    proyecto: Mapped["Proyecto"] = relationship("Proyecto", back_populates="etapas")
    pedidos: Mapped[List["Pedido"]] = relationship(
        "Pedido",
        back_populates="etapa",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
