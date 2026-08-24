"""FastAPI dependencies for the workbench app."""
from __future__ import annotations

import sqlite3
from typing import Iterator

from .db import session


def get_conn() -> Iterator[sqlite3.Connection]:
    with session() as conn:
        yield conn