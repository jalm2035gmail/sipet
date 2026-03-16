from __future__ import annotations


def list_available_modules() -> list[dict]:
    from fastapi_modulo import main as core

    return list(core.list_modules_payload())
