from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.pedido import PedidoCreate, PedidoResponse


class EtapaCreate(BaseModel):
    """Schema for creating an etapa (project stage)."""

    model_config = {"extra": "ignore"}

    nombre: str = Field(..., min_length=3, description="Stage name")
    descripcion: str = Field(..., min_length=10, description="Stage description")
    fecha_inicio: str = Field(..., description="Start date (ISO format)")
    fecha_fin: str = Field(..., description="End date (ISO format)")
    pedidos: List[PedidoCreate] = Field(..., description="List of coverage requests")

    @field_validator("fecha_inicio", "fecha_fin")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in ISO format."""
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("Date must be in ISO format (YYYY-MM-DD)")
        return v

    @field_validator("pedidos")
    @classmethod
    def validate_pedidos_not_empty(cls, v: List[PedidoCreate]) -> List[PedidoCreate]:
        """Validate at least one pedido exists."""
        if not v or len(v) == 0:
            raise ValueError("At least one pedido is required")
        return v

    def validate_dates(self) -> None:
        """Validate fecha_fin >= fecha_inicio."""
        fecha_inicio_date = date.fromisoformat(self.fecha_inicio)
        fecha_fin_date = date.fromisoformat(self.fecha_fin)
        if fecha_fin_date < fecha_inicio_date:
            raise ValueError("fecha_fin must be >= fecha_inicio")


class EtapaResponse(BaseModel):
    """Schema for etapa response (from Cloud API)."""

    model_config = {"from_attributes": True}

    id: UUID
    nombre: str
    descripcion: str
    fecha_inicio: date
    fecha_fin: date
    proyecto_id: UUID
    pedidos: List[PedidoResponse] = []


class EtapaListItem(BaseModel):
    """Schema for etapa list item with pedido counts."""

    model_config = {"from_attributes": True}

    id: UUID
    proyecto_id: UUID
    nombre: str
    descripcion: str
    fecha_inicio: date
    fecha_fin: date
    estado: str
    fecha_completitud: Optional[datetime] = None
    pedidos: List[PedidoResponse] = []
    pedidos_pendientes_count: int = 0
    pedidos_total_count: int = 0


class EtapasListResponse(BaseModel):
    """Schema for list response of etapas."""

    etapas: List[EtapaListItem]
    total: int


class EtapaDetailResponse(BaseModel):
    """Single etapa details with pedido counters."""

    model_config = {"from_attributes": True}

    id: UUID
    proyecto_id: UUID
    nombre: str
    descripcion: str
    fecha_inicio: date
    fecha_fin: date
    estado: str
    pendientes_count: int
    total_pedidos: int
