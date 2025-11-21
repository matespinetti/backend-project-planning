from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


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


class ObservacionProjectInfo(BaseModel):
    """Project metadata included in paginated observacion listings."""

    model_config = {"extra": "ignore"}

    id: UUID
    titulo: str
    estado: str


class ObservacionUserInfo(BaseModel):
    """Minimal representation of a council/executor user."""

    model_config = {"extra": "ignore"}

    id: UUID
    email: str
    ong: str
    nombre: str
    apellido: Optional[str] = None


class ObservacionListItem(ObservacionResponse):
    """Extended observacion entry returned on the global listing."""

    proyecto: Optional[ObservacionProjectInfo] = None
    council_user: Optional[ObservacionUserInfo] = None
    executor_user: Optional[ObservacionUserInfo] = None


class ObservacionesPaginatedResponse(BaseModel):
    """Paginated response for the GET /observaciones endpoint."""

    model_config = {"extra": "ignore"}

    items: List[ObservacionListItem]
    total: int
    page: int
    page_size: int
    pages: int
    total_pages: int

    @model_validator(mode="before")
    @classmethod
    def sync_page_fields(cls, data: object) -> object:
        """Ensure both pages and total_pages exist regardless of API naming."""
        if not isinstance(data, dict):
            return data

        pages = data.get("pages")
        total_pages = data.get("total_pages")

        if pages is None and total_pages is not None:
            data["pages"] = total_pages
        elif total_pages is None and pages is not None:
            data["total_pages"] = pages

        return data


class ObservacionResolveRequest(BaseModel):
    """Payload used when resolving an observacion."""

    respuesta: str = Field(
        ...,
        min_length=10,
        description="Respuesta del ejecutor (mínimo 10 caracteres)",
    )
