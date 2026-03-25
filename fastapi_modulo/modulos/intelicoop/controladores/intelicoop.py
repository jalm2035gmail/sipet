from __future__ import annotations

import csv
import io
import os
import zipfile
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy import text
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import SQLAlchemyError
from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import (
    read_text_file,
    render_backend_page_html,
    require_app_access,
    text_asset_response,
)

from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_models import (
    BatchExecuteInput,
    CampaniaCreate,
    ContactoCampaniaCreate,
    CuentaCreate,
    CreditoCreate,
    FoundationMaterializeInput,
    HistorialPagoCreate,
    ProspectoCreate,
    SeguimientoCampaniaCreate,
    SocioCreate,
    ScoringEvaluateInput,
    TransaccionCreate,
)
from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_db_models import IntelicoopCredito, IntelicoopSocio
from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_store import (
    create_campana,
    create_contacto_campania,
    create_cuenta,
    create_credito,
    create_historial_pago,
    create_prospecto,
    create_seguimiento_campania,
    create_socio,
    create_transaccion,
    get_basic_catalogs,
    get_ahorros_resumen,
    get_credito,
    get_credito_detail,
    list_campanas,
    list_contactos_campania,
    list_cuentas,
    list_creditos,
    list_historial_pagos,
    list_prospectos,
    list_seguimientos_campania,
    list_socios,
    list_transacciones,
)
from fastapi_modulo.modulos.intelicoop.services.analytics_service import (
    get_cohortes_service,
    get_dashboard_resumen_service,
    get_descriptive_analytics_service,
    get_pattern_discovery_summary_service,
    get_tendencias_service,
)
from fastapi_modulo.modulos.intelicoop.services.feature_service import (
    get_foundation_overview_service,
    materialize_foundation_cut_service,
)
from fastapi_modulo.modulos.intelicoop.services.governance_service import (
    get_batch_overview_service,
    get_governance_overview_service,
    list_batch_alerts_service,
    list_batch_runs_service,
    run_batch_job_service,
    run_due_batch_jobs_service,
    run_governance_refresh_service,
)
from fastapi_modulo.modulos.intelicoop.services.scoring_service import (
    evaluate_and_create_scoring_service,
    get_scoring_explainability_service,
    get_scoring_summary_service,
    get_scoring_trace_service,
)
from fastapi_modulo.modulos.intelicoop.services.segmentation_service import (
    get_segmentation_propensity_summary_service,
)

def require_intelicoop_access(request: Request) -> None:
    require_app_access(request, "Intelicoop", "Acceso restringido a Intelicoop")


router = APIRouter(dependencies=[Depends(require_intelicoop_access)])
INTELICOOP_TEMPLATE_PATH = os.path.join("fastapi_modulo", "modulos", "intelicoop", "vistas", "intelicoop.html")
INTELICOOP_JS_PATH = os.path.join("fastapi_modulo", "modulos", "intelicoop", "static", "js", "intelicoop.js")
_SOCIOS_IMPORT_TEMPLATE = """nombre,email,telefono,direccion,segmento,fecha_nacimiento,genero,estado_civil,nivel_educativo,ocupacion,sector_economico,ubicacion_estado,ubicacion_municipio,tipo_socio
Ana Perez,ana@example.com,555-0101,Zona 1,hormiga,1990-03-20,femenino,casada,universitario,contadora,servicios,Guatemala,Guatemala,individual
Carlos Ruiz,carlos@example.com,555-0202,Zona 4,gran_ahorrador,1988-07-11,masculino,soltero,diversificado,comerciante,comercio,Sacatepequez,Antigua,empresarial
Maria Lopez,maria@example.com,555-0303,Zona 10,inactivo,1995-11-02,femenino,soltera,bachillerato,asesora,ventas,Guatemala,Mixco,individual
"""
_CREDITOS_IMPORT_TEMPLATE = """socio_id,socio_email,monto,numero_abonos,periodicidad,ingreso_mensual,deuda_actual,antiguedad_meses,tasa,estado,dias_mora_actual,max_dias_mora,num_reestructuras,fecha_desembolso,fecha_vencimiento
1,,25000,24,mensual,18000,3500,36,18.5,solicitado,,,,,
2,,12000,24,quincenal,9500,1800,18,,vigente,3,15,1,2026-03-23,2027-03-23
3,,8000,10,mensual,7200,950,14,24.0,rechazado,,,,,
,ana@example.com,15000,18,mensual,12500,2200,20,19.75,solicitado,0,7,0,2026-03-23,
,carlos@example.com,42000,72,quincenal,31000,7600,60,16.25,reestructurado,5,45,2,,2029-03-23
,maria@example.com,6000,6,mensual,6800,400,9,,rechazado,,,,,
"""
_CUENTAS_IMPORT_TEMPLATE = """socio_id,socio_email,tipo,saldo
1,,ahorro,12500
,ana@example.com,aportacion,3500
,carlos@example.com,ahorro,9800
"""
_TRANSACCIONES_IMPORT_TEMPLATE = """cuenta_id,monto,tipo,canal
1,500,deposito,ventanilla
1,125,retiro,app
2,900,deposito,web
"""
_CAMPANAS_IMPORT_TEMPLATE = """nombre,tipo,fecha_inicio,fecha_fin,estado
Campana Primavera,Colocacion,2026-03-01T00:00:00,2026-03-31T00:00:00,activa
Recuperacion Abril,Recuperacion,2026-04-01T00:00:00,2026-04-30T00:00:00,borrador
"""
_PROSPECTOS_IMPORT_TEMPLATE = """nombre,telefono,direccion,fuente,score_propension
Luis Soto,555-0404,Zona 7,referido,0.74
Elena Cruz,555-0505,Villa Nueva,web,0.61
"""
_CONTACTOS_IMPORT_TEMPLATE = """campania_id,campania_nombre,socio_id,socio_email,ejecutivo_id,canal,estado_contacto
1,,1,,ejecutivo_general,telefono,pendiente
,Campana Primavera,,ana@example.com,ejecutivo_general,whatsapp,contactado
"""
_SEGUIMIENTOS_IMPORT_TEMPLATE = """campania_id,campania_nombre,socio_id,socio_email,lista,etapa,conversion,monto_colocado
1,,1,,general,contactado,0,0
,Campana Primavera,,ana@example.com,preferente,convertido,1,12500
"""
_PAGOS_IMPORT_TEMPLATE = """credito_id,monto,pago_puntual,dias_atraso
1,1200,1,0
2,980,0,4
"""
_IMPORT_TEMPLATES = {
    "socios": ("intelicoop_socios_plantilla.csv", _SOCIOS_IMPORT_TEMPLATE),
    "creditos": ("intelicoop_creditos_plantilla.csv", _CREDITOS_IMPORT_TEMPLATE),
    "cuentas": ("intelicoop_cuentas_plantilla.csv", _CUENTAS_IMPORT_TEMPLATE),
    "transacciones": ("intelicoop_transacciones_plantilla.csv", _TRANSACCIONES_IMPORT_TEMPLATE),
    "campanas": ("intelicoop_campanas_plantilla.csv", _CAMPANAS_IMPORT_TEMPLATE),
    "prospectos": ("intelicoop_prospectos_plantilla.csv", _PROSPECTOS_IMPORT_TEMPLATE),
    "contactos": ("intelicoop_contactos_plantilla.csv", _CONTACTOS_IMPORT_TEMPLATE),
    "seguimientos": ("intelicoop_seguimientos_plantilla.csv", _SEGUIMIENTOS_IMPORT_TEMPLATE),
    "pagos": ("intelicoop_pagos_plantilla.csv", _PAGOS_IMPORT_TEMPLATE),
}
_BULK_CREDIT_IMPORT_THRESHOLD = 500
_DELETE_CONFIRMATION_TOKEN = "ELIMINAR INTELICOOP"


