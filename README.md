# Tablero de solicitudes

Aplicación full stack para crear, editar y mover solicitudes por un flujo de
estados, con un resumen del tablero generado por un LLM bajo demanda.

**Stack:** FastAPI · SQLAlchemy 2 · MySQL 8 · React 18 + TypeScript + Vite ·
Docker Compose · pytest.

---

## Funcionalidades

- Crear solicitudes; toda solicitud nueva entra en `created`.
- Listar con filtro por estado y paginación.
- Editar únicamente título y descripción (el estado no es editable por PATCH).
- Consultar y ejecutar transiciones respetando la máquina de estados.
- Interfaz responsive: crear, listar, editar inline, botones de transición y
  panel de resumen.
- Resumen generado por un LLM bajo demanda, con cache y degradación controlada:
  si el proveedor falla, el listado sigue funcionando y la UI muestra un mensaje.
- Swagger/OpenAPI automático en `/docs`.
- 68 tests de backend (dominio, servicios y endpoints).

---

## Inicio rápido con Docker

Requisitos: Docker y Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Servicios:

| Servicio | URL |
|---|---|
| Frontend | http://localhost:8080 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| MySQL (host) | `localhost:3307` |

El esquema y los datos de prueba se cargan automáticamente la primera vez que se
inicializa el volumen de MySQL.

Para ver el resumen sin configurar una API key, levanta el backend con el
proveedor de demostración:

```bash
LLM_PROVIDER=fake docker compose up --build
```

Para detener el stack:

```bash
docker compose down
```

Para borrar también la base de datos y volver a cargar el seed:

```bash
docker compose down -v
docker compose up --build
```

> Sin `.env`, el compose funciona igual gracias a los valores por defecto. El
> archivo sirve para personalizar credenciales, proveedor LLM y orígenes CORS.

---

## Inicio local (sin Docker para la aplicación)

### 1. Base de datos

```bash
docker compose up -d db
```

MySQL queda expuesto en `localhost:3307` y carga `db/schema.sql`
automáticamente.

### 2. Backend

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt

cd backend
DATABASE_URL="mysql+pymysql://app:apppass@127.0.0.1:3307/solicitudes?charset=utf8mb4" \
LLM_PROVIDER=fake \
../.venv/bin/uvicorn app.main:app --reload
```

La API queda en http://localhost:8000.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

La UI queda en http://localhost:5173. El cliente usa
`http://localhost:8000/api/v1` por defecto; se puede cambiar con
`VITE_API_URL` en `frontend/.env`.

### 4. Tests

```bash
cd backend
../.venv/bin/python -m pytest
```

---

## Variables de entorno

Todas tienen valores por defecto razonables para desarrollo.

| Variable | Default | Descripción |
|---|---|---|
| `MYSQL_ROOT_PASSWORD` | `rootpass` | Password de root de MySQL |
| `MYSQL_DATABASE` | `solicitudes` | Nombre de la base |
| `MYSQL_USER` | `app` | Usuario de la aplicación |
| `MYSQL_PASSWORD` | `apppass` | Password del usuario |
| `MYSQL_PORT` | `3307` | Puerto de MySQL en el host |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:8080` | Orígenes permitidos, separados por coma |
| `LOG_LEVEL` | `INFO` | Nivel de logs del backend |
| `LLM_PROVIDER` | `openai` | `openai` o `fake` |
| `LLM_API_KEY` | vacío | API key del proveedor; nunca se versiona |
| `LLM_MODEL` | `gpt-4o-mini` | Modelo a usar |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | API compatible con OpenAI |
| `LLM_TIMEOUT_SECONDS` | `8` | Presupuesto total de la llamada |
| `LLM_MAX_RETRIES` | `1` | Reintentos máximos (solo errores transitorios) |
| `LLM_CACHE_TTL_SECONDS` | `300` | TTL del cache en memoria |
| `VITE_API_URL` | `http://localhost:8000/api/v1` | URL de la API usada en el build del frontend |

`DATABASE_URL` solo es necesaria para ejecutar el backend fuera de Docker; el
compose la construye apuntando al servicio `db`.

