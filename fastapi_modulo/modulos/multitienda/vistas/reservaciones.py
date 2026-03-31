from __future__ import annotations


def reservaciones_html() -> str:
    return _HTML


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Reservaciones — Multitienda</title>
  <style>
    :root {
      --rs-bg: var(--page-bg, #f4f6fb);
      --rs-surface: var(--content-bg, #ffffff);
      --rs-border: var(--field-border, #d1d5db);
      --rs-text: var(--body-text, #1f2937);
      --rs-muted: color-mix(in srgb, var(--body-text, #1f2937) 58%, #ffffff 42%);
      --rs-accent: var(--button-bg, #1a6b3c);
      --rs-accent-fg: var(--button-text, #ffffff);
      --rs-danger: #dc2626;
      --rs-danger-soft: color-mix(in srgb, #dc2626 9%, var(--rs-surface));
      --rs-success: #16a34a;
      --rs-warning: #d97706;
    }
    html, body { margin: 0; padding: 0; background: var(--rs-bg); font-family: system-ui, Arial, sans-serif; color: var(--rs-text); }
    * { box-sizing: border-box; }

    /* ── Toolbar ── */
    .rs-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
    .rs-toolbar__left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

    .rs-btn {
      display: inline-flex; align-items: center; gap: 7px;
      min-height: 38px; padding: 0 16px; border-radius: 10px;
      border: 1px solid var(--rs-border); background: var(--rs-surface);
      color: var(--rs-text); font-size: .86rem; font-weight: 700;
      cursor: pointer; text-decoration: none;
      transition: background .14s, border-color .14s, transform .14s;
    }
    .rs-btn:hover { background: color-mix(in srgb, var(--rs-surface) 85%, var(--rs-bg)); transform: translateY(-1px); }
    .rs-btn--primary { background: var(--rs-accent); color: var(--rs-accent-fg); border-color: var(--rs-accent); }
    .rs-btn--primary:hover { background: color-mix(in srgb, var(--rs-accent) 85%, #000 15%); border-color: color-mix(in srgb, var(--rs-accent) 85%, #000 15%); }
    .rs-btn--danger { color: var(--rs-danger); border-color: color-mix(in srgb, var(--rs-danger) 30%, var(--rs-border)); }
    .rs-btn--danger:hover { background: var(--rs-danger-soft); }
    .rs-btn:disabled { opacity: .4; cursor: not-allowed; transform: none; }

    /* ── Search + filter ── */
    .rs-search {
      display: flex; align-items: center; gap: 8px;
      min-height: 38px; padding: 0 12px;
      border: 1px solid var(--rs-border); border-radius: 10px; background: var(--rs-surface);
    }
    .rs-search input { border: none; outline: none; background: transparent; color: var(--rs-text); font-size: .86rem; width: 200px; }
    .rs-search input::placeholder { color: var(--rs-muted); }
    .rs-filter-select {
      min-height: 38px; padding: 0 10px; border: 1px solid var(--rs-border);
      border-radius: 10px; background: var(--rs-surface); color: var(--rs-text);
      font-size: .84rem; cursor: pointer; outline: none;
    }

    /* ── Stats ── */
    .rs-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 18px; }
    .rs-stat {
      background: var(--rs-surface); border: 1px solid var(--rs-border);
      border-radius: 14px; padding: 14px 16px;
      display: flex; align-items: center; gap: 12px;
    }
    .rs-stat__icon { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; font-size: 1rem; flex-shrink: 0; }
    .rs-stat__icon--blue   { background: #dbeafe; color: #1d4ed8; }
    .rs-stat__icon--green  { background: #dcfce7; color: #15803d; }
    .rs-stat__icon--amber  { background: #fef9c3; color: #b45309; }
    .rs-stat__icon--red    { background: #fee2e2; color: #b91c1c; }
    .rs-stat__value { font-size: 1.4rem; font-weight: 800; letter-spacing: -.03em; line-height: 1; color: var(--rs-text); }
    .rs-stat__label { font-size: .76rem; color: var(--rs-muted); margin-top: 3px; }

    /* ── Table ── */
    .rs-table-wrap { overflow-x: auto; }
    .rs-table { width: 100%; border-collapse: collapse; }
    .rs-table thead tr { border-bottom: 2px solid var(--rs-border); }
    .rs-table th {
      padding: 10px 14px; text-align: left; font-size: .80rem; font-weight: 700;
      color: var(--rs-text); white-space: nowrap; user-select: none;
    }
    .rs-table th.sortable { cursor: pointer; }
    .rs-table th.sortable:hover { color: var(--rs-accent); }
    .rs-table th .sarr { margin-left: 3px; font-size: .68rem; color: var(--rs-muted); }
    .rs-table tbody tr {
      border-bottom: 1px solid color-mix(in srgb, var(--rs-border) 55%, transparent);
      cursor: pointer; transition: background .12s;
    }
    .rs-table tbody tr:hover td { background: color-mix(in srgb, var(--rs-accent) 6%, var(--rs-surface)); }
    .rs-table td { padding: 10px 14px; font-size: .875rem; color: var(--rs-text); vertical-align: middle; }

    /* ── Badges de estado ── */
    .rs-badge {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 3px 10px; border-radius: 999px;
      font-size: .74rem; font-weight: 700; white-space: nowrap;
    }
    .rs-badge i { font-size: .62rem; }
    .rs-badge--confirmed { background: color-mix(in srgb, var(--rs-success) 10%, var(--rs-surface)); color: var(--rs-success); }
    .rs-badge--pending   { background: color-mix(in srgb, var(--rs-warning) 10%, var(--rs-surface)); color: var(--rs-warning); }
    .rs-badge--cancelled { background: var(--rs-danger-soft); color: var(--rs-danger); }
    .rs-badge--completed { background: color-mix(in srgb, #6366f1 10%, var(--rs-surface)); color: #6366f1; }

    .rs-empty { text-align: center; padding: 52px 20px; color: var(--rs-muted); font-size: .9rem; }
    .rs-empty i { font-size: 2.4rem; display: block; margin-bottom: 10px; }

    /* ── Drawer ── */
    .rs-drawer {
      position: fixed; top: 0; right: 0;
      width: min(520px, 100vw); height: 100%;
      background: var(--rs-surface); border-left: 1px solid var(--rs-border);
      box-shadow: -12px 0 40px rgba(0,0,0,.10);
      transform: translateX(100%); transition: transform .22s ease;
      z-index: 800; display: flex; flex-direction: column;
    }
    .rs-drawer.open { transform: translateX(0); }

    .rs-drawer__head {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 20px; border-bottom: 1px solid var(--rs-border); flex-shrink: 0;
    }
    .rs-drawer__title { margin: 0; font-size: 1.05rem; font-weight: 800; color: var(--rs-text); }
    .rs-drawer__close {
      width: 32px; height: 32px; border-radius: 8px; border: 1px solid var(--rs-border);
      background: var(--rs-surface); color: var(--rs-muted); font-size: .9rem;
      cursor: pointer; display: grid; place-items: center;
    }
    .rs-drawer__close:hover { background: var(--rs-bg); }
    .rs-drawer__body { flex: 1; overflow-y: auto; padding: 20px; display: grid; gap: 14px; align-content: start; }
    .rs-drawer__foot {
      padding: 14px 20px; border-top: 1px solid var(--rs-border);
      display: flex; gap: 10px; flex-wrap: wrap; justify-content: space-between;
      flex-shrink: 0; background: var(--rs-surface);
    }
    .rs-drawer__foot-left { display: flex; gap: 8px; }

    /* ── Form fields ── */
    .rs-field { display: grid; gap: 5px; }
    .rs-field label { font-size: .80rem; font-weight: 700; color: var(--rs-text); }
    .rs-input, .rs-select, .rs-textarea {
      padding: 8px 10px; border: 1px solid var(--rs-border); border-radius: 8px;
      font-size: .875rem; background: var(--field-color, var(--rs-surface));
      color: var(--field-text, var(--rs-text)); outline: none;
      transition: border-color .14s, box-shadow .14s;
    }
    .rs-input:focus, .rs-select:focus, .rs-textarea:focus {
      border-color: var(--rs-accent);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--rs-accent) 14%, transparent);
    }
    .rs-textarea { min-height: 72px; resize: vertical; }
    .rs-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .rs-row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
    @media (max-width: 420px) { .rs-row-2, .rs-row-3 { grid-template-columns: 1fr; } }
    .rs-section-label {
      font-size: .74rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
      color: var(--rs-muted); padding-bottom: 6px;
      border-bottom: 1px solid var(--rs-border); margin-bottom: 2px;
    }

    /* ── Confirm ── */
    .rs-confirm { position: fixed; inset: 0; z-index: 900; background: rgba(0,0,0,.46); display: flex; align-items: center; justify-content: center; padding: 20px; }
    .rs-confirm[hidden] { display: none; }
    .rs-confirm__card { width: min(400px, 100%); background: var(--rs-surface); border-radius: 14px; padding: 22px; box-shadow: 0 20px 56px rgba(0,0,0,.18); display: grid; gap: 12px; }
    .rs-confirm__title { margin: 0; font-size: 1rem; font-weight: 800; color: var(--rs-danger); }
    .rs-confirm__msg   { margin: 0; font-size: .88rem; color: var(--rs-muted); }
    .rs-confirm__actions { display: flex; gap: 10px; justify-content: flex-end; }

    /* ── Toast ── */
    .rs-toast {
      position: fixed; bottom: 22px; right: 22px; z-index: 1000;
      background: #1e293b; color: #f1f5f9; padding: 11px 16px;
      border-radius: 10px; font-size: .85rem; font-weight: 600;
      box-shadow: 0 8px 24px rgba(0,0,0,.22);
      transform: translateY(8px); opacity: 0;
      transition: opacity .2s, transform .2s; pointer-events: none;
    }
    .rs-toast.visible { opacity: 1; transform: translateY(0); }
    .rs-toast.success { background: #14532d; }
    .rs-toast.error   { background: #7f1d1d; }

    /* ── Calendar strip ── */
    .rs-cal-strip {
      display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; margin-bottom: 16px;
      scrollbar-width: none;
    }
    .rs-cal-strip::-webkit-scrollbar { display: none; }
    .rs-cal-day {
      flex-shrink: 0; width: 56px; border-radius: 12px; padding: 8px 0;
      border: 1px solid var(--rs-border); background: var(--rs-surface);
      display: flex; flex-direction: column; align-items: center; gap: 2px;
      cursor: pointer; transition: background .14s, border-color .14s;
    }
    .rs-cal-day:hover { background: color-mix(in srgb, var(--rs-accent) 8%, var(--rs-surface)); border-color: color-mix(in srgb, var(--rs-accent) 30%, var(--rs-border)); }
    .rs-cal-day.active { background: var(--rs-accent); border-color: var(--rs-accent); color: var(--rs-accent-fg); }
    .rs-cal-day.has-events::after { content: ''; width: 5px; height: 5px; border-radius: 50%; background: var(--rs-accent); display: block; margin-top: 2px; }
    .rs-cal-day.active.has-events::after { background: rgba(255,255,255,.7); }
    .rs-cal-day__dow { font-size: .68rem; font-weight: 700; text-transform: uppercase; color: inherit; opacity: .7; }
    .rs-cal-day__num { font-size: 1.1rem; font-weight: 800; color: inherit; }
  </style>
</head>
<body>
<main>

  <!-- Toolbar -->
  <div class="rs-toolbar">
    <div class="rs-toolbar__left">
      <button class="rs-btn rs-btn--primary" id="rs-nuevo-btn">
        <i class="fa-solid fa-calendar-plus"></i> Nueva reservación
      </button>
      <button class="rs-btn rs-btn--danger" id="rs-eliminar-btn" disabled>
        <i class="fa-solid fa-trash"></i> Eliminar
      </button>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <select class="rs-filter-select" id="rs-filter-estado">
        <option value="">Todos los estados</option>
        <option value="pendiente">Pendiente</option>
        <option value="confirmada">Confirmada</option>
        <option value="completada">Completada</option>
        <option value="cancelada">Cancelada</option>
      </select>
      <div class="rs-search">
        <i class="fa-solid fa-magnifying-glass" style="color:var(--rs-muted);font-size:.82rem"></i>
        <input id="rs-search" type="search" placeholder="Buscar cliente o servicio…" />
      </div>
    </div>
  </div>

  <!-- Stats -->
  <div class="rs-stats">
    <div class="rs-stat">
      <div class="rs-stat__icon rs-stat__icon--blue"><i class="fa-solid fa-calendar-days"></i></div>
      <div><div class="rs-stat__value" id="rs-stat-total">0</div><div class="rs-stat__label">Total</div></div>
    </div>
    <div class="rs-stat">
      <div class="rs-stat__icon rs-stat__icon--amber"><i class="fa-solid fa-hourglass-half"></i></div>
      <div><div class="rs-stat__value" id="rs-stat-pendientes">0</div><div class="rs-stat__label">Pendientes</div></div>
    </div>
    <div class="rs-stat">
      <div class="rs-stat__icon rs-stat__icon--green"><i class="fa-solid fa-circle-check"></i></div>
      <div><div class="rs-stat__value" id="rs-stat-confirmadas">0</div><div class="rs-stat__label">Confirmadas</div></div>
    </div>
    <div class="rs-stat">
      <div class="rs-stat__icon rs-stat__icon--red"><i class="fa-solid fa-circle-xmark"></i></div>
      <div><div class="rs-stat__value" id="rs-stat-canceladas">0</div><div class="rs-stat__label">Canceladas</div></div>
    </div>
  </div>

  <!-- Calendar strip (próximos 14 días) -->
  <div class="rs-cal-strip" id="rs-cal-strip"></div>

  <!-- Tabla -->
  <div class="rs-table-wrap">
    <table class="rs-table">
      <thead>
        <tr>
          <th style="width:32px"><input type="checkbox" id="rs-select-all" /></th>
          <th class="sortable" data-col="cliente">Cliente <span class="sarr">↕</span></th>
          <th class="sortable" data-col="servicio">Servicio <span class="sarr">↕</span></th>
          <th class="sortable" data-col="fecha">Fecha <span class="sarr">↕</span></th>
          <th class="sortable" data-col="hora">Hora <span class="sarr">↕</span></th>
          <th class="sortable" data-col="estado">Estado <span class="sarr">↕</span></th>
          <th>Contacto</th>
          <th style="width:36px"></th>
        </tr>
      </thead>
      <tbody id="rs-tbody"></tbody>
    </table>
    <div id="rs-empty" class="rs-empty" hidden>
      <i class="fa-regular fa-calendar-xmark"></i>
      Sin reservaciones registradas. Haz clic en <strong>Nueva reservación</strong> para agregar la primera.
    </div>
  </div>

  <!-- Drawer / Formulario -->
  <div class="rs-drawer" id="rs-drawer" role="dialog" aria-modal="true" aria-labelledby="rs-drawer-title">
    <div class="rs-drawer__head">
      <h2 class="rs-drawer__title" id="rs-drawer-title">Nueva reservación</h2>
      <button class="rs-drawer__close" id="rs-drawer-close"><i class="fa-solid fa-xmark"></i></button>
    </div>
    <div class="rs-drawer__body">

      <p class="rs-section-label">Cliente</p>
      <div class="rs-row-2">
        <div class="rs-field">
          <label for="rs-cliente">Nombre del cliente *</label>
          <input class="rs-input" id="rs-cliente" type="text" placeholder="Nombre completo" />
        </div>
        <div class="rs-field">
          <label for="rs-email">Correo electrónico</label>
          <input class="rs-input" id="rs-email" type="email" placeholder="correo@ejemplo.com" />
        </div>
      </div>
      <div class="rs-row-2">
        <div class="rs-field">
          <label for="rs-telefono">Teléfono</label>
          <input class="rs-input" id="rs-telefono" type="tel" placeholder="55 1234 5678" />
        </div>
        <div class="rs-field">
          <label for="rs-personas">N.° de personas</label>
          <input class="rs-input" id="rs-personas" type="number" min="1" step="1" placeholder="1" />
        </div>
      </div>

      <p class="rs-section-label">Reservación</p>
      <div class="rs-field">
        <label for="rs-servicio">Servicio / producto *</label>
        <input class="rs-input" id="rs-servicio" type="text" placeholder="Ej. Mesa para 2, Consulta, Tour guiado…" />
      </div>
      <div class="rs-row-3">
        <div class="rs-field">
          <label for="rs-fecha">Fecha *</label>
          <input class="rs-input" id="rs-fecha" type="date" />
        </div>
        <div class="rs-field">
          <label for="rs-hora">Hora inicio</label>
          <input class="rs-input" id="rs-hora" type="time" />
        </div>
        <div class="rs-field">
          <label for="rs-hora-fin">Hora fin</label>
          <input class="rs-input" id="rs-hora-fin" type="time" />
        </div>
      </div>
      <div class="rs-row-2">
        <div class="rs-field">
          <label for="rs-estado">Estado</label>
          <select class="rs-select" id="rs-estado">
            <option value="pendiente">Pendiente</option>
            <option value="confirmada">Confirmada</option>
            <option value="completada">Completada</option>
            <option value="cancelada">Cancelada</option>
          </select>
        </div>
        <div class="rs-field">
          <label for="rs-monto">Monto ($)</label>
          <input class="rs-input" id="rs-monto" type="number" min="0" step="0.01" placeholder="0.00" />
        </div>
      </div>
      <div class="rs-field">
        <label for="rs-notas">Notas internas</label>
        <textarea class="rs-textarea" id="rs-notas" placeholder="Observaciones, requerimientos especiales…"></textarea>
      </div>

    </div>
    <div class="rs-drawer__foot">
      <div class="rs-drawer__foot-left">
        <button class="rs-btn rs-btn--primary" id="rs-guardar-btn">Guardar</button>
        <button class="rs-btn" id="rs-descartar-btn">Cancelar</button>
      </div>
      <button class="rs-btn rs-btn--danger" id="rs-form-eliminar-btn" style="display:none">
        <i class="fa-solid fa-trash"></i> Eliminar
      </button>
    </div>
  </div>

  <!-- Confirm delete -->
  <div class="rs-confirm" id="rs-confirm" hidden>
    <div class="rs-confirm__card">
      <h3 class="rs-confirm__title"><i class="fa-solid fa-triangle-exclamation"></i> Eliminar reservación(es)</h3>
      <p class="rs-confirm__msg" id="rs-confirm-msg">¿Confirmar eliminación?</p>
      <div class="rs-confirm__actions">
        <button class="rs-btn" id="rs-confirm-cancel">Cancelar</button>
        <button class="rs-btn rs-btn--danger" id="rs-confirm-ok">Eliminar</button>
      </div>
    </div>
  </div>

  <!-- Toast -->
  <div class="rs-toast" id="rs-toast"></div>

</main>
<script>
(function () {
  'use strict';

  var STORAGE_KEY = 'multitienda_reservaciones';

  /* ── State ── */
  var reservaciones = [];
  var filtered  = [];
  var selected  = new Set();
  var editId    = null;
  var pendingDeleteIds = [];
  var sortCol = 'fecha', sortAsc = true;
  var filterEstado = '';
  var filterDia = null;   /* ISO date string YYYY-MM-DD | null = todos */

  /* ── Elements ── */
  var tbody         = document.getElementById('rs-tbody');
  var emptyEl       = document.getElementById('rs-empty');
  var selectAll     = document.getElementById('rs-select-all');
  var searchInput   = document.getElementById('rs-search');
  var filterSelect  = document.getElementById('rs-filter-estado');
  var nuevoBtn      = document.getElementById('rs-nuevo-btn');
  var eliminarBtn   = document.getElementById('rs-eliminar-btn');
  var drawer        = document.getElementById('rs-drawer');
  var drawerTitle   = document.getElementById('rs-drawer-title');
  var drawerClose   = document.getElementById('rs-drawer-close');
  var guardarBtn    = document.getElementById('rs-guardar-btn');
  var descartarBtn  = document.getElementById('rs-descartar-btn');
  var formElimBtn   = document.getElementById('rs-form-eliminar-btn');
  var confirm_      = document.getElementById('rs-confirm');
  var confirmMsg    = document.getElementById('rs-confirm-msg');
  var confirmOk     = document.getElementById('rs-confirm-ok');
  var confirmCancel = document.getElementById('rs-confirm-cancel');
  var toast         = document.getElementById('rs-toast');

  /* ── Persistence ── */
  function load() {
    try { reservaciones = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
    catch (e) { reservaciones = []; }
    reservaciones.forEach(function (r) { if (!r._id) r._id = uid(); });
  }
  function save() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(reservaciones)); }
    catch (e) { showToast('Almacenamiento lleno.', 'error'); }
  }

  /* ── Utils ── */
  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2); }
  function esc(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function fmtDate(iso) {
    if (!iso) return '—';
    try { return new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium' }).format(new Date(iso + 'T12:00:00')); }
    catch (e) { return iso; }
  }
  function fmtTime(t) { return t || '—'; }

  /* ── Toast ── */
  var _toastT;
  function showToast(msg, type) {
    toast.textContent = msg;
    toast.className = 'rs-toast visible' + (type ? ' ' + type : '');
    clearTimeout(_toastT);
    _toastT = setTimeout(function () { toast.className = 'rs-toast'; }, 3000);
  }

  /* ── Stats ── */
  function updateStats() {
    document.getElementById('rs-stat-total').textContent = String(reservaciones.length);
    document.getElementById('rs-stat-pendientes').textContent = String(reservaciones.filter(function(r){ return r.estado === 'pendiente'; }).length);
    document.getElementById('rs-stat-confirmadas').textContent = String(reservaciones.filter(function(r){ return r.estado === 'confirmada'; }).length);
    document.getElementById('rs-stat-canceladas').textContent = String(reservaciones.filter(function(r){ return r.estado === 'cancelada'; }).length);
  }

  /* ── Calendar strip (próximos 14 días) ── */
  function buildCalStrip() {
    var strip = document.getElementById('rs-cal-strip');
    strip.innerHTML = '';
    var today = new Date(); today.setHours(0,0,0,0);
    var dows = ['Do','Lu','Ma','Mi','Ju','Vi','Sa'];
    /* "Todos" pill */
    var all = document.createElement('div');
    all.className = 'rs-cal-day' + (!filterDia ? ' active' : '');
    all.style.width = '64px';
    all.innerHTML = '<span class="rs-cal-day__dow">Todo</span><span class="rs-cal-day__num" style="font-size:.85rem">el mes</span>';
    all.addEventListener('click', function () { filterDia = null; buildCalStrip(); applyFilterSort(); });
    strip.appendChild(all);

    for (var i = 0; i < 14; i++) {
      var d = new Date(today); d.setDate(today.getDate() + i);
      var iso = d.toISOString().slice(0, 10);
      var hasEvents = reservaciones.some(function (r) { return r.fecha === iso; });
      var el = document.createElement('div');
      el.className = 'rs-cal-day' + (filterDia === iso ? ' active' : '') + (hasEvents ? ' has-events' : '');
      el.innerHTML =
        '<span class="rs-cal-day__dow">' + dows[d.getDay()] + '</span>' +
        '<span class="rs-cal-day__num">' + d.getDate() + '</span>';
      el.dataset.iso = iso;
      el.addEventListener('click', function () {
        filterDia = this.dataset.iso === filterDia ? null : this.dataset.iso;
        buildCalStrip(); applyFilterSort();
      });
      strip.appendChild(el);
    }
  }

  /* ── Filter / Sort ── */
  function applyFilterSort() {
    var q = (searchInput.value || '').toLowerCase();
    filtered = reservaciones.filter(function (r) {
      if (filterDia && r.fecha !== filterDia) return false;
      if (filterEstado && r.estado !== filterEstado) return false;
      if (!q) return true;
      return (r.cliente||'').toLowerCase().includes(q) ||
             (r.servicio||'').toLowerCase().includes(q) ||
             (r.email||'').toLowerCase().includes(q);
    });
    filtered.sort(function (a, b) {
      var va = String(a[sortCol] || ''), vb = String(b[sortCol] || '');
      if (sortCol === 'monto') { va = parseFloat(va)||0; vb = parseFloat(vb)||0; return sortAsc ? va-vb : vb-va; }
      return sortAsc ? va.localeCompare(vb, 'es') : vb.localeCompare(va, 'es');
    });
    renderTable();
  }

  /* badge config */
  var BADGE = {
    pendiente:  { cls: 'pending',   label: 'Pendiente',   icon: 'fa-hourglass-half' },
    confirmada: { cls: 'confirmed', label: 'Confirmada',  icon: 'fa-circle-check' },
    completada: { cls: 'completed', label: 'Completada',  icon: 'fa-flag-checkered' },
    cancelada:  { cls: 'cancelled', label: 'Cancelada',   icon: 'fa-circle-xmark' },
  };

  /* ── Render ── */
  function renderTable() {
    tbody.innerHTML = '';
    emptyEl.hidden = filtered.length > 0;
    filtered.forEach(function (r) {
      var tr = document.createElement('tr');
      tr.dataset.id = r._id;
      var b = BADGE[r.estado] || { cls: 'pending', label: r.estado || '—', icon: 'fa-circle' };
      tr.innerHTML =
        '<td><input type="checkbox" class="rs-check" data-id="' + esc(r._id) + '" ' + (selected.has(r._id) ? 'checked' : '') + ' /></td>' +
        '<td><strong>' + esc(r.cliente||'—') + '</strong>' + (r.personas && r.personas > 1 ? ' <span style="font-size:.76rem;color:var(--rs-muted)">×' + r.personas + '</span>' : '') + '</td>' +
        '<td>' + esc(r.servicio||'—') + '</td>' +
        '<td>' + fmtDate(r.fecha) + '</td>' +
        '<td>' + fmtTime(r.hora) + (r.horaFin ? ' – ' + fmtTime(r.horaFin) : '') + '</td>' +
        '<td><span class="rs-badge rs-badge--' + b.cls + '"><i class="fa-solid ' + b.icon + '"></i>' + b.label + '</span></td>' +
        '<td style="font-size:.8rem;color:var(--rs-muted)">' + esc(r.telefono || r.email || '—') + '</td>' +
        '<td><button class="rs-btn" style="min-height:28px;padding:0 10px;font-size:.76rem" data-edit="' + esc(r._id) + '"><i class="fa-solid fa-pen"></i></button></td>';
      tbody.appendChild(tr);
    });
    /* sort arrows */
    document.querySelectorAll('.rs-table th.sortable').forEach(function (th) {
      var sp = th.querySelector('.sarr'); if (!sp) return;
      if (th.dataset.col === sortCol) { sp.textContent = sortAsc ? '↑' : '↓'; sp.style.color = 'var(--rs-accent)'; }
      else { sp.textContent = '↕'; sp.style.color = 'var(--rs-muted)'; }
    });
    syncEliminarBtn();
    updateStats();
    selectAll.checked = filtered.length > 0 && filtered.every(function (r) { return selected.has(r._id); });
    selectAll.indeterminate = !selectAll.checked && filtered.some(function (r) { return selected.has(r._id); });
  }

  /* ── Selection ── */
  function syncEliminarBtn() { eliminarBtn.disabled = selected.size === 0; }

  tbody.addEventListener('change', function (e) {
    var cb = e.target.closest('.rs-check'); if (!cb) return;
    if (cb.checked) selected.add(cb.dataset.id); else selected.delete(cb.dataset.id);
    renderTable();
  });
  selectAll.addEventListener('change', function () {
    filtered.forEach(function (r) { if (selectAll.checked) selected.add(r._id); else selected.delete(r._id); });
    renderTable();
  });
  document.querySelectorAll('.rs-table th.sortable').forEach(function (th) {
    th.addEventListener('click', function () {
      if (sortCol === th.dataset.col) sortAsc = !sortAsc; else { sortCol = th.dataset.col; sortAsc = true; }
      applyFilterSort();
    });
  });
  searchInput.addEventListener('input', applyFilterSort);
  filterSelect.addEventListener('change', function () { filterEstado = this.value; applyFilterSort(); });

  tbody.addEventListener('click', function (e) {
    var editBtn = e.target.closest('[data-edit]');
    if (editBtn) { openDrawer(editBtn.dataset.edit); return; }
    var tr = e.target.closest('tr[data-id]');
    if (tr && !e.target.closest('.rs-check') && !e.target.closest('[data-edit]')) openDrawer(tr.dataset.id);
  });

  /* ── Drawer ── */
  function openDrawer(id) {
    editId = id || null;
    var r = id ? reservaciones.find(function (x) { return x._id === id; }) : null;
    drawerTitle.textContent = r ? 'Editar reservación' : 'Nueva reservación';
    document.getElementById('rs-cliente').value   = r ? (r.cliente  || '') : '';
    document.getElementById('rs-email').value     = r ? (r.email    || '') : '';
    document.getElementById('rs-telefono').value  = r ? (r.telefono || '') : '';
    document.getElementById('rs-personas').value  = r ? (r.personas || '') : '';
    document.getElementById('rs-servicio').value  = r ? (r.servicio || '') : '';
    document.getElementById('rs-fecha').value     = r ? (r.fecha    || '') : '';
    document.getElementById('rs-hora').value      = r ? (r.hora     || '') : '';
    document.getElementById('rs-hora-fin').value  = r ? (r.horaFin  || '') : '';
    document.getElementById('rs-estado').value    = r ? (r.estado   || 'pendiente') : 'pendiente';
    document.getElementById('rs-monto').value     = r ? (r.monto    || '') : '';
    document.getElementById('rs-notas').value     = r ? (r.notas    || '') : '';
    formElimBtn.style.display = r ? '' : 'none';
    drawer.classList.add('open');
    document.getElementById('rs-cliente').focus();
  }

  function closeDrawer() { drawer.classList.remove('open'); editId = null; }

  drawerClose.addEventListener('click', closeDrawer);
  descartarBtn.addEventListener('click', closeDrawer);
  nuevoBtn.addEventListener('click', function () { openDrawer(null); });

  /* ── Save ── */
  guardarBtn.addEventListener('click', function () {
    var cliente = document.getElementById('rs-cliente').value.trim();
    var servicio = document.getElementById('rs-servicio').value.trim();
    var fecha = document.getElementById('rs-fecha').value;
    if (!cliente) { showToast('El nombre del cliente es obligatorio.', 'error'); return; }
    if (!servicio) { showToast('El servicio es obligatorio.', 'error'); return; }
    if (!fecha) { showToast('La fecha es obligatoria.', 'error'); return; }
    var r = {
      cliente:  cliente,
      email:    document.getElementById('rs-email').value.trim(),
      telefono: document.getElementById('rs-telefono').value.trim(),
      personas: document.getElementById('rs-personas').value,
      servicio: servicio,
      fecha:    fecha,
      hora:     document.getElementById('rs-hora').value,
      horaFin:  document.getElementById('rs-hora-fin').value,
      estado:   document.getElementById('rs-estado').value,
      monto:    document.getElementById('rs-monto').value,
      notas:    document.getElementById('rs-notas').value.trim(),
      creadoEn: editId ? (reservaciones.find(function(x){return x._id===editId;})||{}).creadoEn || new Date().toISOString() : new Date().toISOString(),
    };
    if (editId) {
      var idx = reservaciones.findIndex(function (x) { return x._id === editId; });
      if (idx >= 0) { r._id = editId; reservaciones[idx] = r; }
    } else {
      r._id = uid(); reservaciones.push(r);
    }
    save(); closeDrawer(); buildCalStrip(); applyFilterSort();
    showToast(editId ? 'Reservación actualizada.' : 'Reservación registrada.', 'success');
  });

  /* ── Delete ── */
  function askDelete(ids, msg) { pendingDeleteIds = ids; confirmMsg.textContent = msg; confirm_.hidden = false; }
  var pendingDeleteIds = [];

  confirmCancel.addEventListener('click', function () { confirm_.hidden = true; pendingDeleteIds = []; });
  confirmOk.addEventListener('click', function () {
    pendingDeleteIds.forEach(function (id) {
      reservaciones = reservaciones.filter(function (r) { return r._id !== id; });
      selected.delete(id);
    });
    confirm_.hidden = true; pendingDeleteIds = [];
    save(); closeDrawer(); buildCalStrip(); applyFilterSort();
    showToast('Reservación(es) eliminada(s).', 'success');
  });

  eliminarBtn.addEventListener('click', function () {
    if (!selected.size) return;
    askDelete(Array.from(selected), '¿Eliminar ' + selected.size + ' reservación(es)? Esta acción no se puede deshacer.');
  });
  formElimBtn.addEventListener('click', function () {
    if (!editId) return;
    var r = reservaciones.find(function (x) { return x._id === editId; });
    askDelete([editId], '¿Eliminar la reservación de "' + (r ? r.cliente : editId) + '"? Esta acción no se puede deshacer.');
  });

  /* ── Init ── */
  load(); buildCalStrip(); applyFilterSort();
})();
</script>
</body>
</html>
"""
