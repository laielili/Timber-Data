"""Backend configuration — single source for paths, dataset bounds and assumptions defaults.

The approved synthetic database is the authority. All paths are resolved relative to the
project root; machine-specific absolute paths are never hard-coded. Override with the
`CTI_DATABASE_PATH` (or `DATABASE_PATH`) environment variable.
"""
from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent


def _resolve_database_path() -> Path:
    env = os.environ.get("CTI_DATABASE_PATH") or os.environ.get("DATABASE_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return PROJECT_ROOT / "data" / "circular_timber_synthetic.db"


DATABASE_PATH: Path = _resolve_database_path()

# Prototype dataset bounds (TIME_SEMANTICS.md). Requests outside this range are rejected
# with HTTP 422 — the backend never silently clamps user dates.
DATASET_PERIOD_START: date = date(2025, 1, 1)
DATASET_PERIOD_END: date = date(2025, 12, 31)
DATASET_AS_OF: datetime = datetime(2025, 12, 31, 18, 0, 0)

DEFAULT_PERIOD_START = DATASET_PERIOD_START.isoformat()
DEFAULT_PERIOD_END = DATASET_PERIOD_END.isoformat()
DEFAULT_AS_OF = DATASET_AS_OF.isoformat()

# Core recovery cost categories (North Star definition — Transport is reported separately).
CORE_COST_CATEGORIES = ("Sorting Labour", "Inspection", "Processing", "Special Handling", "Disposal")

# Prototype dataset identifier (matches meta.seed in the mock payloads).
DATASET_SEED = 20260818

# Development CORS origins for the future React dev server (Backend Phase 02).
# Isolated here and documented — no wildcard production default.
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

# ---------------------------------------------------------------------------
# AI Analyst (Phase 02) — all credentials come from the environment ONLY.
# Never hard-code keys, never expose them to the frontend/browser bundle.
# ---------------------------------------------------------------------------
AI_ENABLED: bool = os.environ.get("AI_ENABLED", "false").lower() == "true"
AI_PROVIDER: str = os.environ.get("AI_PROVIDER", "openai-compatible")
AI_MODEL: str = os.environ.get("AI_MODEL", "")
AI_API_KEY: str = os.environ.get("AI_API_KEY", "")
AI_BASE_URL: str = os.environ.get("AI_BASE_URL", "https://api.openai.com/v1")

# Guardrails (token / cost / loop safety).
AI_MAX_TOOL_ROUNDS: int = int(os.environ.get("AI_MAX_TOOL_ROUNDS", "6"))
AI_MAX_QUESTION_LEN: int = int(os.environ.get("AI_MAX_QUESTION_LEN", "2000"))
AI_MAX_HISTORY: int = int(os.environ.get("AI_MAX_HISTORY", "12"))
AI_TEMPERATURE: float = float(os.environ.get("AI_TEMPERATURE", "0.1"))
AI_REQUEST_TIMEOUT: float = float(os.environ.get("AI_REQUEST_TIMEOUT", "60"))
