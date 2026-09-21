"""Generic raw-SQL repository base (no ORM, no SQLAlchemy).

Builds parametrized SQL from the model dataclass's fields (see ``dataclasses.fields``),
using ``app.infrastructure.db.models.types`` to (de)serialize UUID/datetime/JSON values.
"""
from __future__ import annotations

import dataclasses
import uuid
from typing import Generic, Optional, Sequence, Type, TypeVar

from app.infrastructure.db.models.types import deserialize_value, serialize_value
from app.infrastructure.db.session import DbSession

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]
    table_name: str

    def __init__(self, session: DbSession):
        self.session = session

    def _fields(self) -> Sequence[dataclasses.Field]:
        return dataclasses.fields(self.model)

    def _row_to_model(self, row) -> ModelT:
        kwargs = {
            f.name: deserialize_value(value, f.metadata.get("kind"))
            for f, value in zip(self._fields(), row)
        }
        return self.model(**kwargs)

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[ModelT]:
        columns = [f.name for f in self._fields()]
        sql = f"SELECT {', '.join(columns)} FROM {self.table_name} WHERE id = ?"
        row = await self.session.fetchone(sql, (str(entity_id),))
        return self._row_to_model(row) if row else None

    async def add(self, entity: ModelT) -> ModelT:
        fields = self._fields()
        columns = [f.name for f in fields]
        values = [serialize_value(getattr(entity, f.name)) for f in fields]
        placeholders = ", ".join("?" for _ in columns)
        sql = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        await self.session.execute(sql, values)
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        fields = [f for f in self._fields() if f.name != "id"]
        assignments = ", ".join(f"{f.name} = ?" for f in fields)
        values = [serialize_value(getattr(entity, f.name)) for f in fields]
        values.append(serialize_value(entity.id))
        sql = f"UPDATE {self.table_name} SET {assignments} WHERE id = ?"
        await self.session.execute(sql, values)
        return entity

    async def list(self, **filters) -> Sequence[ModelT]:
        columns = [f.name for f in self._fields()]
        sql = f"SELECT {', '.join(columns)} FROM {self.table_name}"
        params = []
        if filters:
            clauses = [f"{key} = ?" for key in filters]
            params = [serialize_value(value) for value in filters.values()]
            sql += " WHERE " + " AND ".join(clauses)
        rows = await self.session.fetchall(sql, params)
        return [self._row_to_model(row) for row in rows]

    async def commit(self) -> None:
        await self.session.commit()
