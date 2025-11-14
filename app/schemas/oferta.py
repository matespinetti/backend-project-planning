from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.pedido import PedidoResponse


class OfertaCreate(BaseModel):
    """Payload for creating an oferta."""

    descripcion: str = Field(..., min_length=10)
    monto_ofrecido: Optional[float] = Field(None, gt=0)


class OfertaUserSummary(BaseModel):
    """Minimal info about the user who created the oferta."""

    id: UUID
    email: str
    nombre: str
    apellido: str
    ong: str


class OfertaResponse(BaseModel):
    """Oferta returned by the Cloud API."""

    model_config = {"from_attributes": True}

    id: UUID
    pedido_id: UUID
    user_id: UUID
    descripcion: str
    monto_ofrecido: Optional[float] = None
    estado: str
    created_at: datetime
    updated_at: datetime
    user: Optional[OfertaUserSummary] = None


class OfertaConfirmationResponse(BaseModel):
    """Payload returned when confirming an oferta realization."""

    message: str
    success: bool
    oferta_id: UUID
    oferta_estado: str
    pedido_id: UUID
    pedido_estado_anterior: str
    pedido_estado_nuevo: str
    confirmed_at: datetime


class OfertaCompromisoResponse(OfertaResponse):
    """Oferta that includes nested pedido information."""

    pedido: PedidoResponse
