"""Source projects repository — source-type lookups."""
from __future__ import annotations

import sqlite3


def get_source_types(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT DISTINCT source_type FROM SourceProjects ORDER BY source_type").fetchall()
    return [r["source_type"] for r in rows]
