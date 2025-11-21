"""
Create realistic test data with REAL Bonita process instances.

This script calls the Proxy API endpoints to create pending projects that:
1. Persist in Cloud API (get real UUIDs)
2. Start REAL Bonita processes (get real case_id and process_instance_id)
3. Can be used for testing offer acceptance flows

Usage:
    uv run python create_bonita_test_data.py

Requirements:
    - Proxy API running on localhost:8000
    - Cloud API accessible at configured URL
    - Bonita BPM running and accessible
    - Test user credentials in Cloud API
"""

import asyncio
import json
import logging
from datetime import date, timedelta
from typing import Optional

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ProxyAPIClient:
    """Async client for the Proxy API (coordinating Cloud API + Bonita)."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        self.access_token: Optional[str] = None

    async def register_user(self, email: str, password: str, nombre: str, apellido: str, ong: str):
        """Register a new test user via Cloud API."""
        url = f"{self.base_url}/api/v1/auth/register"
        payload = {
            "email": email,
            "password": password,
            "nombre": nombre,
            "apellido": apellido,
            "ong": ong,
        }
        try:
            resp = await self.client.post(url, json=payload)
            if resp.status_code == 201:
                logger.info(f"✅ User registered: {email}")
                return resp.json()
            else:
                logger.warning(f"User registration failed: {resp.status_code} - {resp.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None

    async def login(self, email: str, password: str) -> bool:
        """Authenticate and get access token."""
        url = f"{self.base_url}/api/v1/auth/login"
        payload = {"email": email, "password": password}
        try:
            resp = await self.client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("access_token")
                logger.info(f"✅ Logged in as: {email}")
                return True
            else:
                logger.error(f"Login failed: {resp.status_code} - {resp.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"Error logging in: {e}")
            return False

    async def create_project(self, proyecto_data: dict) -> Optional[dict]:
        """Create a project with real Bonita process."""
        if not self.access_token:
            logger.error("Not authenticated - call login() first")
            return None

        url = f"{self.base_url}/api/v1/projects"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            logger.info(f"Creating proyecto: {proyecto_data.get('titulo', 'Untitled')}")
            resp = await self.client.post(url, json=proyecto_data, headers=headers)

            if resp.status_code == 201:
                data = resp.json()
                logger.info(f"✅ Project created successfully!")
                return data
            else:
                logger.error(f"Project creation failed: {resp.status_code}")
                logger.error(f"   Response: {resp.text[:500]}")
                return None
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None

    async def aclose(self):
        """Close the async client."""
        await self.client.aclose()


async def create_pending_project(client: ProxyAPIClient) -> Optional[dict]:
    """
    Create a realistic PENDING project with real Bonita process.

    This project will:
    - Be in 'pendiente' state (waiting for financing)
    - Have 2 etapas (stages)
    - Have multiple pedidos (requests) for financing
    - Have a REAL Bonita case_id for testing offer acceptance
    """
    proyecto_data = {
        "titulo": "Centro Comunitario Testeable",
        "descripcion": "Centro comunitario con salón multiuso y cocina para 250 familias. Proyecto de demostración para testing.",
        "tipo": "Infraestructura Social",
        "pais": "Argentina",
        "provincia": "Buenos Aires",
        "ciudad": "La Plata",
        "barrio": "Barrio Norte Test",
        "etapas": [
            {
                "nombre": "Fundaciones y Estructura",
                "descripcion": "Excavación, cimientos y estructura de hormigón armado para la base del centro",
                "fecha_inicio": date.today().isoformat(),
                "fecha_fin": (date.today() + timedelta(days=90)).isoformat(),
                "pedidos": [
                    {
                        "tipo": "economico",
                        "descripcion": "Cemento, hierro, arena y piedra para cimientos",
                        "monto": 180000.0,
                        "moneda": "ARS",
                    },
                ],
            },
            {
                "nombre": "Construcción de Paredes y Techo",
                "descripcion": "Levantamiento de paredes de carga, instalación de techo y aberturas",
                "fecha_inicio": (date.today() + timedelta(days=91)).isoformat(),
                "fecha_fin": (date.today() + timedelta(days=180)).isoformat(),
                "pedidos": [
                    {
                        "tipo": "economico",
                        "descripcion": "Materiales para paredes y techo (ladrillos, cemento, hierro)",
                        "monto": 250000.0,
                        "moneda": "ARS",
                    },
                ],
            },
        ],
    }

    return await client.create_project(proyecto_data)


async def print_project_info(project_response: dict):
    """Pretty print the created project information."""
    if not project_response:
        logger.error("No project data to display")
        return

    proyecto = project_response.get("proyecto", {})
    bonita_case_id = project_response.get("bonita_case_id")
    bonita_process_url = project_response.get("bonita_process_url")

    print("\n" + "=" * 80)
    print("✅ PROJECT CREATED SUCCESSFULLY WITH REAL BONITA INTEGRATION!")
    print("=" * 80)

    print(f"\n📋 PROJECT DETAILS:")
    print(f"   ID:              {proyecto.get('id')}")
    print(f"   Título:          {proyecto.get('titulo')}")
    print(f"   Descripción:     {proyecto.get('descripcion')[:60]}...")
    print(f"   Tipo:            {proyecto.get('tipo')}")
    print(f"   Estado:          {proyecto.get('estado')}")
    print(f"   Ubicación:       {proyecto.get('ciudad')}, {proyecto.get('provincia')}, {proyecto.get('pais')}")
    print(f"   Creado:          {proyecto.get('created_at')}")

    print(f"\n🔄 BONITA BPM INTEGRATION:")
    print(f"   Case ID:         {bonita_case_id}")
    print(f"   Process Instance: {proyecto.get('bonita_process_instance_id')}")
    print(f"   Process URL:     {bonita_process_url}")

    print(f"\n📊 PROJECT STRUCTURE:")
    etapas = proyecto.get("etapas", [])
    print(f"   Total Etapas:    {len(etapas)}")

    for idx, etapa in enumerate(etapas, 1):
        pedidos = etapa.get("pedidos", [])
        print(f"\n   Etapa {idx}: {etapa.get('nombre')}")
        print(f"      ID:          {etapa.get('id')}")
        print(f"      Descrip:     {etapa.get('descripcion')[:50]}...")
        print(f"      Fechas:      {etapa.get('fecha_inicio')} to {etapa.get('fecha_fin')}")
        print(f"      Pedidos:     {len(pedidos)}")

        for pidx, pedido in enumerate(pedidos, 1):
            print(f"         {pidx}. {pedido.get('tipo').upper()}: {pedido.get('descripcion')[:40]}...")
            if pedido.get('monto'):
                print(f"            Monto: {pedido.get('monto')} {pedido.get('moneda')}")
            if pedido.get('cantidad'):
                print(f"            Cantidad: {pedido.get('cantidad')} {pedido.get('unidad')}")

    print("\n" + "=" * 80)
    print("\n📝 NEXT STEPS FOR TESTING OFFER ACCEPTANCE:")
    print("   1. Use this project ID for creating pending offers")
    print("   2. The Bonita case is ready to receive task inputs")
    print("   3. Test offer acceptance flows on PENDIENTE pedidos")
    print("   4. Monitor Bonita process progress in the portal")
    print("\n" + "=" * 80 + "\n")


async def main():
    """Main execution flow."""
    print("=" * 80)
    print("🌱 CREATE BONITA TEST DATA WITH REAL PROCESS INSTANCES")
    print("=" * 80)

    client = ProxyAPIClient(base_url="http://localhost:8000")

    try:
        # Step 1: Register a test user (or use existing)
        test_email = "testuser.bonita@example.com"
        test_password = "TestPassword123!"
        test_nombre = "Test"
        test_apellido = "Bonita"
        test_ong = "ONG Testing Bonita"

        logger.info("Step 1: Attempting to register test user...")
        user_result = await client.register_user(
            email=test_email,
            password=test_password,
            nombre=test_nombre,
            apellido=test_apellido,
            ong=test_ong,
        )

        if not user_result:
            logger.info("   (User likely already exists, will try login...)")

        # Step 2: Login with test user
        logger.info("\nStep 2: Authenticating...")
        authenticated = await client.login(email=test_email, password=test_password)

        if not authenticated:
            logger.error("❌ Authentication failed - cannot proceed")
            return

        # Step 3: Create pending project with real Bonita process
        logger.info("\nStep 3: Creating pending project with REAL Bonita process...")
        project_response = await create_pending_project(client)

        if project_response:
            await print_project_info(project_response)

            # Save to file for reference
            output_file = "test_project_data.json"
            with open(output_file, "w") as f:
                json.dump(project_response, f, indent=2, default=str)
            logger.info(f"\n💾 Project data saved to: {output_file}")
        else:
            logger.error("❌ Failed to create project")

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
