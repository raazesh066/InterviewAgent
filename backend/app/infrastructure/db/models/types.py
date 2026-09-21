"""Serialization helpers for the raw pyodbc data layer (no ORM, no SQLAlchemy).

Dataclass fields whose ``metadata`` mark them as ``"uuid"``, ``"datetime"`` or ``"json"``
are converted to/from plain SQL parameter values (strings) by ``BaseRepository`` using
these helpers.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional


def serialize_value(value: Any) -> Any:
    """Convert a Python attribute value into a plain SQL parameter value."""
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return value


def deserialize_value(value: Any, kind: Optional[str]) -> Any:
    """Convert a raw SQL column value back into the dataclass field's Python type."""
    if value is None:
        return None
    if kind == "uuid":
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    if kind == "datetime":
        return value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if kind == "json":
        return json.loads(value) if isinstance(value, str) else value
    return value
