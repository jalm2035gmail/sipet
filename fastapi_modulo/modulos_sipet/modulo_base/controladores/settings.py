from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from starlette.background import BackgroundTask

from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_admin_or_superadmin

router = APIRouter()


def _runtime_helpers():
    from fastapi_modulo.modulos_sipet.modulo_base import runtime_app

    return runtime_app


def _current_database_url(request: Request) -> str:
    from fastapi_modulo.core import db as core_db

    db_info = _runtime_helpers()._get_request_database_info(request)
    host = str(db_info.get("host") or "").strip()
    return core_db.get_dataMAIN_url_for_host(host or None)


def _postgres_connection_parts(db_url: str) -> dict[str, str]:
    parsed = urlparse(str(db_url or "").strip())
    return {
        "host": str(parsed.hostname or "127.0.0.1"),
        "port": str(parsed.port or 5432),
        "user": unquote(str(parsed.username or "")),
        "password": unquote(str(parsed.password or "")),
        "database": str(parsed.path or "").lstrip("/"),
    }


def _unlink_safely(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


def _ensure_command_available(command_name: str) -> None:
    import shutil

    if shutil.which(command_name):
        return
    raise HTTPException(status_code=500, detail=f"No se encontró el comando requerido: {command_name}")


@router.get("/ajustes/configuracion", response_class=HTMLResponse)
def ajustes_configuracion_page(request: Request):
    require_admin_or_superadmin(request)
    return _runtime_helpers()._render_ajustes_configuracion_page(request)


@router.get("/configuracion", response_class=HTMLResponse)
@router.get("/configuracion/", response_class=HTMLResponse)
def configuracion_legacy_redirect(request: Request):
    require_admin_or_superadmin(request)
    return RedirectResponse(url="/ajustes/configuracion", status_code=307)


@router.get("/api/ajustes/actualizacion")
def ajustes_actualizacion_estado(request: Request):
    require_admin_or_superadmin(request)
    runtime = _runtime_helpers()
    context = runtime._get_update_context(request)
    return {"success": True, **runtime._snapshot_update_state(context)}


@router.post("/api/ajustes/actualizacion/verificar")
def ajustes_actualizacion_verificar(request: Request):
    require_admin_or_superadmin(request)
    runtime = _runtime_helpers()
    context = runtime._get_update_context(request)
    try:
        manifest = runtime._fetch_update_manifest(context["manifest_url"])
        manifest_info = runtime._validate_update_manifest(context, manifest)
        snapshot = {
            "checked_at": datetime.utcnow().isoformat(),
            "version": manifest_info["version"],
            "strategy": manifest_info["strategy"],
            "branch": manifest_info["branch"],
            "channel": context["channel"],
            "notes": manifest_info["notes"],
            "manifest_url": context["manifest_url"],
        }
        runtime._write_json_file(context["files"]["manifest"], snapshot)
        runtime._append_update_history(
            context["host"],
            {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "checked",
                "target_version": manifest_info["version"],
            },
        )
        context = runtime._get_update_context(request)
        return {"success": True, **runtime._snapshot_update_state(context, manifest_info)}
    except Exception as exc:
        runtime._append_update_history(
            context["host"],
            {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "check_error",
                "target_version": "",
                "error": str(exc),
            },
        )
        return JSONResponse({"success": False, "error": str(exc)}, status_code=400)


@router.post("/api/ajustes/actualizacion/aplicar")
def ajustes_actualizacion_aplicar(request: Request):
    require_admin_or_superadmin(request)
    runtime = _runtime_helpers()
    context = runtime._get_update_context(request)
    try:
        manifest = runtime._fetch_update_manifest(context["manifest_url"])
        manifest_info = runtime._validate_update_manifest(context, manifest)
        if not manifest_info["update_available"]:
            return {"success": True, **runtime._snapshot_update_state(context, manifest_info)}
        job_payload = runtime._start_update_job(context, manifest_info)
        context = runtime._get_update_context(request)
        state = runtime._snapshot_update_state(context, manifest_info)
        state["last_job"] = job_payload
        return {"success": True, **state}
    except Exception as exc:
        runtime._append_update_history(
            context["host"],
            {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "start_error",
                "target_version": "",
                "error": str(exc),
            },
        )
        return JSONResponse({"success": False, "error": str(exc)}, status_code=400)


@router.get("/empresa/base-datos", response_class=HTMLResponse)
def empresa_base_datos_page(request: Request):
    require_admin_or_superadmin(request)
    return _runtime_helpers()._render_database_tools_page(request)


@router.get("/empresa/base-datos/exportar")
def empresa_base_datos_exportar(request: Request):
    require_admin_or_superadmin(request)
    db_info = _runtime_helpers()._get_request_database_info(request)
    if db_info["engine"] == "sqlite" and db_info["path"]:
        db_path = os.path.abspath(db_info["path"])
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="No se encontró el archivo de base de datos")
        filename = f"sipet_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
        return FileResponse(db_path, media_type="application/octet-stream", filename=filename)

    if db_info["engine"] == "postgresql":
        _ensure_command_available("pg_dump")
        conn = _postgres_connection_parts(_current_database_url(request))
        if not conn["database"] or not conn["user"]:
            raise HTTPException(status_code=400, detail="Configuración PostgreSQL incompleta")
        fd, dump_path = tempfile.mkstemp(prefix="sipet_backup_", suffix=".sql")
        os.close(fd)
        env = os.environ.copy()
        if conn["password"]:
            env["PGPASSWORD"] = conn["password"]
        try:
            subprocess.run(
                [
                    "pg_dump",
                    "-h",
                    conn["host"],
                    "-p",
                    conn["port"],
                    "-U",
                    conn["user"],
                    "--clean",
                    "--if-exists",
                    "--no-owner",
                    "--no-privileges",
                    "--format=plain",
                    "--file",
                    dump_path,
                    conn["database"],
                ],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            _unlink_safely(dump_path)
            raise HTTPException(status_code=500, detail=(exc.stderr or exc.stdout or "No se pudo exportar PostgreSQL").strip())
        filename = f"sipet_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql"
        return FileResponse(
            dump_path,
            media_type="application/sql",
            filename=filename,
            background=BackgroundTask(_unlink_safely, dump_path),
        )

    raise HTTPException(status_code=400, detail="Exportación no disponible para este motor de base de datos")


@router.post("/empresa/base-datos/importar", response_class=HTMLResponse)
async def empresa_base_datos_importar(request: Request, db_file: UploadFile = File(...)):
    from urllib.parse import quote_plus

    from fastapi_modulo.core import db as core_db

    require_admin_or_superadmin(request)
    db_info = _runtime_helpers()._get_request_database_info(request)
    ext = os.path.splitext((db_file.filename or "").lower())[1]
    raw = await db_file.read()
    if not raw:
        return RedirectResponse(
            url="/empresa/base-datos?status=error&msg=Archivo%20vacío",
            status_code=303,
        )
    if db_info["engine"] == "sqlite" and db_info["path"]:
        if ext not in {".db", ".sqlite", ".sqlite3"}:
            return RedirectResponse(
                url="/empresa/base-datos?status=error&msg=Archivo%20inválido.%20Usa%20.db%2C%20.sqlite%20o%20.sqlite3",
                status_code=303,
            )
        db_path = os.path.abspath(db_info["path"])
        tmp_path = f"{db_path}.upload.tmp"
        backup_path = f"{db_path}.bak"
        try:
            with open(tmp_path, "wb") as fh:
                fh.write(raw)
            with sqlite3.connect(tmp_path) as conn:
                conn.execute("PRAGMA schema_version;").fetchone()

            core_db.dispose_engine_for_host(db_info["host"])

            if os.path.exists(db_path):
                import shutil

                shutil.copy2(db_path, backup_path)
            os.replace(tmp_path, db_path)
            return RedirectResponse(
                url="/empresa/base-datos?status=ok&msg=Base%20de%20datos%20importada%20correctamente",
                status_code=303,
            )
        except Exception as exc:
            if os.path.exists(tmp_path):
                _unlink_safely(tmp_path)
            return RedirectResponse(
                url=f"/empresa/base-datos?status=error&msg={quote_plus(str(exc) or 'Error al importar base de datos')}",
                status_code=303,
            )

    if db_info["engine"] == "postgresql":
        if ext not in {".sql"}:
            return RedirectResponse(
                url="/empresa/base-datos?status=error&msg=Archivo%20inválido.%20Usa%20.sql%20para%20PostgreSQL",
                status_code=303,
            )
        _ensure_command_available("psql")
        conn = _postgres_connection_parts(_current_database_url(request))
        if not conn["database"] or not conn["user"]:
            return RedirectResponse(
                url="/empresa/base-datos?status=error&msg=Configuración%20PostgreSQL%20incompleta",
                status_code=303,
            )
        tmp_file = tempfile.NamedTemporaryFile(prefix="sipet_import_", suffix=".sql", delete=False)
        tmp_path = tmp_file.name
        try:
            tmp_file.write(raw)
            tmp_file.close()
            core_db.dispose_engine_for_host(db_info["host"])
            env = os.environ.copy()
            if conn["password"]:
                env["PGPASSWORD"] = conn["password"]
            subprocess.run(
                [
                    "psql",
                    "-h",
                    conn["host"],
                    "-p",
                    conn["port"],
                    "-U",
                    conn["user"],
                    "-d",
                    conn["database"],
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-f",
                    tmp_path,
                ],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )
            return RedirectResponse(
                url="/empresa/base-datos?status=ok&msg=Base%20de%20datos%20importada%20correctamente",
                status_code=303,
            )
        except subprocess.CalledProcessError as exc:
            error = (exc.stderr or exc.stdout or "Error al importar base de datos").strip()
            return RedirectResponse(
                url=f"/empresa/base-datos?status=error&msg={quote_plus(error)}",
                status_code=303,
            )
        except Exception as exc:
            return RedirectResponse(
                url=f"/empresa/base-datos?status=error&msg={quote_plus(str(exc) or 'Error al importar base de datos')}",
                status_code=303,
            )
        finally:
            _unlink_safely(tmp_path)

    return RedirectResponse(
        url="/empresa/base-datos?status=error&msg=Importación%20no%20disponible%20para%20este%20motor",
        status_code=303,
    )


__all__ = ["router"]
