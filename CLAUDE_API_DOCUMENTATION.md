# ProjectPlanning Cloud Persistence API - Documentación Completa

**Versión:** 1.0.0
**Fecha de Entrega:** Octubre 2025

---

## Tabla de Contenidos

1. [Información del Grupo](#información-del-grupo)
2. [URLs de Servicios](#urls-de-servicios)
3. [Introducción](#introducción)
4. [Autenticación](#autenticación)
5. [Endpoints de Autenticación](#endpoints-de-autenticación)
6. [Endpoints de Usuarios](#endpoints-de-usuarios)
7. [Endpoints de Proyectos](#endpoints-de-proyectos)
8. [Endpoints de Etapas](#endpoints-de-etapas)
9. [Endpoints de Pedidos](#endpoints-de-pedidos)
10. [Endpoints de Pedidos - Nuevas Operaciones](#endpoints-de-pedidos---nuevas-operaciones)
11. [Endpoints de Ofertas](#endpoints-de-ofertas)
12. [Endpoints de Ofertas - Nuevas Operaciones](#endpoints-de-ofertas---nuevas-operaciones)
13. [Endpoints de Etapas - Nuevas Operaciones](#endpoints-de-etapas---nuevas-operaciones)
14. [Endpoints de Observaciones](#endpoints-de-observaciones)
15. [Endpoints de Métricas](#endpoints-de-métricas)
16. [Enumeraciones](#enumeraciones)
17. [Flujo Completo de Ejemplo](#flujo-completo-de-ejemplo)
18. [Códigos de Error](#códigos-de-error)
19. [Instrucciones para Pruebas](#instrucciones-para-pruebas)

---

## Información del Grupo

### Integrantes

| Nombre                            | Rol             | Email                         |
| --------------------------------- | --------------- | ----------------------------- |
| **Mateo Spinetti**                | [Desarrollador] | [mateospinetti1@gmail.com]    |
| **Luciano Equiel Wagner**         | [Desarrollador] | [lucianowagner2003@gmail.com] |
| **Matias Santiago Ramos Giacosa** | [Desarrollador] | [matiasramosgi@gmail.com]     |

### Universidad y Cátedra

-   **Universidad:** Facultad de informatica UNLP
-   **Materia:** Desarrollo de software en sistemas distribuidos
-   **Período:** 2025

---

## URLs de Servicios

### API Cloud Persistence (Producción)

**URL Base:** `https://project-planning-cloud-api.onrender.com`

**Acceso Directo:**

-   **API v1:** `https://project-planning-cloud-api.onrender.com/api/v1`
-   **Swagger/Documentación Interactiva:** `https://project-planning-cloud-api.onrender.com/docs`
-   **OpenAPI JSON:** `https://project-planning-cloud-api.onrender.com/openapi.json`
-   **Health Check:** `https://project-planning-cloud-api.onrender.com/health`

### Documentación Interactiva

Para explorar y probar todos los endpoints **sin necesidad de instalar nada**:

**[Abre Swagger UI aquí](https://project-planning-cloud-api.onrender.com/docs)**

En Swagger UI podrás:

-   Ver todos los endpoints disponibles
-   Probar cada endpoint directamente
-   Obtener automáticamente ejemplos de request/response
-   Ver códigos de error y documentación detallada

---

## Introducción

### ¿Qué es esta API?

La **ProjectPlanning Cloud Persistence API** es un servicio backend REST construido con **FastAPI** que gestiona toda la persistencia de datos del sistema ProjectPlanning. Esta API:

-   Maneja autenticación de usuarios con JWT
-   Gestiona proyectos con etapas anidadas
-   Administra pedidos (solicitudes de recursos)
-   Procesa ofertas de usuarios

### Características Principales

**Validación Pydantic** - Validación completa de entrada/salida
**JWT Authentication** - Tokens de acceso y refresco
**CORS Configurado** - Compatible con proxy API
**Docker** - Despliegue containerizado
**PostgreSQL 15+** - Base de datos relacional

### Stack Tecnológico

-   **Framework:** FastAPI
-   **Python:** 3.12+
-   **ORM:** SQLAlchemy 2.0 (async)
-   **Base de Datos:** PostgreSQL 15+
-   **Autenticación:** JWT con bcrypt
-   **Validación:** Pydantic v2
-   **Server:** Uvicorn
-   **Deployment:** Docker + docker-compose

---

## Autenticación

### Flujo de Autenticación JWT

Esta API usa **JWT (JSON Web Tokens)** para autenticación:

#### Paso 1: Registro

```
POST /api/v1/auth/register
→ Recibe: email, password, nombre, apellido, ong, role
→ Devuelve: usuario creado
```

#### Paso 2: Login

```
POST /api/v1/auth/login
→ Recibe: email, password
→ Devuelve: access_token (15 min) + refresh_token (24h)
```

#### Paso 3: Usar Token

Incluye el `access_token` en todas las peticiones protegidas:

```
Authorization: Bearer {access_token}
```

#### Paso 4: Refrescar Token (cuando expira)

```
POST /api/v1/auth/refresh
→ Recibe: refresh_token
→ Devuelve: nuevo access_token + refresh_token
```

### Headers Requeridos

Para endpoints protegidos, incluye:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
```

### Información de Tokens

| Propiedad                | Valor               |
| ------------------------ | ------------------- |
| **Algoritmo**            | HS256               |
| **Access Token Expiry**  | 15 minutos          |
| **Refresh Token Expiry** | 24 horas (1440 min) |
| **Tipo de Token**        | Bearer              |

---

## Endpoints de Autenticación

### 1️⃣ Registrar Nuevo Usuario

Crea una nueva cuenta de usuario en el sistema.

**Método:** `POST`
**Ruta:** `/api/v1/auth/register`
**Autenticación:** No requerida (público)
**Código de Respuesta:** `201 Created`

#### Parámetros

| Campo      | Tipo   | Requerido | Descripción                                              |
| ---------- | ------ | --------- | -------------------------------------------------------- |
| `email`    | string | Sí        | Email del usuario (debe ser único, formato válido)       |
| `password` | string | Sí        | Contraseña (mínimo 8 caracteres)                         |
| `nombre`   | string | Sí        | Nombre del usuario                                       |
| `apellido` | string | Sí        | Apellido del usuario                                     |
| `ong`      | string | Sí        | Nombre de organización                                   |
| `role`     | enum   | No        | Rol del usuario (`MEMBER` por defecto, o `COUNCIL`)      |

#### Body de Prueba

```json
{
	"email": "juan.perez@ong.com",
	"password": "SecurePassword123",
	"nombre": "Juan",
	"apellido": "Pérez",
	"ong": "ONG Solidaria",
	"role": "MEMBER"
}
```

#### Response Exitoso (201)

```json
{
	"id": "550e8400-e29b-41d4-a716-446655440000",
	"email": "juan.perez@ong.com",
	"nombre": "Juan",
	"apellido": "Pérez",
	"ong": "ONG Solidaria",
	"role": "MEMBER",
	"created_at": "2024-10-22T14:30:00+00:00",
	"updated_at": "2024-10-22T14:30:00+00:00"
}
```

#### Errores Posibles

| Código | Descripción                  | Ejemplo de Error                                                                                       | Solución                                                         |
| ------ | ---------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| `400`  | Email ya registrado          | `{"detail": "A user with this email already exists"}`                                                  | Usa un email diferente                                           |
| `400`  | Contraseña demasiado larga   | `{"detail": "Password cannot exceed 72 bytes in length"}`                                              | Usa una contraseña más corta                                     |
| `400`  | Datos de registro inválidos  | `{"detail": "Invalid registration data"}`                                                              | Revisa que todos los campos cumplan los requisitos               |
| `422`  | Error de validación Pydantic | `{"detail": [{"loc": ["body", "email"], "msg": "invalid email format", "type": "value_error.email"}]}` | Revisa el formato de los datos (email válido, campos requeridos) |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado - Sin instalación)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "POST /api/v1/auth/register"
3. Click "Try it out"
4. Rellena los campos con los datos del ejemplo
5. Click "Execute"

**Opción 2: cURL**

```bash
curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan.perez@ong.com",
    "password": "SecurePassword123",
    "nombre": "Juan",
    "apellido": "Pérez",
    "ong": "ONG Solidaria",
    "role": "MEMBER"
  }'
```

**Opción 3: Postman**

1. Nueva petición → POST
2. URL: `https://project-planning-cloud-api.onrender.com/api/v1/auth/register`
3. Tab "Body" → raw → JSON
4. Pega el JSON del ejemplo
5. Click "Send"

---

### 2️⃣ Login de Usuario

Obtiene los tokens JWT para acceder a endpoints protegidos.

**Método:** `POST`
**Ruta:** `/api/v1/auth/login`
**Autenticación:** No requerida (público)
**Código de Respuesta:** `200 OK`

#### Parámetros

| Campo      | Tipo   | Requerido | Descripción      |
| ---------- | ------ | --------- | ---------------- |
| `email`    | string | Sí        | Email registrado |
| `password` | string | Sí        | Contraseña       |

#### Body de Prueba

```json
{
	"email": "juan.perez@ong.com",
	"password": "SecurePassword123"
}
```

#### Response Exitoso (200)

```json
{
	"access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJlbWFpbCI6Imp1YW4ucGVyZXpAb25nLmNvbSIsInJvbGUiOiJNRU1CRVIiLCJleHAiOjE2OTc5ODk2MDB9.QWlDVGV1Q1U2QURNM0x1UWJCdGlRZWxXTG5pOEFBSUE=",
	"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJlbWFpbCI6Imp1YW4ucGVyZXpAb25nLmNvbSIsInJvbGUiOiJNRU1CRVIiLCJleHAiOjE2OTgwNzQ5MDB9.UzBNdjV0cExnMWV3M0hCTVFYOVNQYU5IWmFUVUFBQTA=",
	"token_type": "bearer"
}
```

#### Guardar Tokens

**Importante:** Guarda estos tokens en tu cliente (sesión, localStorage, etc.):

-   `access_token` → Usar para peticiones autenticadas (válido 15 min)
-   `refresh_token` → Guardar seguro para renovar tokens (válido 24h)

#### Errores Posibles

| Código | Descripción                  | Ejemplo de Error                                                                                   | Solución                                               |
| ------ | ---------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `401`  | Credenciales incorrectas     | `{"detail": "Incorrect email or password"}`                                                        | Verifica que el email y contraseña sean correctos      |
| `422`  | Error de validación Pydantic | `{"detail": [{"loc": ["body", "email"], "msg": "field required", "type": "value_error.missing"}]}` | Revisa que todos los campos requeridos estén presentes |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado - Sin instalación)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "POST /api/v1/auth/login"
3. Click "Try it out"
4. Rellena los campos con los datos del ejemplo
5. Click "Execute"
6. Copia el `access_token` de la respuesta

**Opción 2: cURL**

```bash
curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan.perez@ong.com",
    "password": "SecurePassword123"
  }'
```

**Guardar token en variable (bash):**

```bash
TOKEN=$(curl -s -X POST https://project-planning-cloud-api.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"juan.perez@ong.com","password":"SecurePassword123"}' \
  | jq -r '.access_token')

echo $TOKEN
```

---

### 3️⃣ Refrescar Token

Obtiene un nuevo `access_token` cuando el anterior expira.

**Método:** `POST`
**Ruta:** `/api/v1/auth/refresh`
**Autenticación:** No requerida (público)
**Código de Respuesta:** `200 OK`

#### Parámetros

| Campo           | Tipo   | Requerido | Descripción                 |
| --------------- | ------ | --------- | --------------------------- |
| `refresh_token` | string | Sí        | Token de refresco del login |

#### Body de Prueba

```json
{
	"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJlbWFpbCI6Imp1YW4ucGVyZXpAb25nLmNvbSIsInJvbGUiOiJNRU1CRVIiLCJleHAiOjE2OTgwNzQ5MDB9.UzBNdjV0cExnMWV3M0hCTVFYOVNQYU5IWmFUVUFBQTA="
}
```

#### Response Exitoso (200)

```json
{
	"access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJlbWFpbCI6Imp1YW4ucGVyZXpAb25nLmNvbSIsInJvbGUiOiJNRU1CRVIiLCJleHAiOjE2OTc5ODk2MDB9.QWlDVGV1Q1U2QURNM0x1UWJCdGlRZWxXTG5pOEFBSUE=",
	"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJlbWFpbCI6Imp1YW4ucGVyZXpAb25nLmNvbSIsInJvbGUiOiJNRU1CRVIiLCJleHAiOjE2OTgwNzQ5MDB9.UzBNdjV0cExnMWV3M0hCTVFYOVNQYU5IWmFUVUFBQTA=",
	"token_type": "bearer"
}
```

#### Errores Posibles

| Código | Descripción                       | Ejemplo de Error                                                                                           | Solución                                                        |
| ------ | --------------------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `401`  | Refresh token inválido o expirado | `{"detail": "Invalid refresh token"}`                                                                      | Haz login nuevamente para obtener nuevos tokens                 |
| `401`  | Usuario no encontrado             | `{"detail": "Invalid refresh token"}`                                                                      | El usuario asociado al token ya no existe, haz login nuevamente |
| `422`  | Error de validación Pydantic      | `{"detail": [{"loc": ["body", "refresh_token"], "msg": "field required", "type": "value_error.missing"}]}` | Verifica que el campo refresh_token esté presente               |

---

## Endpoints de Proyectos

### 1️⃣ Crear Proyecto

Crea un nuevo proyecto con etapas y pedidos anidados en una sola transacción.

**Método:** `POST`
**Ruta:** `/api/v1/projects`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `201 Created`
**Propietario:** El usuario autenticado

#### Parámetros

| Campo                        | Tipo    | Requerido | Descripción                                                          |
| ---------------------------- | ------- | --------- | -------------------------------------------------------------------- |
| `titulo`                     | string  | Sí        | Título del proyecto (mínimo 5 caracteres)                            |
| `descripcion`                | string  | Sí        | Descripción detallada (mínimo 20 caracteres)                         |
| `tipo`                       | string  | Sí        | Tipo de proyecto (ej: "Infraestructura", "Social")                   |
| `pais`                       | string  | Sí        | País (ej: "Argentina")                                               |
| `provincia`                  | string  | Sí        | Provincia (ej: "Buenos Aires")                                       |
| `ciudad`                     | string  | Sí        | Ciudad (ej: "La Plata")                                              |
| `barrio`                     | string  | No        | Barrio/Localidad (opcional)                                          |
| `estado`                     | enum    | No        | Estado del proyecto (default: `pendiente`, ver enumeraciones) |
| `bonita_case_id`             | string  | No        | ID de caso Bonita (opcional, para integración)                       |
| `bonita_process_instance_id` | integer | No        | ID instancia Bonita (opcional)                                       |
| `etapas`                     | array   | No        | Array de etapas anidadas (ver estructura abajo)                      |

#### Estructura de Etapas

```json
{
	"nombre": "string - Nombre de la etapa",
	"descripcion": "string - Descripción de la etapa",
	"fecha_inicio": "YYYY-MM-DD",
	"fecha_fin": "YYYY-MM-DD",
	"pedidos": [
		{
			"tipo": "enum - Tipo de pedido",
			"descripcion": "string - Descripción",
			"monto": "float - Opcional, para economico",
			"moneda": "string - Opcional, código de moneda",
			"cantidad": "integer - Opcional, para otros tipos",
			"unidad": "string - Opcional, unidad de medida"
		}
	]
}
```

#### Body de Prueba (Ejemplo Completo)

```json
{
	"titulo": "Centro Comunitario La Plata",
	"descripcion": "Construcción de un nuevo centro comunitario con servicios sociales, biblioteca y áreas de educación",
	"tipo": "Infraestructura Social",
	"pais": "Argentina",
	"provincia": "Buenos Aires",
	"ciudad": "La Plata",
	"barrio": "Centro",
	"estado": "pendiente",
	"bonita_case_id": null,
	"bonita_process_instance_id": null,
	"etapas": [
		{
			"nombre": "Fase 1 - Cimientos",
			"descripcion": "Preparación del terreno y construcción de cimientos",
			"fecha_inicio": "2024-11-01",
			"fecha_fin": "2024-12-31",
			"pedidos": [
				{
					"tipo": "economico",
					"descripcion": "Presupuesto para materiales de cimentación",
					"monto": 50000.0,
					"moneda": "ARS"
				},
				{
					"tipo": "mano_obra",
					"descripcion": "Mano de obra para excavación y cimientos",
					"cantidad": 20,
					"unidad": "jornadas"
				}
			]
		},
		{
			"nombre": "Fase 2 - Estructura",
			"descripcion": "Construcción de estructura principal del edificio",
			"fecha_inicio": "2025-01-01",
			"fecha_fin": "2025-03-31",
			"pedidos": [
				{
					"tipo": "materiales",
					"descripcion": "Acero y hormigón para estructura",
					"cantidad": 100,
					"unidad": "toneladas"
				},
				{
					"tipo": "transporte",
					"descripcion": "Transporte de materiales de construcción",
					"cantidad": 10,
					"unidad": "viajes"
				}
			]
		}
	]
}
```

#### Response Exitoso (201)

```json
{
	"id": "123e4567-e89b-12d3-a456-426614174000",
	"user_id": "550e8400-e29b-41d4-a716-446655440000",
	"titulo": "Centro Comunitario La Plata",
	"descripcion": "Construcción de un nuevo centro comunitario con servicios sociales, biblioteca y áreas de educación",
	"tipo": "Infraestructura Social",
	"pais": "Argentina",
	"provincia": "Buenos Aires",
	"ciudad": "La Plata",
	"barrio": "Centro",
	"estado": "pendiente",
	"bonita_case_id": null,
	"bonita_process_instance_id": null,
	"created_at": "2024-10-22T14:30:00+00:00",
	"updated_at": "2024-10-22T14:30:00+00:00",
	"etapas": [
		{
			"id": "223e4567-e89b-12d3-a456-426614174111",
			"proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
			"nombre": "Fase 1 - Cimientos",
			"descripcion": "Preparación del terreno y construcción de cimientos",
			"fecha_inicio": "2024-11-01",
			"fecha_fin": "2024-12-31",
			"pedidos": [
				{
					"id": "323e4567-e89b-12d3-a456-426614174222",
					"etapa_id": "223e4567-e89b-12d3-a456-426614174111",
					"tipo": "economico",
					"descripcion": "Presupuesto para materiales de cimentación",
					"estado": "PENDIENTE",
					"monto": 50000.0,
					"moneda": "ARS",
					"cantidad": null,
					"unidad": null
				},
				{
					"id": "323e4567-e89b-12d3-a456-426614174223",
					"etapa_id": "223e4567-e89b-12d3-a456-426614174111",
					"tipo": "mano_obra",
					"descripcion": "Mano de obra para excavación y cimientos",
					"estado": "PENDIENTE",
					"monto": null,
					"moneda": null,
					"cantidad": 20,
					"unidad": "jornadas"
				}
			]
		},
		{
			"id": "223e4567-e89b-12d3-a456-426614174112",
			"proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
			"nombre": "Fase 2 - Estructura",
			"descripcion": "Construcción de estructura principal del edificio",
			"fecha_inicio": "2025-01-01",
			"fecha_fin": "2025-03-31",
			"pedidos": [
				{
					"id": "323e4567-e89b-12d3-a456-426614174224",
					"etapa_id": "223e4567-e89b-12d3-a456-426614174112",
					"tipo": "materiales",
					"descripcion": "Acero y hormigón para estructura",
					"estado": "PENDIENTE",
					"monto": null,
					"moneda": null,
					"cantidad": 100,
					"unidad": "toneladas"
				}
			]
		}
	]
}
```

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado - Sin instalación)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "POST /api/v1/projects"
3. Click "Try it out"
4. Obtén un token con POST /api/v1/auth/login primero
5. En el authorization button de arriba, pega: `Bearer {tu_token}`
6. Completa el JSON con los datos del ejemplo
7. Click "Execute"

**Opción 2: cURL**

```bash
# Primero obtén un token con login
TOKEN="tu_access_token_aqui"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Centro Comunitario La Plata",
    "descripcion": "Construcción de un nuevo centro comunitario con servicios sociales, biblioteca y áreas de educación",
    "tipo": "Infraestructura Social",
    "pais": "Argentina",
    "provincia": "Buenos Aires",
    "ciudad": "La Plata",
    "barrio": "Centro",
    "estado": "pendiente",
    "etapas": [
      {
        "nombre": "Fase 1 - Cimientos",
        "descripcion": "Preparación del terreno y construcción de cimientos",
        "fecha_inicio": "2024-11-01",
        "fecha_fin": "2024-12-31",
        "pedidos": [
          {
            "tipo": "economico",
            "descripcion": "Presupuesto para materiales de cimentación",
            "monto": 50000.00,
            "moneda": "ARS"
          }
        ]
      }
    ]
  }'
```

**Opción 3: Postman**

1. Nueva petición → POST
2. URL: `https://project-planning-cloud-api.onrender.com/api/v1/projects`
3. Tab "Authorization" → Type: "Bearer Token" → Token: [pega tu access_token]
4. Tab "Body" → raw → JSON
5. Pega el JSON del ejemplo
6. Click "Send"

---

### 2️⃣ Obtener Todos los Proyectos

Lista proyectos con paginación, filtros combinables y ordenamiento dinámico. Retorna una vista resumida para mostrar listados rápidos sin las etapas/pedidos anidados.

**Método:** `GET`
**Ruta:** `/api/v1/projects`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Query Parameters (Paginación)

| Parámetro   | Tipo | Requerido | Descripción                                         |
| ----------- | ---- | --------- | --------------------------------------------------- |
| `page`      | int  | No        | Número de página (>=1). Default: `1`.               |
| `page_size` | int  | No        | Items por página (1-100). Default: `20`.            |

#### Query Parameters (Filtros Opcionales)

| Parámetro    | Tipo    | Descripción                                                                                  |
| ------------ | ------- | -------------------------------------------------------------------------------------------- |
| `estado`     | string  | Filtra por estado exacto: `pendiente`, `en_ejecucion`, `finalizado`.                         |
| `tipo`       | string  | Coincidencia parcial (case-insensitive) contra el tipo del proyecto.                         |
| `pais`       | string  | Coincidencia parcial del país.                                                               |
| `provincia`  | string  | Coincidencia parcial de la provincia.                                                        |
| `ciudad`     | string  | Coincidencia parcial de la ciudad.                                                           |
| `search`     | string  | Búsqueda texto libre en `titulo` y `descripcion` (case-insensitive).                         |
| `user_id`    | UUID    | Filtra por dueño específico. Ignorado si `my_projects=true`.                                 |
| `my_projects`| bool    | Si es `true`, solo retorna proyectos del usuario autenticado (sobrescribe `user_id`).        |

#### Query Parameters (Ordenamiento)

| Parámetro    | Tipo   | Descripción                                                                 |
| ------------ | ------ | --------------------------------------------------------------------------- |
| `sort_by`    | string | Campo para ordenar: `created_at`, `updated_at`, `titulo`. Default: `created_at`. |
| `sort_order` | string | Dirección del orden: `asc` o `desc`. Default: `desc`.                        |

#### Ejemplos de Uso

```http
# Página por defecto (20 items)
GET /api/v1/projects

# Solo mis proyectos
GET /api/v1/projects?my_projects=true

# Proyectos en ejecución en Buenos Aires
GET /api/v1/projects?estado=en_ejecucion&provincia=Buenos Aires

# Búsqueda por texto y paginada
GET /api/v1/projects?search=huerta&page=2&page_size=10&sort_by=titulo&sort_order=asc
```

#### Response Exitoso (200)

```json
{
	"items": [
		{
			"id": "123e4567-e89b-12d3-a456-426614174000",
			"user_id": "550e8400-e29b-41d4-a716-446655440000",
			"titulo": "Centro Comunitario La Plata",
			"descripcion": "Construcción de un nuevo centro comunitario con servicios sociales.",
			"tipo": "Infraestructura Social",
			"pais": "Argentina",
			"provincia": "Buenos Aires",
			"ciudad": "La Plata",
			"barrio": "Centro",
			"estado": "pendiente",
			"created_at": "2024-10-22T14:30:00+00:00",
			"updated_at": "2024-10-22T14:30:00+00:00"
		},
		{
			"id": "223e4567-e89b-12d3-a456-426614174111",
			"user_id": "550e8400-e29b-41d4-a716-446655440001",
			"titulo": "Huerta Urbana Comunitaria",
			"descripcion": "Implementación de una huerta urbana para 40 familias.",
			"tipo": "Agricultura Urbana",
			"pais": "Argentina",
			"provincia": "Buenos Aires",
			"ciudad": "Quilmes",
			"barrio": "Bernal",
			"estado": "en_ejecucion",
			"created_at": "2024-09-10T10:00:00+00:00",
			"updated_at": "2024-10-01T08:15:00+00:00"
		}
	],
	"total": 42,
	"page": 1,
	"page_size": 20,
	"total_pages": 3
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                                                           | Solución                                                 |
| ------ | ------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                                   | Proporciona un access_token válido en el header          |
| `422`  | Parámetros inválidos      | `{"detail": "Invalid estado value: borrador. Must be one of: pendiente, en_ejecucion, finalizado"}`                        | Usa valores permitidos para `estado`, `sort_by`, etc.    |

#### Instrucciones para Probar

**Opción 1: Swagger UI**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "GET /api/v1/projects"
3. Click "Try it out"
4. (Opcional) Completa filtros/paginación y presiona "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"

# Listar todos los proyectos (página 1)
curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/projects \
  -H "Authorization: Bearer $TOKEN"

# Buscar mis proyectos en ejecución ordenados por título ascendente
curl -X GET "https://project-planning-cloud-api.onrender.com/api/v1/projects?my_projects=true&estado=en_ejecucion&sort_by=titulo&sort_order=asc" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3️⃣ Obtener Proyecto por ID

Recupera un proyecto específico con todas sus etapas y pedidos anidados.

**Método:** `GET`
**Ruta:** `/api/v1/projects/{project_id}`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Path Parameters

| Parámetro    | Tipo | Descripción               |
| ------------ | ---- | ------------------------- |
| `project_id` | UUID | ID del proyecto a obtener |

#### Ejemplo de Ruta

```
GET /api/v1/projects/123e4567-e89b-12d3-a456-426614174000
```

#### Response Exitoso (200)

Retorna la estructura completa del proyecto igual que en el `POST` (ver ejemplo anterior).

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                | Solución                                                      |
| ------ | ------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                        | Proporciona un access_token válido en el header Authorization |
| `404`  | Proyecto no encontrado    | `{"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"}` | Verifica que el project_id sea correcto                       |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "GET /api/v1/projects/{project_id}"
3. Click "Try it out"
4. Pega el UUID en "project_id"
5. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4️⃣ Actualizar Proyecto (Parcial)

Actualiza campos específicos del proyecto usando PATCH (solo se actualizan los campos proporcionados).

**Método:** `PATCH`
**Ruta:** `/api/v1/projects/{project_id}`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`
**Restricción:** Solo el propietario del proyecto puede actualizar

#### Path Parameters

| Parámetro    | Tipo | Descripción                  |
| ------------ | ---- | ---------------------------- |
| `project_id` | UUID | ID del proyecto a actualizar |

#### Parámetros Actualizables

Todos los campos son opcionales. Solo se actualizan los que proporcionas:

| Campo                        | Tipo    | Descripción            |
| ---------------------------- | ------- | ---------------------- |
| `titulo`                     | string  | Nuevo título           |
| `descripcion`                | string  | Nueva descripción      |
| `tipo`                       | string  | Nuevo tipo             |
| `pais`                       | string  | Nuevo país             |
| `provincia`                  | string  | Nueva provincia        |
| `ciudad`                     | string  | Nueva ciudad           |
| `barrio`                     | string  | Nuevo barrio           |
| `estado`                     | enum    | Nuevo estado           |
| `bonita_case_id`             | string  | ID de caso Bonita      |
| `bonita_process_instance_id` | integer | ID de instancia Bonita |

#### Body de Prueba

```json
{
	"estado": "en_ejecucion",
	"bonita_case_id": "CASE-2024-001",
	"bonita_process_instance_id": 12345
}
```

#### Response Exitoso (200)

Retorna el proyecto actualizado con todos sus datos.

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                                                           | Solución                                      |
| ------ | ------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                                   | Proporciona un access_token válido            |
| `403`  | No eres el propietario    | `{"detail": "Forbidden - User is not the owner of this resource"}`                                                         | Solo el dueño del proyecto puede actualizar   |
| `404`  | Proyecto no existe        | `{"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"}`                                            | Verifica que el project_id sea correcto       |
| `422`  | Validación fallida        | `{"detail": [{"loc": ["body", "bonita_case_id"], "msg": "string does not match regex", "type": "value_error.str.regex"}]}` | Revisa el formato de los datos proporcionados |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "PATCH /api/v1/projects/{project_id}"
3. Click "Try it out"
4. Pega el UUID en "project_id"
5. Completa el JSON con los datos del ejemplo
6. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

curl -X PATCH https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "en_ejecucion",
    "bonita_case_id": "CASE-2024-001"
  }'
```

---

### 5️⃣ Eliminar Proyecto

Elimina un proyecto y **toda su estructura anidada** (etapas, pedidos, ofertas).

**Método:** `DELETE`
**Ruta:** `/api/v1/projects/{project_id}`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `204 No Content`
**Restricción:** Solo el propietario del proyecto puede eliminar
** Cascada:** Elimina también etapas, pedidos y ofertas

#### Path Parameters

| Parámetro    | Tipo | Descripción                |
| ------------ | ---- | -------------------------- |
| `project_id` | UUID | ID del proyecto a eliminar |

#### Confirmación

La eliminación es **permanente e irrevocable**. No hay confirmación adicional.

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                | Solución                                    |
| ------ | ------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                        | Proporciona un access_token válido          |
| `403`  | No eres el propietario    | `{"detail": "You are not the owner of this project"}`                           | Solo el dueño del proyecto puede eliminarlo |
| `404`  | Proyecto no encontrado    | `{"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"}` | Verifica que el project_id sea correcto     |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "DELETE /api/v1/projects/{project_id}"
3. Click "Try it out"
4. Pega el UUID en "project_id"
5. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

curl -X DELETE https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID \
  -H "Authorization: Bearer $TOKEN"
```

**Resultado esperado:**

-   Sin body en la respuesta
-   Status code: `204 No Content`

---

### 6️⃣ Iniciar Proyecto

Inicia un proyecto cambiando su estado de `pendiente` a `en_ejecucion`.

**Método:** `POST`
**Ruta:** `/api/v1/projects/{project_id}/start`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`
**Restricción:** Solo el propietario del proyecto puede iniciarlo
**Validación:** Todas las etapas deben estar financiadas (sin pedidos en `PENDIENTE`)

#### Path Parameters

| Parámetro    | Tipo | Descripción              |
| ------------ | ---- | ------------------------ |
| `project_id` | UUID | ID del proyecto a iniciar |

#### Validaciones

Para iniciar un proyecto, se deben cumplir estas condiciones:

1. **Estado actual:** El proyecto debe estar en estado `pendiente`
2. **Etapas financiadas:** TODAS las etapas deben tener sus pedidos en estado `COMPROMETIDO` o `COMPLETADO`
3. **Propiedad:** Solo el dueño del proyecto puede iniciarlo

Si algún pedido sigue en `PENDIENTE`, el endpoint retorna error 400 con la lista detallada de pedidos que necesitan financiamiento.

#### Response Exitoso (200)

```json
{
	"id": "123e4567-e89b-12d3-a456-426614174000",
	"titulo": "Centro Comunitario La Plata",
	"estado": "en_ejecucion",
	"message": "Proyecto iniciado exitosamente"
}
```

#### Errores Posibles

| Código | Descripción                         | Ejemplo de Error                                                                                                                  | Solución                                                              |
| ------ | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `401`  | Token inválido o faltante           | `{"detail": "Invalid or expired token"}`                                                                                          | Proporciona un access_token válido                                    |
| `403`  | No eres el propietario              | `{"detail": "Only the project owner can perform this action"}`                                                                    | Solo el dueño del proyecto puede iniciarlo                            |
| `404`  | Proyecto no encontrado              | `{"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"}`                                                   | Verifica que el project_id sea correcto                               |
| `400`  | Estado incorrecto                   | `{"detail": "Project can only be started from 'pendiente' state. Current state: en_ejecucion"}`                                    | El proyecto ya fue iniciado o está en otro estado                     |
| `400`  | Pedidos sin financiamiento (ver abajo)  | Ver ejemplo detallado abajo                                                                                                   | Asegúrate de que todos los pedidos tengan ofertas aceptadas           |

#### Error 400 - Pedidos Sin Financiamiento (Ejemplo Detallado)

Cuando hay pedidos sin completar, el error incluye la lista completa con detalles:

```json
{
	"detail": {
		"message": "No se puede iniciar el proyecto. 2 pedidos no están financiados",
		"pedidos_pendientes": [
			{
				"pedido_id": "323e4567-e89b-12d3-a456-426614174223",
				"etapa_nombre": "Fase 1 - Cimientos",
				"tipo": "mano_obra",
				"estado": "PENDIENTE",
				"descripcion": "Mano de obra para excavación y cimientos"
			},
			{
				"pedido_id": "323e4567-e89b-12d3-a456-426614174224",
				"etapa_nombre": "Fase 2 - Estructura",
				"tipo": "materiales",
				"estado": "PENDIENTE",
				"descripcion": "Acero y hormigón para estructura"
			}
		]
	}
}
```

#### Flujo para Iniciar un Proyecto

1. **Crear proyecto** con etapas y pedidos (POST /api/v1/projects)
2. **Usuarios ofertan** en los pedidos (POST /api/v1/pedidos/{pedido_id}/ofertas)
3. **Propietario acepta ofertas** (POST /api/v1/ofertas/{oferta_id}/accept) → Pedido pasa a `COMPROMETIDO`
4. **(Opcional) Oferentes confirman realización** (POST /api/v1/ofertas/{oferta_id}/confirmar-realizacion) → Pedido pasa a `COMPLETADO`
5. **Cuando TODOS los pedidos están al menos `COMPROMETIDO`**, el propietario puede iniciar el proyecto

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "POST /api/v1/projects/{project_id}/start"
3. Click "Try it out"
4. Pega el UUID del proyecto en "project_id"
5. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID/start \
  -H "Authorization: Bearer $TOKEN"
```

**Resultado esperado:**

-   Status code: `200 OK`
-   Body: JSON con id, titulo, estado y mensaje de éxito

---

### 7️⃣ Finalizar Proyecto

Marca un proyecto como `finalizado` una vez que todas sus etapas se completaron.

**Método:** `POST`  
**Ruta:** `/api/v1/projects/{project_id}/complete`  
**Autenticación:** Requerida (Bearer Token)  
**Código de Respuesta:** `200 OK`  
**Restricción:** Solo el propietario del proyecto puede finalizarlo  
**Validación:** Todas las etapas deben estar en estado `completada`

#### Response Exitoso (200)

```json
{
	"id": "123e4567-e89b-12d3-a456-426614174000",
	"titulo": "Centro Comunitario La Plata",
	"estado": "finalizado",
	"message": "Proyecto finalizado exitosamente"
}
```

#### Errores Posibles

| Código | Descripción                        | Ejemplo de Error                                                                                                                                         | Solución                                                         |
| ------ | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `401`  | Token inválido o faltante          | `{"detail": "Invalid or expired token"}`                                                                                                                 | Proporciona un access_token válido                               |
| `403`  | No eres el propietario             | `{"detail": "Only the project owner can perform this action"}`                                                                                           | Solo el dueño del proyecto puede finalizarlo                     |
| `404`  | Proyecto no encontrado             | `{"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"}`                                                                          | Verifica que el project_id sea correcto                          |
| `400`  | Estado incorrecto                  | `{"detail": "Project can only be completed from 'en_ejecucion' state. Current state: pendiente"}`                                                        | Asegúrate de que el proyecto esté en ejecución                   |
| `400`  | Etapas pendientes                  | `{"detail": {"message": "Todas las etapas deben estar completadas...", "etapas_pendientes": [{"etapa_id": "...", "estado": "en_ejecucion"}]}}`           | Completa todas las etapas antes de finalizar                     |

#### cURL

```bash
TOKEN="tu_access_token_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID/complete \
  -H "Authorization: Bearer $TOKEN"
```

**Si hay pedidos pendientes:**

-   Status code: `400 Bad Request`
-   Body: JSON con mensaje y lista de pedidos no completados

---

## Endpoints de Etapas

### 1️⃣ Listar Etapas de un Proyecto

Obtiene todas las etapas de un proyecto con información detallada de pedidos, conteo de pendientes y filtros por estado.

**Método:** `GET`
**Ruta:** `/api/v1/projects/{project_id}/etapas`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Path Parameters

| Parámetro    | Tipo | Descripción              |
| ------------ | ---- | ------------------------ |
| `project_id` | UUID | ID del proyecto objetivo |

#### Query Parameters (Opcional)

| Parámetro | Tipo  | Descripción                                                                       |
| --------- | ----- | --------------------------------------------------------------------------------- |
| `estado`  | enum  | Filtra por estado específico: `pendiente`, `financiada`, `en_ejecucion`, `completada`. |

#### ¿Qué incluye la respuesta?

-   Lista ordenada por `fecha_inicio`
-   Información completa de cada etapa (fechas, estado, pedidos)
-   Conteo de pedidos totales y pendientes para saber si puede iniciarse

#### Response Exitoso (200)

```json
{
	"etapas": [
		{
			"id": "223e4567-e89b-12d3-a456-426614174111",
			"proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
			"nombre": "Fase 1 - Cimientos",
			"descripcion": "Preparación del terreno y construcción de cimientos",
			"fecha_inicio": "2024-11-01",
			"fecha_fin": "2024-12-31",
			"estado": "pendiente",
			"fecha_completitud": null,
			"pedidos": [
				{
					"id": "323e4567-e89b-12d3-a456-426614174222",
					"descripcion": "Presupuesto para materiales de cimentación",
					"tipo": "economico",
					"estado": "PENDIENTE",
					"monto": 50000.0,
					"moneda": "ARS",
					"cantidad": null,
					"unidad": null
				}
			],
			"pedidos_pendientes_count": 1,
			"pedidos_total_count": 2
		},
		{
			"id": "223e4567-e89b-12d3-a456-426614174112",
			"proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
			"nombre": "Fase 2 - Estructura",
			"descripcion": "Construcción de estructura principal del edificio",
			"fecha_inicio": "2025-01-01",
			"fecha_fin": "2025-03-31",
			"estado": "financiada",
			"fecha_completitud": null,
			"pedidos": [],
			"pedidos_pendientes_count": 0,
			"pedidos_total_count": 0
		}
	],
	"total": 2
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                                      | Solución                                       |
| ------ | ------------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Not authenticated"}`                                                                     | Autentícate y envía el header Authorization.   |
| `422`  | Valor de estado inválido  | `{"detail": [{"loc": ["query", "estado"], "msg": "value is not a valid enumeration member", ...}]}`   | Usa los valores permitidos para `estado`.      |

#### Instrucciones para Probar

**Opción 1: Swagger UI**

1. Autentícate en `POST /api/v1/auth/login`.
2. Abre `GET /api/v1/projects/{project_id}/etapas`.
3. Click "Try it out", ingresa el `project_id` y (opcional) `estado`.
4. Ejecuta la petición.

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID/etapas \
  -H "Authorization: Bearer $TOKEN"
```

---

### 2️⃣ Iniciar Etapa

Cambia una etapa del estado `financiada` (o `pendiente` sin pedidos abiertos) a `en_ejecucion`. Valida automáticamente que el proyecto esté en ejecución y que no existan pedidos pendientes.

**Método:** `POST`
**Ruta:** `/api/v1/etapas/{etapa_id}/start`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`
**Restricción:** Solo el propietario del proyecto puede iniciar etapas

#### Path Parameters

| Parámetro  | Tipo | Descripción              |
| ---------- | ---- | ------------------------ |
| `etapa_id` | UUID | ID de la etapa a iniciar |

#### Response Exitoso (200)

```json
{
	"id": "223e4567-e89b-12d3-a456-426614174111",
	"nombre": "Fase 1 - Cimientos",
	"estado": "en_ejecucion",
	"message": "Etapa iniciada exitosamente"
}
```

#### Errores Posibles

| Código | Descripción                  | Ejemplo de Error                                                                                                                       | Solución                                                                                     |
| ------ | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante    | `{"detail": "Not authenticated"}`                                                                                                      | Envía un access token válido.                                                                |
| `403`  | No sos dueño del proyecto    | `{"detail": "Only the project owner can start etapas"}`                                                                                | Solo el propietario del proyecto puede iniciar etapas.                                       |
| `404`  | Etapa inexistente            | `{"detail": "Etapa with id 223e4567-e89b-12d3-a456-426614174111 not found"}`                                                           | Verifica el `etapa_id`.                                                                     |
| `400`  | Proyecto en estado incorrecto| `{"detail": "Project must be 'en_ejecucion' to start etapas. Current state: pendiente"}`                                               | El proyecto debe estar en ejecución.                                                         |
| `400`  | Pedidos pendientes           | `{"detail": {"message": "Cannot start etapa with 2 pending pedidos...", "pending_pedidos": [{"id": "...", "tipo": "materiales"}]}}`    | Completa o financia todos los pedidos antes de iniciar.                                      |
| `400`  | Etapa ya iniciada/completada | `{"detail": "Etapa is already in execution"}` o `{"detail": "Cannot start a completed etapa"}`                                         | No se puede reiniciar una etapa ya en ejecución o completada.                                |

#### Instrucciones para Probar

**Opción 1: Swagger UI**

1. Autentícate con el propietario del proyecto.
2. Busca `POST /api/v1/etapas/{etapa_id}/start`.
3. Click "Try it out" y pega el `etapa_id`.
4. Ejecuta y verifica el nuevo estado.

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_del_propietario"
ETAPA_ID="223e4567-e89b-12d3-a456-426614174111"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/etapas/$ETAPA_ID/start \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3️⃣ Completar Etapa

Marca una etapa como `completada`, agregando automáticamente la `fecha_completitud`. Solo se puede ejecutar si la etapa ya está `en_ejecucion`.

**Método:** `POST`
**Ruta:** `/api/v1/etapas/{etapa_id}/complete`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`
**Restricción:** Solo el propietario del proyecto puede completarla

#### Path Parameters

| Parámetro  | Tipo | Descripción               |
| ---------- | ---- | ------------------------- |
| `etapa_id` | UUID | ID de la etapa a completar |

#### Response Exitoso (200)

```json
{
	"id": "223e4567-e89b-12d3-a456-426614174111",
	"nombre": "Fase 1 - Cimientos",
	"estado": "completada",
	"fecha_completitud": "2024-12-20T14:10:00.123456+00:00",
	"message": "Etapa completada exitosamente"
}
```

#### Errores Posibles

| Código | Descripción                  | Ejemplo de Error                                                                                                                          | Solución                                                   |
| ------ | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `401`  | Token inválido o faltante    | `{"detail": "Not authenticated"}`                                                                                                         | Incluye un access token válido.                            |
| `403`  | No sos dueño del proyecto    | `{"detail": "Only the project owner can complete etapas"}`                                                                                | Solo el propietario puede completar etapas.                |
| `404`  | Etapa inexistente            | `{"detail": "Etapa with id 223e4567-e89b-12d3-a456-426614174111 not found"}`                                                              | Revisa el `etapa_id`.                                      |
| `400`  | Proyecto en estado incorrecto| `{"detail": "Project must be 'en_ejecucion' to complete etapas. Current state: finalizado"}`                                              | El proyecto debe seguir en ejecución.                      |
| `400`  | Etapa en estado inválido     | `{"detail": "Etapa can only be completed from 'en_ejecucion' state. Current state: financiada"}`                                          | Primero inicia la etapa (`/start`).                        |

#### Instrucciones para Probar

**Opción 1: Swagger UI**

1. Autentícate con el dueño del proyecto.
2. Selecciona `POST /api/v1/etapas/{etapa_id}/complete`.
3. Ingresa el `etapa_id` y ejecuta la petición.

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_del_propietario"
ETAPA_ID="223e4567-e89b-12d3-a456-426614174111"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/etapas/$ETAPA_ID/complete \
  -H "Authorization: Bearer $TOKEN"
```

---

## Endpoints de Pedidos

### 1️⃣ Crear Pedido para Etapa Existente

Crea un nuevo pedido dentro de una etapa específica de un proyecto.

**Método:** `POST`
**Ruta:** `/api/v1/projects/{project_id}/etapas/{etapa_id}/pedidos`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `201 Created`
**Restricción:** Solo el propietario del proyecto

#### Path Parameters

| Parámetro    | Tipo | Descripción                        |
| ------------ | ---- | ---------------------------------- |
| `project_id` | UUID | ID del proyecto dueño              |
| `etapa_id`   | UUID | ID de la etapa dentro del proyecto |

#### Parámetros

| Campo         | Tipo    | Requerido | Descripción                      |
| ------------- | ------- | --------- | -------------------------------- |
| `tipo`        | enum    | Sí        | Tipo de pedido                   |
| `descripcion` | string  | Sí        | Descripción detallada            |
| `monto`       | float   | No        | Monto (para tipo `economico`)    |
| `moneda`      | string  | No        | Código de moneda (ARS, USD, etc) |
| `cantidad`    | integer | No        | Cantidad (para otros tipos)      |
| `unidad`      | string  | No        | Unidad de medida                 |

#### Body de Prueba

```json
{
	"tipo": "economico",
	"descripcion": "Presupuesto para pintura de las paredes interiores",
	"monto": 15000.0,
	"moneda": "ARS"
}
```

Ejemplo alternativo (materiales):

```json
{
	"tipo": "materiales",
	"descripcion": "Ladrillos para mampostería de paredes",
	"cantidad": 5000,
	"unidad": "ladrillos"
}
```

#### Response Exitoso (201)

```json
{
	"id": "423e4567-e89b-12d3-a456-426614174333",
	"etapa_id": "223e4567-e89b-12d3-a456-426614174111",
	"tipo": "economico",
	"descripcion": "Presupuesto para pintura de las paredes interiores",
	"estado": "PENDIENTE",
	"monto": 15000.0,
	"moneda": "ARS",
	"cantidad": null,
	"unidad": null
}
```

#### Errores Posibles

| Código | Descripción                         | Ejemplo de Error                                                                                                       | Solución                                                                                   |
| ------ | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `401`  | Token inválido o faltante           | `{"detail": "Invalid or expired token"}`                                                                               | Proporciona un access_token válido                                                         |
| `403`  | No eres el propietario del proyecto | `{"detail": "You are not the owner of this project"}`                                                                  | Solo el dueño del proyecto puede crear pedidos                                             |
| `404`  | Proyecto no encontrado              | `{"detail": "Proyecto with id ... not found"}`                                                                         | Verifica que el project_id sea correcto                                                    |
| `404`  | Etapa no encontrada                 | `{"detail": "Etapa with id ... not found in proyecto"}`                                                                | Verifica que el etapa_id pertenezca al proyecto                                            |
| `422`  | Validación fallida                  | `{"detail": [{"loc": ["body", "tipo"], "msg": "value is not a valid enumeration member", "type": "type_error.enum"}]}` | Revisa que el tipo sea válido (economico, materiales, mano_obra, transporte, equipamiento) |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "POST /api/v1/projects/{project_id}/etapas/{etapa_id}/pedidos"
3. Click "Try it out"
4. Pega los UUIDs de proyecto y etapa
5. Completa el JSON con los datos del ejemplo
6. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"
ETAPA_ID="223e4567-e89b-12d3-a456-426614174111"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID/etapas/$ETAPA_ID/pedidos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "economico",
    "descripcion": "Presupuesto para pintura de las paredes interiores",
    "monto": 15000.00,
    "moneda": "ARS"
  }'
```

---

### 2️⃣ Listar Pedidos de Proyecto

Obtiene todos los pedidos de un proyecto con filtrado opcional por estado.

**Método:** `GET`
**Ruta:** `/api/v1/projects/{project_id}/pedidos`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Path Parameters

| Parámetro    | Tipo | Descripción     |
| ------------ | ---- | --------------- |
| `project_id` | UUID | ID del proyecto |

#### Query Parameters (Opcionales)

| Parámetro | Tipo | Descripción                                                     |
| --------- | ---- | --------------------------------------------------------------- |
| `estado`  | enum | Filtrar por estado: `PENDIENTE` o `COMPROMETIDO` o `COMPLETADO` |

#### Ejemplos de Ruta

```
GET /api/v1/projects/123e4567-e89b-12d3-a456-426614174000/pedidos
GET /api/v1/projects/123e4567-e89b-12d3-a456-426614174000/pedidos?estado=PENDIENTE
GET /api/v1/projects/123e4567-e89b-12d3-a456-426614174000/pedidos?estado=COMPLETADO
```

#### Response Exitoso (200)

```json
[
	{
		"id": "423e4567-e89b-12d3-a456-426614174333",
		"etapa_id": "223e4567-e89b-12d3-a456-426614174111",
		"tipo": "economico",
		"descripcion": "Presupuesto para pintura de las paredes interiores",
		"estado": "PENDIENTE",
		"monto": 15000.0,
		"moneda": "ARS",
		"cantidad": null,
		"unidad": null
	},
	{
		"id": "423e4567-e89b-12d3-a456-426614174334",
		"etapa_id": "223e4567-e89b-12d3-a456-426614174111",
		"tipo": "mano_obra",
		"descripcion": "Mano de obra para pintura",
		"estado": "COMPROMETIDO",
		"monto": null,
		"moneda": null,
		"cantidad": 5,
		"unidad": "jornadas"
	}
]
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                                                    | Solución                                                |
| ------ | ------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                            | Proporciona un access_token válido                      |
| `404`  | Proyecto no encontrado    | `{"detail": "Proyecto with id ... not found"}`                                                                      | Verifica que el project_id sea correcto                 |
| `422`  | Filtro de estado inválido | `{"detail": [{"loc": ["query", "estado"], "msg": "string does not match regex", "type": "value_error.str.regex"}]}` | El parámetro estado debe ser "pendiente" o "completado" |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "GET /api/v1/projects/{project_id}/pedidos"
3. Click "Try it out"
4. Pega el UUID del proyecto
5. (Opcional) Usa el parámetro `estado` para filtrar
6. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

# Todos los pedidos
curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID/pedidos \
  -H "Authorization: Bearer $TOKEN"

# Solo pendientes
curl -X GET "https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID/pedidos?estado=PENDIENTE" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3️⃣ Eliminar Pedido

Elimina un pedido específico (también elimina sus ofertas asociadas).

**Método:** `DELETE`
**Ruta:** `/api/v1/pedidos/{pedido_id}`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `204 No Content`
**Restricción:** Solo el propietario del proyecto dueño
** Cascada:** Elimina también todas las ofertas del pedido

#### Path Parameters

| Parámetro   | Tipo | Descripción              |
| ----------- | ---- | ------------------------ |
| `pedido_id` | UUID | ID del pedido a eliminar |

#### Errores Posibles

| Código | Descripción                         | Ejemplo de Error                                      | Solución                                          |
| ------ | ----------------------------------- | ----------------------------------------------------- | ------------------------------------------------- |
| `401`  | Token inválido o faltante           | `{"detail": "Invalid or expired token"}`              | Proporciona un access_token válido                |
| `403`  | No eres el propietario del proyecto | `{"detail": "You are not the owner of this project"}` | Solo el dueño del proyecto puede eliminar pedidos |
| `404`  | Pedido no encontrado                | `{"detail": "Pedido with id ... not found"}`          | Verifica que el pedido_id sea correcto            |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "DELETE /api/v1/pedidos/{pedido_id}"
3. Click "Try it out"
4. Pega el UUID del pedido
5. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PEDIDO_ID="423e4567-e89b-12d3-a456-426614174333"

curl -X DELETE https://project-planning-cloud-api.onrender.com/api/v1/pedidos/$PEDIDO_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

## Endpoints de Ofertas

### 1️⃣ Crear Oferta para Pedido

Crea una nueva oferta para un pedido específico. Un usuario propone sus servicios/productos para cubrirlo.

**Método:** `POST`
**Ruta:** `/api/v1/pedidos/{pedido_id}/ofertas`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `201 Created`
**Restricción:** Pedido debe estar en estado `PENDIENTE`

#### Path Parameters

| Parámetro   | Tipo | Descripción             |
| ----------- | ---- | ----------------------- |
| `pedido_id` | UUID | ID del pedido a ofertar |

#### Parámetros

| Campo            | Tipo   | Requerido | Descripción                                                 |
| ---------------- | ------ | --------- | ----------------------------------------------------------- |
| `descripcion`    | string | Sí        | Descripción de la oferta (mínimo 10 caracteres)             |
| `monto_ofrecido` | float  | No        | Monto ofrecido (opcional, para comparar con presupuesto)    |

#### Body de Prueba

```json
{
	"descripcion": "Tengo disponibilidad inmediata para realizar trabajos de pintura con materiales de primera calidad. Garantizo buen acabado y entrega a tiempo.",
	"monto_ofrecido": 14500.0
}
```

#### Response Exitoso (201)

```json
{
	"id": "523e4567-e89b-12d3-a456-426614174444",
	"pedido_id": "423e4567-e89b-12d3-a456-426614174333",
	"user_id": "550e8400-e29b-41d4-a716-446655440001",
	"descripcion": "Tengo disponibilidad inmediata para realizar trabajos de pintura con materiales de primera calidad. Garantizo buen acabado y entrega a tiempo.",
	"monto_ofrecido": 14500.0,
	"estado": "pendiente",
	"created_at": "2024-10-22T15:00:00+00:00",
	"updated_at": "2024-10-22T15:00:00+00:00"
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                                         | Solución                               |
| ------ | ------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                 | Proporciona un access_token válido     |
| `404`  | Pedido no encontrado      | `{"detail": "Pedido with id ... not found"}`                                                             | Verifica que el pedido_id sea correcto |
| `422`  | Validación fallida        | `{"detail": [{"loc": ["body", "descripcion"], "msg": "field required", "type": "value_error.missing"}]}` | La descripción es requerida            |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "POST /api/v1/pedidos/{pedido_id}/ofertas"
3. Click "Try it out"
4. Pega el UUID del pedido
5. Completa el JSON con los datos del ejemplo
6. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PEDIDO_ID="423e4567-e89b-12d3-a456-426614174333"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/pedidos/$PEDIDO_ID/ofertas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Tengo disponibilidad inmediata para realizar trabajos de pintura con materiales de primera calidad.",
    "monto_ofrecido": 14500.00
  }'
```

---

### 2️⃣ Listar Ofertas de Pedido

Obtiene todas las ofertas para un pedido específico (con detalles del usuario oferente).

**Método:** `GET`
**Ruta:** `/api/v1/pedidos/{pedido_id}/ofertas`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`
**Restricción:** Solo el propietario del proyecto puede ver las ofertas

#### Path Parameters

| Parámetro   | Tipo | Descripción   |
| ----------- | ---- | ------------- |
| `pedido_id` | UUID | ID del pedido |

#### Response Exitoso (200)

```json
[
	{
		"id": "523e4567-e89b-12d3-a456-426614174444",
		"pedido_id": "423e4567-e89b-12d3-a456-426614174333",
		"user_id": "550e8400-e29b-41d4-a716-446655440001",
		"descripcion": "Tengo disponibilidad inmediata para realizar trabajos de pintura...",
		"monto_ofrecido": 14500.0,
		"estado": "pendiente",
		"created_at": "2024-10-22T15:00:00+00:00",
		"updated_at": "2024-10-22T15:00:00+00:00",
		"user": {
			"id": "550e8400-e29b-41d4-a716-446655440001",
			"email": "maria.gonzalez@empresa.com",
			"nombre": "María",
			"apellido": "González",
			"ong": "Empresa Pintores"
		}
	}
]
```

#### Errores Posibles

| Código | Descripción                         | Ejemplo de Error                                      | Solución                                                        |
| ------ | ----------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------- |
| `401`  | Token inválido o faltante           | `{"detail": "Invalid or expired token"}`              | Proporciona un access_token válido                              |
| `403`  | No eres el propietario del proyecto | `{"detail": "You are not the owner of this project"}` | Solo el dueño del proyecto puede ver las ofertas de sus pedidos |
| `404`  | Pedido no encontrado                | `{"detail": "Pedido with id ... not found"}`          | Verifica que el pedido_id sea correcto                          |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "GET /api/v1/pedidos/{pedido_id}/ofertas"
3. Click "Try it out"
4. Pega el UUID del pedido
5. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PEDIDO_ID="423e4567-e89b-12d3-a456-426614174333"

curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/pedidos/$PEDIDO_ID/ofertas \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3️⃣ Aceptar Oferta

El propietario del proyecto acepta una oferta, compromentiéndose a usar los servicios del oferente.

**Método:** `POST`
**Ruta:** `/api/v1/ofertas/{oferta_id}/accept`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`
**Restricción:** Solo el propietario del proyecto
**Efecto Cascada:**

-   Oferta estado → `aceptada`
-   Pedido estado → `COMPROMETIDO`
-   Otras ofertas para mismo pedido → `rechazada`

#### Path Parameters

| Parámetro   | Tipo | Descripción               |
| ----------- | ---- | ------------------------- |
| `oferta_id` | UUID | ID de la oferta a aceptar |

#### Body

Sin body requerido.

#### Response Exitoso (200)

```json
{
	"id": "523e4567-e89b-12d3-a456-426614174444",
	"pedido_id": "423e4567-e89b-12d3-a456-426614174333",
	"user_id": "550e8400-e29b-41d4-a716-446655440001",
	"descripcion": "Tengo disponibilidad inmediata para realizar trabajos de pintura...",
	"monto_ofrecido": 14500.0,
	"estado": "aceptada",
	"created_at": "2024-10-22T15:00:00+00:00",
	"updated_at": "2024-10-22T15:10:00+00:00"
}
```

#### Errores Posibles

| Código | Descripción                         | Ejemplo de Error                                          | Solución                                                 |
| ------ | ----------------------------------- | --------------------------------------------------------- | -------------------------------------------------------- |
| `401`  | Token inválido o faltante           | `{"detail": "Invalid or expired token"}`                  | Proporciona un access_token válido                       |
| `403`  | No eres el propietario del proyecto | `{"detail": "You are not the owner of this project"}`     | Solo el dueño del proyecto puede aceptar ofertas         |
| `404`  | Oferta no encontrada                | `{"detail": "Oferta with id ... not found"}`              | Verifica que el oferta_id sea correcto                   |
| `400`  | Pedido ya completado                | `{"detail": "Cannot accept oferta for completed pedido"}` | No se pueden aceptar ofertas de pedidos completados      |
| `400`  | Pedido ya comprometido              | `{"detail": "Cannot accept oferta for committed pedido"}` | No se pueden aceptar ofertas de pedidos ya comprometidos |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "POST /api/v1/ofertas/{oferta_id}/accept"
3. Click "Try it out"
4. Pega el UUID de la oferta
5. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
OFERTA_ID="523e4567-e89b-12d3-a456-426614174444"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/ofertas/$OFERTA_ID/accept \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4️⃣ Rechazar Oferta

El propietario del proyecto rechaza una oferta.

**Método:** `POST`
**Ruta:** `/api/v1/ofertas/{oferta_id}/reject`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`
**Restricción:** Solo el propietario del proyecto

#### Path Parameters

| Parámetro   | Tipo | Descripción                |
| ----------- | ---- | -------------------------- |
| `oferta_id` | UUID | ID de la oferta a rechazar |

#### Response Exitoso (200)

```json
{
	"id": "523e4567-e89b-12d3-a456-426614174444",
	"pedido_id": "423e4567-e89b-12d3-a456-426614174333",
	"user_id": "550e8400-e29b-41d4-a716-446655440001",
	"descripcion": "Tengo disponibilidad inmediata para realizar trabajos de pintura...",
	"monto_ofrecido": 14500.0,
	"estado": "rechazada",
	"created_at": "2024-10-22T15:00:00+00:00",
	"updated_at": "2024-10-22T15:15:00+00:00"
}
```

#### Errores Posibles

| Código | Descripción                         | Ejemplo de Error                                      | Solución                                          |
| ------ | ----------------------------------- | ----------------------------------------------------- | ------------------------------------------------- |
| `401`  | Token inválido o faltante           | `{"detail": "Invalid or expired token"}`              | Proporciona un access_token válido                |
| `403`  | No eres el propietario del proyecto | `{"detail": "You are not the owner of this project"}` | Solo el dueño del proyecto puede rechazar ofertas |
| `404`  | Oferta no encontrada                | `{"detail": "Oferta with id ... not found"}`          | Verifica que el oferta_id sea correcto            |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "POST /api/v1/ofertas/{oferta_id}/reject"
3. Click "Try it out"
4. Pega el UUID de la oferta
5. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
OFERTA_ID="523e4567-e89b-12d3-a456-426614174444"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/ofertas/$OFERTA_ID/reject \
  -H "Authorization: Bearer $TOKEN"
```

---

### 5️⃣ Confirmar Realización de Oferta

El usuario que creó la oferta confirma que realizó el trabajo/servicio.

**Método:** `POST`
**Ruta:** `/api/v1/ofertas/{oferta_id}/confirmar-realizacion`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`
**Restricción:** Solo el creador de la oferta
**Precondiciones:**

-   Oferta debe estar en estado `aceptada`
-   Pedido debe estar en estado `COMPROMETIDO`

#### Path Parameters

| Parámetro   | Tipo | Descripción     |
| ----------- | ---- | --------------- |
| `oferta_id` | UUID | ID de la oferta |

#### Body

Sin body requerido.

#### Response Exitoso (200)

```json
{
	"message": "Realización confirmada exitosamente",
	"success": true,
	"oferta_id": "523e4567-e89b-12d3-a456-426614174444",
	"oferta_estado": "aceptada",
	"pedido_id": "423e4567-e89b-12d3-a456-426614174333",
	"pedido_estado_anterior": "COMPROMETIDO",
	"pedido_estado_nuevo": "COMPLETADO",
	"confirmed_at": "2024-10-22T15:30:00+00:00"
}
```

#### Errores Posibles

| Código | Descripción                     | Ejemplo de Error                                                                                | Solución                                                         |
| ------ | ------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `401`  | Token inválido o faltante       | `{"detail": "Invalid or expired token"}`                                                        | Proporciona un access_token válido                               |
| `403`  | No eres el creador de la oferta | `{"detail": "You are not the creator of this oferta"}`                                          | Solo quien creó la oferta puede confirmar su realización         |
| `404`  | Oferta no encontrada            | `{"detail": "Oferta with id ... not found"}`                                                    | Verifica que el oferta_id sea correcto                           |
| `400`  | Compromiso ya confirmado        | `{"detail": "This commitment has already been confirmed and marked as completado"}`             | Esta oferta ya fue confirmada previamente                        |
| `400`  | Estado de pedido incorrecto     | `{"detail": "Cannot confirm realization. Pedido is in state pendiente, expected comprometido"}` | El pedido debe estar en estado COMPROMETIDO para poder confirmar |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "POST /api/v1/ofertas/{oferta_id}/confirmar-realizacion"
3. Click "Try it out"
4. Pega el UUID de la oferta
5. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
OFERTA_ID="523e4567-e89b-12d3-a456-426614174444"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/ofertas/$OFERTA_ID/confirmar-realizacion \
  -H "Authorization: Bearer $TOKEN"
```

---

### 6️⃣ Obtener Mis Compromisos

Obtiene todas las ofertas que el usuario autenticado ha creado (sus compromisos).

**Método:** `GET`
**Ruta:** `/api/v1/ofertas/mis-compromisos`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Query Parameters (Opcionales)

| Parámetro       | Tipo | Descripción                                                  |
| --------------- | ---- | ------------------------------------------------------------ |
| `estado_pedido` | enum | Filtrar por estado del pedido: `COMPROMETIDO` o `COMPLETADO` |

#### Ejemplos de Ruta

```
GET /api/v1/ofertas/mis-compromisos
GET /api/v1/ofertas/mis-compromisos?estado_pedido=COMPROMETIDO
GET /api/v1/ofertas/mis-compromisos?estado_pedido=COMPLETADO
```

#### Response Exitoso (200)

```json
[
	{
		"id": "523e4567-e89b-12d3-a456-426614174444",
		"pedido_id": "423e4567-e89b-12d3-a456-426614174333",
		"user_id": "550e8400-e29b-41d4-a716-446655440001",
		"descripcion": "Tengo disponibilidad inmediata para realizar trabajos de pintura...",
		"monto_ofrecido": 14500.0,
		"estado": "aceptada",
		"created_at": "2024-10-22T15:00:00+00:00",
		"updated_at": "2024-10-22T15:10:00+00:00",
		"pedido": {
			"id": "423e4567-e89b-12d3-a456-426614174333",
			"etapa_id": "223e4567-e89b-12d3-a456-426614174111",
			"tipo": "economico",
			"descripcion": "Presupuesto para pintura de las paredes interiores",
			"estado": "COMPROMETIDO",
			"monto": 15000.0,
			"moneda": "ARS",
			"cantidad": null,
			"unidad": null
		}
	}
]
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                                                                 | Solución                                                                  |
| ------ | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                                         | Proporciona un access_token válido                                        |
| `422`  | Filtro de estado inválido | `{"detail": [{"loc": ["query", "estado_pedido"], "msg": "value is not a valid enumeration member", "type": "type_error.enum"}]}` | El parámetro estado_pedido debe ser un valor válido del enum EstadoPedido |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "GET /api/v1/ofertas/mis-compromisos"
3. Click "Try it out"
4. (Opcional) Usa el parámetro `estado_pedido` para filtrar
5. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"

# Todos los compromisos
curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/ofertas/mis-compromisos \
  -H "Authorization: Bearer $TOKEN"

# Solo comprometidos
curl -X GET "https://project-planning-cloud-api.onrender.com/api/v1/ofertas/mis-compromisos?estado_pedido=COMPROMETIDO" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 7️⃣ Listar Todas Mis Ofertas

Obtiene todas las ofertas que el usuario autenticado ha creado, en cualquier estado (pendientes, aceptadas, rechazadas). Permite ver el progreso de tus ofertas y cuáles están esperando respuesta.

**Método:** `GET`
**Ruta:** `/api/v1/ofertas/mis-ofertas`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Query Parameters (Opcionales)

| Parámetro       | Tipo | Descripción                                                  |
| --------------- | ---- | ------------------------------------------------------------ |
| `estado_oferta` | enum | Filtrar por estado de la oferta: `pendiente`, `aceptada` o `rechazada` |

#### Ejemplos de Ruta

```
GET /api/v1/ofertas/mis-ofertas
GET /api/v1/ofertas/mis-ofertas?estado_oferta=pendiente
GET /api/v1/ofertas/mis-ofertas?estado_oferta=aceptada
GET /api/v1/ofertas/mis-ofertas?estado_oferta=rechazada
```

#### Response Exitoso (200)

Estructura con información anidada del pedido y etapa:

```json
[
	{
		"id": "523e4567-e89b-12d3-a456-426614174444",
		"pedido_id": "423e4567-e89b-12d3-a456-426614174333",
		"user_id": "550e8400-e29b-41d4-a716-446655440001",
		"descripcion": "Tengo disponibilidad inmediata para realizar trabajos de pintura con materiales de primera calidad...",
		"monto_ofrecido": 14500.0,
		"estado": "pendiente",
		"created_at": "2024-10-22T15:00:00+00:00",
		"updated_at": "2024-10-22T15:00:00+00:00",
		"pedido": {
			"id": "423e4567-e89b-12d3-a456-426614174333",
			"tipo": "economico",
			"descripcion": "Presupuesto para pintura de las paredes interiores",
			"estado": "PENDIENTE",
			"monto": 15000.0,
			"moneda": "ARS",
			"cantidad": null,
			"unidad": null,
			"etapa": {
				"id": "223e4567-e89b-12d3-a456-426614174111",
				"nombre": "Fase 1: Diseño",
				"estado": "pendiente"
			}
		}
	},
	{
		"id": "523e4567-e89b-12d3-a456-426614174445",
		"pedido_id": "423e4567-e89b-12d3-a456-426614174334",
		"user_id": "550e8400-e29b-41d4-a716-446655440001",
		"descripcion": "Puedo suministrar cemento de primera calidad. Entrega garantizada en 10 días...",
		"monto_ofrecido": 8500.0,
		"estado": "aceptada",
		"created_at": "2024-10-20T12:00:00+00:00",
		"updated_at": "2024-10-21T10:30:00+00:00",
		"pedido": {
			"id": "423e4567-e89b-12d3-a456-426614174334",
			"tipo": "materiales",
			"descripcion": "Materiales para construcción de piso",
			"estado": "COMPROMETIDO",
			"monto": 9000.0,
			"moneda": "ARS",
			"cantidad": 50,
			"unidad": "bolsas",
			"etapa": {
				"id": "223e4567-e89b-12d3-a456-426614174222",
				"nombre": "Fase 2: Construcción",
				"estado": "financiada"
			}
		}
	}
]
```

#### Estructura del Response

**OfertaDetailedResponse:**

| Campo           | Tipo                    | Descripción                                          |
| --------------- | ----------------------- | ---------------------------------------------------- |
| `id`            | UUID                    | ID de la oferta                                      |
| `pedido_id`     | UUID                    | ID del pedido                                        |
| `user_id`       | UUID                    | ID del usuario que creó la oferta                    |
| `descripcion`   | string                  | Descripción de la oferta                             |
| `monto_ofrecido`| float (nullable)        | Monto ofrecido                                       |
| `estado`        | string                  | Estado: pendiente, aceptada o rechazada              |
| `created_at`    | datetime                | Fecha de creación                                    |
| `updated_at`    | datetime                | Fecha de última actualización                        |
| `pedido`        | PedidoDetailedInfo      | **Información anidada del pedido (ver debajo)**      |

**PedidoDetailedInfo:**

| Campo        | Tipo                 | Descripción                        |
| ------------ | -------------------- | ---------------------------------- |
| `id`         | UUID                 | ID del pedido                      |
| `tipo`       | string               | Tipo: economico, materiales, etc   |
| `descripcion`| string               | Descripción del pedido             |
| `estado`     | string               | Estado: PENDIENTE, COMPROMETIDO... |
| `monto`      | float (nullable)     | Monto presupuestado                |
| `moneda`     | string (nullable)    | Código de moneda (ARS, USD, etc)   |
| `cantidad`   | int (nullable)       | Cantidad requerida                 |
| `unidad`     | string (nullable)    | Unidad de medida                   |
| `etapa`      | EtapaBasicInfo       | **Información anidada de la etapa**|

**EtapaBasicInfo:**

| Campo   | Tipo   | Descripción                          |
| ------- | ------ | ------------------------------------ |
| `id`    | UUID   | ID de la etapa                       |
| `nombre`| string | Nombre/título de la etapa            |
| `estado`| string | Estado: pendiente, financiada, etc   |

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                                                                 | Solución                                                                  |
| ------ | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                                         | Proporciona un access_token válido                                        |
| `422`  | Filtro de estado inválido | `{"detail": [{"loc": ["query", "estado_oferta"], "msg": "value is not a valid enumeration member", "type": "type_error.enum"}]}` | El parámetro estado_oferta debe ser un valor válido (pendiente, aceptada, rechazada) |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "GET /api/v1/ofertas/mis-ofertas"
3. Click "Try it out"
4. (Opcional) Usa el parámetro `estado_oferta` para filtrar
5. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"

# Todas mis ofertas
curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/ofertas/mis-ofertas \
  -H "Authorization: Bearer $TOKEN"

# Solo pendientes
curl -X GET "https://project-planning-cloud-api.onrender.com/api/v1/ofertas/mis-ofertas?estado_oferta=pendiente" \
  -H "Authorization: Bearer $TOKEN"

# Solo aceptadas
curl -X GET "https://project-planning-cloud-api.onrender.com/api/v1/ofertas/mis-ofertas?estado_oferta=aceptada" \
  -H "Authorization: Bearer $TOKEN"
```

#### Diferencia entre Endpoints de Ofertas

| Endpoint | Descripción | Filtro de Estado | Usa Para |
| -------- | ----------- | --------------- | -------- |
| `GET /api/v1/ofertas/mis-compromisos` | **Solo ofertas aceptadas** (tus compromisos actuales) | Por estado del pedido (COMPROMETIDO, COMPLETADO) | Ver qué compromisos tienes activos |
| `GET /api/v1/ofertas/mis-ofertas` | **Todas tus ofertas** (pendientes, aceptadas, rechazadas) | Por estado de la oferta (pendiente, aceptada, rechazada) | Ver el histórico completo de tus ofertas |

---

## Endpoints de Observaciones

El módulo de **observaciones** permite al consejo directivo realizar seguimiento y control de proyectos en ejecución. Los miembros del consejo pueden crear observaciones que deben ser resueltas por los ejecutores de proyecto dentro de 5 días, con marcado automático como vencidas si no se resuelven a tiempo.

### 1️⃣ Crear Observación para Proyecto

Crea una nueva observación sobre un proyecto en ejecución. **Solo miembros del consejo (role=COUNCIL)** pueden crear observaciones.

**Método:** `POST`
**Ruta:** `/api/v1/projects/{project_id}/observaciones`
**Autenticación:** Requerida (Bearer Token)
**Autorización:** Solo usuarios con role=COUNCIL
**Código de Respuesta:** `201 Created`
**Restricción:** El proyecto debe estar en estado `en_ejecucion`

#### Path Parameters

| Parámetro    | Tipo | Descripción                          |
| ------------ | ---- | ------------------------------------ |
| `project_id` | UUID | ID del proyecto a observar           |

#### Parámetros

| Campo         | Tipo   | Requerido | Descripción                                              |
| ------------- | ------ | --------- | -------------------------------------------------------- |
| `descripcion` | string | Sí        | Descripción de la observación (mínimo 10 caracteres)     |

#### Comportamiento Automático

- **Fecha límite:** Se establece automáticamente a 5 días desde la creación
- **Estado inicial:** `pendiente`
- **Vencimiento:** Si no se resuelve antes de la fecha límite, se marca automáticamente como `vencida`

#### Body de Prueba

```json
{
	"descripcion": "Se observa que el presupuesto destinado a materiales no incluye costos de transporte. Por favor revisar y ajustar el presupuesto según lo conversado en la reunión del consejo."
}
```

#### Response Exitoso (201)

```json
{
	"id": "623e4567-e89b-12d3-a456-426614174555",
	"proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
	"council_user_id": "550e8400-e29b-41d4-a716-446655440003",
	"descripcion": "Se observa que el presupuesto destinado a materiales no incluye costos de transporte. Por favor revisar y ajustar el presupuesto según lo conversado en la reunión del consejo.",
	"estado": "pendiente",
	"fecha_limite": "2024-10-27",
	"respuesta": null,
	"fecha_resolucion": null,
	"created_at": "2024-10-22T10:00:00+00:00",
	"updated_at": "2024-10-22T10:00:00+00:00"
}
```

#### Errores Posibles

| Código | Descripción                              | Ejemplo de Error                                                                                                              | Solución                                               |
| ------ | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `401`  | Token inválido o faltante                | `{"detail": "Invalid or expired token"}`                                                                                      | Proporciona un access_token válido                     |
| `403`  | Usuario no es del consejo                | `{"detail": "Only council members can create observations"}`                                                                  | Solo usuarios con role=COUNCIL pueden crear observaciones |
| `404`  | Proyecto no encontrado                   | `{"detail": "Proyecto with id ... not found"}`                                                                                | Verifica que el project_id sea correcto                |
| `400`  | Proyecto no está en ejecución            | `{"detail": "Observations can only be created for projects in 'en_ejecucion' state. Current state: pendiente"}`        | El proyecto debe estar en estado `en_ejecucion`        |
| `422`  | Validación fallida                       | `{"detail": [{"loc": ["body", "descripcion"], "msg": "ensure this value has at least 10 characters", "type": "value_error"}]}` | La descripción debe tener al menos 10 caracteres       |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. **Importante:** Primero autentícate con un usuario COUNCIL
3. Busca "POST /api/v1/projects/{project_id}/observaciones"
4. Click "Try it out"
5. Pega el UUID del proyecto (debe estar en estado `en_ejecucion`)
6. Completa el JSON con los datos del ejemplo
7. Click "Execute"

**Opción 2: cURL**

```bash
# Token de un usuario COUNCIL
TOKEN="tu_access_token_de_consejo_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID/observaciones \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Se observa que el presupuesto destinado a materiales no incluye costos de transporte. Por favor revisar y ajustar."
  }'
```

---

### 2️⃣ Listar Observaciones de Proyecto

Obtiene todas las observaciones de un proyecto, con información del consejero que las creó. Las observaciones pendientes se verifican automáticamente y se marcan como vencidas si han pasado más de 5 días.

**Método:** `GET`
**Ruta:** `/api/v1/projects/{project_id}/observaciones`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Path Parameters

| Parámetro    | Tipo | Descripción            |
| ------------ | ---- | ---------------------- |
| `project_id` | UUID | ID del proyecto        |

#### Query Parameters (Opcionales)

| Parámetro | Tipo   | Descripción                                         |
| --------- | ------ | --------------------------------------------------- |
| `estado`  | string | Filtrar por estado: `pendiente`, `resuelta`, `vencida` |

#### Comportamiento Automático

- **Verificación de vencimiento:** Al listar, se verifica cada observación pendiente
- **Actualización automática:** Si han pasado más de 5 días desde la creación, el estado cambia automáticamente de `pendiente` a `vencida`
- **Ordenamiento:** Los resultados se ordenan por fecha de creación (más recientes primero)

#### Response Exitoso (200)

```json
[
	{
		"id": "623e4567-e89b-12d3-a456-426614174555",
		"proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
		"council_user_id": "550e8400-e29b-41d4-a716-446655440003",
		"descripcion": "Se observa que el presupuesto destinado a materiales no incluye costos de transporte.",
		"estado": "pendiente",
		"fecha_limite": "2024-10-27",
		"respuesta": null,
		"fecha_resolucion": null,
		"created_at": "2024-10-22T10:00:00+00:00",
		"updated_at": "2024-10-22T10:00:00+00:00",
		"council_user_email": "consejo@ong.org",
		"council_user_ong": "ONG Central",
		"council_user_nombre": "Carlos"
	},
	{
		"id": "723e4567-e89b-12d3-a456-426614174666",
		"proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
		"council_user_id": "550e8400-e29b-41d4-a716-446655440003",
		"descripcion": "El cronograma de la etapa 2 parece muy ajustado. Considerar ampliar plazos.",
		"estado": "resuelta",
		"fecha_limite": "2024-10-20",
		"respuesta": "Hemos revisado el cronograma y agregado 2 semanas adicionales a la etapa 2 según su recomendación.",
		"fecha_resolucion": "2024-10-19T14:30:00+00:00",
		"created_at": "2024-10-15T10:00:00+00:00",
		"updated_at": "2024-10-19T14:30:00+00:00",
		"council_user_email": "consejo@ong.org",
		"council_user_ong": "ONG Central",
		"council_user_nombre": "Carlos"
	}
]
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                                          | Solución                               |
| ------ | ------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                  | Proporciona un access_token válido     |
| `404`  | Proyecto no encontrado    | `{"detail": "Proyecto with id ... not found"}`                                                            | Verifica que el project_id sea correcto |
| `400`  | Filtro de estado inválido | `{"detail": "Invalid estado filter. Must be one of: ['pendiente', 'resuelta', 'vencida']"}`              | Usa un valor válido para el filtro     |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. Busca "GET /api/v1/projects/{project_id}/observaciones"
3. Click "Try it out"
4. Pega el UUID del proyecto
5. (Opcional) Selecciona un filtro de estado
6. Click "Execute"

**Opción 2: cURL**

```bash
TOKEN="tu_access_token_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

# Todas las observaciones
curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID/observaciones \
  -H "Authorization: Bearer $TOKEN"

# Solo observaciones pendientes
curl -X GET "https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID/observaciones?estado=pendiente" \
  -H "Authorization: Bearer $TOKEN"

# Solo observaciones vencidas
curl -X GET "https://project-planning-cloud-api.onrender.com/api/v1/projects/$PROJECT_ID/observaciones?estado=vencida" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3️⃣ Resolver Observación

Permite al ejecutor del proyecto (dueño) resolver una observación proporcionando una respuesta. Se puede resolver incluso si está vencida.

**Método:** `POST`
**Ruta:** `/api/v1/observaciones/{observacion_id}/resolve`
**Autenticación:** Requerida (Bearer Token)
**Autorización:** Solo el dueño del proyecto asociado
**Código de Respuesta:** `200 OK`

#### Path Parameters

| Parámetro        | Tipo | Descripción                   |
| ---------------- | ---- | ----------------------------- |
| `observacion_id` | UUID | ID de la observación a resolver |

#### Parámetros

| Campo      | Tipo   | Requerido | Descripción                                          |
| ---------- | ------ | --------- | ---------------------------------------------------- |
| `respuesta` | string | Sí        | Respuesta del ejecutor (mínimo 10 caracteres)        |

#### Comportamiento

- **Cambio de estado:** Cambia automáticamente a `resuelta`
- **Timestamp:** Registra fecha y hora exacta de resolución
- **Vencidas:** Se pueden resolver observaciones que ya estén vencidas
- **Irreversible:** Una vez resuelta, no se puede volver a estado pendiente

#### Body de Prueba

```json
{
	"respuesta": "Gracias por la observación. He revisado el presupuesto y agregado una partida para costos de transporte de $500 USD. El documento actualizado está adjunto en la sección de archivos del proyecto. Además, he actualizado el cronograma de materiales para incluir los tiempos de entrega."
}
```

#### Response Exitoso (200)

```json
{
	"id": "623e4567-e89b-12d3-a456-426614174555",
	"proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
	"council_user_id": "550e8400-e29b-41d4-a716-446655440003",
	"descripcion": "Se observa que el presupuesto destinado a materiales no incluye costos de transporte.",
	"estado": "resuelta",
	"fecha_limite": "2024-10-27",
	"respuesta": "Gracias por la observación. He revisado el presupuesto y agregado una partida para costos de transporte de $500 USD.",
	"fecha_resolucion": "2024-10-24T16:45:00+00:00",
	"created_at": "2024-10-22T10:00:00+00:00",
	"updated_at": "2024-10-24T16:45:00+00:00"
}
```

#### Errores Posibles

| Código | Descripción                      | Ejemplo de Error                                                                                          | Solución                                        |
| ------ | -------------------------------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `401`  | Token inválido o faltante        | `{"detail": "Invalid or expired token"}`                                                                  | Proporciona un access_token válido              |
| `403`  | No eres el dueño del proyecto    | `{"detail": "Only the project executor (owner) can resolve observations"}`                                | Solo el dueño del proyecto puede resolver       |
| `404`  | Observación no encontrada        | `{"detail": "Observacion with id ... not found"}`                                                         | Verifica que el observacion_id sea correcto     |
| `400`  | Observación ya resuelta          | `{"detail": "Observacion is already resolved"}`                                                           | Esta observación ya fue resuelta anteriormente  |
| `422`  | Validación fallida               | `{"detail": [{"loc": ["body", "respuesta"], "msg": "ensure this value has at least 10 characters"}]}`     | La respuesta debe tener al menos 10 caracteres  |

#### Instrucciones para Probar

**Opción 1: Swagger UI (Recomendado)**

1. Abre: `https://project-planning-cloud-api.onrender.com/docs`
2. **Importante:** Autentícate con el usuario dueño del proyecto
3. Busca "POST /api/v1/observaciones/{observacion_id}/resolve"
4. Click "Try it out"
5. Pega el UUID de la observación
6. Completa el JSON con tu respuesta
7. Click "Execute"

**Opción 2: cURL**

```bash
# Token del dueño del proyecto
TOKEN="tu_access_token_de_ejecutor_aqui"
OBSERVACION_ID="623e4567-e89b-12d3-a456-426614174555"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/observaciones/$OBSERVACION_ID/resolve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "respuesta": "Gracias por la observación. He revisado el presupuesto y agregado una partida para costos de transporte de $500 USD. El documento actualizado está disponible en la sección de archivos."
  }'
```

---

### Flujo Completo: Observaciones

Este es el flujo típico de trabajo con observaciones:

```
1. CONSEJO CREA OBSERVACIÓN
   POST /api/v1/projects/{id}/observaciones
   • Requiere role=COUNCIL
   • Proyecto debe estar en 'en_ejecucion'
   • Se crea con estado 'pendiente'
   • Fecha límite = hoy + 5 días

2. EJECUTOR LISTA OBSERVACIONES
   GET /api/v1/projects/{id}/observaciones?estado=pendiente
   • Ve todas las observaciones pendientes
   • Observaciones vencidas aparecen automáticamente marcadas

3. EJECUTOR RESUELVE OBSERVACIÓN
   POST /api/v1/observaciones/{id}/resolve
   • Requiere ser dueño del proyecto
   • Proporciona respuesta detallada
   • Estado cambia a 'resuelta'
   • Se registra timestamp de resolución

4. CONSEJO VERIFICA RESOLUCIÓN
   GET /api/v1/projects/{id}/observaciones?estado=resuelta
   • Puede ver la respuesta del ejecutor
   • Confirma que la observación fue atendida
```

### Estados de Observaciones

| Estado      | Descripción                                                       | Transición                                |
| ----------- | ----------------------------------------------------------------- | ----------------------------------------- |
| `pendiente` | Observación creada, esperando respuesta del ejecutor              | Creación inicial                          |
| `vencida`   | Observación pendiente que superó los 5 días sin resolverse        | Automático (al listar o consultar)        |
| `resuelta`  | Observación respondida por el ejecutor del proyecto               | Manual (ejecutor resuelve)                |

**Nota importante sobre el vencimiento:**
- Las observaciones NO cambian de estado automáticamente en la base de datos cada 5 días
- La verificación ocurre **al momento de listar o consultar** la observación
- Si una observación tiene más de 5 días sin resolver, se marca como `vencida` en ese momento
- Esto optimiza el rendimiento evitando procesos en background

---

## Endpoints de Usuarios

### 1️⃣ Obtener Perfil del Usuario Autenticado

Obtiene los datos del usuario autenticado actualmente.

**Método:** `GET`
**Ruta:** `/api/v1/users/me`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Response Exitoso (200)

```json
{
	"id": "550e8400-e29b-41d4-a716-446655440001",
	"email": "juan.perez@empresa.com",
	"nombre": "Juan",
	"apellido": "Pérez",
	"ong": "Fundación ABC",
	"role": "MEMBER",
	"created_at": "2024-10-01T10:00:00+00:00",
	"updated_at": "2024-10-22T15:30:00+00:00"
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                     | Solución                               |
| ------ | ------------------------- | ------------------------------------ | -------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}` | Proporciona un access_token válido     |

---

## Endpoints de Pedidos - Nuevas Operaciones

### 1️⃣ Obtener Pedido Específico

Obtiene los detalles de un pedido específico.

**Método:** `GET`
**Ruta:** `/api/v1/pedidos/{pedido_id}`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Path Parameters

| Parámetro   | Tipo | Descripción     |
| ----------- | ---- | --------------- |
| `pedido_id` | UUID | ID del pedido   |

#### Response Exitoso (200)

```json
{
	"id": "423e4567-e89b-12d3-a456-426614174333",
	"etapa_id": "223e4567-e89b-12d3-a456-426614174111",
	"tipo": "economico",
	"descripcion": "Presupuesto para pintura de las paredes interiores",
	"estado": "PENDIENTE",
	"monto": 15000.0,
	"moneda": "ARS",
	"cantidad": null,
	"unidad": null
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                           | Solución                             |
| ------ | ------------------------- | ---------------------------------------------------------- | ------------------------------------ |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                   | Proporciona un access_token válido   |
| `404`  | Pedido no encontrado      | `{"detail": "Pedido with id ... not found"}`               | Verifica que el pedido_id sea correcto |

---

### 2️⃣ Actualizar Pedido

Actualiza un pedido. Solo el dueño del proyecto puede actualizar. Los pedidos solo pueden actualizarse si están en estado PENDIENTE.

**Método:** `PATCH`
**Ruta:** `/api/v1/pedidos/{pedido_id}`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`
**Restricción:** Solo dueño del proyecto; pedido en estado PENDIENTE

#### Path Parameters

| Parámetro   | Tipo | Descripción     |
| ----------- | ---- | --------------- |
| `pedido_id` | UUID | ID del pedido   |

#### Parámetros

Todos los campos son opcionales:

| Campo         | Tipo   | Requerido | Descripción                                    |
| ------------- | ------ | --------- | ---------------------------------------------- |
| `tipo`        | enum   | No        | Tipo: economico, materiales, mano_obra, etc   |
| `descripcion` | string | No        | Descripción del pedido (mín. 5 caracteres)     |
| `monto`       | float  | No        | Monto presupuestado (> 0)                      |
| `moneda`      | string | No        | Código de moneda (ej: ARS, USD)                |
| `cantidad`    | int    | No        | Cantidad requerida (> 0)                       |
| `unidad`      | string | No        | Unidad de medida                               |

#### Body de Prueba

```json
{
	"descripcion": "Presupuesto actualizado para pintura con materiales premium",
	"monto": 18000.0
}
```

#### Response Exitoso (200)

```json
{
	"id": "423e4567-e89b-12d3-a456-426614174333",
	"etapa_id": "223e4567-e89b-12d3-a456-426614174111",
	"tipo": "economico",
	"descripcion": "Presupuesto actualizado para pintura con materiales premium",
	"estado": "PENDIENTE",
	"monto": 18000.0,
	"moneda": "ARS",
	"cantidad": null,
	"unidad": null
}
```

#### Errores Posibles

| Código | Descripción                         | Ejemplo de Error                                                       | Solución                                                            |
| ------ | ----------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `401`  | Token inválido o faltante           | `{"detail": "Invalid or expired token"}`                               | Proporciona un access_token válido                                  |
| `403`  | No eres el propietario del proyecto | `{"detail": "Only the project owner can update pedidos"}`              | Solo el dueño puede actualizar                                      |
| `404`  | Pedido no encontrado                | `{"detail": "Pedido with id ... not found"}`                           | Verifica que el pedido_id sea correcto                              |
| `400`  | Pedido no está en PENDIENTE         | `{"detail": "Cannot update pedido in state COMPROMETIDO. ..."}` | Solo se pueden actualizar pedidos en estado PENDIENTE               |

---

## Endpoints de Ofertas - Nuevas Operaciones

### 1️⃣ Obtener Oferta Específica

Obtiene los detalles de una oferta específica.

**Método:** `GET`
**Ruta:** `/api/v1/ofertas/{oferta_id}`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Path Parameters

| Parámetro   | Tipo | Descripción     |
| ----------- | ---- | --------------- |
| `oferta_id` | UUID | ID de la oferta |

#### Response Exitoso (200)

```json
{
	"id": "523e4567-e89b-12d3-a456-426614174444",
	"pedido_id": "423e4567-e89b-12d3-a456-426614174333",
	"user_id": "550e8400-e29b-41d4-a716-446655440001",
	"descripcion": "Tengo disponibilidad inmediata para realizar trabajos de pintura...",
	"monto_ofrecido": 14500.0,
	"estado": "pendiente",
	"created_at": "2024-10-22T15:00:00+00:00",
	"updated_at": "2024-10-22T15:00:00+00:00"
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                           | Solución                             |
| ------ | ------------------------- | ---------------------------------------------------------- | ------------------------------------ |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                   | Proporciona un access_token válido   |
| `404`  | Oferta no encontrada      | `{"detail": "Oferta with id ... not found"}`               | Verifica que el oferta_id sea correcto |

---

### 2️⃣ Actualizar Oferta

Actualiza una oferta. Solo el creador de la oferta puede actualizarla. Las ofertas solo pueden actualizarse si están en estado PENDIENTE.

**Método:** `PATCH`
**Ruta:** `/api/v1/ofertas/{oferta_id}`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`
**Restricción:** Solo creador; oferta en estado PENDIENTE

#### Path Parameters

| Parámetro   | Tipo | Descripción     |
| ----------- | ---- | --------------- |
| `oferta_id` | UUID | ID de la oferta |

#### Parámetros

Todos los campos son opcionales:

| Campo            | Tipo   | Requerido | Descripción                                           |
| ---------------- | ------ | --------- | ----------------------------------------------------- |
| `descripcion`    | string | No        | Descripción actualizada de la oferta (mín. 10 car)    |
| `monto_ofrecido` | float  | No        | Monto actualizado ofrecido (> 0)                      |

#### Body de Prueba

```json
{
	"descripcion": "Tengo disponibilidad inmediata con materiales de primera calidad. Entrega dentro de 5 días.",
	"monto_ofrecido": 13500.0
}
```

#### Response Exitoso (200)

```json
{
	"id": "523e4567-e89b-12d3-a456-426614174444",
	"pedido_id": "423e4567-e89b-12d3-a456-426614174333",
	"user_id": "550e8400-e29b-41d4-a716-446655440001",
	"descripcion": "Tengo disponibilidad inmediata con materiales de primera calidad. Entrega dentro de 5 días.",
	"monto_ofrecido": 13500.0,
	"estado": "pendiente",
	"created_at": "2024-10-22T15:00:00+00:00",
	"updated_at": "2024-10-22T15:45:00+00:00"
}
```

#### Errores Posibles

| Código | Descripción                    | Ejemplo de Error                                                      | Solución                                           |
| ------ | ------------------------------ | --------------------------------------------------------------------- | -------------------------------------------------- |
| `401`  | Token inválido o faltante      | `{"detail": "Invalid or expired token"}`                              | Proporciona un access_token válido                 |
| `403`  | No eres el creador de la oferta | `{"detail": "Only the user who created the oferta can update it"}`    | Solo quien creó la oferta puede actualizarla       |
| `404`  | Oferta no encontrada           | `{"detail": "Oferta with id ... not found"}`                          | Verifica que el oferta_id sea correcto             |
| `400`  | Oferta no está en PENDIENTE    | `{"detail": "Cannot update oferta in state aceptada. ..."}` | Solo se pueden actualizar ofertas en estado PENDIENTE |

---

### 3️⃣ Eliminar Oferta

Elimina una oferta. Solo el creador puede eliminarla. Las ofertas solo pueden eliminarse si están en estado PENDIENTE.

**Método:** `DELETE`
**Ruta:** `/api/v1/ofertas/{oferta_id}`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `204 No Content`
**Restricción:** Solo creador; oferta en estado PENDIENTE

#### Path Parameters

| Parámetro   | Tipo | Descripción     |
| ----------- | ---- | --------------- |
| `oferta_id` | UUID | ID de la oferta |

#### Response Exitoso (204)

Sin contenido (No Content)

#### Errores Posibles

| Código | Descripción                    | Ejemplo de Error                                                      | Solución                                       |
| ------ | ------------------------------ | --------------------------------------------------------------------- | ---------------------------------------------- |
| `401`  | Token inválido o faltante      | `{"detail": "Invalid or expired token"}`                              | Proporciona un access_token válido             |
| `403`  | No eres el creador de la oferta | `{"detail": "Only the user who created the oferta can delete it"}`    | Solo quien creó la oferta puede eliminarla      |
| `404`  | Oferta no encontrada           | `{"detail": "Oferta with id ... not found"}`                          | Verifica que el oferta_id sea correcto          |
| `400`  | Oferta no está en PENDIENTE    | `{"detail": "Cannot delete oferta in state aceptada. ..."}` | Solo se pueden eliminar ofertas en estado PENDIENTE |

---

## Endpoints de Etapas - Nuevas Operaciones

### 1️⃣ Obtener Etapa Específica

Obtiene los detalles de una etapa específica.

**Método:** `GET`
**Ruta:** `/api/v1/etapas/{etapa_id}`
**Autenticación:** Requerida (Bearer Token)
**Código de Respuesta:** `200 OK`

#### Path Parameters

| Parámetro  | Tipo | Descripción    |
| ---------- | ---- | -------------- |
| `etapa_id` | UUID | ID de la etapa |

#### Response Exitoso (200)

```json
{
	"id": "223e4567-e89b-12d3-a456-426614174111",
	"proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
	"nombre": "Fase 1: Planificación",
	"descripcion": "Diseño arquitectónico y planificación inicial del proyecto",
	"fecha_inicio": "2024-11-01",
	"fecha_fin": "2024-12-31",
	"estado": "pendiente",
	"pendientes_count": 3,
	"total_pedidos": 5
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                           | Solución                             |
| ------ | ------------------------- | ---------------------------------------------------------- | ------------------------------------ |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                   | Proporciona un access_token válido   |
| `404`  | Etapa no encontrada       | `{"detail": "Etapa with id ... not found"}`                | Verifica que el etapa_id sea correcto |

---

## Endpoints de Métricas

El módulo de métricas expone indicadores listos para tableros (PowerBI, Grafana, dashboards internos) sin que el frontend tenga que recalcularlos. Todos los endpoints requieren JWT pero cualquier usuario autenticado puede consultarlos.

### 1️⃣ Dashboard de Proyectos

Estadísticas globales del sistema para alimentar el dashboard principal.

**Método:** `GET`  
**Ruta:** `/api/v1/metrics/dashboard`  
**Autenticación:** Requerida (Bearer Token)  
**Código de Respuesta:** `200 OK`

#### Métricas incluidas

- Conteo de proyectos por estado (`pendiente`, `en_ejecucion`, `finalizado`)
- Totales generales (proyectos creados, activos y listos para iniciar)
- `tasa_exito`: porcentaje de proyectos finalizados sobre el total

#### Response Exitoso (200)

```json
{
	"proyectos_por_estado": {
		"pendiente": 2,
		"en_ejecucion": 3,
		"finalizado": 1
	},
	"total_proyectos": 6,
	"proyectos_activos": 3,
	"proyectos_listos_para_iniciar": 1,
	"tasa_exito": 16.67
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                        | Solución                                  |
| ------ | ------------------------- | --------------------------------------- | ----------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}` | Envía un access token válido (Bearer).    |

#### Instrucciones para Probar

- **Swagger UI:** Ejecuta `GET /api/v1/metrics/dashboard` luego de autenticarte.
- **cURL:**

```bash
TOKEN="tu_access_token_aqui"

curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/metrics/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

---

### 2️⃣ Seguimiento Detallado de Proyecto

Muestra todas las métricas operativas de un proyecto (progreso, pedidos, observaciones, posibilidad de inicio).

**Método:** `GET`  
**Ruta:** `/api/v1/metrics/projects/{project_id}/tracking`  
**Autenticación:** Requerida (Bearer Token)  
**Código de Respuesta:** `200 OK`

#### Path Parameters

| Parámetro    | Tipo | Descripción                   |
| ------------ | ---- | ----------------------------- |
| `project_id` | UUID | ID del proyecto a monitorizar |

#### Métricas incluidas

- Progreso porcentual por etapa y global
- Cantidad de pedidos completados/pendientes
- Observaciones por estado (pendientes, resueltas, vencidas)
- Indicador `puede_iniciar` (todos los pedidos completados)

#### Response Exitoso (200)

```json
{
	"proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
	"titulo": "Centro Comunitario Barrio Norte",
	"estado": "en_ejecucion",
	"etapas": [
		{
			"etapa_id": "223e4567-e89b-12d3-a456-426614174111",
			"nombre": "Fundaciones",
			"total_pedidos": 3,
			"pedidos_completados": 2,
			"pedidos_pendientes": 1,
			"progreso_porcentaje": 66.67,
			"dias_planificados": 45,
			"dias_transcurridos": 30
		}
	],
	"total_pedidos": 5,
	"pedidos_completados": 3,
	"pedidos_pendientes": 2,
	"progreso_global_porcentaje": 60.0,
	"observaciones_pendientes": 1,
	"observaciones_resueltas": 2,
	"observaciones_vencidas": 0,
	"puede_iniciar": false
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                                                                | Solución                                        |
| ------ | ------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                        | Autentícate antes de llamar al endpoint.        |
| `404`  | Proyecto no encontrado    | `{"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"}` | Revisa que el `project_id` exista en la base.   |

#### Instrucciones para Probar

```bash
TOKEN="tu_access_token_aqui"
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/metrics/projects/$PROJECT_ID/tracking \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3️⃣ Métricas de Compromisos (Ofertas)

Analiza la participación de la red en la cobertura de pedidos.

**Método:** `GET`  
**Ruta:** `/api/v1/metrics/commitments`  
**Autenticación:** Requerida (Bearer Token)  
**Código de Respuesta:** `200 OK`

#### Métricas incluidas

- Cobertura de ofertas y tasa de aceptación
- Distribución de ofertas por estado
- Tiempo promedio de respuesta de la comunidad
- Top 5 contribuidores con más ofertas/aceptaciones
- Totales monetarios: solicitado vs comprometido

#### Response Exitoso (200)

```json
{
	"total_pedidos": 12,
	"pedidos_con_ofertas": 9,
	"cobertura_ofertas_porcentaje": 75.0,
	"total_ofertas": 18,
	"ofertas_aceptadas": 6,
	"ofertas_pendientes": 9,
	"tasa_aceptacion_porcentaje": 33.33,
	"tiempo_respuesta_promedio_dias": 2.5,
	"top_contribuidores": [
		{
			"user_id": "550e8400-e29b-41d4-a716-446655440003",
			"nombre": "Lucía",
			"apellido": "Gómez",
			"ong": "Construcciones Solidarias",
			"ofertas_realizadas": 7,
			"ofertas_aceptadas": 3,
			"tasa_aceptacion": 42.86
		}
	],
	"valor_total_solicitado": 500000.0,
	"valor_total_comprometido": 360000.0
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                        | Solución                     |
| ------ | ------------------------- | --------------------------------------- | ---------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}` | Autentícate nuevamente.      |

#### Instrucciones para Probar

```bash
TOKEN="tu_access_token_aqui"

curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/metrics/commitments \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4️⃣ Métricas de Rendimiento del Sistema

Indicadores transversales de eficiencia del proceso (tiempos, observaciones, proyectos estancados).

**Método:** `GET`  
**Ruta:** `/api/v1/metrics/performance`  
**Autenticación:** Requerida (Bearer Token)  
**Código de Respuesta:** `200 OK`

#### Métricas incluidas

- Tiempo promedio por etapa y desde creación hasta inicio de proyecto
- Cantidad de proyectos pendientes por más de 30 días
- Estado de observaciones (total, resueltas, pendientes, vencidas)
- Tiempo promedio de resolución de observaciones

#### Response Exitoso (200)

```json
{
	"tiempo_promedio_etapa_dias": 45.5,
	"tiempo_inicio_promedio_dias": 12.3,
	"proyectos_pendientes_mas_30_dias": 3,
	"observaciones_total": 20,
	"observaciones_resueltas": 12,
	"observaciones_pendientes": 6,
	"observaciones_vencidas": 2,
	"tiempo_resolucion_observaciones_promedio_dias": 4.2
}
```

#### Errores Posibles

| Código | Descripción               | Ejemplo de Error                        | Solución                         |
| ------ | ------------------------- | --------------------------------------- | -------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}` | Autorízate con un access token. |

#### Instrucciones para Probar

```bash
TOKEN="tu_access_token_aqui"

curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/metrics/performance \
  -H "Authorization: Bearer $TOKEN"
```

---

## Enumeraciones

### EstadoProyecto

Estados disponibles para los proyectos:

```python
"pendiente"             # Buscando financiamiento (default)
"en_ejecucion"          # En ejecución
"finalizado"            # Proyecto completado y cerrado
```

Ejemplo de uso:

```json
{
	"estado": "pendiente"
}
```

---

### TipoPedido

Tipos disponibles para los pedidos:

```python
"economico"     # Solicitud de presupuesto/dinero
"materiales"    # Solicitud de materiales
"mano_obra"     # Solicitud de mano de obra
"transporte"    # Solicitud de transporte
"equipamiento"  # Solicitud de equipamiento/máquinas
```

**Recomendaciones de uso:**

-   `economico` → Usa `monto` + `moneda`
-   Otros tipos → Usa `cantidad` + `unidad`

Ejemplos:

```json
// Económico
{
  "tipo": "economico",
  "monto": 50000.00,
  "moneda": "ARS"
}

// Materiales
{
  "tipo": "materiales",
  "cantidad": 100,
  "unidad": "metros"
}

// Mano de obra
{
  "tipo": "mano_obra",
  "cantidad": 20,
  "unidad": "jornadas"
}
```

---

### EstadoPedido

Estados disponibles para los pedidos:

```python
"PENDIENTE"      # Sin oferta aceptada (default)
"COMPROMETIDO"   # Con oferta aceptada, esperando confirmación
"COMPLETADO"     # Realización confirmada
```

**Flujo de estado:**

```
PENDIENTE → (aceptar oferta) → COMPROMETIDO → (confirmar realización) → COMPLETADO
```

---

### EstadoOferta

Estados disponibles para las ofertas:

```python
"pendiente"     # Recién creada, esperando decisión (default)
"aceptada"      # Proyecto aceptó la oferta
"rechazada"     # Proyecto rechazó la oferta
```

---

### EstadoObservacion

Estados disponibles para las observaciones:

```python
"pendiente"  # Observación creada, esperando resolución (default)
"vencida"    # Observación pendiente que superó los 5 días sin resolver
"resuelta"   # Observación respondida por el ejecutor del proyecto
```

**Flujo de estado:**

```
PENDIENTE → (automático si >5 días) → VENCIDA
PENDIENTE → (ejecutor resuelve) → RESUELTA
VENCIDA → (ejecutor resuelve) → RESUELTA
```

**Notas importantes:**
- El cambio de `pendiente` a `vencida` ocurre **automáticamente** al listar o consultar observaciones
- Las observaciones `vencidas` aún pueden ser resueltas por el ejecutor
- Una vez `resuelta`, el estado no puede cambiar

Ejemplo de uso:

```json
{
	"estado": "pendiente",
	"fecha_limite": "2024-10-27"
}
```

---

### UserRole

Roles disponibles para usuarios:

```python
"MEMBER"   # Usuario regular
"COUNCIL"  # Miembro de consejo (elevados permisos)
```

---

## Flujo Completo de Ejemplo

A continuación, un ejemplo paso a paso de cómo usar la API desde cero:

### Paso 1: Registrar Dos Usuarios

**Usuario 1 - Proyecto Owner (María)**

```bash
curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "maria@ong.com",
    "password": "Password123",
    "nombre": "María",
    "apellido": "López",
    "ong": "ONG Social",
    "role": "MEMBER"
  }'
```

Guarda el `id` retornado. Ejemplo: `550e8400-e29b-41d4-a716-446655440000`

**Usuario 2 - Oferente (Carlos)**

```bash
curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "carlos@empresa.com",
    "password": "Password456",
    "nombre": "Carlos",
    "apellido": "García",
    "ong": "Empresa Constructora",
    "role": "MEMBER"
  }'
```

Guarda el `id` retornado. Ejemplo: `550e8400-e29b-41d4-a716-446655440001`

### Paso 2: Login con Ambos Usuarios

**María (Dueña del Proyecto)**

```bash
curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "maria@ong.com",
    "password": "Password123"
  }'
```

Guarda el `access_token`. Ejemplo para usar:

```bash
MARIA_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Carlos (Oferente)**

```bash
curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "carlos@empresa.com",
    "password": "Password456"
  }'
```

Guarda el `access_token`:

```bash
CARLOS_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Paso 3: María Crea un Proyecto

```bash
MARIA_TOKEN="tu_token_aqui"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/projects \
  -H "Authorization: Bearer $MARIA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Renovación Centro Comunitario",
    "descripcion": "Renovación completa del centro comunitario incluyendo pintura, pisos y techos",
    "tipo": "Infraestructura",
    "pais": "Argentina",
    "provincia": "Buenos Aires",
    "ciudad": "La Plata",
    "barrio": "Centro",
    "estado": "pendiente",
    "etapas": [
      {
        "nombre": "Remodelación Interior",
        "descripcion": "Todas las reparaciones interiores",
        "fecha_inicio": "2024-11-01",
        "fecha_fin": "2024-12-31",
        "pedidos": [
          {
            "tipo": "economico",
            "descripcion": "Presupuesto para pintura de interiores",
            "monto": 15000.00,
            "moneda": "ARS"
          }
        ]
      }
    ]
  }'
```

**Guarda los IDs retornados:**

-   `project_id`: ID del proyecto (ej: `123e4567-e89b-12d3-a456-426614174000`)
-   `pedido_id`: ID del pedido (ej: `423e4567-e89b-12d3-a456-426614174333`)

### Paso 4: Carlos Crea una Oferta

```bash
CARLOS_TOKEN="tu_token_aqui"
PEDIDO_ID="423e4567-e89b-12d3-a456-426614174333"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/pedidos/$PEDIDO_ID/ofertas \
  -H "Authorization: Bearer $CARLOS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Soy pintor profesional con 15 años de experiencia. Ofrezco trabajo de calidad con materiales premium y garantía de acabado perfecto.",
    "monto_ofrecido": 14000.00
  }'
```

**Guarda el `oferta_id` retornado:**

-   Ejemplo: `523e4567-e89b-12d3-a456-426614174444`

### Paso 5: María ve las Ofertas del Pedido

```bash
MARIA_TOKEN="tu_token_aqui"
PEDIDO_ID="423e4567-e89b-12d3-a456-426614174333"

curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/pedidos/$PEDIDO_ID/ofertas \
  -H "Authorization: Bearer $MARIA_TOKEN"
```

Verá la oferta de Carlos con sus detalles.

### Paso 6: María Acepta la Oferta de Carlos

```bash
MARIA_TOKEN="tu_token_aqui"
OFERTA_ID="523e4567-e89b-12d3-a456-426614174444"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/ofertas/$OFERTA_ID/accept \
  -H "Authorization: Bearer $MARIA_TOKEN"
```

**Cambios automáticos:**

-   Oferta estado: `pendiente` → `aceptada`
-   Pedido estado: `PENDIENTE` → `COMPROMETIDO`

### Paso 7: Carlos Confirma que Realizó el Trabajo

```bash
CARLOS_TOKEN="tu_token_aqui"
OFERTA_ID="523e4567-e89b-12d3-a456-426614174444"

curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/ofertas/$OFERTA_ID/confirmar-realizacion \
  -H "Authorization: Bearer $CARLOS_TOKEN"
```

**Cambios automáticos:**

-   Pedido estado: `COMPROMETIDO` → `COMPLETADO`

### Paso 8: Carlos Visualiza sus Compromisos

```bash
CARLOS_TOKEN="tu_token_aqui"

curl -X GET https://project-planning-cloud-api.onrender.com/api/v1/ofertas/mis-compromisos \
  -H "Authorization: Bearer $CARLOS_TOKEN"
```

Verá todas sus ofertas aceptadas con estado `aceptada` y sus pedidos asociados.

---

## Códigos de Error

Esta sección describe **todos los códigos de error posibles** que la API puede retornar, organizados por categoría.

### Códigos HTTP Estándar

| Código | Nombre                | Descripción                                     |
| ------ | --------------------- | ----------------------------------------------- |
| `200`  | OK                    | Petición exitosa                                |
| `201`  | Created               | Recurso creado exitosamente                     |
| `204`  | No Content            | Eliminación exitosa (sin body)                  |
| `400`  | Bad Request           | Solicitud incorrecta o regla de negocio violada |
| `401`  | Unauthorized          | Sin autenticación o token inválido              |
| `403`  | Forbidden             | No tienes permisos para esta acción             |
| `404`  | Not Found             | Recurso no existe                               |
| `422`  | Unprocessable Entity  | Validación de datos fallida                     |
| `500`  | Internal Server Error | Error inesperado del servidor                   |

---

### Errores por Endpoint

#### Autenticación

##### POST /api/v1/auth/register

| Código | Error                      | Ejemplo                                                                                                |
| ------ | -------------------------- | ------------------------------------------------------------------------------------------------------ |
| `400`  | Email ya registrado        | `{"detail": "A user with this email already exists"}`                                                  |
| `400`  | Contraseña demasiado larga | `{"detail": "Password cannot exceed 72 bytes in length"}`                                              |
| `400`  | Datos inválidos            | `{"detail": "Invalid registration data"}`                                                              |
| `422`  | Validación Pydantic        | `{"detail": [{"loc": ["body", "email"], "msg": "invalid email format", "type": "value_error.email"}]}` |

##### POST /api/v1/auth/login

| Código | Error                    | Ejemplo                                                                                            |
| ------ | ------------------------ | -------------------------------------------------------------------------------------------------- |
| `401`  | Credenciales incorrectas | `{"detail": "Incorrect email or password"}`                                                        |
| `422`  | Validación Pydantic      | `{"detail": [{"loc": ["body", "email"], "msg": "field required", "type": "value_error.missing"}]}` |

##### POST /api/v1/auth/refresh

| Código | Error                  | Ejemplo                                                                                                    |
| ------ | ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| `401`  | Refresh token inválido | `{"detail": "Invalid refresh token"}`                                                                      |
| `401`  | Usuario no encontrado  | `{"detail": "Invalid refresh token"}`                                                                      |
| `422`  | Validación Pydantic    | `{"detail": [{"loc": ["body", "refresh_token"], "msg": "field required", "type": "value_error.missing"}]}` |

---

#### Proyectos

##### POST /api/v1/projects

| Código | Error                     | Ejemplo                                                                                                                                     |
| ------ | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                                                    |
| `422`  | Validación Pydantic       | `{"detail": [{"loc": ["body", "titulo"], "msg": "ensure this value has at least 5 characters", "type": "value_error.any_str.min_length"}]}` |
| `422`  | Validación del servicio   | `{"detail": "Invalid proyecto data"}`                                                                                                       |
| `500`  | Error del servidor        | `{"detail": "Error creating proyecto: Database error"}`                                                                                     |

##### GET /api/v1/projects/{project_id}

| Código | Error                     | Ejemplo                                                                         |
| ------ | ------------------------- | ------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                        |
| `404`  | Proyecto no encontrado    | `{"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"}` |

##### PATCH /api/v1/projects/{project_id}

| Código | Error                     | Ejemplo                                                                                                                    |
| ------ | ------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                                   |
| `403`  | No eres el dueño          | `{"detail": "Forbidden - User is not the owner of this resource"}`                                                         |
| `404`  | Proyecto no encontrado    | `{"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"}`                                            |
| `422`  | Validación Pydantic       | `{"detail": [{"loc": ["body", "bonita_case_id"], "msg": "string does not match regex", "type": "value_error.str.regex"}]}` |

##### DELETE /api/v1/projects/{project_id}

| Código | Error                     | Ejemplo                                                                         |
| ------ | ------------------------- | ------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                        |
| `403`  | No eres el dueño          | `{"detail": "You are not the owner of this project"}`                           |
| `404`  | Proyecto no encontrado    | `{"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"}` |

##### POST /api/v1/projects/{project_id}/start

| Código | Error                      | Ejemplo                                                                                                                                                                                                                                                                                                     |
| ------ | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante  | `{"detail": "Invalid or expired token"}`                                                                                                                                                                                                                                                                    |
| `403`  | No eres el dueño           | `{"detail": "Only the project owner can perform this action"}`                                                                                                                                                                                                                                              |
| `404`  | Proyecto no encontrado     | `{"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"}`                                                                                                                                                                                                                             |
| `400`  | Estado incorrecto          | `{"detail": "Project can only be started from 'pendiente' state. Current state: en_ejecucion"}`                                                                                                                                                                                                      |
| `400`  | Pedidos no completados     | `{"detail": {"message": "No se puede iniciar el proyecto. 3 pedidos no están completados", "pedidos_pendientes": [{"pedido_id": "323e4567...", "etapa_nombre": "Fase 1", "tipo": "economico", "estado": "COMPROMETIDO", "descripcion": "Presupuesto para materiales de cimentación"}]}}`                  |

---

#### Pedidos

##### POST /api/v1/projects/{project_id}/etapas/{etapa_id}/pedidos

| Código | Error                         | Ejemplo                                                                                                                |
| ------ | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante     | `{"detail": "Invalid or expired token"}`                                                                               |
| `403`  | No eres el dueño del proyecto | `{"detail": "You are not the owner of this project"}`                                                                  |
| `404`  | Proyecto no encontrado        | `{"detail": "Proyecto with id ... not found"}`                                                                         |
| `404`  | Etapa no encontrada           | `{"detail": "Etapa with id ... not found in proyecto"}`                                                                |
| `422`  | Validación Pydantic           | `{"detail": [{"loc": ["body", "tipo"], "msg": "value is not a valid enumeration member", "type": "type_error.enum"}]}` |

##### GET /api/v1/projects/{project_id}/pedidos

| Código | Error                     | Ejemplo                                                                                                             |
| ------ | ------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                            |
| `404`  | Proyecto no encontrado    | `{"detail": "Proyecto with id ... not found"}`                                                                      |
| `422`  | Filtro estado inválido    | `{"detail": [{"loc": ["query", "estado"], "msg": "string does not match regex", "type": "value_error.str.regex"}]}` |

##### DELETE /api/v1/pedidos/{pedido_id}

| Código | Error                         | Ejemplo                                               |
| ------ | ----------------------------- | ----------------------------------------------------- |
| `401`  | Token inválido o faltante     | `{"detail": "Invalid or expired token"}`              |
| `403`  | No eres el dueño del proyecto | `{"detail": "You are not the owner of this project"}` |
| `404`  | Pedido no encontrado          | `{"detail": "Pedido with id ... not found"}`          |

---

#### Ofertas

##### POST /api/v1/pedidos/{pedido_id}/ofertas

| Código | Error                     | Ejemplo                                                                                                  |
| ------ | ------------------------- | -------------------------------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                 |
| `404`  | Pedido no encontrado      | `{"detail": "Pedido with id ... not found"}`                                                             |
| `422`  | Validación Pydantic       | `{"detail": [{"loc": ["body", "descripcion"], "msg": "field required", "type": "value_error.missing"}]}` |

##### GET /api/v1/pedidos/{pedido_id}/ofertas

| Código | Error                         | Ejemplo                                               |
| ------ | ----------------------------- | ----------------------------------------------------- |
| `401`  | Token inválido o faltante     | `{"detail": "Invalid or expired token"}`              |
| `403`  | No eres el dueño del proyecto | `{"detail": "You are not the owner of this project"}` |
| `404`  | Pedido no encontrado          | `{"detail": "Pedido with id ... not found"}`          |

##### POST /api/v1/ofertas/{oferta_id}/accept

| Código | Error                         | Ejemplo                                                   |
| ------ | ----------------------------- | --------------------------------------------------------- |
| `401`  | Token inválido o faltante     | `{"detail": "Invalid or expired token"}`                  |
| `403`  | No eres el dueño del proyecto | `{"detail": "You are not the owner of this project"}`     |
| `404`  | Oferta no encontrada          | `{"detail": "Oferta with id ... not found"}`              |
| `400`  | Pedido ya completado          | `{"detail": "Cannot accept oferta for completed pedido"}` |
| `400`  | Pedido ya comprometido        | `{"detail": "Cannot accept oferta for committed pedido"}` |

##### POST /api/v1/ofertas/{oferta_id}/reject

| Código | Error                         | Ejemplo                                               |
| ------ | ----------------------------- | ----------------------------------------------------- |
| `401`  | Token inválido o faltante     | `{"detail": "Invalid or expired token"}`              |
| `403`  | No eres el dueño del proyecto | `{"detail": "You are not the owner of this project"}` |
| `404`  | Oferta no encontrada          | `{"detail": "Oferta with id ... not found"}`          |

##### POST /api/v1/ofertas/{oferta_id}/confirmar-realizacion

| Código | Error                           | Ejemplo                                                                                         |
| ------ | ------------------------------- | ----------------------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante       | `{"detail": "Invalid or expired token"}`                                                        |
| `403`  | No eres el creador de la oferta | `{"detail": "You are not the creator of this oferta"}`                                          |
| `404`  | Oferta no encontrada            | `{"detail": "Oferta with id ... not found"}`                                                    |
| `400`  | Compromiso ya confirmado        | `{"detail": "This commitment has already been confirmed and marked as completado"}`             |
| `400`  | Estado de pedido incorrecto     | `{"detail": "Cannot confirm realization. Pedido is in state pendiente, expected comprometido"}` |

##### GET /api/v1/ofertas/mis-compromisos

| Código | Error                     | Ejemplo                                                                                                                          |
| ------ | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `401`  | Token inválido o faltante | `{"detail": "Invalid or expired token"}`                                                                                         |
| `422`  | Filtro estado inválido    | `{"detail": [{"loc": ["query", "estado_pedido"], "msg": "value is not a valid enumeration member", "type": "type_error.enum"}]}` |

---

### Ejemplos de Respuestas de Error

#### Error 401 - Sin Autenticación

```json
{
	"detail": "Invalid or expired token"
}
```

#### Error 403 - Sin Permiso

```json
{
	"detail": "You are not the owner of this project"
}
```

#### Error 404 - No Encontrado

```json
{
	"detail": "Proyecto with id 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

#### Error 422 - Validación Fallida

```json
{
	"detail": [
		{
			"loc": ["body", "email"],
			"msg": "invalid email format",
			"type": "value_error.email"
		},
		{
			"loc": ["body", "password"],
			"msg": "field required",
			"type": "value_error.missing"
		}
	]
}
```

#### Error 400 - Regla de Negocio Violada

```json
{
	"detail": "A user with this email already exists"
}
```

#### Error 500 - Error del Servidor

```json
{
	"detail": "Error creating proyecto: Unexpected database error"
}
```

---

### Cómo Interpretar Errores 422 (Validación)

Los errores de validación retornan un array de objetos con:

-   **loc**: Ubicación del error (ej: `["body", "email"]` significa error en el campo email del body)
-   **msg**: Mensaje descriptivo del error
-   **type**: Tipo de error Pydantic

**Ejemplo completo:**

```json
{
	"detail": [
		{
			"loc": ["body", "titulo"],
			"msg": "ensure this value has at least 5 characters",
			"type": "value_error.any_str.min_length"
		}
	]
}
```

**Solución**: El campo `titulo` debe tener al menos 5 caracteres.

---

## Instrucciones para Pruebas

### Quick Start - La Forma Más Rápida

**¡Sin instalación, solo 3 pasos!**

1. **Abre en tu navegador:**

    ```
    https://project-planning-cloud-api.onrender.com/docs
    ```

2. **Haz click en "POST /api/v1/auth/register"** → "Try it out"

3. **Completa los datos de prueba:**

    ```json
    {
    	"email": "profesor@test.com",
    	"password": "Test1234",
    	"nombre": "Profesor",
    	"apellido": "Corrector",
    	"ong": "Universidad"
    }
    ```

4. **Click "Execute"**

¡Listo! Ya tienes un usuario. Ahora puedes probar cualquier endpoint directamente desde Swagger.

---

### Opción 1: Swagger UI (Recomendado)

Esta es la forma más fácil y no requiere instalar nada.

1. **Abre en tu navegador:**

    ```
    https://project-planning-cloud-api.onrender.com/docs
    ```

2. **Autentzate:**

    - Busca "POST /api/v1/auth/login"
    - Click "Try it out"
    - Usa los datos del paso anterior para login
    - Click "Execute"
    - Copia el `access_token`
    - Haz click en el botón **"Authorize"** (arriba a la derecha)
    - Pega: `Bearer {tu_access_token}`
    - Click "Authorize"

3. **Prueba cualquier endpoint:**
    - Todos los endpoints están listados
    - Click "Try it out" en cualquiera
    - Completa los parámetros/body
    - Click "Execute"

---

### Opción 2: Postman

**Si prefieres usar Postman:**

1. Descarga: https://www.postman.com/downloads/
2. Crea nueva petición POST
3. URL: `https://project-planning-cloud-api.onrender.com/api/v1/auth/register`
4. Body (JSON): usa el ejemplo de arriba
5. Click "Send"
6. Para endpoints protegidos:
    - Tab "Authorization" → Type: "Bearer Token"
    - Token: pega tu access_token

---

### Opción 3: cURL (Terminal)

```bash
# 1. Registrar
curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"profesor@test.com","password":"Test1234","nombre":"Profesor","apellido":"Corrector","ong":"Universidad"}'

# 2. Login
curl -X POST https://project-planning-cloud-api.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"profesor@test.com","password":"Test1234"}'
```

---

## Checklist de Pruebas

**Use este checklist para validar que todos los endpoints funcionan correctamente:**

### Autenticación

-   [ ] POST `/api/v1/auth/register` - Crear nuevo usuario
-   [ ] POST `/api/v1/auth/login` - Obtener tokens
-   [ ] POST `/api/v1/auth/refresh` - Refrescar token

### Proyectos

-   [ ] POST `/api/v1/projects` - Crear proyecto con etapas y pedidos anidados
-   [ ] GET `/api/v1/projects/{project_id}` - Obtener proyecto completo
-   [ ] PATCH `/api/v1/projects/{project_id}` - Actualizar proyecto
-   [ ] DELETE `/api/v1/projects/{project_id}` - Eliminar proyecto
-   [ ] GET `/api/v1/projects/{project_id}/pedidos` - Listar pedidos de proyecto

### Pedidos

-   [ ] POST `/api/v1/projects/{project_id}/etapas/{etapa_id}/pedidos` - Crear pedido
-   [ ] GET `/api/v1/projects/{project_id}/pedidos?estado=PENDIENTE` - Filtrar pendientes
-   [ ] DELETE `/api/v1/pedidos/{pedido_id}` - Eliminar pedido

### Ofertas

-   [ ] POST `/api/v1/pedidos/{pedido_id}/ofertas` - Crear oferta
-   [ ] GET `/api/v1/pedidos/{pedido_id}/ofertas` - Listar ofertas para pedido
-   [ ] POST `/api/v1/ofertas/{oferta_id}/accept` - Aceptar oferta
-   [ ] POST `/api/v1/ofertas/{oferta_id}/reject` - Rechazar oferta
-   [ ] POST `/api/v1/ofertas/{oferta_id}/confirmar-realizacion` - Confirmar realización
-   [ ] GET `/api/v1/ofertas/mis-compromisos` - Ver mis compromisos

---

## Soporte

-   **Swagger Interactivo:** https://project-planning-cloud-api.onrender.com/docs
-   **Health Check:** https://project-planning-cloud-api.onrender.com/health
-   **OpenAPI JSON:** https://project-planning-cloud-api.onrender.com/openapi.json

---

**Fin de Documentación**
