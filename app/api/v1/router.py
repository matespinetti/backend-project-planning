from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    etapas,
    metrics,
    observaciones,
    ofertas,
    pedidos,
    projects,
    users,
)

api_router = APIRouter()

# Include auth endpoints
api_router.include_router(auth.router, tags=["auth"])

# Include metrics endpoints
api_router.include_router(metrics.router, tags=["metrics"])

# Include users endpoints
api_router.include_router(users.router, tags=["users"])

# Include etapas endpoints
api_router.include_router(etapas.router, tags=["etapas"])

# Include pedidos endpoints
api_router.include_router(pedidos.router, tags=["pedidos"])

# Include ofertas endpoints
api_router.include_router(ofertas.router, tags=["ofertas"])

# Include observaciones endpoints
api_router.include_router(observaciones.router, tags=["observaciones"])

# Include project endpoints
api_router.include_router(projects.router, tags=["projects"])
