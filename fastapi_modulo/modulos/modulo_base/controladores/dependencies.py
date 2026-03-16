from __future__ import annotations

from fastapi import Request

from fastapi_modulo.modulos.modulo_base.bootstrap import permission_registry


def require_modulo_base_access(request: Request) -> None:
    permission_registry.require_access(request)
