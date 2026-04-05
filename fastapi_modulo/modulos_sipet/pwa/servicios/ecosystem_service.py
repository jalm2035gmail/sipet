from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi_modulo.core.module_registry import list_enabled_module_manifests


def _get_enabled_keys() -> set[str]:
    try:
        manifests = list_enabled_module_manifests()
        return {m.get("name", "") for m in manifests if m.get("name")}
    except Exception:
        return set()


def is_module_available(module_key: str) -> bool:
    return module_key in _get_enabled_keys()


def is_multitienda_available() -> bool:
    return is_module_available("multitienda")


def get_enabled_extensions() -> dict[str, Any]:
    keys = _get_enabled_keys()
    return {
        "multitienda": "multitienda" in keys,
    }
