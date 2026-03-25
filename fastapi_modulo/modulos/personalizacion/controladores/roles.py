"""Controlador de roles — roles.py"""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from fastapi_modulo.core.db import SessionLocal, engine
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Rol
from fastapi_modulo.modulos_sipet.web.servicios.require_superadmin import require_superadmin
from fastapi_modulo.modulos_sipet.web.servicios.ui_shell_service import get_colores_context

# ── Constantes ────────────────────────────────────────────────────────────────

DEFAULT_SYSTEM_ROLES = [
    ("superadministrador",       "Acceso total a todo el módulo"),
    ("administrador_multiempresa","Acceso a todas las empresas del sistema"),
    ("administrador",            "Acceso completo a su empresa"),
    ("autoridades",              "Acceso al tablero de control"),
    ("departamento",             "Acceso a su departamento"),
    ("usuario",                  "Acceso solo a sus datos"),
]

router = APIRouter()
templates = Jinja2Templates(directory=["fastapi_modulo/templates", "fastapi_modulo"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def ensure_default_roles() -> None:
    """Crea los roles del sistema si no existen."""
    Rol.__table__.create(bind=engine, checkfirst=True)
    db = SessionLocal()
    try:
        for role_name, role_description in DEFAULT_SYSTEM_ROLES:
            existing = db.query(Rol).filter(Rol.nombre == role_name).first()
            if existing:
                if (existing.descripcion or "").strip() != role_description:
                    existing.descripcion = role_description
                    db.add(existing)
                continue
            db.add(Rol(nombre=role_name, descripcion=role_description))
        db.commit()
    finally:
        db.close()


def _roles_template_context(request: Request, roles: list, title: str, description: str) -> dict:
    """Construye el contexto común para las vistas de roles."""
    from pathlib import Path
    MODULE_DIR = Path(__file__).resolve().parent.parent
    roles_html_path = MODULE_DIR / "vistas" / "roles.html"
    with open(roles_html_path, encoding="utf-8") as f:
        template_str = f.read()

    # Renderizar filas de la tabla
    from html import escape
    rows_html = "".join(
        f"<tr>"
        f"<td>{escape(role.nombre or '')}</td>"
        f"<td>{escape(role.descripcion or '')}</td>"
        f"<td>"
        f"<form method='post' action='/roles/edit/{role.id}'>"
        f"<input type='text' name='nombre' value='{escape(role.nombre or '')}' required class='campo-personalizado'>"
        f"<input type='text' name='descripcion' value='{escape(role.descripcion or '')}' class='campo-personalizado'>"
        f"<button type='submit' class='color-btn color-btn--ghost'>Editar</button>"
        f"</form>"
        f"<form method='post' action='/roles/delete/{role.id}'>"
        f"<button type='submit' class='color-btn color-btn--primary' "
        f"onclick=\"return confirm('¿Eliminar este rol?')\">Eliminar</button>"
        f"</form>"
        f"</td>"
        f"</tr>"
        for role in roles
    )
    content = template_str.replace("{{ rows_html }}", rows_html)

    return {
        "request": request,
        "title": title,
        "description": description,
        "page_title": title,
        "page_description": description,
        "section_label": "",
        "section_title": "",
        "content": content,
        "floating_actions_html": "",
        "floating_actions_screen": "personalization",
        "hide_floating_actions": True,
        "show_page_header": True,
        "colores": get_colores_context(),
    }


# ── Rutas ─────────────────────────────────────────────────────────────────────

@router.get("/roles", response_class=HTMLResponse)
def roles_page(request: Request):
    ensure_default_roles()
    db = SessionLocal()
    try:
        roles = db.query(Rol).order_by(Rol.id.asc()).all()
    finally:
        db.close()
    return templates.TemplateResponse(
        "base.html",
        _roles_template_context(request, roles, "Roles", "Administra los roles del sistema."),
    )


@router.get("/roles-sistema", response_class=HTMLResponse)
@router.get("/roles-permisos", response_class=HTMLResponse)
@router.get("/api/v1/personalizacion/roles-permisos", response_class=HTMLResponse)
@router.get("/personalizacion/roles-permisos", response_class=HTMLResponse)
def roles_permisos_page(request: Request):
    """Vista de roles y permisos — solo superadmin. Redirige a /roles si no tiene acceso."""
    try:
        require_superadmin(request)
    except HTTPException:
        return RedirectResponse(url="/roles", status_code=status.HTTP_303_SEE_OTHER)
    ensure_default_roles()
    db = SessionLocal()
    try:
        roles = db.query(Rol).order_by(Rol.id.asc()).all()
    finally:
        db.close()
    return templates.TemplateResponse(
        "base.html",
        _roles_template_context(request, roles, "Roles y permisos", "Gestión de roles y permisos"),
    )


@router.post("/roles/create")
def create_role(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(""),
):
    del request
    db = SessionLocal()
    try:
        db.add(Rol(nombre=nombre.strip(), descripcion=descripcion.strip()))
        db.commit()
    finally:
        db.close()
    return RedirectResponse(url="/roles", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/roles/edit/{role_id}")
def edit_role(
    request: Request,
    role_id: int,
    nombre: str = Form(...),
    descripcion: str = Form(""),
):
    del request
    db = SessionLocal()
    try:
        role = db.query(Rol).filter(Rol.id == role_id).first()
        if role:
            role.nombre = nombre.strip()
            role.descripcion = descripcion.strip()
            db.add(role)
            db.commit()
    finally:
        db.close()
    return RedirectResponse(url="/roles", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/roles/delete/{role_id}")
def delete_role(request: Request, role_id: int):
    del request
    db = SessionLocal()
    try:
        role = db.query(Rol).filter(Rol.id == role_id).first()
        if role:
            db.delete(role)
            db.commit()
    finally:
        db.close()
    return RedirectResponse(url="/roles", status_code=status.HTTP_303_SEE_OTHER)
    