# Script / Guion para Evaluación — Rúbrica Proyecto MongoDB

Este documento sirve como **guion para presentación o video** y como **checklist** para responder cada criterio de la rúbrica. Incluye qué mostrar y dónde está implementado en el proyecto.

---

## ETAPA 01

### 1. Documentación del diseño del proyecto (10 pts)

**Qué decir:**  
“La documentación del diseño del proyecto incluye:”

- **README principal** (`README.md`): descripción del proyecto, cómo ejecutar backend y frontend, seed y Docker.
- **README del backend** (`python_backend/README.md`): configuración, variables de entorno, rutas clave para la rúbrica, seed (≥50k docs), explain e índices.
- **Guion de video** (`python_backend/docs/video_script.md`): flujo sugerido para demostrar todas las funcionalidades en menos de 10 minutos.

**Dónde está:**  
`README.md`, `python_backend/README.md`, `python_backend/docs/video_script.md`

**Qué mostrar:**  
Abrir los README y el `video_script.md` y señalar las secciones de diseño, arquitectura (FastAPI + MongoDB) y uso.

---

### 2. Modelado de datos — campos y tipos (5 pts)

**Qué decir:**  
“El modelo de datos está definido en Pydantic y refleja el caso de uso de un sistema de restaurantes:”

- **Restaurantes:** `name`, `description`, `category`, `location` (GeoJSON Point), `ratingAverage`, `createdAt`.
- **MenuItems (referenciados):** `restaurantId`, `name`, `price`, `category`, `tags` (array).
- **Users:** `name`, `email`, `password`, `role` (customer/admin), `createdAt`.
- **Orders:** `userId`, `restaurantId` (referencias), `items` (array de documentos embebidos: `menuItemId`, `name`, `quantity`, `price`), `status`, `totalAmount`, `createdAt`.
- **Reviews:** `restaurantId`, `userId`, `orderId` (opcional), `rating`, `comment`, `createdAt`.

El modelo hace sentido al caso de uso: órdenes con ítems embebidos, referencias a restaurante y usuario, y reseñas vinculadas a orden/restaurante.

**Dónde está:**  
`python_backend/app/models.py`

**Qué mostrar:**  
Abrir `models.py` y recorrer `Location`, `RestaurantBase`, `OrderItem`, `OrderBase`, `ReviewBase`, etc.

---

### 3. Índices — 4 tipos diversos (5 pts)

**Qué decir:**  
“Se implementaron y validaron al menos 4 tipos de índices en distintas colecciones:”

1. **Índice simple (único):** `users.email` — único, para búsqueda por email.
2. **Índice compuesto:** `orders`: `(restaurantId, createdAt)` — para listar órdenes por restaurante ordenadas por fecha.
3. **Índice multikey:** `menuItems.tags` — para consultas por tag.
4. **Índice geoespacial:** `restaurants.location` — `2dsphere` para búsquedas por proximidad.
5. **Índice de texto:** `restaurants`: `(name, description)` — text search.

La validación se hace con `explain("executionStats")`; los reportes están en `python_backend/docs/explain/*.json` y muestran `IXSCAN` (no COLLSCAN).

**Dónde está:**  
- Creación: `python_backend/app/database.py` → `create_indexes()`  
- Validación: `python_backend/scripts/explain_report.py` y archivos en `python_backend/docs/explain/`

**Qué mostrar:**  
- Código en `database.py` (líneas de `create_index`).  
- Ejecutar `python3 scripts/explain_report.py` y abrir uno o dos JSON en `docs/explain/` mostrando `winningPlan.inputStage.stage: "IXSCAN"`.

---

## CRUD

### 4. Creación — documento embebido (parte de 10 pts)

**Qué decir:**  
“Los documentos embebidos se crean dentro de las órdenes: cada orden tiene un array `items` donde cada elemento es un documento embebido con `menuItemId`, `name`, `quantity`, `price`. No son colecciones separadas; viven dentro del documento de la orden.”

