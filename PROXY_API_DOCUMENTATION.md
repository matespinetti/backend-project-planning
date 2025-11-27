# ProjectPlanning Proxy API — Documentación de Flujos Bonita

**Versión:** 2.3.0
**Última actualización:** 2025-11-21
**Alcance:** endpoints que orquestan la Cloud Persistence API y Bonita BPM (no simples proxys)

---

## Tabla de contenidos

1. [Introducción](#introducción)
2. [Servicios y URLs](#servicios-y-urls)
3. [Autenticación](#autenticación)
4. [Endpoint · Crear Proyecto + Instanciar Proceso](#1️⃣-crear-proyecto--instanciar-proceso-bonita)
5. [Endpoint · Iniciar Proyecto ejecutando ConfirmStartProject](#2️⃣-iniciar-proyecto-ejecutando-confirmdartproject)
6. [Endpoint · Evaluar Oferta mediante Bonita](#3️⃣-evaluar-oferta-mediante-bonita)
7. [Endpoint · Iniciar Etapa ejecutando StartStage](#4️⃣-iniciar-etapa-ejecutando-startstage)
8. [Endpoint · Completar Etapa ejecutando FinishStage](#5️⃣-completar-etapa-ejecutando-finishstage)
9. [Endpoint · Finalizar Proyecto ejecutando FinishProject](#6️⃣-finalizar-proyecto-ejecutando-finishproject)
10. [Endpoint · Crear Observación + Instanciar ObservationsReviewal](#7️⃣-crear-observación--instanciar-observationsreviewal)
11. [Endpoint · Resolver Observación ejecutando SolveObservation](#8️⃣-resolver-observación-ejecutando-solveobservation)
12. [Códigos de error comunes](#códigos-de-error-comunes)

---

## Introducción

Esta API FastAPI actúa como **proxy stateless** entre el frontend (Next.js), la **Cloud Persistence API** (dueña del JWT y la base de datos) y **Bonita BPM** (motor de workflows).  
Los endpoints descritos aquí son los únicos que contienen lógica adicional: validan datos, coordinan múltiples servicios y aplican reglas de rollback para mantener la integridad del proceso.

---

## Servicios y URLs

| Servicio                     | Descripción                                               | URL / Configuración                      |
| ---------------------------- | --------------------------------------------------------- | ---------------------------------------- |
| Proxy FastAPI                | Punto de entrada para el frontend                         | Local por defecto: `http://localhost:8000` |
| Prefijo API                  | Todas las rutas expuestas                                 | `/api/v1`                                |
| Cloud Persistence API        | Persiste proyectos/pedidos/ofertas y emite JWT            | `CLOUD_API_URL` (var. de entorno)        |
| Bonita BPM                   | Motor del proceso `BONITA_PROCESS_NAME` (p.ej. ProyectyCreation) | `BONITA_URL` (var. de entorno)           |

---

## Autenticación

- Todos los endpoints requieren `Authorization: Bearer <access_token>` emitido por la **Cloud API**.  
- El proxy valida la firma con el secreto compartido, reutiliza el token en cada llamada al Cloud API y **nunca emite JWT propios**.  
- Contenido JSON: `Content-Type: application/json`.

---

## 1️⃣ Crear Proyecto + Instanciar Proceso Bonita

| Propiedad     | Valor                                                             |
| ------------- | ----------------------------------------------------------------- |
| **Método**    | `POST`                                                            |
| **Ruta**      | `/api/v1/projects`                                                |
| **Auth**      | JWT Cloud (`Bearer`)                                              |
| **HTTP 201**  | Proyecto persistido en Cloud API + proceso `BONITA_PROCESS_NAME` iniciado |

### Resumen funcional

1. **Validación Pydantic** (`ProyectoCreate` + sub-esquemas `EtapaCreate` y `PedidoCreate`).  
2. **Persistencia en Cloud API:** se envía el payload y se obtiene el `project_id` real.  
3. **Arranque de Bonita:** se crea una instancia del proceso configurado, enviando `{"project_id": "<uuid>"}` como contrato de inicio.  
4. **Actualización en Cloud:** se parchea el proyecto con `bonita_case_id` y `bonita_process_instance_id`.  
5. **Respuesta al frontend:** se devuelve la entidad persistida + metadata Bonita (`bonita_process_url`) para facilitar deep-links.

```
Frontend ──POST /projects──► Proxy
Proxy ──POST /api/v1/projects──► Cloud API (crea proyecto)
Proxy ──POST /API/bpm/process/{id}/instantiation──► Bonita (recibe project_id)
Proxy ──PATCH /api/v1/projects/{id}──► Cloud API (guarda case_id)
Proxy ◄─201 + payload orquestado── Frontend
```

### Request Body (`ProyectoCreate`)

| Campo                  | Tipo / Reglas                                               | Descripción                                                                 |
| ---------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------- |
| `titulo`               | `string` (≥ 5)                                              | Nombre del proyecto                                                         |
| `descripcion`          | `string` (≥ 20)                                             | Descripción completa                                                        |
| `tipo`                 | `string`                                                    | Categoría (educación, salud, etc.)                                          |
| `pais` / `provincia` / `ciudad` | `string`                                          | Localización                                                                |
| `barrio`               | `string` opcional                                           | Barrio o zona                                                                |
| `etapas[]`             | Lista de `EtapaCreate` (mínimo una)                         | Cada etapa valida fechas ISO (`YYYY-MM-DD`) y requiere al menos un pedido   |
| `etapas[].pedidos[]`   | Lista de `PedidoCreate`                                     | Define pedidos `economico`, `materiales`, `mano_obra`, `transporte`, `equipamiento` |

#### Ejemplo de request

```json
{
  "titulo": "Construcción Aula Digital",
  "descripcion": "Creamos un aula equipada para capacitaciones comunitarias.",
  "tipo": "educacion",
  "pais": "Argentina",
  "provincia": "Buenos Aires",
  "ciudad": "La Plata",
  "etapas": [
    {
      "nombre": "Infraestructura",
      "descripcion": "Preparación del espacio físico",
      "fecha_inicio": "2025-12-01",
      "fecha_fin": "2026-01-30",
      "pedidos": [
        {
          "tipo": "materiales",
          "descripcion": "Compra de ladrillos y cemento",
          "cantidad": 500,
          "unidad": "unidad"
        }
      ]
    }
  ]
}
```

### Respuesta 201 (`ProyectoCreateResponse`)

```json
{
  "proyecto": {
    "id": "64be9f36-32d7-4ac8-97de-e614a76c6bb1",
    "titulo": "Construcción Aula Digital",
    "descripcion": "Creamos un aula equipada para capacitaciones comunitarias.",
    "tipo": "educacion",
    "estado": "en_planificacion",
    "pais": "Argentina",
    "provincia": "Buenos Aires",
    "ciudad": "La Plata",
    "bonita_case_id": "501",
    "bonita_process_instance_id": 4201,
    "created_at": "2025-11-20T14:22:01.123Z",
    "updated_at": "2025-11-20T14:22:01.123Z",
    "etapas": [
      {
        "id": "72c9d7b8-1e20-4ac7-a831-3245c83c8f46",
        "nombre": "Infraestructura",
        "descripcion": "Preparación del espacio físico",
        "fecha_inicio": "2025-12-01",
        "fecha_fin": "2026-01-30",
        "proyecto_id": "64be9f36-32d7-4ac8-97de-e614a76c6bb1",
        "pedidos": [
          {
            "id": "b3f43d0a-3a4c-41fb-9d76-995f5409ef73",
            "tipo": "materiales",
            "descripcion": "Compra de ladrillos y cemento",
            "estado": "pendiente",
            "etapa_id": "72c9d7b8-1e20-4ac7-a831-3245c83c8f46"
          }
        ]
      }
    ]
  },
  "bonita_case_id": "501",
  "bonita_process_url": "https://bonita.example.com/portal/resource/processInstance/501/content/",
  "message": "Proyecto creado exitosamente e iniciado en Bonita"
}
```

### Errores y rollback

| Código | Origen | Descripción                                                                                                   |
| ------ | ------ | ------------------------------------------------------------------------------------------------------------- |
| `422`  | Proxy  | Validación Pydantic (campos obligatorios, fechas, pedidos vacíos).                                            |
| `500`  | Cloud  | Falla al persistir el proyecto: no hay payload de Cloud API → no se crea nada.                                |
| `500`  | Bonita | `BonitaClient.start_process` retorna `None`: se hace **rollback** (`DELETE /api/v1/projects/{id}`) y se informa que debe reintentar. |
| `500`  | Bonita/Cloud | Error inesperado luego de crear el proyecto: se intenta rollback y se detalla si la eliminación también falló.      |
| `502/504` | Red | Errores de red propagados desde el Cloud API.                                                                 |

> Nota: Si la actualización final (`update_project_bonita_info`) falla, **no se hace rollback** porque el proyecto existe y Bonita está corriendo; solo se registra una advertencia.

---

## 2️⃣ Iniciar Proyecto ejecutando ConfirmStartProject

| Propiedad     | Valor                                              |
| ------------- | -------------------------------------------------- |
| **Método**    | `POST`                                             |
| **Ruta**      | `/api/v1/projects/{project_id}/start`              |
| **Auth**      | JWT Cloud (`Bearer`)                               |
| **HTTP 200**  | Tarea humana `ConfirmStartProject` completada en Bonita y proyecto actualizado a `en_ejecucion` en Cloud API |

### Precondiciones

- El proyecto debe existir en Cloud API.
- El proyecto debe tener `bonita_case_id` asignado (generado en el endpoint de creación).
- Debe existir una tarea humana *ready* llamada **"ConfirmStartProject"** para ese `caseId`.
- Todos los pedidos deben estar en estado `COMPROMETIDO` o `COMPLETADO` (validado por Cloud API via Bonita connectors).

### Flujo detallado

1. **Lectura de proyecto en Cloud API** (`GET /api/v1/projects/{project_id}`): obtener `bonita_case_id`.
2. **Bonita:** buscar tareas pendientes (`/API/bpm/humanTask?f=caseId=...&f=name=ConfirmStartProject`).
3. **Asignación:** si la tarea no está asignada, asignarla al usuario autenticado.
4. **Ejecución tarea:** enviar contrato vacío `{}`.
5. **Conectores Bonita** actualizan el estado del proyecto a `en_ejecucion` en la Cloud API.
6. **Sync final:** el proxy espera ~2 segundos y vuelve a leer el proyecto para devolver su estado final.

```
Frontend ──POST /projects/{id}/start──► Proxy
Proxy ──GET /api/v1/projects/{id}──► Cloud API (bonita_case_id)
Proxy ──GET humanTask?caseId={case}──► Bonita
Proxy ──PUT humanTask/{taskId}──► Bonita (asignar)
Proxy ──POST userTask/{taskId}/execution──► Bonita ({})
Bonita connectors ──POST /api/v1/projects/{id}/start──► Cloud API
Proxy ──GET /api/v1/projects/{id}──► Cloud API (estado actualizado)
Proxy ◄─200 + proyecto actualizado── Frontend
```

### Request (vacío)

```http
POST /api/v1/projects/64be9f36-32d7-4ac8-97de-e614a76c6bb1/start
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{}
```

### Respuesta 200 (`ProyectoResponse`)

```json
{
  "id": "64be9f36-32d7-4ac8-97de-e614a76c6bb1",
  "titulo": "Construcción Aula Digital",
  "descripcion": "Creamos un aula equipada para capacitaciones comunitarias.",
  "tipo": "educacion",
  "pais": "Argentina",
  "provincia": "Buenos Aires",
  "ciudad": "La Plata",
  "estado": "en_ejecucion",
  "bonita_case_id": "501",
  "bonita_process_instance_id": 4201,
  "created_at": "2025-11-20T10:00:00.000Z",
  "updated_at": "2025-11-20T15:45:30.123Z",
  "etapas": [...]
}
```

### Errores frecuentes

| Código | Origen  | Descripción                                                                                           |
| ------ | ------- | ----------------------------------------------------------------------------------------------------- |
| `404`  | Cloud   | No existe el proyecto consultado.                                                                      |
| `400`  | Proxy   | El proyecto no tiene `bonita_case_id` asignado (no se inició en Bonita en la creación).               |
| `404`  | Bonita  | No hay tareas *ready* "ConfirmStartProject" para ese caseId (ya fue tomada o nunca se generó).        |
| `500`  | Bonita  | Falló la ejecución de la tarea (error de contrato, sesión, etc.).                                      |
| `500`  | Proxy   | Bonita ejecutó la tarea pero no se pudo volver a leer el proyecto actualizado (ver logs de Cloud API). |

---

## 3️⃣ Evaluar Oferta mediante Bonita

| Propiedad     | Valor                                              |
| ------------- | -------------------------------------------------- |
| **Método**    | `POST`                                             |
| **Ruta**      | `/api/v1/ofertas/{oferta_id}/evaluate`             |
| **Auth**      | JWT Cloud (`Bearer`)                               |
| **HTTP 200**  | Tarea humana `Evaluate Offer` completada en Bonita y oferta actualizada en Cloud API |

### Precondiciones

- La oferta debe tener un pedido asociado; el pedido debe pertenecer a una etapa y esta a un proyecto.  
- El proyecto debe almacenar `bonita_case_id` (llenado en el endpoint anterior).  
- Debe existir una tarea humana *ready* llamada **"Evaluate Offer"** para ese `caseId`.

### Flujo detallado

1. **Lectura de oferta en Cloud API** (`GET /api/v1/ofertas/{id}`) que ya incluye `pedido` y `proyecto` (con `bonita_case_id`).  
2. **(Opcional) Fallback:** solo si falta `bonita_case_id` se consulta Cloud API por pedido/etapa/proyecto para reconstruir el contexto.  
3. **Bonita:** buscar tareas pendientes (`/API/bpm/humanTask?f=caseId=...&f=displayName=Evaluate%20Offer`).  
4. **Ejecución tarea:** se envían los inputs del contrato `{"decision": "accept" | "reject", "oferta_id": "<uuid>"}`.  
5. **Conectores Bonita** llaman internamente a `accept_oferta` / `reject_oferta` en la Cloud API.  
6. **Sync final:** el proxy espera ~2 segundos y vuelve a leer la oferta para devolver su estado final.

```
Frontend ──POST /ofertas/{id}/evaluate──► Proxy
Proxy ──GET /api/v1/ofertas/{id}──► Cloud API (pedido + proyecto + bonita_case_id)
Proxy ──GET humanTask?caseId={case}──► Bonita
Proxy ──POST userTask/{taskId}/execution──► Bonita (decision)
Bonita ──(connector)──► Cloud API accept/reject
Proxy ──GET /api/v1/ofertas/{id}──► Cloud API (estado final)
Proxy ◄─200 + oferta actualizada── Frontend
```

### Request Body (`OfertaEvaluationRequest`)

| Campo     | Tipo / Reglas                               | Descripción                                     |
| --------- | ------------------------------------------- | ----------------------------------------------- |
| `decision`| `string`, regex `^(accept\|reject)$`        | Indica si se acepta o rechaza la oferta         |

#### Ejemplo

```http
POST /api/v1/ofertas/7c64f2fb-d93b-4efa-a228-e7924507241e/evaluate
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "decision": "accept"
}
```

### Respuesta 200 (`OfertaResponse`)

```json
{
  "id": "7c64f2fb-d93b-4efa-a228-e7924507241e",
  "pedido_id": "1f6326cb-e2d9-4a5d-902d-f5d8720d2f34",
  "user_id": "0815c031-b8dd-4a50-9d7a-fc4484ffe735",
  "descripcion": "Puedo donar el mobiliario completo",
  "monto_ofrecido": 0,
  "estado": "aceptada",
  "created_at": "2025-11-15T10:00:11.911Z",
  "updated_at": "2025-11-20T15:33:42.001Z",
  "user": {
    "id": "0815c031-b8dd-4a50-9d7a-fc4484ffe735",
    "email": "donante@example.com",
    "nombre": "Ana",
    "apellido": "Paz",
    "ong": "Fundación Conecta"
  }
}
```

### Errores frecuentes

| Código | Origen  | Descripción                                                                                           |
| ------ | ------- | ----------------------------------------------------------------------------------------------------- |
| `404`  | Cloud   | No existe la oferta/pedido/etapa/proyecto consultado.                                                  |
| `400`  | Proxy   | La oferta/pedido/etapa no están encadenados correctamente o al proyecto le falta `bonita_case_id`.     |
| `404`  | Bonita  | No hay tareas *ready* "Evaluate Offer" para ese caseId (ya fue tomada o nunca se generó).              |
| `500`  | Bonita  | Falló la ejecución de la tarea (error de contrato, sesión, etc.).                                      |
| `500`  | Proxy   | Bonita ejecutó la tarea pero no se pudo volver a leer la oferta actualizada (ver logs de Cloud API).   |
| `422`  | Proxy   | `decision` no cumple con el patrón `accept|reject`.                                                    |

---

## 4️⃣ Iniciar Etapa ejecutando StartStage

| Propiedad     | Valor                                              |
| ------------- | -------------------------------------------------- |
| **Método**    | `POST`                                             |
| **Ruta**      | `/api/v1/etapas/{etapa_id}/start`                 |
| **Auth**      | JWT Cloud (`Bearer`)                               |
| **HTTP 200**  | Tarea humana `StartStage` completada en Bonita y etapa actualizada a `en_ejecucion` en Cloud API |

### Precondiciones

- La etapa debe existir en Cloud API.
- La etapa debe tener `bonita_case_id` asignado (generado en el proceso `StageExecution` de Bonita).
- Debe existir una tarea humana *ready* llamada **"StartStage"** para ese `caseId`.
- Todos los pedidos de la etapa deben estar en estado `COMPROMETIDO` o `COMPLETADO` (validado por Cloud API).

### Flujo detallado

1. **Lectura de etapa en Cloud API** (`GET /api/v1/etapas/{etapa_id}`): obtener `bonita_case_id`.
2. **Bonita:** buscar tareas pendientes (`/API/bpm/humanTask?f=caseId=...&f=name=StartStage`).
3. **Asignación:** si la tarea no está asignada, asignarla al usuario autenticado.
4. **Ejecución tarea:** enviar contrato vacío `{}`.
5. **Conectores Bonita** actualizan el estado de la etapa a `en_ejecucion` en la Cloud API.
6. **Sync final:** el proxy espera ~2 segundos y vuelve a leer la etapa para devolver su estado final.

```
Frontend ──POST /etapas/{id}/start──► Proxy
Proxy ──GET /api/v1/etapas/{id}──► Cloud API (bonita_case_id)
Proxy ──GET humanTask?caseId={case}──► Bonita
Proxy ──PUT humanTask/{taskId}──► Bonita (asignar)
Proxy ──POST userTask/{taskId}/execution──► Bonita ({})
Bonita connectors ──POST /api/v1/etapas/{id}/start──► Cloud API
Proxy ──GET /api/v1/etapas/{id}──► Cloud API (estado actualizado)
Proxy ◄─200 + etapa actualizada── Frontend
```

### Request (vacío)

```http
POST /api/v1/etapas/223e4567-e89b-12d3-a456-426614174111/start
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{}
```

### Respuesta 200 (`EtapaDetailResponse`)

```json
{
  "id": "223e4567-e89b-12d3-a456-426614174111",
  "proyecto_id": "64be9f36-32d7-4ac8-97de-e614a76c6bb1",
  "nombre": "Fundaciones y Estructura",
  "descripcion": "Excavación, cimientos y estructura de hormigón armado",
  "fecha_inicio": "2025-12-01",
  "fecha_fin": "2026-01-30",
  "estado": "en_ejecucion",
  "bonita_case_id": "8003",
  "bonita_process_instance_id": 4202,
  "pendientes_count": 0,
  "total_pedidos": 1
}
```

### Errores frecuentes

| Código | Origen  | Descripción                                                                                           |
| ------ | ------- | ----------------------------------------------------------------------------------------------------- |
| `404`  | Cloud   | No existe la etapa consultada.                                                                         |
| `400`  | Proxy   | La etapa no tiene `bonita_case_id` asignado (no está integrada con Bonita `StageExecution`).         |
| `404`  | Bonita  | No hay tareas *ready* "StartStage" para ese caseId (ya fue tomada o nunca se generó).                |
| `500`  | Bonita  | Falló la ejecución de la tarea (error de contrato, sesión, etc.).                                      |
| `500`  | Proxy   | Bonita ejecutó la tarea pero no se pudo volver a leer la etapa actualizada (ver logs de Cloud API).   |

---

## 5️⃣ Completar Etapa ejecutando FinishStage

| Propiedad     | Valor                                              |
| ------------- | -------------------------------------------------- |
| **Método**    | `POST`                                             |
| **Ruta**      | `/api/v1/etapas/{etapa_id}/complete`              |
| **Auth**      | JWT Cloud (`Bearer`)                               |
| **HTTP 200**  | Tarea humana `FinishStage` completada en Bonita y etapa actualizada a `completada` en Cloud API |

### Precondiciones

- La etapa debe existir en Cloud API.
- La etapa debe estar en estado `en_ejecucion`.
- La etapa debe tener `bonita_case_id` asignado (generado en el proceso `StageExecution` de Bonita).
- Debe existir una tarea humana *ready* llamada **"FinishStage"** para ese `caseId`.
- El usuario debe ser el propietario del proyecto o un administrador.

### Flujo detallado

1. **Lectura de etapa en Cloud API** (`GET /api/v1/etapas/{etapa_id}`): obtener `bonita_case_id`.
2. **Bonita:** buscar tareas pendientes (`/API/bpm/humanTask?f=parentCaseId=...&f=name=FinishStage`).
3. **Asignación:** si la tarea no está asignada, asignarla al usuario autenticado.
4. **Ejecución tarea:** enviar contrato vacío `{}`.
5. **Conectores Bonita** actualizan el estado de la etapa a `completada` en la Cloud API y establecen `fecha_completitud`.
6. **Sync final:** el proxy espera ~2 segundos y vuelve a leer la etapa para devolver su estado final.

```
Frontend ──POST /etapas/{id}/complete──► Proxy
Proxy ──GET /api/v1/etapas/{id}──► Cloud API (bonita_case_id)
Proxy ──GET humanTask?parentCaseId={case}──► Bonita
Proxy ──PUT humanTask/{taskId}──► Bonita (asignar)
Proxy ──POST userTask/{taskId}/execution──► Bonita ({})
Bonita connectors ──POST /api/v1/etapas/{id}/complete──► Cloud API
Proxy ──GET /api/v1/etapas/{id}──► Cloud API (estado actualizado + fecha_completitud)
Proxy ◄─200 + etapa actualizada── Frontend
```

### Request (vacío)

```http
POST /api/v1/etapas/223e4567-e89b-12d3-a456-426614174111/complete
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{}
```

### Respuesta 200 (`EtapaDetailResponse`)

```json
{
  "id": "223e4567-e89b-12d3-a456-426614174111",
  "proyecto_id": "64be9f36-32d7-4ac8-97de-e614a76c6bb1",
  "nombre": "Fundaciones y Estructura",
  "descripcion": "Excavación, cimientos y estructura de hormigón armado",
  "fecha_inicio": "2025-12-01",
  "fecha_fin": "2026-01-30",
  "estado": "completada",
  "bonita_case_id": "8003",
  "bonita_process_instance_id": 4202,
  "fecha_completitud": "2025-12-15T14:30:00Z",
  "pendientes_count": 0,
  "total_pedidos": 1
}
```

### Errores frecuentes

| Código | Origen  | Descripción                                                                                           |
| ------ | ------- | ----------------------------------------------------------------------------------------------------- |
| `404`  | Cloud   | No existe la etapa consultada.                                                                         |
| `400`  | Proxy   | La etapa no tiene `bonita_case_id` asignado (no está integrada con Bonita `StageExecution`).         |
| `404`  | Bonita  | No hay tareas *ready* "FinishStage" para ese caseId (ya fue tomada o nunca se generó).                |
| `500`  | Bonita  | Falló la ejecución de la tarea (error de contrato, sesión, etc.).                                      |
| `500`  | Proxy   | Bonita ejecutó la tarea pero no se pudo volver a leer la etapa actualizada (ver logs de Cloud API).   |

---

## 6️⃣ Finalizar Proyecto ejecutando FinishProject

| Propiedad     | Valor                                              |
| ------------- | -------------------------------------------------- |
| **Método**    | `POST`                                             |
| **Ruta**      | `/api/v1/projects/{project_id}/complete`           |
| **Auth**      | JWT Cloud (`Bearer`)                               |
| **HTTP 200**  | Tarea humana `FinishProject` completada en Bonita y proyecto actualizado a `finalizado` en Cloud API |

### Precondiciones

- El proyecto debe existir en Cloud API.
- El proyecto debe estar en estado `en_ejecucion`.
- El proyecto debe tener `bonita_case_id` asignado (generado en el proceso `ProjectExecution` de Bonita).
- Debe existir una tarea humana *ready* llamada **"FinishProject"** para ese `caseId`.
- El usuario debe ser el propietario del proyecto o un administrador.
- Todas las etapas del proyecto deben estar completadas.

### Flujo detallado

1. **Lectura de proyecto en Cloud API** (`GET /api/v1/projects/{project_id}`): obtener `bonita_case_id`.
2. **Bonita:** buscar tareas pendientes (`/API/bpm/humanTask?f=caseId=...&f=name=FinishProject`).
3. **Asignación:** si la tarea no está asignada, asignarla al usuario autenticado.
4. **Ejecución tarea:** enviar contrato vacío `{}`.
5. **Conectores Bonita** actualizan el estado del proyecto a `finalizado` en la Cloud API.
6. **Sync final:** el proxy espera ~2 segundos y vuelve a leer el proyecto para devolver su estado final.

```
Frontend ──POST /projects/{id}/complete──► Proxy
Proxy ──GET /api/v1/projects/{id}──► Cloud API (bonita_case_id)
Proxy ──GET humanTask?caseId={case}──► Bonita
Proxy ──PUT humanTask/{taskId}──► Bonita (asignar)
Proxy ──POST userTask/{taskId}/execution──► Bonita ({})
Bonita connectors ──POST /api/v1/projects/{id}/complete──► Cloud API
Proxy ──GET /api/v1/projects/{id}──► Cloud API (estado actualizado)
Proxy ◄─200 + proyecto actualizado── Frontend
```

### Request (vacío)

```http
POST /api/v1/projects/64be9f36-32d7-4ac8-97de-e614a76c6bb1/complete
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{}
```

### Respuesta 200 (`ProyectoResponse`)

```json
{
  "id": "64be9f36-32d7-4ac8-97de-e614a76c6bb1",
  "titulo": "Centro Comunitario Testeable",
  "descripcion": "Centro comunitario con salón multiuso y cocina para 250 familias",
  "tipo": "Infraestructura Social",
  "pais": "Argentina",
  "provincia": "Buenos Aires",
  "ciudad": "La Plata",
  "barrio": "Barrio Norte",
  "estado": "finalizado",
  "bonita_case_id": "8062",
  "bonita_process_instance_id": 8062,
  "created_at": "2025-11-21T19:51:51Z",
  "updated_at": "2025-12-15T15:45:00Z"
}
```

### Errores frecuentes

| Código | Origen  | Descripción                                                                                           |
| ------ | ------- | ----------------------------------------------------------------------------------------------------- |
| `404`  | Cloud   | No existe el proyecto consultado.                                                                      |
| `400`  | Proxy   | El proyecto no tiene `bonita_case_id` asignado (no está integrado con Bonita `ProjectExecution`).     |
| `404`  | Bonita  | No hay tareas *ready* "FinishProject" para ese caseId (ya fue tomada o nunca se generó).              |
| `500`  | Bonita  | Falló la ejecución de la tarea (error de contrato, sesión, etc.).                                      |
| `500`  | Proxy   | Bonita ejecutó la tarea pero no se pudo volver a leer el proyecto actualizado (ver logs de Cloud API). |

---

## 7️⃣ Crear Observación + Instanciar ObservationsReviewal

| Propiedad     | Valor                                              |
| ------------- | -------------------------------------------------- |
| **Método**    | `POST`                                             |
| **Ruta**      | `/api/v1/projects/{project_id}/observaciones`     |
| **Auth**      | JWT Cloud (`Bearer`)                               |
| **HTTP 201**  | Observación persistida en Cloud API + proceso `ObservationsReviewal` iniciado |

### Precondiciones

- El proyecto debe existir en Cloud API.
- El proyecto debe estar en estado `en_ejecucion`.
- El usuario debe ser miembro del consejo (role=COUNCIL).
- La descripción debe tener mínimo 10 caracteres.

### Flujo detallado

1. **Lectura y validación en Proxy** (`POST /api/v1/projects/{project_id}/observaciones`): validación Pydantic del payload.
2. **Persistencia en Cloud API:** se envía el payload y se obtiene el `observacion_id` real (estado = `pendiente`, fecha_límite = +5 días automático).
3. **Arranque de Bonita:** se crea una instancia del proceso `ObservationsReviewal`, enviando `{"observacion_id": "<uuid>"}` como contrato de inicio.
4. **Actualización en Cloud API:** se parchea la observación con `bonita_case_id` y `bonita_process_instance_id` usando PATCH.
5. **Sync final:** el proxy vuelve a leer la observación para obtener el estado final.
6. **Respuesta al frontend:** se devuelve la entidad actualizada + metadata Bonita para tracking.

```
Frontend ──POST /projects/{id}/observaciones──► Proxy
Proxy ──POST /api/v1/projects/{id}/observaciones──► Cloud API (crea observación)
Proxy ──POST /API/bpm/process/{id}/instantiation──► Bonita (recibe observacion_id)
Proxy ──PATCH /api/v1/observaciones/{id}──► Cloud API (guarda case_id)
Proxy ──GET /api/v1/projects/{id}/observaciones──► Cloud API (estado final)
Proxy ◄─201 + observación orquestada── Frontend
```

### Request Body (`ObservacionCreate`)

```json
{
  "descripcion": "Se observa que el presupuesto destinado a materiales no incluye costos de transporte. Por favor revisar y ajustar el presupuesto según lo conversado en la reunión del consejo."
}
```

### Respuesta 201 (`ObservacionResponse`)

```json
{
  "id": "623e4567-e89b-12d3-a456-426614174555",
  "proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
  "council_user_id": "550e8400-e29b-41d4-a716-446655440003",
  "descripcion": "Se observa que el presupuesto destinado a materiales no incluye costos de transporte. Por favor revisar y ajustar el presupuesto según lo conversado en la reunión del consejo.",
  "estado": "pendiente",
  "fecha_limite": "2025-12-20",
  "respuesta": null,
  "fecha_resolucion": null,
  "created_at": "2025-12-15T10:00:00+00:00",
  "updated_at": "2025-12-15T10:00:00+00:00",
  "bonita_case_id": "8065",
  "bonita_process_instance_id": 8065
}
```

### Errores frecuentes

| Código | Origen  | Descripción                                                                                           |
| ------ | ------- | ----------------------------------------------------------------------------------------------------- |
| `401`  | Cloud   | Token inválido o ausente. Proporciona un access_token válido.                                        |
| `403`  | Cloud   | Usuario no es del consejo. Solo usuarios con role=COUNCIL pueden crear observaciones.               |
| `404`  | Cloud   | No existe el proyecto consultado.                                                                      |
| `400`  | Cloud   | El proyecto no está en estado `en_ejecucion`. Las observaciones solo se crean en proyectos activos.  |
| `422`  | Proxy   | Validación fallida (descripción < 10 caracteres, etc.). Revisar el payload.                         |
| `500`  | Bonita  | Falló al instanciar el proceso ObservationsReviewal. La observación fue eliminada (rollback).            |
| `500`  | Proxy   | Bonita instanció pero no se pudo actualizar con metadata. Ver logs para detalles.                    |

---

## 8️⃣ Resolver Observación ejecutando SolveObservation

| Propiedad     | Valor                                                        |
| ------------- | ------------------------------------------------------------ |
| **Método**    | `POST`                                                       |
| **Ruta**      | `/api/v1/observaciones/{observacion_id}/resolve`            |
| **Auth**      | JWT Cloud (`Bearer`)                                         |
| **HTTP 200**  | Tarea humana `SolveObservation` completada + observación actualizada a `resuelta` |

### Precondiciones

- La observación existe en Cloud API y pertenece al proyecto del usuario ejecutor.
- La observación tiene `bonita_case_id` asociado (se creó con el endpoint 7️⃣).
- El usuario autenticado es el ejecutor del proyecto (validado por Cloud API).
- El payload incluye `respuesta` (mínimo 10 caracteres).

### Flujo detallado

1. **Lectura Cloud API** (`GET /api/v1/observaciones/{id}`): obtener `proyecto_id` y `bonita_case_id`.
2. **Resolver en Cloud API** (`POST /api/v1/observaciones/{id}/resolve`): persiste la respuesta y marca estado `resuelta` o `resuelta_vencida`.
3. **Bonita:** buscar tarea pendiente `SolveObservation` con filtro por nombre y *fallback* sin filtro (matching por `name` o `displayName`).
4. **Asignación:** si la tarea no está asignada, se asigna al usuario Bonita autenticado.
5. **Ejecución tarea:** enviar contrato plano `{ "respuesta": "<texto>" }`.
6. **Esperar conectores:** `await asyncio.sleep(2)` para que Bonita propague cambios a Cloud API.
7. **Sync final:** `GET /api/v1/observaciones/{id}` en Cloud API y devolver la entidad actualizada.
8. **Cleanup:** cierre de clientes httpx (`aclose()`).

```
Frontend ──POST /observaciones/{id}/resolve──► Proxy
Proxy ──GET /api/v1/observaciones/{id}──► Cloud API (obtiene bonita_case_id)
Proxy ──POST /api/v1/observaciones/{id}/resolve──► Cloud API (persiste respuesta)
Proxy ──/API/bpm/humanTask (SolveObservation)──► Bonita (fallback sin filtro)
Proxy ──POST /API/bpm/userTask/{taskId}/execution──► Bonita ({"respuesta": ...})
Proxy ◄─GET /api/v1/observaciones/{id}── Cloud API (estado final)
Proxy ◄─200 + observación resuelta── Frontend
```

### Request Body (`ObservacionResolveRequest`)

```json
{
  "respuesta": "Se ajustaron los montos de materiales según la observación del consejo."
}
```

### Respuesta 200 (`ObservacionResponse`)

```json
{
  "id": "623e4567-e89b-12d3-a456-426614174555",
  "proyecto_id": "123e4567-e89b-12d3-a456-426614174000",
  "council_user_id": "550e8400-e29b-41d4-a716-446655440003",
  "descripcion": "Se observa que el presupuesto destinado a materiales no incluye costos de transporte...",
  "estado": "resuelta",
  "fecha_limite": "2025-12-20",
  "respuesta": "Se incorporaron costos de transporte y se actualizó el presupuesto.",
  "fecha_resolucion": "2025-12-17T18:02:11Z",
  "created_at": "2025-12-15T10:00:00Z",
  "updated_at": "2025-12-17T18:02:11Z",
  "bonita_case_id": "8065",
  "bonita_process_instance_id": 8065
}
```

### Errores frecuentes

| Código | Origen  | Descripción                                                                                             |
| ------ | ------- | ------------------------------------------------------------------------------------------------------- |
| `400`  | Proxy   | La observación no tiene `bonita_case_id` o falta `proyecto_id` para contextualizar el proceso.          |
| `401`  | Cloud   | Token inválido o ausente.                                                                               |
| `404`  | Cloud   | Observación inexistente.                                                                                |
| `404`  | Bonita  | No hay tarea pendiente `SolveObservation` para ese `caseId` (ya tomada o no generada).                  |
| `500`  | Bonita  | Falló la ejecución de la tarea (contrato inválido o sesión).                                            |
| `500`  | Proxy   | Bonita ejecutó la tarea pero no se pudo leer la observación actualizada (revisar logs de Cloud API).    |

---

## Códigos de error comunes

| Código | Significado en este contexto                                                                 |
| ------ | -------------------------------------------------------------------------------------------- |
| `401`  | Token inválido o ausente. El frontend debe redirigir a login con la Cloud API.               |
| `422`  | Validaciones Pydantic en el proxy; revisar payloads antes de reintentar.                     |
| `500`  | Error interno en el flujo de orquestación (detalles específicos en `detail` y en los logs).  |
| `502`  | Error propagado del Cloud API (gateway).                                                     |
| `504`  | Timeout al contactarse con la Cloud API o Bonita.                                            |

### Novedades recientes (Cloud API 2025-11)

- `/api/v1/projects`: nuevo filtro `exclude_my_projects` (no combinar con `my_projects`; el proxy devuelve 400 si se usan juntos). Útil para explorar proyectos de otros.
- `/api/v1/projects/{id}` y `/projects/{id}/pedidos`: los pedidos pueden venir con `ya_oferto` (bool) indicando si el usuario autenticado ya hizo una oferta; el proxy lo expone en el schema.
- `/pedidos/{id}/ofertas`: el proxy ahora propaga `409 Conflict` cuando el usuario intenta duplicar una oferta sobre el mismo pedido.
- Ofertas incluyen `fecha_resolucion` (datetime, opcional) en las respuestas; refleja cuándo se aceptó/rechazó.

Para depuración, revisar los logs del proxy: cada paso critica (persistencia, inicio de proceso, ejecución de tarea) registra `logger.info`/`logger.error` con IDs de proyecto/oferta/case para correlacionar eventos en Cloud API y Bonita.

---

¿Necesitás agregar más flujos Bonita? Documenta siempre la secuencia Cloud ↔ Bonita ↔ frontend para mantener a los equipos alineados.
