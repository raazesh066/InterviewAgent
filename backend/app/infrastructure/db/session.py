"""Raw pyodbc-based database session management (no ORM, no SQLAlchemy).

pyodbc has no native asyncio support, so every blocking DB-API call is offloaded to a
worker thread via ``asyncio.to_thread``. ``DbSession`` wraps any DB-API 2.0 connection
(``pyodbc.Connection`` in production/SQL Server, ``sqlite3.Connection`` in tests) since
both use the same "?" (qmark) parameter placeholder style.
"""
from __future__ import annotations

import asyncio
import pathlib
import sqlite3
import threading
from typing import Any, AsyncIterator, Optional, Sequence

import pyodbc

from app.core.config import get_settings

settings = get_settings()
_sqlite_initialized = False
_sqlite_init_lock = threading.Lock()
_SQLITE_SCHEMA_PATH = pathlib.Path(__file__).with_name("schema_sqlite.sql")


class DbSession:
    """Thin async wrapper around a single DB-API 2.0 connection."""

    def __init__(self, connection: Any):
        self._connection = connection

    async def fetchone(self, sql: str, params: Sequence[Any] = ()) -> Optional[Any]:
        return await asyncio.to_thread(self._fetchone_sync, sql, params)

    def _fetchone_sync(self, sql: str, params: Sequence[Any]) -> Optional[Any]:
        cursor = self._connection.cursor()
        cursor.execute(sql, tuple(params))
        return cursor.fetchone()

    async def fetchall(self, sql: str, params: Sequence[Any] = ()) -> list:
        return await asyncio.to_thread(self._fetchall_sync, sql, params)

    def _fetchall_sync(self, sql: str, params: Sequence[Any]) -> list:
        cursor = self._connection.cursor()
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()

    async def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        await asyncio.to_thread(self._execute_sync, sql, params)

    def _execute_sync(self, sql: str, params: Sequence[Any]) -> None:
        cursor = self._connection.cursor()
        cursor.execute(sql, tuple(params))

    async def commit(self) -> None:
        await asyncio.to_thread(self._connection.commit)

    async def rollback(self) -> None:
        await asyncio.to_thread(self._connection.rollback)

    def close(self) -> None:
        self._connection.close()


def _connect() -> Any:
    if settings.database_backend.lower() == "sqlite":
        database_path = pathlib.Path(settings.sqlite_database_path)
        if not database_path.is_absolute():
            backend_root = pathlib.Path(__file__).resolve().parents[3]
            database_path = backend_root / database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database_path, check_same_thread=False)
        connection.execute("PRAGMA foreign_keys = ON")
        global _sqlite_initialized
        with _sqlite_init_lock:
            if not _sqlite_initialized:
                connection.executescript(_SQLITE_SCHEMA_PATH.read_text(encoding="utf-8"))
                _sqlite_initialized = True
        return connection
    return pyodbc.connect(settings.build_database_connection_string(), autocommit=False)


async def get_db_session() -> AsyncIterator[DbSession]:
    connection = await asyncio.to_thread(_connect)
    session = DbSession(connection)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        session.close()
