# ProjectPlanning FastAPI Proxy API - ENTREGA 2

## Project Overview
You are building a **FastAPI Proxy API** that serves as an orchestration layer between a Next.js frontend, Bonita BPM, and a Cloud Persistence API. This API does **NOT** persist data locally - it coordinates between external services following microservices architecture patterns.

### Current Scope (ENTREGA 2):

- **POST /api/v1/projects** - Create project and orchestrate Bonita + Cloud API
- **GET /api/v1/projects/{project_id}** - Proxy GET requests to Cloud API
- **No local database** - All persistence handled by Cloud API
- **Bonita BPM integration** - Start and manage process instances
- **Microservices pattern** - Coordinate between distributed services

## Architecture

```
┌─────────────┐
│  Next.js    │
│  Frontend   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  FastAPI Proxy API  │  ◄── This API (no database)
│  (Orchestration)    │
└──────┬──────┬───────┘
       │      │
       ▼      ▼
┌──────────┐ ┌────────────────────┐
│ Bonita   │ │  Cloud API         │
│ BPM      │ │  (Hostinger/Render)│
│          │ │  - PostgreSQL      │
│          │ │  - Data Persistence│
└──────────┘ └────────────────────┘
```

### Data Flow

**Creating a Project (Cloud API First):**
1. Frontend → Proxy API: Send proyecto data
2. Proxy API → Cloud API: POST - Persist proyecto (get real UUID, no Bonita info yet)
3. Proxy API → Bonita BPM: Start process with real project UUID
4. **If Bonita fails** → Proxy API → Cloud API: DELETE - Rollback project
5. **If Bonita succeeds** → Proxy API → Cloud API: PATCH - Update with Bonita case_id
6. Proxy API → Frontend: Return combined response

**Reading a Project:**
1. Frontend → Proxy API: Request proyecto by ID
2. Proxy API → Cloud API: Forward GET request
3. Proxy API → Frontend: Return proyecto data

## Tech Stack

- **Framework:** FastAPI
- **Package Manager:** uv (modern Python package manager)
- **Server:** Uvicorn
- **Validation:** Pydantic v2
- **HTTP Client:** httpx (for Bonita & Cloud API calls)
- **Deployment:** Docker ready (no database container)

## Folder Structure

```
project-planning-api/
├── pyproject.toml              # uv configuration with dependencies
├── uv.lock
├── Dockerfile
├── docker-compose.yml          # API only (no PostgreSQL)
├── .env.example
├── .env
├── README.md
├── CLAUDE.md                   # This file
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization, CORS, routes
│   ├── config.py               # Pydantic Settings for environment variables
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # Main API router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── projects.py # POST & GET /api/v1/projects endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bonita.py           # Bonita BPM client class
│   │   └── cloud_client.py     # Cloud Persistence API client
│   │
│   └── schemas/                # Pydantic schemas (request/response)
│       ├── __init__.py
│       ├── proyecto.py         # ProyectoCreate, ProyectoResponse
│       ├── etapa.py            # EtapaCreate, EtapaResponse
│       └── pedido.py           # PedidoCreate, PedidoResponse
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_projects.py
```

**Note:** No `app/db/`, `app/models/`, or `app/crud/` directories - all database operations are handled by the Cloud API.

## Core Requirements

### 1. Data Schema Matching

The API must accept data that exactly matches the Next.js Zod schema structure:

**From Next.js Frontend:**
```typescript
{
  titulo: string (min 5 chars),
  descripcion: string (min 20 chars),
  tipo: string (min 1 char),
  pais: string,
  provincia: string,
  ciudad: string,
  barrio?: string,
  etapas: [
    {
      nombre: string (min 3 chars),
      descripcion: string (min 10 chars),
      fecha_inicio: string (ISO date),
      fecha_fin: string (ISO date),
      pedidos: [
        {
          tipo: string (economico|materiales|mano_obra|transporte|equipamiento),
          descripcion: string (min 5 chars),
          monto?: number,
          moneda?: string,
          cantidad?: number,
          unidad?: string
        }
      ]
    }
  ]
}
```

