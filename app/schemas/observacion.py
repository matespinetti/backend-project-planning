from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ObservacionResponse(BaseModel):
    """Represents a council observation entry from the Cloud API."""

    id: UUID
    proyecto_id: UUID
    council_user_id: UUID
    descripcion: str
    estado: str
    fecha_limite: date
    respuesta: Optional[str] = None
    fecha_resolucion: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    council_user_email: Optional[str] = None
    council_user_ong: Optional[str] = None
    council_user_nombre: Optional[str] = None
