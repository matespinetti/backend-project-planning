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
    proyectos_en_riesgo: int
    velocidad_completacion: float
    observaciones_vencidas_total: int


class MetricsProjectStageStatus(BaseModel):
    etapa_id: UUID
    nombre: str
    total_pedidos: int
    pedidos_completados: int
    pedidos_pendientes: int
    progreso_porcentaje: float
    dias_planificados: int
    dias_transcurridos: Optional[int] = None
    estado_salud: str
    dias_restantes: Optional[int] = None


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
    tasa_aceptacion: float


class MetricsCommitmentsResponse(BaseModel):
    total_pedidos: int
    pedidos_con_ofertas: int
    cobertura_ofertas_porcentaje: float
    tasa_aceptacion_porcentaje: float
    tiempo_respuesta_promedio_dias: Optional[float] = None
    top_contribuidores: List[MetricsCommitmentContributor]
    pedidos_por_tipo: Dict[str, int]
    cobertura_por_tipo: Dict[str, float]


class MetricsPerformanceResponse(BaseModel):
    tiempo_promedio_etapa_dias: float
    semanas_promedio_etapa: float
    tiempo_inicio_promedio_dias: Optional[float] = None
    proyectos_pendientes_mas_30_dias: int
    observaciones_total: int
    observaciones_resueltas: int
    observaciones_pendientes: int
    observaciones_vencidas: int
    tiempo_resolucion_observaciones_promedio_dias: float
    tasa_cumplimiento_observaciones: float
    tiempo_respuesta_promedio_pedido_dias: float
    distribucion_pedidos_por_tipo: Dict[str, int]
