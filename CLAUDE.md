ProjectPlanning FastAPI Backend - ENTREGA 1 & 2
Project Overview
You are building a FastAPI backend that serves as middleware between a Next.js frontend and Bonita BPM. This initial version focuses on project creation which will start a Bonita process instance.
Current Scope (ENTREGA 1 & 2):

Single endpoint: POST /api/v1/projects
Create project with nested etapas and pedidos
Store in PostgreSQL database
Initialize Bonita process instance
Return project data with Bonita process information

Tech Stack

Framework: FastAPI
Package Manager: uv (modern Python package manager)
Server: Uvicorn
Database: PostgreSQL
ORM: SQLAlchemy 2.0
Validation: Pydantic v2
HTTP Client: httpx (for Bonita API calls)
Deployment: Docker ready

Folder Structure
project-planning-api/
├── pyproject.toml # uv configuration with dependencies
├── uv.lock
├── Dockerfile
├── docker-compose.yml # PostgreSQL + API
├── .env.example
├── .env
├── README.md
│
├── app/
│ ├── **init**.py
│ ├── main.py # FastAPI app initialization, CORS, routes
│ ├── config.py # Pydantic Settings for environment variables
│ │
│ ├── api/
│ │ ├── **init**.py
│ │ └── v1/
│ │ ├── **init**.py
│ │ ├── router.py # Main API router
│ │ └── endpoints/
│ │ ├── **init**.py
│ │ └── projects.py # POST /api/v1/projects endpoint
│ │
│ ├── core/
│ │ ├── **init**.py
│ │ └── bonita.py # Bonita BPM client class
│ │
│ ├── models/ # SQLAlchemy ORM models
│ │ ├── **init**.py
│ │ ├── proyecto.py # Proyecto table with Bonita tracking
│ │ ├── etapa.py # Etapa table (stages)
│ │ └── pedido.py # Pedido table (coverage requests)
│ │
│ ├── schemas/ # Pydantic schemas (request/response)
│ │ ├── **init**.py
│ │ ├── proyecto.py # ProyectoCreate, ProyectoResponse
│ │ ├── etapa.py # EtapaCreate, EtapaResponse
│ │ └── pedido.py # PedidoCreate, PedidoResponse
│ │
│ ├── crud/ # Database operations
│ │ ├── **init**.py
│ │ └── proyecto.py # CRUD operations for projects
│ │
│ └── db/
│ ├── **init**.py
│ ├── base.py # SQLAlchemy Base class
│ ├── session.py # Database session management
│ └── init_db.py # Create tables on startup
│
└── tests/
├── **init**.py
├── conftest.py
└── test_projects.py
Core Requirements

