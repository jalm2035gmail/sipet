import os

# Módulo inicial para endpoints y lógica de departamentos
from fastapi import APIRouter, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import List, Dict, Set
from fastapi_modulo.db import SessionLocal, DepartamentoOrganizacional, Base, engine

router = APIRouter()
DEPARTAMENTOS_TEMPLATE_PATH = os.path.join("fastapi_modulo", "modulos", "empleados", "departamentos.html")


def _ensure_departamentos_schema() -> None:
    # Crea la tabla si no existe (producción sin migración previa).
    Base.metadata.create_all(bind=engine, tables=[DepartamentoOrganizacional.__table__], checkfirst=True)


def _render_departamentos_page(request: Request) -> HTMLResponse:
    from fastapi_modulo.main import render_backend_page

    try:
        with open(DEPARTAMENTOS_TEMPLATE_PATH, "r", encoding="utf-8") as fh:
            areas_content = fh.read()
    except OSError:
        areas_content = ""
    return render_backend_page(
        request,
        title="Departamentos",
        description="Administra la estructura de departamentos de la organización",
        content=areas_content,
        hide_floating_actions=True,
        show_page_header=False,
    )


@router.get("/departamentos", response_class=HTMLResponse)
def departamentos_page(request: Request):
    # Redirige a la vista backend oficial con estilos y layout unificados.
    return RedirectResponse(url="/inicio/departamentos", status_code=307)


@router.get("/inicio/departamentos", response_class=HTMLResponse)
def inicio_departamentos_page(request: Request):
    return _render_departamentos_page(request)


@router.get("/areas-organizacionales", response_class=HTMLResponse)
def areas_organizacionales_page(request: Request):
    return RedirectResponse(url="/inicio/departamentos", status_code=307)


def _serialize_departamentos(rows: List[DepartamentoOrganizacional]) -> List[Dict[str, str]]:
    data: List[Dict[str, str]] = []
    for row in rows:
        data.append(
            {
                "name": str(row.nombre or "").strip(),
                "parent": str(row.padre or "N/A").strip() or "N/A",
                "manager": str(row.responsable or "").strip(),
                "code": str(row.codigo or "").strip(),
                "color": str(row.color or "#1d4ed8").strip() or "#1d4ed8",
                "status": str(row.estado or "Activo").strip() or "Activo",
            }
        )
    return data

@router.get("/api/inicio/departamentos")
def listar_departamentos():
    _ensure_departamentos_schema()
    db = SessionLocal()
    try:
        rows = (
            db.query(DepartamentoOrganizacional)
            .order_by(DepartamentoOrganizacional.orden.asc(), DepartamentoOrganizacional.id.asc())
            .all()
        )
        return {"success": True, "data": _serialize_departamentos(rows)}
    finally:
        db.close()

@router.post("/api/inicio/departamentos")
async def guardar_departamentos(request: Request, data: dict = Body(...)):
    from fastapi_modulo.main import require_admin_or_superadmin

    require_admin_or_superadmin(request)
    incoming = data.get("data", [])
    if not isinstance(incoming, list):
        raise HTTPException(status_code=400, detail="Formato inválido")

    cleaned_rows: List[Dict[str, str]] = []
    used_codes: Set[str] = set()
    for item in incoming:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        code = str(item.get("code") or "").strip()
        parent = str(item.get("parent") or "N/A").strip() or "N/A"
        manager = str(item.get("manager") or "").strip()
        color = str(item.get("color") or "#1d4ed8").strip() or "#1d4ed8"
        status = "Activo"
        if not name or not code:
            continue
        code_key = code.lower()
        if code_key in used_codes:
            continue
        used_codes.add(code_key)
        cleaned_rows.append(
            {
                "name": name,
                "code": code,
                "parent": parent,
                "manager": manager,
                "color": color,
                "status": status,
            }
        )

    if not cleaned_rows:
        raise HTTPException(status_code=400, detail="No hay departamentos válidos para guardar")

    _ensure_departamentos_schema()
    db = SessionLocal()
    try:
        db.query(DepartamentoOrganizacional).delete()
        for idx, item in enumerate(cleaned_rows, start=1):
            db.add(
                DepartamentoOrganizacional(
                    nombre=item["name"],
                    codigo=item["code"],
                    padre=item["parent"],
                    responsable=item["manager"],
                    color=item["color"],
                    estado=item["status"],
                    orden=idx,
                )
            )
        db.commit()
        rows = (
            db.query(DepartamentoOrganizacional)
            .order_by(DepartamentoOrganizacional.orden.asc(), DepartamentoOrganizacional.id.asc())
            .all()
        )
        return {"success": True, "data": _serialize_departamentos(rows)}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando departamentos: {exc}")
    finally:
        db.close()
