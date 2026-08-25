# Timber Data — Workbench

User-driven data workbench for a circular timber recovery operation: upload your own
timber data, explore an interactive dashboard with dimension filters, and chat with an
OpenAI-compatible AI grounded in that data.

The project contains two applications:

| App | Launcher | Backend | Frontend | Status |
|-----|----------|---------|----------|--------|
| **Workbench (new)** | `new.py` | `src/new/` | `static/new/` | ✅ active |
| Legacy prototype | `archived-version/main.py` | `archived-version/src/app/` | `archived-version/static/` | 🗄 archived |

This README documents the **active Workbench** application. The original
"Circular Timber Intelligence" prototype has been moved to `archived-version/`; it is
not required to run the Workbench and can be deleted without affecting startup.

## Quick start

```bash
py -m venv venv
venv/scripts/activate
```

```bash
pip install -r requirements.txt          # backend deps (fastapi, uvicorn, httpx, pytest, ...)
npm install --prefix static/new          # frontend deps (react, vite, recharts)
py new.py serve                          # full stack: backend :8100 + frontend :5174
```

- Backend API docs: http://127.0.0.1:8100/docs
- Frontend app: http://127.0.0.1:5174
- Health probe: http://127.0.0.1:8100/health

> To populate the workbench with a synthetic sample dataset, use the **载入示例数据**
> action on the dashboard (or call `POST /api/new/demo`). The generator lives in
> `scripts/generate_workbench_demo.py`.

## Layout

```
new.py                  one-command full-stack launcher (py new.py serve)
requirements.txt         root-level Python dependencies
static/new/              frontend (Vite + React + recharts)
src/new/                 backend (FastAPI app + routers + services)
scripts/
  generate_workbench_demo.py   synthetic sample-data generator
data/
  workbench.db           runtime SQLite database (user-uploaded / sample data)
  csv/                   CSV exports (13 tables)
docs/
  planning/              master plan + prompts
  data/                  data dictionaries, time semantics, validation reports
  backend/               backend docs + analyst tool schemas
  frontend/              data contract, schema, types, integration report
  assets/                posters + timber.pdf
archived-version/        legacy "Circular Timber Intelligence" prototype (old code)
  main.py                old launcher
  src/app/               old FastAPI backend
  static/                old frontend
```

## Environment

Backend behaviour is controlled by environment variables (`WB_AI_ENABLED`, `WB_AI_MODEL`,
`WB_AI_API_KEY`, `WB_AI_BASE_URL`, ...). See `src/new/.env.example`. The AI API key is
stored only server-side in `src/new/.secrets/` and is never returned to the frontend.

## Tests

```bash
python -m pytest src            # backend tests (contract parity, mutation, AI guards)
npm --prefix static/new run typecheck
npm --prefix static/new run build
```
