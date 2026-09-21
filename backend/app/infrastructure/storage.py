"""Local filesystem storage helper (swap for Azure Blob Storage in production by
implementing the same interface)."""
from __future__ import annotations

import os
import uuid

from app.core.config import get_settings


def save_file(sub_folder: str, original_file_name: str, content: bytes) -> str:
    settings = get_settings()
    folder = os.path.join(settings.storage_root, sub_folder)
    os.makedirs(folder, exist_ok=True)
    unique_name = f"{uuid.uuid4()}_{original_file_name}"
    path = os.path.join(folder, unique_name)
    with open(path, "wb") as f:
        f.write(content)
    return path


def read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()
