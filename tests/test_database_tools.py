from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

from fastapi_modulo.core import db as core_db
from fastapi_modulo.modulos_sipet.identidad_institucional.controladores import identidad_institucional
from fastapi_modulo.modulos_sipet.modulo_base.controladores import settings


def _create_sqlite(path: Path, marker: str) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS sample (id INTEGER PRIMARY KEY, marker TEXT NOT NULL)")
        conn.execute("DELETE FROM sample")
        conn.execute("INSERT INTO sample(marker) VALUES (?)", (marker,))
        conn.commit()
    finally:
        conn.close()


def _read_marker(path: Path) -> str | None:
    conn = sqlite3.connect(path)
    try:
        row = conn.execute("SELECT marker FROM sample LIMIT 1").fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def test_database_tools_support_redirect_export_and_import_backup(tmp_path, monkeypatch) -> None:
    active_db = tmp_path / "active.db"
    import_db = tmp_path / "imported.db"
    backup_db = Path(f"{active_db}.bak")
    _create_sqlite(active_db, "ORIGINAL")
    _create_sqlite(import_db, "IMPORTED")

    class FakeRuntime:
        @staticmethod
        def _get_request_database_info(request=None):
            return {
                "engine": "sqlite",
                "path": str(active_db),
                "host": "test.local",
                "name": "active",
                "url": f"sqlite:///{active_db}",
            }

        @staticmethod
        def _render_database_tools_page(request):
            return HTMLResponse("base de datos")

    monkeypatch.setattr(settings, "_runtime_helpers", lambda: FakeRuntime)
    monkeypatch.setattr(settings, "require_admin_or_superadmin", lambda request: None)
    monkeypatch.setattr(identidad_institucional, "_require_empresa_permission", lambda request, permission: None)
    monkeypatch.setattr(core_db, "dispose_engine_for_host", lambda host=None: None)

    app = FastAPI()

    @app.get("/empresa/MAIN-datos", response_class=HTMLResponse)
    def empresa_main_datos(request: Request):
        return identidad_institucional.empresa_main_datos_page(request)

    @app.get("/empresa/base-datos", response_class=HTMLResponse)
    def empresa_base_datos(request: Request):
        return settings.empresa_base_datos_page(request)

    @app.get("/empresa/base-datos/exportar")
    def empresa_base_datos_exportar(request: Request):
        return settings.empresa_base_datos_exportar(request)

    @app.post("/empresa/base-datos/importar", response_class=HTMLResponse)
    async def empresa_base_datos_importar(request: Request):
        form = await request.form()
        return await settings.empresa_base_datos_importar(request, form["db_file"])

    client = TestClient(app)

    redirect_response = client.get("/empresa/MAIN-datos", follow_redirects=False)
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "/empresa/base-datos"

    active_bytes_before_import = active_db.read_bytes()
    export_response = client.get("/empresa/base-datos/exportar")
    assert export_response.status_code == 200
    assert export_response.content == active_bytes_before_import

    with import_db.open("rb") as handle:
        import_response = client.post(
            "/empresa/base-datos/importar",
            files={"db_file": ("imported.db", handle, "application/octet-stream")},
            follow_redirects=False,
        )

    assert import_response.status_code == 303
    assert import_response.headers["location"] == "/empresa/base-datos?status=ok&msg=Base%20de%20datos%20importada%20correctamente"
    assert _read_marker(active_db) == "IMPORTED"
    assert backup_db.exists()
    assert _read_marker(backup_db) == "ORIGINAL"
