from __future__ import annotations

from pathlib import Path
from typing import Generator, List, Optional

import csv
import io

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos.referidos.modelos.db_models import ensure_referidos_schema
from fastapi_modulo.modulos.referidos.modelos.schemas import (
    AmbassadorCreate,
    AmbassadorRead,
    AmbassadorRequestCreate,
    AmbassadorRequestRead,
    ConfiguracionRead,
    ConfiguracionUpdate,
    ConvertirReferidoInput,
    IncentivoCreate,
    IncentivoRead,
    ProgramAssignmentCreate,
    ProgramAssignmentRead,
    RechazarReferidoInput,
    ReferenteCreate,
    ReferenteRead,
    ReferidoCreate,
    ReferidoRead,
    ReferidoUpdate,
)
from fastapi_modulo.modulos.referidos.modelos.store import (
    approve_ambassador_request,
    cleanup_stale_referidos,
    convert_referido,
    create_ambassador,
    create_ambassador_request,
    create_incentivo,
    create_program_assignment,
    create_referente,
    create_referido,
    get_configuracion,
    get_dashboard_stats,
    get_incentivo,
    get_program_assignment_by_business_slug,
    get_referente,
    get_referente_by_miu,
    list_ambassador_requests,
    list_ambassadors,
    list_incentivos,
    list_program_assignments,
    list_referentes,
    list_referidos,
    pay_referido,
    qualify_referido,
    reject_ambassador_request,
    reject_referido,
    update_referido,
    upsert_configuracion,
)
from fastapi_modulo.modulos_sipet.web import render_backend_page_html
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import find_user_by_login, get_session_local
from fastapi_modulo.modulos_sipet.web.servicios.session_service import read_session_cookie

