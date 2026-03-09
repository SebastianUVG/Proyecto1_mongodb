# Guion sugerido (video ≤ 10 min)

## Setup (0:00 - 1:00)

- Mostrar `.env` (sin credenciales reales) o export de `MONGO_URI`.
- Mostrar que el API está corriendo y abrir `http://localhost:8000/docs`.

## Dataset + CRUD (1:00 - 4:00)

1) En el **CLI** ejecutar:
   - **Opción 1**: Seed (crea ≥50,000 órdenes).
2) En `/docs` o en el CLI:
   - Crear 1 restaurant (CRUD create).
   - Crear 1 user (CRUD create).
   - Crear 1 menu item (CRUD create).
   - Crear 1 order + review (transacción) (**CLI opción 9**).

## Reads avanzadas (lookup + filtros + proyección + sort + skip/limit) (4:00 - 6:00)

- Ejecutar **CLI opción 10** (Orders enriched).
  - Explicar: usa `$lookup` a `users` y `restaurants`, trae paginado, con proyección lite.

## Arrays (6:00 - 7:00)

- Mostrar que se puede:
  - `menuItems.tags` con `$addToSet`/`$pull` (endpoints de tags).
  - `orders.items` con `$push`/`$pull` (`/orders/{id}/items:push` y `/orders/{id}/items:pull`).

## Agregaciones (7:00 - 8:30)

- Ejecutar **CLI opción 11**:
  - Top restaurantes (reviews → group + lookup)
  - Platillos más vendidos (`$unwind`)
  - Revenue por restaurante
  - Counts simples

## Índices + explain (8:30 - 9:30)

- Ejecutar **CLI opción 14** (Explain report).
- Mostrar `python_backend/docs/explain/*.json` y señalar que aparece `IXSCAN` (no `COLLSCAN`).

## GridFS (9:30 - 10:00)

- Ejecutar:
  - **CLI opción 12**: upload archivo
  - **CLI opción 13**: download archivo y mostrar que se guardó localmente

