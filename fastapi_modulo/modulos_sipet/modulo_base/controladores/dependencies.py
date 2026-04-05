from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from fastapi_modulo.modulos_sipet.modulo_base.bootstrap import permission_registry
from fastapi_modulo.modulos_sipet.modulo_base.modelos.schemas import ModuloBaseRequestContext
from fastapi_modulo.modulos_sipet.modulo_base.repositorios.common import get_db


def require_modulo_base_access(request: Request) -> None:
    try:
        permission_registry.require_permission(
            request,
            "modulo_base.ver",
            detail="Acceso restringido al núcleo base.",
        )
    except HTTPException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


def get_modulo_base_request_context(request: Request) -> ModuloBaseRequestContext:
    tenant_id = (getattr(request.state, "tenant_id", None) or "default").strip() or "default"
    user_role = (getattr(request.state, "user_role", None) or "usuario").strip() or "usuario"
    return ModuloBaseRequestContext(tenant_id=tenant_id, user_role=user_role)


def get_modulo_base_tenant_id(context: ModuloBaseRequestContext = Depends(get_modulo_base_request_context)) -> str:
    return context.tenant_id


def get_modulo_base_db() -> Generator[Session, None, None]:
    db = get_db()
    try:
        yield db
    finally:
        db.close()