**Dónde está:**  
- Modelo: `OrderItem` en `models.py`; en `orders` el campo `items` es `List[OrderItem]`.  
- Creación: `python_backend/app/routers/orders.py` — `create_order` y `create_orders_bulk` construyen `items` como array de objetos dentro del documento.

**Qué mostrar:**  
En Swagger: POST `/orders` con un body que incluya `items: [{ "menuItemId": "...", "name": "...", "quantity": 1, "price": 10.5 }]`. Mostrar en MongoDB Compass o en la respuesta que `items` es un array de subdocumentos.

---

### 5. Creación — documentos referenciados (parte de 10 pts)

**Qué decir:**  
“Los documentos referenciados son entidades en sus propias colecciones, vinculadas por ID:”

- **Restaurantes:** colección `restaurants`; se referencian por `_id` en `menuItems.restaurantId`, `orders.restaurantId`, `reviews.restaurantId`.
- **Usuarios:** colección `users`; referenciados en `orders.userId`, `reviews.userId`.
- **Menu items:** colección `menuItems`; referenciados en `orders.items[].menuItemId`.

Creación: POST a `/restaurants`, `/users`, `/menu-items`, `/reviews` crean un documento cada uno; POST a `/orders/bulk` o `/restaurants/bulk`, etc., crean varios.

**Dónde está:**  
- Un documento: `routers/restaurants.py` (POST `""`), `routers/users.py`, `routers/menu_items.py`, `routers/orders.py`, `routers/reviews.py`.  
- Varios: `routers/*.py` — endpoints `POST .../bulk` con `insert_many`.

**Qué mostrar:**  
En Swagger: crear 1 restaurante, 1 usuario, 1 menu item, 1 orden. Luego (opcional) POST `/orders/bulk` o `/restaurants/bulk` con un array para mostrar “uno o varios documentos”.

---

### 6. Lectura y consulta — multi-colección (lookups), filtros, proyección, ordenamiento, skip, límite (15 pts)

**Qué decir:**  
“La lectura avanzada se hace en el endpoint de órdenes enriquecidas:”

- **Lookups (multi-colección):** `$lookup` de `orders` con `users` y con `restaurants` para traer datos de usuario y restaurante en la misma respuesta.
- **Filtros:** por `restaurantId`, `status`, `minTotal` (totalAmount >= valor).
- **Ordenamiento:** parámetro `sort` (ej. `-createdAt`).
- **Skip y límite:** parámetros `skip` y `limit` para paginación.
- **Proyección:** parámetro `lite=true` devuelve menos campos (solo status, totalAmount, createdAt y un slice de user/restaurant).

**Dónde está:**  
`python_backend/app/routers/orders.py` → `GET /orders/enriched/query`

**Qué mostrar:**  
En Swagger: GET `/orders/enriched/query` con `restaurantId`, `status`, `minTotal`, `skip`, `limit`, `sort`, `lite`. Mostrar la respuesta con datos de orden + usuario + restaurante.

---

### 7. Actualización — 1 documento y varios documentos (10 pts)

**Qué decir:**  
“Actualización de un documento: PATCH por ID en cada recurso (por ejemplo PATCH `/orders/{order_id}` con un body `{ "status": "completed" }`). Actualización de varios: endpoints bulk con filtro y operador de actualización.”

**Dónde está:**  
- Un documento:  
  - `PATCH /restaurants/{id}`, `PATCH /users/{id}`, `PATCH /menu-items/{id}`, `PATCH /orders/{id}`, `PATCH /reviews/{id}` (todos con `update_one`).  
- Varios:  
  - `PATCH /restaurants/bulk/update-many`, `/users/bulk/update-many`, `/menu-items/bulk/update-many`, `/orders/bulk/update-many`, `/reviews/bulk/update-many` (body: `{ "filter": {...}, "update": {...} }`).

