import logging
from app.workers.celery_app import celery_app
from app.services import report_service
import pandas as pd

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.generate_pdf", max_retries=3)
def generate_pdf_task(self, title: str, sections: list[dict], output_path: str):
    try:
        report_service.generate_pdf(title=title, sections=sections, output_path=output_path)
        logger.info("PDF task complete: %s", output_path)
        return {"status": "ok", "path": output_path}
    except Exception as exc:
        logger.error("PDF task failed: %s", exc)
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(bind=True, name="tasks.generate_excel", max_retries=3)
def generate_excel_task(self, sheets_data: list[dict], output_path: str):
    """sheets_data: [{"name": str, "records": [...]}]"""
    try:
        sheets = [
            {"name": s["name"], "dataframe": pd.DataFrame(s["records"])}
            for s in sheets_data
        ]
        report_service.generate_excel(sheets=sheets, output_path=output_path)
        logger.info("Excel task complete: %s", output_path)
        return {"status": "ok", "path": output_path}
    except Exception as exc:
        logger.error("Excel task failed: %s", exc)
        raise self.retry(exc=exc, countdown=10)
