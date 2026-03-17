from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos_sipet.modulo_base.core.repository import SQLAlchemyRepository
from fastapi_modulo.modulos_sipet.modulo_base.modelos.db_models import ModuloBaseRegistro


class ModuloBaseRepository(SQLAlchemyRepository[ModuloBaseRegistro]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ModuloBaseRegistro)

    def count_by_tenant(self, tenant_id: str) -> int:
        return self.count_by(tenant_id=tenant_id)

    def list_by_tenant(self, tenant_id: str) -> list[ModuloBaseRegistro]:
        return self.list(tenant_id=tenant_id)
