from __future__ import annotations

from typing import Any

from fastapi_modulo.modulos_sipet.modulo_base.bootstrap import MODULE_CONFIG
from fastapi_modulo.modulos_sipet.modulo_base.core.service import BaseModuleService
from fastapi_modulo.modulos_sipet.modulo_base.repositorios.common import get_db
from fastapi_modulo.modulos_sipet.modulo_base.repositorios.base_repository import ModuloBaseRepository


def _normalize_tenant(tenant_id: str | None) -> str:
    candidate = (tenant_id or "default").strip()
    return candidate or "default"


class ModuloBaseService(BaseModuleService):
    def __init__(self) -> None:
        super().__init__(MODULE_CONFIG)


service = ModuloBaseService()


def get_modulo_base_health() -> dict[str, Any]:
    return service.health_payload()


def get_modulo_base_resumen(tenant_id: str | None = None) -> dict[str, Any]:
    db = get_db()
    try:
        normalized_tenant = _normalize_tenant(tenant_id)
        repository = ModuloBaseRepository(db)
        return service.resumen_payload(
            tenant_id=normalized_tenant,
            total_registros=repository.count_by_tenant(normalized_tenant),
        )
    finally:
        db.close()
