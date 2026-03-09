# Python Backend (FastAPI + MongoDB)

Este directorio contiene la implementación del proyecto en **Python** usando **FastAPI** y **MongoDB Atlas**.

## Requisitos

- Python 3.10+ (en macOS normalmente es `python3`)
- Acceso a MongoDB (Atlas recomendado)

## Configuración rápida

1) Crear entorno virtual e instalar dependencias:

```bash
cd python_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Variables de entorno:

- Copia `.env_example` a `.env` y llena `MONGO_URI`, o exporta la variable:

```bash
export MONGO_URI="mongodb+srv://<Usuario>:<db_password>@cluster0.bziapgx.mongodb.net/?appName=<nombreCluster>"
```

3) Levantar la API:

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger: `http://localhost:8000/docs`

## Seed (colección con ≥50,000 documentos)

El script de seed crea datos coherentes y, por defecto, genera **50,000 órdenes**:

```bash
python3 scripts/seed.py
```

Puedes ajustar cantidades:

```bash
python3 scripts/seed.py --orders 50000 --restaurants 30 --users 200 --menu-items 300 --reviews 5000
```

## Explain (evidencia de uso de índices)

Genera archivos `.json` con `explain("executionStats")` en:

- `python_backend/docs/explain/`

Ejecuta:

```bash
python3 scripts/explain_report.py
```

### Rechazo de COLLSCAN

- La app intenta activar `notablescan=1` en startup (si el cluster/permiso lo permite).
- Alternativa controlada por env: si `ENFORCE_NO_COLLSCAN=1`, algunas rutas con consultas “por índice” ejecutan `explain` y rechazan cuando detectan `COLLSCAN`.

## CLI (menú de consola para la demo)

El CLI llama al backend para demostrar CRUD, consultas, agregaciones, transacciones y GridFS.

1) (Opcional) define el URL del API:

```bash
export API_BASE_URL="http://localhost:8000"
```

2) Ejecuta el CLI:

```bash
python3 cli/main.py
```

## Rutas clave para la rúbrica (base)

- **CRUD**: `/restaurants`, `/users`, `/menu-items`, `/orders`, `/reviews`
- **Update many / delete many**: `/.../bulk/update-many`, `/.../bulk/delete-many`
- **Arrays**:
  - `menuItems.tags`: `/menu-items/{id}/tags:add`, `/menu-items/{id}/tags:remove`
  - `orders.items`: `/orders/{id}/items:push`, `/orders/{id}/items:pull`
- **Transacción multi-documento**: `/orders/with-review`
- **Lookup + filtros + proyección + sort + skip/limit**: `/orders/enriched/query`
- **Agregaciones**:
  - `/analytics/top-restaurants`
  - `/analytics/top-menu-items`
  - `/analytics/revenue-by-restaurant`
  - `/analytics/counts`
- **GridFS**: `/files/upload`, `/files/{gridfs_id}`

