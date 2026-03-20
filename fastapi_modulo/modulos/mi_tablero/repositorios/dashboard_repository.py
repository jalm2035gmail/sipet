from __future__ import annotations

from fastapi_modulo.core.module_registry import list_modules_payload


def list_available_modules() -> list[dict]:
    return list(list_modules_payload())