**Key Points:**
- All IDs (proyecto, etapa, pedido) are auto-generated UUIDs by the **Cloud API**
- Dates come as ISO strings from frontend
- Validate `fecha_fin >= fecha_inicio` in Pydantic
- `monto` and `cantidad` must be positive when present
- `etapas` array must have at least 1 element

### 2. Cloud Persistence API Contract

**POST /api/v1/projects (to Cloud API)**

Request (Initial creation, before Bonita):
```json
{
  "titulo": "...",
  "descripcion": "...",
  "tipo": "...",
  "pais": "...",
  "provincia": "...",
  "ciudad": "...",
  "barrio": "...",
  "bonita_case_id": null,
  "bonita_process_instance_id": null,
  "estado": "en_planificacion",
  "etapas": [...]
}
```

Note: `bonita_case_id` and `bonita_process_instance_id` are `null` during initial creation since Bonita process hasn't started yet.

Response (201 Created):
```json
{
  "id": "uuid",
  "titulo": "...",
  "descripcion": "...",
  "tipo": "...",
  "pais": "...",
  "provincia": "...",
  "ciudad": "...",
  "barrio": "...",
  "estado": "en_planificacion",
  "bonita_case_id": "12345",
  "bonita_process_instance_id": 67890,
  "fecha_creacion": "2024-01-01T12:00:00",
  "fecha_actualizacion": "2024-01-01T12:00:00",
  "etapas": [
    {
      "id": "uuid",
      "proyecto_id": "uuid",
      "nombre": "...",
      "descripcion": "...",
      "fecha_inicio": "2024-01-01",
      "fecha_fin": "2024-12-31",
      "pedidos": [
        {
          "id": "uuid",
          "etapa_id": "uuid",
          "tipo": "economico",
          "descripcion": "...",
          "monto": 1000.0,
          "moneda": "USD",
          "cantidad": null,
          "unidad": null
        }
      ]
    }
  ]
}
```

**GET /api/v1/projects/{project_id} (from Cloud API)**

Response (200 OK):
```json
{
  "id": "uuid",
  "titulo": "...",
  // ... same structure as POST response
}
```

Response (404 Not Found):
```json
{
  "detail": "Proyecto with id {project_id} not found"
}
```

**DELETE /api/v1/projects/{project_id} (from Cloud API)**

Used for rollback when Bonita process fails to start.

Response (204 No Content or 200 OK):
```
(Empty body - successful deletion)
```

Response (404 Not Found):
```json
{
  "detail": "Proyecto with id {project_id} not found"
}
```

