## Proyecto 1 MongoDB (2026) — Backend en Python

El backend principal del proyecto está en `python_backend/` (FastAPI + MongoDB).

### Cómo correr (rápido)

```bash
cd python_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export MONGO_URI="mongodb+srv://<Usuario>:<db_password>@cluster0.bziapgx.mongodb.net/?appName=<nombreCluster>"
uvicorn app.main:app --reload --port 8000
```

- Swagger: `http://localhost:8000/docs`

### CLI (demo)

```bash
python3 cli/main.py
```

### Seed (≥50,000 docs)

```bash
python3 scripts/seed.py
```

> Nota: El backend del proyecto es `python_backend/`. Cualquier directorio viejo de backend (por ejemplo `Restaurant_backend/`) ya no se usa.