---

## Flujo de estados

```mermaid
stateDiagram-v2
    [*] --> created
    created --> in_review
    in_review --> in_progress
    in_review --> paused
    in_progress --> done
    in_progress --> paused
    paused --> in_review
    paused --> in_progress
    done --> [*]
```

Reglas implementadas:

- `created → in_progress` se rechaza.
- `paused` solo se alcanza desde `in_review` o `in_progress`.
- `paused → done` se rechaza: primero hay que reanudar.
- Desde `paused` solo se puede volver a `in_review` o `in_progress`.
- `done` es final.

Las reglas viven en `backend/app/domain/transitions.py`, sin dependencias de
FastAPI ni de la base de datos.

---

## Documentación de la API

Prefijo: `/api/v1`. Los estados siempre se identifican por su `code`, nunca por
el id interno de la base de datos.

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Healthcheck |
| `GET` | `/statuses` | Catálogo de estados (`code`, `label`, `is_final`) |
| `POST` | `/requests` | Crea una solicitud en `created` |
| `GET` | `/requests` | Lista con `status`, `page` y `page_size` |
| `GET` | `/requests/{id}` | Detalle |
| `PATCH` | `/requests/{id}` | Edita título y/o descripción |
| `GET` | `/requests/{id}/transitions` | Estado actual y transiciones permitidas |
| `POST` | `/requests/{id}/transitions` | Ejecuta una transición |
| `GET` | `/requests/summary` | Resumen generado por el LLM |

Cada solicitud incluye `allowed_transitions`, calculado por el backend, para que
la interfaz solo ofrezca acciones válidas sin hacer una petición por tarjeta.

### Crear

```bash
curl -s -X POST http://localhost:8000/api/v1/requests \
  -H 'Content-Type: application/json' \
  -d '{"title":"Revisar contrato","description":"Pendiente de firma"}'
```

```json
{
  "id": 13,
  "title": "Revisar contrato",
  "description": "Pendiente de firma",
  "status": {
    "code": "created",
    "label": "Creada",
    "is_final": false
  },
  "allowed_transitions": ["in_review"],
  "created_at": "2026-11-10T02:38:28Z",
  "updated_at": "2026-11-10T02:38:28Z"
}
```

### Listar y filtrar

```bash
curl -s 'http://localhost:8000/api/v1/requests?status=created&page=1&page_size=5'
```

Respuesta: `{ "items": [...], "total": 3, "page": 1, "page_size": 5 }`.

### Editar

```bash
curl -s -X PATCH http://localhost:8000/api/v1/requests/1 \
  -H 'Content-Type: application/json' \
  -d '{"title":"Título actualizado","description":null}'
```

`PATCH` usa un schema estricto: enviar `status` u otro campo devuelve `422`.
La descripción se puede borrar enviando `null`.

### Consultar transiciones

```bash
curl -s http://localhost:8000/api/v1/requests/1/transitions
```

```json
{
  "current": { "code": "created", "label": "Creada", "is_final": false },
  "allowed": [{ "code": "in_review", "label": "En revisión", "is_final": false }]
}
```

### Ejecutar una transición

```bash
curl -s -X POST http://localhost:8000/api/v1/requests/1/transitions \
  -H 'Content-Type: application/json' \
  -d '{"to":"in_review"}'
```

Transición inválida (`409 Conflict`):

```bash
curl -s -X POST http://localhost:8000/api/v1/requests/1/transitions \
  -H 'Content-Type: application/json' \
  -d '{"to":"in_progress"}'
```

```json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "No se puede pasar de 'created' a 'in_progress'.",
    "details": {
      "from": "created",
      "to": "in_progress",
      "allowed": ["in_review"]
    }
  }
}
```

### Resumen con LLM

```bash
curl -s http://localhost:8000/api/v1/requests/summary
```

Con proveedor disponible:

```json
{
  "status": "ok",
  "summary": "Hay 12 solicitudes...",
  "generated_at": "2026-11-10T02:40:00Z",
  "cached": false,
  "message": null
}
```

Si el LLM falla o expira, la API responde `200` para no romper la UI:

