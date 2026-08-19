# Circular Timber Intelligence

Executive dashboard + AI analyst prototype for a circular timber recovery operation,
backed by a deterministic synthetic SQLite dataset (read-only).

## Quick start

```Shell
py -m venv venv
venv/scripts/activate
```

```bash
pip install -r requirements.txt     # backend deps (fastapi, uvicorn, pytest, ...)
npm install --prefix static         # frontend deps (react, vite, recharts)
py main.py serve                    # full stack: backend :8000 + frontend :5173
```

- Backend API docs: http://127.0.0.1:8000/docs
- Frontend app: http://127.0.0.1:5173
- Health probe: http://127.0.0.1:8000/health

## Layout

```
main.py                  one-command full-stack launcher (py main.py serve)
requirements.txt         root-level Python dependencies
static/                  frontend (original frontend/, incl. node_modules & dist)
src/                     backend (original backend/: FastAPI app + tests)
scripts/                 generate_synthetic_database.py (data generator)
data/
  circular_timber_synthetic.db       approved SQLite source of truth
  circular_timber_synthetic_database.xlsx
  csv/                   CSV exports (13 tables)
  mock/                  frontend mock JSON (regression reference)
docs/
  planning/              master plan + prompts
  data/                  data dictionaries, time semantics, validation reports
  backend/               backend docs + analyst tool schemas
  frontend/              data contract, schema, types, integration report
  assets/                posters + timber.pdf
```

## Environment

Backend behaviour is controlled by environment variables (`AI_ENABLED`, `AI_PROVIDER`,
`AI_MODEL`, `AI_API_KEY`, `AI_BASE_URL`, ...). See `src/.env.example`. Credentials are
never committed.

## Tests

```bash
python -m pytest src            # backend tests (contract parity, mutation, AI guards)
npm --prefix static run typecheck
npm --prefix static run build
```
