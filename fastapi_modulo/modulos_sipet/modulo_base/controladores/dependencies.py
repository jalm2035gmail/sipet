from __future__ import annotations

import unicodedata

from fastapi import Depends, HTTPException, Request

from fastapi_modulo.modulos_sipet.modulo_base.modelos.schemas import ModuloBaseRequestContext


def _normalize_role(value: str | None) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return "usuario"
    normalized = unicodedata.normalize("NFKD", raw)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.replace(" ", "_").replace("-", "_")
    return normalized.strip("_") or "usuario"


def require_modulo_base_access(request: Request) -> None:
    role = _normalize_role(
        getattr(request.state, "user_role", None)
        or getattr(request.state, "role", None)
        or request.headers.get("x-role")
    )
    if role not in {"admin", "administrador", "superadmin", "superadministrador", "administrador_multiempresa"}:
        raise HTTPException(status_code=403, detail="Acceso restringido al núcleo base.")


def get_modulo_base_request_context(request: Request) -> ModuloBaseRequestContext:
    tenant_id = (getattr(request.state, "tenant_id", None) or "default").strip() or "default"
    user_role = (getattr(request.state, "user_role", None) or "usuario").strip() or "usuario"
    return ModuloBaseRequestContext(tenant_id=tenant_id, user_role=user_role)


def get_modulo_base_tenant_id(context: ModuloBaseRequestContext = Depends(get_modulo_base_request_context)) -> str:
    return context.tenant_id