```json
{
  "status": "unavailable",
  "summary": null,
  "generated_at": null,
  "cached": false,
  "message": "No pudimos generar el resumen en este momento. Intenta de nuevo en unos minutos."
}
```

### Formato de error

Todos los errores de dominio y validación comparten la misma forma:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Datos de entrada inválidos.",
    "details": {
      "fields": [
        { "field": "title", "message": "String should have at least 3 characters", "type": "string_too_short" }
      ]
    }
  }
}
```

Códigos HTTP: `201` al crear, `200` en lecturas y ediciones, `404` si no existe,
`409` para una transición inválida y `422` para validación de entrada.

---

## Integración con LLM

### Qué se envía

Solo datos agregados y títulos cortos:

- Total de solicitudes.
- Conteo por estado (incluidos estados con cero).
- Solicitudes pausadas: título truncado a 80 caracteres y días sin cambios.
- Hasta 5 solicitudes abiertas más antiguas: título truncado, estado y días sin
  cambios.

**No se envían** descripciones, ids, fechas exactas, datos personales ni el
listado completo. El resumen necesita panorama y cuellos de botella, no el texto
completo. Menos tokens, menos latencia y menos exposición de datos.

### Cuándo se genera

- Bajo demanda desde el botón del panel de resumen.
- Endpoint independiente `GET /requests/summary`; el listado nunca depende de él.
- Cache en memoria con TTL de 5 minutos, keyed por un hash del payload. Si los
  datos no cambiaron, no se vuelve a llamar al modelo.
- Timeout total configurable (8 s por defecto) más un reintento para errores
  transitorios. El servicio añade `asyncio.wait_for` como red de seguridad.
- Cualquier fallo se traduce a `status: "unavailable"` con un mensaje claro.

### Proveedores

La implementación usa la API de chat completions compatible con OpenAI. Se puede
cambiar de proveedor con `LLM_BASE_URL` y `LLM_MODEL`, o usar `LLM_PROVIDER=fake`
para una demo sin red ni tokens. El cliente está detrás de un `Protocol`
(`LLMClient`), por lo que añadir otro proveedor no toca servicios ni routers.

La API key se pasa solo por variable de entorno.

---

## Arquitectura

```mermaid
flowchart LR
    UI[React + TS] -->|JSON / HTTP| API[Routers FastAPI]
    API --> SVC[Services]
    SVC --> DOM[Dominio: máquina de estados]
    SVC --> REPO[Repositories]
    REPO --> DB[(MySQL)]
    SVC --> LLM[LLMClient]
