"""
Create realistic test data with REAL Bonita process instances.

This script calls the Proxy API endpoints to create **multiple** pending projects that:
1. Persist in Cloud API (get real UUIDs)
2. Start REAL Bonita processes (get real case_id and process_instance_id)
3. Create ofertas (some aceptadas, otras pendientes)

Usage:
    uv run python create_bonita_test_data.py

Requirements:
    - Proxy API running on localhost:8000 (or set PROXY_API_URL)
    - Cloud API accessible at configured URL
    - Bonita BPM running and accessible
    - Usuarios ya creados en la BD (ver credenciales abajo)
"""

import asyncio
import json
import logging
import os
from datetime import date, timedelta
from typing import Optional

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Usuarios existentes en la base (seed de Cloud API)
EXISTING_USERS = {
    "member_maria": {
        "email": "maria@barrionorte.org",
        "password": "Password123",
        "label": "Miembro (proyectos/ofertas)",
    },
    "member_pedro": {
        "email": "pedro@desarrollo.org",
        "password": "Password123",
        "label": "Miembro (proyectos/ofertas)",
    },
    "council_carlos": {
        "email": "consejo@rednacional.org",
        "password": "Password123",
        "label": "Council (aprobaciones/observaciones)",
    },
    "council_ana": {
        "email": "auditoria@rednacional.org",
        "password": "Password123",
        "label": "Council (auditoría/observaciones)",
    },
}

ACTIVE_MEMBER_USERS = ("member_maria", "member_pedro")


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


async def create_offer(
    client: ProxyAPIClient,
    pedido_id: str,
    descripcion: str,
    monto_ofrecido: Optional[float] = None,
) -> Optional[dict]:
    """Create an oferta for a pedido."""
    if not client.access_token:
        logger.error("Client not authenticated for creating oferta")
        return None

    url = f"{client.base_url}/api/v1/pedidos/{pedido_id}/ofertas"
    payload = {"descripcion": descripcion}
    if monto_ofrecido:
        payload["monto_ofrecido"] = monto_ofrecido

    resp = await client.client.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {client.access_token}"},
    )

    if resp.status_code in (200, 201):
        return resp.json()

    logger.error("Failed to create oferta on pedido %s: %s - %s", pedido_id, resp.status_code, resp.text[:300])
    return None


async def evaluate_offer(client: ProxyAPIClient, oferta_id: str, decision: str) -> Optional[dict]:
    """Evaluate (accept/reject) an oferta via Bonita user task."""
    if decision not in ("accept", "reject"):
        logger.error("Decision must be accept or reject")
        return None

    url = f"{client.base_url}/api/v1/ofertas/{oferta_id}/evaluate"
    payload = {"decision": decision}

    resp = await client.client.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {client.access_token}"},
    )

    if resp.status_code == 200:
        return resp.json()

    logger.error("Failed to evaluate oferta %s: %s - %s", oferta_id, resp.status_code, resp.text[:300])
    return None


async def create_observacion(client: ProxyAPIClient, project_id: str, descripcion: str) -> Optional[dict]:
    """Create an observacion (council) for a project."""
    url = f"{client.base_url}/api/v1/projects/{project_id}/observaciones"
    payload = {"descripcion": descripcion}

    resp = await client.client.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {client.access_token}"},
    )

    if resp.status_code in (200, 201):
        return resp.json()

    logger.error("Failed to create observacion on project %s: %s - %s", project_id, resp.status_code, resp.text[:300])
    return None


async def resolve_observacion(client: ProxyAPIClient, observacion_id: str, respuesta: str) -> Optional[dict]:
    """Resolve an observacion via Bonita SolveObservation task."""
    url = f"{client.base_url}/api/v1/observaciones/{observacion_id}/resolve"
    payload = {"respuesta": respuesta}

    resp = await client.client.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {client.access_token}"},
    )

    if resp.status_code == 200:
        return resp.json()

    logger.error("Failed to resolve observacion %s: %s - %s", observacion_id, resp.status_code, resp.text[:300])
    return None


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


def _flatten_pedidos(proyecto: dict) -> list[dict]:
    """Return a flat list of pedidos with etapa context."""
    pedidos: list[dict] = []
    for etapa in proyecto.get("etapas", []) or []:
        for pedido in etapa.get("pedidos", []) or []:
            pedidos.append(
                {
                    "id": pedido.get("id"),
                    "tipo": pedido.get("tipo"),
                    "descripcion": pedido.get("descripcion"),
                    "etapa_id": etapa.get("id"),
                    "etapa_nombre": etapa.get("nombre"),
                }
            )
    return pedidos