def _parse_optional_datetime(value: str | None) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"Fecha invalida: {raw}") from exc


def _parse_optional_bool(value: str | None, default: bool = False) -> bool:
    raw = str(value or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "si", "sí", "yes", "y", "x"}


def _parse_float(value: str | None, default: float = 0.0) -> float:
    raw = str(value or "").strip()
    if not raw:
        return default
    normalized = raw.replace("$", "").replace(",", "").replace("Q", "").strip()
    if normalized.startswith("(") and normalized.endswith(")"):
        normalized = f"-{normalized[1:-1].strip()}"
    try:
        return float(normalized)
    except ValueError as exc:
        raise ValueError(f"Numero invalido: {raw}") from exc


def _parse_int(value: str | None, default: int = 0) -> int:
    raw = str(value or "").strip()
    if not raw:
        return default
    return int(_parse_float(raw, float(default)))


def _normalize_credito_estado_import(value: str | None) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return "solicitado"
    mapping = {
        "pagado": "liquidado",
        "liquidado": "liquidado",
        "activo": "vigente",
        "vigente": "vigente",
        "aprobado": "aprobado",
        "rechazado": "rechazado",
        "mora": "mora",
        "moroso": "mora",
        "reestructurado": "reestructurado",
        "solicitado": "solicitado",
    }
    return mapping.get(raw, raw)


def _normalize_periodicidad_import(value: str | None) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return "mensual"
    compact = raw.replace(" ", "")
    if raw in {"mensual", "quincenal", "semanal", "bimestral"}:
        return raw
    if "quinc" in raw or compact in {"15dias", "1quincena"}:
        return "quincenal"
    if "seman" in raw or compact in {"7dias", "1semana"}:
        return "semanal"
    if "bimes" in raw or compact in {"2meses", "60dias"}:
        return "bimestral"
    if "mes" in raw or compact in {"1mes", "30dias"}:
        return "mensual"
    return "mensual"


async def _read_csv_rows(file: UploadFile) -> tuple[list[dict[str, str]], str]:
    filename = str(file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=422, detail="Solo se permite importar archivos CSV.")
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="El archivo debe estar codificado en UTF-8.") from exc
    rows = list(csv.DictReader(io.StringIO(text)))
    return rows, filename


def _ensure_required_columns(rows: list[dict[str, str]], required_columns: set[str]) -> None:
    fieldnames = set(rows[0].keys()) if rows else set()
    missing_columns = sorted(required_columns - fieldnames)
    if missing_columns:
        raise HTTPException(status_code=422, detail=f"Faltan columnas requeridas: {', '.join(missing_columns)}")


def _lookup_socio(row: dict[str, str], socios_by_id: dict[str, dict], socios_by_email: dict[str, dict]) -> dict:
    socio_id_raw = str(row.get("socio_id") or "").strip()
    socio_email_raw = str(row.get("socio_email") or "").strip().lower()
    socio = socios_by_id.get(socio_id_raw) if socio_id_raw else socios_by_email.get(socio_email_raw)
    if not socio:
        raise ValueError("No se encontro socio por socio_id o socio_email.")
    return socio


