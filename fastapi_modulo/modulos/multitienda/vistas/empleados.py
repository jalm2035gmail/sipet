from __future__ import annotations

from html import escape


def empleados_html(max_users: int = 0) -> str:
    return _HTML.replace("__MAX_USERS__", escape(str(max_users)))


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Equipo — Multitienda</title>
  <style>
    :root {
      --em-bg: var(--page-bg, #f4f6fb);
      --em-surface: var(--content-bg, #ffffff);
      --em-border: var(--field-border, #d1d5db);
      --em-text: var(--body-text, #1f2937);
      --em-muted: color-mix(in srgb, var(--body-text, #1f2937) 58%, #ffffff 42%);
      --em-accent: var(--button-bg, #1a6b3c);
      --em-accent-fg: var(--button-text, #ffffff);
      --em-danger: #dc2626;
      --em-danger-soft: color-mix(in srgb, #dc2626 9%, var(--em-surface));
      --em-success: #16a34a;
      --em-warning: #d97706;
    }
    html, body { margin: 0; padding: 0; background: var(--em-bg); font-family: system-ui, Arial, sans-serif; color: var(--em-text); }
    * { box-sizing: border-box; }

    /* ── Capacity bar ── */
    .em-capacity {
      display: flex; align-items: center; gap: 14px;
      background: var(--em-surface); border: 1px solid var(--em-border);
      border-radius: 14px; padding: 14px 18px; margin-bottom: 18px;
    }
    .em-capacity__icon { width: 40px; height: 40px; border-radius: 12px; background: #dbeafe; color: #1d4ed8; display: grid; place-items: center; font-size: 1rem; flex-shrink: 0; }
    .em-capacity__info { flex: 1; min-width: 0; }
    .em-capacity__title { font-size: .86rem; font-weight: 700; margin-bottom: 6px; }
    .em-capacity__bar-wrap { height: 8px; border-radius: 999px; background: color-mix(in srgb, var(--em-border) 60%, var(--em-bg)); overflow: hidden; }
    .em-capacity__bar { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #1d4ed8, #2563eb); transition: width .4s ease; }
    .em-capacity__bar.is-full { background: linear-gradient(90deg, var(--em-warning), #ef4444); }
    .em-capacity__numbers { font-size: .78rem; color: var(--em-muted); margin-top: 4px; }
    .em-capacity__tag {
      display: inline-flex; align-items: center; gap: 5px; padding: 4px 12px;
      border-radius: 999px; font-size: .78rem; font-weight: 700; flex-shrink: 0;
      background: #dbeafe; color: #1d4ed8;
    }
    .em-capacity__tag.is-full { background: #fee2e2; color: #b91c1c; }

    /* ── Toolbar ── */
    .em-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
    .em-toolbar__left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

    /* ── Buttons ── */
    .em-btn {
      display: inline-flex; align-items: center; gap: 7px;
      min-height: 38px; padding: 0 16px; border-radius: 10px;
      border: 1px solid var(--em-border); background: var(--em-surface);
      color: var(--em-text); font-size: .86rem; font-weight: 700;
      cursor: pointer; text-decoration: none;
      transition: background .14s, border-color .14s, transform .14s;
    }
    .em-btn:hover { background: color-mix(in srgb, var(--em-surface) 85%, var(--em-bg)); transform: translateY(-1px); }
    .em-btn--primary { background: var(--em-accent); color: var(--em-accent-fg); border-color: var(--em-accent); }
    .em-btn--primary:hover { background: color-mix(in srgb, var(--em-accent) 85%, #000 15%); border-color: color-mix(in srgb, var(--em-accent) 85%, #000 15%); }
    .em-btn--danger { color: var(--em-danger); border-color: color-mix(in srgb, var(--em-danger) 30%, var(--em-border)); }
    .em-btn--danger:hover { background: var(--em-danger-soft); }
    .em-btn:disabled { opacity: .4; cursor: not-allowed; transform: none; }

    /* ── Search ── */
    .em-search {
      display: flex; align-items: center; gap: 8px;
      min-height: 38px; padding: 0 12px;
      border: 1px solid var(--em-border); border-radius: 10px; background: var(--em-surface);
    }
    .em-search input { border: none; outline: none; background: transparent; color: var(--em-text); font-size: .86rem; width: 200px; }
    .em-search input::placeholder { color: var(--em-muted); }
    .em-filter-select {
      min-height: 38px; padding: 0 10px; border: 1px solid var(--em-border);
      border-radius: 10px; background: var(--em-surface); color: var(--em-text);
      font-size: .84rem; cursor: pointer; outline: none;
    }

    /* ── Grid de tarjetas ── */
    .em-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
    .em-card {
      background: var(--em-surface); border: 1px solid var(--em-border);
      border-radius: 16px; padding: 18px; cursor: pointer;
      transition: box-shadow .16s, transform .16s, border-color .16s;
    }
    .em-card:hover { box-shadow: 0 6px 22px rgba(0,0,0,.08); transform: translateY(-2px); border-color: color-mix(in srgb, var(--em-accent) 35%, var(--em-border)); }
    .em-card__head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
    .em-card__avatar {
      width: 48px; height: 48px; border-radius: 16px; flex-shrink: 0;
      background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
      display: grid; place-items: center; color: #fff;
      font-size: 1.2rem; font-weight: 800; text-transform: uppercase;
      overflow: hidden;
    }
    .em-card__avatar img { width: 100%; height: 100%; object-fit: cover; border-radius: 16px; }
    .em-card__name { font-weight: 700; font-size: .95rem; }
    .em-card__user { font-size: .78rem; color: var(--em-muted); }
    .em-card__meta { display: grid; gap: 5px; }
    .em-card__row { display: flex; align-items: center; gap: 7px; font-size: .80rem; color: var(--em-muted); }
    .em-card__row i { width: 14px; text-align: center; font-size: .75rem; }
    .em-card__foot { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--em-border); }

    /* ── Badges ── */
    .em-badge {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 2px 9px; border-radius: 999px;
      font-size: .72rem; font-weight: 700;
    }
    .em-badge--active  { background: color-mix(in srgb, var(--em-success) 10%, var(--em-surface)); color: var(--em-success); }
    .em-badge--inactive{ background: var(--em-danger-soft); color: var(--em-danger); }
    .em-badge--role    { background: #ede9fe; color: #7c3aed; }

    .em-empty { text-align: center; padding: 52px 20px; color: var(--em-muted); font-size: .9rem; }
    .em-empty i { font-size: 2.4rem; display: block; margin-bottom: 10px; }

    /* ── Drawer ── */
    .em-drawer {
      position: fixed; top: 0; right: 0;
      width: min(500px, 100vw); height: 100%;
      background: var(--em-surface); border-left: 1px solid var(--em-border);
      box-shadow: -12px 0 40px rgba(0,0,0,.10);
      transform: translateX(100%); transition: transform .22s ease;
      z-index: 800; display: flex; flex-direction: column;
    }
    .em-drawer.is-open { transform: translateX(0); }
    .em-drawer__head {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 20px; border-bottom: 1px solid var(--em-border); flex-shrink: 0;
    }
    .em-drawer__title { font-size: 1rem; font-weight: 700; }
    .em-drawer__close {
      width: 34px; height: 34px; border-radius: 10px; border: 1px solid var(--em-border);
      background: transparent; cursor: pointer; display: grid; place-items: center;
      color: var(--em-muted); transition: background .14s;
    }
    .em-drawer__close:hover { background: var(--em-danger-soft); color: var(--em-danger); }
    .em-drawer__body { flex: 1; overflow-y: auto; padding: 20px; display: grid; gap: 14px; align-content: start; }
    .em-drawer__footer {
      padding: 14px 20px; border-top: 1px solid var(--em-border);
      display: flex; gap: 10px; flex-shrink: 0;
    }
    .em-drawer__footer .em-btn { flex: 1; justify-content: center; }

    /* ── Tabs dentro del drawer ── */
    .em-dtabs { display: flex; gap: 2px; border-bottom: 1px solid var(--em-border); margin-bottom: 16px; }
    .em-dtab {
      padding: 8px 14px; border: none; background: none; font-size: .84rem; font-weight: 700;
      color: var(--em-muted); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px;
    }
    .em-dtab.is-active { color: var(--em-accent); border-bottom-color: var(--em-accent); }
    .em-dpanel { display: none; }
    .em-dpanel.is-active { display: grid; gap: 12px; }

    /* ── Form fields ── */
    .em-field { display: grid; gap: 5px; }
    .em-field label { font-size: .80rem; font-weight: 700; color: var(--em-text); }
    .em-field input, .em-field select, .em-field textarea {
      width: 100%; padding: 8px 12px; border: 1px solid var(--em-border);
      border-radius: 9px; background: var(--em-bg); color: var(--em-text);
      font-size: .88rem; outline: none; transition: border-color .14s;
    }
    .em-field input:focus, .em-field select:focus, .em-field textarea:focus { border-color: var(--em-accent); }
    .em-field--row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .em-field--hint { font-size: .75rem; color: var(--em-muted); margin-top: 2px; }

    /* ── Password section ── */
    .em-pwd-section { background: var(--em-bg); border: 1px solid var(--em-border); border-radius: 12px; padding: 14px; }
    .em-pwd-section h4 { font-size: .84rem; font-weight: 700; margin: 0 0 10px; }
    .em-pwd-row { display: flex; gap: 8px; align-items: flex-end; }
    .em-pwd-row .em-field { flex: 1; }
    .em-pwd-row .em-btn { flex-shrink: 0; min-height: 38px; margin-bottom: 0; }

    /* ── Overlay ── */
    .em-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,.32);
      z-index: 799; opacity: 0; pointer-events: none; transition: opacity .2s;
    }
    .em-overlay.is-open { opacity: 1; pointer-events: all; }

    /* ── Confirm ── */
    .em-confirm {
      position: fixed; inset: 0; z-index: 900;
      display: flex; align-items: center; justify-content: center;
      background: rgba(0,0,0,.38); opacity: 0; pointer-events: none; transition: opacity .18s;
    }
    .em-confirm.is-open { opacity: 1; pointer-events: all; }
    .em-confirm__card {
      background: var(--em-surface); border: 1px solid var(--em-border);
      border-radius: 18px; padding: 28px 28px 22px;
      max-width: 360px; width: 90%; text-align: center;
      box-shadow: 0 20px 60px rgba(0,0,0,.15);
    }
    .em-confirm__icon { font-size: 2rem; color: var(--em-danger); margin-bottom: 12px; }
    .em-confirm__title { font-size: 1rem; font-weight: 700; margin-bottom: 8px; }
    .em-confirm__text { font-size: .86rem; color: var(--em-muted); margin-bottom: 20px; line-height: 1.5; }
    .em-confirm__actions { display: flex; gap: 10px; justify-content: center; }
    .em-confirm__actions .em-btn { min-width: 110px; justify-content: center; }

    /* ── Toast ── */
    .em-toast {
      position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%) translateY(20px);
      background: #1f2937; color: #fff; padding: 10px 22px; border-radius: 999px;
      font-size: .86rem; font-weight: 600; z-index: 1000;
      opacity: 0; transition: opacity .2s, transform .2s; pointer-events: none;
    }
    .em-toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

    /* ── Skeleton loader ── */
    .em-skeleton { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
    .em-skeleton-card { background: var(--em-surface); border: 1px solid var(--em-border); border-radius: 16px; padding: 18px; }
    .em-skeleton-line { height: 12px; border-radius: 6px; background: color-mix(in srgb, var(--em-border) 70%, var(--em-bg)); margin-bottom: 8px; }
    .em-skeleton-line:last-child { margin-bottom: 0; }
    @keyframes em-pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
    .em-skeleton-card { animation: em-pulse 1.5s ease-in-out infinite; }
  </style>
</head>
<body>
<main>

  <!-- Capacity bar -->
  <div class="em-capacity" id="em-capacity">
    <div class="em-capacity__icon"><i class="fa-solid fa-users"></i></div>
    <div class="em-capacity__info">
      <div class="em-capacity__title">Capacidad del equipo</div>
      <div class="em-capacity__bar-wrap">
        <div class="em-capacity__bar" id="em-cap-bar" style="width:0%"></div>
      </div>
      <div class="em-capacity__numbers" id="em-cap-numbers">Cargando…</div>
    </div>
    <div class="em-capacity__tag" id="em-cap-tag">0 / __MAX_USERS__</div>
  </div>

  <!-- Toolbar -->
  <div class="em-toolbar">
    <div class="em-toolbar__left">
      <button class="em-btn em-btn--primary" id="em-nuevo-btn" onclick="openDrawer(-1)">
        <i class="fa-solid fa-user-plus"></i> Agregar integrante
      </button>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
      <select class="em-filter-select" id="em-filter-rol" onchange="renderGrid()">
        <option value="">Todos los roles</option>
        <option value="superadministrador">Superadmin</option>
        <option value="administrador">Administrador</option>
        <option value="usuario">Usuario</option>
      </select>
      <select class="em-filter-select" id="em-filter-estado" onchange="renderGrid()">
        <option value="">Todos los estados</option>
        <option value="Activo">Activo</option>
        <option value="Inactivo">Inactivo</option>
      </select>
      <div class="em-search">
        <i class="fa-solid fa-magnifying-glass" style="color:var(--em-muted);font-size:.8rem;"></i>
        <input type="text" id="em-search" placeholder="Buscar nombre o usuario…" oninput="renderGrid()" />
      </div>
    </div>
  </div>

  <!-- Grid -->
  <div id="em-container">
    <div class="em-skeleton">
      <div class="em-skeleton-card">
        <div class="em-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="em-skeleton-line" style="width:80%;"></div>
        <div class="em-skeleton-line" style="width:60%;"></div>
        <div class="em-skeleton-line" style="width:70%;"></div>
      </div>
      <div class="em-skeleton-card">
        <div class="em-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="em-skeleton-line" style="width:80%;"></div>
        <div class="em-skeleton-line" style="width:60%;"></div>
        <div class="em-skeleton-line" style="width:70%;"></div>
      </div>
      <div class="em-skeleton-card">
        <div class="em-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="em-skeleton-line" style="width:80%;"></div>
        <div class="em-skeleton-line" style="width:60%;"></div>
        <div class="em-skeleton-line" style="width:70%;"></div>
      </div>
    </div>
  </div>

  <!-- Confirm -->
  <div class="em-confirm" id="em-confirm">
    <div class="em-confirm__card">
      <div class="em-confirm__icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div class="em-confirm__title" id="em-confirm-title">¿Desactivar integrante?</div>
      <div class="em-confirm__text" id="em-confirm-text">El usuario perderá acceso al sistema.</div>
      <div class="em-confirm__actions">
        <button class="em-btn" onclick="closeConfirm()">Cancelar</button>
        <button class="em-btn em-btn--danger" id="em-confirm-ok">Confirmar</button>
      </div>
    </div>
  </div>
</main>

<!-- Overlay -->
<div class="em-overlay" id="em-overlay" onclick="closeDrawer()"></div>

<!-- Drawer -->
<aside class="em-drawer" id="em-drawer">
  <div class="em-drawer__head">
    <span class="em-drawer__title" id="em-drawer-title">Nuevo integrante</span>
    <button class="em-drawer__close" onclick="closeDrawer()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="em-drawer__body">
    <!-- Tabs -->
    <div class="em-dtabs">
      <button class="em-dtab is-active" data-tab="info" onclick="showDTab('info')">
        <i class="fa-solid fa-user"></i> Información
      </button>
      <button class="em-dtab" data-tab="acceso" onclick="showDTab('acceso')">
        <i class="fa-solid fa-key"></i> Acceso
      </button>
    </div>

    <!-- Panel: Información -->
    <div class="em-dpanel is-active" id="em-dpanel-info">
      <div class="em-field--row">
        <div class="em-field">
          <label for="em-f-nombre">Nombre completo <span style="color:var(--em-danger)">*</span></label>
          <input id="em-f-nombre" type="text" placeholder="Nombre Apellido" />
        </div>
        <div class="em-field">
          <label for="em-f-puesto">Puesto</label>
          <input id="em-f-puesto" type="text" placeholder="Ej. Encargado de tienda" />
        </div>
      </div>
      <div class="em-field">
        <label for="em-f-departamento">Departamento</label>
        <input id="em-f-departamento" type="text" placeholder="Ej. Ventas" />
      </div>
      <div class="em-field">
        <label for="em-f-correo">Correo electrónico</label>
        <input id="em-f-correo" type="email" placeholder="correo@ejemplo.com" />
      </div>
      <div class="em-field">
        <label for="em-f-celular">Teléfono / celular</label>
        <input id="em-f-celular" type="tel" placeholder="+52 55 1234 5678" />
      </div>
    </div>

    <!-- Panel: Acceso -->
    <div class="em-dpanel" id="em-dpanel-acceso">
      <div class="em-field">
        <label for="em-f-usuario">Usuario (login) <span style="color:var(--em-danger)">*</span></label>
        <input id="em-f-usuario" type="text" placeholder="usuario_login" autocomplete="off" />
        <span class="em-field--hint">Nombre de usuario para iniciar sesión. Sin espacios.</span>
      </div>
      <div class="em-field">
        <label for="em-f-rol">Rol</label>
        <select id="em-f-rol">
          <option value="usuario">Usuario</option>
          <option value="administrador">Administrador</option>
        </select>
      </div>
      <div class="em-field">
        <label for="em-f-estado">Estado</label>
        <select id="em-f-estado">
          <option value="activo">Activo</option>
          <option value="inactivo">Inactivo</option>
        </select>
      </div>

      <!-- Password block (only for new) -->
      <div class="em-pwd-section" id="em-pwd-new-block">
        <h4><i class="fa-solid fa-lock" style="margin-right:6px;color:var(--em-muted);"></i>Contraseña inicial</h4>
        <div class="em-field">
          <label for="em-f-pwd">Contraseña <span style="color:var(--em-danger)">*</span></label>
          <input id="em-f-pwd" type="password" placeholder="Contraseña de acceso" autocomplete="new-password" />
        </div>
      </div>

      <!-- Password block (only for existing) -->
      <div class="em-pwd-section" id="em-pwd-change-block" style="display:none;">
        <h4><i class="fa-solid fa-lock-open" style="margin-right:6px;color:var(--em-muted);"></i>Cambiar contraseña</h4>
        <div class="em-pwd-row">
          <div class="em-field">
            <label for="em-f-newpwd">Nueva contraseña</label>
            <input id="em-f-newpwd" type="password" placeholder="Dejar vacío para no cambiar" autocomplete="new-password" />
          </div>
          <button class="em-btn" onclick="changePwd()">
            <i class="fa-solid fa-floppy-disk"></i> Guardar
          </button>
        </div>
      </div>
    </div>
  </div>
  <div class="em-drawer__footer">
    <button class="em-btn em-btn--danger" id="em-f-toggle-btn" onclick="openConfirm('toggle')" style="display:none;">
      <i class="fa-solid fa-user-slash"></i> Desactivar
    </button>
    <button class="em-btn em-btn--primary" onclick="saveEmployee()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<!-- Toast -->
<div class="em-toast" id="em-toast"></div>

<script>
(function () {
  var MAX_USERS = parseInt('__MAX_USERS__', 10) || 0;
  var employees = [];
  var editId = null; // null = new

  /* ── Load from API ── */
  function loadEmployees() {
    fetch('/api/colaboradores', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.success) {
          employees = res.data || [];
        } else {
          employees = [];
        }
        renderGrid();
        updateCapacity();
      })
      .catch(function () {
        employees = [];
        renderGrid();
        updateCapacity();
      });
  }

  /* ── Capacity bar ── */
  function updateCapacity() {
    var count = employees.length;
    var max   = MAX_USERS;
    var pct   = max > 0 ? Math.min(100, Math.round(count / max * 100)) : 0;
    var bar   = document.getElementById('em-cap-bar');
    var nums  = document.getElementById('em-cap-numbers');
    var tag   = document.getElementById('em-cap-tag');
    var btn   = document.getElementById('em-nuevo-btn');
    bar.style.width = pct + '%';
    bar.className   = 'em-capacity__bar' + (count >= max && max > 0 ? ' is-full' : '');
    nums.textContent = count + ' integrante' + (count !== 1 ? 's' : '') + ' de ' + (max > 0 ? max + ' permitido' + (max !== 1 ? 's' : '') : 'sin límite');
    tag.textContent  = count + ' / ' + (max > 0 ? max : '∞');
    tag.className    = 'em-capacity__tag' + (count >= max && max > 0 ? ' is-full' : '');
    if (btn) btn.disabled = max > 0 && count >= max;
  }

  /* ── Grid ── */
  window.renderGrid = function () {
    var q  = (document.getElementById('em-search').value || '').toLowerCase();
    var fr = document.getElementById('em-filter-rol').value.toLowerCase();
    var fe = document.getElementById('em-filter-estado').value.toLowerCase();

    var rows = employees.filter(function (e) {
      if (fr && (e.rol || '').toLowerCase() !== fr) return false;
      if (fe && (e.estado || '').toLowerCase() !== fe.toLowerCase()) return false;
      if (q) {
        var hay = ((e.nombre || '') + ' ' + (e.full_name || '') + ' ' + (e.usuario || '')).toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });

    var container = document.getElementById('em-container');
    if (!rows.length) {
      container.innerHTML = '<div class="em-empty"><i class="fa-solid fa-users"></i>No hay integrantes que coincidan.</div>';
      return;
    }

    container.innerHTML = '<div class="em-grid">' + rows.map(function (e) {
      var name    = (e.full_name || e.nombre || '').trim() || e.usuario || '?';
      var initials = name.split(' ').slice(0, 2).map(function (p) { return p[0] || ''; }).join('').toUpperCase();
      var avatar  = e.imagen
        ? '<img src="' + esc(e.imagen) + '" alt="' + esc(name) + '" />'
        : initials;
      var isActive = (e.estado || 'Activo').toLowerCase() !== 'inactivo';
      var badgeEstado = isActive
        ? '<span class="em-badge em-badge--active"><i class="fa-solid fa-circle" style="font-size:.5rem;"></i>Activo</span>'
        : '<span class="em-badge em-badge--inactive"><i class="fa-solid fa-circle" style="font-size:.5rem;"></i>Inactivo</span>';
      var rolLabel = rolNice(e.rol || 'usuario');
      return '<div class="em-card" onclick="openDrawer(' + e.id + ')">'
        + '<div class="em-card__head">'
        + '<div class="em-card__avatar">' + avatar + '</div>'
        + '<div><div class="em-card__name">' + esc(name) + '</div>'
        + '<div class="em-card__user">@' + esc(e.usuario || '') + '</div></div>'
        + '</div>'
        + '<div class="em-card__meta">'
        + (e.puesto ? '<div class="em-card__row"><i class="fa-solid fa-briefcase"></i>' + esc(e.puesto) + '</div>' : '')
        + (e.departamento ? '<div class="em-card__row"><i class="fa-solid fa-building"></i>' + esc(e.departamento) + '</div>' : '')
        + (e.correo ? '<div class="em-card__row"><i class="fa-solid fa-envelope"></i>' + esc(e.correo) + '</div>' : '')
        + '</div>'
        + '<div class="em-card__foot">'
        + '<span class="em-badge em-badge--role">' + esc(rolLabel) + '</span>'
        + badgeEstado
        + '</div>'
        + '</div>';
    }).join('') + '</div>';
  };

  function rolNice(r) {
    var m = { superadministrador: 'Superadmin', administrador: 'Admin', usuario: 'Usuario' };
    return m[(r || '').toLowerCase()] || r;
  }

  /* ── Drawer tabs ── */
  window.showDTab = function (id) {
    document.querySelectorAll('.em-dtab').forEach(function (t) { t.classList.toggle('is-active', t.dataset.tab === id); });
    document.querySelectorAll('.em-dpanel').forEach(function (p) { p.classList.toggle('is-active', p.id === 'em-dpanel-' + id); });
  };

  /* ── Open drawer ── */
  window.openDrawer = function (id) {
    editId = id === -1 ? null : id;
    showDTab('info');

    var emp = editId !== null ? employees.find(function (e) { return e.id === editId; }) : null;
    document.getElementById('em-drawer-title').textContent = emp ? 'Editar integrante' : 'Nuevo integrante';
    document.getElementById('em-f-nombre').value      = emp ? (emp.full_name || emp.nombre || '') : '';
    document.getElementById('em-f-puesto').value      = emp ? (emp.puesto || '') : '';
    document.getElementById('em-f-departamento').value= emp ? (emp.departamento || '') : '';
    document.getElementById('em-f-correo').value      = emp ? (emp.correo || '') : '';
    document.getElementById('em-f-celular').value     = emp ? (emp.celular || '') : '';
    document.getElementById('em-f-usuario').value     = emp ? (emp.usuario || '') : '';
    document.getElementById('em-f-rol').value         = emp ? (emp.rol || 'usuario').toLowerCase() : 'usuario';
    var isActive = emp ? (emp.estado || 'Activo').toLowerCase() !== 'inactivo' : true;
    document.getElementById('em-f-estado').value      = isActive ? 'activo' : 'inactivo';
    document.getElementById('em-f-pwd').value         = '';
    document.getElementById('em-f-newpwd').value      = '';

    // Blocks
    document.getElementById('em-pwd-new-block').style.display    = emp ? 'none' : '';
    document.getElementById('em-pwd-change-block').style.display = emp ? '' : 'none';
    var toggleBtn = document.getElementById('em-f-toggle-btn');
    toggleBtn.style.display = emp ? '' : 'none';
    if (emp) {
      toggleBtn.innerHTML = isActive
        ? '<i class="fa-solid fa-user-slash"></i> Desactivar'
        : '<i class="fa-solid fa-user-check"></i> Activar';
      toggleBtn.className = isActive ? 'em-btn em-btn--danger' : 'em-btn';
    }

    document.getElementById('em-drawer').classList.add('is-open');
    document.getElementById('em-overlay').classList.add('is-open');
  };

  window.closeDrawer = function () {
    document.getElementById('em-drawer').classList.remove('is-open');
    document.getElementById('em-overlay').classList.remove('is-open');
    editId = null;
  };

  /* ── Save ── */
  window.saveEmployee = function () {
    var nombre  = (document.getElementById('em-f-nombre').value || '').trim();
    var usuario = (document.getElementById('em-f-usuario').value || '').trim();
    var correo  = (document.getElementById('em-f-correo').value || '').trim();
    var pwd     = document.getElementById('em-f-pwd').value;
    var isNew   = editId === null;

    if (!nombre)  { showToast('El nombre es obligatorio.'); showDTab('info');   return; }
    if (!usuario) { showToast('El usuario es obligatorio.'); showDTab('acceso'); return; }
    if (isNew && !pwd) { showToast('La contraseña es obligatoria para nuevos integrantes.'); showDTab('acceso'); return; }

    var payload = {
      nombre:       nombre,
      full_name:    nombre,
      usuario:      usuario,
      correo:       correo,
      puesto:       document.getElementById('em-f-puesto').value.trim(),
      departamento: document.getElementById('em-f-departamento').value.trim(),
      celular:      document.getElementById('em-f-celular').value.trim(),
      rol:          document.getElementById('em-f-rol').value,
      colaborador:  true,
    };
    if (isNew) {
      payload.contrasena = pwd;
    } else {
      payload.id = editId;
    }

    fetch('/api/colaboradores', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.success) {
          closeDrawer();
          showToast(isNew ? 'Integrante agregado.' : 'Integrante actualizado.');
          loadEmployees();
        } else {
          showToast(res.error || 'Error al guardar.');
        }
      })
      .catch(function () { showToast('Error de conexión.'); });
  };

  /* ── Change password ── */
  window.changePwd = function () {
    var pwd = (document.getElementById('em-f-newpwd').value || '').trim();
    if (!pwd) { showToast('Ingresa una nueva contraseña.'); return; }
    if (editId === null) { showToast('Guarda el integrante primero.'); return; }
    fetch('/api/colaboradores/' + editId + '/password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ password: pwd }),
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.success) {
          document.getElementById('em-f-newpwd').value = '';
          showToast('Contraseña actualizada.');
        } else {
          showToast(res.error || 'Error al cambiar contraseña.');
        }
      })
      .catch(function () { showToast('Error de conexión.'); });
  };

  /* ── Toggle active/inactive ── */
  var confirmCallback = null;
  window.openConfirm = function (mode) {
    var emp = editId !== null ? employees.find(function (e) { return e.id === editId; }) : null;
    if (!emp) return;
    var isActive = (emp.estado || 'Activo').toLowerCase() !== 'inactivo';
    document.getElementById('em-confirm-title').textContent = isActive ? '¿Desactivar integrante?' : '¿Activar integrante?';
    document.getElementById('em-confirm-text').textContent  = isActive
      ? 'El usuario no podrá iniciar sesión hasta que sea reactivado.'
      : 'El usuario podrá volver a iniciar sesión.';
    document.getElementById('em-confirm-ok').textContent = isActive ? 'Sí, desactivar' : 'Sí, activar';
    document.getElementById('em-confirm-ok').className   = isActive ? 'em-btn em-btn--danger' : 'em-btn em-btn--primary';
    confirmCallback = function () {
      var newEstado = isActive ? 'inactivo' : 'activo';
      fetch('/api/colaboradores', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ id: editId, estado: newEstado }),
      })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (res.success) {
            closeDrawer();
            showToast(isActive ? 'Integrante desactivado.' : 'Integrante activado.');
            loadEmployees();
          } else {
            showToast(res.error || 'Error.');
          }
        })
        .catch(function () { showToast('Error de conexión.'); });
    };
    document.getElementById('em-confirm').classList.add('is-open');
  };
  window.closeConfirm = function () { document.getElementById('em-confirm').classList.remove('is-open'); };
  document.getElementById('em-confirm-ok').addEventListener('click', function () {
    closeConfirm();
    if (confirmCallback) { confirmCallback(); confirmCallback = null; }
  });

  /* ── Helpers ── */
  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function showToast(msg) {
    var t = document.getElementById('em-toast');
    t.textContent = msg; t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 2800);
  }

  /* ── Init ── */
  loadEmployees();
})();
</script>
</body>
</html>
"""
