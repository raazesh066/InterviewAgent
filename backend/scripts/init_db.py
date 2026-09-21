"""Initialize the SQL Server / Azure SQL database schema using raw pyodbc.

Usage:
    python -m scripts.init_db

Executes the T-SQL DDL in docs/api/DATABASE_SCHEMA.sql against the database configured
via the app's settings (DATABASE_SERVER / DATABASE_NAME / ... env vars).
"""
from __future__ import annotations

import pathlib
import re

import pyodbc

from app.core.config import get_settings

SCHEMA_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / "docs" / "api" / "DATABASE_SCHEMA.sql"


def _split_statements(sql_script: str) -> list[str]:
    """Split a SQL script into individual statements on blank-line boundaries."""
    statements = re.split(r";\s*\n", sql_script)
    return [s.strip() for s in statements if s.strip()]


def main() -> None:
    settings = get_settings()
    sql_script = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = _split_statements(sql_script)

    connection = pyodbc.connect(settings.build_database_connection_string(), autocommit=True)
    try:
        cursor = connection.cursor()
        for statement in statements:
            cursor.execute(statement)
        print(f"Applied {len(statements)} statements from {SCHEMA_PATH}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
