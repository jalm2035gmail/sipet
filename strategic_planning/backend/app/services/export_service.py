import io
from datetime import datetime
from typing import Any, Dict

from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

from app.models.strategic.plan import StrategicPlan


class ExportService:
    """Servicio para exportar planes estratégicos a Excel o PDF."""

    @staticmethod
    def export_plan_to_excel(plan: StrategicPlan) -> bytes:
        wb = Workbook()
        sheet = wb.active
        sheet.title = "Plan Estratégico"

        rows = [
            ("Campo", "Valor"),
            ("ID", plan.id),
            ("Nombre", plan.name),
            ("Código", plan.code),
            ("Descripción", plan.description),
            ("Versión", plan.version),
            ("Inicio", plan.start_date),
            ("Fin", plan.end_date),
            ("Visión", plan.vision),
            ("Misión", plan.mission),
            ("Valores", ", ".join(plan.values or [])),
            ("Estado", plan.status.value if plan.status else ""),
            ("Departamento", plan.department.name if plan.department else ""),
            ("Progreso", f"{plan.get_progress()}%"),
            ("Días Restantes", plan.get_days_remaining()),
        ]

        for row in rows:
            sheet.append(row)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def export_plan_to_pdf(plan: StrategicPlan) -> bytes:
        buffer = io.BytesIO()
        canvas = Canvas(buffer, pagesize=letter)
        width, height = letter
        margin = 40
        y = height - margin
        line_height = 16

        header = f"Plan Estratégico | {plan.name}"
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(margin, y, header)
        y -= line_height * 2

        canvas.setFont("Helvetica", 11)
        for key, value in ExportService._plan_summary(plan).items():
            if y < margin:
                canvas.showPage()
                y = height - margin
                canvas.setFont("Helvetica", 11)
            canvas.drawString(margin, y, f"{key}: {value}")
            y -= line_height

        canvas.save()
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def _plan_summary(plan: StrategicPlan) -> Dict[str, Any]:
        return {
            "ID": plan.id,
            "Código": plan.code,
            "Inicio": plan.start_date,
            "Fin": plan.end_date,
            "Estado": plan.status.value if plan.status else "",
            "Progreso": f"{plan.get_progress()}%",
            "Días restantes": plan.get_days_remaining(),
            "Departamento": plan.department.name if plan.department else "",
            "Fecha Exportación": datetime.utcnow().isoformat(),
        }
