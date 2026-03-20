"""Router para la pantalla base del módulo IA."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="fastapi_modulo/modulos/ia/vistas")

@router.get("/ia", response_class=HTMLResponse)
def ia_home(request: Request):
    """
    Página principal del módulo IA (Fase 0).
    """
    return templates.TemplateResponse("ia.html", {"request": request})
