from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import inspect, text

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.database_router import can_connect_current_database
from fastapi_modulo.core.module_registry import get_active_module_keys
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_superadmin

router = APIRouter()
SERVER_PANEL_ENABLED = (os.environ.get("ENABLE_SERVER_PANEL") or "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
DEFAULT_LOG_FILE = (os.environ.get("LOG_FILE") or "uvicorn.log").strip() or "uvicorn.log"
KEY_TABLES = (
    "users",
    "roles",
    "colores",
    "web_user_session",
    "web_login_attempt",
    "web_security_event",
)


def _ensure_enabled(request: Request) -> None:
    if not SERVER_PANEL_ENABLED:
        raise HTTPException(status_code=404, detail="Panel deshabilitado")
    require_superadmin(request)


def _tail_log_lines(path: str, max_lines: int = 150) -> list[str]:
    log_path = Path(path)
    if not log_path.exists() or not log_path.is_file():
        return []
    try:
        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    return lines[-max(1, int(max_lines)) :]


def _database_snapshot() -> dict[str, Any]:
    db_info = core_db.get_current_database_info()
    ok, error = can_connect_current_database()
    table_status: dict[str, bool] = {name: False for name in KEY_TABLES}
    probe_error = ""
    if ok:
        try:
            inspector = inspect(core_db.get_current_engine())
            available = set(inspector.get_table_names())
            for table_name in KEY_TABLES:
                table_status[table_name] = table_name in available
        except Exception as exc:
            probe_error = str(exc)
    return {
        "connected": ok,
        "error": str(error or probe_error or ""),
        "info": db_info,
        "tables": table_status,
    }


def _runtime_snapshot(request: Request) -> dict[str, Any]:
    app_state = getattr(request.app, "state", None)
    return {
        "server_panel_enabled": SERVER_PANEL_ENABLED,
        "environment": (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower(),
        "host": core_db.get_request_host() or "",
        "database_setup_required": bool(getattr(app_state, "database_setup_required", False)),
        "database_setup_error": str(getattr(app_state, "database_setup_error", "") or ""),
        "core_schema_initialized": bool(getattr(app_state, "core_schema_initialized", False)),
        "startup_routers_registered": bool(getattr(app_state, "startup_routers_registered", False)),
        "late_routers_registered": bool(getattr(app_state, "late_routers_registered", False)),
        "active_modules": list(get_active_module_keys()),
    }


def _health_snapshot() -> dict[str, Any]:
    payload = {"status": "ok"}
    try:
        with core_db.get_current_engine().connect() as connection:
            payload["database_select_1"] = bool(connection.execute(text("SELECT 1")).scalar())
    except Exception as exc:
        payload["status"] = "degraded"
        payload["database_select_1"] = False
        payload["database_error"] = str(exc)
    return payload


def _page_content() -> str:
    return """
<section style="display:grid;gap:20px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;">
    <div>
      <h1 style="margin:0;font-size:2rem;font-weight:800;color:var(--text);">Panel del servidor</h1>
      <p style="margin:6px 0 0;color:var(--muted);">Estado de runtime, base de datos, salud y logs recientes.</p>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <button id="server-admin-refresh" class="db-btn" type="button" style="width:auto;padding:10px 18px;">Refrescar runtime</button>
      <button id="server-admin-bootstrap" class="db-btn" type="button" style="width:auto;padding:10px 18px;">Bootstrap esquema</button>
    </div>
  </div>

  <div id="server-admin-msg" style="display:none;padding:12px 14px;border-radius:12px;background:#f8fafc;border:1px solid var(--line);font-size:.9rem;"></div>

  <div class="two-col" style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;">
    <div style="background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;">
      <h2 style="margin:0 0 12px;font-size:1.05rem;">Runtime</h2>
      <div id="server-admin-runtime" style="display:grid;gap:8px;"></div>
    </div>
    <div style="background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;">
      <h2 style="margin:0 0 12px;font-size:1.05rem;">Salud</h2>
      <div id="server-admin-health" style="display:grid;gap:8px;"></div>
    </div>
  </div>

  <div style="background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;">
    <h2 style="margin:0 0 12px;font-size:1.05rem;">Base de datos</h2>
    <div id="server-admin-db" style="display:grid;gap:8px;"></div>
    <div id="server-admin-tables" style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:16px;"></div>
  </div>

  <div style="background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;">
    <h2 style="margin:0 0 12px;font-size:1.05rem;">Logs recientes</h2>
    <pre id="server-admin-logs" style="margin:0;background:#0f172a;color:#e2e8f0;padding:16px;border-radius:14px;overflow:auto;max-height:420px;font-size:.82rem;line-height:1.45;"></pre>
  </div>
</section>
<script>
(() => {
  const $ = (id) => document.getElementById(id);
  const t = (value) => String(value ?? '');
  const esc = (value) => t(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');

  const showMsg = (text, isError = false) => {
    const el = $('server-admin-msg');
    el.style.display = text ? '' : 'none';
    el.textContent = text || '';
    el.style.color = isError ? '#b42318' : '#166534';
    el.style.borderColor = isError ? '#fecaca' : '#bbf7d0';
    el.style.background = isError ? '#fff7f7' : '#f0fdf4';
  };

  const kv = (label, value) => `<div style="display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid var(--line);padding:8px 0;">
    <strong style="font-size:.88rem;">${esc(label)}</strong><span style="color:var(--muted);font-size:.88rem;word-break:break-all;text-align:right;">${esc(value)}</span>
  </div>`;

  const render = (payload) => {
    const runtime = payload.runtime || {};
    const health = payload.health || {};
    const database = payload.database || {};
    $('server-admin-runtime').innerHTML = [
      kv('Entorno', runtime.environment || ''),
      kv('Host', runtime.host || ''),
      kv('Setup requerido', runtime.database_setup_required ? 'si' : 'no'),
      kv('Error setup', runtime.database_setup_error || ''),
      kv('Core schema', runtime.core_schema_initialized ? 'ok' : 'pendiente'),
      kv('Routers startup', runtime.startup_routers_registered ? 'ok' : 'pendiente'),
      kv('Routers late', runtime.late_routers_registered ? 'ok' : 'pendiente'),
      kv('Modulos activos', (runtime.active_modules || []).join(', ')),
    ].join('');
    $('server-admin-health').innerHTML = [
      kv('Estado', health.status || ''),
      kv('SELECT 1', health.database_select_1 ? 'ok' : 'fallo'),
      kv('Error BD', health.database_error || ''),
    ].join('');
    const info = database.info || {};
    $('server-admin-db').innerHTML = [
      kv('Conectada', database.connected ? 'si' : 'no'),
      kv('Engine', info.engine || ''),
      kv('Nombre', info.name || ''),
      kv('Host', info.host || ''),
      kv('Ruta/URL', info.path || info.url || ''),
      kv('Error', database.error || ''),
    ].join('');
    const tables = database.tables || {};
    $('server-admin-tables').innerHTML = Object.keys(tables).map((name) => {
      const ok = !!tables[name];
      return `<div style="border:1px solid ${ok ? '#bbf7d0' : '#fecaca'};background:${ok ? '#f0fdf4' : '#fff7f7'};border-radius:12px;padding:12px;">
        <div style="font-weight:700;font-size:.9rem;">${esc(name)}</div>
        <div style="margin-top:6px;color:${ok ? '#166534' : '#b42318'};font-size:.84rem;">${ok ? 'presente' : 'faltante'}</div>
      </div>`;
    }).join('');
    $('server-admin-logs').textContent = (payload.logs || []).join('\\n') || 'Sin logs locales disponibles.';
  };

  const loadStatus = async () => {
    const res = await fetch('/api/server-admin/status');
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.error || 'Error al cargar el panel');
    render(data);
  };

  const runAction = async (action) => {
    const res = await fetch('/api/server-admin/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action}),
    });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.error || 'Accion no disponible');
    showMsg(data.message || 'Operacion ejecutada.');
    await loadStatus();
  };

  $('server-admin-refresh').addEventListener('click', async () => {
    try { await runAction('refresh_runtime'); } catch (err) { showMsg(t(err.message || err), true); }
  });
  $('server-admin-bootstrap').addEventListener('click', async () => {
    try { await runAction('bootstrap_schema'); } catch (err) { showMsg(t(err.message || err), true); }
  });

  loadStatus().catch((err) => showMsg(t(err.message || err), true));
})();
</script>
"""


@router.get("/server-admin", response_class=HTMLResponse)
def server_admin_page(request: Request):
    _ensure_enabled(request)
    return render_backend_page(
        request,
        title="Panel del servidor",
        description="Estado basico del runtime y herramientas de operacion para produccion.",
        content=_page_content(),
        hide_floating_actions=True,
    )


@router.get("/api/server-admin/status")
def server_admin_status(request: Request):
    _ensure_enabled(request)
    return JSONResponse(
        {
            "success": True,
            "runtime": _runtime_snapshot(request),
            "health": _health_snapshot(),
            "database": _database_snapshot(),
            "logs": _tail_log_lines(DEFAULT_LOG_FILE, max_lines=150),
        }
    )


@router.post("/api/server-admin/action")
async def server_admin_action(request: Request):
    _ensure_enabled(request)
    payload = await request.json()
    action = str((payload or {}).get("action") or "").strip().lower()
    if action == "refresh_runtime":
        core_db.refresh_runtime_database_state()
        return JSONResponse({"success": True, "message": "Runtime de base de datos refrescado."})
    if action == "bootstrap_schema":
        from fastapi_modulo.modulos_sipet.modulo_base import runtime_app

        runtime_app.run_core_schema_bootstrap(force_refresh_database=True)
        request.app.state.database_setup_required = False
        request.app.state.database_setup_error = ""
        request.app.state.core_schema_initialized = True
        return JSONResponse({"success": True, "message": "Bootstrap de esquema ejecutado."})
    raise HTTPException(status_code=400, detail="Accion no soportada")
