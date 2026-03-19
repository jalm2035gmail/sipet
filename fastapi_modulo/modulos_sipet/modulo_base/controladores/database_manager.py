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
    list_domain_conf_entries,
    read_conf_file,
    save_domain_conf_entry,
    update_sipet_conf_settings,
)
from fastapi_modulo.modulos_sipet.instalacion.servicios.installer_service import bootstrap_installation
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.servicios.access_service import is_superadmin, require_admin_or_superadmin
from fastapi_modulo.modulos_sipet.web.servicios.session_service import AUTH_COOKIE_SECRET

router = APIRouter()
SETUP_AUTH_COOKIE_NAME = "sipet_setup_auth"
DEFAULT_SETUP_USERNAME_B64 = "MGtvbm9taXlha2k="
DEFAULT_SETUP_PASSWORD_B64 = "WFgsJCwyNixzaXBldCwyNiwkLFhY"
BRAND_LOGO_URL = "/modulos_sipet/avancoop.png"


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
    if _is_setup_authenticated(request):
        return
    if _setup_required(request):
        if require_setup_auth and not _is_setup_authenticated(request):
            raise HTTPException(status_code=401, detail="Autenticación requerida para gestionar la base de datos")
        return
    require_admin_or_superadmin(request)


def _manager_content() -> str:
    return f"""
<style>
  .db-btn {{
    display:block; width:100%; padding:11px 0; border-radius:10px;
    border:2px solid #16a34a; background:#16a34a; color:#fff;
    font-weight:600; font-size:.95rem; cursor:pointer; text-align:center;
    transition:background .15s, color .15s;
  }}
  .db-btn:hover {{ background:#fff; color:#16a34a; }}
  .db-btn:disabled {{ opacity:.4; cursor:not-allowed; pointer-events:none; }}
  .db-item {{
    display:flex; flex-direction:column; gap:3px;
    padding:14px 20px; border-bottom:1px solid var(--line);
    cursor:pointer; border-left:4px solid transparent;
    transition:background .1s, border-color .1s;
  }}
  .db-item:last-child {{ border-bottom:none; }}
  .db-item:hover {{ background:#f0fdf4; }}
  .db-item.selected {{ border-left-color:#16a34a; background:#f0fdf4; }}
  .db-item-domain {{ font-weight:700; color:var(--text); font-size:.95rem; }}
  .db-item-meta {{ font-size:.8rem; color:var(--muted); }}
  .form-panel {{
    display:none; background:#fff; border:1px solid var(--line);
    border-radius:16px; padding:24px; flex-direction:column; gap:16px;
  }}
  .form-panel.open {{ display:flex; }}
  .form-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
  .field {{ display:flex; flex-direction:column; gap:5px; }}
  .field label {{ font-size:.85rem; font-weight:600; color:var(--text); }}
  .field input, .field select {{
    padding:9px 12px; border:1px solid var(--line); border-radius:8px;
    font-size:.9rem; background:#fff; color:var(--text); width:100%;
    box-sizing:border-box;
  }}
  .field input:focus, .field select:focus {{ outline:2px solid #16a34a; border-color:#16a34a; }}
  .btn-cancel {{
    padding:10px 24px; border-radius:10px; border:2px solid var(--line);
    background:#fff; color:var(--text); font-weight:600; cursor:pointer;
    font-size:.95rem;
  }}
  .btn-cancel:hover {{ background:#f8fafc; }}
  @media (max-width:640px) {{
    .two-col {{ grid-template-columns:1fr !important; }}
    .form-grid {{ grid-template-columns:1fr !important; }}
  }}
</style>

<section style="width:100%;display:grid;gap:20px;">

  <!-- Encabezado -->
  <div style="display:flex;align-items:center;gap:20px;background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px 24px;">
    <img src="{BRAND_LOGO_URL}" alt="Logo" width="80" height="80"
         style="border-radius:12px;box-shadow:0 4px 20px rgba(15,23,42,.18);object-fit:contain;flex-shrink:0;">
    <div>
      <h1 style="font-size:clamp(1.5rem,3vw,2.2rem);font-weight:800;margin:0;color:var(--text);">
        Gestión de bases de datos
      </h1>
      <p style="margin:4px 0 0;color:var(--muted);font-size:.95rem;">
        Alta, edición y baja de bases de datos del sitio.
      </p>
    </div>
  </div>

  <!-- Dos columnas: lista + botones -->
  <div class="two-col" style="display:grid;grid-template-columns:1fr 180px;gap:20px;align-items:start;">

    <!-- Izquierda: lista de BD -->
    <div style="background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;">
      <div style="padding:14px 20px;border-bottom:1px solid var(--line);font-weight:700;font-size:.95rem;color:var(--text);">
        Bases de datos del sitio
      </div>
      <ul id="db-list" style="list-style:none;margin:0;padding:0;min-height:120px;">
        <li style="padding:20px;color:var(--muted);font-size:.9rem;">Cargando…</li>
      </ul>
      <p id="db-msg" style="padding:10px 20px;font-size:.85rem;margin:0;display:none;"></p>
    </div>

    <!-- Derecha: botones de acción -->
    <div style="display:flex;flex-direction:column;gap:10px;">
      <button class="db-btn" id="btn-crear" type="button">Crear</button>
      <button class="db-btn" id="btn-inicializar" type="button" disabled>Inicializar base</button>
      <button class="db-btn" id="btn-editar" type="button" disabled>Editar</button>
      <button class="db-btn" id="btn-eliminar" type="button" disabled>Eliminar</button>
    </div>
  </div>

  <!-- Panel de formulario (crear / editar) -->
  <div class="form-panel" id="form-panel">
    <h2 id="form-title" style="margin:0;font-size:1.1rem;font-weight:700;color:var(--text);"></h2>
    <div class="form-grid">
      <div class="field">
        <label>Motor BD</label>
        <select id="f-db-engine">
          <option value="postgresql">PostgreSQL</option>
          <option value="mysql">MySQL</option>
          <option value="sqlite">SQLite</option>
        </select>
      </div>
      <div class="field">
        <label>Dominio</label>
        <input id="f-domain" placeholder="demo.midominio.com">
      </div>
      <div class="field">
        <label>Host BD</label>
        <input id="f-db-host" placeholder="localhost">
      </div>
      <div class="field">
        <label>Puerto</label>
        <input id="f-db-port" value="5432">
      </div>
      <div class="field">
        <label>Usuario BD</label>
        <input id="f-db-user" placeholder="sipet">
      </div>
      <div class="field">
        <label>Password BD</label>
        <input id="f-db-password" type="password">
      </div>
      <div class="field">
        <label>Nombre BD</label>
        <input id="f-db-name" placeholder="sipet_demo">
      </div>
    </div>
    <div class="field">
      <label>SQLite path (opcional)</label>
      <input id="f-sqlite-path" placeholder="base_datos/demo.db">
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
      <button class="db-btn" id="btn-guardar" type="button" style="width:auto;padding:10px 28px;">
        Guardar
      </button>
      <button class="btn-cancel" id="btn-cancelar" type="button">Cancelar</button>
    </div>
    <p id="form-msg" style="font-size:.85rem;margin:0;"></p>
  </div>

</section>
<script>
(() => {{
  let entries = [];
  let selected = null;
  let mode = null;

  const $ = (id) => document.getElementById(id);
  const t = (v) => String(v ?? '');

  const showMsg = (el, text, err) => {{
    el.textContent = text;
    el.style.color = err ? '#b42318' : '#16a34a';
    el.style.display = text ? '' : 'none';
  }};

  const syncButtons = () => {{
    $('btn-inicializar').disabled = !selected;
    $('btn-editar').disabled = !selected;
    $('btn-eliminar').disabled = !selected;
  }};

  const renderList = () => {{
    const list = $('db-list');
    if (!entries.length) {{
      list.innerHTML = '<li style="padding:20px;color:var(--muted);font-size:.9rem;">Sin bases de datos configuradas.</li>';
      return;
    }}
    list.innerHTML = entries.map((e) => {{
      const engine = String(e.db_engine || '').trim().toLowerCase();
      const tipo = e.sqlite_path ? 'SQLite' : (engine === 'mysql' ? 'MySQL' : (e.db_name ? 'PostgreSQL' : '—'));
      const sel = e.domain === selected ? ' selected' : '';
      return `<li class="db-item${{sel}}" data-domain="${{t(e.domain)}}">
        <span class="db-item-domain">${{t(e.domain) || '—'}}</span>
        <span class="db-item-meta">
          ${{tipo}}${{e.db_name ? ' · ' + t(e.db_name) : ''}}${{e.db_host ? ' · ' + t(e.db_host) : ''}}
        </span>
      </li>`;
    }}).join('');
    list.querySelectorAll('.db-item').forEach((item) => {{
      item.addEventListener('click', () => {{
        selected = item.dataset.domain;
        $('form-panel').classList.remove('open');
        mode = null;
        renderList();
        syncButtons();
      }});
    }});
  }};

  const loadEntries = async () => {{
    try {{
      const res = await fetch('/api/base_datos/gestion/list');
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'Error al cargar');
      entries = data.entries || [];
      renderList();
    }} catch (err) {{
      showMsg($('db-msg'), t(err.message || err), true);
    }}
  }};

  const openPanel = (m) => {{
    mode = m;
    $('form-title').textContent = m === 'crear' ? 'Nueva base de datos' : 'Editar base de datos';
    const e = m === 'editar' ? entries.find((x) => x.domain === selected) : null;
    $('f-db-engine').value = t(e?.db_engine || (e?.sqlite_path ? 'sqlite' : (String(e?.db_host || '').includes('mysql') ? 'mysql' : 'postgresql'))) || 'postgresql';
    $('f-domain').value = t(e?.domain); $('f-domain').disabled = m === 'editar';
    $('f-db-host').value = t(e?.db_host);
    $('f-db-port').value = t(e?.db_port || ($('f-db-engine').value === 'mysql' ? '3306' : '5432'));
    $('f-db-user').value = t(e?.db_user);
    $('f-db-password').value = '';
    $('f-db-name').value = t(e?.db_name);
    $('f-sqlite-path').value = t(e?.sqlite_path);
    showMsg($('form-msg'), '', false);
    $('form-panel').classList.add('open');
    $('form-panel').scrollIntoView({{ behavior:'smooth', block:'nearest' }});
  }};

  $('f-db-engine').addEventListener('change', () => {{
    if ($('f-db-engine').value === 'mysql' && !$('f-db-port').value.trim()) $('f-db-port').value = '3306';
    if ($('f-db-engine').value === 'postgresql' && (!$('f-db-port').value.trim() || $('f-db-port').value.trim() === '3306')) $('f-db-port').value = '5432';
  }});

  $('btn-crear').addEventListener('click', () => openPanel('crear'));
  $('btn-editar').addEventListener('click', () => openPanel('editar'));
  $('btn-inicializar').addEventListener('click', async () => {{
    const entry = entries.find((x) => x.domain === selected);
    if (!entry) return;
    try {{
      const payload = {{
        domain: t(entry.domain).trim(),
        db_engine: t(entry.db_engine).trim(),
        db_host: t(entry.db_host).trim(),
        db_port: t(entry.db_port).trim(),
        db_user: t(entry.db_user).trim(),
        db_password: t(entry.db_password),
        db_name: t(entry.db_name).trim(),
        sqlite_db_path: t(entry.sqlite_path).trim(),
      }};
      const res = await fetch('/api/base_datos/inicializar', {{
        method:'POST',
        headers:{{'Content-Type':'application/json'}},
        body: JSON.stringify(payload),
      }});
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'Error al inicializar');
      showMsg($('db-msg'), 'Base de datos inicializada correctamente.', false);
      await loadEntries();
    }} catch (err) {{
      showMsg($('db-msg'), t(err.message || err), true);
    }}
  }});
  $('btn-cancelar').addEventListener('click', () => {{
    $('form-panel').classList.remove('open');
    mode = null;
  }});

  $('btn-guardar').addEventListener('click', async () => {{
    const payload = {{
      db_engine: $('f-db-engine').value.trim(),
      domain: $('f-domain').value.trim(),
      db_host: $('f-db-host').value.trim(),
      db_port: $('f-db-port').value.trim(),
      db_user: $('f-db-user').value.trim(),
      db_password: $('f-db-password').value,
      db_name: $('f-db-name').value.trim(),
      sqlite_db_path: $('f-sqlite-path').value.trim(),
      enabled: true,
    }};
    try {{
      const res = await fetch('/api/base_datos/gestion/save', {{
        method:'POST', headers:{{'Content-Type':'application/json'}},
        body: JSON.stringify(payload),
      }});
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'Error al guardar');
      selected = payload.domain;
      $('form-panel').classList.remove('open');
      mode = null;
      await loadEntries();
      syncButtons();
      showMsg($('db-msg'), 'Base de datos guardada correctamente.', false);
    }} catch (err) {{
      showMsg($('form-msg'), t(err.message || err), true);
    }}
  }});

  $('btn-eliminar').addEventListener('click', async () => {{
    if (!selected || !confirm(`¿Eliminar la base de datos "${{selected}}"?`)) return;
    try {{
      const res = await fetch(`/api/base_datos/gestion/${{encodeURIComponent(selected)}}`, {{method:'DELETE'}});
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'Error al eliminar');
      selected = null;
      $('form-panel').classList.remove('open');
      await loadEntries();
      syncButtons();
      showMsg($('db-msg'), 'Base de datos eliminada.', false);
    }} catch (err) {{
      showMsg($('db-msg'), t(err.message || err), true);
    }}
  }});

  loadEntries();
  syncButtons();
}})();
</script>
"""


