from __future__ import annotations

from fastapi import Request

from fastapi_modulo.modulos_sipet.web.servicios.module_tools import require_app_access


def require_crm_access(request: Request) -> None:
    require_app_access(request, "CRM", "Acceso restringido al módulo CRM")
