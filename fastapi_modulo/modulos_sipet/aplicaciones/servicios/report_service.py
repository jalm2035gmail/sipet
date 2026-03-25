from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.persistence_repository import (
    list_registry_state,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.catalog_service import (
    decorate_modules_payload,
)

# ---------------------------------------------------------------------------
# palette
# ---------------------------------------------------------------------------
_BLUE_DARK = colors.HexColor("#1E3A5F")
_BLUE_MID = colors.HexColor("#2E6DA4")
_BLUE_LIGHT = colors.HexColor("#EAF0FB")
_GREEN = colors.HexColor("#27AE60")
_RED = colors.HexColor("#C0392B")
_GRAY = colors.HexColor("#7F8C8D")
_WHITE = colors.white
_BLACK = colors.black

# ---------------------------------------------------------------------------
# styles
# ---------------------------------------------------------------------------
_BASE = getSampleStyleSheet()

_S_TITLE = ParagraphStyle(
    "ReportTitle",
    parent=_BASE["Title"],
    fontSize=18,
    textColor=_BLUE_DARK,
    spaceAfter=4,
)
_S_SUBTITLE = ParagraphStyle(
    "ReportSubtitle",
    parent=_BASE["Normal"],
    fontSize=10,
    textColor=_GRAY,
    spaceAfter=2,
)
_S_SECTION = ParagraphStyle(
    "SectionHead",
    parent=_BASE["Heading2"],
    fontSize=12,
    textColor=_BLUE_DARK,
    spaceBefore=14,
    spaceAfter=4,
    borderPad=2,
)
_S_BODY = ParagraphStyle(
    "Body",
    parent=_BASE["Normal"],
    fontSize=9,
    leading=13,
)
_S_CELL = ParagraphStyle(
    "Cell",
    parent=_BASE["Normal"],
    fontSize=8,
    leading=11,
    wordWrap="CJK",
)
_S_CELL_BOLD = ParagraphStyle(
    "CellBold",
    parent=_S_CELL,
    fontName="Helvetica-Bold",
)

# ---------------------------------------------------------------------------
# table helpers
# ---------------------------------------------------------------------------

_TBL_HEADER_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), _BLUE_DARK),
    ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ("TOPPADDING", (0, 0), (-1, 0), 6),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _BLUE_LIGHT]),
    ("FONTSIZE", (0, 1), (-1, -1), 8),
    ("ALIGN", (0, 1), (-1, -1), "LEFT"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 1), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("GRID", (0, 0), (-1, -1), 0.3, _GRAY),
])

_TBL_KV_STYLE = TableStyle([
    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
    ("ALIGN", (1, 0), (1, -1), "LEFT"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_WHITE, _BLUE_LIGHT]),
    ("GRID", (0, 0), (-1, -1), 0.2, _GRAY),
])


def _bool_chip(value: Any) -> Paragraph:
    color = "#27AE60" if value else "#C0392B"
    label = "Sí" if value else "No"
    html = f'<font color="{color}"><b>{label}</b></font>'
    return Paragraph(html, _S_CELL)


def _p(text: str, style: ParagraphStyle = _S_CELL) -> Paragraph:
    return Paragraph(str(text or ""), style)


# ---------------------------------------------------------------------------
# data retrieval
# ---------------------------------------------------------------------------

def _load_module_data(module_key: str) -> dict[str, Any]:
    modules = decorate_modules_payload()
    mod = next((m for m in modules if str(m.get("key") or "") == module_key), None)
    return mod or {}


def _load_registry_audits(module_key: str) -> list[Any]:
    from sqlalchemy import desc
    from sqlalchemy.exc import OperationalError, ProgrammingError

    from fastapi_modulo.core import db as core_db
    from fastapi_modulo.modulos_sipet.aplicaciones.modelos.db_models import AppRegistryAudit

    try:
        session_factory = core_db.get_admin_session_factory()
        with session_factory() as db:
            return (
                db.query(AppRegistryAudit)
                .filter(AppRegistryAudit.module_key == module_key)
                .order_by(desc(AppRegistryAudit.created_at), desc(AppRegistryAudit.id))
                .all()
            )
    except (OperationalError, ProgrammingError):
        return []


def _load_package_uploads(module_key: str) -> list[Any]:
    from sqlalchemy import desc
    from sqlalchemy.exc import OperationalError, ProgrammingError

    from fastapi_modulo.core import db as core_db
    from fastapi_modulo.modulos_sipet.aplicaciones.modelos.db_models import AppPackageUpload

    try:
        session_factory = core_db.get_admin_session_factory()
        with session_factory() as db:
            return (
                db.query(AppPackageUpload)
                .filter(AppPackageUpload.module_key == module_key)
                .order_by(desc(AppPackageUpload.uploaded_at), desc(AppPackageUpload.id))
                .all()
            )
    except (OperationalError, ProgrammingError):
        return []


# ---------------------------------------------------------------------------
# section builders
# ---------------------------------------------------------------------------

def _section_header(title: str) -> list:
    return [
        Paragraph(title, _S_SECTION),
        HRFlowable(width="100%", thickness=1, color=_BLUE_MID, spaceAfter=4),
    ]