def _resolve_or_create_import_socio(
    row: dict[str, str],
    socios_by_id: dict[str, dict],
    socios_by_email: dict[str, dict],
) -> dict:
    try:
        return _lookup_socio(row, socios_by_id, socios_by_email)
    except ValueError:
        socio_id_raw = str(row.get("socio_id") or "").strip()
        socio_email_raw = str(row.get("socio_email") or "").strip().lower()
        synthetic_email = socio_email_raw or (f"intelicoop-import-{socio_id_raw}@local.invalid" if socio_id_raw else "")
        if synthetic_email and synthetic_email in socios_by_email:
            return socios_by_email[synthetic_email]
        if not synthetic_email:
            raise
        socio = create_socio(
            {
                "nombre": f"Socio importado {socio_id_raw or synthetic_email}",
                "email": synthetic_email,
                "telefono": "",
                "direccion": "",
                "segmento": "inactivo",
                "tipo_socio": "activo",
            }
        )
        if socio_id_raw:
            socios_by_id[socio_id_raw] = socio
        socios_by_email[str(socio.get("email") or "").strip().lower()] = socio
        return socio


def _lookup_campania(row: dict[str, str], campanias_by_id: dict[str, dict], campanias_by_name: dict[str, dict]) -> dict:
    campania_id_raw = str(row.get("campania_id") or "").strip()
    campania_nombre_raw = str(row.get("campania_nombre") or "").strip().lower()
    campania = campanias_by_id.get(campania_id_raw) if campania_id_raw else campanias_by_name.get(campania_nombre_raw)
    if not campania:
        raise ValueError("No se encontro campana por campania_id o campania_nombre.")
    return campania


def _build_import_response(file: UploadFile, total_rows: int, imported: list[dict], errors: list[dict]) -> JSONResponse:
    return JSONResponse(
        {
            "archivo": file.filename or "importacion.csv",
            "total_filas": total_rows,
            "importados": len(imported),
            "errores": errors,
            "registros": imported,
        },
        status_code=201,
    )


def _purge_intelicoop_data() -> dict:
    db = SessionLocal()
    try:
        bind = db.get_bind()
        intelicoop_tables = [name for name in sa_inspect(bind).get_table_names() if name.startswith("intelicoop_")]
        deleted_counts: dict[str, int] = {}
        db.execute(text("PRAGMA foreign_keys=OFF"))
        for table_name in reversed(intelicoop_tables):
            count = db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar() or 0
            db.execute(text(f'DELETE FROM "{table_name}"'))
            deleted_counts[table_name] = int(count)
        db.commit()
        return {
            "confirmation_required": _DELETE_CONFIRMATION_TOKEN,
            "deleted_tables": len(intelicoop_tables),
            "deleted_rows": sum(deleted_counts.values()),
            "counts": deleted_counts,
        }
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"No se pudieron eliminar los datos de Intelicoop: {exc}") from exc
    finally:
        db.close()


def _build_credito_payload(row: dict[str, str], socio_id: int) -> dict:
    numero_abonos_raw = row.get("numero_abonos")
    if numero_abonos_raw in (None, ""):
        numero_abonos_raw = row.get("plazo")
    return {
        "socio_id": int(socio_id),
        "monto": _parse_float(row.get("monto"), 0),
        "numero_abonos": _parse_int(numero_abonos_raw, 0),
        "periodicidad": _normalize_periodicidad_import(row.get("periodicidad")),
        "ingreso_mensual": _parse_float(row.get("ingreso_mensual"), 0),
        "deuda_actual": _parse_float(row.get("deuda_actual"), 0),
        "antiguedad_meses": _parse_int(row.get("antiguedad_meses"), 0),
        "tasa": _parse_float(row.get("tasa"), 0),
        "estado": _normalize_credito_estado_import(row.get("estado")),
        "dias_mora_actual": _parse_int(row.get("dias_mora_actual"), 0),
        "max_dias_mora": _parse_int(row.get("max_dias_mora"), 0),
        "num_reestructuras": _parse_int(row.get("num_reestructuras"), 0),
        "fecha_desembolso": _parse_optional_datetime(row.get("fecha_desembolso")),
        "fecha_vencimiento": _parse_optional_datetime(row.get("fecha_vencimiento")),
    }


