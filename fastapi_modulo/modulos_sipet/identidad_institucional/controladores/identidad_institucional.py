from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field, field_validator

from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_admin_or_superadmin
from fastapi_modulo.modulos_sipet.web.servicios.login_identity_service import (
    DEFAULT_LOGIN_IDENTITY,
    _build_login_asset_url,
    _load_login_identity,
    clear_frontend_page_cache,
    remove_login_image_if_custom,
    save_login_identity,
    store_login_image,
)
from fastapi_modulo.modulos_sipet.web.servicios.template_service import get_templates

router = APIRouter()

_MODULE_DIR = Path(__file__).resolve().parent.parent
_TEMPLATE_NAME = "modulos_sipet/identidad_institucional/vistas/identidad_institucional.html"
_CSS_PATH = _MODULE_DIR / "static" / "css" / "identidad_institucional.css"


class IdentidadForm(BaseModel):
    company_short_name: str = Field(default="", max_length=60)
    login_message: str = Field(default="", max_length=200)
    menu_position: Literal["arriba", "abajo"] = "arriba"

    @field_validator("company_short_name", "login_message", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return (v or "").strip()


def _render_identidad_institucional_page(request: Request) -> HTMLResponse:
    identity = _load_login_identity()
    favicon_url = _build_login_asset_url(identity.get("favicon_filename"), DEFAULT_LOGIN_IDENTITY["favicon_filename"])
    logo_url = _build_login_asset_url(identity.get("logo_filename"), DEFAULT_LOGIN_IDENTITY["logo_filename"])
    desktop_bg_url = _build_login_asset_url(identity.get("desktop_bg_filename"), DEFAULT_LOGIN_IDENTITY["desktop_bg_filename"])
    mobile_bg_url = _build_login_asset_url(identity.get("mobile_bg_filename"), DEFAULT_LOGIN_IDENTITY["mobile_bg_filename"])
    loaded_assets = sum(1 for v in [favicon_url, logo_url, desktop_bg_url, mobile_bg_url] if (v or "").strip())
    consistency = max(60, min(100, int(round((loaded_assets / 4) * 100)))) if loaded_assets else 60

    template = get_templates().env.get_template(_TEMPLATE_NAME)
    content = template.render(
        saved=request.query_params.get("saved") == "1",
        company_short_name=identity.get("company_short_name", DEFAULT_LOGIN_IDENTITY["company_short_name"]),
        login_message=identity.get("login_message", DEFAULT_LOGIN_IDENTITY["login_message"]),
        menu_position=(identity.get("menu_position") or DEFAULT_LOGIN_IDENTITY["menu_position"]).strip().lower(),
        favicon_url=favicon_url,
        logo_url=logo_url,
        desktop_bg_url=desktop_bg_url,
        mobile_bg_url=mobile_bg_url,
        loaded_assets=loaded_assets,
        consistency=consistency,
    )
    return render_backend_page(
        request,
        title="Identidad institucional",
        description="Configuración de identidad para la pantalla de login.",
        content=content,
        hide_floating_actions=True,
        show_page_header=True,
    )


@router.get("/identidad-institucional/css/identidad_institucional.css")
def identidad_institucional_css():
    return FileResponse(_CSS_PATH, media_type="text/css")


@router.get("/identidad-institucional", response_class=HTMLResponse)
def identidad_institucional_page(request: Request):
    require_admin_or_superadmin(request)
    return _render_identidad_institucional_page(request)


@router.get("/identidad-institucional/", response_class=HTMLResponse)
def identidad_institucional_page_slash(request: Request):
    require_admin_or_superadmin(request)
    return RedirectResponse(url="/identidad-institucional", status_code=307)


@router.post("/identidad-institucional", response_class=HTMLResponse)
async def identidad_institucional_save(
    request: Request,
    company_short_name: str = Form(""),
    login_message: str = Form(""),
    menu_position: str = Form("arriba"),
    favicon: Optional[UploadFile] = File(None),
    logo_empresa: Optional[UploadFile] = File(None),
    fondo_escritorio: Optional[UploadFile] = File(None),
    fondo_movil: Optional[UploadFile] = File(None),
    remove_favicon: str = Form("0"),
    remove_logo: str = Form("0"),
    remove_desktop: str = Form("0"),
    remove_mobile: str = Form("0"),
):
    require_admin_or_superadmin(request)
    form = IdentidadForm(
        company_short_name=company_short_name,
        login_message=login_message,
        menu_position=menu_position if menu_position in ("arriba", "abajo") else "arriba",
    )

    current = _load_login_identity()
    current["company_short_name"] = form.company_short_name or DEFAULT_LOGIN_IDENTITY["company_short_name"]
    current["login_message"] = form.login_message or DEFAULT_LOGIN_IDENTITY["login_message"]
    current["menu_position"] = form.menu_position

    if str(remove_favicon).strip() == "1":
        remove_login_image_if_custom(current.get("favicon_filename"))
        current["favicon_filename"] = DEFAULT_LOGIN_IDENTITY["favicon_filename"]
    if str(remove_logo).strip() == "1":
        remove_login_image_if_custom(current.get("logo_filename"))
        current["logo_filename"] = DEFAULT_LOGIN_IDENTITY["logo_filename"]
    if str(remove_desktop).strip() == "1":
        remove_login_image_if_custom(current.get("desktop_bg_filename"))
        current["desktop_bg_filename"] = DEFAULT_LOGIN_IDENTITY["desktop_bg_filename"]
    if str(remove_mobile).strip() == "1":
        remove_login_image_if_custom(current.get("mobile_bg_filename"))
        current["mobile_bg_filename"] = DEFAULT_LOGIN_IDENTITY["mobile_bg_filename"]

    new_favicon = await store_login_image(favicon, "favicon") if favicon else None
    if new_favicon:
        remove_login_image_if_custom(current.get("favicon_filename"))
        current["favicon_filename"] = new_favicon

    new_logo = await store_login_image(logo_empresa, "logo_empresa") if logo_empresa else None
    if new_logo:
        remove_login_image_if_custom(current.get("logo_filename"))
        current["logo_filename"] = new_logo

    new_desktop = await store_login_image(fondo_escritorio, "fondo_escritorio") if fondo_escritorio else None
    if new_desktop:
        remove_login_image_if_custom(current.get("desktop_bg_filename"))
        current["desktop_bg_filename"] = new_desktop

    new_mobile = await store_login_image(fondo_movil, "fondo_movil") if fondo_movil else None
    if new_mobile:
        remove_login_image_if_custom(current.get("mobile_bg_filename"))
        current["mobile_bg_filename"] = new_mobile

    save_login_identity(current)
    clear_frontend_page_cache()
    return RedirectResponse(url="/identidad-institucional?saved=1", status_code=303)
