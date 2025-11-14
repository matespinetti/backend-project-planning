from __future__ import annotations

from app.core.cloud_client.auth import CloudAuthClientMixin
from app.core.cloud_client.metrics import CloudMetricsClientMixin
from app.core.cloud_client.pedidos import CloudPedidoClientMixin
from app.core.cloud_client.projects import CloudProjectClientMixin

__all__ = ["CloudAPIClient"]


class CloudAPIClient(
    CloudAuthClientMixin,
    CloudProjectClientMixin,
    CloudPedidoClientMixin,
    CloudMetricsClientMixin,
):
    """
    Aggregates individual domain mixins into a single facade to keep
    endpoint-specific logic modular while exposing one client to the app.
    """

    pass
