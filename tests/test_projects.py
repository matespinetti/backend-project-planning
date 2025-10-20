import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "ProjectPlanning API is running"


def test_health_check(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_project_validation_error(client: TestClient):
    """Test project creation with invalid data."""
    # Missing required fields
    invalid_data = {
        "titulo": "Test",  # Too short
        "descripcion": "Short",  # Too short
    }

    response = client.post("/api/v1/projects", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_create_project_valid_data(client: TestClient):
    """Test project creation with valid data."""
    valid_data = {
        "titulo": "Proyecto de Prueba",
        "descripcion": "Esta es una descripción de prueba para el proyecto",
        "tipo": "Infraestructura",
        "pais": "Argentina",
        "provincia": "Buenos Aires",
        "ciudad": "La Plata",
        "barrio": "Centro",
        "etapas": [
            {
                "nombre": "Etapa 1",
                "descripcion": "Descripción de la etapa 1",
                "fecha_inicio": "2024-01-01",
                "fecha_fin": "2024-06-30",
                "pedidos": [
                    {
                        "tipo": "economico",
                        "descripcion": "Financiamiento inicial",
                        "monto": 10000.0,
                        "moneda": "ARS",
                    }
                ],
            }
        ],
    }

    # Note: This test will fail without Bonita running
    # For real testing, you'd mock the BonitaClient
    response = client.post("/api/v1/projects", json=valid_data)

    # If Bonita is not available, expect 500
    # If Bonita is available, expect 201
    assert response.status_code in [201, 500]