router = APIRouter()
MODULE_DIR = Path(__file__).resolve().parents[1]
VIEWS_DIR = MODULE_DIR / "vistas"
_jinja_env = Environment(
    loader=FileSystemLoader(str(VIEWS_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
)


def get_current_user(request: Request, auth_session: str = Cookie(None)):
    if not auth_session:
        raise HTTPException(status_code=401, detail="No autenticado")
    session_data = read_session_cookie(auth_session)
    if not session_data or not session_data.get("username"):
        raise HTTPException(status_code=401, detail="Sesión inválida")
    db = get_session_local()()
    try:
        user = find_user_by_login(db, session_data["username"])
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return user
    finally:
        db.close()


try:
    ensure_referidos_schema()
except Exception as _e:
    print(f"[referidos] schema init warning: {_e}")


def get_db() -> Generator[object, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        close = getattr(db, "close", None)
        if callable(close):
            close()

# Consultar blacklist (solo admin)
@router.get("/api/referidos/blacklist")
async def api_list_blacklist(db=Depends(get_db), current_user=Depends(get_current_user)):
    from fastapi_modulo.modulos.referidos.modelos.db_models import BlacklistReferido
    from fastapi_modulo.modulos.referidos.modelos.store import user_has_business_access
    if not user_has_business_access(db, current_user.id, None, roles=["admin_global"]):
        raise HTTPException(status_code=403, detail="Sin permisos para ver blacklist")
    res = db.query(BlacklistReferido).order_by(BlacklistReferido.created_at.desc()).all()
    return [
        {"id": b.id, "phone": b.phone, "email": b.email, "motivo": b.motivo, "created_at": b.created_at, "created_by": b.created_by}
        for b in res
    ]

# Consultar revisión manual (solo admin)
@router.get("/api/referidos/revision-manual")
async def api_list_revision_manual(db=Depends(get_db), current_user=Depends(get_current_user)):
    from fastapi_modulo.modulos.referidos.modelos.db_models import RevisionManual
    from fastapi_modulo.modulos.referidos.modelos.store import user_has_business_access
    if not user_has_business_access(db, current_user.id, None, roles=["admin_global"]):
        raise HTTPException(status_code=403, detail="Sin permisos para ver revisión manual")
    res = db.query(RevisionManual).order_by(RevisionManual.created_at.desc()).all()
    return [
        {"id": r.id, "referido_id": r.referido_id, "motivo": r.motivo, "estado": r.estado, "created_at": r.created_at, "reviewed_by": r.reviewed_by}
        for r in res
    ]
# ─── API: Reportes Fase 7 ───────────────────────────────────────────────────
from fastapi_modulo.modulos.referidos.modelos.store import (
    add_to_blacklist,
    add_to_revision_manual,
    get_kpis_por_negocio,
    get_kpis_por_embajador,
    get_conversion_por_canal,
)

@router.get("/api/referidos/reportes/kpis-negocio")
async def api_kpis_negocio(db=Depends(get_db), current_user=Depends(get_current_user)):
    return get_kpis_por_negocio(db)

@router.get("/api/referidos/reportes/kpis-embajador")
async def api_kpis_embajador(business_id: Optional[int] = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    return get_kpis_por_embajador(db, business_id=business_id)

@router.get("/api/referidos/reportes/conversion-canal")
async def api_conversion_canal(program_assignment_id: Optional[int] = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    return get_conversion_por_canal(db, program_assignment_id=program_assignment_id)

@router.get("/api/referidos/reportes/incentivos")
async def api_incentivos_reporte(db=Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import func as sqlfunc
    from fastapi_modulo.modulos.referidos.modelos.db_models import RefReferido
    pendientes = float(
        db.query(sqlfunc.coalesce(sqlfunc.sum(RefReferido.incentive_amount), 0))
        .filter(RefReferido.state == "converted")
        .scalar() or 0
    )
    pagados = float(
        db.query(sqlfunc.coalesce(sqlfunc.sum(RefReferido.incentive_amount), 0))
        .filter(RefReferido.state == "paid")
        .scalar() or 0
    )
    return {"incentivos_pendientes": pendientes, "incentivos_pagados": pagados, "total": pendientes + pagados}


@router.get("/api/referidos/exportar/csv")
async def api_exportar_csv(db=Depends(get_db), current_user=Depends(get_current_user)):
    referidos = list_referidos(db, limit=10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Código", "Prospecto", "Email", "Teléfono", "MIU", "Estado", "Conversión Q",
                     "Incentivo Q", "Fraude", "Score", "Fecha"])
    for r in referidos:
        writer.writerow([
            r.cvr_code, r.nombre_prospecto, r.email or "", r.phone or "",
            r.referente_miu or "", r.state.name if hasattr(r.state, "name") else r.state,
            float(r.conversion_amount or 0), float(r.incentive_amount or 0),
            "Sí" if r.fraud_flag else "No", r.fraud_score or 0,
            r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=referidos.csv"},
    )


@router.get("/api/referidos/exportar/excel")
async def api_exportar_excel(db=Depends(get_db), current_user=Depends(get_current_user)):
    import openpyxl
    referidos = list_referidos(db, limit=10000)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Referidos"
    headers = ["Código", "Prospecto", "Email", "Teléfono", "MIU", "Estado",
               "Conversión Q", "Incentivo Q", "Fraude", "Score", "Fecha"]
    ws.append(headers)
    for r in referidos:
        ws.append([
            r.cvr_code, r.nombre_prospecto, r.email or "", r.phone or "",
            r.referente_miu or "", r.state.name if hasattr(r.state, "name") else r.state,
            float(r.conversion_amount or 0), float(r.incentive_amount or 0),
            "Sí" if r.fraud_flag else "No", r.fraud_score or 0,
            r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
        ])
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=referidos.xlsx"},
    )


# ─── API: Alertas automáticas ───────────────────────────────────────────────

@router.get("/api/referidos/alertas")
async def api_alertas(db=Depends(get_db), current_user=Depends(get_current_user)):
    """
    Devuelve alertas activas:
    - Referidos con fraud_score >= 70 no enviados a revisión manual
    - Referidos convertidos sin incentivo (incentive_amount = 0)
    - Incentivos pendientes que llevan más de 30 días sin pagarse
    - Embajadores con más de 20 referidos sin convertir
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func as sqlfunc
    from fastapi_modulo.modulos.referidos.modelos.db_models import (
        RefReferido, RefRevisionManual, RefBrandAmbassador,
    )

    alertas = []

    # 1. Referidos de alto fraude sin revisión
    ya_en_revision = {
        row.referido_id
        for row in db.query(RefRevisionManual.referido_id).all()
    }
    alto_fraude = (
        db.query(RefReferido)
        .filter(RefReferido.fraud_score >= 70)
        .all()
    )
    sin_revision = [r for r in alto_fraude if r.id not in ya_en_revision]
    if sin_revision:
        alertas.append({
            "tipo": "fraude_sin_revision",
            "nivel": "alto",
            "mensaje": f"{len(sin_revision)} referido(s) con score de fraude ≥70 sin revisión manual",
            "ids": [r.id for r in sin_revision],
        })

    # 2. Referidos convertidos sin incentivo asignado
    sin_incentivo = (
        db.query(RefReferido)
        .filter(
            RefReferido.state == "converted",
            (RefReferido.incentive_amount == None) | (RefReferido.incentive_amount == 0),
        )
        .all()
    )
    if sin_incentivo:
        alertas.append({
            "tipo": "convertido_sin_incentivo",
            "nivel": "medio",
            "mensaje": f"{len(sin_incentivo)} referido(s) convertido(s) con incentivo pendiente de asignar",
            "ids": [r.id for r in sin_incentivo],
        })

    # 3. Incentivos sin pagar por más de 30 días
    hace_30 = datetime.utcnow() - timedelta(days=30)
    incentivos_vencidos = (
        db.query(RefReferido)
        .filter(
            RefReferido.state == "converted",
            RefReferido.incentive_amount > 0,
            RefReferido.updated_at < hace_30,
        )
        .all()
    )
    if incentivos_vencidos:
        alertas.append({
            "tipo": "incentivo_vencido",
            "nivel": "alto",
            "mensaje": f"{len(incentivos_vencidos)} incentivo(s) sin pagar con más de 30 días",
            "ids": [r.id for r in incentivos_vencidos],
        })

    # 4. Embajadores con muchos referidos sin convertir
    embajadores_inactivos = (
        db.query(
            RefReferido.ambassador_id,
            sqlfunc.count(RefReferido.id).label("total"),
        )
        .filter(RefReferido.state.in_(["pending", "contacted"]))
        .group_by(RefReferido.ambassador_id)
        .having(sqlfunc.count(RefReferido.id) >= 20)
        .all()
    )
    if embajadores_inactivos:
        alertas.append({
            "tipo": "embajador_sin_conversion",
            "nivel": "bajo",
            "mensaje": f"{len(embajadores_inactivos)} embajador(es) con 20+ referidos sin convertir",
            "items": [{"ambassador_id": e.ambassador_id, "total": e.total} for e in embajadores_inactivos],
        })

    return {"total_alertas": len(alertas), "alertas": alertas}


# ─── API: Integración CRM / ventas ──────────────────────────────────────────

@router.get("/api/referidos/crm/export")
async def api_crm_export(
    estado: str = None,
    business_id: int = None,
    limit: int = 500,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Endpoint para consumo externo por CRM/sistema de ventas.
    Devuelve referidos convertidos (o filtrado por estado) con datos de contacto
    y contexto de negocio para seguimiento comercial.
    """
    from fastapi_modulo.modulos.referidos.modelos.db_models import RefReferido, RefProgramAssignment

    query = db.query(RefReferido)
    if estado:
        query = query.filter(RefReferido.state == estado)
    else:
        query = query.filter(RefReferido.state.in_(["converted", "contacted", "scheduled"]))
    if business_id:
        query = query.join(
            RefProgramAssignment,
            RefReferido.program_assignment_id == RefProgramAssignment.id,
        ).filter(RefProgramAssignment.business_id == business_id)
    referidos = query.order_by(RefReferido.created_at.desc()).limit(limit).all()

    return {
        "total": len(referidos),
        "referidos": [
            {
                "id": r.id,
                "codigo": r.cvr_code,
                "prospecto": r.nombre_prospecto,
                "email": r.email,
                "telefono": r.phone,
                "miu": r.referente_miu,
                "estado": r.state.name if hasattr(r.state, "name") else r.state,
                "conversion_amount": float(r.conversion_amount or 0),
                "incentivo": float(r.incentive_amount or 0),
                "fraude_score": r.fraud_score or 0,
                "fraud_flag": r.fraud_flag or False,
                "program_assignment_id": r.program_assignment_id,
                "ambassador_id": r.ambassador_id,
                "fecha_creacion": r.created_at.isoformat() if r.created_at else None,
                "fecha_actualizacion": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in referidos
        ],
    }


# ─── API: Blacklist y revisión manual ───────────────────────────────────────

@router.post("/api/referidos/blacklist")
async def api_add_blacklist(phone: str = None, email: str = None, motivo: str = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    # Solo admin puede agregar
    from fastapi_modulo.modulos.referidos.modelos.store import user_has_business_access
    if not user_has_business_access(db, current_user.id, None, roles=["admin_global"]):
        raise HTTPException(status_code=403, detail="Sin permisos para blacklist")
    obj = add_to_blacklist(db, phone=phone, email=email, motivo=motivo, created_by=current_user.id)
    return {"id": obj.id, "phone": obj.phone, "email": obj.email, "motivo": obj.motivo}

@router.post("/api/referidos/revision-manual")
async def api_add_revision_manual(referido_id: int, motivo: str = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    # Solo admin puede agregar
    from fastapi_modulo.modulos.referidos.modelos.store import user_has_business_access
    if not user_has_business_access(db, current_user.id, None, roles=["admin_global"]):
        raise HTTPException(status_code=403, detail="Sin permisos para revisión manual")
    obj = add_to_revision_manual(db, referido_id=referido_id, motivo=motivo)
    return {"id": obj.id, "referido_id": obj.referido_id, "motivo": obj.motivo}
# ─── API: Cambiar estado de embajador ───────────────────────────────────────

from fastapi_modulo.modulos.referidos.modelos.db_models import AmbassadorState

@router.post("/api/referidos/embajadores/{ambassador_id}/estado", response_model=AmbassadorRead)
async def api_cambiar_estado_embajador(ambassador_id: int, nuevo_estado: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    # Solo admin_global o admin_negocio pueden cambiar estado
    from fastapi_modulo.modulos.referidos.modelos.store import user_has_business_access
    obj = db.query(RefBrandAmbassador).filter_by(id=ambassador_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Embajador no encontrado")
    # Validar acceso
    if not user_has_business_access(db, current_user.id, obj.business_id, roles=["admin_global", "admin_negocio"]):
        raise HTTPException(status_code=403, detail="Sin permisos para cambiar estado")
    # Validar estado
    if nuevo_estado not in AmbassadorState.__members__:
        raise HTTPException(status_code=400, detail="Estado inválido")
    obj.state = AmbassadorState[nuevo_estado]
    db.commit()
    db.refresh(obj)
    return obj
@router.get("/embajador/dashboard/{code}", response_class=HTMLResponse)
async def embajador_dashboard(code: str, request: Request, db=Depends(get_db)):
    from fastapi_modulo.modulos.referidos.modelos.db_models import RefBrandAmbassador
    embajador = db.query(RefBrandAmbassador).filter_by(code=code).first()
    if not embajador:
        raise HTTPException(status_code=404, detail="Embajador no encontrado")
    # Métricas básicas
    total_referidos = len(embajador.referidos)
    convertidos = len([r for r in embajador.referidos if r.state.name == "converted"])
    incentivos = sum([float(r.incentive_amount or 0) for r in embajador.referidos if r.incentive_amount])
    # Ranking global y por negocio
    all_ambassadors = db.query(RefBrandAmbassador).all()
    all_ambassadors_sorted = sorted(
        all_ambassadors,
        key=lambda a: (
            -len(a.referidos),
            -sum([float(r.incentive_amount or 0) for r in a.referidos if r.incentive_amount])
        )
    )
    global_rank = next((i+1 for i, a in enumerate(all_ambassadors_sorted) if a.id == embajador.id), None)
    # Ranking por negocio
    business_ambassadors = db.query(RefBrandAmbassador).filter_by(business_id=embajador.business_id).all()
    business_ambassadors_sorted = sorted(
        business_ambassadors,
        key=lambda a: (
            -len(a.referidos),
            -sum([float(r.incentive_amount or 0) for r in a.referidos if r.incentive_amount])
        )
    )
    business_rank = next((i+1 for i, a in enumerate(business_ambassadors_sorted) if a.id == embajador.id), None)
    # Metas: cantidad y monto
    from fastapi_modulo.modulos.referidos.modelos.db_models import RefConfiguracion, RefProgramAssignment
    program = db.query(RefProgramAssignment).filter_by(id=embajador.business_id).first()
    meta_cantidad = None
    meta_monto = None
    if program:
        config = db.query(RefConfiguracion).filter_by(scenario_type=program.business_type).first()
        if config:
            meta_cantidad = getattr(config, "kpi_target", None)
            meta_monto = getattr(config, "max_amount", None)
    # Render
    template_path = VIEWS_DIR / "dashboard_embajador.html"
    if not template_path.exists():
        return "<p>No se pudo cargar el dashboard del embajador.</p>"
    html = _jinja_env.get_template("dashboard_embajador.html").render(
        embajador=embajador,
        total_referidos=total_referidos,
        convertidos=convertidos,
        incentivos=incentivos,
        global_rank=global_rank,
        business_rank=business_rank,
        meta_cantidad=meta_cantidad,
        meta_monto=meta_monto,
    )
    return render_backend_page_html(
        request,
        title=f"Dashboard de {embajador.name}",
        description="Panel de métricas del embajador.",
        content=html,
        show_page_header=False,
    )
def _render_referidos_content(**context: object) -> str:
    template_path = VIEWS_DIR / "referidos.html"
    if not template_path.exists():
        return "<p>No se pudo cargar la vista del modulo Referidos.</p>"
    return _jinja_env.get_template("referidos.html").render(**context)


# ─── Pages ──────────────────────────────────────────────────────────────────

from fastapi_modulo.modulos.referidos.modelos.store import user_has_business_access

@router.get("/referidos", response_class=HTMLResponse)
async def referidos_dashboard(
    request: Request,
    business_slug: Optional[str] = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    selected_program = None
    if business_slug:
        selected_program = get_program_assignment_by_business_slug(db, business_slug)
        if selected_program and not user_has_business_access(db, current_user.id, selected_program.id):
            raise HTTPException(status_code=403, detail="Acceso denegado a este negocio")
    stats = get_dashboard_stats(db)
    referidos = list_referidos(
        db,
        limit=50,
        program_assignment_id=getattr(selected_program, "id", None),
    )
    referentes = list_referentes(db, limit=200)
    incentivos = list_incentivos(db)
    configuracion = get_configuracion(db)
    programas = list_program_assignments(db)
    return render_backend_page_html(
        request,
        title="Referidos",
        description="Programa integral de referidos, incentivos y embajadores.",
        content=_render_referidos_content(
            stats=stats,
            referidos=referidos,
            referentes=referentes,
            incentivos=incentivos,
            configuracion=configuracion,
            programas=programas,
            selected_program=selected_program,
            selected_business_slug=business_slug,
        ),
        show_page_header=False,
    )


# ─── API: Referentes ─────────────────────────────────────────────────────────

@router.get("/api/referidos/referentes", response_model=List[ReferenteRead])
async def api_list_referentes(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    return list_referentes(db, skip=skip, limit=limit)


@router.post("/api/referidos/referentes", response_model=ReferenteRead)
async def api_create_referente(data: ReferenteCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    # current_user disponible para lógica de permisos
    return create_referente(db, data)


@router.get("/api/referidos/referentes/{referente_id}", response_model=ReferenteRead)
async def api_get_referente(referente_id: int, db=Depends(get_db)):
    obj = get_referente(db, referente_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Referente no encontrado")
    return obj


@router.get("/api/referidos/referentes/miu/{miu_code}", response_model=ReferenteRead)
async def api_get_referente_by_miu(miu_code: str, db=Depends(get_db)):
    obj = get_referente_by_miu(db, miu_code)
    if not obj:
        raise HTTPException(status_code=404, detail="MIU no encontrado")
    return obj


# ─── API: Referidos ───────────────────────────────────────────────────────────

@router.get("/api/referidos/lista", response_model=List[ReferidoRead])
async def api_list_referidos(
    state: Optional[str] = None,
    referente_id: Optional[int] = None,
    program_assignment_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    if program_assignment_id:
        from fastapi_modulo.modulos.referidos.modelos.store import user_has_business_access
        if not user_has_business_access(db, current_user.id, program_assignment_id):
            raise HTTPException(status_code=403, detail="Acceso denegado a este negocio")
    return list_referidos(
        db,
        state=state,
        referente_id=referente_id,
        program_assignment_id=program_assignment_id,
        skip=skip,
        limit=limit,
    )


@router.post("/api/referidos/crear", response_model=ReferidoRead)
async def api_create_referido(data: ReferidoCreate, request: Request, db=Depends(get_db), current_user=Depends(get_current_user)):
    # current_user disponible para lógica de permisos
    return create_referido(db, data)


@router.patch("/api/referidos/{referido_id}", response_model=ReferidoRead)
async def api_update_referido(referido_id: int, data: ReferidoUpdate, db=Depends(get_db)):
    obj = update_referido(db, referido_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Referido no encontrado")
    return obj


@router.post("/api/referidos/{referido_id}/cualificar", response_model=ReferidoRead)
async def api_qualify_referido(referido_id: int, db=Depends(get_db)):
    obj = qualify_referido(db, referido_id)
    if not obj:
        raise HTTPException(status_code=400, detail="No se puede cualificar este referido")
    return obj


@router.post("/api/referidos/{referido_id}/convertir", response_model=ReferidoRead)
async def api_convert_referido(referido_id: int, data: ConvertirReferidoInput, db=Depends(get_db)):
    obj = convert_referido(db, referido_id, data)
    if not obj:
        raise HTTPException(status_code=400, detail="No se puede convertir este referido")
    return obj


@router.post("/api/referidos/{referido_id}/pagar", response_model=ReferidoRead)
async def api_pay_referido(referido_id: int, db=Depends(get_db)):
    obj = pay_referido(db, referido_id)
    if not obj:
        raise HTTPException(status_code=400, detail="No se puede liquidar este referido")
    return obj


@router.post("/api/referidos/{referido_id}/rechazar", response_model=ReferidoRead)
async def api_reject_referido(referido_id: int, data: RechazarReferidoInput, db=Depends(get_db)):
    obj = reject_referido(db, referido_id, data)
    if not obj:
        raise HTTPException(status_code=400, detail="No se puede rechazar este referido")
    return obj


@router.post("/api/referidos/cron/limpiar-inactivos")
async def api_cleanup_stale(days: int = 90, db=Depends(get_db)):
    count = cleanup_stale_referidos(db, days=days)
    return {"rechazados": count}


# ─── API: Dashboard ───────────────────────────────────────────────────────────

@router.get("/api/referidos/stats")
async def api_stats(db=Depends(get_db)):
    return get_dashboard_stats(db)


# ─── API: Incentivos ─────────────────────────────────────────────────────────

@router.get("/api/referidos/incentivos", response_model=List[IncentivoRead])
async def api_list_incentivos(active_only: bool = True, db=Depends(get_db)):
    return list_incentivos(db, active_only=active_only)


@router.post("/api/referidos/incentivos", response_model=IncentivoRead)
async def api_create_incentivo(data: IncentivoCreate, db=Depends(get_db)):
    return create_incentivo(db, data)


# ─── API: Configuracion ───────────────────────────────────────────────────────

@router.get("/api/referidos/configuracion", response_model=ConfiguracionRead)
async def api_get_configuracion(db=Depends(get_db)):
    cfg = get_configuracion(db)
    if not cfg:
        raise HTTPException(status_code=404, detail="Sin configuración activa")
    return cfg


@router.put("/api/referidos/configuracion", response_model=ConfiguracionRead)
async def api_update_configuracion(data: ConfiguracionUpdate, db=Depends(get_db)):
    return upsert_configuracion(db, data)


# ─── API: Program Assignments ─────────────────────────────────────────────────

@router.get("/api/referidos/programas", response_model=List[ProgramAssignmentRead])
async def api_list_programas(db=Depends(get_db), current_user=Depends(get_current_user)):
    # Opcional: filtrar programas según acceso del usuario
    # Ejemplo: solo retornar programas donde user_has_business_access es True
    from fastapi_modulo.modulos.referidos.modelos.db_models import RefProgramAssignment
    from fastapi_modulo.modulos.referidos.modelos.store import user_has_business_access
    programas = db.query(RefProgramAssignment).all()
    programas_filtrados = [p for p in programas if user_has_business_access(db, current_user.id, p.id)]
    return programas_filtrados


@router.post("/api/referidos/programas", response_model=ProgramAssignmentRead)
async def api_create_programa(data: ProgramAssignmentCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    # current_user disponible para lógica de permisos
    return create_program_assignment(db, data)


# ─── API: Embajadores ─────────────────────────────────────────────────────────

@router.get("/api/referidos/embajadores", response_model=List[AmbassadorRead])
async def api_list_embajadores(business_id: Optional[int] = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    if business_id:
        from fastapi_modulo.modulos.referidos.modelos.store import user_has_business_access
        if not user_has_business_access(db, current_user.id, business_id):
            raise HTTPException(status_code=403, detail="Acceso denegado a este negocio")
    return list_ambassadors(db, business_id=business_id)


@router.post("/api/referidos/embajadores", response_model=AmbassadorRead)
async def api_create_embajador(data: AmbassadorCreate, db=Depends(get_db)):
    return create_ambassador(db, data)


# ─── API: Ambassador Requests ─────────────────────────────────────────────────

@router.get("/api/referidos/solicitudes-embajador", response_model=List[AmbassadorRequestRead])
async def api_list_ambassador_requests(state: Optional[str] = None, db=Depends(get_db)):
    return list_ambassador_requests(db, state=state)


@router.post("/api/referidos/solicitudes-embajador", response_model=AmbassadorRequestRead)
async def api_create_ambassador_request(data: AmbassadorRequestCreate, db=Depends(get_db)):
    return create_ambassador_request(db, data)


@router.post("/api/referidos/solicitudes-embajador/{request_id}/aprobar", response_model=AmbassadorRequestRead)
async def api_approve_ambassador_request(request_id: int, db=Depends(get_db)):
    obj = approve_ambassador_request(db, request_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return obj


@router.post("/api/referidos/solicitudes-embajador/{request_id}/rechazar", response_model=AmbassadorRequestRead)
async def api_reject_ambassador_request_ep(request_id: int, db=Depends(get_db)):
    obj = reject_ambassador_request(db, request_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return obj


# ─── Portal público: landing page por MIU ─────────────────────────────────────

@router.get("/referral/{miu_code}", response_class=HTMLResponse)
async def referral_landing(miu_code: str, request: Request, db=Depends(get_db)):
    referente = get_referente_by_miu(db, miu_code)
    if not referente:
        raise HTTPException(status_code=404, detail="MIU no encontrado")
    # Solo mostrar referidos de este referente
    referidos = list_referidos(db, referente_id=referente.id, limit=50)
    # No mostrar dashboard global ni lista de referentes ni programas
    incentivos = list_incentivos(db)
    configuracion = get_configuracion(db)
    return render_backend_page_html(
        request,
        title=f"Referidos {miu_code}",
        description="Portal público del programa de referidos.",
        content=_render_referidos_content(
            stats=None,
            referidos=referidos,
            referentes=[referente],
            incentivos=incentivos,
            configuracion=configuracion,
            programas=[],
            selected_program=None,
            selected_business_slug=None,
        ),
        show_page_header=False,
    )
