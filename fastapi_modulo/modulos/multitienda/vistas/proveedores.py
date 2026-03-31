from __future__ import annotations


def proveedores_html() -> str:
    return _HTML


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Proveedores — Multitienda</title>
  <style>
    :root {
      --pv-bg: var(--page-bg, #f4f6fb);
      --pv-surface: var(--content-bg, #ffffff);
      --pv-border: var(--field-border, #d1d5db);
      --pv-text: var(--body-text, #1f2937);
      --pv-muted: color-mix(in srgb, var(--body-text, #1f2937) 58%, #ffffff 42%);
      --pv-accent: var(--button-bg, #1a6b3c);
      --pv-accent-fg: var(--button-text, #ffffff);
      --pv-danger: #dc2626;
      --pv-danger-soft: color-mix(in srgb, #dc2626 9%, var(--pv-surface));
      --pv-teal: #0d9488;
      --pv-teal-soft: color-mix(in srgb, #0d9488 10%, var(--pv-surface));
      --pv-warning: #d97706;
      --pv-success: #16a34a;
    }
    html, body { margin: 0; padding: 0; background: var(--pv-bg); font-family: system-ui, Arial, sans-serif; color: var(--pv-text); }
    * { box-sizing: border-box; }

    /* ── Stats ── */
    .pv-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 18px; }
    .pv-stat {
      background: var(--pv-surface); border: 1px solid var(--pv-border);
      border-radius: 14px; padding: 14px 16px;
      display: flex; align-items: center; gap: 12px;
    }
    .pv-stat__icon { width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center; font-size: .95rem; flex-shrink: 0; }
    .pv-stat__icon--teal   { background: color-mix(in srgb,#0d9488 12%,var(--pv-surface)); color: var(--pv-teal); }
    .pv-stat__icon--green  { background: #dcfce7; color: #15803d; }
    .pv-stat__icon--amber  { background: #fef9c3; color: #b45309; }
    .pv-stat__icon--blue   { background: #dbeafe; color: #1d4ed8; }
    .pv-stat__value { font-size: 1.35rem; font-weight: 800; letter-spacing: -.03em; line-height: 1; }
    .pv-stat__label { font-size: .74rem; color: var(--pv-muted); margin-top: 2px; }

    /* ── Toolbar ── */
    .pv-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
    .pv-toolbar__left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

    /* ── Buttons ── */
    .pv-btn {
      display: inline-flex; align-items: center; gap: 7px;
      min-height: 38px; padding: 0 16px; border-radius: 10px;
      border: 1px solid var(--pv-border); background: var(--pv-surface);
      color: var(--pv-text); font-size: .86rem; font-weight: 700;
      cursor: pointer; text-decoration: none;
      transition: background .14s, border-color .14s, transform .14s;
    }
    .pv-btn:hover { background: color-mix(in srgb, var(--pv-surface) 85%, var(--pv-bg)); transform: translateY(-1px); }
    .pv-btn--primary { background: var(--pv-teal); color: #fff; border-color: var(--pv-teal); }
    .pv-btn--primary:hover { background: color-mix(in srgb, var(--pv-teal) 85%, #000 15%); border-color: color-mix(in srgb, var(--pv-teal) 85%, #000 15%); }
    .pv-btn--danger { color: var(--pv-danger); border-color: color-mix(in srgb, var(--pv-danger) 30%, var(--pv-border)); }
    .pv-btn--danger:hover { background: var(--pv-danger-soft); }
    .pv-btn:disabled { opacity: .4; cursor: not-allowed; transform: none; }

    /* ── Search / filter ── */
    .pv-search {
      display: flex; align-items: center; gap: 8px;
      min-height: 38px; padding: 0 12px;
      border: 1px solid var(--pv-border); border-radius: 10px; background: var(--pv-surface);
    }
    .pv-search input { border: none; outline: none; background: transparent; color: var(--pv-text); font-size: .86rem; width: 200px; }
    .pv-search input::placeholder { color: var(--pv-muted); }
    .pv-filter-select {
      min-height: 38px; padding: 0 10px; border: 1px solid var(--pv-border);
      border-radius: 10px; background: var(--pv-surface); color: var(--pv-text);
      font-size: .84rem; cursor: pointer; outline: none;
    }

    /* ── Table ── */
    .pv-table-wrap { overflow-x: auto; }
    .pv-table { width: 100%; border-collapse: collapse; }
    .pv-table thead tr { border-bottom: 2px solid var(--pv-border); }
    .pv-table th {
      padding: 10px 14px; text-align: left; font-size: .80rem; font-weight: 700;
      color: var(--pv-text); white-space: nowrap; user-select: none;
    }
    .pv-table th.sortable { cursor: pointer; }
    .pv-table th.sortable:hover { color: var(--pv-teal); }
    .pv-table th .sarr { margin-left: 3px; font-size: .68rem; color: var(--pv-muted); }
    .pv-table tbody tr {
      border-bottom: 1px solid color-mix(in srgb, var(--pv-border) 55%, transparent);
      cursor: pointer; transition: background .12s;
    }
    .pv-table tbody tr:hover td { background: var(--pv-teal-soft); }
    .pv-table td { padding: 10px 14px; font-size: .875rem; color: var(--pv-text); vertical-align: middle; }

    /* ── Score bar ── */
    .pv-score-wrap { display: flex; align-items: center; gap: 8px; }
    .pv-score-bar { flex: 1; height: 6px; border-radius: 999px; background: color-mix(in srgb,var(--pv-border) 60%,var(--pv-bg)); overflow: hidden; min-width: 60px; }
    .pv-score-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--pv-teal), #0891b2); }
    .pv-score-fill.is-high { background: linear-gradient(90deg, var(--pv-success), #0d9488); }
    .pv-score-fill.is-low  { background: linear-gradient(90deg, var(--pv-warning), #f59e0b); }
    .pv-score-num { font-size: .78rem; font-weight: 700; color: var(--pv-muted); width: 32px; text-align: right; flex-shrink: 0; }

    /* ── Fuente chip ── */
    .pv-fuente {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 2px 9px; border-radius: 999px;
      font-size: .72rem; font-weight: 700; white-space: nowrap;
    }
    .pv-fuente--referido    { background: #dbeafe; color: #1d4ed8; }
    .pv-fuente--directo     { background: #dcfce7; color: #15803d; }
    .pv-fuente--feria       { background: #fef9c3; color: #b45309; }
    .pv-fuente--online      { background: #ede9fe; color: #7c3aed; }
    .pv-fuente--campana     { background: color-mix(in srgb,var(--pv-teal) 10%,var(--pv-surface)); color: var(--pv-teal); }
    .pv-fuente--otro        { background: #f3f4f6; color: #374151; }

    .pv-empty { text-align: center; padding: 52px 20px; color: var(--pv-muted); font-size: .9rem; }
    .pv-empty i { font-size: 2.4rem; display: block; margin-bottom: 10px; }

    /* ── Drawer ── */
    .pv-drawer {
      position: fixed; top: 0; right: 0;
      width: min(480px, 100vw); height: 100%;
      background: var(--pv-surface); border-left: 1px solid var(--pv-border);
      box-shadow: -12px 0 40px rgba(0,0,0,.10);
      transform: translateX(100%); transition: transform .22s ease;
      z-index: 800; display: flex; flex-direction: column;
    }
    .pv-drawer.is-open { transform: translateX(0); }
    .pv-drawer__head {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 20px; border-bottom: 1px solid var(--pv-border); flex-shrink: 0;
    }
    .pv-drawer__title { font-size: 1rem; font-weight: 700; }
    .pv-drawer__close {
      width: 34px; height: 34px; border-radius: 10px; border: 1px solid var(--pv-border);
      background: transparent; cursor: pointer; display: grid; place-items: center;
      color: var(--pv-muted); transition: background .14s;
    }
    .pv-drawer__close:hover { background: var(--pv-danger-soft); color: var(--pv-danger); }
    .pv-drawer__body { flex: 1; overflow-y: auto; padding: 20px; display: grid; gap: 14px; align-content: start; }
    .pv-drawer__footer {
      padding: 14px 20px; border-top: 1px solid var(--pv-border);
      display: flex; gap: 10px; flex-shrink: 0;
    }
    .pv-drawer__footer .pv-btn { flex: 1; justify-content: center; }

    /* ── Intel banner ── */
    .pv-intel-banner {
      display: flex; align-items: center; gap: 10px; padding: 10px 14px;
      background: var(--pv-teal-soft); border: 1px solid color-mix(in srgb,var(--pv-teal) 25%,var(--pv-border));
      border-radius: 12px; font-size: .82rem; color: var(--pv-teal);
    }
    .pv-intel-banner i { font-size: 1rem; flex-shrink: 0; }
    .pv-intel-banner a { color: var(--pv-teal); font-weight: 700; text-decoration: underline; }

    /* ── Campañas card ── */
    .pv-section-title { font-size: .80rem; font-weight: 700; color: var(--pv-muted); text-transform: uppercase; letter-spacing: .08em; margin: 4px 0 8px; }
    .pv-camp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin-bottom: 20px; }
    .pv-camp-card {
      background: var(--pv-surface); border: 1px solid var(--pv-border); border-radius: 12px;
      padding: 12px 14px; cursor: pointer;
      transition: box-shadow .14s, border-color .14s;
    }
    .pv-camp-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,.07); border-color: color-mix(in srgb,var(--pv-teal) 35%,var(--pv-border)); }
    .pv-camp-card__name { font-weight: 700; font-size: .88rem; margin-bottom: 4px; }
    .pv-camp-card__meta { font-size: .76rem; color: var(--pv-muted); display: flex; gap: 8px; flex-wrap: wrap; }

    /* ── Status badge ── */
    .pv-badge {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 2px 8px; border-radius: 999px; font-size: .72rem; font-weight: 700;
    }
    .pv-badge--activa  { background: #dcfce7; color: #15803d; }
    .pv-badge--borrador{ background: #f3f4f6; color: #6b7280; }
    .pv-badge--cerrada { background: #fee2e2; color: #b91c1c; }

    /* ── Form fields ── */
    .pv-field { display: grid; gap: 5px; }
    .pv-field label { font-size: .80rem; font-weight: 700; color: var(--pv-text); }
    .pv-field input, .pv-field select, .pv-field textarea {
      width: 100%; padding: 8px 12px; border: 1px solid var(--pv-border);
      border-radius: 9px; background: var(--pv-bg); color: var(--pv-text);
      font-size: .88rem; outline: none; transition: border-color .14s;
    }
    .pv-field input:focus, .pv-field select:focus, .pv-field textarea:focus { border-color: var(--pv-teal); }
    .pv-field textarea { resize: vertical; min-height: 70px; }
    .pv-field--row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .pv-field--hint { font-size: .75rem; color: var(--pv-muted); margin-top: 2px; }

    /* ── Tabs ── */
    .pv-tabs { display: flex; gap: 2px; border-bottom: 2px solid var(--pv-border); margin-bottom: 18px; }
    .pv-tab {
      display: inline-flex; align-items: center; gap: 7px;
      padding: 9px 16px; border: none; background: none;
      font-size: .875rem; font-weight: 700; color: var(--pv-muted);
      cursor: pointer; border-bottom: 3px solid transparent; margin-bottom: -2px;
      transition: color .14s, border-color .14s;
    }
    .pv-tab:hover { color: var(--pv-text); }
    .pv-tab.is-active { color: var(--pv-teal); border-bottom-color: var(--pv-teal); }
    .pv-tab-panel { display: none; }
    .pv-tab-panel.is-active { display: block; }

    /* ── Overlay / Confirm / Toast ── */
    .pv-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,.32);
      z-index: 799; opacity: 0; pointer-events: none; transition: opacity .2s;
    }
    .pv-overlay.is-open { opacity: 1; pointer-events: all; }
    .pv-confirm {
      position: fixed; inset: 0; z-index: 900;
      display: flex; align-items: center; justify-content: center;
      background: rgba(0,0,0,.38); opacity: 0; pointer-events: none; transition: opacity .18s;
    }
    .pv-confirm.is-open { opacity: 1; pointer-events: all; }
    .pv-confirm__card {
      background: var(--pv-surface); border: 1px solid var(--pv-border);
      border-radius: 18px; padding: 28px 28px 22px;
      max-width: 360px; width: 90%; text-align: center;
      box-shadow: 0 20px 60px rgba(0,0,0,.15);
    }
    .pv-confirm__icon { font-size: 2rem; color: var(--pv-danger); margin-bottom: 12px; }
    .pv-confirm__title { font-size: 1rem; font-weight: 700; margin-bottom: 8px; }
    .pv-confirm__text  { font-size: .86rem; color: var(--pv-muted); margin-bottom: 20px; line-height: 1.5; }
    .pv-confirm__actions { display: flex; gap: 10px; justify-content: center; }
    .pv-confirm__actions .pv-btn { min-width: 110px; justify-content: center; }
    .pv-toast {
      position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%) translateY(20px);
      background: #1f2937; color: #fff; padding: 10px 22px; border-radius: 999px;
      font-size: .86rem; font-weight: 600; z-index: 1000;
      opacity: 0; transition: opacity .2s, transform .2s; pointer-events: none;
    }
    .pv-toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
  </style>
</head>
<body>
<main>

  <!-- Stats -->
  <div class="pv-stats">
    <div class="pv-stat">
      <div class="pv-stat__icon pv-stat__icon--teal"><i class="fa-solid fa-handshake"></i></div>
      <div><div class="pv-stat__value" id="pv-stat-total">0</div><div class="pv-stat__label">Total contactos</div></div>
    </div>
    <div class="pv-stat">
      <div class="pv-stat__icon pv-stat__icon--green"><i class="fa-solid fa-star"></i></div>
      <div><div class="pv-stat__value" id="pv-stat-alta">0</div><div class="pv-stat__label">Alta propensión</div></div>
    </div>
    <div class="pv-stat">
      <div class="pv-stat__icon pv-stat__icon--blue"><i class="fa-solid fa-bullhorn"></i></div>
      <div><div class="pv-stat__value" id="pv-stat-campanas">0</div><div class="pv-stat__label">Campañas activas</div></div>
    </div>
    <div class="pv-stat">
      <div class="pv-stat__icon pv-stat__icon--amber"><i class="fa-solid fa-clock-rotate-left"></i></div>
      <div><div class="pv-stat__value" id="pv-stat-nuevos">0</div><div class="pv-stat__label">Nuevos este mes</div></div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="pv-tabs">
    <button class="pv-tab is-active" data-tab="contactos" onclick="showTab('contactos')">
      <i class="fa-solid fa-address-card"></i> Red de contactos
    </button>
    <button class="pv-tab" data-tab="campanas" onclick="showTab('campanas')">
      <i class="fa-solid fa-bullhorn"></i> Campañas
    </button>
  </div>

  <!-- ═══ TAB: Contactos ═══ -->
  <div class="pv-tab-panel is-active" id="pv-panel-contactos">
    <div class="pv-toolbar">
      <div class="pv-toolbar__left">
        <button class="pv-btn pv-btn--primary" onclick="openContactDrawer(null)">
          <i class="fa-solid fa-plus"></i> Nuevo contacto
        </button>
        <button class="pv-btn pv-btn--danger" id="pv-del-btn" disabled onclick="openConfirm('bulk')">
          <i class="fa-regular fa-trash-can"></i> Eliminar
        </button>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
        <select class="pv-filter-select" id="pv-filter-fuente" onchange="renderContactos()">
          <option value="">Todas las fuentes</option>
          <option value="referido">Referido</option>
          <option value="directo">Directo</option>
          <option value="feria">Feria / evento</option>
          <option value="online">Online</option>
          <option value="campana">Campaña</option>
          <option value="otro">Otro</option>
        </select>
        <div class="pv-search">
          <i class="fa-solid fa-magnifying-glass" style="color:var(--pv-muted);font-size:.8rem;"></i>
          <input type="text" id="pv-search" placeholder="Buscar nombre o teléfono…" oninput="renderContactos()" />
        </div>
      </div>
    </div>
    <div class="pv-table-wrap">
      <table class="pv-table">
        <thead>
          <tr>
            <th style="width:36px;"><input type="checkbox" id="pv-check-all" onchange="toggleAll(this.checked)" /></th>
            <th class="sortable" onclick="sortBy('nombre')">Nombre <span class="sarr">↕</span></th>
            <th class="sortable" onclick="sortBy('telefono')">Teléfono <span class="sarr">↕</span></th>
            <th class="sortable" onclick="sortBy('fuente')">Fuente <span class="sarr">↕</span></th>
            <th class="sortable" onclick="sortBy('score_propension')">Propensión <span class="sarr">↕</span></th>
            <th class="sortable" onclick="sortBy('fecha_creacion')">Registro <span class="sarr">↕</span></th>
          </tr>
        </thead>
        <tbody id="pv-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- ═══ TAB: Campañas ═══ -->
  <div class="pv-tab-panel" id="pv-panel-campanas">
    <div class="pv-toolbar">
      <div class="pv-toolbar__left">
        <button class="pv-btn pv-btn--primary" onclick="openCampDrawer(null)">
          <i class="fa-solid fa-plus"></i> Nueva campaña
        </button>
      </div>
      <div style="display:flex;gap:10px;align-items:center;">
        <select class="pv-filter-select" id="pv-camp-filter" onchange="renderCampanas()">
          <option value="">Todos los estados</option>
          <option value="activa">Activa</option>
          <option value="borrador">Borrador</option>
          <option value="cerrada">Cerrada</option>
        </select>
      </div>
    </div>
    <div id="pv-camp-container">
      <div class="pv-empty"><i class="fa-solid fa-bullhorn"></i>Cargando campañas…</div>
    </div>
  </div>

  <!-- Confirm -->
  <div class="pv-confirm" id="pv-confirm">
    <div class="pv-confirm__card">
      <div class="pv-confirm__icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div class="pv-confirm__title" id="pv-confirm-title">¿Eliminar?</div>
      <div class="pv-confirm__text" id="pv-confirm-text">Esta acción eliminará también el registro en Intelicoop.</div>
      <div class="pv-confirm__actions">
        <button class="pv-btn" onclick="closeConfirm()">Cancelar</button>
        <button class="pv-btn pv-btn--danger" id="pv-confirm-ok">Sí, eliminar</button>
      </div>
    </div>
  </div>
</main>

<div class="pv-overlay" id="pv-overlay" onclick="closeAllDrawers()"></div>

<!-- Contact drawer -->
<aside class="pv-drawer" id="pv-contact-drawer">
  <div class="pv-drawer__head">
    <span class="pv-drawer__title" id="pv-contact-drawer-title">Nuevo contacto</span>
    <button class="pv-drawer__close" onclick="closeAllDrawers()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="pv-drawer__body">
    <div class="pv-intel-banner">
      <i class="fa-solid fa-circle-nodes"></i>
      <span>Guardado en <a href="/intelicoop" target="_blank">Intelicoop</a> como prospecto.</span>
    </div>
    <div class="pv-field">
      <label for="pv-f-nombre">Nombre completo <span style="color:var(--pv-danger)">*</span></label>
      <input id="pv-f-nombre" type="text" placeholder="Nombre Apellido / Empresa" />
    </div>
    <div class="pv-field--row">
      <div class="pv-field">
        <label for="pv-f-tel">Teléfono</label>
        <input id="pv-f-tel" type="tel" placeholder="+52 55 1234 5678" />
      </div>
      <div class="pv-field">
        <label for="pv-f-fuente">Fuente</label>
        <select id="pv-f-fuente">
          <option value="directo">Directo</option>
          <option value="referido">Referido</option>
          <option value="feria">Feria / evento</option>
          <option value="online">Online</option>
          <option value="campana">Campaña</option>
          <option value="otro">Otro</option>
        </select>
      </div>
    </div>
    <div class="pv-field">
      <label for="pv-f-dir">Dirección / Ubicación</label>
      <input id="pv-f-dir" type="text" placeholder="Ciudad, Estado" />
    </div>
    <div class="pv-field">
      <label for="pv-f-score">Propensión (0 – 1)</label>
      <input id="pv-f-score" type="number" min="0" max="1" step="0.01" placeholder="0.50" />
      <span class="pv-field--hint">Probabilidad estimada de conversión. Intelicoop la recalcula automáticamente.</span>
    </div>
    <div class="pv-field">
      <label for="pv-f-notas">Notas</label>
      <textarea id="pv-f-notas" placeholder="Observaciones sobre este contacto…"></textarea>
    </div>
  </div>
  <div class="pv-drawer__footer">
    <button class="pv-btn pv-btn--danger" id="pv-f-del-btn" onclick="openConfirm('single')" style="display:none;">
      <i class="fa-regular fa-trash-can"></i> Eliminar
    </button>
    <button class="pv-btn pv-btn--primary" onclick="saveContact()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<!-- Campaign drawer -->
<aside class="pv-drawer" id="pv-camp-drawer">
  <div class="pv-drawer__head">
    <span class="pv-drawer__title" id="pv-camp-drawer-title">Nueva campaña</span>
    <button class="pv-drawer__close" onclick="closeAllDrawers()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="pv-drawer__body">
    <div class="pv-intel-banner">
      <i class="fa-solid fa-circle-nodes"></i>
      <span>Sincronizado con <a href="/intelicoop" target="_blank">Intelicoop</a>.</span>
    </div>
    <div class="pv-field">
      <label for="pv-cf-nombre">Nombre de la campaña <span style="color:var(--pv-danger)">*</span></label>
      <input id="pv-cf-nombre" type="text" placeholder="Ej. Captación proveedores Q2" />
    </div>
    <div class="pv-field">
      <label for="pv-cf-tipo">Tipo</label>
      <select id="pv-cf-tipo">
        <option value="Colocacion">Colocación</option>
        <option value="Recuperacion">Recuperación</option>
        <option value="Captacion">Captación</option>
        <option value="Retencion">Retención</option>
        <option value="Otro">Otro</option>
      </select>
    </div>
    <div class="pv-field--row">
      <div class="pv-field">
        <label for="pv-cf-inicio">Fecha inicio</label>
        <input id="pv-cf-inicio" type="date" />
      </div>
      <div class="pv-field">
        <label for="pv-cf-fin">Fecha fin</label>
        <input id="pv-cf-fin" type="date" />
      </div>
    </div>
    <div class="pv-field">
      <label for="pv-cf-estado">Estado</label>
      <select id="pv-cf-estado">
        <option value="borrador">Borrador</option>
        <option value="activa">Activa</option>
        <option value="cerrada">Cerrada</option>
      </select>
    </div>
  </div>
  <div class="pv-drawer__footer">
    <button class="pv-btn pv-btn--primary" onclick="saveCampaña()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<div class="pv-toast" id="pv-toast"></div>

<script>
(function () {
  var prospectos = [];
  var campanas   = [];
  var sortCol = 'nombre';
  var sortAsc = true;
  var editContactId  = null;
  var confirmMode    = '';
  var confirmCallback = null;

  /* ── Load ── */
  function load() {
    Promise.all([
      fetch('/api/intelicoop/prospectos', { credentials: 'same-origin' }).then(function (r) { return r.json(); }),
      fetch('/api/intelicoop/campanas',   { credentials: 'same-origin' }).then(function (r) { return r.json(); }),
    ]).then(function (results) {
      prospectos = Array.isArray(results[0]) ? results[0] : (results[0].data || []);
      campanas   = Array.isArray(results[1]) ? results[1] : (results[1].data || []);
      renderContactos();
      renderCampanas();
      updateStats();
    }).catch(function () {
      prospectos = []; campanas = [];
      renderContactos();
      renderCampanas();
      updateStats();
    });
  }

  /* ── Stats ── */
  function updateStats() {
    var thisMonth = new Date().toISOString().slice(0, 7);
    var alta = 0, nuevos = 0;
    prospectos.forEach(function (p) {
      if (parseFloat(p.score_propension || 0) >= 0.6) alta++;
      if ((p.fecha_creacion || '').slice(0, 7) === thisMonth) nuevos++;
    });
    var activasCamp = campanas.filter(function (c) { return c.estado === 'activa'; }).length;
    document.getElementById('pv-stat-total').textContent   = prospectos.length;
    document.getElementById('pv-stat-alta').textContent    = alta;
    document.getElementById('pv-stat-campanas').textContent= activasCamp;
    document.getElementById('pv-stat-nuevos').textContent  = nuevos;
  }

  /* ── Tabs ── */
  window.showTab = function (id) {
    document.querySelectorAll('.pv-tab').forEach(function (t) { t.classList.toggle('is-active', t.dataset.tab === id); });
    document.querySelectorAll('.pv-tab-panel').forEach(function (p) { p.classList.toggle('is-active', p.id === 'pv-panel-' + id); });
  };

  /* ─── CONTACTOS ─── */
  window.sortBy = function (col) {
    if (sortCol === col) { sortAsc = !sortAsc; } else { sortCol = col; sortAsc = true; }
    renderContactos();
  };
  window.toggleAll = function (v) {
    document.querySelectorAll('.pv-row-check').forEach(function (cb) { cb.checked = v; });
    syncDelBtn();
  };
  window.syncDelBtn = function () {
    document.getElementById('pv-del-btn').disabled = !document.querySelectorAll('.pv-row-check:checked').length;
  };

  window.renderContactos = function () {
    var q  = (document.getElementById('pv-search').value || '').toLowerCase();
    var ff = document.getElementById('pv-filter-fuente').value;
    var rows = prospectos.filter(function (p, i) {
      p._idx = i;
      if (ff && (p.fuente || '').toLowerCase() !== ff) return false;
      if (q && ((p.nombre || '') + ' ' + (p.telefono || '')).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    rows.sort(function (a, b) {
      var av = String(a[sortCol] || '').toLowerCase();
      var bv = String(b[sortCol] || '').toLowerCase();
      return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    var tbody = document.getElementById('pv-tbody');
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="6"><div class="pv-empty"><i class="fa-solid fa-handshake"></i>No hay contactos todavía.</div></td></tr>';
      syncDelBtn(); updateStats(); return;
    }
    tbody.innerHTML = rows.map(function (p) {
      var score = parseFloat(p.score_propension || 0);
      var pct   = Math.round(score * 100);
      var cls   = score >= 0.6 ? 'is-high' : score < 0.3 ? 'is-low' : '';
      var fuente = (p.fuente || 'otro').toLowerCase();
      var fuenteLabel = { referido:'Referido', directo:'Directo', feria:'Feria', online:'Online', campana:'Campaña', otro:'Otro' }[fuente] || fuente;
      return '<tr onclick="openContactDrawer(' + p.id + ')">'
        + '<td onclick="event.stopPropagation()"><input type="checkbox" class="pv-row-check" data-id="' + p.id + '" onchange="syncDelBtn()" /></td>'
        + '<td><strong>' + esc(p.nombre || '') + '</strong></td>'
        + '<td>' + esc(p.telefono || '—') + '</td>'
        + '<td><span class="pv-fuente pv-fuente--' + esc(fuente) + '">' + esc(fuenteLabel) + '</span></td>'
        + '<td><div class="pv-score-wrap"><div class="pv-score-bar"><div class="pv-score-fill ' + cls + '" style="width:' + pct + '%"></div></div><span class="pv-score-num">' + pct + '%</span></div></td>'
        + '<td>' + esc((p.fecha_creacion || '').slice(0, 10) || '—') + '</td>'
        + '</tr>';
    }).join('');
    document.getElementById('pv-check-all').checked = false;
    syncDelBtn(); updateStats();
  };

  window.openContactDrawer = function (id) {
    editContactId = id;
    var p = id !== null ? prospectos.find(function (x) { return x.id === id; }) : null;
    document.getElementById('pv-contact-drawer-title').textContent = p ? 'Editar contacto' : 'Nuevo contacto';
    document.getElementById('pv-f-nombre').value  = p ? (p.nombre || '') : '';
    document.getElementById('pv-f-tel').value     = p ? (p.telefono || '') : '';
    document.getElementById('pv-f-fuente').value  = p ? (p.fuente || 'directo') : 'directo';
    document.getElementById('pv-f-dir').value     = p ? (p.direccion || '') : '';
    document.getElementById('pv-f-score').value   = p ? (p.score_propension !== undefined ? p.score_propension : '') : '';
    document.getElementById('pv-f-notas').value   = p ? (p.notas || '') : '';
    document.getElementById('pv-f-del-btn').style.display = p ? '' : 'none';
    openDrawer('pv-contact-drawer');
  };

  window.saveContact = function () {
    var nombre = (document.getElementById('pv-f-nombre').value || '').trim();
    if (!nombre) { showToast('El nombre es obligatorio.'); return; }
    var payload = {
      nombre:           nombre,
      telefono:         document.getElementById('pv-f-tel').value.trim(),
      fuente:           document.getElementById('pv-f-fuente').value,
      direccion:        document.getElementById('pv-f-dir').value.trim(),
      score_propension: parseFloat(document.getElementById('pv-f-score').value || '0') || 0,
    };
    var isNew = editContactId === null;
    var url    = isNew ? '/api/intelicoop/prospectos' : '/api/intelicoop/prospectos/' + editContactId;
    var method = isNew ? 'POST' : 'PUT';
    fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.id || res.success) {
          closeAllDrawers(); showToast(isNew ? 'Contacto agregado.' : 'Contacto actualizado.'); load();
        } else { showToast(res.detail || res.error || 'Error al guardar.'); }
      })
      .catch(function () { showToast('Error de conexión.'); });
  };

  /* ─── CAMPAÑAS ─── */
  window.renderCampanas = function () {
    var fe = document.getElementById('pv-camp-filter').value;
    var rows = campanas.filter(function (c) { return !fe || c.estado === fe; });
    var container = document.getElementById('pv-camp-container');
    if (!rows.length) {
      container.innerHTML = '<div class="pv-empty"><i class="fa-solid fa-bullhorn"></i>No hay campañas todavía.</div>';
      return;
    }
    var badgeMap = { activa: 'pv-badge--activa', borrador: 'pv-badge--borrador', cerrada: 'pv-badge--cerrada' };
    container.innerHTML = '<div class="pv-camp-grid">' + rows.map(function (c) {
      var badge = '<span class="pv-badge ' + (badgeMap[c.estado] || 'pv-badge--borrador') + '">' + esc(c.estado || '') + '</span>';
      var inicio = (c.fecha_inicio || '').slice(0, 10);
      var fin    = (c.fecha_fin || '').slice(0, 10);
      return '<div class="pv-camp-card" onclick="openCampDrawer(' + c.id + ')">'
        + '<div class="pv-camp-card__name">' + esc(c.nombre || '') + '</div>'
        + '<div class="pv-camp-card__meta">'
        + '<span>' + esc(c.tipo || '') + '</span>'
        + badge
        + (inicio ? '<span>' + inicio + '</span>' : '')
        + (fin ? '<span>→ ' + fin + '</span>' : '')
        + '</div>'
        + '</div>';
    }).join('') + '</div>';
    updateStats();
  };

  window.openCampDrawer = function (id) {
    var c = id !== null ? campanas.find(function (x) { return x.id === id; }) : null;
    document.getElementById('pv-camp-drawer-title').textContent = c ? 'Editar campaña' : 'Nueva campaña';
    document.getElementById('pv-cf-nombre').value = c ? (c.nombre || '') : '';
    document.getElementById('pv-cf-tipo').value   = c ? (c.tipo || 'Colocacion') : 'Colocacion';
    document.getElementById('pv-cf-inicio').value = c ? ((c.fecha_inicio || '').slice(0, 10)) : '';
    document.getElementById('pv-cf-fin').value    = c ? ((c.fecha_fin || '').slice(0, 10)) : '';
    document.getElementById('pv-cf-estado').value = c ? (c.estado || 'borrador') : 'borrador';
    openDrawer('pv-camp-drawer');
  };

  window.saveCampaña = function () {
    var nombre = (document.getElementById('pv-cf-nombre').value || '').trim();
    if (!nombre) { showToast('El nombre es obligatorio.'); return; }
    var payload = {
      nombre:       nombre,
      tipo:         document.getElementById('pv-cf-tipo').value,
      fecha_inicio: document.getElementById('pv-cf-inicio').value || null,
      fecha_fin:    document.getElementById('pv-cf-fin').value || null,
      estado:       document.getElementById('pv-cf-estado').value,
    };
    fetch('/api/intelicoop/campanas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.id || res.success) {
          closeAllDrawers(); showToast('Campaña guardada.'); load();
        } else { showToast(res.detail || res.error || 'Error al guardar.'); }
      })
      .catch(function () { showToast('Error de conexión.'); });
  };

  /* ─── CONFIRM / DELETE ─── */
  window.openConfirm = function (mode) {
    confirmMode = mode;
    if (mode === 'bulk') {
      var n = document.querySelectorAll('.pv-row-check:checked').length;
      document.getElementById('pv-confirm-title').textContent = '¿Eliminar ' + n + ' contacto' + (n !== 1 ? 's' : '') + '?';
      document.getElementById('pv-confirm-text').textContent  = 'Se eliminarán también de Intelicoop.';
      confirmCallback = function () {
        var ids = [];
        document.querySelectorAll('.pv-row-check:checked').forEach(function (cb) { ids.push(parseInt(cb.dataset.id, 10)); });
        Promise.all(ids.map(function (id) {
          return fetch('/api/intelicoop/prospectos/' + id, { method: 'DELETE', credentials: 'same-origin' });
        })).then(function () { showToast('Contactos eliminados.'); load(); });
      };
    } else {
      var p = editContactId !== null ? prospectos.find(function (x) { return x.id === editContactId; }) : null;
      document.getElementById('pv-confirm-title').textContent = '¿Eliminar "' + ((p && p.nombre) || 'este contacto') + '"?';
      document.getElementById('pv-confirm-text').textContent  = 'Se eliminará también de Intelicoop.';
      confirmCallback = function () {
        fetch('/api/intelicoop/prospectos/' + editContactId, { method: 'DELETE', credentials: 'same-origin' })
          .then(function () { closeAllDrawers(); showToast('Contacto eliminado.'); load(); });
      };
    }
    document.getElementById('pv-confirm').classList.add('is-open');
  };
  window.closeConfirm = function () { document.getElementById('pv-confirm').classList.remove('is-open'); };
  document.getElementById('pv-confirm-ok').addEventListener('click', function () {
    closeConfirm();
    if (confirmCallback) { confirmCallback(); confirmCallback = null; }
  });

  /* ─── DRAWERS ─── */
  function openDrawer(id) {
    document.querySelectorAll('.pv-drawer').forEach(function (d) { d.classList.remove('is-open'); });
    document.getElementById(id).classList.add('is-open');
    document.getElementById('pv-overlay').classList.add('is-open');
  }
  window.closeAllDrawers = function () {
    document.querySelectorAll('.pv-drawer').forEach(function (d) { d.classList.remove('is-open'); });
    document.getElementById('pv-overlay').classList.remove('is-open');
    editContactId = null;
  };

  /* ─── HELPERS ─── */
  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function showToast(msg) {
    var t = document.getElementById('pv-toast');
    t.textContent = msg; t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 2800);
  }

  /* ─── INIT ─── */
  load();
})();
</script>
</body>
</html>
"""
