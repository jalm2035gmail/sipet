from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from openpyxl import Workbook

SYSTEM_REPORT_HEADER_TEMPLATE_ID = "system-report-header"

router = APIRouter()


def _render_reportes_page(request: Request, title: str = "Reportes") -> HTMLResponse:
    try:
        from fastapi_modulo.main import render_backend_page
    except Exception:
        return HTMLResponse("<h1>Reportes</h1><p>Módulo de reportes.</p>")
    content = (
        "<section class='content-section'>"
        "<div class='content-section-head'><h2 class='content-section-title'>Exportación de reportes</h2></div>"
        "<div class='content-section-body'>"
        "<p>Genera y descarga reportes consolidados en HTML, PDF y Excel.</p>"
        "<div class='actions' style='display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;'>"
        "<a class='color-btn color-btn--primary' href='/api/reportes/export/html'>Exportar HTML</a>"
        "<a class='color-btn color-btn--ghost' href='/api/reportes/export/pdf'>Exportar PDF</a>"
        "<a class='color-btn color-btn--ghost' href='/api/reportes/export/excel'>Exportar Excel</a>"
        "</div></div></section>"
    )
    return render_backend_page(
        request,
        title=title,
        description="Generación y exportación de reportes.",
        content=content,
        hide_floating_actions=True,
        show_page_header=True,
    )


@router.get("/reportes", response_class=HTMLResponse)
def reportes_page(request: Request) -> HTMLResponse:
    return _render_reportes_page(request, "Reportes")


@router.get("/reportes/documentos", response_class=HTMLResponse)
def reportes_documentos_page(request: Request) -> HTMLResponse:
    return _render_reportes_page(request, "Reportes de documentos")


def _get_core_callables() -> Tuple[Optional[Callable[[], List[Dict[str, str]]]], Optional[Callable[[], Dict[str, Any]]]]:
    try:
        from fastapi_modulo import main as core  # Import diferido para evitar ciclo.
    except Exception:
        return None, None
    load_plantillas_store = getattr(core, "_load_plantillas_store", None)
    load_login_identity = getattr(core, "_load_login_identity", None)
    if not callable(load_plantillas_store):
        load_plantillas_store = None
    if not callable(load_login_identity):
        load_login_identity = None
    return load_plantillas_store, load_login_identity


def build_default_report_header_template() -> Dict[str, str]:
    now_iso = datetime.utcnow().isoformat()
    return {
        "id": SYSTEM_REPORT_HEADER_TEMPLATE_ID,
        "nombre": "Encabezado",
        "html": (
            "<header class='reporte-encabezado'>"
            "<div class='reporte-encabezado__marca'>{{ empresa }}</div>"
            "<div class='reporte-encabezado__meta'>"
            "<h1>{{ titulo_reporte }}</h1>"
            "<p>{{ subtitulo_reporte }}</p>"
            "</div>"
            "<div class='reporte-encabezado__fecha'>Fecha: {{ fecha_reporte }}</div>"
            "</header>"
        ),
        "css": (
            ".reporte-encabezado { display:flex; align-items:center; justify-content:space-between; gap:16px; "
            "padding:16px 20px; border:1px solid #cbd5e1; border-radius:12px; background:#f8fafc; font-family:Arial,sans-serif; } "
            ".reporte-encabezado__marca { font-weight:800; color:#0f172a; font-size:1.1rem; letter-spacing:.04em; } "
            ".reporte-encabezado__meta h1 { margin:0; font-size:1.05rem; color:#0f172a; } "
            ".reporte-encabezado__meta p { margin:4px 0 0; color:#475569; font-size:.88rem; } "
            ".reporte-encabezado__fecha { color:#334155; font-size:.84rem; white-space:nowrap; }"
        ),
        "created_at": now_iso,
        "updated_at": now_iso,
    }


