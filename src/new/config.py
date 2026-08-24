"""Workbench configuration — paths, ports, AI defaults.

Everything resolves relative to the project root; nothing machine-specific is
hard-coded. The upload database lives under ``data/`` and persists across
restarts.
"""
from __future__ import annotations

import os
from pathlib import Path

NEW_DIR = Path(__file__).resolve().parent
SRC_DIR = NEW_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

# User-upload database (persistent, git-ignored). Override with WORKBENCH_DB_PATH.
def _resolve_db_path() -> Path:
    env = os.environ.get("WORKBENCH_DB_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return PROJECT_ROOT / "data" / "workbench.db"


DATABASE_PATH: Path = _resolve_db_path()

# Ports for the new stack (the old prototype keeps 8000 / 5173).
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = int(os.environ.get("WORKBENCH_BACKEND_PORT", "8100"))
FRONTEND_PORT = int(os.environ.get("WORKBENCH_FRONTEND_PORT", "5174"))

# Development CORS for the new Vite dev server.
CORS_ORIGINS = [
    "http://localhost:%d" % FRONTEND_PORT,
    "http://127.0.0.1:%d" % FRONTEND_PORT,
]

# ---------------------------------------------------------------------------
# AI provider (OpenAI-compatible). Credentials come from the environment OR the
# local settings store (src/new/.secrets/ai_provider.json). Never committed.
# ---------------------------------------------------------------------------
DEFAULT_BASE_URL = "https://api.openai.com/v1"

AI_ENABLED: bool = os.environ.get("WB_AI_ENABLED", "false").lower() == "true"
AI_BASE_URL: str = os.environ.get("WB_AI_BASE_URL", DEFAULT_BASE_URL)
AI_MODEL: str = os.environ.get("WB_AI_MODEL", "")
AI_API_KEY: str = os.environ.get("WB_AI_API_KEY", "")

AI_MAX_TOOL_ROUNDS: int = int(os.environ.get("WB_AI_MAX_TOOL_ROUNDS", "6"))
AI_MAX_HISTORY: int = int(os.environ.get("WB_AI_MAX_HISTORY", "20"))
AI_TEMPERATURE: float = float(os.environ.get("WB_AI_TEMPERATURE", "0.2"))
AI_REQUEST_TIMEOUT: float = float(os.environ.get("WB_AI_REQUEST_TIMEOUT", "60"))

# Backend-only secret store for the AI provider settings.
SECRETS_DIR = NEW_DIR / ".secrets"
SETTINGS_FILE = SECRETS_DIR / "ai_provider.json"

# Upload limits (defensive; files are parsed as streaming CSV).
MAX_UPLOAD_BYTES = int(os.environ.get("WB_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))