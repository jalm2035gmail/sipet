import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any
import pandas as pd

from app.api.deps import get_current_active_user
from app.services import report_service

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class TableSection(BaseModel):
    heading: str | None = None
    body: str | None = None
    table: list[list[Any]] | None = None


class PDFRequest(BaseModel):
    title: str
    sections: list[TableSection]


class ExcelSheetRequest(BaseModel):
    name: str
    records: list[dict]


class ExcelRequest(BaseModel):
    sheets: list[ExcelSheetRequest]


# ── PDF ───────────────────────────────────────────────────────────────────────

@router.post("/pdf")
def generate_pdf(
    body: PDFRequest,
    current_user=Depends(get_current_active_user),
):
    try:
        sections = [s.model_dump(exclude_none=True) for s in body.sections]
        pdf_bytes = report_service.generate_pdf(title=body.title, sections=sections)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{body.title}.pdf"'},
    )


@router.post("/pdf/from-excel")
async def pdf_from_excel(
    title: str = "Report",
    file: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
):
    """Convierte un Excel subido directamente a PDF."""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx / .xls files accepted")

    try:
        contents = await file.read()
        df = report_service.excel_to_dataframe(contents)
        pdf_bytes = report_service.dataframe_to_pdf(df, title=title)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{title}.pdf"'},
    )


# ── Excel ─────────────────────────────────────────────────────────────────────

@router.post("/excel")
def generate_excel(
    body: ExcelRequest,
    current_user=Depends(get_current_active_user),
):
    try:
        sheets = [
            {"name": s.name, "dataframe": pd.DataFrame(s.records)}
            for s in body.sheets
        ]
        excel_bytes = report_service.generate_excel(sheets=sheets)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="report.xlsx"'},
    )


@router.post("/excel/upload")
async def read_excel(
    file: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
):
    """Lee un Excel y devuelve los datos como JSON."""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx / .xls files accepted")

    try:
        contents = await file.read()
        df = report_service.excel_to_dataframe(contents)
        return {"rows": len(df), "columns": list(df.columns), "data": df.to_dict(orient="records")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
