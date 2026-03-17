from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import shutil
from html import escape
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from fastapi_modulo.core.database_router import (
    can_connect_current_database,
    delete_domain_conf_entry,
    export_domain_conf_text,
    get_sipet_conf_settings,
    import_domain_conf_text,
    initialize_database_from_sipet_conf,
    list_domain_conf_entries,
    read_conf_file,
    save_domain_conf_entry,
    update_sipet_conf_settings,
)
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_admin_or_superadmin
from fastapi_modulo.modulos_sipet.web.servicios.session_service import AUTH_COOKIE_SECRET

router = APIRouter()
SETUP_AUTH_COOKIE_NAME = "sipet_setup_auth"
DEFAULT_SETUP_USERNAME_B64 = "MGtvbm9taXlha2k="
DEFAULT_SETUP_PASSWORD_B64 = "WFgsJCwyNixzaXBldCwyNiwkLFhY"
BRAND_LOGO_URL = "/modulos_sipet/web/static/imagenes/avancoop.png"


def _decode_b64(value: str) -> str:
    return base64.b64decode(value.encode("utf-8")).decode("utf-8")


def _setup_username() -> str:
    return (os.environ.get("SYSTEM_SUPERADMIN_USERNAME") or _decode_b64(DEFAULT_SETUP_USERNAME_B64)).strip()


def _setup_password() -> str:
    return os.environ.get("SYSTEM_SUPERADMIN_PASSWORD") or _decode_b64(DEFAULT_SETUP_PASSWORD_B64)


