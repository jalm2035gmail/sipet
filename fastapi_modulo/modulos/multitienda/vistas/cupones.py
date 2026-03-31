from __future__ import annotations


def cupones_html() -> str:
    return _HTML


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cupones — Multitienda</title>
  <style>
    :root {
      --cp-bg: var(--page-bg, #f4f6fb);
      --cp-surface: var(--content-bg, #ffffff);
      --cp-border: var(--field-border, #d1d5db);
      --cp-text: var(--body-text, #1f2937);
      --cp-muted: color-mix(in srgb, var(--body-text, #1f2937) 58%, #ffffff 42%);
      --cp-accent: var(--button-bg, #1a6b3c);
      --cp-accent-fg: var(--button-text, #ffffff);
      --cp-danger: #dc2626;
      --cp-danger-soft: color-mix(in srgb, #dc2626 9%, var(--cp-surface));
      --cp-success: #16a34a;
      --cp-warning: #d97706;
    }
    html, body { margin: 0; padding: 0; background: var(--cp-bg); font-family: system-ui, Arial, sans-serif; color: var(--cp-text); }
    * { box-sizing: border-box; }

    /* ── Toolbar ── */
    .cp-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
    .cp-toolbar__left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

    .cp-btn {
      display: inline-flex; align-items: center; gap: 7px;
      min-height: 38px; padding: 0 16px; border-radius: 10px;
      border: 1px solid var(--cp-border); background: var(--cp-surface);
      color: var(--cp-text); font-size: .86rem; font-weight: 700;
      cursor: pointer; text-decoration: none;
      transition: background .14s, border-color .14s, transform .14s;
    }
    .cp-btn:hover { background: color-mix(in srgb, var(--cp-surface) 85%, var(--cp-bg)); transform: translateY(-1px); }
    .cp-btn--primary { background: var(--cp-accent); color: var(--cp-accent-fg); border-color: var(--cp-accent); }
    .cp-btn--primary:hover { background: color-mix(in srgb, var(--cp-accent) 85%, #000 15%); border-color: color-mix(in srgb, var(--cp-accent) 85%, #000 15%); }
    .cp-btn--danger { color: var(--cp-danger); border-color: color-mix(in srgb, var(--cp-danger) 30%, var(--cp-border)); }
    .cp-btn--danger:hover { background: var(--cp-danger-soft); }
    .cp-btn:disabled { opacity: .4; cursor: not-allowed; transform: none; }

    /* ── Search ── */
    .cp-search {
      display: flex; align-items: center; gap: 8px;
      min-height: 38px; padding: 0 12px;
      border: 1px solid var(--cp-border); border-radius: 10px; background: var(--cp-surface);
    }
    .cp-search input { border: none; outline: none; background: transparent; color: var(--cp-text); font-size: .86rem; width: 200px; }
    .cp-search input::placeholder { color: var(--cp-muted); }
    .cp-filter-select {
      min-height: 38px; padding: 0 10px; border: 1px solid var(--cp-border);
      border-radius: 10px; background: var(--cp-surface); color: var(--cp-text);
      font-size: .84rem; cursor: pointer; outline: none;
    }

    /* ── Stats ── */
    .cp-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 18px; }
    .cp-stat {
      background: var(--cp-surface); border: 1px solid var(--cp-border);
      border-radius: 14px; padding: 14px 16px;
      display: flex; align-items: center; gap: 12px;
    }
    .cp-stat__icon { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; font-size: 1rem; flex-shrink: 0; }
    .cp-stat__icon--blue   { background: #dbeafe; color: #1d4ed8; }
    .cp-stat__icon--green  { background: #dcfce7; color: #15803d; }
    .cp-stat__icon--amber  { background: #fef9c3; color: #b45309; }
    .cp-stat__icon--red    { background: #fee2e2; color: #b91c1c; }
    .cp-stat__value { font-size: 1.4rem; font-weight: 800; letter-spacing: -.03em; line-height: 1; color: var(--cp-text); }
    .cp-stat__label { font-size: .76rem; color: var(--cp-muted); margin-top: 3px; }

    /* ── Table ── */
    .cp-table-wrap { overflow-x: auto; }
    .cp-table { width: 100%; border-collapse: collapse; }
    .cp-table thead tr { border-bottom: 2px solid var(--cp-border); }
    .cp-table th {
      padding: 10px 14px; text-align: left; font-size: .80rem; font-weight: 700;
      color: var(--cp-text); white-space: nowrap; user-select: none;
    }
    .cp-table th.sortable { cursor: pointer; }
    .cp-table th.sortable:hover { color: var(--cp-accent); }
    .cp-table th .sarr { margin-left: 3px; font-size: .68rem; color: var(--cp-muted); }
    .cp-table tbody tr {
      border-bottom: 1px solid color-mix(in srgb, var(--cp-border) 55%, transparent);
      cursor: pointer; transition: background .12s;
    }
    .cp-table tbody tr:hover td { background: color-mix(in srgb, var(--cp-accent) 6%, var(--cp-surface)); }
    .cp-table td { padding: 10px 14px; font-size: .875rem; color: var(--cp-text); vertical-align: middle; }

    /* ── Code chip ── */
    .cp-code-chip {
      display: inline-block; padding: 2px 10px; border-radius: 8px;
      background: color-mix(in srgb, var(--cp-accent) 10%, var(--cp-surface));
      color: var(--cp-accent); font-family: monospace; font-size: .82rem; font-weight: 700;
      letter-spacing: .04em;
    }

    /* ── Badges ── */
    .cp-badge {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 3px 10px; border-radius: 999px;
      font-size: .74rem; font-weight: 700; white-space: nowrap;
    }
    .cp-badge i { font-size: .62rem; }
    .cp-badge--active    { background: color-mix(in srgb, var(--cp-success) 10%, var(--cp-surface)); color: var(--cp-success); }
    .cp-badge--expired   { background: var(--cp-danger-soft); color: var(--cp-danger); }
    .cp-badge--disabled  { background: color-mix(in srgb, var(--cp-muted) 10%, var(--cp-surface)); color: var(--cp-muted); }
    .cp-badge--scheduled { background: color-mix(in srgb, var(--cp-warning) 10%, var(--cp-surface)); color: var(--cp-warning); }

    .cp-empty { text-align: center; padding: 52px 20px; color: var(--cp-muted); font-size: .9rem; }
    .cp-empty i { font-size: 2.4rem; display: block; margin-bottom: 10px; }

    /* ── Drawer ── */
    .cp-drawer {
      position: fixed; top: 0; right: 0;
      width: min(480px, 100vw); height: 100%;
      background: var(--cp-surface); border-left: 1px solid var(--cp-border);
      box-shadow: -12px 0 40px rgba(0,0,0,.10);
      transform: translateX(100%); transition: transform .22s ease;
      z-index: 800; display: flex; flex-direction: column;
    }
    .cp-drawer.is-open { transform: translateX(0); }
    .cp-drawer__head {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 20px; border-bottom: 1px solid var(--cp-border);
      flex-shrink: 0;
    }
    .cp-drawer__title { font-size: 1rem; font-weight: 700; color: var(--cp-text); }
    .cp-drawer__close {
      width: 34px; height: 34px; border-radius: 10px; border: 1px solid var(--cp-border);
      background: transparent; cursor: pointer; display: grid; place-items: center;
      color: var(--cp-muted); transition: background .14s;
    }
    .cp-drawer__close:hover { background: var(--cp-danger-soft); color: var(--cp-danger); }
    .cp-drawer__body { flex: 1; overflow-y: auto; padding: 20px; display: grid; gap: 14px; align-content: start; }
    .cp-drawer__footer {
      padding: 14px 20px; border-top: 1px solid var(--cp-border);
      display: flex; gap: 10px; flex-shrink: 0;
    }
    .cp-drawer__footer .cp-btn { flex: 1; justify-content: center; }

    /* ── Form fields ── */
    .cp-field { display: grid; gap: 5px; }
    .cp-field label { font-size: .80rem; font-weight: 700; color: var(--cp-text); }
    .cp-field input, .cp-field select, .cp-field textarea {
      width: 100%; padding: 8px 12px; border: 1px solid var(--cp-border);
      border-radius: 9px; background: var(--cp-bg); color: var(--cp-text);
      font-size: .88rem; outline: none; transition: border-color .14s;
    }
    .cp-field input:focus, .cp-field select:focus, .cp-field textarea:focus { border-color: var(--cp-accent); }
    .cp-field textarea { resize: vertical; min-height: 70px; }
    .cp-field--row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .cp-field--hint { font-size: .75rem; color: var(--cp-muted); margin-top: 2px; }

    /* ── Overlay ── */
    .cp-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,.32);
      z-index: 799; opacity: 0; pointer-events: none; transition: opacity .2s;
    }
    .cp-overlay.is-open { opacity: 1; pointer-events: all; }

    /* ── Confirm dialog ── */
    .cp-confirm {
      position: fixed; inset: 0; z-index: 900;
      display: flex; align-items: center; justify-content: center;
      background: rgba(0,0,0,.38); opacity: 0; pointer-events: none; transition: opacity .18s;
    }
    .cp-confirm.is-open { opacity: 1; pointer-events: all; }
    .cp-confirm__card {
      background: var(--cp-surface); border: 1px solid var(--cp-border);
      border-radius: 18px; padding: 28px 28px 22px;
      max-width: 360px; width: 90%; text-align: center;
      box-shadow: 0 20px 60px rgba(0,0,0,.15);
    }
    .cp-confirm__icon { font-size: 2rem; color: var(--cp-danger); margin-bottom: 12px; }
    .cp-confirm__title { font-size: 1rem; font-weight: 700; margin-bottom: 8px; }
    .cp-confirm__text { font-size: .86rem; color: var(--cp-muted); margin-bottom: 20px; line-height: 1.5; }
    .cp-confirm__actions { display: flex; gap: 10px; justify-content: center; }
    .cp-confirm__actions .cp-btn { min-width: 110px; justify-content: center; }

    /* ── Toast ── */
    .cp-toast {
      position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%) translateY(20px);
      background: #1f2937; color: #fff; padding: 10px 22px; border-radius: 999px;
      font-size: .86rem; font-weight: 600; z-index: 1000;
      opacity: 0; transition: opacity .2s, transform .2s; pointer-events: none;
    }
    .cp-toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
  </style>
</head>
<body>
<main>
  <!-- Stats -->
  <div class="cp-stats">
    <div class="cp-stat">
      <div class="cp-stat__icon cp-stat__icon--blue"><i class="fa-solid fa-ticket"></i></div>
      <div><div class="cp-stat__value" id="cp-stat-total">0</div><div class="cp-stat__label">Total cupones</div></div>
    </div>
    <div class="cp-stat">
      <div class="cp-stat__icon cp-stat__icon--green"><i class="fa-solid fa-circle-check"></i></div>
      <div><div class="cp-stat__value" id="cp-stat-activos">0</div><div class="cp-stat__label">Activos</div></div>
    </div>
    <div class="cp-stat">
      <div class="cp-stat__icon cp-stat__icon--amber"><i class="fa-solid fa-clock-rotate-left"></i></div>
      <div><div class="cp-stat__value" id="cp-stat-usados">0</div><div class="cp-stat__label">Usos totales</div></div>
    </div>
    <div class="cp-stat">
      <div class="cp-stat__icon cp-stat__icon--red"><i class="fa-solid fa-calendar-xmark"></i></div>
      <div><div class="cp-stat__value" id="cp-stat-expirados">0</div><div class="cp-stat__label">Expirados</div></div>
    </div>
  </div>

  <!-- Toolbar -->
  <div class="cp-toolbar">
    <div class="cp-toolbar__left">
      <button class="cp-btn cp-btn--primary" id="cp-nuevo-btn" onclick="openDrawer(-1)">
        <i class="fa-solid fa-plus"></i> Nuevo cupón
      </button>
      <button class="cp-btn cp-btn--danger" id="cp-eliminar-btn" disabled onclick="openConfirm('bulk')">
        <i class="fa-regular fa-trash-can"></i> Eliminar
      </button>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
      <select class="cp-filter-select" id="cp-filter-estado" onchange="renderTable()">
        <option value="">Todos los estados</option>
        <option value="activo">Activo</option>
        <option value="programado">Programado</option>
        <option value="desactivado">Desactivado</option>
        <option value="expirado">Expirado</option>
      </select>
      <select class="cp-filter-select" id="cp-filter-tipo" onchange="renderTable()">
        <option value="">Todos los tipos</option>
        <option value="porcentaje">Porcentaje</option>
        <option value="monto">Monto fijo</option>
        <option value="envio">Envío gratis</option>
      </select>
      <div class="cp-search">
        <i class="fa-solid fa-magnifying-glass" style="color:var(--cp-muted);font-size:.8rem;"></i>
        <input type="text" id="cp-search" placeholder="Buscar código o descripción…" oninput="renderTable()" />
      </div>
    </div>
  </div>

  <!-- Table -->
  <div class="cp-table-wrap">
    <table class="cp-table" id="cp-table">
      <thead>
        <tr>
          <th style="width:36px;"><input type="checkbox" id="cp-check-all" onchange="toggleSelectAll(this.checked)" /></th>
          <th class="sortable" data-col="codigo" onclick="sortBy('codigo')">Código <span class="sarr">↕</span></th>
          <th class="sortable" data-col="descripcion" onclick="sortBy('descripcion')">Descripción <span class="sarr">↕</span></th>
          <th class="sortable" data-col="tipo" onclick="sortBy('tipo')">Tipo <span class="sarr">↕</span></th>
          <th class="sortable" data-col="valor" onclick="sortBy('valor')">Descuento <span class="sarr">↕</span></th>
          <th class="sortable" data-col="usos" onclick="sortBy('usos')">Usos <span class="sarr">↕</span></th>
          <th class="sortable" data-col="expiracion" onclick="sortBy('expiracion')">Expira <span class="sarr">↕</span></th>
          <th class="sortable" data-col="estado" onclick="sortBy('estado')">Estado <span class="sarr">↕</span></th>
        </tr>
      </thead>
      <tbody id="cp-tbody"></tbody>
    </table>
  </div>

  <!-- Confirm dialog -->
  <div class="cp-confirm" id="cp-confirm">
    <div class="cp-confirm__card">
      <div class="cp-confirm__icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div class="cp-confirm__title" id="cp-confirm-title">¿Eliminar cupón?</div>
      <div class="cp-confirm__text" id="cp-confirm-text">Esta acción no se puede deshacer.</div>
      <div class="cp-confirm__actions">
        <button class="cp-btn" onclick="closeConfirm()">Cancelar</button>
        <button class="cp-btn cp-btn--danger" id="cp-confirm-ok">Sí, eliminar</button>
      </div>
    </div>
  </div>
</main>

<!-- Overlay -->
<div class="cp-overlay" id="cp-overlay" onclick="closeDrawer()"></div>

<!-- Drawer -->
<aside class="cp-drawer" id="cp-drawer">
  <div class="cp-drawer__head">
    <span class="cp-drawer__title" id="cp-drawer-title">Nuevo cupón</span>
    <button class="cp-drawer__close" onclick="closeDrawer()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="cp-drawer__body">
    <div class="cp-field">
      <label for="cp-f-codigo">Código <span style="color:var(--cp-danger)">*</span></label>
      <input id="cp-f-codigo" type="text" placeholder="Ej. VERANO20" style="text-transform:uppercase;" />
      <span class="cp-field--hint">Los clientes usarán este código en el carrito.</span>
    </div>
    <div class="cp-field">
      <label for="cp-f-desc">Descripción</label>
      <input id="cp-f-desc" type="text" placeholder="Descripción breve del cupón" />
    </div>
    <div class="cp-field--row">
      <div class="cp-field">
        <label for="cp-f-tipo">Tipo de descuento</label>
        <select id="cp-f-tipo" onchange="onTipoChange()">
          <option value="porcentaje">Porcentaje (%)</option>
          <option value="monto">Monto fijo</option>
          <option value="envio">Envío gratis</option>
        </select>
      </div>
      <div class="cp-field" id="cp-f-valor-wrap">
        <label for="cp-f-valor">Valor</label>
        <input id="cp-f-valor" type="number" min="0" step="0.01" placeholder="0" />
      </div>
    </div>
    <div class="cp-field--row">
      <div class="cp-field">
        <label for="cp-f-min-compra">Mínimo de compra</label>
        <input id="cp-f-min-compra" type="number" min="0" step="0.01" placeholder="0.00" />
      </div>
      <div class="cp-field">
        <label for="cp-f-max-usos">Usos máximos</label>
        <input id="cp-f-max-usos" type="number" min="0" step="1" placeholder="Ilimitado" />
      </div>
    </div>
    <div class="cp-field--row">
      <div class="cp-field">
        <label for="cp-f-inicio">Fecha inicio</label>
        <input id="cp-f-inicio" type="date" />
      </div>
      <div class="cp-field">
        <label for="cp-f-fin">Fecha expiración</label>
        <input id="cp-f-fin" type="date" />
      </div>
    </div>
    <div class="cp-field">
      <label for="cp-f-estado">Estado</label>
      <select id="cp-f-estado">
        <option value="activo">Activo</option>
        <option value="programado">Programado</option>
        <option value="desactivado">Desactivado</option>
      </select>
    </div>
    <div class="cp-field">
      <label for="cp-f-notas">Notas internas</label>
      <textarea id="cp-f-notas" placeholder="Observaciones sobre este cupón…"></textarea>
    </div>
  </div>
  <div class="cp-drawer__footer">
    <button class="cp-btn cp-btn--danger" id="cp-f-delete-btn" onclick="openConfirm('single')" style="display:none;">
      <i class="fa-regular fa-trash-can"></i> Eliminar
    </button>
    <button class="cp-btn cp-btn--primary" onclick="saveDrawer()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<!-- Toast -->
<div class="cp-toast" id="cp-toast"></div>

<script>
(function () {
  var STORAGE_KEY = 'multitienda_cupones';
  var data = [];
  var sortCol = 'codigo';
  var sortAsc = true;
  var editIdx = -1;
  var confirmMode = '';

  /* ── Storage ── */
  function load() {
    try { data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch (e) { data = []; }
  }
  function save() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); } catch (e) {}
  }

  /* ── Stats ── */
  function updateStats() {
    var today = new Date().toISOString().slice(0, 10);
    var total = data.length;
    var activos = 0, usados = 0, expirados = 0;
    data.forEach(function (c) {
      var st = computeEstado(c);
      if (st === 'activo') activos++;
      if (st === 'expirado') expirados++;
      usados += parseInt(c.usos || 0, 10);
    });
    document.getElementById('cp-stat-total').textContent = total;
    document.getElementById('cp-stat-activos').textContent = activos;
    document.getElementById('cp-stat-usados').textContent = usados;
    document.getElementById('cp-stat-expirados').textContent = expirados;
  }

  function computeEstado(c) {
    if (c.estado === 'desactivado') return 'desactivado';
    var today = new Date().toISOString().slice(0, 10);
    if (c.expiracion && c.expiracion < today) return 'expirado';
    if (c.inicio && c.inicio > today) return 'programado';
    return c.estado || 'activo';
  }

  /* ── Table ── */
  function getFiltered() {
    var q = (document.getElementById('cp-search').value || '').toLowerCase();
    var fe = document.getElementById('cp-filter-estado').value;
    var ft = document.getElementById('cp-filter-tipo').value;
    return data.filter(function (c, i) {
      c._idx = i;
      var st = computeEstado(c);
      if (fe && st !== fe) return false;
      if (ft && (c.tipo || '') !== ft) return false;
      if (q && (c.codigo || '').toLowerCase().indexOf(q) < 0 && (c.descripcion || '').toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
  }

  window.renderTable = function () {
    var rows = getFiltered();
    rows.sort(function (a, b) {
      var av = (a[sortCol] || '').toString().toLowerCase();
      var bv = (b[sortCol] || '').toString().toLowerCase();
      return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    var tbody = document.getElementById('cp-tbody');
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="8"><div class="cp-empty"><i class="fa-solid fa-ticket"></i>No hay cupones que coincidan con los filtros.</div></td></tr>';
      syncEliminarBtn();
      updateStats();
      return;
    }
    tbody.innerHTML = rows.map(function (c) {
      var st = computeEstado(c);
      var badge = badgeHtml(st);
      var maxUsos = c.maxUsos ? parseInt(c.maxUsos, 10) : null;
      var usosTxt = maxUsos ? ((c.usos || 0) + ' / ' + maxUsos) : (c.usos || 0);
      var descTxt = c.tipo === 'envio' ? 'Envío gratis' : (c.tipo === 'monto' ? '$' + parseFloat(c.valor || 0).toFixed(2) : (parseFloat(c.valor || 0).toFixed(1) + '%'));
      return '<tr onclick="rowClick(' + c._idx + ')">'
        + '<td onclick="event.stopPropagation()"><input type="checkbox" class="cp-row-check" data-idx="' + c._idx + '" onchange="syncEliminarBtn()" /></td>'
        + '<td><span class="cp-code-chip">' + esc(c.codigo || '') + '</span></td>'
        + '<td>' + esc(c.descripcion || '—') + '</td>'
        + '<td>' + tipoLabel(c.tipo) + '</td>'
        + '<td>' + esc(descTxt) + '</td>'
        + '<td>' + esc(String(usosTxt)) + '</td>'
        + '<td>' + esc(c.expiracion || '—') + '</td>'
        + '<td>' + badge + '</td>'
        + '</tr>';
    }).join('');
    syncEliminarBtn();
    updateStats();
    document.getElementById('cp-check-all').checked = false;
  };

  function tipoLabel(tipo) {
    return tipo === 'monto' ? 'Monto fijo' : tipo === 'envio' ? 'Envío gratis' : 'Porcentaje';
  }

  function badgeHtml(st) {
    var map = {
      activo:      ['cp-badge--active',    'fa-circle-check',   'Activo'],
      programado:  ['cp-badge--scheduled', 'fa-clock',          'Programado'],
      desactivado: ['cp-badge--disabled',  'fa-circle-xmark',   'Desactivado'],
      expirado:    ['cp-badge--expired',   'fa-calendar-xmark', 'Expirado'],
    };
    var v = map[st] || map['desactivado'];
    return '<span class="cp-badge ' + v[0] + '"><i class="fa-solid ' + v[1] + '"></i>' + v[2] + '</span>';
  }

  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  /* ── Sort ── */
  window.sortBy = function (col) {
    if (sortCol === col) { sortAsc = !sortAsc; } else { sortCol = col; sortAsc = true; }
    renderTable();
  };

  /* ── Select all ── */
  window.toggleSelectAll = function (checked) {
    document.querySelectorAll('.cp-row-check').forEach(function (cb) { cb.checked = checked; });
    syncEliminarBtn();
  };

  window.syncEliminarBtn = function () {
    var any = document.querySelectorAll('.cp-row-check:checked').length > 0;
    document.getElementById('cp-eliminar-btn').disabled = !any;
  };

  /* ── Row click ── */
  window.rowClick = function (idx) { openDrawer(idx); };

  /* ── Drawer ── */
  window.openDrawer = function (idx) {
    editIdx = idx;
    var c = idx >= 0 ? data[idx] : null;
    document.getElementById('cp-drawer-title').textContent = c ? 'Editar cupón' : 'Nuevo cupón';
    document.getElementById('cp-f-codigo').value    = c ? (c.codigo || '') : '';
    document.getElementById('cp-f-desc').value      = c ? (c.descripcion || '') : '';
    document.getElementById('cp-f-tipo').value      = c ? (c.tipo || 'porcentaje') : 'porcentaje';
    document.getElementById('cp-f-valor').value     = c ? (c.valor || '') : '';
    document.getElementById('cp-f-min-compra').value = c ? (c.minCompra || '') : '';
    document.getElementById('cp-f-max-usos').value  = c ? (c.maxUsos || '') : '';
    document.getElementById('cp-f-inicio').value    = c ? (c.inicio || '') : '';
    document.getElementById('cp-f-fin').value       = c ? (c.expiracion || '') : '';
    document.getElementById('cp-f-estado').value    = c ? (c.estado || 'activo') : 'activo';
    document.getElementById('cp-f-notas').value     = c ? (c.notas || '') : '';
    document.getElementById('cp-f-delete-btn').style.display = c ? '' : 'none';
    onTipoChange();
    document.getElementById('cp-drawer').classList.add('is-open');
    document.getElementById('cp-overlay').classList.add('is-open');
  };

  window.closeDrawer = function () {
    document.getElementById('cp-drawer').classList.remove('is-open');
    document.getElementById('cp-overlay').classList.remove('is-open');
    editIdx = -1;
  };

  window.onTipoChange = function () {
    var tipo = document.getElementById('cp-f-tipo').value;
    document.getElementById('cp-f-valor-wrap').style.display = tipo === 'envio' ? 'none' : '';
  };

  window.saveDrawer = function () {
    var codigo = (document.getElementById('cp-f-codigo').value || '').trim().toUpperCase();
    if (!codigo) { showToast('El código es obligatorio.'); return; }
    // Duplicate check (skip self when editing)
    for (var i = 0; i < data.length; i++) {
      if (i !== editIdx && (data[i].codigo || '').toUpperCase() === codigo) {
        showToast('Ya existe un cupón con ese código.'); return;
      }
    }
    var rec = {
      codigo:      codigo,
      descripcion: document.getElementById('cp-f-desc').value.trim(),
      tipo:        document.getElementById('cp-f-tipo').value,
      valor:       document.getElementById('cp-f-valor').value,
      minCompra:   document.getElementById('cp-f-min-compra').value,
      maxUsos:     document.getElementById('cp-f-max-usos').value,
      inicio:      document.getElementById('cp-f-inicio').value,
      expiracion:  document.getElementById('cp-f-fin').value,
      estado:      document.getElementById('cp-f-estado').value,
      notas:       document.getElementById('cp-f-notas').value.trim(),
      usos:        editIdx >= 0 ? (data[editIdx].usos || 0) : 0,
    };
    if (editIdx >= 0) { data[editIdx] = rec; } else { data.push(rec); }
    save();
    closeDrawer();
    renderTable();
    showToast(editIdx >= 0 ? 'Cupón actualizado.' : 'Cupón creado.');
  };

  /* ── Confirm ── */
  window.openConfirm = function (mode) {
    confirmMode = mode;
    if (mode === 'bulk') {
      var n = document.querySelectorAll('.cp-row-check:checked').length;
      document.getElementById('cp-confirm-title').textContent = '¿Eliminar ' + n + ' cupón' + (n > 1 ? 'es' : '') + '?';
      document.getElementById('cp-confirm-text').textContent = 'Esta acción no se puede deshacer.';
    } else {
      var codigo = editIdx >= 0 ? (data[editIdx].codigo || 'este cupón') : 'este cupón';
      document.getElementById('cp-confirm-title').textContent = '¿Eliminar "' + codigo + '"?';
      document.getElementById('cp-confirm-text').textContent = 'Esta acción no se puede deshacer.';
    }
    document.getElementById('cp-confirm').classList.add('is-open');
  };

  window.closeConfirm = function () {
    document.getElementById('cp-confirm').classList.remove('is-open');
  };

  document.getElementById('cp-confirm-ok').addEventListener('click', function () {
    closeConfirm();
    if (confirmMode === 'bulk') {
      var toDelete = [];
      document.querySelectorAll('.cp-row-check:checked').forEach(function (cb) {
        toDelete.push(parseInt(cb.dataset.idx, 10));
      });
      toDelete.sort(function (a, b) { return b - a; });
      toDelete.forEach(function (idx) { data.splice(idx, 1); });
      save(); renderTable(); showToast('Cupones eliminados.');
    } else {
      if (editIdx >= 0) {
        data.splice(editIdx, 1);
        save(); closeDrawer(); renderTable(); showToast('Cupón eliminado.');
      }
    }
  });

  /* ── Toast ── */
  function showToast(msg) {
    var t = document.getElementById('cp-toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 2800);
  }

  /* ── Init ── */
  load();
  renderTable();
})();
</script>
</body>
</html>
"""
