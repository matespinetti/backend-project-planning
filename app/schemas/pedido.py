from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID


class PedidoCreate(BaseModel):
    """Schema for creating a pedido (coverage request)."""

    tipo: str = Field(..., min_length=1, description="economico|materiales|mano_obra")
    descripcion: str = Field(..., min_length=5, description="Description of the request")
    monto: Optional[float] = Field(None, gt=0, description="Amount (for economico)")
    moneda: Optional[str] = Field(None, description="Currency code (for economico)")
    cantidad: Optional[int] = Field(None, gt=0, description="Quantity (for materiales/mano_obra)")
    unidad: Optional[str] = Field(None, description="Unit (for materiales/mano_obra)")

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, v: str) -> str:
        """Validate tipo is one of the allowed values."""
        allowed = ["economico", "materiales", "mano_obra"]
        if v not in allowed:
            raise ValueError(f"tipo must be one of {allowed}")
        return v


class PedidoResponse(BaseModel):
    """Schema for pedido response."""

    model_config = {"from_attributes": True}

    id: UUID
    tipo: str
    descripcion: str
    monto: Optional[float] = None
    moneda: Optional[str] = None
    cantidad: Optional[int] = None
    unidad: Optional[str] = None
    etapa_id: UUID