def _setup_login_content() -> str:
    return f"""
<section class="w-full max-w-xl mx-auto">
  <article class="card border border-MAIN-300 bg-MAIN-100 shadow-sm">
    <div class="card-body gap-4">
      <div class="flex" style="justify-content:center;">
        <img src="{BRAND_LOGO_URL}" alt="AVANCOOP" width="144" height="144" style="border-radius:18px; box-shadow:0 8px 32px rgba(15,23,42,.18); object-fit:contain;">
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


def _forbidden_as_not_found() -> HTMLResponse:
    return HTMLResponse(
        """<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>404 — Página no encontrada</title>
<style>
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
background:#f6f7f9;display:flex;align-items:center;justify-content:center;min-height:100vh;}
.box{text-align:center;padding:48px 32px;}
h1{font-size:6rem;font-weight:900;margin:0;color:#d1d5db;letter-spacing:-4px;}
h2{font-size:1.4rem;font-weight:700;margin:12px 0 8px;color:#374151;}
p{color:#6b7280;margin:0 0 24px;}
a{color:#0f766e;text-decoration:none;font-weight:600;}
a:hover{text-decoration:underline;}
</style></head>
<body><div class="box">
<h1>404</h1>
<h2>Página no encontrada</h2>
<p>El recurso solicitado no existe o no está disponible.</p>
<a href="/">← Ir al inicio</a>
</div></body></html>""",
        status_code=403,
    )


@router.get("/base_datos/inicializar", response_class=HTMLResponse)
def database_setup_page(request: Request):
    if _setup_required(request):
        return _standalone_setup_page(
            "Inicializar base de datos",
            _setup_login_content() if not _is_setup_authenticated(request) else _manager_content(),
        )
    if _is_setup_authenticated(request):
        return _standalone_setup_page("Gestión de bases de datos", _manager_content())
    if not is_superadmin(request):
        return _forbidden_as_not_found()
    return _standalone_setup_page("Gestión de bases de datos", _manager_content())


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
        result = bootstrap_installation(payload if isinstance(payload, dict) else {})
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
    if getattr(request.app.state, "database_setup_required", False):
        request.app.state.database_setup_required = not bool(result.get("connected"))
        request.app.state.database_setup_error = str(result.get("error") or "")
    return JSONResponse({"success": True, "result": result, "settings": get_sipet_conf_settings()})


@router.post("/api/base_datos/setup/login")
async def setup_login(request: Request):
    try:
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
    if str(username or "").strip() != _setup_username() or str(password or "") != _setup_password():
        return _standalone_setup_page(
            "Gestión de bases de datos" if not _setup_required(request) else "Inicializar base de datos",
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
