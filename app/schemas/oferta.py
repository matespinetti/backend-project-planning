from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.pedido import PedidoResponse


class OfertaCreate(BaseModel):
    """Payload for creating an oferta."""

    descripcion: str = Field(..., min_length=10)
    monto_ofrecido: Optional[float] = Field(None, gt=0)


class OfertaUpdate(BaseModel):
    """Payload for updating an oferta."""

    descripcion: Optional[str] = Field(None, min_length=10)
    monto_ofrecido: Optional[float] = Field(None, gt=0)


class OfertaEstadoFilter(str, Enum):
    """Allowed states for filtering personal ofertas."""

    pendiente = "pendiente"
    aceptada = "aceptada"
    rechazada = "rechazada"


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


class EtapaBasicInfo(BaseModel):
    """Minimal etapa information for nested pedido data."""

    model_config = {"from_attributes": True, "extra": "ignore"}

    id: Optional[UUID] = None
    nombre: Optional[str] = None
    estado: Optional[str] = None


class ProyectoBasicInfo(BaseModel):
    """Minimal project information to support future nested responses."""

    id: UUID
    titulo: str


class PedidoDetailedInfo(BaseModel):
    """Pedido with nested etapa info for richer oferta responses."""

    model_config = {"from_attributes": True, "extra": "ignore"}

    id: Optional[UUID] = None
    tipo: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    monto: Optional[float] = None
    moneda: Optional[str] = None
    cantidad: Optional[int] = None
    unidad: Optional[str] = None
    etapa: Optional[EtapaBasicInfo] = None
    proyecto: Optional[ProyectoBasicInfo] = None


class OfertaDetailedResponse(OfertaResponse):
    """Oferta enriched with nested pedido (and etapa) details."""

    pedido: Optional[PedidoDetailedInfo] = None