async def main():
    """Main execution flow."""
    print("=" * 80)
    print("🌱 CREATE BONITA TEST DATA WITH REAL PROCESS INSTANCES")
    print("=" * 80)

    base_url = os.getenv("PROXY_API_URL", "http://localhost:8000")
    print(f"Using Proxy API base URL: {base_url}")

    # Create clients per user
    clients = {key: ProxyAPIClient(base_url=base_url) for key in EXISTING_USERS}
    users_summary = {
        key: {
            "email": data["email"],
            "label": data["label"],
            "projects": [],
            "offers_made": [],
            "offers_evaluated": [],
        }
        for key, data in EXISTING_USERS.items()
    }

    try:
        # Authenticate only member users (council users remain listed but unused in seed)
        logger.info("Authenticating member users...")
        for user_key in ACTIVE_MEMBER_USERS:
            data = EXISTING_USERS[user_key]
            ok = await clients[user_key].login(email=data["email"], password=data["password"])
            if not ok:
                raise RuntimeError(f"Authentication failed for {data['email']}")
            logger.info("   %s logged in (%s)", data["email"], data["label"])

        # Project scenarios
        project_scenarios = [
            {
                "name": "Red de Agua Segura",
                "owner": "member_maria",
                "payload": {
                    "titulo": "Red de Agua Segura",
                    "descripcion": "Instalación de sistema de agua potable y distribución comunitaria para 12 barrios.",
                    "tipo": "Infraestructura Social",
                    "pais": "Argentina",
                    "provincia": "Chaco",
                    "ciudad": "Resistencia",
                    "barrio": "Barrio Esperanza",
                    "etapas": [
                        {
                            "nombre": "Perforación y bombeo",
                            "descripcion": "Perforación de pozo, bomba sumergible y tablero eléctrico.",
                            "fecha_inicio": date.today().isoformat(),
                            "fecha_fin": (date.today() + timedelta(days=60)).isoformat(),
                            "pedidos": [
                                {
                                    "tipo": "economico",
                                    "descripcion": "Financiamiento para perforación y compra de bomba",
                                    "monto": 220000.0,
                                    "moneda": "ARS",
                                },
                                {
                                    "tipo": "materiales",
                                    "descripcion": "Caños tricapa para impulsión y distribución",
                                    "cantidad": 180,
                                    "unidad": "metros",
                                },
                            ],
                        },
                        {
                            "nombre": "Distribución comunitaria",
                            "descripcion": "Tanques, clorador y conexiones domiciliarias básicas.",
                            "fecha_inicio": (date.today() + timedelta(days=61)).isoformat(),
                            "fecha_fin": (date.today() + timedelta(days=130)).isoformat(),
                            "pedidos": [
                                {
                                    "tipo": "equipamiento",
                                    "descripcion": "Tanques elevados y clorador automático",
                                    "cantidad": 2,
                                    "unidad": "sets",
                                },
                                {
                                    "tipo": "mano_obra",
                                    "descripcion": "Instaladores sanitarios matriculados",
                                    "cantidad": 4,
                                    "unidad": "personas",
                                },
                            ],
                        },
                    ],
                },
                "offers": [
                    {
                        "pedido_index": 0,
                        "user": "member_pedro",
                        "descripcion": "Financio 60% perforación y bomba con entrega en 10 días",
                        "monto": 132000.0,
                        "decision": "accept",
                        "decider": "member_maria",
                    },
                    {
                        "pedido_index": 1,
                        "user": "member_pedro",
                        "descripcion": "Donación parcial de caños tricapa certificados",
                        "monto": None,
                        "decision": None,
                        "decider": None,
                    },
                ],
            },
            {
                "name": "Centro de Salud Modular",
                "owner": "member_pedro",
                "payload": {
                    "titulo": "Centro de Salud Modular",
                    "descripcion": "Construcción de consultorios modulares para atención primaria y vacunatorio.",
                    "tipo": "Salud",
                    "pais": "Argentina",
                    "provincia": "Buenos Aires",
                    "ciudad": "Moreno",
                    "barrio": "Villa Trujui",
                    "etapas": [
                        {
                            "nombre": "Fundaciones y plataforma",
                            "descripcion": "Movimiento de suelo, platea de hormigón y acometidas sanitarias.",
                            "fecha_inicio": date.today().isoformat(),
                            "fecha_fin": (date.today() + timedelta(days=50)).isoformat(),
                            "pedidos": [
                                {
                                    "tipo": "economico",
                                    "descripcion": "Platea de hormigón H21 y nivelación de terreno",
                                    "monto": 180000.0,
                                    "moneda": "ARS",
                                },
                            ],
                        },
                        {
                            "nombre": "Módulos y terminaciones",
                            "descripcion": "Montaje modular, instalaciones eléctricas y terminaciones sanitarias.",
                            "fecha_inicio": (date.today() + timedelta(days=51)).isoformat(),
                            "fecha_fin": (date.today() + timedelta(days=120)).isoformat(),
                            "pedidos": [
                                {
                                    "tipo": "materiales",
                                    "descripcion": "Paneles sándwich y aberturas DVH",
                                    "cantidad": 40,
                                    "unidad": "paneles",
                                },
                                {
                                    "tipo": "transporte",
                                    "descripcion": "Traslado de módulos desde depósito central",
                                    "cantidad": 3,
                                    "unidad": "viajes",
                                },
                            ],
                        },
                    ],
                },
                "offers": [
                    {
                        "pedido_index": 0,
                        "user": "member_maria",
                        "descripcion": "Aporte del 50% del hormigón con certificación IRAM",
                        "monto": 90000.0,
                        "decision": None,
                        "decider": None,
                    },
                    {
                        "pedido_index": 2,
                        "user": "member_maria",
                        "descripcion": "Logística de transporte de módulos en 3 viajes",
                        "monto": None,
                        "decision": "accept",
                        "decider": "member_pedro",
                    },
                ],
            },
        ]

        created_data = []

        for scenario in project_scenarios:
            owner_client = clients[scenario["owner"]]
            logger.info("\nCreating project: %s", scenario["name"])
            project_response = await owner_client.create_project(scenario["payload"])

            if not project_response:
                logger.error("❌ Failed to create project %s", scenario["name"])
                continue

            await print_project_info(project_response)
            proyecto = project_response.get("proyecto", {})
            pedidos = _flatten_pedidos(proyecto)
            users_summary[scenario["owner"]]["projects"].append(proyecto.get("id"))

            project_summary = {
                "name": scenario["name"],
                "project_id": proyecto.get("id"),
                "bonita_case_id": proyecto.get("bonita_case_id") or project_response.get("bonita_case_id"),
                "offers": [],
            }

            # Create offers
            for offer_plan in scenario.get("offers", []):
                if offer_plan["pedido_index"] >= len(pedidos):
                    logger.warning("Pedido index %s out of range for project %s", offer_plan["pedido_index"], scenario["name"])
                    continue
                pedido = pedidos[offer_plan["pedido_index"]]
                offer_client = clients[offer_plan["user"]]
                oferta = await create_offer(
                    client=offer_client,
                    pedido_id=pedido["id"],
                    descripcion=offer_plan["descripcion"],
                    monto_ofrecido=offer_plan["monto"],
                )
                if not oferta:
                    continue

                oferta_id = oferta.get("id") or oferta.get("oferta", {}).get("id")
                oferta_estado = oferta.get("estado") or oferta.get("oferta", {}).get("estado")
                logger.info("Oferta creada en pedido %s (%s): %s", pedido["id"], pedido["tipo"], oferta_id)

                users_summary[offer_plan["user"]]["offers_made"].append(
                    {
                        "oferta_id": oferta_id,
                        "project_id": proyecto.get("id"),
                        "pedido_id": pedido["id"],
                        "pedido_tipo": pedido["tipo"],
                    }
                )

                if offer_plan.get("decision") and oferta_id:
                    decider_client = clients[offer_plan["decider"]]
                    evaluated = await evaluate_offer(decider_client, oferta_id=oferta_id, decision=offer_plan["decision"])
                    if evaluated:
                        oferta_estado = evaluated.get("estado") or evaluated.get("oferta", {}).get("estado") or oferta_estado
                        logger.info("Oferta %s evaluada (%s)", oferta_id, oferta_estado)
                        users_summary[offer_plan["decider"]]["offers_evaluated"].append(
                            {
                                "oferta_id": oferta_id,
                                "project_id": proyecto.get("id"),
                                "decision": offer_plan["decision"],
                            }
                        )

                project_summary["offers"].append(
                    {
                        "oferta_id": oferta_id,
                        "pedido_id": pedido["id"],
                        "pedido_tipo": pedido["tipo"],
                        "estado": oferta_estado,
                        "decision": offer_plan.get("decision"),
                    }
                )

            created_data.append(project_summary)

        # Persist summary to disk
        output_file = "bonita_seed_data.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "projects": created_data,
                    "users": users_summary,
                },
                f,
                indent=2,
                default=str,
            )
        logger.info("\n💾 Seed summary saved to: %s", output_file)

        # Quick recap
        print("\n=== SEED SUMMARY ===")
        for item in created_data:
            print(f"- {item['name']} | Project: {item['project_id']} | Bonita case: {item['bonita_case_id']}")
            print(f"  Ofertas: {len(item['offers'])}")
        print("\n=== USERS ACTIVITY ===")
        for key, info in users_summary.items():
            print(f"- {info['email']} ({info['label']})")
            print(f"  Proyectos creados: {len(info['projects'])} -> {info['projects']}")
            print(f"  Ofertas creadas: {len(info['offers_made'])}")
            for off in info["offers_made"]:
                print(f"    • {off['oferta_id']} on proyecto {off['project_id']} (pedido {off['pedido_id']} - {off['pedido_tipo']})")
            print(f"  Ofertas evaluadas: {len(info['offers_evaluated'])}")
            for ev in info["offers_evaluated"]:
                print(f"    • {ev['oferta_id']} on proyecto {ev['project_id']} (decision: {ev['decision']})")
        print("====================\n")

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
    finally:
        for cli in clients.values():
            await cli.aclose()


if __name__ == "__main__":
    asyncio.run(main())
