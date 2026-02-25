# Módulo inicial para endpoints y lógica de departamentos
from fastapi import APIRouter, Request, Body, HTTPException
from fastapi.responses import HTMLResponse
from typing import List, Dict, Set
from fastapi_modulo.db import SessionLocal, DepartamentoOrganizacional

router = APIRouter()

@router.get("/departamentos", response_class=HTMLResponse)
def departamentos_page(request: Request):
    # Renderizar la plantilla departamentos.html
    return request.app.state.templates.TemplateResponse(
        "modulos/empleados/departamentos.html",
        {"request": request}
    )

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
async def guardar_departamentos(data: dict = Body(...)):
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
        status = str(item.get("status") or "Activo").strip() or "Activo"
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
    finally:
        db.close()