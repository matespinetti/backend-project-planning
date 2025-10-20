from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from uuid import UUID

from app.schemas.etapa import EtapaCreate, EtapaResponse


class ProyectoCreate(BaseModel):
    """Schema for creating a proyecto."""

    titulo: str = Field(..., min_length=5, description="Project title")
    descripcion: str = Field(..., min_length=20, description="Project description")
    tipo: str = Field(..., min_length=1, description="Project type")
    pais: str = Field(..., description="Country")
    provincia: str = Field(..., description="Province/State")
    ciudad: str = Field(..., description="City")
    barrio: Optional[str] = Field(None, description="Neighborhood")
    etapas: List[EtapaCreate] = Field(..., description="Project stages")

    @field_validator("etapas")
    @classmethod
    def validate_etapas_not_empty(cls, v: List[EtapaCreate]) -> List[EtapaCreate]:
        """Validate at least one etapa exists."""
        if not v or len(v) == 0:
            raise ValueError("At least one etapa is required")

        # Validate dates for each etapa
        for etapa in v:
            etapa.validate_dates()

        return v


class ProyectoResponse(BaseModel):
    """Schema for proyecto response (from Cloud API)."""

    model_config = {"from_attributes": True}

    id: UUID
    titulo: str
    descripcion: str
    tipo: str
    pais: str
    provincia: str
    ciudad: str
    barrio: Optional[str] = None
    estado: str
    bonita_case_id: Optional[str] = None
    bonita_process_instance_id: Optional[int] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    etapas: List[EtapaResponse] = []


class ProyectoCreateResponse(BaseModel):
    """Schema for proyecto creation response with Bonita info."""

    proyecto: ProyectoResponse
    bonita_case_id: Optional[str] = None
    bonita_process_url: Optional[str] = None
    message: str