def _bulk_import_creditos(rows: list[dict[str, str]]) -> tuple[int, list[dict], list[dict]]:
    db = SessionLocal()
    imported: list[dict] = []
    errors: list[dict] = []
    total_rows = 0
    try:
        socios = db.query(IntelicoopSocio).all()
        socios_by_id = {str(row.id): {"id": row.id, "email": row.email, "nombre": row.nombre} for row in socios}
        socios_by_email = {str(row.email or "").strip().lower(): {"id": row.id, "email": row.email, "nombre": row.nombre} for row in socios}
        pending_socio_specs: dict[str, dict] = {}
        staged_rows: list[tuple[int, dict, str]] = []

        for index, row in enumerate(rows, start=2):
            if not any(str(value or "").strip() for value in row.values()):
                continue
            total_rows += 1
            try:
                socio_id_raw = str(row.get("socio_id") or "").strip()
                socio_email_raw = str(row.get("socio_email") or "").strip().lower()
                synthetic_email = socio_email_raw or (f"intelicoop-import-{socio_id_raw}@local.invalid" if socio_id_raw else "")
                socio = socios_by_id.get(socio_id_raw) if socio_id_raw else socios_by_email.get(socio_email_raw)
                if socio is None and synthetic_email:
                    socio = socios_by_email.get(synthetic_email)
                if socio is None:
                    if not synthetic_email:
                        raise ValueError("No se encontro socio por socio_id o socio_email.")
                    pending_socio_specs.setdefault(
                        synthetic_email,
                        {
                            "nombre": f"Socio importado {socio_id_raw or synthetic_email}",
                            "email": synthetic_email,
                        },
                    )
                payload = _build_credito_payload(row, socio["id"] if socio else 0)
                staged_rows.append((index, payload, synthetic_email))
            except (TypeError, ValueError) as exc:
                errors.append({"linea": index, "error": str(exc)})

        if pending_socio_specs:
            socio_rows = [
                IntelicoopSocio(
                    nombre=spec["nombre"],
                    email=spec["email"],
                    telefono="",
                    direccion="",
                    segmento="inactivo",
                    tipo_socio="activo",
                )
                for spec in pending_socio_specs.values()
            ]
            db.add_all(socio_rows)
            db.flush()
            for row in socio_rows:
                socio_payload = {"id": row.id, "email": row.email, "nombre": row.nombre}
                socios_by_email[str(row.email or "").strip().lower()] = socio_payload

        credito_rows: list[tuple[int, IntelicoopCredito]] = []
        for index, payload, synthetic_email in staged_rows:
            try:
                socio = socios_by_email.get(synthetic_email) if synthetic_email else None
                if payload["socio_id"] <= 0:
                    if not socio:
                        raise ValueError("No se pudo resolver el socio para el credito.")
                    payload["socio_id"] = int(socio["id"])
                credito = IntelicoopCredito(
                    socio_id=int(payload["socio_id"]),
                    monto=float(payload["monto"]),
                    plazo=int(payload["numero_abonos"]),
                    numero_abonos=int(payload["numero_abonos"]),
                    periodicidad=str(payload["periodicidad"]),
                    ingreso_mensual=float(payload["ingreso_mensual"]),
                    deuda_actual=float(payload["deuda_actual"]),
                    antiguedad_meses=int(payload["antiguedad_meses"]),
                    tasa=float(payload["tasa"]),
                    estado=str(payload["estado"]),
                    dias_mora_actual=int(payload["dias_mora_actual"]),
                    max_dias_mora=int(payload["max_dias_mora"]),
                    num_reestructuras=int(payload["num_reestructuras"]),
                    fecha_desembolso=payload["fecha_desembolso"],
                    fecha_vencimiento=payload["fecha_vencimiento"],
                )
                credito_rows.append((index, credito))
            except (TypeError, ValueError) as exc:
                errors.append({"linea": index, "error": str(exc)})

        if credito_rows:
            db.add_all([row for _, row in credito_rows])
            db.flush()
            for index, credito in credito_rows:
                imported.append(
                    {
                        "linea": index,
                        "credito_id": credito.id,
                        "socio_id": credito.socio_id,
                        "scoring_omitido": True,
                    }
                )

        db.commit()
        return total_rows, imported, errors
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"No se pudo completar la importacion masiva: {exc}") from exc
    finally:
        db.close()


def _template_response(entity_key: str) -> Response:
    if entity_key not in _IMPORT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Plantilla no disponible.")
    filename, content = _IMPORT_TEMPLATES[entity_key]
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _templates_zip_response() -> Response:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, content in _IMPORT_TEMPLATES.values():
            archive.writestr(filename, content)
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="intelicoop_plantillas_importacion.zip"'},
    )


def _create_credito_with_scoring(payload: dict) -> dict:
    credito = create_credito(payload)
    scoring = evaluate_and_create_scoring_service(
        {
            "solicitud_id": f"cred-{credito['id']}",
            "socio_id": credito["socio_id"],
            "credito_id": credito["id"],
            "ingreso_mensual": float(payload.get("ingreso_mensual", 0) or 0),
            "deuda_actual": float(payload.get("deuda_actual", 0) or 0),
            "antiguedad_meses": int(payload.get("antiguedad_meses", 0) or 0),
        }
    )
    return {"credito": credito, "scoring": scoring}


@router.get("/intelicoop", response_class=HTMLResponse)
def intelicoop_redirect() -> RedirectResponse:
    return RedirectResponse(url="/inicio/intelicoop", status_code=307)


@router.get("/inicio/intelicoop", response_class=HTMLResponse)
def intelicoop_page(request: Request):
    content = read_text_file(INTELICOOP_TEMPLATE_PATH, "<p>No se pudo cargar la vista de Intelicoop.</p>")
    return render_backend_page_html(
        request,
        title="Intelicoop",
        description="Modulo SIPET para socios, creditos, ahorros, campanas y scoring.",
        content=content,
        show_page_header=False,
        module_icon="fa-solid fa-microchip",
    )


@router.get("/api/intelicoop/assets/intelicoop.js")
def intelicoop_js_asset() -> Response:
    return text_asset_response(
        INTELICOOP_JS_PATH,
        media_type="application/javascript",
        fallback="console.error('Intelicoop JS no disponible');",
    )


@router.get("/api/intelicoop/socios")
def api_list_socios():
    return JSONResponse(list_socios())


