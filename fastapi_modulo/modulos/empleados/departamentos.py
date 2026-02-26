import os

# Módulo inicial para endpoints y lógica de departamentos
from fastapi import APIRouter, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import List, Dict, Set, Any
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


def _build_empleados_count_map(rows: List[DepartamentoOrganizacional]) -> Dict[str, int]:
    # Import diferido para evitar ciclo de importación con fastapi_modulo.main.
    from fastapi_modulo.main import Usuario

    db = SessionLocal()
    try:
        all_users = db.query(Usuario).all()
    finally:
        db.close()

    buckets: Dict[str, int] = {}
    for user in all_users:
        dep = str(getattr(user, "departamento", "") or "").strip().lower()
        if not dep:
            continue
        buckets[dep] = buckets.get(dep, 0) + 1

    counts: Dict[str, int] = {}
    for row in rows:
        name_key = str(row.nombre or "").strip().lower()
        code_key = str(row.codigo or "").strip().lower()
        counts[code_key] = buckets.get(name_key, 0)
        if code_key and code_key != name_key:
            counts[code_key] += buckets.get(code_key, 0)
    return counts


def _serialize_departamentos(
    rows: List[DepartamentoOrganizacional],
    count_map: Dict[str, int] | None = None,
) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    count_map = count_map or {}
    for row in rows:
        code_key = str(row.codigo or "").strip().lower()
        data.append(
            {
                "name": str(row.nombre or "").strip(),
                "parent": str(row.padre or "N/A").strip() or "N/A",
                "manager": str(row.responsable or "").strip(),
                "code": str(row.codigo or "").strip(),
                "color": str(row.color or "#1d4ed8").strip() or "#1d4ed8",
                "status": str(row.estado or "Activo").strip() or "Activo",
                "empleados_asignados": int(count_map.get(code_key, 0)),
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
        count_map = _build_empleados_count_map(rows)
        return {"success": True, "data": _serialize_departamentos(rows, count_map)}
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
        # Upsert no destructivo para evitar pérdida masiva si el frontend envía payload parcial.
        for idx, item in enumerate(cleaned_rows, start=1):
            existing = (
                db.query(DepartamentoOrganizacional)
                .filter(DepartamentoOrganizacional.codigo == item["code"])
                .first()
            )
            if existing:
                existing.nombre = item["name"]
                existing.padre = item["parent"]
                existing.responsable = item["manager"]
                existing.color = item["color"]
                existing.estado = item["status"]
                existing.orden = idx
                db.add(existing)
            else:
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
        count_map = _build_empleados_count_map(rows)
        return {"success": True, "data": _serialize_departamentos(rows, count_map)}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando departamentos: {exc}")
    finally:
        db.close()


@router.delete("/api/inicio/departamentos/{code}")
def eliminar_departamento(request: Request, code: str):
    from fastapi_modulo.main import require_admin_or_superadmin

    require_admin_or_superadmin(request)
    _ensure_departamentos_schema()
    target_code = str(code or "").strip()
    if not target_code:
        raise HTTPException(status_code=400, detail="Código inválido")
    db = SessionLocal()
    try:
        row = (
            db.query(DepartamentoOrganizacional)
            .filter(DepartamentoOrganizacional.codigo == target_code)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Departamento no encontrado")
        db.delete(row)
        db.commit()
        rows = (
            db.query(DepartamentoOrganizacional)
            .order_by(DepartamentoOrganizacional.orden.asc(), DepartamentoOrganizacional.id.asc())
            .all()
        )
        count_map = _build_empleados_count_map(rows)
        return {"success": True, "data": _serialize_departamentos(rows, count_map)}
    finally:
        db.close()