**Qué mostrar:**  
En Swagger: PATCH `/orders/{order_id}` con `{"status": "completed"}`. Luego PATCH `/orders/bulk/update-many` con `{"filter": {"status": "pending"}, "update": {"$set": {"status": "cancelled"}}}` y mostrar `matched` y `modified`.

---

### 8. Eliminación — 1 documento y varios documentos (10 pts)

**Qué decir:**  
“Eliminación de un documento: DELETE por ID. Eliminación de varios: endpoint bulk con filtro.”

**Dónde está:**  
- Un documento: `DELETE /restaurants/{id}`, `DELETE /users/{id}`, `DELETE /menu-items/{id}`, `DELETE /orders/{id}`, `DELETE /reviews/{id}` (`delete_one`).  
- Varios: `POST /restaurants/bulk/delete-many`, `/users/bulk/delete-many`, `/menu-items/bulk/delete-many`, `/orders/bulk/delete-many`, `/reviews/bulk/delete-many` (body: `{ "filter": {...} }`).

**Qué mostrar:**  
DELETE una orden por ID; luego POST `/orders/bulk/delete-many` con un filtro (ej. `{"status": "cancelled"}`) y mostrar `deleted`.

---

## GridFS y archivos (5 pts)

**Qué decir:**  
“GridFS se usa para archivos que pueden superar el límite de 16MB. La aplicación permite subir archivos, listar metadatos en la colección `files` y descargar por `gridfsId`. Los cambios se reflejan en MongoDB (colecciones `fs.files`, `fs.chunks` y nuestra colección `files`). Además, existe al menos una colección con al menos 50.000 documentos: la colección `orders` se puebla con el script de seed con 50.000 órdenes por defecto.”

**Dónde está:**  
- GridFS: `python_backend/app/routers/files.py` — POST `/files/upload`, GET `/files`, GET `/files/{gridfs_id}` (download).  
- ≥50k documentos: `python_backend/scripts/seed.py` — `--orders 50000` por defecto.

**Qué mostrar:**  
1) Ejecutar `python3 scripts/seed.py` y mostrar el conteo de `orders` (50.000).  
2) Subir un archivo por Swagger (POST `/files/upload`) o por el frontend en “Archivos”.  
3) Listar archivos (GET `/files`) y descargar uno (GET `/files/{gridfs_id}`). Opcional: mostrar en Compass las colecciones `fs.files` y `fs.chunks`.

---

## Agregaciones y otros

### 9. Agregaciones simples — count, distinct (5 pts)

**Qué decir:**  
“Agregaciones simples: `count_documents` para conteos y `distinct` para valores únicos.”

**Dónde está:**  
`python_backend/app/routers/analytics.py`:  
- `GET /analytics/counts`: cuenta documentos en restaurants, users, menuItems, orders, reviews.  
- `GET /analytics/simple/counts-by-status`: cuenta órdenes por `status`.  
- `GET /analytics/simple/distinct-categories`: `distinct("category")` en restaurantes.  
- `GET /analytics/simple/distinct-menu-categories`: `distinct` en categorías y tags de menu items.

**Qué mostrar:**  
Llamar a `/analytics/counts` y a `/analytics/simple/distinct-categories` (o counts-by-status) y mostrar la respuesta.

---

### 10. Agregaciones complejas — pipelines (10 pts)

**Qué decir:**  
“Pipelines de agregación complejos con `$group`, `$lookup`, `$sort`, `$limit`, y en algunos casos `$bucket` o `$facet`.”

**Dónde está:**  
`python_backend/app/routers/analytics.py`:  
- `GET /analytics/top-restaurants`: group por restaurantId en reviews, avg rating, lookup a restaurants.  
- `GET /analytics/top-menu-items`: unwind de orders.items, group por nombre, total vendido.  
- `GET /analytics/revenue-by-restaurant`: group por restaurantId en orders, totalRevenue, lookup a restaurants.  
- `GET /analytics/complex/user-spending-brackets`: lookup orders en users, total gastado, `$bucket` por rangos.  
- `GET /analytics/complex/restaurant-performance-analytics`: `$facet` con varios sub-pipelines (por rating, por órdenes, por categoría).  
- `GET /analytics/complex/order-items-analysis`: unwind items, group por item y restaurante, lookup restaurants.

