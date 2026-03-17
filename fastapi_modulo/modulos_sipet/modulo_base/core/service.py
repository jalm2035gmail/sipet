from __future__ import annotations

from typing import Any

from fastapi_modulo.modulos_sipet.modulo_base.core.module import ModuleConfig


class BaseService:
    def __init__(self, db: Any, tenant_id: str = "default") -> None:
        self.db = db
        self.tenant_id = tenant_id or "default"


class BaseModuleService(BaseService):
    def __init__(self, config: ModuleConfig, db: Any = None, tenant_id: str = "default") -> None:
        super().__init__(db=db, tenant_id=tenant_id)
        self.config = config

    def health_payload(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "module": self.config.key,
            "purpose": "framework",
            "route": self.config.route,
        }

    def resumen_payload(self, *, tenant_id: str, total_registros: int) -> dict[str, Any]:
        return {
            "tenant_id": tenant_id,
            "total_registros": total_registros,
            "health": "ok",
            "module": self.config.key,
            "sections": list(self.config.sections),
        }
