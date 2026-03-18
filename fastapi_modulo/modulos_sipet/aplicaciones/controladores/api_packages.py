from __future__ import annotations

import io
import os

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

from fastapi_modulo.modulos_sipet.aplicaciones.controladores.dependencies import (
    APPLICATIONS_PERMISSION_AUDIT_VIEW,
    APPLICATIONS_PERMISSION_PACKAGES_UPLOAD,
    APPLICATIONS_PERMISSION_VIEW,
    require_applications_permission,
    request_actor_context,
)
from fastapi_modulo.modulos_sipet.aplicaciones.modelos.schemas import ModuleRollbackResponse, ModuleUploadResponse
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.image_branding_service import build_module_image_response
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.package_service import (
    get_module_image_path,
    import_module_package,
    rollback_module_package_job,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.security_service import (
    SENSITIVE_ACTION_PACKAGE_ROLLBACK,
    SENSITIVE_ACTION_PACKAGE_UPLOAD,
    verify_sensitive_action_token,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.task_queue_service import queue_task
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.export_service import export_catalog_xlsx
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.report_service import generate_module_audit_pdf, get_report_filename
from fastapi_modulo.core.module_registry import MODULES_BY_KEY

router = APIRouter()


@router.post("/api/system/modules/{module_key}/upload", response_model=ModuleUploadResponse, include_in_schema=False)
@router.post("/api/aplicaciones/modulos/{module_key}/upload", response_model=ModuleUploadResponse)
async def aplicaciones_upload(
    module_key: str,
    request: Request,
    package: UploadFile = File(...),
    dry_run: bool = Form(True),
    expected_checksum: str = Form(""),
    challenge_token: str = Form(""),
):
    require_applications_permission(request, APPLICATIONS_PERMISSION_PACKAGES_UPLOAD)
    actor = request_actor_context(request)
    filename = str(package.filename or "").strip()
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Debes subir un archivo .zip.")
    if not dry_run:
        if not challenge_token:
            raise HTTPException(status_code=400, detail="Debes confirmar la aplicacion del ZIP.")
        verify_sensitive_action_token(
            token=challenge_token,
            username=actor["user_id"],
            action=SENSITIVE_ACTION_PACKAGE_UPLOAD,
            module_key=module_key,
        )
    return await import_module_package(
        module_key,
        package,
        dry_run=dry_run,
        expected_checksum=expected_checksum,
        user_id=actor["user_id"],
        tenant_id=actor["tenant_id"],
        ip=actor["ip"],
    )


@router.post("/api/system/modules/{module_key}/rollback", response_model=ModuleRollbackResponse, include_in_schema=False)
@router.post("/api/aplicaciones/modulos/{module_key}/rollback", response_model=ModuleRollbackResponse)
def aplicaciones_rollback(
    module_key: str,
    request: Request,
    challenge_token: str = Form(...),
):
    require_applications_permission(request, APPLICATIONS_PERMISSION_PACKAGES_UPLOAD)
    actor = request_actor_context(request)
    verify_sensitive_action_token(
        token=challenge_token,
        username=actor["user_id"],
        action=SENSITIVE_ACTION_PACKAGE_ROLLBACK,
        module_key=module_key,
    )
    queued = queue_task(
        "package_rollback",
        {
            "module_key": module_key,
            "user_id": actor["user_id"],
            "tenant_id": actor["tenant_id"] or "",
            "ip": actor["ip"] or "",
        },
    )
    if queued["status"] == "inline":
        return rollback_module_package_job(
            module_key=module_key,
            user_id=actor["user_id"],
            tenant_id=actor["tenant_id"],
            ip=actor["ip"],
        )
    return {
        "module_key": module_key,
        "status": "queued",
        "task_id": str(queued["task_id"]),
        "task_name": "package_rollback",
        "restored_files": 0,
        "snapshot_path": "",
    }


@router.get("/api/system/modules/assets/{module_key}/{filename}")
@router.get("/api/aplicaciones/assets/{module_key}/{filename}")
def aplicaciones_asset(
    module_key: str,
    filename: str,
    request: Request,
    variant: str = Query("card"),
):
    require_applications_permission(request, APPLICATIONS_PERMISSION_VIEW)
    image_path = get_module_image_path(str(module_key or "").strip())
    if image_path and filename == os.path.basename(image_path):
        return build_module_image_response(module_key, filename, variant=variant)
    definition = MODULES_BY_KEY.get(str(module_key or "").strip())
    label = str(getattr(definition, "label", "") or getattr(definition, "name", "") or module_key)
    if filename == "preview.png":
        return build_module_image_response(module_key, filename, label=label, variant=variant)
    raise HTTPException(status_code=404, detail="Recurso no encontrado")


@router.get("/api/aplicaciones/modulos/export", summary="Exportar catálogo de módulos a Excel")
def aplicaciones_export(request: Request):
    require_applications_permission(request, APPLICATIONS_PERMISSION_VIEW)
    buffer = export_catalog_xlsx()
    headers = {"Content-Disposition": "attachment; filename=catalogo_modulos.xlsx"}
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/api/aplicaciones/modulos/{module_key}/reporte", summary="Reporte PDF de auditoría de un módulo")
def aplicaciones_module_report(module_key: str, request: Request):
    require_applications_permission(request, APPLICATIONS_PERMISSION_AUDIT_VIEW)
    pdf_bytes = generate_module_audit_pdf(module_key)
    filename = get_report_filename(module_key)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


__all__ = ["router"]
