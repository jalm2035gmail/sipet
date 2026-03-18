from fastapi import HTTPException, Request
from fastapi_modulo.modulos_sipet.web.servicios.access_service import is_superadmin

def require_superadmin(request: Request, detail: str = "Acceso solo para superadministrador") -> None:
    if not is_superadmin(request):
        raise HTTPException(status_code=403, detail=detail)
