from sqlalchemy import String, Text, Integer, Float, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from typing import Optional, TYPE_CHECKING
import enum
import uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.etapa import Etapa


class TipoPedido(str, enum.Enum):
    """Tipo de pedido de cobertura."""
    ECONOMICO = "economico"
    MATERIALES = "materiales"
    MANO_OBRA = "mano_obra"


class Pedido(Base):
    """Modelo de pedido de cobertura."""

    __tablename__ = "pedidos"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo: Mapped[TipoPedido] = mapped_column(
        SQLAlchemyEnum(TipoPedido, values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional fields based on tipo
    monto: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    moneda: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    cantidad: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unidad: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Foreign key to etapa
    etapa_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("etapas.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    etapa: Mapped["Etapa"] = relationship("Etapa", back_populates="pedidos")