1. Data Schema Matching
   The API must accept data that exactly matches the Next.js Zod schema structure:
   From Next.js Frontend:
   typescript{
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
   tipo: string (economico|materiales|mano_obra),
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
   Key Points:

All IDs (proyecto, etapa, pedido) are auto-generated UUIDs by the database
Dates come as ISO strings, convert to Python date objects
Validate fecha_fin >= fecha_inicio in Pydantic
monto and cantidad must be positive when present
Etapas array must have at least 1 element

2. Database Design
   Tables:

proyectos - Main project table with Bonita tracking fields
etapas - Project stages (one-to-many with proyectos)
pedidos - Coverage requests (one-to-many with etapas)

Important Fields:

All tables use UUID primary keys (auto-generated with uuid.uuid4())
proyectos.id - UUID primary key
proyectos.bonita_case_id - Store Bonita case ID (string)
proyectos.bonita_process_instance_id - Store process instance ID (integer)
proyectos.estado - Enum: borrador, en_planificacion, buscando_financiamiento, completo, en_ejecucion
etapas.id - UUID primary key
etapas.proyecto_id - UUID foreign key to proyectos
pedidos.id - UUID primary key
pedidos.etapa_id - UUID foreign key to etapas

Relationships:

Use SQLAlchemy relationships with back_populates
Cascade deletes: delete project → delete etapas → delete pedidos
Use from_attributes = True in Pydantic for ORM mode
Use PostgreSQL UUID type (PGUUID with as_uuid=True)

3. Bonita BPM Integration
   Bonita REST API Flow:

Login - POST /loginservice to get JSESSIONID cookie
Get Process Definition - GET /API/bpm/process?p=0&c=100&f=name={process_name}
Start Process - POST /API/bpm/process/{processId}/instantiation
Set Variables (if needed) - PUT /API/bpm/caseVariable/{caseId}/{variableName}

BonitaClient Class Must:

Handle authentication and session management
Store session cookie for subsequent requests
Find process definition by name (e.g., "ProjectPlanning")
Start process instance with initial variables
Return case ID and process instance ID
Handle errors gracefully (log and raise appropriate exceptions)

Variables to Send to Bonita:
python{
"titulo": proyecto.titulo,
"descripcion": proyecto.descripcion,
"tipo": proyecto.tipo,
"pais": proyecto.pais,
"num_etapas": len(proyecto.etapas),
"proyecto_id": proyecto.id # DB ID for reference
} 4. API Endpoint Behavior
POST /api/v1/projects
Request Flow:

Receive JSON payload from Next.js
Validate with Pydantic (ProyectoCreate schema)
Start database transaction
Create Proyecto record (estado = "en_planificacion")
Create Etapa records (convert ISO strings to dates)
Create Pedido records for each etapa
Commit transaction
Initialize Bonita process with project data
Update proyecto with bonita_case_id and bonita_process_instance_id
Return full proyecto with nested etapas/pedidos + Bonita info

Response Format:
json{
"proyecto": {
"id": 1,
"titulo": "...",
"descripcion": "...",
"bonita_case_id": "...",
"estado": "en_planificacion",
"fecha_creacion": "...",
"etapas": [...]
},
"bonita_case_id": "...",
"bonita_process_url": "http://bonita:8080/bonita/portal/...",
"message": "Proyecto creado exitosamente e iniciado en Bonita"
}
Error Handling:

422: Validation errors (from Pydantic)
500: Database errors or Bonita connection failures
Always rollback database transaction if Bonita fails
Return detailed error messages for debugging

5. Configuration (Environment Variables)
   Required in .env:
   env# Database
   DATABASE_URL=postgresql://user:password@localhost:5432/projectplanning

# Bonita BPM

BONITA_URL=http://localhost:8080/bonita
BONITA_USERNAME=walter.bates
BONITA_PASSWORD=bpm
BONITA_PROCESS_NAME=ProjectPlanning
BONITA_PROCESS_VERSION=1.0

# API Settings

API_V1_PREFIX=/api/v1
PROJECT_NAME=ProjectPlanning API

# CORS

ALLOWED_ORIGINS=["http://localhost:3000"]
Use Pydantic Settings:

Create Settings class that reads from environment
Validate required variables on startup
Use @lru_cache to create singleton settings instance

6. Development Setup
   Dependencies to include in pyproject.toml:
   tomldependencies = [
   "fastapi>=0.115.0",
   "uvicorn[standard]>=0.30.0",
   "sqlalchemy>=2.0.0",
   "psycopg2-binary>=2.9.0", # PostgreSQL driver
   "pydantic>=2.0.0",
   "pydantic-settings>=2.0.0",
   "httpx>=0.27.0", # Async HTTP client for Bonita
   "python-dotenv>=1.0.0",
   ]
   Commands:
   bash# Install with uv
   uv sync

# Run dev server with auto-reload

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API docs

http://localhost:8000/docs 7. Docker Deployment
docker-compose.yml must include:

PostgreSQL service (persist data with volumes)
FastAPI service (depends on postgres)
Network configuration for services
Environment variables passed correctly
Health checks for postgres

Dockerfile must:

Use Python 3.11+ slim image
Install uv
Copy and install dependencies first (layer caching)
Copy application code
Expose port 8000
Run with uvicorn

Key Implementation Notes
Date Handling

Frontend sends: "2024-10-15" (ISO string)
Pydantic receives: string field
Convert to Python date object before storing in DB
Use datetime.fromisoformat() for conversion

UUID Handling

All IDs are auto-generated UUIDs by the database (uuid.uuid4())
Use PostgreSQL UUID type with sqlalchemy.dialects.postgresql.UUID
Set as_uuid=True to work with Python's uuid.UUID objects
No need for frontend to send IDs - backend generates them automatically

Nested Object Creation

Use SQLAlchemy relationships for automatic cascade
Create proyecto first (UUID auto-generated), then etapas with proyecto_id (UUID), then pedidos with etapa_id (UUID)
Let SQLAlchemy handle the relationship population
UUIDs are returned in the response for frontend tracking

Bonita Session Management

Bonita sessions expire after inactivity
Login before each process operation (or implement session caching)
Handle 401 responses by re-authenticating

CORS Configuration

Allow Next.js origin (localhost:3000 in dev)
Allow credentials if needed for future auth
Configure for production domains later

Testing Strategy
Manual Testing with Swagger UI:

Use /docs endpoint for interactive testing
Test validation errors (missing fields, invalid dates)
Test database persistence
Verify Bonita process starts correctly

Key Test Cases:

Create project with 1 etapa, 1 pedido
Create project with multiple etapas, multiple pedidos per etapa
Test fecha_fin < fecha_inicio (should fail validation)
Test missing required fields (should return 422)
Test Bonita unavailable (should rollback DB changes)

Success Criteria for ENTREGA 1 & 2
✅ Modelo de proceso Bonita - Process definition exists in Bonita
✅ Formulario web - Next.js form sends correctly formatted data
✅ API funcional - POST /api/v1/projects accepts data, stores in DB
✅ Integración Bonita - API starts process instance via Bonita API
✅ Variables seteadas - Project data passed to Bonita as variables
✅ Documentación - Swagger docs accessible and accurate
✅ Docker ready - Can run with docker-compose


Common Pitfalls to Avoid
❌ Don't forget to handle Bonita authentication properly
❌ Don't skip validation - use Pydantic validators
❌ Don't hardcode URLs or credentials - use environment variables
❌ Don't commit database transaction BEFORE calling Bonita - commit AFTER Bonita succeeds
❌ Don't forget CORS configuration - Next.js won't connect otherwise
❌ Don't skip error handling - log errors and return meaningful messages
❌ Don't forget to import UUID types from sqlalchemy.dialects.postgresql and uuid module

---

# Database Migrations with Alembic

The project uses **Alembic** for database schema migrations to support future functionality additions.

## Architecture

- **Async-compatible**: Alembic is configured to work with SQLAlchemy async engine
- **Auto-detection**: Can auto-generate migrations from model changes
- **Version control**: Migrations tracked in `alembic/versions/`
- **Environment-based**: Reads DATABASE_URL from `.env` file

## Configuration Files

### `alembic.ini`
- Main Alembic configuration
- Database URL is overridden by `alembic/env.py` (reads from `.env`)

### `alembic/env.py`
- Configured for async SQLAlchemy
- Imports all models from `app.models`
- Uses `async_engine_from_config` for async migrations
- Converts `postgresql://` → `postgresql+asyncpg://` automatically

## Common Commands

### Create a new migration (auto-generate from model changes)
```bash
uv run alembic revision --autogenerate -m "Add new field to proyecto"
```

### Create an empty migration (for manual SQL)
```bash
uv run alembic revision -m "Add custom index"
```

### Apply migrations (upgrade to latest)
```bash
uv run alembic upgrade head
```

### Rollback one migration
```bash
uv run alembic downgrade -1
```

### Show current migration status
```bash
uv run alembic current
```

### Show migration history
```bash
uv run alembic history
```

### Rollback to specific revision
```bash
uv run alembic downgrade <revision_id>
```

## Migration Workflow for New Features

1. **Modify models** in `app/models/`
   ```python
   # Example: Add new field to Proyecto model
   class Proyecto(Base):
       # ... existing fields ...
       presupuesto_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
   ```

2. **Generate migration**
   ```bash
   uv run alembic revision --autogenerate -m "Add presupuesto_total to proyectos"
   ```

3. **Review generated migration** in `alembic/versions/`
   - Check that the `upgrade()` function is correct
   - Check that the `downgrade()` function reverses changes properly

4. **Test migration locally**
   ```bash
   # Apply migration
   uv run alembic upgrade head

   # Test rollback
   uv run alembic downgrade -1

   # Re-apply
   uv run alembic upgrade head
   ```

5. **Commit migration file** to version control
   ```bash
   git add alembic/versions/xxxxx_add_presupuesto_total_to_proyectos.py
   git commit -m "Add presupuesto_total field to proyectos table"
   ```

## Initial Setup (Already Done)

The initial migration (`e33c335d25f7`) creates:
- `proyectos` table with Bonita tracking fields
- `etapas` table with FK to proyectos
- `pedidos` table with FK to etapas
- PostgreSQL ENUM types: `EstadoProyecto`, `TipoPedido`

## Important Notes

### Transaction Handling
- Migrations run in a transaction by default
- If migration fails, changes are rolled back automatically
- Test migrations in development before deploying to production

### Async Considerations
- The `env.py` file uses `asyncio.run()` to run async migrations
- Works seamlessly with async SQLAlchemy engine
- No changes needed for standard migration operations

### Production Deployment
```bash
# In production, run migrations before starting the app
uv run alembic upgrade head && uv run uvicorn app.main:app
```

### Docker Integration
Add to Dockerfile or docker-compose startup script:
```bash
# Run migrations on container startup
uv run alembic upgrade head
```

### Common Migration Patterns

#### Adding a nullable field
```python
def upgrade() -> None:
    op.add_column('proyectos', sa.Column('new_field', sa.String(100), nullable=True))

def downgrade() -> None:
    op.drop_column('proyectos', 'new_field')
```

#### Adding a required field (with default)
```python
def upgrade() -> None:
    # Add as nullable first
    op.add_column('proyectos', sa.Column('status', sa.String(50), nullable=True))
    # Set default value for existing rows
    op.execute("UPDATE proyectos SET status = 'active' WHERE status IS NULL")
    # Make it not nullable
    op.alter_column('proyectos', 'status', nullable=False)

def downgrade() -> None:
    op.drop_column('proyectos', 'status')
```

#### Creating an index
```python
def upgrade() -> None:
    op.create_index('ix_proyectos_titulo', 'proyectos', ['titulo'])

def downgrade() -> None:
    op.drop_index('ix_proyectos_titulo')
```

#### Adding a new ENUM value
```python
def upgrade() -> None:
    # PostgreSQL requires special handling for enum updates
    op.execute("ALTER TYPE estadoproyecto ADD VALUE 'cancelado'")

def downgrade() -> None:
    # WARNING: Removing enum values is complex in PostgreSQL
    # Usually requires recreating the enum type
    pass  # Document manual rollback if needed
```

## Troubleshooting

### "Target database is not up to date"
```bash
# Check current version
uv run alembic current

# Apply pending migrations
uv run alembic upgrade head
```

### "Can't locate revision identified by 'xxxxx'"
- Make sure all migration files are committed to git
- Check that `alembic/versions/` directory is not in `.gitignore`

### Migration conflicts (multiple developers)
```bash
# If two developers create migrations from same base:
# Use alembic merge to create a merge migration
uv run alembic merge -m "Merge migrations" <rev1> <rev2>
```

### Reset database (DEVELOPMENT ONLY - destroys data)
```bash
# Downgrade to base (remove all tables)
uv run alembic downgrade base

# Re-apply all migrations
uv run alembic upgrade head
```
