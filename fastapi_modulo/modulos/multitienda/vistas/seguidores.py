from __future__ import annotations

from html import escape


def seguidores_html(max_users: int = 0) -> str:
    return _HTML.replace("__MAX_USERS__", escape(str(max_users)))


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Seguidores — Multitienda</title>
  <style>
    :root {
      --sg-bg: var(--page-bg, #f4f6fb);
      --sg-surface: var(--content-bg, #ffffff);
      --sg-border: var(--field-border, #d1d5db);
      --sg-text: var(--body-text, #1f2937);
      --sg-muted: color-mix(in srgb, var(--body-text, #1f2937) 58%, #ffffff 42%);
      --sg-accent: var(--button-bg, #1a6b3c);
      --sg-accent-fg: var(--button-text, #ffffff);
      --sg-danger: #dc2626;
      --sg-danger-soft: color-mix(in srgb, #dc2626 9%, var(--sg-surface));
      --sg-success: #16a34a;
      --sg-warning: #d97706;
      --sg-purple: #7c3aed;
    }
    html, body { margin: 0; padding: 0; background: var(--sg-bg); font-family: system-ui, Arial, sans-serif; color: var(--sg-text); }
    * { box-sizing: border-box; }

    /* ── Capacity bar ── */
    .sg-capacity {
      display: flex; align-items: center; gap: 14px;
      background: var(--sg-surface); border: 1px solid var(--sg-border);
      border-radius: 14px; padding: 14px 18px; margin-bottom: 18px;
    }
    .sg-capacity__icon { width: 40px; height: 40px; border-radius: 12px; background: #ede9fe; color: var(--sg-purple); display: grid; place-items: center; font-size: 1rem; flex-shrink: 0; }
    .sg-capacity__info { flex: 1; min-width: 0; }
    .sg-capacity__title { font-size: .86rem; font-weight: 700; margin-bottom: 6px; }
    .sg-capacity__bar-wrap { height: 8px; border-radius: 999px; background: color-mix(in srgb, var(--sg-border) 60%, var(--sg-bg)); overflow: hidden; }
    .sg-capacity__bar { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--sg-purple), #a855f7); transition: width .4s ease; }
    .sg-capacity__bar.is-full { background: linear-gradient(90deg, var(--sg-warning), #ef4444); }
    .sg-capacity__numbers { font-size: .78rem; color: var(--sg-muted); margin-top: 4px; }
    .sg-capacity__tag {
      display: inline-flex; align-items: center; gap: 5px; padding: 4px 12px;
      border-radius: 999px; font-size: .78rem; font-weight: 700; flex-shrink: 0;
      background: #ede9fe; color: var(--sg-purple);
    }
    .sg-capacity__tag.is-full { background: #fee2e2; color: #b91c1c; }

    /* ── Toolbar ── */
    .sg-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
    .sg-toolbar__left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

    /* ── Buttons ── */
    .sg-btn {
      display: inline-flex; align-items: center; gap: 7px;
      min-height: 38px; padding: 0 16px; border-radius: 10px;
      border: 1px solid var(--sg-border); background: var(--sg-surface);
      color: var(--sg-text); font-size: .86rem; font-weight: 700;
      cursor: pointer; text-decoration: none;
      transition: background .14s, border-color .14s, transform .14s;
    }
    .sg-btn:hover { background: color-mix(in srgb, var(--sg-surface) 85%, var(--sg-bg)); transform: translateY(-1px); }
    .sg-btn--primary { background: var(--sg-accent); color: var(--sg-accent-fg); border-color: var(--sg-accent); }
    .sg-btn--primary:hover { background: color-mix(in srgb, var(--sg-accent) 85%, #000 15%); border-color: color-mix(in srgb, var(--sg-accent) 85%, #000 15%); }
    .sg-btn--danger { color: var(--sg-danger); border-color: color-mix(in srgb, var(--sg-danger) 30%, var(--sg-border)); }
    .sg-btn--danger:hover { background: var(--sg-danger-soft); }
    .sg-btn:disabled { opacity: .4; cursor: not-allowed; transform: none; }

    /* ── Search / filters ── */
    .sg-search {
      display: flex; align-items: center; gap: 8px;
      min-height: 38px; padding: 0 12px;
      border: 1px solid var(--sg-border); border-radius: 10px; background: var(--sg-surface);
    }
    .sg-search input { border: none; outline: none; background: transparent; color: var(--sg-text); font-size: .86rem; width: 200px; }
    .sg-search input::placeholder { color: var(--sg-muted); }
    .sg-filter-select {
      min-height: 38px; padding: 0 10px; border: 1px solid var(--sg-border);
      border-radius: 10px; background: var(--sg-surface); color: var(--sg-text);
      font-size: .84rem; cursor: pointer; outline: none;
    }

    /* ── Segmento chips (Intelicoop) ── */
    .sg-seg {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 2px 9px; border-radius: 999px;
      font-size: .72rem; font-weight: 700; white-space: nowrap;
    }
    .sg-seg--hormiga         { background: #fef9c3; color: #854d0e; }
    .sg-seg--gran_ahorrador  { background: #dcfce7; color: #15803d; }
    .sg-seg--inactivo        { background: color-mix(in srgb,var(--sg-border) 40%,var(--sg-surface)); color: var(--sg-muted); }
    .sg-seg--activo          { background: #dbeafe; color: #1d4ed8; }
    .sg-seg--prospecto       { background: #ede9fe; color: var(--sg-purple); }
    .sg-seg--default         { background: #f3f4f6; color: #374151; }

    /* ── Stats row ── */
    .sg-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 18px; }
    .sg-stat {
      background: var(--sg-surface); border: 1px solid var(--sg-border);
      border-radius: 14px; padding: 14px 16px;
      display: flex; align-items: center; gap: 12px;
    }
    .sg-stat__icon { width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center; font-size: .95rem; flex-shrink: 0; }
    .sg-stat__icon--purple { background: #ede9fe; color: var(--sg-purple); }
    .sg-stat__icon--green  { background: #dcfce7; color: #15803d; }
    .sg-stat__icon--amber  { background: #fef9c3; color: #b45309; }
    .sg-stat__icon--blue   { background: #dbeafe; color: #1d4ed8; }
    .sg-stat__value { font-size: 1.35rem; font-weight: 800; letter-spacing: -.03em; line-height: 1; }
    .sg-stat__label { font-size: .74rem; color: var(--sg-muted); margin-top: 2px; }

    /* ── Grid de tarjetas ── */
    .sg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
    .sg-card {
      background: var(--sg-surface); border: 1px solid var(--sg-border);
      border-radius: 16px; padding: 18px; cursor: pointer;
      transition: box-shadow .16s, transform .16s, border-color .16s;
    }
    .sg-card:hover { box-shadow: 0 6px 22px rgba(0,0,0,.08); transform: translateY(-2px); border-color: color-mix(in srgb, var(--sg-purple) 35%, var(--sg-border)); }
    .sg-card__head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
    .sg-card__avatar {
      width: 48px; height: 48px; border-radius: 16px; flex-shrink: 0;
      background: linear-gradient(135deg, var(--sg-purple) 0%, #db2777 100%);
      display: grid; place-items: center; color: #fff;
      font-size: 1.2rem; font-weight: 800; text-transform: uppercase;
    }
    .sg-card__name { font-weight: 700; font-size: .95rem; }
    .sg-card__email { font-size: .78rem; color: var(--sg-muted); }
    .sg-card__meta { display: grid; gap: 5px; }
    .sg-card__row { display: flex; align-items: center; gap: 7px; font-size: .80rem; color: var(--sg-muted); }
    .sg-card__row i { width: 14px; text-align: center; font-size: .75rem; }
    .sg-card__foot { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--sg-border); }

    .sg-empty { text-align: center; padding: 52px 20px; color: var(--sg-muted); font-size: .9rem; }
    .sg-empty i { font-size: 2.4rem; display: block; margin-bottom: 10px; }

    /* ── Drawer ── */
    .sg-drawer {
      position: fixed; top: 0; right: 0;
      width: min(480px, 100vw); height: 100%;
      background: var(--sg-surface); border-left: 1px solid var(--sg-border);
      box-shadow: -12px 0 40px rgba(0,0,0,.10);
      transform: translateX(100%); transition: transform .22s ease;
      z-index: 800; display: flex; flex-direction: column;
    }
    .sg-drawer.is-open { transform: translateX(0); }
    .sg-drawer__head {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 20px; border-bottom: 1px solid var(--sg-border); flex-shrink: 0;
    }
    .sg-drawer__title { font-size: 1rem; font-weight: 700; }
    .sg-drawer__close {
      width: 34px; height: 34px; border-radius: 10px; border: 1px solid var(--sg-border);
      background: transparent; cursor: pointer; display: grid; place-items: center;
      color: var(--sg-muted); transition: background .14s;
    }
    .sg-drawer__close:hover { background: var(--sg-danger-soft); color: var(--sg-danger); }
    .sg-drawer__body { flex: 1; overflow-y: auto; padding: 20px; display: grid; gap: 14px; align-content: start; }
    .sg-drawer__footer {
      padding: 14px 20px; border-top: 1px solid var(--sg-border);
      display: flex; gap: 10px; flex-shrink: 0;
    }
    .sg-drawer__footer .sg-btn { flex: 1; justify-content: center; }

    /* ── Intelicoop link banner ── */
    .sg-intel-banner {
      display: flex; align-items: center; gap: 10px; padding: 10px 14px;
      background: #ede9fe; border: 1px solid #c4b5fd; border-radius: 12px;
      font-size: .82rem; color: var(--sg-purple);
    }
    .sg-intel-banner i { font-size: 1rem; flex-shrink: 0; }
    .sg-intel-banner a { color: var(--sg-purple); font-weight: 700; text-decoration: underline; }

    /* ── Form fields ── */
    .sg-field { display: grid; gap: 5px; }
    .sg-field label { font-size: .80rem; font-weight: 700; color: var(--sg-text); }
    .sg-field input, .sg-field select, .sg-field textarea {
      width: 100%; padding: 8px 12px; border: 1px solid var(--sg-border);
      border-radius: 9px; background: var(--sg-bg); color: var(--sg-text);
      font-size: .88rem; outline: none; transition: border-color .14s;
    }
    .sg-field input:focus, .sg-field select:focus, .sg-field textarea:focus { border-color: var(--sg-purple); }
    .sg-field--row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .sg-field--hint { font-size: .75rem; color: var(--sg-muted); margin-top: 2px; }

    /* ── Overlay ── */
    .sg-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,.32);
      z-index: 799; opacity: 0; pointer-events: none; transition: opacity .2s;
    }
    .sg-overlay.is-open { opacity: 1; pointer-events: all; }

    /* ── Confirm ── */
    .sg-confirm {
      position: fixed; inset: 0; z-index: 900;
      display: flex; align-items: center; justify-content: center;
      background: rgba(0,0,0,.38); opacity: 0; pointer-events: none; transition: opacity .18s;
    }
    .sg-confirm.is-open { opacity: 1; pointer-events: all; }
    .sg-confirm__card {
      background: var(--sg-surface); border: 1px solid var(--sg-border);
      border-radius: 18px; padding: 28px 28px 22px;
      max-width: 360px; width: 90%; text-align: center;
      box-shadow: 0 20px 60px rgba(0,0,0,.15);
    }
    .sg-confirm__icon { font-size: 2rem; color: var(--sg-danger); margin-bottom: 12px; }
    .sg-confirm__title { font-size: 1rem; font-weight: 700; margin-bottom: 8px; }
    .sg-confirm__text { font-size: .86rem; color: var(--sg-muted); margin-bottom: 20px; line-height: 1.5; }
    .sg-confirm__actions { display: flex; gap: 10px; justify-content: center; }
    .sg-confirm__actions .sg-btn { min-width: 110px; justify-content: center; }

    /* ── Toast ── */
    .sg-toast {
      position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%) translateY(20px);
      background: #1f2937; color: #fff; padding: 10px 22px; border-radius: 999px;
      font-size: .86rem; font-weight: 600; z-index: 1000;
      opacity: 0; transition: opacity .2s, transform .2s; pointer-events: none;
    }
    .sg-toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

    /* ── Skeleton ── */
    .sg-skeleton { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
    .sg-skeleton-card { background: var(--sg-surface); border: 1px solid var(--sg-border); border-radius: 16px; padding: 18px; }
    .sg-skeleton-line { height: 12px; border-radius: 6px; background: color-mix(in srgb,var(--sg-border) 70%,var(--sg-bg)); margin-bottom: 8px; }
    @keyframes sg-pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
    .sg-skeleton-card { animation: sg-pulse 1.5s ease-in-out infinite; }
  </style>
</head>
<body>
<main>

  <!-- Capacity bar -->
  <div class="sg-capacity">
    <div class="sg-capacity__icon"><i class="fa-solid fa-user-group"></i></div>
    <div class="sg-capacity__info">
      <div class="sg-capacity__title">Capacidad de seguidores</div>
      <div class="sg-capacity__bar-wrap">
        <div class="sg-capacity__bar" id="sg-cap-bar" style="width:0%"></div>
      </div>
      <div class="sg-capacity__numbers" id="sg-cap-numbers">Cargando…</div>
    </div>
    <div class="sg-capacity__tag" id="sg-cap-tag">0 / __MAX_USERS__</div>
  </div>

  <!-- Stats -->
  <div class="sg-stats">
    <div class="sg-stat">
      <div class="sg-stat__icon sg-stat__icon--purple"><i class="fa-solid fa-users"></i></div>
      <div><div class="sg-stat__value" id="sg-stat-total">0</div><div class="sg-stat__label">Total seguidores</div></div>
    </div>
    <div class="sg-stat">
      <div class="sg-stat__icon sg-stat__icon--green"><i class="fa-solid fa-circle-check"></i></div>
      <div><div class="sg-stat__value" id="sg-stat-activos">0</div><div class="sg-stat__label">Activos</div></div>
    </div>
    <div class="sg-stat">
      <div class="sg-stat__icon sg-stat__icon--blue"><i class="fa-solid fa-user-plus"></i></div>
      <div><div class="sg-stat__value" id="sg-stat-prospectos">0</div><div class="sg-stat__label">Prospectos</div></div>
    </div>
    <div class="sg-stat">
      <div class="sg-stat__icon sg-stat__icon--amber"><i class="fa-solid fa-user-clock"></i></div>
      <div><div class="sg-stat__value" id="sg-stat-inactivos">0</div><div class="sg-stat__label">Inactivos</div></div>
    </div>
  </div>

  <!-- Toolbar -->
  <div class="sg-toolbar">
    <div class="sg-toolbar__left">
      <button class="sg-btn sg-btn--primary" id="sg-nuevo-btn" onclick="openDrawer(null)">
        <i class="fa-solid fa-user-plus"></i> Agregar seguidor
      </button>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
      <select class="sg-filter-select" id="sg-filter-seg" onchange="renderGrid()">
        <option value="">Todos los segmentos</option>
        <option value="activo">Activo</option>
        <option value="prospecto">Prospecto</option>
        <option value="hormiga">Hormiga</option>
        <option value="gran_ahorrador">Gran ahorrador</option>
        <option value="inactivo">Inactivo</option>
      </select>
      <div class="sg-search">
        <i class="fa-solid fa-magnifying-glass" style="color:var(--sg-muted);font-size:.8rem;"></i>
        <input type="text" id="sg-search" placeholder="Buscar nombre o email…" oninput="renderGrid()" />
      </div>
    </div>
  </div>

  <!-- Grid -->
  <div id="sg-container">
    <div class="sg-skeleton">
      <div class="sg-skeleton-card">
        <div class="sg-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="sg-skeleton-line" style="width:80%;"></div>
        <div class="sg-skeleton-line" style="width:60%;"></div>
      </div>
      <div class="sg-skeleton-card">
        <div class="sg-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="sg-skeleton-line" style="width:80%;"></div>
        <div class="sg-skeleton-line" style="width:60%;"></div>
      </div>
      <div class="sg-skeleton-card">
        <div class="sg-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="sg-skeleton-line" style="width:80%;"></div>
        <div class="sg-skeleton-line" style="width:60%;"></div>
      </div>
    </div>
  </div>

  <!-- Confirm -->
  <div class="sg-confirm" id="sg-confirm">
    <div class="sg-confirm__card">
      <div class="sg-confirm__icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div class="sg-confirm__title" id="sg-confirm-title">¿Eliminar seguidor?</div>
      <div class="sg-confirm__text" id="sg-confirm-text">Esta acción no se puede deshacer.</div>
      <div class="sg-confirm__actions">
        <button class="sg-btn" onclick="closeConfirm()">Cancelar</button>
        <button class="sg-btn sg-btn--danger" id="sg-confirm-ok">Sí, eliminar</button>
      </div>
    </div>
  </div>
</main>

<!-- Overlay -->
<div class="sg-overlay" id="sg-overlay" onclick="closeDrawer()"></div>

<!-- Drawer -->
<aside class="sg-drawer" id="sg-drawer">
  <div class="sg-drawer__head">
    <span class="sg-drawer__title" id="sg-drawer-title">Nuevo seguidor</span>
    <button class="sg-drawer__close" onclick="closeDrawer()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="sg-drawer__body">

    <!-- Intelicoop banner -->
    <div class="sg-intel-banner">
      <i class="fa-solid fa-circle-nodes"></i>
      <span>Los seguidores se sincronizan con <a href="/intelicoop" target="_blank">Intelicoop</a> como socios.</span>
    </div>

    <div class="sg-field">
      <label for="sg-f-nombre">Nombre completo <span style="color:var(--sg-danger)">*</span></label>
      <input id="sg-f-nombre" type="text" placeholder="Nombre Apellido" />
    </div>
    <div class="sg-field">
      <label for="sg-f-email">Correo electrónico <span style="color:var(--sg-danger)">*</span></label>
      <input id="sg-f-email" type="email" placeholder="correo@ejemplo.com" />
    </div>
    <div class="sg-field--row">
      <div class="sg-field">
        <label for="sg-f-tel">Teléfono</label>
        <input id="sg-f-tel" type="tel" placeholder="+52 55 1234 5678" />
      </div>
      <div class="sg-field">
        <label for="sg-f-tipo">Tipo de socio</label>
        <select id="sg-f-tipo">
          <option value="activo">Activo</option>
          <option value="prospecto">Prospecto</option>
          <option value="inactivo">Inactivo</option>
        </select>
      </div>
    </div>
    <div class="sg-field">
      <label for="sg-f-segmento">Segmento (Intelicoop)</label>
      <select id="sg-f-segmento">
        <option value="activo">Activo</option>
        <option value="prospecto">Prospecto</option>
        <option value="hormiga">Hormiga</option>
        <option value="gran_ahorrador">Gran ahorrador</option>
        <option value="inactivo">Inactivo</option>
      </select>
    </div>
    <div class="sg-field">
      <label for="sg-f-dir">Dirección</label>
      <input id="sg-f-dir" type="text" placeholder="Ciudad, Estado" />
    </div>
    <div class="sg-field--row">
      <div class="sg-field">
        <label for="sg-f-genero">Género</label>
        <select id="sg-f-genero">
          <option value="">Sin especificar</option>
          <option value="femenino">Femenino</option>
          <option value="masculino">Masculino</option>
          <option value="otro">Otro</option>
        </select>
      </div>
      <div class="sg-field">
        <label for="sg-f-nacimiento">Fecha de nacimiento</label>
        <input id="sg-f-nacimiento" type="date" />
      </div>
    </div>
    <div class="sg-field">
      <label for="sg-f-ocupacion">Ocupación</label>
      <input id="sg-f-ocupacion" type="text" placeholder="Ej. Comerciante" />
    </div>
  </div>
  <div class="sg-drawer__footer">
    <button class="sg-btn sg-btn--danger" id="sg-f-del-btn" onclick="openConfirm('single')" style="display:none;">
      <i class="fa-regular fa-trash-can"></i> Eliminar
    </button>
    <button class="sg-btn sg-btn--primary" onclick="saveSeguidor()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<!-- Toast -->
<div class="sg-toast" id="sg-toast"></div>

<script>
(function () {
  var MAX_USERS = parseInt('__MAX_USERS__', 10) || 0;
  var socios = [];
  var editId = null;
  var confirmCallback = null;

  /* ── Load ── */
  function load() {
    fetch('/api/intelicoop/socios', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        socios = Array.isArray(res) ? res : (res.data || []);
        renderGrid();
        updateCapacity();
        updateStats();
      })
      .catch(function () {
        socios = [];
        renderGrid();
        updateCapacity();
        updateStats();
      });
  }

  /* ── Capacity ── */
  function updateCapacity() {
    var count = socios.length;
    var max   = MAX_USERS;
    var pct   = max > 0 ? Math.min(100, Math.round(count / max * 100)) : 0;
    document.getElementById('sg-cap-bar').style.width = pct + '%';
    document.getElementById('sg-cap-bar').className   = 'sg-capacity__bar' + (count >= max && max > 0 ? ' is-full' : '');
    document.getElementById('sg-cap-numbers').textContent = count + ' seguidor' + (count !== 1 ? 'es' : '') + ' de ' + (max > 0 ? max + ' permitido' + (max !== 1 ? 's' : '') : 'sin límite');
    document.getElementById('sg-cap-tag').textContent  = count + ' / ' + (max > 0 ? max : '∞');
    document.getElementById('sg-cap-tag').className    = 'sg-capacity__tag' + (count >= max && max > 0 ? ' is-full' : '');
    var btn = document.getElementById('sg-nuevo-btn');
    if (btn) btn.disabled = max > 0 && count >= max;
  }

  /* ── Stats ── */
  function updateStats() {
    var total = socios.length, activos = 0, prospectos = 0, inactivos = 0;
    socios.forEach(function (s) {
      var seg = (s.segmento || s.tipo_socio || '').toLowerCase();
      if (seg === 'activo' || seg === 'hormiga' || seg === 'gran_ahorrador') activos++;
      else if (seg === 'prospecto') prospectos++;
      else inactivos++;
    });
    document.getElementById('sg-stat-total').textContent     = total;
    document.getElementById('sg-stat-activos').textContent   = activos;
    document.getElementById('sg-stat-prospectos').textContent= prospectos;
    document.getElementById('sg-stat-inactivos').textContent = inactivos;
  }

  /* ── Grid ── */
  window.renderGrid = function () {
    var q  = (document.getElementById('sg-search').value || '').toLowerCase();
    var fs = document.getElementById('sg-filter-seg').value;
    var rows = socios.filter(function (s) {
      var seg = (s.segmento || s.tipo_socio || '').toLowerCase();
      if (fs && seg !== fs) return false;
      if (q) {
        var hay = ((s.nombre || '') + ' ' + (s.email || '')).toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });
    var container = document.getElementById('sg-container');
    if (!rows.length) {
      container.innerHTML = '<div class="sg-empty"><i class="fa-solid fa-user-group"></i>No hay seguidores que coincidan.</div>';
      return;
    }
    container.innerHTML = '<div class="sg-grid">' + rows.map(function (s) {
      var name     = (s.nombre || s.name || '').trim() || s.email || '?';
      var initials = name.split(' ').slice(0, 2).map(function (p) { return p[0] || ''; }).join('').toUpperCase();
      var seg      = (s.segmento || s.tipo_socio || 'default').toLowerCase();
      var segLabel = segLabels[seg] || seg;
      var regDate  = s.fecha_registro ? s.fecha_registro.slice(0, 10) : '';
      return '<div class="sg-card" onclick="openDrawer(' + s.id + ')">'
        + '<div class="sg-card__head">'
        + '<div class="sg-card__avatar">' + initials + '</div>'
        + '<div><div class="sg-card__name">' + esc(name) + '</div>'
        + '<div class="sg-card__email">' + esc(s.email || '') + '</div></div>'
        + '</div>'
        + '<div class="sg-card__meta">'
        + (s.telefono ? '<div class="sg-card__row"><i class="fa-solid fa-phone"></i>' + esc(s.telefono) + '</div>' : '')
        + (s.ocupacion ? '<div class="sg-card__row"><i class="fa-solid fa-briefcase"></i>' + esc(s.ocupacion) + '</div>' : '')
        + (s.direccion ? '<div class="sg-card__row"><i class="fa-solid fa-location-dot"></i>' + esc(s.direccion) + '</div>' : '')
        + '</div>'
        + '<div class="sg-card__foot">'
        + '<span class="sg-seg sg-seg--' + esc(seg) + '">' + esc(segLabel) + '</span>'
        + (regDate ? '<span style="font-size:.72rem;color:var(--sg-muted);">' + esc(regDate) + '</span>' : '')
        + '</div>'
        + '</div>';
    }).join('') + '</div>';
  };

  var segLabels = {
    activo: 'Activo', prospecto: 'Prospecto',
    hormiga: 'Hormiga', gran_ahorrador: 'Gran ahorrador', inactivo: 'Inactivo',
  };

  /* ── Drawer ── */
  window.openDrawer = function (id) {
    editId = id;
    var s = id !== null ? socios.find(function (x) { return x.id === id; }) : null;
    document.getElementById('sg-drawer-title').textContent = s ? 'Editar seguidor' : 'Nuevo seguidor';
    document.getElementById('sg-f-nombre').value     = s ? (s.nombre || '') : '';
    document.getElementById('sg-f-email').value      = s ? (s.email || '') : '';
    document.getElementById('sg-f-tel').value        = s ? (s.telefono || '') : '';
    document.getElementById('sg-f-tipo').value       = s ? (s.tipo_socio || 'activo') : 'activo';
    document.getElementById('sg-f-segmento').value   = s ? (s.segmento || 'activo') : 'activo';
    document.getElementById('sg-f-dir').value        = s ? (s.direccion || '') : '';
    document.getElementById('sg-f-genero').value     = s ? (s.genero || '') : '';
    document.getElementById('sg-f-nacimiento').value = s ? (s.fecha_nacimiento || '') : '';
    document.getElementById('sg-f-ocupacion').value  = s ? (s.ocupacion || '') : '';
    document.getElementById('sg-f-del-btn').style.display = s ? '' : 'none';
    document.getElementById('sg-drawer').classList.add('is-open');
    document.getElementById('sg-overlay').classList.add('is-open');
  };

  window.closeDrawer = function () {
    document.getElementById('sg-drawer').classList.remove('is-open');
    document.getElementById('sg-overlay').classList.remove('is-open');
    editId = null;
  };

  /* ── Save ── */
  window.saveSeguidor = function () {
    var nombre = (document.getElementById('sg-f-nombre').value || '').trim();
    var email  = (document.getElementById('sg-f-email').value || '').trim();
    if (!nombre) { showToast('El nombre es obligatorio.'); return; }
    if (!email)  { showToast('El correo es obligatorio.'); return; }

    var payload = {
      nombre:          nombre,
      email:           email,
      telefono:        document.getElementById('sg-f-tel').value.trim(),
      tipo_socio:      document.getElementById('sg-f-tipo').value,
      segmento:        document.getElementById('sg-f-segmento').value,
      direccion:       document.getElementById('sg-f-dir').value.trim(),
      genero:          document.getElementById('sg-f-genero').value,
      fecha_nacimiento:document.getElementById('sg-f-nacimiento').value,
      ocupacion:       document.getElementById('sg-f-ocupacion').value.trim(),
    };

    var url    = editId !== null ? '/api/intelicoop/socios/' + editId : '/api/intelicoop/socios';
    var method = editId !== null ? 'PUT' : 'POST';

    fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.id || res.success || res.email) {
          closeDrawer();
          showToast(editId !== null ? 'Seguidor actualizado.' : 'Seguidor agregado.');
          load();
        } else {
          showToast(res.detail || res.error || 'Error al guardar.');
        }
      })
      .catch(function () { showToast('Error de conexión.'); });
  };

  /* ── Confirm / delete ── */
  window.openConfirm = function (mode) {
    var s = editId !== null ? socios.find(function (x) { return x.id === editId; }) : null;
    document.getElementById('sg-confirm-title').textContent = '¿Eliminar "' + ((s && s.nombre) || 'este seguidor') + '"?';
    document.getElementById('sg-confirm-text').textContent  = 'Se eliminará también del módulo Intelicoop.';
    confirmCallback = function () {
      if (editId === null) return;
      fetch('/api/intelicoop/socios/' + editId, {
        method: 'DELETE',
        credentials: 'same-origin',
      })
        .then(function (r) { return r.ok ? {} : r.json(); })
        .then(function (res) {
          closeDrawer();
          showToast('Seguidor eliminado.');
          load();
        })
        .catch(function () { showToast('Error de conexión.'); });
    };
    document.getElementById('sg-confirm').classList.add('is-open');
  };

  window.closeConfirm = function () { document.getElementById('sg-confirm').classList.remove('is-open'); };
  document.getElementById('sg-confirm-ok').addEventListener('click', function () {
    closeConfirm();
    if (confirmCallback) { confirmCallback(); confirmCallback = null; }
  });

  /* ── Helpers ── */
  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function showToast(msg) {
    var t = document.getElementById('sg-toast');
    t.textContent = msg; t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 2800);
  }

  /* ── Init ── */
  load();
})();
</script>
</body>
</html>
"""
