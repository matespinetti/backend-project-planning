from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class MetricsDashboardResponse(BaseModel):
    proyectos_por_estado: Dict[str, int]
    total_proyectos: int
    proyectos_activos: int
    proyectos_listos_para_iniciar: int
    tasa_exito: float


class MetricsProjectStageStatus(BaseModel):
    etapa_id: UUID
    nombre: str
    total_pedidos: int
    pedidos_completados: int
    pedidos_pendientes: int
    progreso_porcentaje: float
    dias_planificados: int
    dias_transcurridos: int


class MetricsProjectTrackingResponse(BaseModel):
    proyecto_id: UUID
    titulo: str
    estado: str
    etapas: List[MetricsProjectStageStatus]
    total_pedidos: int
    pedidos_completados: int
    pedidos_pendientes: int
    progreso_global_porcentaje: float
    observaciones_pendientes: int
    observaciones_resueltas: int
    observaciones_vencidas: int
    puede_iniciar: bool


class MetricsCommitmentContributor(BaseModel):
    user_id: UUID
    nombre: str
    apellido: str
    ong: str
    ofertas_realizadas: int
    ofertas_aceptadas: int
    tasa_aceptacion: float


class MetricsCommitmentsResponse(BaseModel):
    total_pedidos: int
    pedidos_con_ofertas: int
    cobertura_ofertas_porcentaje: float
    total_ofertas: int
    ofertas_aceptadas: int
    ofertas_pendientes: int
    tasa_aceptacion_porcentaje: float
    # Puede venir null cuando no hay datos históricos suficientes
    tiempo_respuesta_promedio_dias: Optional[float] = None
    top_contribuidores: List[MetricsCommitmentContributor]
    valor_total_solicitado: float
    valor_total_comprometido: float


class MetricsPerformanceResponse(BaseModel):
    tiempo_promedio_etapa_dias: float
    tiempo_inicio_promedio_dias: float
    proyectos_pendientes_mas_30_dias: int
    observaciones_total: int
    observaciones_resueltas: int
    observaciones_pendientes: int
    observaciones_vencidas: int
    tiempo_resolucion_observaciones_promedio_dias: float
