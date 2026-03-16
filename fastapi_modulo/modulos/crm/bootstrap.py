from __future__ import annotations

from fastapi_modulo.modulos.crm.repositorios.common import ensure_crm_schema


def init_crm_module() -> None:
    ensure_crm_schema()