```

Capas del backend:

- **API / routers:** validación HTTP con Pydantic, códigos de estado y
  serialización. No contienen reglas de negocio.
- **Services:** casos de uso (crear, editar, transicionar, resumir) y
  transacciones.
- **Domain:** estados, transiciones y errores de negocio. Código puro, testeable
  sin base de datos ni HTTP.
- **Repositories:** todo el acceso a SQLAlchemy.
- **Integrations:** cliente LLM detrás de una interfaz, con implementación real
  y fake.

### Decisiones y justificación

**FastAPI.** Tipado con Pydantic, validación automática y OpenAPI/Swagger sin
trabajo extra. Es async, lo que encaja con la llamada externa al LLM.

**Estados por `code`, no por id.** `statuses.code` es único y estable
(`created`, `in_review`, ...). El id autoincremental es un detalle de la base de
datos que puede cambiar entre entornos o al recargar datos. La API expone y
recibe códigos; el id solo se usa internamente para la FK y la integridad
referencial.

**Transiciones en código, no en tabla.** Son cinco estados con reglas estables.
Un mapa inmutable en el dominio es más simple, versionable y testeable que una
tabla de transiciones. Si las reglas tuvieran que cambiar por rol o sin
desplegar, se migrarían a `status_transitions(from_status_id, to_status_id)`.

**Validar antes de escribir.** El servicio llama a `ensure_transition` antes de
cualquier `UPDATE`. Si la transición es inválida, hace rollback y responde
`409`; la base de datos no se modifica.

**Concurrencia.** La transición lee la fila con `SELECT ... FOR UPDATE` dentro de
la transacción, para que dos cambios simultáneos no se pisen. El rollback explícito
libera el lock cuando la transición es inválida.

**409 para transición inválida.** El estado actual del recurso impide la acción:
es un conflicto, no un error de formato. `422` se reserva para cuerpos o
parámetros inválidos.

**La UI no inventa transiciones.** Cada solicitud incluye
`allowed_transitions`, calculado por el dominio en el backend. La interfaz pinta
solo esos botones y, aun así, el `POST` vuelve a validar. Si hay una carrera, se
muestra el `409` en la tarjeta.

**LLM bajo demanda y aislado.** Generar en cada carga gastaría tokens y añadiría
latencia. El endpoint es independiente, tiene cache y degrada a un mensaje claro.
La app sigue siendo usable sin API key (`LLM_PROVIDER=fake` o `unavailable`).

**Frontend sin estado global.** Para esta escala, hooks propios (`useRequests`,
`useSummary`) y estado local bastan. No se justifica Redux. El CSS es puro, con
Grid/Flexbox y media queries.

**`schema.sql` como fuente de verdad.** La entrega pide un archivo SQL. Para un
proyecto de este tamaño, Alembic duplicaría la fuente de verdad. Si el esquema
evolucionara en equipo, se añadiría Alembic con una migración inicial basada en
este schema.

**Tests de integración con SQLite.** Son rápidos y aislados, y permiten ejecutar
la suite sin Docker. El esquema y las consultas se validaron además contra MySQL
8.4 real (incluido el flujo completo, UTF-8 y `FOR UPDATE`). Para CI estricto se
puede parametrizar el fixture con una instancia MySQL de test.

---

## Estructura del proyecto

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   ├── errors.py
│   │   │   └── v1/
│   │   │       ├── requests.py
│   │   │       ├── router.py
│   │   │       └── statuses.py
│   │   ├── core/config.py
│   │   ├── db/
│   │   ├── domain/
│   │   │   ├── errors.py
│   │   │   ├── status.py
│   │   │   └── transitions.py
│   │   ├── integrations/llm/
│   │   │   ├── base.py
│   │   │   ├── factory.py
│   │   │   ├── fake_client.py
│   │   │   └── openai_client.py
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── request_service.py
│   │   │   └── summary_service.py
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-dev.txt
├── db/
│   └── schema.sql
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Base de datos

### `statuses`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `TINYINT UNSIGNED` | PK interna |
| `code` | `VARCHAR(30)` | Único; identificador público |
| `label` | `VARCHAR(60)` | Texto para la UI |
| `sort_order` | `TINYINT UNSIGNED` | Orden del catálogo |
| `is_final` | `BOOLEAN` | `done` es final |

### `requests`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `BIGINT UNSIGNED` | PK |
| `title` | `VARCHAR(150)` | Obligatorio |
| `description` | `TEXT` | Nullable |
| `status_id` | `TINYINT UNSIGNED` | FK a `statuses.id` |
| `created_at` | `DATETIME` | Default `CURRENT_TIMESTAMP` |
| `updated_at` | `DATETIME` | `ON UPDATE CURRENT_TIMESTAMP` |

Decisiones:

- InnoDB, `utf8mb4` y `utf8mb4_unicode_ci` para acentos y emojis.
- FK con `ON DELETE RESTRICT`: nunca queda una solicitud con un estado inválido.
- Índices en `status_id` y `created_at` para filtros y orden.
- `SET NAMES utf8mb4` al inicio del script: evita que el cliente MySQL interprete
  el archivo como latin1 y corrompa los acentos al inicializar el contenedor.
- Seed idempotente: 5 estados y 12 solicitudes repartidas en todos los estados,
  incluidas dos pausadas. Se inserta solo si `requests` está vacía.

Para recrear la base desde cero:

```bash
docker compose down -v
docker compose up --build
```

---

## Pruebas

```bash
cd backend
../.venv/bin/python -m pytest
```

Resultado actual: **68 passed**.

Cobertura funcional:

- **Dominio:** las 25 combinaciones origen × destino, reglas de `paused`,
  `done` final, inmutabilidad del mapa y mensajes de error.
- **Integración CRUD:** creación, trim, validaciones, filtro, paginación, 404,
  PATCH de campos, rechazo de `status` y body vacío.
- **Transiciones:** camino feliz, salto inválido sin tocar la BD, pausa y
  reanudación, `paused → done` rechazado, `done` final, mismo estado, destino
  desconocido y solicitud inexistente.
- **LLM:** respuesta correcta, cache, invalidación al cambiar datos, fallo del
  proveedor sin romper el listado, respuesta vacía, timeout, ausencia de
  descripciones e ids en el prompt y truncado de títulos.

Los tests de integración usan SQLite en memoria por velocidad. El stack completo
se verificó con MySQL 8.4 y `docker compose up --build`.

---

## Uso de IA

- **Desarrollo:** usé OpenCode como agente de codificación (modelo DeepSeek
  V4.1 Flash Free) para generar el scaffolding, proponer la arquitectura por
  capas, redactar tests y este README. Cada cambio se revisó y validó con
  `pytest` (68 tests), `tsc --noEmit`, `vite build` y pruebas manuales contra
  MySQL 8.4 y el stack Docker.
- **Producto:** la aplicación integra un LLM opcional compatible con la API de
  OpenAI para generar el resumen. Sin API key o con el proveedor caído, el
  resumen se degrada a un mensaje y el resto del tablero sigue operativo.
- **Privacidad:** al modelo solo se envían agregados y títulos truncados; nunca
  descripciones, ids internos ni fechas exactas.

---

## Checklist de la prueba

| Requisito | Implementación |
|---|---|
| Secuencia `created → in_review → in_progress → done` | Dominio + tests de las 25 combinaciones |
| Rechazo de transiciones inválidas sin tocar la BD | `ensure_transition` antes del `UPDATE`, rollback y `409` |
| Estados sin ids internos | `code` único expuesto por la API |
| `paused` desde `in_review`/`in_progress` | Tabla de transiciones y tests |
| `paused → done` rechazado | Test explícito |
| Esquema y datos de prueba | `db/schema.sql` |
| API de crear, listar, editar y transicionar | `/api/v1/requests` |
| Integración LLM con resumen | `/api/v1/requests/summary` + panel |
| Fallo del LLM no rompe el listado | Endpoint separado, `200 unavailable`, test |
| Minimización de datos | Solo agregados y títulos truncados; test del prompt |
| Frontend responsive | React + CSS Grid/Flexbox |
| Transiciones solo válidas en la UI | `allowed_transitions` del backend + revalidación |
| README con instalación, API, decisiones, estructura y IA | Este documento |

---

## Mejoras futuras

- Historial de transiciones (`request_status_history`) para auditoría y mejores
  resúmenes.
- Autenticación y autorización por rol.
- Tests de integración contra MySQL en CI (servicio de base de datos).
- Tests de componentes/E2E para el frontend.
- Cache distribuido (Redis) si se ejecutan varios workers.
- Paginación por cursor y búsqueda por texto.
- Métricas y trazas del proveedor LLM.
- Alembic si el esquema empieza a evolucionar en equipo.

---

## Solución de problemas

- **El puerto 3307 está ocupado:** cambia `MYSQL_PORT` en `.env`.
- **Cambié el schema y no se aplica:** el script solo corre al inicializar el
  volumen. Usa `docker compose down -v` y vuelve a levantar.
- **El resumen dice `unavailable`:** configura `LLM_API_KEY` con
  `LLM_PROVIDER=openai`, o usa `LLM_PROVIDER=fake` para la demo.
- **Error de CORS:** agrega el origen exacto a `CORS_ORIGINS` y reinicia el
  backend.
- **Cambié la URL de la API:** `VITE_API_URL` se hornea en el build del
  frontend; hay que reconstruir la imagen (`docker compose up --build`).
- **La API no conecta a MySQL:** el backend espera el healthcheck de `db`.
  Revisa `docker compose ps` y los logs con `docker compose logs -f backend`.
