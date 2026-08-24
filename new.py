"""Workbench — one-command full-stack launcher (new application).

Usage:
    py new.py serve

Starts the new FastAPI backend (src/new/, http://127.0.0.1:8100) and the new
Vite frontend (static/new/, http://127.0.0.1:5174) concurrently. Both processes
are terminated together on exit (Ctrl+C).

The original prototype stack (py main.py serve) is untouched.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
NEW_STATIC_DIR = PROJECT_ROOT / "static" / "new"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8100
FRONTEND_PORT = 5174


def _print_guide() -> None:
    print("\n" + "=" * 70)
    print("  Workbench -- 数据工作台（new application）")
    print("  Backend  API : http://127.0.0.1:%d/docs" % BACKEND_PORT)
    print("  Frontend App : http://127.0.0.1:%d" % FRONTEND_PORT)
    print("  Health probe : http://127.0.0.1:%d/health" % BACKEND_PORT)
    print("  Press Ctrl+C to stop both servers.")
    print("=" * 70 + "\n")


def serve() -> None:
    sys.path.insert(0, str(SRC_DIR))
    _print_guide()

    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "new.main:app",
         "--host", BACKEND_HOST, "--port", str(BACKEND_PORT), "--reload"],
        cwd=str(SRC_DIR),
        env={**os.environ, "PYTHONPATH": str(SRC_DIR)},
    )

    npm = "npm.cmd" if os.name == "nt" else "npm"
    frontend = subprocess.Popen([npm, "run", "dev"], cwd=str(NEW_STATIC_DIR))

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