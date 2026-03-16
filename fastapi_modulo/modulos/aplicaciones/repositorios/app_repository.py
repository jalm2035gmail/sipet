from typing import Any

from fastapi_modulo.module_registry import list_modules_payload, set_module_enabled


def list_catalog_modules() -> list[dict[str, Any]]:
    return list_modules_payload()


def set_catalog_module_enabled(module_key: str, enabled: bool) -> dict[str, Any]:
    return set_module_enabled(module_key, enabled)


__all__ = ["list_catalog_modules", "set_catalog_module_enabled"]
