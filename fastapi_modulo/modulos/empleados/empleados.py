import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi_modulo.db import SessionLocal

router = APIRouter()

EMPLEADOS_TEMPLATE_PATH = os.path.join(
    "fastapi_modulo",
    "templates",
    "modulos",
    "empleados",
    "empleados.html",
)


@router.get("/api/colaboradores", response_class=JSONResponse)
def api_listar_colaboradores():
    # Import diferido para evitar importación circular con fastapi_modulo.main.
    from fastapi_modulo.main import Usuario, _decrypt_sensitive

    db = SessionLocal()
    try:
        rows = db.query(Usuario).all()
        data = [
            {
                "id": u.id,
                "nombre": u.nombre or "",
                "usuario": (_decrypt_sensitive(u.usuario) or "").strip(),
                "correo": (_decrypt_sensitive(u.correo) or "").strip(),
                "departamento": u.departamento or "",
                "estado": "Activo" if getattr(u, "is_active", True) else "Inactivo",
            }
            for u in rows
        ]
        return {"success": True, "data": data}
    finally:
        db.close()


def _load_empleados_template() -> str:
    try:
        with open(EMPLEADOS_TEMPLATE_PATH, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return """
        <section id="usuario-panel" class="usuario-panel">
            <div id="usuario-view"></div>
        </section>
        """


def _render_empleados_page(
    request: Request,
    title: str = "Usuarios",
    description: str = "Gestiona usuarios, roles y permisos desde la misma pantalla",
) -> HTMLResponse:
    from fastapi_modulo.main import render_backend_page

    return render_backend_page(
        request,
        title=title,
        description=description,
        content=_load_empleados_template(),
        hide_floating_actions=True,
        view_buttons=[
            {"label": "Form", "icon": "/templates/icon/formulario.svg", "view": "form"},
            {"label": "Lista", "icon": "/templates/icon/list.svg", "view": "list", "active": True},
            {"label": "Kanban", "icon": "/templates/icon/kanban.svg", "view": "kanban"},
            {"label": "Organigrama", "icon": "/icon/organigrama.svg", "view": "organigrama"},
        ],
        floating_actions_screen="none",
    )


@router.get("/usuarios", response_class=HTMLResponse)
@router.get("/usuarios-sistema", response_class=HTMLResponse)
def usuarios_page(request: Request):
    return _render_empleados_page(request)


@router.get("/inicio/colaboradores", response_class=HTMLResponse)
def inicio_colaboradores_page(request: Request):
    return _render_empleados_page(
        request,
        title="Colaboradores",
        description="Gestiona colaboradores, roles y permisos desde la misma pantalla",
    )