def _get_report_header_template() -> Dict[str, str]:
    load_plantillas_store, _ = _get_core_callables()
    if not load_plantillas_store:
        return build_default_report_header_template()
    templates = load_plantillas_store()
    for tpl in templates:
        if str(tpl.get("id", "")).strip() == SYSTEM_REPORT_HEADER_TEMPLATE_ID:
            return tpl
    for tpl in templates:
        if str(tpl.get("nombre", "")).strip().lower() == "encabezado":
            return tpl
    return build_default_report_header_template()


def _apply_template_context(content: str, context: Dict[str, str]) -> str:
    rendered = content or ""
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{ {key} }}}}", value)
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def _build_report_export_context() -> Dict[str, str]:
    _, load_login_identity = _get_core_callables()
    identidad = load_login_identity() if load_login_identity else {}
    empresa = str(identidad.get("company_short_name") or "SIPET")
    return {
        "empresa": empresa,
        "titulo_reporte": "Reporte consolidado",
        "subtitulo_reporte": "Avance, desempeno y seguimiento",
        "fecha_reporte": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _build_report_export_rows() -> List[Dict[str, str]]:
    return [
        {
            "reporte": "Reporte ejecutivo",
            "descripcion": "Resumen de estado estrategico",
            "formato": "PDF / Excel",
        },
        {
            "reporte": "Reporte operativo",
            "descripcion": "Actividades, avances y cumplimiento",
            "formato": "PDF / Excel",
        },
        {
            "reporte": "Reporte KPI",
            "descripcion": "Indicadores, metas y variaciones",
            "formato": "PDF / Excel",
        },
    ]


def _build_report_export_html_document() -> str:
    template = _get_report_header_template()
    context = _build_report_export_context()
    header_html = _apply_template_context(template.get("html", ""), context)
    header_css = template.get("css", "")
    rows = _build_report_export_rows()
    rows_html = "".join(
        (
            "<tr>"
            f"<td>{escape(row['reporte'])}</td>"
            f"<td>{escape(row['descripcion'])}</td>"
            f"<td>{escape(row['formato'])}</td>"
            "</tr>"
        )
        for row in rows
    )
    return (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        "<title>Reporte consolidado</title>"
        "<style>"
        f"{header_css}"
        "body{font-family:Arial,sans-serif;background:#fff;color:#0f172a;padding:24px;}"
        ".reporte-bloque{margin-top:18px;}"
        "table{width:100%;border-collapse:collapse;}"
        "th,td{border:1px solid #cbd5e1;padding:10px;text-align:left;font-size:14px;}"
        "th{background:#f1f5f9;}"
        "</style></head><body>"
        f"{header_html}"
        "<section class='reporte-bloque'>"
        "<h2>Detalle de reportes</h2>"
        "<table><thead><tr><th>Reporte</th><th>Descripcion</th><th>Formato</th></tr></thead>"
        f"<tbody>{rows_html}</tbody></table>"
        "</section></body></html>"
    )


def _build_report_export_xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Reporte"
    sheet.append(["Reporte", "Descripcion", "Formato"])
    for row in _build_report_export_rows():
        sheet.append([row["reporte"], row["descripcion"], row["formato"]])
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


@router.get("/reportes/exportar-html", response_class=HTMLResponse)
def exportar_reporte_html_legacy() -> HTMLResponse:
    html = _build_report_export_html_document()
    return HTMLResponse(content=html)


@router.get("/api/reportes/export/html", response_class=HTMLResponse)
def exportar_reporte_html() -> HTMLResponse:
    html = _build_report_export_html_document()
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": "attachment; filename=reporte_consolidado.html"},
    )


@router.get("/api/reportes/export/pdf", response_class=HTMLResponse)
def exportar_reporte_pdf() -> HTMLResponse:
    # Fallback mientras no exista motor PDF en el proyecto.
    html = _build_report_export_html_document()
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": "attachment; filename=reporte_consolidado.html"},
    )


@router.get("/api/reportes/export/excel")
def exportar_reporte_excel() -> Response:
    return Response(
        content=_build_report_export_xlsx_bytes(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reporte_consolidado.xlsx"},
    )