def _build_setup_auth_cookie(username: str) -> str:
    payload = username.strip()
    signature = hmac.new(AUTH_COOKIE_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def _is_setup_authenticated(request: Request) -> bool:
    token = str(request.cookies.get(SETUP_AUTH_COOKIE_NAME) or "").strip()
    if "." not in token:
        return False
    payload, signature = token.rsplit(".", 1)
    expected = hmac.new(AUTH_COOKIE_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected) and payload == _setup_username()


def _setup_required(request: Request) -> bool:
    return bool(getattr(getattr(request, "app", None), "state", None) and getattr(request.app.state, "database_setup_required", False))


def _enforce_admin_or_setup(request: Request, *, require_setup_auth: bool = False) -> None:
    if _setup_required(request):
        if require_setup_auth and not _is_setup_authenticated(request):
            raise HTTPException(status_code=401, detail="Autenticación requerida para gestionar la base de datos")
        return
    require_admin_or_superadmin(request)


def _manager_content() -> str:
    settings = get_sipet_conf_settings()
    settings_json = escape(json.dumps(settings, ensure_ascii=False))
    return f"""
<section class="w-full space-y-4">
  <div class="titulo bg-MAIN-200 rounded-box border border-MAIN-300 p-4 sm:p-6">
    <div class="w-full flex flex-col md:flex-row items-center gap-10">
      <img src="{BRAND_LOGO_URL}" alt="AVANCOOP" width="132" height="132" class="shrink-0 rounded-box border border-MAIN-300 bg-MAIN-100 p-3 object-contain" />
      <div class="w-full grid gap-2 content-center">
        <div class="block w-full text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight text-[color:var(--sidebar-bottom)]">Gestión de bases de datos</div>
        <div class="block w-full text-MAIN sm:text-lg text-MAIN-content/70">Alta, edición, baja, exportación e importación de dominios y bases.</div>
      </div>
    </div>
  </div>

  <div class="grid grid-cols-1 xl:grid-cols-12 gap-4">
    <aside class="card border border-MAIN-300 bg-MAIN-100 shadow-sm xl:col-span-4">
      <div class="card-body gap-3">
        <h3 class="card-title">`sipet.conf`</h3>
        <label class="form-control gap-1"><span class="label-text">Dominio base</span><input id="sipet-domain" class="input input-bordered" value="{escape(str(settings.get('domain') or ''))}"></label>
        <label class="form-control gap-1"><span class="label-text">Host BD</span><input id="sipet-db-host" class="input input-bordered" value="{escape(str(settings.get('db_host') or ''))}"></label>
        <label class="form-control gap-1"><span class="label-text">Puerto</span><input id="sipet-db-port" class="input input-bordered" value="{escape(str(settings.get('db_port') or '5432'))}"></label>
        <label class="form-control gap-1"><span class="label-text">Usuario BD</span><input id="sipet-db-user" class="input input-bordered" value="{escape(str(settings.get('db_user') or ''))}"></label>
        <label class="form-control gap-1"><span class="label-text">Password BD</span><input id="sipet-db-password" type="password" class="input input-bordered" value=""></label>
        <label class="form-control gap-1"><span class="label-text">Nombre BD</span><input id="sipet-db-name" class="input input-bordered" value="{escape(str(settings.get('db_name') or ''))}"></label>
        <label class="form-control gap-1"><span class="label-text">dbfilter</span><input id="sipet-dbfilter" class="input input-bordered" value="{escape(str(settings.get('dbfilter') or ''))}"></label>
        <label class="label cursor-pointer justify-start gap-3"><input id="sipet-show-db-path" type="checkbox" class="checkbox" {"checked" if settings.get("show_db_path") else ""}><span class="label-text">Mostrar ruta</span></label>
        <div class="flex gap-2 flex-wrap">
          <button id="save-sipet-conf" class="btn btn-primary btn-sm" type="button">Guardar</button>
          <button id="initialize-database" class="btn btn-secondary btn-sm" type="button">Inicializar BD</button>
          <a class="btn btn-outline btn-sm" href="/api/base_datos/gestion/export/sipet-conf">Exportar conf</a>
        </div>
        <p class="text-xs text-MAIN-content/60 break-all">{escape(str(settings.get("path") or ""))}</p>
      </div>
    </aside>

    <section class="card border border-MAIN-300 bg-MAIN-100 shadow-sm xl:col-span-8">
      <div class="card-body gap-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label class="form-control gap-1"><span class="label-text">Dominio</span><input id="entry-domain" class="input input-bordered" placeholder="demo.midominio.com"></label>
          <label class="form-control gap-1"><span class="label-text">Host BD</span><input id="entry-db-host" class="input input-bordered" placeholder="localhost"></label>
          <label class="form-control gap-1"><span class="label-text">Puerto</span><input id="entry-db-port" class="input input-bordered" value="5432"></label>
          <label class="form-control gap-1"><span class="label-text">Usuario BD</span><input id="entry-db-user" class="input input-bordered" placeholder="sipet"></label>
          <label class="form-control gap-1"><span class="label-text">Password BD</span><input id="entry-db-password" type="password" class="input input-bordered"></label>
          <label class="form-control gap-1"><span class="label-text">Nombre BD</span><input id="entry-db-name" class="input input-bordered" placeholder="sipet_demo"></label>
          <label class="form-control gap-1 md:col-span-2"><span class="label-text">SQLite path opcional</span><input id="entry-sqlite-db-path" class="input input-bordered" placeholder="base_datos/demo.db"></label>
          <label class="label cursor-pointer justify-start gap-3"><input id="entry-enabled" type="checkbox" class="checkbox" checked><span class="label-text">Activo</span></label>
        </div>
        <div class="flex gap-2 flex-wrap">
          <button id="save-entry" class="btn btn-primary btn-sm" type="button">Guardar dominio</button>
          <button id="reset-entry" class="btn btn-outline btn-sm" type="button">Limpiar</button>
          <label class="btn btn-ghost btn-sm cursor-pointer">Importar conf<input id="import-conf-input" type="file" class="hidden" accept=".conf,.ini,.json,text/plain"></label>
        </div>
        <div class="overflow-x-auto rounded-box border border-MAIN-300 bg-MAIN-100">
          <table class="table table-zebra w-full text-sm min-w-[960px]">
            <thead>
              <tr>
                <th>Dominio</th>
                <th>BD</th>
                <th>Ruta/URL</th>
                <th>Archivo</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody id="db-manager-body"></tbody>
          </table>
        </div>
        <p id="db-manager-message" class="text-sm text-MAIN-content/60"></p>
      </div>
    </section>
  </div>
</section>
<script>
(() => {{
  const state = {{ settings: {settings_json}, entries: [] }};
  const byId = (id) => document.getElementById(id);
  const msg = byId('db-manager-message');
  const body = byId('db-manager-body');
  const text = (v) => String(v ?? '');

  const showMsg = (value, isError = false) => {{
    if (!msg) return;
    msg.textContent = value;
    msg.className = isError ? 'text-sm text-red-600' : 'text-sm text-MAIN-content/60';
  }};

  const formPayload = () => ({{
    domain: text(byId('entry-domain')?.value).trim(),
    db_host: text(byId('entry-db-host')?.value).trim(),
    db_port: text(byId('entry-db-port')?.value).trim(),
    db_user: text(byId('entry-db-user')?.value).trim(),
    db_password: text(byId('entry-db-password')?.value).trim(),
    db_name: text(byId('entry-db-name')?.value).trim(),
    sqlite_db_path: text(byId('entry-sqlite-db-path')?.value).trim(),
    enabled: Boolean(byId('entry-enabled')?.checked),
  }});

  const fillForm = (entry) => {{
    byId('entry-domain').value = text(entry.domain);
    byId('entry-db-host').value = text(entry.db_host);
    byId('entry-db-port').value = text(entry.db_port || '5432');
    byId('entry-db-user').value = text(entry.db_user);
    byId('entry-db-password').value = text(entry.db_password);
    byId('entry-db-name').value = text(entry.db_name);
    byId('entry-sqlite-db-path').value = text(entry.sqlite_path);
    byId('entry-enabled').checked = Boolean(entry.enabled);
  }};

  const clearForm = () => {{
    fillForm({{ domain:'', db_host:'', db_port:'5432', db_user:'', db_password:'', db_name:'', sqlite_path:'', enabled:true }});
  }};

  const render = () => {{
    const showPath = Boolean(state.settings.show_db_path);
    body.innerHTML = (state.entries || []).map((entry) => {{
      const pathCell = showPath ? (entry.sqlite_path || entry.db_url || '') : 'Oculta';
      return `
        <tr>
          <td>${{text(entry.domain)}}</td>
          <td>${{text(entry.db_name || (entry.sqlite_path ? 'sqlite' : ''))}}</td>
          <td class="break-all">${{text(pathCell)}}</td>
          <td class="break-all">${{text(entry.file_path)}}</td>
          <td>
            <div class="flex gap-2 flex-wrap">
              <button type="button" class="btn btn-xs btn-outline" data-action="edit" data-domain="${{text(entry.domain)}}">Editar</button>
              <a class="btn btn-xs btn-ghost" href="/api/base_datos/gestion/export/conf?domain=${{encodeURIComponent(text(entry.domain))}}">Exportar conf</a>
              <a class="btn btn-xs btn-ghost" href="/api/base_datos/gestion/export/db?domain=${{encodeURIComponent(text(entry.domain))}}">Exportar BD</a>
              <button type="button" class="btn btn-xs btn-error" data-action="delete" data-domain="${{text(entry.domain)}}">Eliminar</button>
            </div>
          </td>
        </tr>
      `;
    }}).join('') || '<tr><td colspan="5" class="text-center">Sin dominios configurados.</td></tr>';
  }};

  const loadEntries = async () => {{
    const res = await fetch('/api/base_datos/gestion/list');
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.error || 'No se pudo cargar');
    state.entries = data.entries || [];
    state.settings = data.settings || state.settings;
    render();
  }};

  byId('save-entry')?.addEventListener('click', async () => {{
    try {{
      const res = await fetch('/api/base_datos/gestion/save', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(formPayload()),
      }});
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'No se pudo guardar');
      clearForm();
      await loadEntries();
      showMsg('Dominio guardado.');
    }} catch (err) {{
      showMsg(String(err.message || err), true);
    }}
  }});

  byId('reset-entry')?.addEventListener('click', clearForm);

  byId('save-sipet-conf')?.addEventListener('click', async () => {{
    try {{
      const payload = {{
        domain: text(byId('sipet-domain')?.value).trim(),
        db_host: text(byId('sipet-db-host')?.value).trim(),
        db_port: text(byId('sipet-db-port')?.value).trim(),
        db_user: text(byId('sipet-db-user')?.value).trim(),
        db_password: text(byId('sipet-db-password')?.value).trim(),
        db_name: text(byId('sipet-db-name')?.value).trim(),
        dbfilter: text(byId('sipet-dbfilter')?.value).trim(),
        show_db_path: Boolean(byId('sipet-show-db-path')?.checked),
      }};
      const res = await fetch('/api/base_datos/gestion/sipet-conf', {{
        method: 'PUT',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload),
      }});
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'No se pudo guardar sipet.conf');
      state.settings = data.settings || state.settings;
      render();
      showMsg('sipet.conf actualizado.');
    }} catch (err) {{
      showMsg(String(err.message || err), true);
    }}
  }});

  byId('initialize-database')?.addEventListener('click', async () => {{
    try {{
      const payload = {{
        domain: text(byId('sipet-domain')?.value).trim(),
        db_host: text(byId('sipet-db-host')?.value).trim(),
        db_port: text(byId('sipet-db-port')?.value).trim(),
        db_user: text(byId('sipet-db-user')?.value).trim(),
        db_password: text(byId('sipet-db-password')?.value).trim(),
        db_name: text(byId('sipet-db-name')?.value).trim(),
        dbfilter: text(byId('sipet-dbfilter')?.value).trim(),
        show_db_path: Boolean(byId('sipet-show-db-path')?.checked),
      }};
      const res = await fetch('/api/base_datos/inicializar', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload),
      }});
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'No se pudo inicializar la base');
      state.settings = data.settings || state.settings;
      render();
      showMsg(data.result?.connected ? 'Base de datos inicializada.' : (data.result?.error || 'No se pudo conectar.'), !data.result?.connected);
      if (data.result?.connected) {{
        window.setTimeout(() => window.location.href = '/backend/login', 800);
      }}
    }} catch (err) {{
      showMsg(String(err.message || err), true);
    }}
  }});

  byId('import-conf-input')?.addEventListener('change', async (event) => {{
    const file = event.target.files?.[0];
    if (!file) return;
    try {{
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/base_datos/gestion/import/conf', {{ method: 'POST', body: formData }});
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'No se pudo importar');
      await loadEntries();
      showMsg('Archivo importado.');
    }} catch (err) {{
      showMsg(String(err.message || err), true);
    }} finally {{
      event.target.value = '';
    }}
  }});

  body?.addEventListener('click', async (event) => {{
    const target = event.target.closest('[data-action]');
    if (!target) return;
    const action = target.dataset.action;
    const domain = target.dataset.domain || '';
    const entry = state.entries.find((item) => text(item.domain) === domain);
    if (action === 'edit' && entry) {{
      fillForm(entry);
      return;
    }}
    if (action === 'delete' && domain) {{
      if (!window.confirm(`Eliminar configuración para ${{domain}}?`)) return;
      try {{
        const res = await fetch(`/api/base_datos/gestion/${{encodeURIComponent(domain)}}`, {{ method: 'DELETE' }});
        const data = await res.json();
        if (!res.ok || !data.success) throw new Error(data.error || 'No se pudo eliminar');
        await loadEntries();
        showMsg('Dominio eliminado.');
      }} catch (err) {{
        showMsg(String(err.message || err), true);
      }}
    }}
  }});

  loadEntries().catch((err) => showMsg(String(err.message || err), true));
  clearForm();
}})();
</script>
"""


def _setup_login_content() -> str:
    return f"""
<section class="w-full max-w-xl mx-auto">
  <article class="card border border-MAIN-300 bg-MAIN-100 shadow-sm">
    <div class="card-body gap-4">
      <div class="flex" style="justify-content:center;">
        <img src="{BRAND_LOGO_URL}" alt="AVANCOOP" width="144" height="144" style="border:1px solid var(--line); border-radius:18px; background:#fff; padding:14px; object-fit:contain;">
      </div>
      <h2 class="card-title">Inicializar base de datos</h2>
      <p>Se requieren las credenciales maestras para crear o modificar la base de datos.</p>
      <form method="post" action="/base_datos/setup/login" class="grid" style="gap:16px;">
        <label class="form-control gap-1">
          <span class="label-text">Usuario</span>
          <input name="username" class="input input-bordered" autocomplete="off">
        </label>
        <label class="form-control gap-1">
          <span class="label-text">Contraseña</span>
          <input name="password" type="password" class="input input-bordered">
        </label>
        <div class="flex gap-2">
          <button type="submit" class="btn btn-primary btn-sm">Entrar</button>
        </div>
      </form>
      <p id="setup-login-msg" class="text-sm text-MAIN-content/60"></p>
    </div>
  </article>
</section>
"""


def _standalone_setup_page(title: str, content: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --card: #ffffff;
      --line: #d9dee7;
      --text: #16202a;
      --muted: #5b6673;
      --primary: #0f766e;
      --primary-ink: #ffffff;
      --danger: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #eef3f7 0%, var(--bg) 100%);
      color: var(--text);
    }}
    .wrap {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .shell {{
      background: rgba(255,255,255,.75);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 18px;
      box-shadow: 0 20px 60px rgba(15, 23, 42, .08);
    }}
    .card, .titulo {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
    }}
    .card-body, .titulo {{
      padding: 20px;
    }}
    .grid {{
      display: grid;
      gap: 16px;
    }}
    .xl-grid {{
      grid-template-columns: 1fr 2fr;
    }}
    .form-control {{
      display: grid;
      gap: 6px;
    }}
    .label-text, .card-title {{
      font-weight: 600;
    }}
    .input {{
      width: 100%;
      min-height: 40px;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fff;
      color: var(--text);
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 38px;
      padding: 0 14px;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      text-decoration: none;
      cursor: pointer;
    }}
    .btn-primary, .btn-secondary {{
      background: var(--primary);
      color: var(--primary-ink);
      border-color: var(--primary);
    }}
    .btn-error {{
      color: var(--danger);
      border-color: #f1b7b1;
      background: #fff7f6;
    }}
    .flex {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #fff;
      border-radius: 12px;
      overflow: hidden;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{ background: #f8fafc; }}
    .text-sm {{ font-size: 14px; }}
    .text-xs {{ font-size: 12px; }}
    .text-muted {{ color: var(--muted); }}
    .text-danger {{ color: var(--danger); }}
    .break-all {{ word-break: break-all; }}
    @media (max-width: 980px) {{
      .xl-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="shell">{content}</div>
  </div>
</body>
</html>"""
    )


@router.get("/base_datos/gestion", response_class=HTMLResponse)
def database_manager_page(request: Request):
    if _setup_required(request) and not _is_setup_authenticated(request):
        return _standalone_setup_page("Inicializar base de datos", _setup_login_content())
    else:
        _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
        content = _manager_content()
    if _setup_required(request):
        return _standalone_setup_page("Gestión de bases de datos", content)
    return render_backend_page(
        request,
        title="Gestión de bases de datos",
        description="Administrador de bases y dominios estilo Odoo.",
        content=content,
        hide_floating_actions=True,
        show_page_header=False,
    )


@router.get("/base_datos/inicializar", response_class=HTMLResponse)
def database_setup_page(request: Request):
    if not _setup_required(request):
        return HTMLResponse("", status_code=303, headers={"Location": "/base_datos/gestion"})
    return _standalone_setup_page(
        "Inicializar base de datos",
        _setup_login_content() if not _is_setup_authenticated(request) else _manager_content(),
    )


@router.get("/api/base_datos/gestion/list")
def list_database_entries(request: Request):
    _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
    ok, error = can_connect_current_database()
    return JSONResponse({"success": True, "entries": list_domain_conf_entries(), "settings": get_sipet_conf_settings(), "database_ready": ok, "database_error": error})


@router.post("/api/base_datos/gestion/save")
async def save_database_entry(request: Request):
    _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
    payload = await request.json()
    try:
        entry = save_domain_conf_entry(payload if isinstance(payload, dict) else {})
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
    return JSONResponse({"success": True, "entry": entry})


@router.put("/api/base_datos/gestion/sipet-conf")
async def save_sipet_conf(request: Request):
    _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
    payload = await request.json()
    try:
        settings = update_sipet_conf_settings(payload if isinstance(payload, dict) else {})
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
    return JSONResponse({"success": True, "settings": settings})


@router.delete("/api/base_datos/gestion/{domain}")
def delete_database_entry(request: Request, domain: str):
    _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
    deleted = delete_domain_conf_entry(domain)
    return JSONResponse({"success": deleted, "domain": domain, "deleted": deleted}, status_code=200 if deleted else 404)


@router.get("/api/base_datos/gestion/export/conf")
def export_domain_conf(request: Request, domain: str):
    _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
    try:
        content = export_domain_conf_text(domain)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dominio no encontrado")
    return HTMLResponse(content=content, media_type="text/plain; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{domain}.conf"'})


@router.get("/api/base_datos/gestion/export/sipet-conf")
def export_sipet_conf(request: Request):
    _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
    parser = read_conf_file(Path("sipet.conf"))
    raw = []
    for section in parser.sections():
        raw.append(f"[{section}]")
        for key, value in parser[section].items():
            raw.append(f"{key} = {value}")
        raw.append("")
    return HTMLResponse(content="\n".join(raw), media_type="text/plain; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="sipet.conf"'})


@router.get("/api/base_datos/gestion/export/db")
def export_database_file(request: Request, domain: str):
    _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
    entry = next((item for item in list_domain_conf_entries() if item.get("domain") == domain), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Dominio no encontrado")
    sqlite_path = Path(str(entry.get("sqlite_path") or ""))
    if not sqlite_path.exists() or not sqlite_path.is_file():
        detail = "La exportación binaria solo aplica a SQLite con archivo local"
        raise HTTPException(status_code=400, detail=detail)
    return FileResponse(str(sqlite_path), filename=sqlite_path.name, media_type="application/octet-stream")


@router.post("/api/base_datos/gestion/import/conf")
async def import_database_conf(request: Request, file: UploadFile = File(...)):
    _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
    content = (await file.read()).decode("utf-8", errors="ignore")
    try:
        entry = import_domain_conf_text(file.filename or "import.conf", content)
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
    return JSONResponse({"success": True, "entry": entry})


@router.post("/api/base_datos/gestion/import/db")
async def import_database_file(request: Request, domain: str, file: UploadFile = File(...)):
    _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
    entry = next((item for item in list_domain_conf_entries() if item.get("domain") == domain), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Dominio no encontrado")
    sqlite_path = Path(str(entry.get("sqlite_path") or ""))
    if not str(sqlite_path):
        raise HTTPException(status_code=400, detail="Dominio sin sqlite_path configurado")
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = sqlite_path.with_suffix(sqlite_path.suffix + ".upload")
    with temp_path.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    temp_path.replace(sqlite_path)
    return JSONResponse({"success": True, "domain": domain, "path": str(sqlite_path)})


@router.post("/api/base_datos/inicializar")
async def initialize_database(request: Request):
    _enforce_admin_or_setup(request, require_setup_auth=_setup_required(request))
    payload = await request.json()
    try:
        result = initialize_database_from_sipet_conf(payload if isinstance(payload, dict) else {})
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
    if getattr(request.app.state, "database_setup_required", False):
        request.app.state.database_setup_required = not bool(result.get("connected"))
        request.app.state.database_setup_error = str(result.get("error") or "")
    return JSONResponse({"success": True, "result": result, "settings": get_sipet_conf_settings()})


@router.post("/api/base_datos/setup/login")
async def setup_login(request: Request):
    try:
        if not _setup_required(request):
            return JSONResponse({"success": False, "error": "Setup no requerido"}, status_code=404)
        payload = await request.json()
        username = str((payload or {}).get("username") or "").strip()
        password = str((payload or {}).get("password") or "")
        if username != _setup_username() or password != _setup_password():
            return JSONResponse({"success": False, "error": "Credenciales inválidas"}, status_code=401)
        response = JSONResponse({"success": True})
        response.set_cookie(
            SETUP_AUTH_COOKIE_NAME,
            _build_setup_auth_cookie(username),
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=3600,
        )
        return response
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@router.post("/base_datos/setup/login")
async def setup_login_form(request: Request, username: str = Form(""), password: str = Form("")):
    if not _setup_required(request):
        return RedirectResponse(url="/base_datos/gestion", status_code=303)
    if str(username or "").strip() != _setup_username() or str(password or "") != _setup_password():
        return _standalone_setup_page(
            "Inicializar base de datos",
            _setup_login_content() + '<p class="text-sm text-danger">Credenciales inválidas.</p>',
        )
    response = RedirectResponse(url="/base_datos/inicializar", status_code=303)
    response.set_cookie(
        SETUP_AUTH_COOKIE_NAME,
        _build_setup_auth_cookie(str(username or "").strip()),
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=3600,
    )
    return response
