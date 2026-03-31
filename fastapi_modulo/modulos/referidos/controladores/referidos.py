from __future__ import annotations

from pathlib import Path
from typing import Generator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web import render_backend_page_html
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

router = APIRouter()
MODULE_DIR = Path(__file__).resolve().parents[1]
VIEWS_DIR = MODULE_DIR / "vistas"
_jinja_env = Environment(
    loader=FileSystemLoader(str(VIEWS_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
)

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


def _render_referidos_content(**context: object) -> str:
    template_path = VIEWS_DIR / "referidos.html"
    if not template_path.exists():
        return "<p>No se pudo cargar la vista del modulo Referidos.</p>"
    return _jinja_env.get_template("referidos.html").render(**context)


# ─── Pages ──────────────────────────────────────────────────────────────────

@router.get("/referidos", response_class=HTMLResponse)
async def referidos_dashboard(
    request: Request,
    business_slug: Optional[str] = None,
    db=Depends(get_db),
):
    selected_program = None
    if business_slug:
        selected_program = get_program_assignment_by_business_slug(db, business_slug)
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
async def api_create_referente(data: ReferenteCreate, db=Depends(get_db)):
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
):
    return list_referidos(
        db,
        state=state,
        referente_id=referente_id,
        program_assignment_id=program_assignment_id,
        skip=skip,
        limit=limit,
    )


@router.post("/api/referidos/crear", response_model=ReferidoRead)
async def api_create_referido(data: ReferidoCreate, request: Request, db=Depends(get_db)):
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
async def api_list_programas(db=Depends(get_db)):
    return list_program_assignments(db)


@router.post("/api/referidos/programas", response_model=ProgramAssignmentRead)
async def api_create_programa(data: ProgramAssignmentCreate, db=Depends(get_db)):
    return create_program_assignment(db, data)


# ─── API: Embajadores ─────────────────────────────────────────────────────────

@router.get("/api/referidos/embajadores", response_model=List[AmbassadorRead])
async def api_list_embajadores(business_id: Optional[int] = None, db=Depends(get_db)):
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
    stats = get_dashboard_stats(db)
    referidos = list_referidos(db, limit=50)
    referentes = list_referentes(db, limit=200)
    incentivos = list_incentivos(db)
    configuracion = get_configuracion(db)
    return render_backend_page_html(
        request,
        title=f"Referidos {miu_code}",
        description="Portal publico del programa de referidos.",
        content=_render_referidos_content(
            stats=stats,
            referidos=referidos,
            referentes=referentes,
            incentivos=incentivos,
            configuracion=configuracion,
            programas=[],
            selected_program=None,
            selected_business_slug=None,
            referente=referente,
            miu_code=miu_code,
        ),
        show_page_header=False,
        referente=referente,
        miu_code=miu_code,
    )
