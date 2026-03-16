from __future__ import annotations

from io import BytesIO

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def build_dashboard_report_payload(summary: dict) -> dict:
    return {
        "title": "Reporte de mi tablero",
        "summary": summary,
    }


def generate_dashboard_pdf(user_id: str, payload: dict) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    pdf.setTitle(f"dashboard_{user_id}")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(48, height - 48, "Reporte de mi tablero")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(48, height - 72, f"Usuario: {user_id}")
    pdf.drawString(48, height - 88, f"Modulos visibles: {payload.get('metrics', {}).get('total_modules', 0)}")
    pdf.drawString(48, height - 104, f"Widgets: {len(payload.get('widgets', []))}")
    pdf.drawString(48, height - 120, "Accesos principales:")
    y = height - 144
    for item in payload.get("modules", [])[:12]:
        pdf.drawString(64, y, f"- {item.get('label', 'Modulo')} -> {item.get('route', '')}")
        y -= 16
        if y < 72:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y = height - 48
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def generate_dashboard_excel(user_id: str, payload: dict) -> bytes:
    buffer = BytesIO()
    modules_df = pd.DataFrame(payload.get("modules", []))
    apps_usage_df = pd.DataFrame(payload.get("usage_stats", {}).get("most_used_apps", []))
    screens_usage_df = pd.DataFrame(payload.get("usage_stats", {}).get("most_used_screens", []))
    summary_df = pd.DataFrame(
        [
            {
                "user_id": user_id,
                "total_modules": payload.get("metrics", {}).get("total_modules", 0),
                "total_widgets": len(payload.get("widgets", [])),
                "stats_status": payload.get("stats_job", {}).get("status", ""),
            }
        ]
    )
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        modules_df.to_excel(writer, sheet_name="modules", index=False)
        apps_usage_df.to_excel(writer, sheet_name="apps_usage", index=False)
        screens_usage_df.to_excel(writer, sheet_name="screens_usage", index=False)
    return buffer.getvalue()
