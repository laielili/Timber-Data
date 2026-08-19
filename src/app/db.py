"""Read-only SQLite access layer.

Connections are opened per-request (or per test) and always closed. The backend is
READ ONLY for this phase — no POST / PATCH / DELETE business data operations exist.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from . import config


def connect() -> sqlite3.Connection:
    """Open a read-only connection to the approved synthetic database."""
    conn = sqlite3.connect(
        f"file:{config.DATABASE_PATH}?mode=ro",
        uri=True,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def database_ok() -> bool:
    """Health probe: can we open the database and read a marker value?"""
    try:
        with session() as conn:
            conn.execute("SELECT COUNT(*) FROM Batches").fetchone()
        return True
    except sqlite3.Error:
        return False