Note: 404 is treated as success for rollback purposes (project doesn't exist = rollback successful).

**PATCH /api/v1/projects/{project_id} (to Cloud API)**

Used to update project with Bonita information after process starts successfully.

Request (Partial update):
```json
{
  "bonita_case_id": "12345",
  "bonita_process_instance_id": 67890
}
```

Response (200 OK):
```json
{
  "id": "uuid",
  "titulo": "...",
  "bonita_case_id": "12345",
  "bonita_process_instance_id": 67890,
  // ... rest of project data
}
```

Note: This is called AFTER Bonita succeeds to save the case_id in the database for future reference.

### 3. Bonita BPM Integration

**Bonita REST API Flow:**
1. Login - `POST /loginservice` to get JSESSIONID cookie
2. Get Process Definition - `GET /API/bpm/process?p=0&c=100&f=name={process_name}`
3. Start Process - `POST /API/bpm/process/{processId}/instantiation`
4. Set Variables (if needed) - `PUT /API/bpm/caseVariable/{caseId}/{variableName}`

**BonitaClient Class Must:**
- Handle authentication and session management
- Store session cookie for subsequent requests
- Find process definition by name (e.g., "ProjectPlanning")
- Start process instance with contract inputs
- Return case ID and process instance ID
- Handle errors gracefully (log and raise appropriate exceptions)

**Contract Inputs for Process Start:**
```python
{
    "project_id": "real-uuid-from-cloud-api"  # Real UUID from Cloud API
}
```

### 4. Cloud API Client

**CloudAPIClient Class:**
- Located in `app/core/cloud_client.py`
- Uses `httpx.AsyncClient` for HTTP requests
- Configurable timeout (default: 30s)
- Methods:
  - `create_project()` - POST to Cloud API with proyecto data (Bonita params optional)
  - `get_project()` - GET proyecto by ID from Cloud API
  - `delete_project()` - DELETE proyecto by ID (used for rollback)
  - `update_project_bonita_info()` - PATCH proyecto with Bonita case_id and process_instance_id
- Proper error handling and logging
- Async context manager support

**Key Features:**
- Sends full proyecto data to Cloud API (initially without Bonita info)
- Returns persisted proyecto with database-generated UUIDs
- Updates proyecto with Bonita info after process starts
- Supports rollback by deleting projects
- Handles network errors, timeouts, and HTTP errors
- Structured logging for debugging

### 5. API Endpoint Behavior

**POST /api/v1/projects**

Request Flow (Cloud API First, Then Bonita, Then Update):
1. Receive JSON payload from Next.js
2. Validate with Pydantic (ProyectoCreate schema)
3. **POST to Cloud API** → Get real project UUID (no Bonita info yet)
4. If Cloud API fails → Return 500, nothing to rollback
5. **Start Bonita BPM process** with real project UUID
6. If Bonita fails → **Rollback**: DELETE project from Cloud API
7. If rollback succeeds → Return 500 "Project was rolled back"
8. If rollback fails → Return 500 with project_id for manual cleanup
9. **PATCH Cloud API** → Update project with Bonita case_id and process_instance_id
10. If update fails → Log warning but continue (project exists, Bonita running)
11. Return combined response with all information

Response Format (201 Created):
```json
{
  "proyecto": {
    "id": "uuid",
    "titulo": "...",
    "descripcion": "...",
    "bonita_case_id": "12345",
    "estado": "en_planificacion",
    "fecha_creacion": "...",
    "etapas": [...]
  },
  "bonita_case_id": "12345",
  "bonita_process_url": "http://bonita:8080/bonita/portal/...",
  "message": "Proyecto creado exitosamente e iniciado en Bonita"
}
```

**GET /api/v1/projects/{project_id}**

Request Flow:
1. Receive project_id from request path
2. Forward GET request to Cloud API
3. If Cloud API returns 404 → Return 404
4. If Cloud API returns 200 → Return proyecto data
5. If Cloud API errors → Return 500

**Error Handling:**
- **422:** Validation errors (from Pydantic)
- **500:** Bonita connection failures, Cloud API failures
- **404:** Project not found in Cloud API (GET endpoint only)

Always log errors with full context for debugging and operations.

### 6. Additional Proxy Endpoints

Besides the original project orchestration endpoints, the proxy now exposes more Cloud API capabilities. Each route continues to be stateless: validate input with Pydantic, enforce authorization (ownership/creator checks) and forward to the Cloud Persistence API using the same JWT.

#### Usuarios
- **GET /api/v1/users/me** → Returns the authenticated profile (`id`, `email`, `nombre`, `apellido`, `ong`, `role`, timestamps). Simply forwards the call and returns whatever the Cloud API responds.

#### Pedidos
- **GET /api/v1/pedidos/{pedido_id}** → Fetches a single pedido with tipo/descripcion/estado/montos.
- **PATCH /api/v1/pedidos/{pedido_id}** → Updates optional fields (tipo, descripcion, monto, moneda, cantidad, unidad). Guardrails: only the project owner can edit and only when the pedido is `PENDIENTE`.

#### Ofertas
- **GET /api/v1/ofertas/{oferta_id}** → Retrieves full oferta detail from the Cloud API.
- **PATCH /api/v1/ofertas/{oferta_id}** → Allows the creator to change `descripcion` and `monto_ofrecido` while the oferta is `pendiente`.
- **DELETE /api/v1/ofertas/{oferta_id}** → Removes a pending oferta created by the authenticated user. Returns `204` on success.
- **GET /api/v1/ofertas/mis-ofertas** → Returns the enriched `OfertaDetailedResponse`, which embeds pedido + etapa info exactly as provided by the Cloud API. Ready to accept `page/page_size` whenever the upstream API supports it.
- **GET /api/v1/ofertas/mis-compromisos** → Still returns the current list schema. Pagination parameters will be proxied transparently once available upstream.

#### Etapas
- **GET /api/v1/etapas/{etapa_id}** → Fetches etapa metadata plus `pendientes_count`/`total_pedidos` counters so dashboards can show progress per etapa.

All these endpoints live in their respective routers (`app/api/v1/endpoints/...`) and extra orchestration/ownership checks are encapsulated in `app/services/pedido_service.py` and `app/services/oferta_service.py` to keep routers thin.

### 7. Configuration (Environment Variables)

Required in `.env`:

```env
# Cloud Persistence API (hosted on Hostinger/Render)
CLOUD_API_URL=https://your-cloud-api.example.com
CLOUD_API_TIMEOUT=30

# Bonita BPM
BONITA_URL=http://localhost:8080/bonita
BONITA_USERNAME=walter.bates
BONITA_PASSWORD=bpm
BONITA_PROCESS_NAME=ProjectPlanning
BONITA_PROCESS_VERSION=1.0

# API Settings
API_V1_PREFIX=/api/v1
PROJECT_NAME=ProjectPlanning Proxy API

# CORS - comma separated list of origins
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Use Pydantic Settings:**
- Create `Settings` class that reads from environment
- Validate required variables on startup
- Use `@lru_cache` to create singleton settings instance

### 8. Development Setup

**Dependencies in `pyproject.toml`:**
```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
]
```

**Commands:**
```bash
# Install with uv
uv sync

