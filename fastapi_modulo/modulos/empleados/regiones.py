import json
import os
from typing import Dict, List

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import HTMLResponse

router = APIRouter()
APP_ENV_DEFAULT = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
RUNTIME_STORE_DIR = (os.environ.get("RUNTIME_STORE_DIR") or f"fastapi_modulo/runtime_store/{APP_ENV_DEFAULT}").strip()

REGIONES_STORE_PATH = (
    os.environ.get("REGIONES_STORE_PATH")
    or os.path.join(RUNTIME_STORE_DIR, "regiones_store.json")
)
REGIONES_TEMPLATE_PATH = os.path.join("fastapi_modulo", "templates", "modulos", "empleados", "regiones.html")


def _ensure_store_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_regiones_store() -> List[Dict[str, str]]:
    if not os.path.exists(REGIONES_STORE_PATH):
        return []
    try:
        with open(REGIONES_STORE_PATH, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(loaded, list):
        return []
    rows: List[Dict[str, str]] = []
    for item in loaded:
        if not isinstance(item, dict):
            continue
        nombre = str(item.get("nombre") or "").strip()
        codigo = str(item.get("codigo") or "").strip()
        descripcion = str(item.get("descripcion") or "").strip()
        if not nombre and not codigo and not descripcion:
            continue
        rows.append(
            {
                "nombre": nombre,
                "codigo": codigo,
                "descripcion": descripcion,
            }
        )
    return rows


def save_regiones_store(rows: List[Dict[str, str]]) -> None:
    safe_rows: List[Dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        nombre = str(item.get("nombre") or "").strip()
        codigo = str(item.get("codigo") or "").strip()
        descripcion = str(item.get("descripcion") or "").strip()
        if not nombre and not codigo and not descripcion:
            continue
        safe_rows.append(
            {
                "nombre": nombre,
                "codigo": codigo,
                "descripcion": descripcion,
            }
        )
    _ensure_store_parent_dir(REGIONES_STORE_PATH)
    with open(REGIONES_STORE_PATH, "w", encoding="utf-8") as fh:
        json.dump(safe_rows, fh, ensure_ascii=False, indent=2)


def _load_regiones_template() -> str:
    try:
        with open(REGIONES_TEMPLATE_PATH, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return "<p>No se pudo cargar la plantilla de Regiones.</p>"


@router.get("/inicio/regiones", response_class=HTMLResponse)
def inicio_regiones_page(request: Request):
    from fastapi_modulo.main import render_backend_page

    return render_backend_page(
        request,
        title="Regiones",
        description="Registro y visualización de regiones.",
        content=_load_regiones_template(),
        hide_floating_actions=True,
        show_page_header=True,
        view_buttons=[
            {"label": "Form", "icon": "/templates/icon/formulario.svg", "view": "form", "active": True},
            {"label": "Lista", "icon": "/templates/icon/list.svg", "view": "list"},
            {"label": "Kanban", "icon": "/templates/icon/kanban.svg", "view": "kanban"},
        ],
    )


@router.get("/api/inicio/regiones")
def listar_regiones():
    return {"success": True, "data": load_regiones_store()}


@router.post("/api/inicio/regiones")
async def guardar_regiones(data: dict = Body(...)):
    incoming = data.get("data", [])
    if not isinstance(incoming, list):
        raise HTTPException(status_code=400, detail="Formato inválido")
    save_regiones_store(incoming)
    return {"success": True, "data": load_regiones_store()}