@router.post("/api/intelicoop/socios")
def api_create_socio(payload: SocioCreate):
    try:
        return JSONResponse(create_socio(payload.model_dump()), status_code=201)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/api/intelicoop/creditos")
def api_list_creditos():
    return JSONResponse(list_creditos())


@router.get("/api/intelicoop/creditos/{credito_id}")
def api_get_credito(credito_id: int):
    credito = get_credito(credito_id)
    if not credito:
        raise HTTPException(status_code=404, detail="Credito no encontrado.")
    return JSONResponse(credito)


@router.get("/api/intelicoop/creditos/{credito_id}/detalle")
def api_get_credito_detail(credito_id: int):
    credito = get_credito_detail(credito_id)
    if not credito:
        raise HTTPException(status_code=404, detail="Credito no encontrado.")
    return JSONResponse(credito)


@router.post("/api/intelicoop/creditos")
def api_create_credito(payload: CreditoCreate):
    try:
        return JSONResponse(_create_credito_with_scoring(payload.model_dump()), status_code=201)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/api/intelicoop/importacion/plantillas")
def api_import_templates_zip():
    return _templates_zip_response()


@router.get("/api/intelicoop/importacion/plantillas/{entity_key}")
def api_import_template_by_entity(entity_key: str):
    return _template_response(entity_key)


@router.get("/api/intelicoop/socios/importacion/plantilla")
def api_socios_template():
    return _template_response("socios")