def _build_module_summary(mod: dict[str, Any], page_width: float) -> list:
    col_w = (page_width - 4 * cm) / 2
    kv = [
        ["Clave:", mod.get("key", "—")],
        ["Nombre:", mod.get("name", "—")],
        ["Versión instalada:", mod.get("installed_version", "—") or "—"],
        ["Habilitado:", _bool_chip(mod.get("enabled"))],
        ["Directorio:", mod.get("module_dir", "—") or "—"],
        ["Subida de paquete:", _bool_chip(mod.get("package_upload_enabled"))],
        ["Archivo subido:", mod.get("uploaded_filename", "—") or "—"],
        ["Fecha subida:", mod.get("uploaded_at", "—") or "—"],
    ]
    rows = [[_p(r[0], _S_CELL_BOLD), _p(r[1]) if isinstance(r[1], str) else r[1]] for r in kv]
    tbl = Table(rows, colWidths=[col_w * 0.4, col_w * 1.6])
    tbl.setStyle(_TBL_KV_STYLE)
    return [*_section_header("Información del Módulo"), tbl, Spacer(1, 6)]


def _build_protocol_section(mod: dict[str, Any], page_width: float) -> list:
    col_w = (page_width - 4 * cm) / 2
    missing = ", ".join(mod.get("protocol_missing") or []) or "Ninguno"
    kv = [
        ["Protocolo OK:", _bool_chip(mod.get("protocol_ok"))],
        ["Tiene __init__.py:", _bool_chip(mod.get("protocol_has_init"))],
        ["Tiene __manifest__.py:", _bool_chip(mod.get("protocol_has_manifest"))],
        ["Archivos faltantes:", _p(missing)],
    ]
    rows = [[_p(r[0], _S_CELL_BOLD), _p(r[1]) if isinstance(r[1], str) else r[1]] for r in kv]
    tbl = Table(rows, colWidths=[col_w * 0.5, col_w * 1.5])
    tbl.setStyle(_TBL_KV_STYLE)
    return [*_section_header("Auditoría de Protocolo"), tbl, Spacer(1, 6)]


def _build_uploads_section(uploads: list[Any], page_width: float) -> list:
    usable = page_width - 4 * cm
    headers = ["#", "Archivo original", "Checksum", "Tamaño (bytes)", "Subido por", "Fecha (UTC)", "Aplicado"]
    col_widths = [
        usable * 0.04,
        usable * 0.22,
        usable * 0.20,
        usable * 0.10,
        usable * 0.14,
        usable * 0.18,
        usable * 0.12,
    ]
    rows = [[_p(h, _S_CELL_BOLD) for h in headers]]
    for i, up in enumerate(uploads, start=1):
        uploaded = up.uploaded_at
        date_str = uploaded.strftime("%Y-%m-%d %H:%M") if isinstance(uploaded, datetime) else str(uploaded or "")
        rows.append([
            _p(str(i)),
            _p(up.original_filename or ""),
            _p((up.checksum or "")[:18] + "…" if len(up.checksum or "") > 18 else (up.checksum or "")),
            _p(str(up.file_size or 0)),
            _p(up.uploaded_by or "—"),
            _p(date_str),
            _bool_chip(up.applied),
        ])
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(_TBL_HEADER_STYLE)
    return [*_section_header("Historial de Paquetes Subidos"), tbl, Spacer(1, 6)]


def _build_audit_section(audits: list[Any], page_width: float) -> list:
    usable = page_width - 4 * cm
    headers = ["#", "Acción", "Resultado", "Usuario", "IP", "Fecha (UTC)", "Payload (resumen)"]
    col_widths = [
        usable * 0.04,
        usable * 0.14,
        usable * 0.10,
        usable * 0.14,
        usable * 0.12,
        usable * 0.16,
        usable * 0.30,
    ]
    rows = [[_p(h, _S_CELL_BOLD) for h in headers]]
    for i, a in enumerate(audits, start=1):
        created = a.created_at
        date_str = created.strftime("%Y-%m-%d %H:%M") if isinstance(created, datetime) else str(created or "")
        try:
            payload_obj = json.loads(a.payload_json or "{}")
            payload_text = ", ".join(f"{k}={v}" for k, v in payload_obj.items())[:120]
        except Exception:
            payload_text = str(a.payload_json or "")[:120]
        rows.append([
            _p(str(i)),
            _p(a.action or ""),
            _p(a.result or ""),
            _p(a.user_id or "—"),
            _p(a.ip or "—"),
            _p(date_str),
            _p(payload_text),
        ])
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(_TBL_HEADER_STYLE)
    return [*_section_header("Historial de Auditoría"), tbl, Spacer(1, 6)]


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def generate_module_audit_pdf(module_key: str) -> bytes:
    mod = _load_module_data(module_key)
    audits = _load_registry_audits(module_key)
    uploads = _load_package_uploads(module_key)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
        title=f"Reporte de Auditoría – {module_key}",
        author="SIPET",
    )

    page_width = A4[0]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    story: list = [
        Paragraph(f"Reporte de Auditoría de Módulo", _S_TITLE),
        Paragraph(f"Módulo: <b>{module_key}</b> &nbsp;·&nbsp; Generado: {generated_at}", _S_SUBTITLE),
        HRFlowable(width="100%", thickness=2, color=_BLUE_DARK, spaceAfter=10),
    ]

    if mod:
        story += _build_module_summary(mod, page_width)
        story += _build_protocol_section(mod, page_width)
    else:
        story.append(Paragraph(f"No se encontró información para el módulo <b>{module_key}</b>.", _S_BODY))

    if uploads:
        story += _build_uploads_section(uploads, page_width)
    else:
        story += [*_section_header("Historial de Paquetes Subidos"), Paragraph("Sin registros.", _S_BODY), Spacer(1, 6)]

    if audits:
        story += _build_audit_section(audits, page_width)
    else:
        story += [*_section_header("Historial de Auditoría"), Paragraph("Sin registros de auditoría.", _S_BODY)]

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def get_report_filename(module_key: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"reporte_auditoria_{module_key}_{ts}.pdf"


__all__ = ["generate_module_audit_pdf", "get_report_filename"]