# Run dev server with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API docs
http://localhost:8000/docs
```

### 9. Docker Deployment

**docker-compose.yml** includes:
- FastAPI proxy service only (no PostgreSQL)
- Environment variables for Cloud API and Bonita
- Network configuration
- Restart policy

**Dockerfile must:**
- Use Python 3.11+ slim image
- Install uv
- Copy and install dependencies first (layer caching)
- Copy application code
- Expose port 8000
- Run with uvicorn

**Note:** No database migrations or initialization needed - this is a stateless proxy API.

## Key Implementation Notes

### Microservices Error Handling

**Bonita Fails:**
- Return 500 to frontend immediately
- Don't call Cloud API (no process to persist)
- Log error with full context

**Bonita Succeeds, Cloud API Fails:**
- Log error with Bonita case_id
- Return 500 with message including case_id for manual recovery
- Operations team can manually persist data using case_id

**Both Succeed:**
- Return 201 with full response
- Log success with both IDs

**Network Timeouts:**
- 20s timeout for Bonita (configured in BonitaClient)
- 30s timeout for Cloud API (configurable via env var)
- Proper error messages for each service

### Logging Strategy

**Structured Logging:**
- Log all external service calls (Bonita, Cloud API)
- Include request/response summaries for debugging
- Log latency for performance monitoring
- Clear error messages with context

**Example Log Messages:**
```python
logger.info(f"Starting Bonita process for proyecto: {proyecto_data.titulo}")
logger.info(f"Bonita process started. Case ID: {bonita_case_id}")
logger.info("Forwarding proyecto data to Cloud Persistence API")
logger.error(f"Cloud API persistence failed for Bonita case {bonita_case_id}")
```

### Service Orchestration Pattern

This API follows the **Orchestrator Pattern** where:
1. **Orchestrator** (this API) coordinates multiple services
2. **Services** (Bonita, Cloud API) are independent and decoupled
3. **Failure handling** is explicit and traceable
4. **Idempotency** considerations for retry logic (future enhancement)

### Date Handling

- Frontend sends: `"2024-10-15"` (ISO string)
- Pydantic receives: string field
- Cloud API handles conversion to database types
- Proxy API validates format but doesn't convert

### UUID Handling

- Cloud API generates all UUIDs (proyecto, etapa, pedido)
- Proxy API generates temporary UUID for Bonita contract (will be replaced)
- Use Python's `uuid.uuid4()` for temporary IDs
- Cloud API returns real UUIDs in response

### CORS Configuration

- Allow Next.js origin (localhost:3000 in dev)
- Allow credentials if needed for future auth
- Configure for production domains later

## Testing Strategy

**Manual Testing with Swagger UI:**
- Use `/docs` endpoint for interactive testing
- Test validation errors (missing fields, invalid dates)
- Test Bonita integration (verify process starts)
- Test Cloud API integration (verify data persists)

**Key Test Cases:**
1. Create project with 1 etapa, 1 pedido
2. Create project with multiple etapas, multiple pedidos per etapa
3. Test `fecha_fin < fecha_inicio` (should fail validation)
4. Test missing required fields (should return 422)
5. Test Bonita unavailable (should return 500)
6. Test Cloud API unavailable (should return 500 with Bonita case_id)
7. Test GET endpoint with valid ID
8. Test GET endpoint with non-existent ID (should return 404)

## Success Criteria for ENTREGA 2

✅ API acts as pure proxy (no local database)
✅ Bonita process starts correctly
✅ Cloud API receives full proyecto data
✅ Response includes both Bonita and Cloud API info
✅ All database dependencies removed
✅ Docker setup simplified (no PostgreSQL)
✅ Error handling follows microservices best practices
✅ Documentation updated completely
✅ GET endpoint proxies to Cloud API
✅ Proper logging and observability

## Common Pitfalls to Avoid

❌ Don't forget to handle Bonita authentication properly
❌ Don't skip validation - use Pydantic validators
❌ Don't hardcode URLs or credentials - use environment variables
❌ Don't forget CORS configuration - Next.js won't connect otherwise
❌ Don't skip error handling - log errors and return meaningful messages
❌ Don't forget to close httpx clients (use context managers)
❌ Don't ignore Cloud API errors - always log with Bonita case_id for recovery
❌ Don't start Bonita process before validation - validate first

---

## Future Enhancements (Post-ENTREGA 2)

- **Authentication:** Add JWT tokens or API keys for security
- **Retry Logic:** Implement exponential backoff for failed Cloud API calls
- **Circuit Breaker:** Protect against cascading failures
- **Rate Limiting:** Protect against abuse
- **Caching:** Cache frequently accessed proyectos from Cloud API
- **Webhooks:** Receive updates from Bonita when process state changes
- **Metrics:** Prometheus metrics for service health monitoring
- **Tracing:** Distributed tracing with OpenTelemetry

---

## Architecture Decision Records

### ADR-001: Why Proxy Pattern Instead of Database?

**Context:** Original design had local PostgreSQL database. Requirements changed to use cloud-hosted persistence API.

**Decision:** Convert to pure proxy API that orchestrates between Bonita and Cloud API.

**Rationale:**
- **Separation of Concerns:** This API focuses on BPM integration, Cloud API handles persistence
- **Scalability:** Stateless proxy can scale horizontally without database concerns
- **Simplicity:** Fewer dependencies, easier deployment
- **Cost:** No database infrastructure to maintain
- **Flexibility:** Can swap Cloud API implementation without changing this proxy

**Consequences:**
- ✅ Simpler deployment (no database migrations)
- ✅ Better separation of concerns
- ✅ Easier to test (mock external services)
- ⚠️ Depends on Cloud API availability
- ⚠️ Network latency for every operation

### ADR-002: Cloud API First, Then Bonita (REVISED)

**Context:** Need to decide order of service calls. Originally chose Bonita first, but requirement changed: Bonita needs real project UUID from database.

**Decision:** Persist in Cloud API first (get real UUID), then start Bonita process with that UUID.

**Rationale:**
- Bonita process requires the real project ID from the database
- Cloud API is easier to rollback (simple DELETE operation)
- If Bonita fails, we can cleanly delete the project from Cloud API
- Database is the source of truth for project IDs
- Rollback is straightforward and reliable

**Consequences:**
- ✅ Bonita receives real project UUID (not temporary ID)
- ✅ Clean rollback mechanism (DELETE from Cloud API)
- ✅ Database is source of truth for IDs
- ✅ No orphaned Bonita processes without corresponding data
- ⚠️ Project briefly exists in Cloud API before Bonita starts
- ⚠️ If rollback fails, manual cleanup needed (rare, but logged)

---

**End of Documentation**