**Qué mostrar:**  
Llamar a dos o tres de estos (por ejemplo top-restaurants, revenue-by-restaurant, user-spending-brackets) y comentar las etapas del pipeline.

---

### 11. Manejo de arrays — $push, $pull, $addToSet (10 pts)

**Qué decir:**  
“Manejo de arrays con operadores de actualización:”

- **Menu items – tags:** `$addToSet` para agregar un tag sin duplicados; `$pull` para quitar (endpoints en menu_items y en analytics).
- **Orders – items:** `$push` para agregar un ítem a la orden; `$pull` para quitar ítems que cumplan una condición.

**Dónde está:**  
- Tags: `routers/menu_items.py` — POST `/{id}/tags:add` (`$addToSet`), POST `/{id}/tags:remove` (`$pull`).  
- Orders items: `routers/orders.py` — POST `/{id}/items:push` (`$push`), POST `/{id}/items:pull` (`$pull`).  
- Analytics (alternativos): `routers/analytics.py` — `/analytics/arrays/add-tag-to-menu-item`, `push-to-order-items`, `pull-from-order-items`.

**Qué mostrar:**  
Añadir un tag a un menu item (tags:add) y mostrar el array `tags` antes/después. Añadir un ítem a una orden (items:push) y opcionalmente hacer un pull (items:pull).

---

### 12. Manejo de documentos embebidos (5 pts)

**Qué decir:**  
“Los documentos embebidos se usan en órdenes (`items`) y se consultan o transforman en pipelines: por ejemplo `$addFields` con `$map` sobre `items` para calcular subtotales, o `$unwind` de `items` para agregaciones. También hay un endpoint que devuelve restaurantes con su menú (lookup a menuItems) como documento anidado.”

**Dónde está:**  
`python_backend/app/routers/analytics.py`:  
- `GET /analytics/embedded/orders-with-enriched-items`: usa `$addFields` y `$map` sobre `items` para calcular subtotal por ítem.  
- `GET /analytics/embedded/restaurant-menu-aggregated`: lookup de menuItems y agregación (menuCount, avgPrice, categorías) con menú embebido en la respuesta.

**Qué mostrar:**  
Llamar a `/analytics/embedded/orders-with-enriched-items` o `/analytics/embedded/restaurant-menu-aggregated` y señalar el uso de `items` embebidos o el menú embebido.

---

## Extras (opcionales)

### Operaciones BULK (bulkWrite) — hasta 5 pts extra

**Qué decir (si se implementa):**  
“Se implementó `bulk_write` para ejecutar varias operaciones (insert, update, delete) en un solo round-trip a la base de datos.”

**Nota:** En el código actual no hay uso de `bulk_write`; los “bulk” son `insert_many`, `update_many`, `delete_many`. Para optar a este extra habría que añadir un endpoint que use `collection.bulk_write([InsertOne(...), UpdateOne(...), ...])` y mostrarlo en la demo.

---

### Mongo Charts — hasta 5 pts (no compatible con BI Connectors)

**Qué decir (si se hace):**  
“Se crearon dashboards en MongoDB Charts conectados a este cluster, con gráficas que tienen sentido de negocio (por ejemplo: ingresos por restaurante, órdenes por estado, valoración media por categoría).”  
Cada gráfica embebida con sentido de negocio puede sumar hasta 2 pts, máximo 5 pts.

---

### BI Connectors — hasta 5 pts (no compatible con Mongo Charts)

