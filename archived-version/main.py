"""Circular Timber Intelligence -- one-command full-stack launcher.

Usage:
    py main.py serve

Starts the FastAPI backend (src/, http://127.0.0.1:8000) and the Vite
frontend (static/, http://127.0.0.1:5173) concurrently. Both processes are
terminated together on exit (Ctrl+C).

Backend configuration still comes from environment variables
(e.g. AI_ENABLED=true, AI_API_KEY=...); see src/.env.example.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
STATIC_DIR = PROJECT_ROOT / "static"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 5173


def _print_guide() -> None:
    print("\n" + "=" * 70)
    print("  Circular Timber Intelligence -- full-stack dev servers")
    print("  Backend  API : http://127.0.0.1:%d/docs" % BACKEND_PORT)
    print("  Frontend App : http://127.0.0.1:%d" % FRONTEND_PORT)
    print("  Health probe : http://127.0.0.1:%d/health" % BACKEND_PORT)
    print("  Press Ctrl+C to stop both servers.")
    print("=" * 70 + "\n")


def serve() -> None:
    sys.path.insert(0, str(SRC_DIR))
    _print_guide()

    # Backend: uvicorn with reload (config.py resolves the DB path via __file__,
    # independent of the working directory).
    import uvicorn
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", BACKEND_HOST, "--port", str(BACKEND_PORT), "--reload"],
        cwd=str(SRC_DIR),
        env={**os.environ, "PYTHONPATH": str(SRC_DIR)},
    )

    # Frontend: Vite dev server inside static/.
    npm = "npm.cmd" if os.name == "nt" else "npm"
    frontend = subprocess.Popen([npm, "run", "dev"], cwd=str(STATIC_DIR))

    try:
        while True:
            if backend.poll() is not None or frontend.poll() is not None:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (backend, frontend):
            if proc.poll() is None:
                try:
                    proc.terminate()
                except OSError:
                    pass
        time.sleep(1)
        for proc in (backend, frontend):
            if proc.poll() is None:
                try:
                    proc.kill()
                except OSError:
                    pass
        print("\nBoth servers stopped.")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve()
        return
    print(__doc__.strip())


if __name__ == "__main__":
    main()