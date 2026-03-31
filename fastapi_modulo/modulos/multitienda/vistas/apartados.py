from __future__ import annotations


def apartados_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Apartados</title>
  <style>
    :root {
      --ap-accent:  #1d4ed8;
      --ap-accent2: #1e40af;
      --ap-light:   #dbeafe;
      --ap-bg:      var(--page-bg, #f5f6f8);
      --ap-surface: var(--content-bg, #ffffff);
      --ap-border:  var(--field-border, #d1d5db);
      --ap-text:    var(--body-text, #1f2937);
      --ap-muted:   color-mix(in srgb, var(--body-text, #1f2937) 60%, #ffffff 40%);
      --ap-focus:   #1d4ed8;
      --ap-danger:  #dc2626;
      --ap-success: #16a34a;
      --ap-warn:    #d97706;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: var(--ap-bg); font-family: Arial, sans-serif; color: var(--ap-text); }

    .ap-page { padding: 0 0 48px; }

    /* ── Hero ───────────────────────────────────────────────────────────── */
    .ap-hero {
      background: linear-gradient(135deg, #0a1628 0%, #0f2557 50%, #0d2340 100%);
      border-radius: 20px; padding: 32px 32px 28px; margin-bottom: 28px;
      position: relative; overflow: hidden;
    }
    .ap-hero::before {
      content: ""; position: absolute; inset: 0;
      background:
        radial-gradient(ellipse 55% 60% at 82% 18%, rgba(29,78,216,0.38) 0%, transparent 70%),
        radial-gradient(ellipse 38% 45% at 12% 82%, rgba(30,64,175,0.22) 0%, transparent 70%);
      pointer-events: none;
    }
    .ap-hero__inner { position: relative; z-index: 1; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
    .ap-hero__icon {
      width: 64px; height: 64px; border-radius: 20px; flex-shrink: 0;
      background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      display: grid; place-items: center; font-size: 1.6rem; color: #fff;
      box-shadow: 0 8px 24px rgba(29,78,216,0.45);
    }
    .ap-hero__copy { flex: 1; min-width: 200px; }
    .ap-hero__copy h1 { margin: 0 0 6px; font-size: 1.55rem; font-weight: 800; color: #fff; letter-spacing: -0.02em; }
    .ap-hero__copy p  { margin: 0; color: rgba(255,255,255,0.72); font-size: 0.92rem; line-height: 1.5; }
    .ap-hero__badges  { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
    .ap-hero__badge {
      padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
      letter-spacing: 0.04em; text-transform: uppercase;
    }
    .ap-hero__badge--enganche { background: rgba(59,130,246,0.32); color: #bfdbfe; border: 1px solid rgba(191,219,254,0.25); }
    .ap-hero__badge--abonos   { background: rgba(30,64,175,0.32);  color: #a5b4fc; border: 1px solid rgba(165,180,252,0.25); }

    /* ── Stats ──────────────────────────────────────────────────────────── */
    .ap-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 16px; margin-bottom: 28px;
    }
    .ap-stat {
      background: var(--ap-surface); border: 1px solid var(--ap-border);
      border-radius: 16px; padding: 18px 20px;
    }
    .ap-stat__value { font-size: 1.75rem; font-weight: 800; color: var(--ap-accent); line-height: 1; margin-bottom: 4px; }
    .ap-stat__label { font-size: 0.8rem; color: var(--ap-muted); font-weight: 600; }
    .ap-stat__sub   { font-size: 0.72rem; color: var(--ap-muted); margin-top: 2px; }
    .ap-stat--warn .ap-stat__value  { color: var(--ap-warn); }
    .ap-stat--ok   .ap-stat__value  { color: var(--ap-success); }

    /* ── Tabs ───────────────────────────────────────────────────────────── */
    .ap-tabs { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
    .ap-tab {
      padding: 8px 18px; border-radius: 12px; font-size: 0.88rem; font-weight: 700;
      cursor: pointer; border: 1.5px solid var(--ap-border);
      background: var(--ap-surface); color: var(--ap-muted); transition: all 0.16s;
    }
    .ap-tab.is-active { background: var(--ap-accent); color: #fff; border-color: var(--ap-accent); }
    .ap-tab-panel { display: none; }
    .ap-tab-panel.is-active { display: block; }

    /* ── Toolbar ────────────────────────────────────────────────────────── */
    .ap-toolbar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
    .ap-search {
      flex: 1; min-width: 200px; max-width: 320px;
      padding: 9px 14px; border-radius: 12px; border: 1.5px solid var(--ap-border);
      font-size: 0.9rem; background: var(--ap-surface); color: var(--ap-text);
      outline: none; transition: border-color 0.15s;
    }
    .ap-search:focus { border-color: var(--ap-focus); }
    .ap-filter {
      padding: 9px 14px; border-radius: 12px; border: 1.5px solid var(--ap-border);
      font-size: 0.88rem; background: var(--ap-surface); color: var(--ap-text);
      outline: none; cursor: pointer;
    }
    .ap-btn-add {
      margin-left: auto; padding: 9px 18px; border-radius: 12px;
      background: var(--ap-accent); color: #fff; font-weight: 700; font-size: 0.88rem;
      border: none; cursor: pointer; display: flex; align-items: center; gap: 7px;
      transition: opacity 0.15s;
    }
    .ap-btn-add:hover { opacity: 0.88; }

    /* ── Table ──────────────────────────────────────────────────────────── */
    .ap-table-wrap { overflow-x: auto; border-radius: 14px; border: 1px solid var(--ap-border); }
    .ap-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    .ap-table thead tr { background: color-mix(in srgb, var(--ap-surface) 82%, var(--ap-bg) 18%); }
    .ap-table th { padding: 12px 14px; text-align: left; font-size: 0.72rem; font-weight: 700; color: var(--ap-muted); text-transform: uppercase; letter-spacing: 0.08em; white-space: nowrap; }
    .ap-table td { padding: 12px 14px; border-top: 1px solid var(--ap-border); vertical-align: middle; }
    .ap-table tbody tr { cursor: pointer; transition: background 0.12s; }
    .ap-table tbody tr:hover { background: color-mix(in srgb, var(--ap-accent) 5%, var(--ap-surface) 95%); }
    .ap-table__empty td { text-align: center; padding: 56px 16px; color: var(--ap-muted); cursor: default; }

    /* ── Progress mini ──────────────────────────────────────────────────── */
    .ap-prog-wrap { display: flex; align-items: center; gap: 7px; min-width: 120px; }
    .ap-prog-bar  { flex: 1; height: 7px; border-radius: 4px; background: #e5e7eb; overflow: hidden; }
    .ap-prog-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #3b82f6, #1d4ed8); transition: width 0.4s; }
    .ap-prog-fill--warn { background: linear-gradient(90deg, #f59e0b, #d97706); }
    .ap-prog-fill--done { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .ap-prog-pct  { font-size: 0.75rem; font-weight: 700; color: var(--ap-muted); white-space: nowrap; }

    /* ── Badges ─────────────────────────────────────────────────────────── */
    .ap-badge {
      display: inline-block; padding: 3px 10px; border-radius: 10px;
      font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; white-space: nowrap;
    }
    .ap-badge--activo     { background: #dbeafe; color: #1e40af; }
    .ap-badge--completado { background: #dcfce7; color: #166534; }
    .ap-badge--cancelado  { background: #f3f4f6; color: #6b7280; }
    .ap-badge--vencido    { background: #fee2e2; color: #991b1b; }
    .ap-badge--entregado  { background: #d1fae5; color: #065f46; }

    /* ── Money ──────────────────────────────────────────────────────────── */
    .ap-money { font-variant-numeric: tabular-nums; font-weight: 700; }
    .ap-money--pend { color: var(--ap-danger); }
    .ap-money--paid { color: var(--ap-success); }
    .ap-money--warn { color: var(--ap-warn); }

    /* ── Client cell ────────────────────────────────────────────────────── */
    .ap-client      { display: grid; gap: 1px; }
    .ap-client__name { font-weight: 700; font-size: 0.88rem; }
    .ap-client__tel  { font-size: 0.75rem; color: var(--ap-muted); }

    /* ── Overdue indicator ──────────────────────────────────────────────── */
    .ap-overdue-dot {
      display: inline-block; width: 8px; height: 8px; border-radius: 50%;
      background: var(--ap-danger); margin-right: 5px; vertical-align: middle;
    }

    /* ── Drawer backdrop ────────────────────────────────────────────────── */
    .ap-drawer-bg {
      display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.44);
      z-index: 1040; align-items: flex-end; justify-content: center;
    }
    .ap-drawer-bg.is-open { display: flex; }

    /* ── Drawer base ────────────────────────────────────────────────────── */
    .ap-drawer {
      background: var(--ap-surface); border-radius: 24px 24px 0 0;
      width: 100%; max-width: 680px;
      padding: 28px 28px 32px; max-height: 94vh; overflow-y: auto;
    }
    .ap-drawer__title    { font-size: 1.2rem; font-weight: 800; margin: 0 0 2px; }
    .ap-drawer__subtitle { font-size: 0.82rem; color: var(--ap-muted); margin: 0 0 22px; }

    /* ── Form fields ────────────────────────────────────────────────────── */
    .ap-field { margin-bottom: 15px; }
    .ap-field label { display: block; font-size: 0.77rem; font-weight: 700; margin-bottom: 5px; color: var(--ap-muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .ap-field input, .ap-field select, .ap-field textarea {
      width: 100%; padding: 10px 12px; border-radius: 10px;
      border: 1.5px solid var(--ap-border); font-size: 0.95rem;
      background: var(--ap-surface); color: var(--ap-text); outline: none; transition: border-color 0.15s;
    }
    .ap-field input:focus, .ap-field select:focus, .ap-field textarea:focus { border-color: var(--ap-focus); }
    .ap-field textarea { resize: vertical; min-height: 60px; }
    .ap-field--row  { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .ap-field--row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
    .ap-field--ro input { background: color-mix(in srgb, var(--ap-surface) 82%, var(--ap-bg) 18%); }

    .ap-section-title {
      font-size: 0.78rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
      color: var(--ap-muted); margin: 20px 0 12px; padding-top: 16px;
      border-top: 1px solid var(--ap-border);
    }

    /* ── Progress big (detail drawer) ──────────────────────────────────── */
    .ap-detail-prog {
      background: color-mix(in srgb, var(--ap-accent) 7%, var(--ap-surface) 93%);
      border: 1px solid color-mix(in srgb, var(--ap-accent) 22%, var(--ap-border) 78%);
      border-radius: 16px; padding: 18px 20px; margin-bottom: 20px;
    }
    .ap-detail-prog__header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
    .ap-detail-prog__title  { font-size: 0.82rem; font-weight: 700; color: var(--ap-muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .ap-detail-prog__pct    { font-size: 1.4rem; font-weight: 800; color: var(--ap-accent); }
    .ap-detail-bar { height: 12px; border-radius: 6px; background: #e5e7eb; overflow: hidden; margin-bottom: 10px; }
    .ap-detail-fill { height: 100%; border-radius: 6px; background: linear-gradient(90deg, #3b82f6, #1d4ed8); transition: width 0.5s; }
    .ap-detail-fill--done { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .ap-detail-amounts { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
    .ap-detail-amount__label { font-size: 0.72rem; font-weight: 700; color: var(--ap-muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; }
    .ap-detail-amount__value { font-size: 1.1rem; font-weight: 800; }

    /* ── Abonos list ────────────────────────────────────────────────────── */
    .ap-abonos-list { display: grid; gap: 8px; margin-bottom: 16px; }
    .ap-abono-row {
      display: flex; align-items: center; gap: 10px;
      padding: 10px 14px; border-radius: 12px;
      background: color-mix(in srgb, var(--ap-accent) 5%, var(--ap-surface) 95%);
      border: 1px solid color-mix(in srgb, var(--ap-accent) 14%, var(--ap-border) 86%);
    }
    .ap-abono-row__icon {
      width: 34px; height: 34px; border-radius: 10px; flex-shrink: 0;
      background: linear-gradient(135deg, rgba(59,130,246,0.18) 0%, rgba(29,78,216,0.18) 100%);
      display: grid; place-items: center; color: var(--ap-accent); font-size: 0.85rem;
    }
    .ap-abono-row__info { flex: 1; min-width: 0; }
    .ap-abono-row__fecha  { font-size: 0.78rem; color: var(--ap-muted); }
    .ap-abono-row__metodo { font-size: 0.75rem; color: var(--ap-muted); margin-top: 1px; }
    .ap-abono-row__monto  { font-size: 1rem; font-weight: 800; color: var(--ap-success); white-space: nowrap; }
    .ap-abono-row__del    { background: none; border: none; cursor: pointer; color: #e5e7eb; font-size: 0.8rem; padding: 4px; transition: color 0.15s; }
    .ap-abono-row__del:hover { color: var(--ap-danger); }
    .ap-abonos-empty { text-align: center; padding: 24px; color: var(--ap-muted); font-size: 0.88rem; background: color-mix(in srgb, var(--ap-surface) 85%, var(--ap-bg) 15%); border-radius: 12px; }

    /* ── Nuevo abono inline form ────────────────────────────────────────── */
    .ap-abono-form {
      background: color-mix(in srgb, var(--ap-accent) 5%, var(--ap-surface) 95%);
      border: 1.5px dashed color-mix(in srgb, var(--ap-accent) 30%, var(--ap-border) 70%);
      border-radius: 14px; padding: 16px 18px; margin-top: 4px;
    }
    .ap-abono-form__title { font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: var(--ap-accent); margin-bottom: 12px; }
    .ap-abono-form__grid  { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
    .ap-abono-form input, .ap-abono-form select {
      width: 100%; padding: 9px 11px; border-radius: 9px;
      border: 1.5px solid var(--ap-border); font-size: 0.88rem;
      background: var(--ap-surface); color: var(--ap-text); outline: none;
      transition: border-color 0.15s;
    }
    .ap-abono-form input:focus, .ap-abono-form select:focus { border-color: var(--ap-focus); }
    .ap-abono-form__actions { display: flex; gap: 8px; justify-content: flex-end; }
    .ap-abono-save-btn {
      padding: 8px 18px; border-radius: 10px; background: var(--ap-accent);
      color: #fff; font-weight: 700; font-size: 0.85rem; border: none; cursor: pointer;
      transition: opacity 0.15s;
    }
    .ap-abono-save-btn:hover { opacity: 0.88; }
    .ap-abono-cancel-btn {
      padding: 8px 14px; border-radius: 10px; background: var(--ap-surface);
      color: var(--ap-muted); font-weight: 700; font-size: 0.85rem;
      border: 1.5px solid var(--ap-border); cursor: pointer;
    }

    /* ── Drawer footer ──────────────────────────────────────────────────── */
    .ap-drawer__footer {
      display: flex; justify-content: flex-end; gap: 10px;
      margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--ap-border);
      flex-wrap: wrap;
    }
    .ap-btn {
      padding: 10px 22px; border-radius: 12px; font-size: 0.9rem; font-weight: 700;
      cursor: pointer; border: none; transition: opacity 0.15s;
    }
    .ap-btn:hover { opacity: 0.88; }
    .ap-btn--primary   { background: var(--ap-accent);   color: #fff; }
    .ap-btn--secondary { background: var(--ap-surface);  color: var(--ap-muted); border: 1.5px solid var(--ap-border); }
    .ap-btn--success   { background: var(--ap-success);  color: #fff; }
    .ap-btn--danger    { background: #fee2e2; color: var(--ap-danger); }
    .ap-btn--warn      { background: #fef3c7; color: var(--ap-warn); }

    @media (max-width: 640px) {
      .ap-hero { padding: 20px 16px 18px; }
      .ap-hero__copy h1 { font-size: 1.25rem; }
      .ap-field--row, .ap-field--row3, .ap-abono-form__grid { grid-template-columns: 1fr; }
      .ap-detail-amounts { grid-template-columns: 1fr 1fr; }
    }
  </style>
</head>
<body>
<main class="ap-page">

  <!-- Hero -->
  <div class="ap-hero">
    <div class="ap-hero__inner">
      <div class="ap-hero__icon"><i class="fa-solid fa-box-archive" aria-hidden="true"></i></div>
      <div class="ap-hero__copy">
        <h1>Apartados</h1>
        <p>El cliente reserva un producto con un enganche y liquida el saldo con abonos antes de llevárselo.</p>
        <div class="ap-hero__badges">
          <span class="ap-hero__badge ap-hero__badge--enganche"><i class="fa-solid fa-hand-holding-dollar"></i> Enganche inicial</span>
          <span class="ap-hero__badge ap-hero__badge--abonos"><i class="fa-solid fa-coins"></i> Abonos parciales</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Stats -->
  <div class="ap-stats">
    <div class="ap-stat">
      <div class="ap-stat__value" id="ap-stat-activos">—</div>
      <div class="ap-stat__label">Apartados activos</div>
      <div class="ap-stat__sub" id="ap-stat-activos-monto">—</div>
    </div>
    <div class="ap-stat ap-stat--warn">
      <div class="ap-stat__value" id="ap-stat-vencer">—</div>
      <div class="ap-stat__label">Por vencer (7 días)</div>
      <div class="ap-stat__sub">revisar próximamente</div>
    </div>
    <div class="ap-stat ap-stat--ok">
      <div class="ap-stat__value" id="ap-stat-completados">—</div>
      <div class="ap-stat__label">Completados este mes</div>
      <div class="ap-stat__sub" id="ap-stat-completados-monto">—</div>
    </div>
    <div class="ap-stat">
      <div class="ap-stat__value" id="ap-stat-pendiente">—</div>
      <div class="ap-stat__label">Saldo pendiente total</div>
      <div class="ap-stat__sub">en todos los activos</div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="ap-tabs">
    <button class="ap-tab is-active" data-tab="activos">Activos</button>
    <button class="ap-tab" data-tab="completados">Completados</button>
    <button class="ap-tab" data-tab="cancelados">Cancelados / Vencidos</button>
  </div>

  <!-- Panel: Activos -->
  <div class="ap-tab-panel is-active" id="ap-panel-activos">
    <div class="ap-toolbar">
      <input class="ap-search" type="search" id="ap-search-activos" placeholder="Buscar por folio, cliente, producto…" />
      <button class="ap-btn-add" id="ap-add-btn">
        <i class="fa-solid fa-plus" aria-hidden="true"></i> Nuevo apartado
      </button>
    </div>
    <div class="ap-table-wrap">
      <table class="ap-table">
        <thead>
          <tr>
            <th>Folio</th>
            <th>Cliente</th>
            <th>Producto</th>
            <th>Total</th>
            <th>Pagado</th>
            <th>Pendiente</th>
            <th>Avance</th>
            <th>Fecha límite</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody id="ap-tbody-activos"></tbody>
      </table>
    </div>
  </div>

  <!-- Panel: Completados -->
  <div class="ap-tab-panel" id="ap-panel-completados">
    <div class="ap-toolbar">
      <input class="ap-search" type="search" id="ap-search-completados" placeholder="Buscar…" />
    </div>
    <div class="ap-table-wrap">
      <table class="ap-table">
        <thead>
          <tr>
            <th>Folio</th>
            <th>Cliente</th>
            <th>Producto</th>
            <th>Total</th>
            <th>Abonos</th>
            <th>Completado</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody id="ap-tbody-completados"></tbody>
      </table>
    </div>
  </div>

  <!-- Panel: Cancelados / Vencidos -->
  <div class="ap-tab-panel" id="ap-panel-cancelados">
    <div class="ap-toolbar">
      <input class="ap-search" type="search" id="ap-search-cancelados" placeholder="Buscar…" />
    </div>
    <div class="ap-table-wrap">
      <table class="ap-table">
        <thead>
          <tr>
            <th>Folio</th>
            <th>Cliente</th>
            <th>Producto</th>
            <th>Total</th>
            <th>Recuperado</th>
            <th>Fecha límite</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody id="ap-tbody-cancelados"></tbody>
      </table>
    </div>
  </div>

</main>

<!-- ══════════════════════════════════════════════════════════════════════
     Drawer: Nuevo / Editar apartado
═══════════════════════════════════════════════════════════════════════ -->
<div class="ap-drawer-bg" id="ap-new-drawer-bg" role="dialog" aria-modal="true" aria-labelledby="ap-new-title">
  <div class="ap-drawer">
    <h2 class="ap-drawer__title" id="ap-new-title">Nuevo apartado</h2>
    <p class="ap-drawer__subtitle" id="ap-new-subtitle">Registra el enganche y los datos del cliente y producto</p>

    <p class="ap-section-title" style="margin-top:0;padding-top:0;border-top:none">Datos del cliente</p>
    <div class="ap-field--row">
      <div class="ap-field">
        <label>Nombre del cliente *</label>
        <input type="text" id="ap-f-nombre" maxlength="120" placeholder="Nombre completo" />
      </div>
      <div class="ap-field">
        <label>Teléfono</label>
        <input type="tel" id="ap-f-tel" maxlength="20" placeholder="10 dígitos" />
      </div>
    </div>
    <div class="ap-field">
      <label>Correo electrónico</label>
      <input type="email" id="ap-f-email" maxlength="120" placeholder="cliente@correo.com" />
    </div>

    <p class="ap-section-title">Producto apartado</p>
    <div class="ap-field">
      <label>Nombre del producto *</label>
      <input type="text" id="ap-f-producto" maxlength="160" placeholder="Ej. Televisor 55″ 4K" />
    </div>
    <div class="ap-field">
      <label>Descripción / SKU</label>
      <input type="text" id="ap-f-sku" maxlength="120" placeholder="Modelo, color, referencia…" />
    </div>
    <div class="ap-field--row3">
      <div class="ap-field">
        <label>Precio total *</label>
        <input type="number" id="ap-f-precio" min="0" step="0.01" placeholder="0.00" />
      </div>
      <div class="ap-field">
        <label>Enganche *</label>
        <input type="number" id="ap-f-enganche" min="0" step="0.01" placeholder="0.00" />
      </div>
      <div class="ap-field ap-field--ro">
        <label>Saldo inicial</label>
        <input type="number" id="ap-f-saldo" readonly placeholder="Auto" />
      </div>
    </div>

    <p class="ap-section-title">Plan de pago</p>
    <div class="ap-field--row">
      <div class="ap-field">
        <label>Modalidad</label>
        <select id="ap-f-modalidad">
          <option value="libre">Abonos libres</option>
          <option value="cuotas">Cuotas fijas</option>
        </select>
      </div>
      <div class="ap-field" id="ap-f-cuotas-wrap" style="display:none">
        <label>Número de cuotas</label>
        <input type="number" id="ap-f-cuotas" min="1" step="1" placeholder="Ej. 4" />
      </div>
    </div>
    <div class="ap-field--row" id="ap-f-cuota-monto-row" style="display:none">
      <div class="ap-field ap-field--ro">
        <label>Monto por cuota</label>
        <input type="number" id="ap-f-cuota-monto" readonly placeholder="Auto" />
      </div>
      <div class="ap-field">
        <label>Periodicidad</label>
        <select id="ap-f-periodicidad">
          <option value="semanal">Semanal</option>
          <option value="quincenal">Quincenal</option>
          <option value="mensual">Mensual</option>
        </select>
      </div>
    </div>
    <div class="ap-field--row">
      <div class="ap-field">
        <label>Fecha de inicio</label>
        <input type="date" id="ap-f-fecha-inicio" />
      </div>
      <div class="ap-field">
        <label>Fecha límite *</label>
        <input type="date" id="ap-f-fecha-limite" />
      </div>
    </div>
    <div class="ap-field">
      <label>Notas / Condiciones</label>
      <textarea id="ap-f-notas" rows="2" placeholder="Ej. El cliente no puede cambiar el modelo. Se entrega en tienda."></textarea>
    </div>

    <div class="ap-drawer__footer">
      <button class="ap-btn ap-btn--danger" id="ap-new-delete-btn" style="display:none">Eliminar</button>
      <button class="ap-btn ap-btn--secondary" id="ap-new-cancel-btn">Cancelar</button>
      <button class="ap-btn ap-btn--primary" id="ap-new-save-btn">Guardar apartado</button>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════════════
     Drawer: Detalle + abonos
═══════════════════════════════════════════════════════════════════════ -->
<div class="ap-drawer-bg" id="ap-detail-drawer-bg" role="dialog" aria-modal="true" aria-labelledby="ap-detail-title">
  <div class="ap-drawer">
    <h2 class="ap-drawer__title" id="ap-detail-title">Apartado</h2>
    <p class="ap-drawer__subtitle" id="ap-detail-subtitle"></p>

    <!-- Progress -->
    <div class="ap-detail-prog">
      <div class="ap-detail-prog__header">
        <span class="ap-detail-prog__title">Avance de pago</span>
        <span class="ap-detail-prog__pct" id="ap-dp-pct">0%</span>
      </div>
      <div class="ap-detail-bar">
        <div class="ap-detail-fill" id="ap-dp-bar" style="width:0%"></div>
      </div>
      <div class="ap-detail-amounts">
        <div>
          <div class="ap-detail-amount__label">Total</div>
          <div class="ap-detail-amount__value" id="ap-dp-total">—</div>
        </div>
        <div>
          <div class="ap-detail-amount__label">Pagado</div>
          <div class="ap-detail-amount__value" style="color:var(--ap-success)" id="ap-dp-pagado">—</div>
        </div>
        <div>
          <div class="ap-detail-amount__label">Pendiente</div>
          <div class="ap-detail-amount__value" style="color:var(--ap-danger)" id="ap-dp-pendiente">—</div>
        </div>
      </div>
    </div>

    <!-- Abonos list -->
    <p class="ap-section-title" style="margin-top:4px">Historial de abonos</p>
    <div class="ap-abonos-list" id="ap-abonos-list"></div>

    <!-- Nuevo abono inline form -->
    <div class="ap-abono-form" id="ap-abono-form">
      <div class="ap-abono-form__title"><i class="fa-solid fa-plus" style="margin-right:5px"></i>Registrar abono</div>
      <div class="ap-abono-form__grid">
        <div>
          <label style="font-size:0.75rem;font-weight:700;color:var(--ap-muted);text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:4px">Monto *</label>
          <input type="number" id="ap-abono-monto" min="0" step="0.01" placeholder="0.00" />
        </div>
        <div>
          <label style="font-size:0.75rem;font-weight:700;color:var(--ap-muted);text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:4px">Fecha</label>
          <input type="date" id="ap-abono-fecha" />
        </div>
        <div>
          <label style="font-size:0.75rem;font-weight:700;color:var(--ap-muted);text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:4px">Método de pago</label>
          <select id="ap-abono-metodo">
            <option value="efectivo">Efectivo</option>
            <option value="transferencia">Transferencia</option>
            <option value="tarjeta">Tarjeta</option>
            <option value="otro">Otro</option>
          </select>
        </div>
        <div>
          <label style="font-size:0.75rem;font-weight:700;color:var(--ap-muted);text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:4px">Referencia</label>
          <input type="text" id="ap-abono-ref" maxlength="60" placeholder="Opcional" />
        </div>
      </div>
      <div class="ap-abono-form__actions">
        <button class="ap-abono-save-btn" id="ap-abono-save-btn">
          <i class="fa-solid fa-check" style="margin-right:5px"></i>Confirmar abono
        </button>
      </div>
    </div>

    <div class="ap-drawer__footer">
      <button class="ap-btn ap-btn--secondary" id="ap-detail-edit-btn">
        <i class="fa-solid fa-pen" style="margin-right:5px"></i>Editar
      </button>
      <button class="ap-btn ap-btn--warn" id="ap-detail-cancel-ap-btn">Cancelar apartado</button>
      <button class="ap-btn ap-btn--success" id="ap-detail-entregar-btn">
        <i class="fa-solid fa-box-open" style="margin-right:5px"></i>Marcar entregado
      </button>
      <button class="ap-btn ap-btn--secondary" id="ap-detail-close-btn">Cerrar</button>
    </div>
  </div>
</div>

<script>
(function () {
  var LS_KEY = 'multitienda_apartados';

  // ── Storage ──────────────────────────────────────────────────────────────
  function load()    { try { return JSON.parse(localStorage.getItem(LS_KEY) || '[]'); } catch { return []; } }
  function save(d)   { localStorage.setItem(LS_KEY, JSON.stringify(d)); }

  // ── Helpers ──────────────────────────────────────────────────────────────
  function fmt(n) { return '$' + parseFloat(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function escHtml(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function today() { return new Date().toISOString().slice(0,10); }
  function inDays(dateStr, days) {
    if (!dateStr) return false;
    var d = new Date(dateStr + 'T00:00:00');
    var now = new Date(); now.setHours(0,0,0,0);
    var diff = (d - now) / 86400000;
    return diff >= 0 && diff <= days;
  }
  function isOverdue(dateStr) {
    if (!dateStr) return false;
    var d = new Date(dateStr + 'T00:00:00');
    var now = new Date(); now.setHours(0,0,0,0);
    return d < now;
  }
  function currentMonth() { return new Date().toISOString().slice(0,7); }
  function totalPagado(ap) {
    return (ap.abonos || []).reduce(function(s,a){ return s + parseFloat(a.monto || 0); }, 0)
           + parseFloat(ap.enganche || 0);
  }

  // ── Stats ────────────────────────────────────────────────────────────────
  function refreshStats() {
    var list = load();
    var activos     = list.filter(function(a){ return a.estado === 'activo'; });
    var vencer      = activos.filter(function(a){ return inDays(a.fechaLimite, 7); });
    var mes         = currentMonth();
    var completados = list.filter(function(a){ return (a.estado === 'completado' || a.estado === 'entregado') && (a.fechaCompletado || '').startsWith(mes); });
    var pendTotal   = activos.reduce(function(s,a){ var t = parseFloat(a.precio||0); var p = totalPagado(a); return s + Math.max(0, t - p); }, 0);
    var activosMonto= activos.reduce(function(s,a){ return s + parseFloat(a.precio||0); }, 0);
    var compMonto   = completados.reduce(function(s,a){ return s + parseFloat(a.precio||0); }, 0);

    setText('ap-stat-activos',           activos.length);
    setText('ap-stat-activos-monto',     fmt(activosMonto) + ' en productos');
    setText('ap-stat-vencer',            vencer.length);
    setText('ap-stat-completados',       completados.length);
    setText('ap-stat-completados-monto', fmt(compMonto) + ' recuperado');
    setText('ap-stat-pendiente',         fmt(pendTotal));
  }

  function setText(id, val) { var el = document.getElementById(id); if (el) el.textContent = val; }

  // ── Badge helpers ─────────────────────────────────────────────────────────
  var BADGE_CSS   = { activo:'ap-badge--activo', completado:'ap-badge--completado', entregado:'ap-badge--entregado', cancelado:'ap-badge--cancelado', vencido:'ap-badge--vencido' };
  var BADGE_LABEL = { activo:'Activo', completado:'Liquidado', entregado:'Entregado', cancelado:'Cancelado', vencido:'Vencido' };
  function badge(estado) { return '<span class="ap-badge ' + (BADGE_CSS[estado]||'') + '">' + (BADGE_LABEL[estado]||estado) + '</span>'; }

  // ── Render rows ───────────────────────────────────────────────────────────
  function rowActivo(ap) {
    var precio   = parseFloat(ap.precio || 0);
    var pagado   = totalPagado(ap);
    var pend     = Math.max(0, precio - pagado);
    var pct      = precio > 0 ? Math.min(100, Math.round(pagado / precio * 100)) : 0;
    var overdue  = isOverdue(ap.fechaLimite);
    var fillCls  = pct >= 100 ? ' ap-prog-fill--done' : (overdue ? ' ap-prog-fill--warn' : '');
    var prog     = '<div class="ap-prog-wrap">'
                 + '<div class="ap-prog-bar"><div class="ap-prog-fill' + fillCls + '" style="width:' + pct + '%"></div></div>'
                 + '<span class="ap-prog-pct">' + pct + '%</span>'
                 + '</div>';
    var fechaLbl = ap.fechaLimite
      ? (overdue ? '<span class="ap-overdue-dot"></span>' : '') + escHtml(ap.fechaLimite)
      : '—';
    return '<tr data-id="' + ap.id + '" data-drawer="detail">'
      + '<td><code style="font-size:0.82rem">' + escHtml(ap.folio) + '</code></td>'
      + '<td><div class="ap-client"><span class="ap-client__name">' + escHtml(ap.nombre) + '</span>'
      + '<span class="ap-client__tel">' + escHtml(ap.telefono||'') + '</span></div></td>'
      + '<td>' + escHtml(ap.producto) + '</td>'
      + '<td class="ap-money">' + fmt(precio) + '</td>'
      + '<td class="ap-money ap-money--paid">' + fmt(pagado) + '</td>'
      + '<td class="ap-money ap-money--pend">' + fmt(pend) + '</td>'
      + '<td>' + prog + '</td>'
      + '<td style="white-space:nowrap">' + fechaLbl + '</td>'
      + '<td>' + badge(ap.estado) + '</td>'
      + '</tr>';
  }

  function rowCompletado(ap) {
    var precio = parseFloat(ap.precio || 0);
    var n      = (ap.abonos || []).length + 1;
    return '<tr data-id="' + ap.id + '" data-drawer="detail">'
      + '<td><code style="font-size:0.82rem">' + escHtml(ap.folio) + '</code></td>'
      + '<td><div class="ap-client"><span class="ap-client__name">' + escHtml(ap.nombre) + '</span>'
      + '<span class="ap-client__tel">' + escHtml(ap.telefono||'') + '</span></div></td>'
      + '<td>' + escHtml(ap.producto) + '</td>'
      + '<td class="ap-money">' + fmt(precio) + '</td>'
      + '<td>' + n + ' pagos</td>'
      + '<td style="white-space:nowrap">' + escHtml(ap.fechaCompletado||'') + '</td>'
      + '<td>' + badge(ap.estado) + '</td>'
      + '</tr>';
  }

  function rowCancelado(ap) {
    var precio  = parseFloat(ap.precio || 0);
    var pagado  = totalPagado(ap);
    return '<tr data-id="' + ap.id + '" data-drawer="detail">'
      + '<td><code style="font-size:0.82rem">' + escHtml(ap.folio) + '</code></td>'
      + '<td><div class="ap-client"><span class="ap-client__name">' + escHtml(ap.nombre) + '</span>'
      + '<span class="ap-client__tel">' + escHtml(ap.telefono||'') + '</span></div></td>'
      + '<td>' + escHtml(ap.producto) + '</td>'
      + '<td class="ap-money">' + fmt(precio) + '</td>'
      + '<td class="ap-money ap-money--warn">' + fmt(pagado) + '</td>'
      + '<td style="white-space:nowrap">' + escHtml(ap.fechaLimite||'') + '</td>'
      + '<td>' + badge(ap.estado) + '</td>'
      + '</tr>';
  }

  function emptyRow(cols, icon, msg) {
    return '<tr class="ap-table__empty"><td colspan="' + cols + '"><i class="fa-solid ' + icon + '" style="font-size:1.8rem;margin-bottom:10px;display:block;opacity:.3"></i>' + msg + '</td></tr>';
  }

  function renderAll() {
    var list = load();
    renderTab('activos',    list, 'ap-search-activos');
    renderTab('completados',list, 'ap-search-completados');
    renderTab('cancelados', list, 'ap-search-cancelados');
    refreshStats();
  }

  function filterList(list, tab, search) {
    return list.filter(function(ap){
      if (tab === 'activos'    && ap.estado !== 'activo')   return false;
      if (tab === 'completados'&& ap.estado !== 'completado' && ap.estado !== 'entregado') return false;
      if (tab === 'cancelados' && ap.estado !== 'cancelado' && ap.estado !== 'vencido')    return false;
      if (search) {
        var hay = (ap.folio + ' ' + ap.nombre + ' ' + ap.producto).toLowerCase();
        if (!hay.includes(search.toLowerCase())) return false;
      }
      return true;
    });
  }

  function renderTab(tab, list, searchId) {
    var search   = (document.getElementById(searchId) && document.getElementById(searchId).value) || '';
    var filtered = filterList(list, tab, search);
    var tbody    = document.getElementById('ap-tbody-' + tab);
    if (!tbody) return;
    if (!filtered.length) {
      if (tab === 'activos')     tbody.innerHTML = emptyRow(9, 'fa-box-archive', 'No hay apartados activos.');
      if (tab === 'completados') tbody.innerHTML = emptyRow(7, 'fa-circle-check', 'Ningún apartado completado.');
      if (tab === 'cancelados')  tbody.innerHTML = emptyRow(7, 'fa-ban', 'Sin cancelados ni vencidos.');
      return;
    }
    if (tab === 'activos')     tbody.innerHTML = filtered.map(rowActivo).join('');
    if (tab === 'completados') tbody.innerHTML = filtered.map(rowCompletado).join('');
    if (tab === 'cancelados')  tbody.innerHTML = filtered.map(rowCancelado).join('');
  }

  // ── Tab switching ─────────────────────────────────────────────────────────
  document.querySelectorAll('.ap-tab').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.ap-tab').forEach(function(b){ b.classList.remove('is-active'); });
      document.querySelectorAll('.ap-tab-panel').forEach(function(p){ p.classList.remove('is-active'); });
      btn.classList.add('is-active');
      var panel = document.getElementById('ap-panel-' + btn.dataset.tab);
      if (panel) panel.classList.add('is-active');
    });
  });

  // ── Search ────────────────────────────────────────────────────────────────
  ['activos','completados','cancelados'].forEach(function(tab){
    var el = document.getElementById('ap-search-' + tab);
    if (el) el.addEventListener('input', function(){
      renderTab(tab, load(), 'ap-search-' + tab);
    });
  });

  // ── Row click → drawer ────────────────────────────────────────────────────
  document.addEventListener('click', function(e){
    var tr = e.target.closest('tr[data-id][data-drawer]');
    if (!tr) return;
    if (tr.dataset.drawer === 'detail') openDetailDrawer(tr.dataset.id);
  });

  // ────────────────────────────────────────────────────────────────────────
  // NEW / EDIT DRAWER
  // ────────────────────────────────────────────────────────────────────────
  var newDrawerBg = document.getElementById('ap-new-drawer-bg');
  var newEditingId = null;

  function openNewDrawer(id) {
    newEditingId = id;
    var list = load();
    var item = id ? list.find(function(a){ return a.id === id; }) : null;
    document.getElementById('ap-new-title').textContent = id ? 'Editar apartado' : 'Nuevo apartado';
    document.getElementById('ap-f-nombre').value       = item ? item.nombre       : '';
    document.getElementById('ap-f-tel').value          = item ? item.telefono      : '';
    document.getElementById('ap-f-email').value        = item ? item.email         : '';
    document.getElementById('ap-f-producto').value     = item ? item.producto      : '';
    document.getElementById('ap-f-sku').value          = item ? item.sku           : '';
    document.getElementById('ap-f-precio').value       = item ? item.precio        : '';
    document.getElementById('ap-f-enganche').value     = item ? item.enganche      : '';
    document.getElementById('ap-f-saldo').value        = item ? (parseFloat(item.precio||0) - parseFloat(item.enganche||0)).toFixed(2) : '';
    document.getElementById('ap-f-modalidad').value    = item ? (item.modalidad || 'libre') : 'libre';
    document.getElementById('ap-f-cuotas').value       = item ? (item.cuotas || '') : '';
    document.getElementById('ap-f-periodicidad').value = item ? (item.periodicidad || 'mensual') : 'mensual';
    document.getElementById('ap-f-fecha-inicio').value = item ? item.fechaInicio   : today();
    document.getElementById('ap-f-fecha-limite').value = item ? item.fechaLimite   : '';
    document.getElementById('ap-f-notas').value        = item ? item.notas         : '';
    document.getElementById('ap-new-delete-btn').style.display = id ? 'inline-flex' : 'none';
    toggleModalidad();
    calcSaldo();
    calcCuotaMonto();
    newDrawerBg.classList.add('is-open');
    document.getElementById('ap-f-nombre').focus();
  }

  function closeNewDrawer() { newDrawerBg.classList.remove('is-open'); newEditingId = null; }

  document.getElementById('ap-add-btn').addEventListener('click', function(){ openNewDrawer(null); });
  document.getElementById('ap-new-cancel-btn').addEventListener('click', closeNewDrawer);
  newDrawerBg.addEventListener('click', function(e){ if (e.target === newDrawerBg) closeNewDrawer(); });

  // Auto-calc saldo inicial
  function calcSaldo() {
    var p = parseFloat(document.getElementById('ap-f-precio').value || 0);
    var e = parseFloat(document.getElementById('ap-f-enganche').value || 0);
    document.getElementById('ap-f-saldo').value = p > 0 ? Math.max(0, p - e).toFixed(2) : '';
    calcCuotaMonto();
  }
  document.getElementById('ap-f-precio').addEventListener('input', calcSaldo);
  document.getElementById('ap-f-enganche').addEventListener('input', calcSaldo);

  function calcCuotaMonto() {
    var p = parseFloat(document.getElementById('ap-f-precio').value || 0);
    var e = parseFloat(document.getElementById('ap-f-enganche').value || 0);
    var n = parseInt(document.getElementById('ap-f-cuotas').value || 0);
    var el = document.getElementById('ap-f-cuota-monto');
    if (p > 0 && n > 0) el.value = Math.max(0, (p - e) / n).toFixed(2);
    else el.value = '';
  }
  document.getElementById('ap-f-cuotas').addEventListener('input', calcCuotaMonto);

  function toggleModalidad() {
    var val = document.getElementById('ap-f-modalidad').value;
    document.getElementById('ap-f-cuotas-wrap').style.display       = val === 'cuotas' ? 'block' : 'none';
    document.getElementById('ap-f-cuota-monto-row').style.display   = val === 'cuotas' ? 'grid'  : 'none';
  }
  document.getElementById('ap-f-modalidad').addEventListener('change', toggleModalidad);

  // Folio generator
  function genFolio() {
    var n = (load().length + 1).toString().padStart(4, '0');
    return 'AP-' + new Date().getFullYear() + '-' + n;
  }

  document.getElementById('ap-new-save-btn').addEventListener('click', function(){
    var nombre   = document.getElementById('ap-f-nombre').value.trim();
    var producto = document.getElementById('ap-f-producto').value.trim();
    var precio   = parseFloat(document.getElementById('ap-f-precio').value || 0);
    var enganche = parseFloat(document.getElementById('ap-f-enganche').value || 0);
    var fechaLim = document.getElementById('ap-f-fecha-limite').value;
    if (!nombre)   { document.getElementById('ap-f-nombre').focus();   return; }
    if (!producto) { document.getElementById('ap-f-producto').focus(); return; }
    if (!precio)   { document.getElementById('ap-f-precio').focus();   return; }
    if (!fechaLim) { document.getElementById('ap-f-fecha-limite').focus(); return; }

    var list = load();
    var item = {
      id:           newEditingId || ('ap-' + Date.now()),
      folio:        newEditingId ? (list.find(function(a){ return a.id === newEditingId; }) || {}).folio : genFolio(),
      nombre,
      telefono:     document.getElementById('ap-f-tel').value.trim(),
      email:        document.getElementById('ap-f-email').value.trim(),
      producto,
      sku:          document.getElementById('ap-f-sku').value.trim(),
      precio,
      enganche,
      modalidad:    document.getElementById('ap-f-modalidad').value,
      cuotas:       parseInt(document.getElementById('ap-f-cuotas').value || 0),
      periodicidad: document.getElementById('ap-f-periodicidad').value,
      fechaInicio:  document.getElementById('ap-f-fecha-inicio').value,
      fechaLimite:  fechaLim,
      notas:        document.getElementById('ap-f-notas').value.trim(),
      estado:       'activo',
      abonos:       [],
    };
    if (newEditingId) {
      var idx = list.findIndex(function(a){ return a.id === newEditingId; });
      if (idx >= 0) { item.abonos = list[idx].abonos || []; item.estado = list[idx].estado; list[idx] = item; }
    } else {
      list.push(item);
    }
    save(list);
    renderAll();
    closeNewDrawer();
  });

  document.getElementById('ap-new-delete-btn').addEventListener('click', function(){
    if (!newEditingId) return;
    if (!confirm('¿Eliminar este apartado permanentemente?')) return;
    save(load().filter(function(a){ return a.id !== newEditingId; }));
    renderAll();
    closeNewDrawer();
  });

  // ────────────────────────────────────────────────────────────────────────
  // DETAIL DRAWER (abonos)
  // ────────────────────────────────────────────────────────────────────────
  var detailDrawerBg = document.getElementById('ap-detail-drawer-bg');
  var detailId = null;

  function openDetailDrawer(id) {
    detailId = id;
    renderDetailDrawer(id);
    document.getElementById('ap-abono-fecha').value = today();
    document.getElementById('ap-abono-monto').value = '';
    document.getElementById('ap-abono-ref').value   = '';
    detailDrawerBg.classList.add('is-open');
  }

  function renderDetailDrawer(id) {
    var list = load();
    var ap   = list.find(function(a){ return a.id === id; });
    if (!ap) return;

    var precio  = parseFloat(ap.precio || 0);
    var pagado  = totalPagado(ap);
    var pend    = Math.max(0, precio - pagado);
    var pct     = precio > 0 ? Math.min(100, Math.round(pagado / precio * 100)) : 0;

    document.getElementById('ap-detail-title').textContent    = ap.folio;
    document.getElementById('ap-detail-subtitle').textContent = ap.producto + ' · ' + ap.nombre;
    document.getElementById('ap-dp-pct').textContent = pct + '%';
    document.getElementById('ap-dp-total').textContent    = fmt(precio);
    document.getElementById('ap-dp-pagado').textContent   = fmt(pagado);
    document.getElementById('ap-dp-pendiente').textContent= fmt(pend);

    var bar = document.getElementById('ap-dp-bar');
    bar.style.width = pct + '%';
    bar.className   = 'ap-detail-fill' + (pct >= 100 ? ' ap-detail-fill--done' : '');

    // Abonos list
    var abonosList = document.getElementById('ap-abonos-list');
    var allAbonos  = [{ monto: ap.enganche, fecha: ap.fechaInicio, metodo: 'enganche', ref: 'Enganche inicial', _eng: true }]
                    .concat(ap.abonos || []);
    if (!allAbonos.length || (allAbonos.length === 1 && !parseFloat(allAbonos[0].monto))) {
      abonosList.innerHTML = '<div class="ap-abonos-empty">Sin abonos registrados aún.</div>';
    } else {
      abonosList.innerHTML = allAbonos.map(function(ab, i){
        var isEng = ab._eng;
        return '<div class="ap-abono-row">'
          + '<div class="ap-abono-row__icon"><i class="fa-solid ' + (isEng ? 'fa-handshake' : 'fa-coins') + '"></i></div>'
          + '<div class="ap-abono-row__info">'
          + '<div class="ap-abono-row__fecha">' + escHtml(ab.fecha || '') + (isEng ? ' — <strong>Enganche</strong>' : '') + '</div>'
          + '<div class="ap-abono-row__metodo">' + escHtml(ab.metodo || '') + (ab.ref ? ' · ' + escHtml(ab.ref) : '') + '</div>'
          + '</div>'
          + '<span class="ap-abono-row__monto">' + fmt(ab.monto) + '</span>'
          + (!isEng ? '<button class="ap-abono-row__del" data-abono-idx="' + i + '" title="Eliminar abono"><i class="fa-solid fa-trash"></i></button>' : '')
          + '</div>';
      }).join('');
    }

    // Show/hide form & buttons based on status
    var isActive  = ap.estado === 'activo';
    document.getElementById('ap-abono-form').style.display       = isActive ? 'block' : 'none';
    document.getElementById('ap-detail-entregar-btn').style.display    = (ap.estado === 'completado') ? 'inline-flex' : 'none';
    document.getElementById('ap-detail-cancel-ap-btn').style.display   = isActive ? 'inline-flex' : 'none';
  }

  // Delete abono
  document.getElementById('ap-abonos-list').addEventListener('click', function(e){
    var btn = e.target.closest('[data-abono-idx]');
    if (!btn) return;
    var idx  = parseInt(btn.dataset.abonoIdx);
    var list = load();
    var ap   = list.find(function(a){ return a.id === detailId; });
    if (!ap) return;
    // idx 0 = enganche row (not deletable), real abonos start at index 1
    var abonoIdx = idx - 1;
    if (abonoIdx < 0) return;
    if (!confirm('¿Eliminar este abono?')) return;
    ap.abonos.splice(abonoIdx, 1);
    // Recalculate state
    var pagado = totalPagado(ap);
    if (pagado < parseFloat(ap.precio || 0)) ap.estado = 'activo';
    save(list);
    renderDetailDrawer(detailId);
    renderAll();
  });

  // Save abono
  document.getElementById('ap-abono-save-btn').addEventListener('click', function(){
    var monto = parseFloat(document.getElementById('ap-abono-monto').value || 0);
    if (!monto) { document.getElementById('ap-abono-monto').focus(); return; }
    var list = load();
    var ap   = list.find(function(a){ return a.id === detailId; });
    if (!ap) return;
    ap.abonos = ap.abonos || [];
    ap.abonos.push({
      monto:  monto,
      fecha:  document.getElementById('ap-abono-fecha').value || today(),
      metodo: document.getElementById('ap-abono-metodo').value,
      ref:    document.getElementById('ap-abono-ref').value.trim(),
    });
    // Check if fully paid
    var pagado = totalPagado(ap);
    var precio = parseFloat(ap.precio || 0);
    if (pagado >= precio) {
      ap.estado          = 'completado';
      ap.fechaCompletado = today();
    }
    save(list);
    renderDetailDrawer(detailId);
    renderAll();
    document.getElementById('ap-abono-monto').value = '';
    document.getElementById('ap-abono-ref').value   = '';
  });

  // Marcar entregado
  document.getElementById('ap-detail-entregar-btn').addEventListener('click', function(){
    var list = load();
    var ap   = list.find(function(a){ return a.id === detailId; });
    if (!ap) return;
    ap.estado = 'entregado';
    save(list);
    renderDetailDrawer(detailId);
    renderAll();
  });

  // Cancelar apartado
  document.getElementById('ap-detail-cancel-ap-btn').addEventListener('click', function(){
    if (!confirm('¿Cancelar este apartado? El cliente ha pagado ' + fmt(totalPagado(load().find(function(a){ return a.id===detailId; })||{})) + ' hasta ahora.')) return;
    var list = load();
    var ap   = list.find(function(a){ return a.id === detailId; });
    if (ap) { ap.estado = 'cancelado'; }
    save(list);
    renderDetailDrawer(detailId);
    renderAll();
  });

  // Edit from detail drawer
  document.getElementById('ap-detail-edit-btn').addEventListener('click', function(){
    closeDetailDrawer();
    openNewDrawer(detailId);
  });

  function closeDetailDrawer() { detailDrawerBg.classList.remove('is-open'); detailId = null; }
  document.getElementById('ap-detail-close-btn').addEventListener('click', closeDetailDrawer);
  detailDrawerBg.addEventListener('click', function(e){ if (e.target === detailDrawerBg) closeDetailDrawer(); });

  // ── Init ──────────────────────────────────────────────────────────────────
  renderAll();
})();
</script>
</body>
</html>"""