@router.post("/api/intelicoop/socios/importacion")
async def api_import_socios(file: UploadFile = File(...)):
    rows, _filename = await _read_csv_rows(file)
    _ensure_required_columns(rows, {"nombre", "email"})
    imported = []
    errors = []
    total_rows = 0
    for index, row in enumerate(rows, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        total_rows += 1
        try:
            payload = {
                "nombre": str(row.get("nombre") or "").strip(),
                "email": str(row.get("email") or "").strip(),
                "telefono": str(row.get("telefono") or "").strip(),
                "direccion": str(row.get("direccion") or "").strip(),
                "segmento": str(row.get("segmento") or "inactivo").strip() or "inactivo",
                "fecha_nacimiento": str(row.get("fecha_nacimiento") or "").strip() or None,
                "genero": str(row.get("genero") or "").strip(),
                "estado_civil": str(row.get("estado_civil") or "").strip(),
                "nivel_educativo": str(row.get("nivel_educativo") or "").strip(),
                "ocupacion": str(row.get("ocupacion") or "").strip(),
                "sector_economico": str(row.get("sector_economico") or "").strip(),
                "ubicacion_estado": str(row.get("ubicacion_estado") or "").strip(),
                "ubicacion_municipio": str(row.get("ubicacion_municipio") or "").strip(),
                "tipo_socio": str(row.get("tipo_socio") or "activo").strip() or "activo",
            }
            socio = create_socio(payload)
            imported.append({"linea": index, "socio_id": socio["id"], "email": socio["email"]})
        except (TypeError, ValueError) as exc:
            errors.append({"linea": index, "error": str(exc)})
    return _build_import_response(file, total_rows, imported, errors)


@router.get("/api/intelicoop/creditos/importacion/plantilla")
def api_creditos_template():
    return _template_response("creditos")


@router.post("/api/intelicoop/creditos/importacion")
async def api_import_creditos(file: UploadFile = File(...)):
    rows, _filename = await _read_csv_rows(file)
    _ensure_required_columns(rows, {"monto", "numero_abonos", "ingreso_mensual", "deuda_actual", "antiguedad_meses", "estado"})
    non_empty_rows = [row for row in rows if any(str(value or "").strip() for value in row.values())]
    if len(non_empty_rows) > _BULK_CREDIT_IMPORT_THRESHOLD:
        total_rows, imported, errors = _bulk_import_creditos(rows)
        return JSONResponse(
            {
                "archivo": file.filename or "importacion.csv",
                "total_filas": total_rows,
                "importados": len(imported),
                "errores": errors,
                "registros": imported,
                "modo_importacion": "batch_sin_scoring",
            },
            status_code=201,
        )

    socios_by_id = {str(row["id"]): row for row in list_socios()}
    socios_by_email = {str(row.get("email") or "").strip().lower(): row for row in list_socios()}
    imported = []
    errors = []
    total_rows = 0

    for index, row in enumerate(rows, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        total_rows += 1
        try:
            socio = _resolve_or_create_import_socio(row, socios_by_id, socios_by_email)
            payload = _build_credito_payload(row, int(socio["id"]))
            result = _create_credito_with_scoring(payload)
            imported.append(
                {
                    "linea": index,
                    "credito_id": result["credito"]["id"],
                    "socio_id": result["credito"]["socio_id"],
                    "score": result["scoring"]["score"],
                    "recomendacion": result["scoring"]["recomendacion"],
                }
            )
        except (TypeError, ValueError) as exc:
            errors.append({"linea": index, "error": str(exc)})

    return _build_import_response(file, total_rows, imported, errors)


@router.get("/api/intelicoop/creditos/{credito_id}/pagos")
def api_list_credito_pagos(credito_id: int):
    return JSONResponse(list_historial_pagos(credito_id))


@router.get("/api/intelicoop/creditos/pagos/importacion/plantilla")
def api_pagos_template():
    return _template_response("pagos")


@router.post("/api/intelicoop/creditos/pagos/importacion")
async def api_import_pagos(file: UploadFile = File(...)):
    rows, _filename = await _read_csv_rows(file)
    _ensure_required_columns(rows, {"credito_id", "monto"})
    creditos_by_id = {str(row["id"]): row for row in list_creditos()}
    imported = []
    errors = []
    total_rows = 0

    for index, row in enumerate(rows, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        total_rows += 1
        try:
            credito_id_raw = str(row.get("credito_id") or "").strip()
            if credito_id_raw not in creditos_by_id:
                raise ValueError("No se encontro credito por credito_id.")
            payload = {
                "credito_id": int(credito_id_raw),
                "monto": float(row.get("monto") or 0),
                "pago_puntual": _parse_optional_bool(row.get("pago_puntual"), default=True),
                "dias_atraso": int(float(row.get("dias_atraso") or 0)),
            }
            pago = create_historial_pago(payload)
            imported.append({"linea": index, "pago_id": pago["id"], "credito_id": pago["credito_id"]})
        except (TypeError, ValueError) as exc:
            errors.append({"linea": index, "error": str(exc)})

    return _build_import_response(file, total_rows, imported, errors)


@router.post("/api/intelicoop/creditos/pagos")
def api_create_credito_pago(payload: HistorialPagoCreate):
    try:
        return JSONResponse(create_historial_pago(payload.model_dump()), status_code=201)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/api/intelicoop/ahorros/resumen")
def api_ahorros_resumen():
    return JSONResponse(get_ahorros_resumen())


@router.get("/api/intelicoop/ahorros/cuentas")
def api_list_cuentas():
    return JSONResponse(list_cuentas())


@router.get("/api/intelicoop/ahorros/cuentas/importacion/plantilla")
def api_cuentas_template():
    return _template_response("cuentas")


@router.post("/api/intelicoop/ahorros/cuentas/importacion")
async def api_import_cuentas(file: UploadFile = File(...)):
    rows, _filename = await _read_csv_rows(file)
    _ensure_required_columns(rows, {"tipo", "saldo"})
    socios = list_socios()
    socios_by_id = {str(row["id"]): row for row in socios}
    socios_by_email = {str(row.get("email") or "").strip().lower(): row for row in socios}
    imported = []
    errors = []
    total_rows = 0

    for index, row in enumerate(rows, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        total_rows += 1
        try:
            socio = _lookup_socio(row, socios_by_id, socios_by_email)
            payload = {
                "socio_id": int(socio["id"]),
                "tipo": str(row.get("tipo") or "ahorro").strip() or "ahorro",
                "saldo": float(row.get("saldo") or 0),
            }
            cuenta = create_cuenta(payload)
            imported.append({"linea": index, "cuenta_id": cuenta["id"], "socio_id": cuenta["socio_id"]})
        except (TypeError, ValueError) as exc:
            errors.append({"linea": index, "error": str(exc)})

    return _build_import_response(file, total_rows, imported, errors)


@router.post("/api/intelicoop/ahorros/cuentas")
def api_create_cuenta(payload: CuentaCreate):
    try:
        return JSONResponse(create_cuenta(payload.model_dump()), status_code=201)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/api/intelicoop/ahorros/transacciones")
def api_list_transacciones():
    return JSONResponse(list_transacciones())


@router.get("/api/intelicoop/ahorros/transacciones/importacion/plantilla")
def api_transacciones_template():
    return _template_response("transacciones")


@router.post("/api/intelicoop/ahorros/transacciones/importacion")
async def api_import_transacciones(file: UploadFile = File(...)):
    rows, _filename = await _read_csv_rows(file)
    _ensure_required_columns(rows, {"cuenta_id", "monto"})
    cuentas_by_id = {str(row["id"]): row for row in list_cuentas()}
    imported = []
    errors = []
    total_rows = 0

    for index, row in enumerate(rows, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        total_rows += 1
        try:
            cuenta_id_raw = str(row.get("cuenta_id") or "").strip()
            if cuenta_id_raw not in cuentas_by_id:
                raise ValueError("No se encontro cuenta por cuenta_id.")
            payload = {
                "cuenta_id": int(cuenta_id_raw),
                "monto": float(row.get("monto") or 0),
                "tipo": str(row.get("tipo") or "deposito").strip() or "deposito",
                "canal": str(row.get("canal") or "").strip(),
            }
            transaccion = create_transaccion(payload)
            imported.append(
                {"linea": index, "transaccion_id": transaccion["id"], "cuenta_id": transaccion["cuenta_id"]}
            )
        except (TypeError, ValueError) as exc:
            errors.append({"linea": index, "error": str(exc)})

    return _build_import_response(file, total_rows, imported, errors)


@router.post("/api/intelicoop/ahorros/transacciones")
def api_create_transaccion(payload: TransaccionCreate):
    try:
        return JSONResponse(create_transaccion(payload.model_dump()), status_code=201)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/api/intelicoop/campanas")
def api_list_campanas():
    return JSONResponse(list_campanas())


@router.get("/api/intelicoop/campanas/importacion/plantilla")
def api_campanas_template():
    return _template_response("campanas")


@router.post("/api/intelicoop/campanas/importacion")
async def api_import_campanas(file: UploadFile = File(...)):
    rows, _filename = await _read_csv_rows(file)
    _ensure_required_columns(rows, {"nombre", "tipo"})
    imported = []
    errors = []
    total_rows = 0

    for index, row in enumerate(rows, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        total_rows += 1
        try:
            payload = {
                "nombre": str(row.get("nombre") or "").strip(),
                "tipo": str(row.get("tipo") or "").strip(),
                "fecha_inicio": _parse_optional_datetime(row.get("fecha_inicio")),
                "fecha_fin": _parse_optional_datetime(row.get("fecha_fin")),
                "estado": str(row.get("estado") or "borrador").strip() or "borrador",
            }
            campania = create_campana(payload)
            imported.append({"linea": index, "campania_id": campania["id"], "nombre": campania["nombre"]})
        except (TypeError, ValueError) as exc:
            errors.append({"linea": index, "error": str(exc)})

    return _build_import_response(file, total_rows, imported, errors)


@router.post("/api/intelicoop/campanas")
def api_create_campana(payload: CampaniaCreate):
    return JSONResponse(create_campana(payload.model_dump()), status_code=201)


@router.get("/api/intelicoop/campanas/contactos")
def api_list_contactos_campania():
    return JSONResponse(list_contactos_campania())


@router.get("/api/intelicoop/campanas/contactos/importacion/plantilla")
def api_contactos_template():
    return _template_response("contactos")


@router.post("/api/intelicoop/campanas/contactos/importacion")
async def api_import_contactos(file: UploadFile = File(...)):
    rows, _filename = await _read_csv_rows(file)
    _ensure_required_columns(rows, {"ejecutivo_id", "canal", "estado_contacto"})
    socios = list_socios()
    campanias = list_campanas()
    socios_by_id = {str(row["id"]): row for row in socios}
    socios_by_email = {str(row.get("email") or "").strip().lower(): row for row in socios}
    campanias_by_id = {str(row["id"]): row for row in campanias}
    campanias_by_name = {str(row.get("nombre") or "").strip().lower(): row for row in campanias}
    imported = []
    errors = []
    total_rows = 0

    for index, row in enumerate(rows, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        total_rows += 1
        try:
            campania = _lookup_campania(row, campanias_by_id, campanias_by_name)
            socio = _lookup_socio(row, socios_by_id, socios_by_email)
            payload = {
                "campania_id": int(campania["id"]),
                "socio_id": int(socio["id"]),
                "ejecutivo_id": str(row.get("ejecutivo_id") or "ejecutivo_general").strip() or "ejecutivo_general",
                "canal": str(row.get("canal") or "telefono").strip() or "telefono",
                "estado_contacto": str(row.get("estado_contacto") or "pendiente").strip() or "pendiente",
            }
            contacto = create_contacto_campania(payload)
            imported.append(
                {
                    "linea": index,
                    "contacto_id": contacto["id"],
                    "campania_id": contacto["campania_id"],
                    "socio_id": contacto["socio_id"],
                }
            )
        except (TypeError, ValueError) as exc:
            errors.append({"linea": index, "error": str(exc)})

    return _build_import_response(file, total_rows, imported, errors)


@router.post("/api/intelicoop/campanas/contactos")
def api_create_contacto_campania(payload: ContactoCampaniaCreate):
    try:
        return JSONResponse(create_contacto_campania(payload.model_dump()), status_code=201)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/api/intelicoop/campanas/seguimientos")
def api_list_seguimientos_campania():
    return JSONResponse(list_seguimientos_campania())


@router.get("/api/intelicoop/campanas/seguimientos/importacion/plantilla")
def api_seguimientos_template():
    return _template_response("seguimientos")


@router.post("/api/intelicoop/campanas/seguimientos/importacion")
async def api_import_seguimientos(file: UploadFile = File(...)):
    rows, _filename = await _read_csv_rows(file)
    _ensure_required_columns(rows, {"lista", "etapa", "monto_colocado"})
    socios = list_socios()
    campanias = list_campanas()
    socios_by_id = {str(row["id"]): row for row in socios}
    socios_by_email = {str(row.get("email") or "").strip().lower(): row for row in socios}
    campanias_by_id = {str(row["id"]): row for row in campanias}
    campanias_by_name = {str(row.get("nombre") or "").strip().lower(): row for row in campanias}
    imported = []
    errors = []
    total_rows = 0

    for index, row in enumerate(rows, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        total_rows += 1
        try:
            campania = _lookup_campania(row, campanias_by_id, campanias_by_name)
            socio = _lookup_socio(row, socios_by_id, socios_by_email)
            payload = {
                "campania_id": int(campania["id"]),
                "socio_id": int(socio["id"]),
                "lista": str(row.get("lista") or "general").strip() or "general",
                "etapa": str(row.get("etapa") or "contactado").strip() or "contactado",
                "conversion": _parse_optional_bool(row.get("conversion"), default=False),
                "monto_colocado": float(row.get("monto_colocado") or 0),
            }
            seguimiento = create_seguimiento_campania(payload)
            imported.append(
                {
                    "linea": index,
                    "seguimiento_id": seguimiento["id"],
                    "campania_id": seguimiento["campania_id"],
                    "socio_id": seguimiento["socio_id"],
                }
            )
        except (TypeError, ValueError) as exc:
            errors.append({"linea": index, "error": str(exc)})

    return _build_import_response(file, total_rows, imported, errors)


@router.post("/api/intelicoop/campanas/seguimientos")
def api_create_seguimiento_campania(payload: SeguimientoCampaniaCreate):
    try:
        return JSONResponse(create_seguimiento_campania(payload.model_dump()), status_code=201)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/api/intelicoop/prospectos")
def api_list_prospectos():
    return JSONResponse(list_prospectos())


@router.get("/api/intelicoop/prospectos/importacion/plantilla")
def api_prospectos_template():
    return _template_response("prospectos")


@router.post("/api/intelicoop/prospectos/importacion")
async def api_import_prospectos(file: UploadFile = File(...)):
    rows, _filename = await _read_csv_rows(file)
    _ensure_required_columns(rows, {"nombre"})
    imported = []
    errors = []
    total_rows = 0

    for index, row in enumerate(rows, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        total_rows += 1
        try:
            payload = {
                "nombre": str(row.get("nombre") or "").strip(),
                "telefono": str(row.get("telefono") or "").strip(),
                "direccion": str(row.get("direccion") or "").strip(),
                "fuente": str(row.get("fuente") or "").strip(),
                "score_propension": float(row.get("score_propension") or 0),
            }
            prospecto = create_prospecto(payload)
            imported.append({"linea": index, "prospecto_id": prospecto["id"], "nombre": prospecto["nombre"]})
        except (TypeError, ValueError) as exc:
            errors.append({"linea": index, "error": str(exc)})

    return _build_import_response(file, total_rows, imported, errors)


@router.post("/api/intelicoop/prospectos")
def api_create_prospecto(payload: ProspectoCreate):
    return JSONResponse(create_prospecto(payload.model_dump()), status_code=201)


@router.post("/api/intelicoop/scoring/evaluar")
def api_scoring_evaluar(payload: ScoringEvaluateInput):
    result = evaluate_and_create_scoring_service(payload.model_dump())
    return JSONResponse(result, status_code=201)


@router.get("/api/intelicoop/scoring/{scoring_result_id}/traza")
def api_scoring_traza(scoring_result_id: int):
    result = get_scoring_trace_service(scoring_result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Traza de scoring no encontrada.")
    return JSONResponse(result)


@router.get("/api/intelicoop/scoring/resumen")
def api_scoring_resumen():
    return JSONResponse(get_scoring_summary_service())


@router.get("/api/intelicoop/scoring/explicabilidad")
def api_scoring_explicabilidad(socio_id: int | None = None):
    return JSONResponse(get_scoring_explainability_service(socio_id=socio_id))


@router.get("/api/intelicoop/dashboard/resumen")
def api_dashboard_resumen():
    return JSONResponse(get_dashboard_resumen_service())


@router.get("/api/intelicoop/catalogos/basicos")
def api_basic_catalogs():
    return JSONResponse(get_basic_catalogs())


@router.get("/api/intelicoop/fundamentos/resumen")
def api_foundation_overview():
    return JSONResponse(get_foundation_overview_service())


@router.post("/api/intelicoop/fundamentos/materializar")
def api_foundation_materialize(payload: FoundationMaterializeInput):
    return JSONResponse(materialize_foundation_cut_service(cut_type=payload.cut_type), status_code=201)


@router.get("/api/intelicoop/analitica/resumen")
def api_analitica_resumen():
    return JSONResponse(get_descriptive_analytics_service())


@router.get("/api/intelicoop/analitica/tendencias")
def api_analitica_tendencias(kpi_key: str = "imor_pct", n_cuts: int = 12):
    return JSONResponse(get_tendencias_service(kpi_key=kpi_key, n_cuts=n_cuts))


@router.get("/api/intelicoop/analitica/cohortes")
def api_analitica_cohortes(dimension: str = ""):
    return JSONResponse(get_cohortes_service(dimension=dimension or None))


@router.get("/api/intelicoop/analitica/patrones")
def api_analitica_patrones():
    return JSONResponse(get_pattern_discovery_summary_service())


@router.get("/api/intelicoop/segmentacion/resumen")
def api_segmentacion_resumen():
    return JSONResponse(get_segmentation_propensity_summary_service())


@router.get("/api/intelicoop/batch/resumen")
def api_batch_resumen():
    return JSONResponse(get_batch_overview_service())


@router.get("/api/intelicoop/batch/runs")
def api_batch_runs(limit: int = 20):
    return JSONResponse(list_batch_runs_service(limit=limit))


@router.get("/api/intelicoop/batch/alertas")
def api_batch_alertas(limit: int = 20):
    return JSONResponse(list_batch_alerts_service(limit=limit))


@router.post("/api/intelicoop/batch/ejecutar")
def api_batch_ejecutar(payload: BatchExecuteInput):
    return JSONResponse(run_batch_job_service(job_key=payload.job_key), status_code=201)


@router.post("/api/intelicoop/batch/ejecutar-programados")
def api_batch_ejecutar_programados():
    return JSONResponse(run_due_batch_jobs_service(), status_code=201)


@router.get("/api/intelicoop/gobernanza/resumen")
def api_gobernanza_resumen():
    return JSONResponse(get_governance_overview_service())


@router.post("/api/intelicoop/gobernanza/refresh")
def api_gobernanza_refresh():
    return JSONResponse(run_governance_refresh_service(actor="manual"), status_code=201)


@router.post("/api/intelicoop/datos/eliminar")
async def api_eliminar_datos_intelicoop(request: Request):
    payload = await request.json()
    confirmation = str(payload.get("confirmation") or "").strip()
    if confirmation != _DELETE_CONFIRMATION_TOKEN:
        raise HTTPException(
            status_code=422,
            detail=f"Confirmacion invalida. Escribe exactamente: {_DELETE_CONFIRMATION_TOKEN}",
        )
    return JSONResponse(_purge_intelicoop_data(), status_code=200)
