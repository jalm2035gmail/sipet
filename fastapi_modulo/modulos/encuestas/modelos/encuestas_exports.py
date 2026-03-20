from __future__ import annotations

from io import BytesIO, StringIO
from typing import Any, Dict, List, Optional

import pandas as pd
from openpyxl.utils import get_column_letter
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from fastapi_modulo.modulos.encuestas.modelos.encuestas_analytics import get_results_dashboard

# ── Chart dimensions ────────────────────────────────────────────────────────
_CHART_W, _CHART_H = 480, 220
_BAR_COLOR = (29, 78, 216)       # blue-700
_DONUT_COLORS = [
    (29, 78, 216), (15, 118, 110), (194, 65, 12),
    (124, 58, 237), (217, 119, 6), (4, 120, 87),
    (190, 18, 60), (3, 105, 161),
]
_FONT = None  # use Pillow default


def _bar_chart(labels: List[str], values: List[float], title: str = "") -> BytesIO:
    """Horizontal bar chart. Returns PNG bytes in a BytesIO buffer."""
    img = Image.new("RGB", (_CHART_W, _CHART_H), "white")
    draw = ImageDraw.Draw(img)
    if not values or max(values) == 0:
        draw.text((10, _CHART_H // 2), "Sin datos", fill=(150, 150, 150), font=_FONT)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

    pad_left, pad_right, pad_top, pad_bottom = 140, 20, 30, 20
    bar_area_w = _CHART_W - pad_left - pad_right
    bar_area_h = _CHART_H - pad_top - pad_bottom
    n = len(values)
    max_val = max(values)
    bar_h = max(8, bar_area_h // n - 6)

    if title:
        draw.text((pad_left, 6), title[:50], fill=(30, 30, 30), font=_FONT)

    for i, (label, val) in enumerate(zip(labels, values)):
        y = pad_top + i * (bar_area_h // n)
        bar_w = int(bar_area_w * val / max_val) if max_val else 0
        draw.rectangle([pad_left, y, pad_left + bar_w, y + bar_h], fill=_BAR_COLOR)
        short_label = str(label)[:20]
        draw.text((2, y + 1), short_label, fill=(30, 30, 30), font=_FONT)
        draw.text((pad_left + bar_w + 4, y + 1), str(round(val, 1)), fill=(80, 80, 80), font=_FONT)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _donut_chart(labels: List[str], values: List[float], title: str = "") -> BytesIO:
    """Donut chart. Returns PNG bytes in a BytesIO buffer."""
    img = Image.new("RGB", (_CHART_W, _CHART_H), "white")
    draw = ImageDraw.Draw(img)
    total = sum(values) or 1
    cx, cy, r_out, r_in = _CHART_H // 2, _CHART_H // 2, _CHART_H // 2 - 10, _CHART_H // 4

    if title:
        draw.text((_CHART_H + 10, 6), title[:30], fill=(30, 30, 30), font=_FONT)

    angle = -90.0
    for i, (label, val) in enumerate(zip(labels, values)):
        sweep = 360.0 * val / total
        color = _DONUT_COLORS[i % len(_DONUT_COLORS)]
        draw.pieslice([cx - r_out, cy - r_out, cx + r_out, cy + r_out],
                      start=angle, end=angle + sweep, fill=color)
        angle += sweep

    # Punch out center
    draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill="white")

    # Legend
    lx, ly = _CHART_H + 10, 30
    for i, (label, val) in enumerate(zip(labels, values)):
        color = _DONUT_COLORS[i % len(_DONUT_COLORS)]
        draw.rectangle([lx, ly + i * 18, lx + 12, ly + i * 18 + 12], fill=color)
        pct = f"{100 * val / total:.1f}%"
        draw.text((lx + 16, ly + i * 18), f"{str(label)[:18]} {pct}", fill=(30, 30, 30), font=_FONT)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _rl_image(buf: BytesIO, width: float = 4 * inch, height: float = 1.8 * inch) -> RLImage:
    """Wrap a PNG BytesIO as a ReportLab Image flowable."""
    return RLImage(buf, width=width, height=height)


def _question_export_columns(dashboard: Dict[str, Any]) -> List[Dict[str, str]]:
    columns: List[Dict[str, str]] = []
    for item in dashboard.get("question_report", []):
        question_id = str(item.get("question_id") or "").strip()
        if not question_id:
            continue
        label = str(item.get("question_title") or f"Pregunta {question_id}").strip()
        section = str(item.get("section_title") or "").strip()
        header = f"[{question_id}] {section} · {label}" if section else f"[{question_id}] {label}"
        columns.append({"question_id": question_id, "header": header})
    return columns


def _responses_export_dataframe(dashboard: Dict[str, Any]) -> pd.DataFrame:
    MAIN_columns = [
        "response_id",
        "respondent_name",
        "role",
        "department",
        "position",
        "company",
        "channel",
        "status",
        "completion_pct",
        "total_score",
        "started_at",
        "submitted_at",
    ]
    question_columns = _question_export_columns(dashboard)
    rows: List[Dict[str, Any]] = []
    for row in dashboard.get("responses_table", []):
        payload = {key: row.get(key, "") for key in MAIN_columns}
        answers = row.get("answers_json") or {}
        for item in question_columns:
            value = answers.get(item["question_id"])
            if isinstance(value, list):
                payload[item["header"]] = ", ".join(str(part) for part in value)
            else:
                payload[item["header"]] = value if value is not None else ""
        rows.append(payload)
    ordered_columns = MAIN_columns + [item["header"] for item in question_columns]
    return pd.DataFrame(rows, columns=ordered_columns)


def _results_frames(dashboard: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    summary_df = pd.DataFrame(
        [{"metric": key, "value": value} for key, value in (dashboard.get("summary") or {}).items()],
        columns=["metric", "value"],
    )
    questions_df = pd.DataFrame(
        [
            {
                "section_title": row.get("section_title"),
                "question_title": row.get("question_title"),
                "question_type": row.get("question_type"),
                "responses_count": row.get("responses_count"),
                "avg_score": row.get("avg_score"),
                "options_or_samples": str(row.get("options") or row.get("sample_answers") or row.get("word_cloud") or []),
            }
            for row in dashboard.get("question_report", [])
        ],
        columns=["section_title", "question_title", "question_type", "responses_count", "avg_score", "options_or_samples"],
    )
    segment_rows: List[Dict[str, Any]] = []
    for segment_type, rows in (dashboard.get("segment_report") or {}).items():
        for row in rows or []:
            segment_rows.append(
                {
                    "segment_type": segment_type,
                    "label": row.get("label"),
                    "segment": row.get("segment"),
                    "responses": row.get("responses"),
                    "completion_pct_avg": row.get("completion_pct_avg"),
                    "score_avg": row.get("score_avg"),
                }
            )
    segments_df = pd.DataFrame(
        segment_rows,
        columns=["segment_type", "label", "segment", "responses", "completion_pct_avg", "score_avg"],
    )
    return {
        "summary": summary_df,
        "questions": questions_df,
        "segments": segments_df,
        "responses": _responses_export_dataframe(dashboard),
    }


def export_results_csv(instance_id: int, tenant_id: str, dashboard: Optional[Dict[str, Any]] = None) -> str:
    dashboard = dashboard or get_results_dashboard(instance_id, tenant_id)
    output = StringIO()
    _results_frames(dashboard)["responses"].to_csv(output, index=False)
    return output.getvalue()


def export_results_excel(instance_id: int, tenant_id: str, dashboard: Optional[Dict[str, Any]] = None) -> bytes:
    dashboard = dashboard or get_results_dashboard(instance_id, tenant_id)
    frames = _results_frames(dashboard)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        frames["summary"].to_excel(writer, index=False, sheet_name="Resumen")
        frames["questions"].to_excel(writer, index=False, sheet_name="Preguntas")
        frames["segments"].to_excel(writer, index=False, sheet_name="Segmentos")
        frames["responses"].to_excel(writer, index=False, sheet_name="Respuestas")
        for sheet_name, ws in writer.sheets.items():
            ws.freeze_panes = "A2"
            for idx, column_cells in enumerate(ws.columns, start=1):
                values = [str(cell.value or "") for cell in column_cells[:100]]
                width = min(max((len(value) for value in values), default=12) + 2, 42)
                ws.column_dimensions[get_column_letter(idx)].width = width
    return buffer.getvalue()


def export_results_pdf(instance_id: int, tenant_id: str, dashboard: Optional[Dict[str, Any]] = None) -> bytes:
    dashboard = dashboard or get_results_dashboard(instance_id, tenant_id)
    frames = _results_frames(dashboard)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Encuesta: {dashboard.get('instance', {}).get('nombre', 'Resultados')}", styles["Title"]),
        Paragraph("Exportación PDF de resultados básicos", styles["Normal"]),
        Spacer(1, 12),
    ]
    applied_filters = dashboard.get("applied_filters") or {}
    active_filters = [
        f"Departamento: {applied_filters.get('department')}" if applied_filters.get("department") else "",
        f"Rol: {applied_filters.get('role')}" if applied_filters.get("role") else "",
        f"Empresa: {applied_filters.get('company')}" if applied_filters.get("company") else "",
        f"Comparativo por: {applied_filters.get('segment_by')}" if applied_filters.get("segment_by") else "",
    ]
    active_filters = [item for item in active_filters if item]
    if active_filters:
        story.extend([
            Paragraph("Filtros aplicados", styles["Heading2"]),
            Paragraph(" · ".join(active_filters), styles["Normal"]),
            Spacer(1, 12),
        ])

    summary_table = Table(
        [["Métrica", "Valor"]] + [
            [str(row["metric"]), str(row["value"] if row["value"] is not None else "")]
            for _, row in frames["summary"].iterrows()
        ],
        repeatRows=1,
    )
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f8fafc")]),
        ])
    )
    story.extend([Paragraph("Resumen", styles["Heading2"]), summary_table, Spacer(1, 12)])

    # ── NPS / CSAT / CES donut charts ───────────────────────────────────────
    summary = dashboard.get("summary") or {}
    nps = float(summary.get("nps_score") or 0)
    csat = float(summary.get("csat_score") or 0)
    ces = float(summary.get("ces_score") or 0)
    if any([nps, csat, ces]):
        donut_labels = ["NPS", "CSAT", "CES"]
        donut_values = [max(nps, 0), max(csat, 0), max(ces, 0)]
        donut_buf = _donut_chart(donut_labels, donut_values, "Métricas CX")
        story.extend([
            Paragraph("Métricas de experiencia", styles["Heading2"]),
            _rl_image(donut_buf, width=3 * inch, height=1.6 * inch),
            Spacer(1, 8),
        ])

    # ── Option distribution bar charts per question ──────────────────────────
    story.append(Paragraph("Preguntas", styles["Heading2"]))
    _CHOICE_QTYPES = {
        "single_choice", "live_poll_single_choice", "quiz_single_choice",
        "yes_no", "multiple_choice", "scale_1_5", "live_scale_1_5",
        "nps_0_10", "dropdown", "image_choice", "true_false",
    }
    question_rows = [["Sección", "Pregunta", "Tipo", "Resp.", "Score"]]
    for item in (dashboard.get("question_report") or [])[:20]:
        question_rows.append([
            str(item.get("section_title") or ""),
            str(item.get("question_title") or ""),
            str(item.get("question_type") or ""),
            str(item.get("responses_count") or 0),
            str(item.get("avg_score") if item.get("avg_score") is not None else ""),
        ])
        opts = item.get("options") or []
        if item.get("question_type") in _CHOICE_QTYPES and opts:
            opt_labels = [str(o.get("label") or o.get("value") or "")[:20] for o in opts]
            opt_values = [float(o.get("count") or 0) for o in opts]
            if any(v > 0 for v in opt_values):
                chart_buf = _bar_chart(
                    opt_labels, opt_values,
                    str(item.get("question_title") or "")[:40],
                )
                story.append(_rl_image(chart_buf, width=4 * inch, height=1.6 * inch))
    question_table = Table(question_rows, repeatRows=1, colWidths=[110, 200, 90, 50, 60])
    question_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.extend([question_table, Spacer(1, 12)])

    if not frames["segments"].empty:
        seg_df = frames["segments"]
        # Bar chart: responses by segment (department)
        dept_df = seg_df[seg_df["segment_type"] == "department"].head(12)
        if not dept_df.empty:
            seg_buf = _bar_chart(
                dept_df["segment"].tolist(),
                dept_df["responses"].astype(float).tolist(),
                "Respuestas por departamento",
            )
            story.extend([
                Paragraph("Segmentos", styles["Heading2"]),
                _rl_image(seg_buf, width=4 * inch, height=1.8 * inch),
            ])
        seg_rows = [["Tipo", "Etiqueta", "Segmento", "Respuestas", "Finalización", "Score"]]
        for _, row in seg_df.head(20).iterrows():
            seg_rows.append([
                str(row["segment_type"] or ""),
                str(row["label"] or ""),
                str(row["segment"] or ""),
                str(row["responses"] or 0),
                str(row["completion_pct_avg"] if row["completion_pct_avg"] is not None else ""),
                str(row["score_avg"] if row["score_avg"] is not None else ""),
            ])
        segment_table = Table(seg_rows, repeatRows=1, colWidths=[90, 90, 160, 70, 90, 70])
        segment_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c2410c")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.extend([segment_table, Spacer(1, 8)])
    comparison_rows = dashboard.get("comparison_report") or []
    if comparison_rows:
        comparison_table = Table(
            [["Segmento", "Respuestas", "Finalización", "Score", "NPS", "CSAT", "CES"]] + [
                [
                    str(row.get("segment") or ""),
                    str(row.get("responses") or 0),
                    str(row.get("completion_pct_avg") if row.get("completion_pct_avg") is not None else ""),
                    str(row.get("total_score_avg") if row.get("total_score_avg") is not None else ""),
                    str(row.get("nps_score") if row.get("nps_score") is not None else ""),
                    str(row.get("csat_score") if row.get("csat_score") is not None else ""),
                    str(row.get("ces_score") if row.get("ces_score") is not None else ""),
                ]
                for row in comparison_rows[:20]
            ],
            repeatRows=1,
            colWidths=[180, 70, 90, 70, 60, 60, 60],
        )
        comparison_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ])
        )
        story.extend([Spacer(1, 12), Paragraph("Comparativo", styles["Heading2"]), comparison_table])

    doc.build(story)
    return buffer.getvalue()