**Qué decir (si se hace):**  
“Se configuró el conector de BI (por ejemplo Power BI o Tableau) a MongoDB Atlas y se construyeron reportes o dashboards usando los datos del proyecto.”

---

### Frontend / HCI — hasta 10 pts

**Qué decir:**  
“El frontend es una aplicación Streamlit que consume el API REST. Permite gestionar restaurantes, menu items, órdenes y reviews; crear datos en bulk; ejecutar consultas avanzadas (órdenes enriquecidas); actualizaciones y eliminaciones; subir y descargar archivos (GridFS); manejo de arrays (tags, items en órdenes) y ver documentos embebidos y analytics. La interfaz está en español y organizada por secciones en el sidebar.”

**Dónde está:**  
`frontend/app.py` — Streamlit, secciones: Restaurantes, Menu Items, Órdenes, Reviews, Analytics, Crear Bulk, Consultas Avanzadas, Updates, Deletes, Archivos, Manejo de Arrays, Documentos Embebidos.

**Qué mostrar:**  
Abrir el frontend (`streamlit run app.py` en `frontend/`), recorrer las pestañas y mostrar al menos: crear un restaurante, listar órdenes enriquecidas, analytics, subir archivo, añadir tag a un item.

---

## Orden sugerido para video o presentación (≈10 min)

1. **Intro (1 min):** README y documentación del diseño; modelo de datos en `models.py`.  
2. **Índices (1 min):** `database.py` + ejecutar `explain_report.py` y mostrar un JSON con IXSCAN.  
3. **CRUD (2 min):** Crear 1 restaurante, 1 usuario, 1 menu item; crear 1 orden (con items embebidos) y opcionalmente orden + review (transacción). Mencionar bulk (varios documentos).  
4. **Lectura avanzada (1 min):** GET `/orders/enriched/query` con filtros, sort, skip, limit, lite.  
5. **Updates y deletes (1 min):** PATCH uno, PATCH bulk; DELETE uno, POST bulk delete-many.  
6. **GridFS + 50k docs (1 min):** Mostrar conteo de orders tras seed; subir y descargar un archivo.  
7. **Agregaciones (1.5 min):** Counts/distinct; un pipeline complejo (top-restaurants o user-spending-brackets).  
8. **Arrays y embebidos (1 min):** tags:add / items:push; endpoint embedded (orders-with-enriched-items o restaurant-menu-aggregated).  
9. **Frontend (1 min):** Navegar por el dashboard y mostrar 2–3 acciones.  
10. **Cierre (0.5 min):** Resumen de criterios cubiertos y extras si aplican.

---

## Checklist rápido (para no olvidar ningún punto)

| Criterio | Dónde demostrarlo |
|----------|-------------------|
| Doc. diseño | README.md, python_backend/README.md, docs/video_script.md |
| Modelado datos | app/models.py |
| 4 índices | app/database.py + docs/explain/*.json |
| Doc. embebido | orders.items en POST /orders |
| Doc. referenciados | POST /restaurants, /users, /menu-items, /reviews, /orders y bulk |
| Lookup + filtros + proyección + sort + skip + limit | GET /orders/enriched/query |
| Update 1 | PATCH /orders/{id} (o cualquier recurso) |
| Update muchos | PATCH /orders/bulk/update-many |
| Delete 1 | DELETE /orders/{id} |
| Delete muchos | POST /orders/bulk/delete-many |
| GridFS + 50k docs | files.py + seed.py (orders ≥50k) |
| Agreg. simples | /analytics/counts, /analytics/simple/* |
| Agreg. complejas | /analytics/top-restaurants, /analytics/complex/* |
| Arrays | /menu-items/{id}/tags:add, /orders/{id}/items:push y :pull |
| Doc. embebidos | /analytics/embedded/* |
| BulkWrite (extra) | Por implementar si se desea el extra |
| Frontend | frontend/app.py — Streamlit |

Con este script puedes preparar la presentación o el video y responder punto por punto cada ítem de la rúbrica.
