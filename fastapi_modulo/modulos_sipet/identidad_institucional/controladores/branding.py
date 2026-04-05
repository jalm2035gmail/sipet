from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field, field_validator

from fastapi_modulo.modulos_sipet.identidad_institucional.servicios.acceso_empresa_service import require_empresa_permission
from fastapi_modulo.modulos_sipet.identidad_institucional.servicios.identidad_service import (
    build_identidad_view_context,
    save_identity_assets,
)
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.servicios.template_service import get_templates


router = APIRouter()
logger = logging.getLogger(__name__)

_MODULE_DIR = Path(__file__).resolve().parent.parent
_TEMPLATE_NAME = "modulos_sipet/identidad_institucional/vistas/identidad_institucional.html"
_CSS_PATH = _MODULE_DIR / "static" / "css" / "identidad_institucional.css"

_PLACEHOLDER_CONTENT = """
<section class="w-full flex flex-col items-center justify-center" style="min-height:260px;gap:1rem;">
  <i class="{icon}" style="font-size:3rem;opacity:0.25;"></i>
  <p style="font-size:1rem;opacity:0.5;margin:0;">{label}</p>
  <p style="font-size:0.85rem;opacity:0.35;margin:0;">Próximamente disponible.</p>
</section>
"""


class IdentidadForm(BaseModel):
    company_short_name: str = Field(default="", max_length=60)
    login_message: str = Field(default="", max_length=200)
    menu_position: Literal["arriba", "abajo"] = "arriba"

    @field_validator("company_short_name", "login_message", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return (value or "").strip()


def _render_identidad_institucional_page(
    request: Request,
    *,
    error_message: str = "",
    form_values: Optional[dict[str, str]] = None,
    status_code: int = 200,
) -> HTMLResponse:
    template = get_templates().env.get_template(_TEMPLATE_NAME)
    context = build_identidad_view_context(form_values=form_values)
    content = template.render(
        saved=request.query_params.get("saved") == "1",
        error_message=error_message,
        **context,
    )
    return render_backend_page(
        request,
        title="Identidad institucional",
        description="Configuración de identidad para la pantalla de login.",
        content=content,
        hide_floating_actions=True,
        show_page_header=True,
        status_code=status_code,
    )


@router.get("/identidad-institucional/css/identidad_institucional.css")
def identidad_institucional_css():
    return FileResponse(_CSS_PATH, media_type="text/css")


@router.get("/identidad-institucional", response_class=HTMLResponse)
def identidad_institucional_page(request: Request):
    require_empresa_permission(request, "ver_branding")
    return _render_identidad_institucional_page(request)


@router.get("/identidad-institucional/", response_class=HTMLResponse)
def identidad_institucional_page_slash(request: Request):
    require_empresa_permission(request, "ver_branding")
    return RedirectResponse(url="/identidad-institucional", status_code=307)


@router.post("/identidad-institucional", response_class=HTMLResponse)
async def identidad_institucional_save(
    request: Request,
    company_short_name: str = Form(""),
    login_message: str = Form(""),
    menu_position: str = Form("arriba"),
    sidebar_style_variant: str = Form("modern"),
    favicon: Optional[UploadFile] = File(None),
    logo_empresa: Optional[UploadFile] = File(None),
    logo_login: Optional[UploadFile] = File(None),
    fondo_escritorio: Optional[UploadFile] = File(None),
    fondo_movil: Optional[UploadFile] = File(None),
    remove_favicon: str = Form("0"),
    remove_logo: str = Form("0"),
    remove_login_logo: str = Form("0"),
    remove_desktop: str = Form("0"),
    remove_mobile: str = Form("0"),
):
    require_empresa_permission(request, "editar_branding")
    form = IdentidadForm(
        company_short_name=company_short_name,
        login_message=login_message,
        menu_position=menu_position if menu_position in ("arriba", "abajo") else "arriba",
    )
    try:
        await save_identity_assets(
            company_short_name=form.company_short_name,
            login_message=form.login_message,
            menu_position=form.menu_position,
            sidebar_style_variant=sidebar_style_variant,
            favicon=favicon,
            logo_empresa=logo_empresa,
            logo_login=logo_login,
            fondo_escritorio=fondo_escritorio,
            fondo_movil=fondo_movil,
            remove_favicon=str(remove_favicon).strip() == "1",
            remove_logo=str(remove_logo).strip() == "1",
            remove_login_logo=str(remove_login_logo).strip() == "1",
            remove_desktop=str(remove_desktop).strip() == "1",
            remove_mobile=str(remove_mobile).strip() == "1",
        )
        return RedirectResponse(url="/identidad-institucional?saved=1", status_code=303)
    except HTTPException as exc:
        detail = str(getattr(exc, "detail", "") or "").strip() or "No se pudo guardar la identidad institucional."
        logger.warning("identity branding upload failed: %s", detail)
        return _render_identidad_institucional_page(
            request,
            error_message=detail,
            form_values={
                "company_short_name": form.company_short_name,
                "login_message": form.login_message,
                "menu_position": form.menu_position,
                "sidebar_style_variant": sidebar_style_variant,
            },
            status_code=int(getattr(exc, "status_code", 400) or 400),
        )
    except Exception:
        logger.exception("identity branding save failed")
        return _render_identidad_institucional_page(
            request,
            error_message="No se pudo guardar el icono o los recursos visuales. Verifica permisos de escritura del servidor e intenta de nuevo.",
            form_values={
                "company_short_name": form.company_short_name,
                "login_message": form.login_message,
                "menu_position": form.menu_position,
                "sidebar_style_variant": sidebar_style_variant,
            },
            status_code=500,
        )


@router.get("/plantillas", response_class=HTMLResponse)
def plantillas_page(request: Request):
    require_empresa_permission(request, "ver_plantillas")
    content = _PLACEHOLDER_CONTENT.format(icon="fa-solid fa-file-alt", label="Plantillas")
    return render_backend_page(
        request,
        title="Plantillas",
        description="Gestión de plantillas del sistema.",
        content=content,
        show_page_header=True,
    )


@router.get("/plantillas/constructor", response_class=HTMLResponse)
def plantillas_constructor_page(request: Request):
    require_empresa_permission(request, "editar_plantillas")
    content = _PLACEHOLDER_CONTENT.format(icon="fa-solid fa-tools", label="Constructor de formularios")
    return render_backend_page(
        request,
        title="Constructor de formularios",
        description="Constructor visual de formularios y plantillas.",
        content=content,
        show_page_header=True,
    )
