from __future__ import annotations


def repartidores_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Repartidores</title>
  <style>
    :root {
      --rd-accent:  #15803d;
      --rd-accent2: #166534;
      --rd-light:   #dcfce7;
      --rd-bg:      var(--page-bg, #f5f6f8);
      --rd-surface: var(--content-bg, #ffffff);
      --rd-border:  var(--field-border, #d1d5db);
      --rd-text:    var(--body-text, #1f2937);
      --rd-muted:   color-mix(in srgb, var(--body-text, #1f2937) 60%, #ffffff 40%);
      --rd-focus:   #15803d;
      --rd-danger:  #dc2626;
      --rd-warn:    #d97706;
      --rd-info:    #0284c7;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: var(--rd-bg); font-family: Arial, sans-serif; color: var(--rd-text); }

    .rd-page { padding: 0 0 48px; }

    /* ── Hero ───────────────────────────────────────────────────────────── */
    .rd-hero {
      background: linear-gradient(135deg, #052e16 0%, #14532d 50%, #0c1a28 100%);
      border-radius: 20px; padding: 32px 32px 28px; margin-bottom: 28px;
      position: relative; overflow: hidden;
    }
    .rd-hero::before {
      content: ""; position: absolute; inset: 0;
      background:
        radial-gradient(ellipse 56% 58% at 82% 16%, rgba(21,128,61,0.42) 0%, transparent 68%),
        radial-gradient(ellipse 38% 44% at 12% 84%, rgba(2,132,199,0.18) 0%, transparent 70%);
      pointer-events: none;
    }
    .rd-hero__inner { position: relative; z-index: 1; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
    .rd-hero__icon {
      width: 64px; height: 64px; border-radius: 20px; flex-shrink: 0;
      background: linear-gradient(135deg, #22c55e 0%, #15803d 100%);
      display: grid; place-items: center; font-size: 1.6rem; color: #fff;
      box-shadow: 0 8px 24px rgba(21,128,61,0.5);
    }
    .rd-hero__copy { flex: 1; min-width: 200px; }
    .rd-hero__copy h1 { margin: 0 0 6px; font-size: 1.55rem; font-weight: 800; color: #fff; letter-spacing: -0.02em; }
    .rd-hero__copy p  { margin: 0; color: rgba(255,255,255,0.72); font-size: 0.92rem; line-height: 1.5; }
    .rd-hero__badges  { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
    .rd-hero__badge {
      padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
      letter-spacing: 0.04em; text-transform: uppercase;
    }
    .rd-hero__badge--didi  { background: rgba(255,102,0,0.32); color: #fed7aa; border: 1px solid rgba(254,215,170,0.25); }
    .rd-hero__badge--uber  { background: rgba(2,132,199,0.28);  color: #bae6fd; border: 1px solid rgba(186,230,253,0.25); }
    .rd-hero__badge--own   { background: rgba(21,128,61,0.32);  color: #bbf7d0; border: 1px solid rgba(187,247,208,0.25); }

    /* ── Stats ──────────────────────────────────────────────────────────── */
    .rd-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 16px; margin-bottom: 28px; }
    .rd-stat  { background: var(--rd-surface); border: 1px solid var(--rd-border); border-radius: 16px; padding: 18px 20px; }
    .rd-stat__value { font-size: 1.75rem; font-weight: 800; color: var(--rd-accent); line-height: 1; margin-bottom: 4px; }
    .rd-stat__label { font-size: 0.8rem; color: var(--rd-muted); font-weight: 600; }
    .rd-stat__sub   { font-size: 0.72rem; color: var(--rd-muted); margin-top: 2px; }
    .rd-stat--live .rd-stat__value { color: var(--rd-info); }

    /* ── Tabs ───────────────────────────────────────────────────────────── */
    .rd-tabs { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
    .rd-tab  { padding: 8px 18px; border-radius: 12px; font-size: 0.88rem; font-weight: 700; cursor: pointer; border: 1.5px solid var(--rd-border); background: var(--rd-surface); color: var(--rd-muted); transition: all 0.16s; }
    .rd-tab.is-active { background: var(--rd-accent); color: #fff; border-color: var(--rd-accent); }
    .rd-tab-panel { display: none; }
    .rd-tab-panel.is-active { display: block; }

    /* ── Toolbar ────────────────────────────────────────────────────────── */
    .rd-toolbar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
    .rd-search  { flex: 1; min-width: 180px; max-width: 300px; padding: 9px 14px; border-radius: 12px; border: 1.5px solid var(--rd-border); font-size: 0.9rem; background: var(--rd-surface); color: var(--rd-text); outline: none; transition: border-color 0.15s; }
    .rd-search:focus { border-color: var(--rd-focus); }
    .rd-filter  { padding: 9px 14px; border-radius: 12px; border: 1.5px solid var(--rd-border); font-size: 0.88rem; background: var(--rd-surface); color: var(--rd-text); outline: none; cursor: pointer; }
    .rd-btn-add { margin-left: auto; padding: 9px 18px; border-radius: 12px; background: var(--rd-accent); color: #fff; font-weight: 700; font-size: 0.88rem; border: none; cursor: pointer; display: flex; align-items: center; gap: 7px; transition: opacity 0.15s; }
    .rd-btn-add:hover { opacity: 0.88; }

    /* ── Pipeline strip ─────────────────────────────────────────────────── */
    .rd-pipeline { display: flex; gap: 0; margin-bottom: 20px; overflow-x: auto; border-radius: 14px; border: 1px solid var(--rd-border); }
    .rd-pipeline__step { flex: 1; min-width: 100px; padding: 12px 10px; text-align: center; border-right: 1px solid var(--rd-border); cursor: pointer; transition: background 0.15s; }
    .rd-pipeline__step:last-child { border-right: none; }
    .rd-pipeline__step:hover { background: color-mix(in srgb, var(--rd-accent) 5%, var(--rd-surface) 95%); }
    .rd-pipeline__step.is-active { background: color-mix(in srgb, var(--rd-accent) 10%, var(--rd-surface) 90%); border-bottom: 3px solid var(--rd-accent); }
    .rd-pipeline__count { font-size: 1.4rem; font-weight: 800; color: var(--rd-accent); line-height: 1; }
    .rd-pipeline__label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: var(--rd-muted); margin-top: 3px; }

    /* ── Table ──────────────────────────────────────────────────────────── */
    .rd-table-wrap { overflow-x: auto; border-radius: 14px; border: 1px solid var(--rd-border); }
    .rd-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    .rd-table thead tr { background: color-mix(in srgb, var(--rd-surface) 82%, var(--rd-bg) 18%); }
    .rd-table th { padding: 12px 14px; text-align: left; font-size: 0.72rem; font-weight: 700; color: var(--rd-muted); text-transform: uppercase; letter-spacing: 0.08em; white-space: nowrap; }
    .rd-table td { padding: 12px 14px; border-top: 1px solid var(--rd-border); vertical-align: middle; }
    .rd-table tbody tr { cursor: pointer; transition: background 0.12s; }
    .rd-table tbody tr:hover { background: color-mix(in srgb, var(--rd-accent) 5%, var(--rd-surface) 95%); }
    .rd-table__empty td { text-align: center; padding: 56px 16px; color: var(--rd-muted); cursor: default; }

    /* ── Platform chips ─────────────────────────────────────────────────── */
    .rd-platform {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 3px 9px; border-radius: 10px; font-size: 0.72rem; font-weight: 800;
      text-transform: uppercase; letter-spacing: 0.06em; white-space: nowrap;
    }
    .rd-platform--didi   { background: #fff3e0; color: #e65100; border: 1px solid #ffcc80; }
    .rd-platform--uber   { background: #e8f5e9; color: #1b5e20; border: 1px solid #a5d6a7; }
    .rd-platform--rappi  { background: #fce4ec; color: #880e4f; border: 1px solid #f48fb1; }
    .rd-platform--propio { background: var(--rd-light); color: var(--rd-accent2); border: 1px solid #86efac; }
    .rd-platform--otro   { background: #f3f4f6; color: #374151; border: 1px solid var(--rd-border); }

    /* ── Status badges ──────────────────────────────────────────────────── */
    .rd-badge { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; white-space: nowrap; }
    .rd-badge--pendiente  { background: #fef3c7; color: #92400e; }
    .rd-badge--asignado   { background: #dbeafe; color: #1e40af; }
    .rd-badge--en_camino  { background: #dcfce7; color: #166534; }
    .rd-badge--entregado  { background: #d1fae5; color: #065f46; }
    .rd-badge--cancelado  { background: #f3f4f6; color: #6b7280; }
    .rd-badge--fallido    { background: #fee2e2; color: #991b1b; }
    .rd-badge--disponible    { background: #dcfce7; color: #166534; }
    .rd-badge--en_entrega    { background: #dbeafe; color: #1e40af; }
    .rd-badge--desconectado  { background: #f3f4f6; color: #6b7280; }

    /* ── Elapsed timer ──────────────────────────────────────────────────── */
    .rd-elapsed { font-size: 0.78rem; font-weight: 700; white-space: nowrap; }
    .rd-elapsed--ok   { color: var(--rd-accent); }
    .rd-elapsed--warn { color: var(--rd-warn); }
    .rd-elapsed--late { color: var(--rd-danger); }

    /* ── Driver cards ───────────────────────────────────────────────────── */
    .rd-driver-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
    .rd-driver-card {
      background: var(--rd-surface); border: 1px solid var(--rd-border);
      border-radius: 18px; padding: 20px 18px; display: grid; gap: 12px;
      cursor: pointer; transition: box-shadow 0.16s, transform 0.16s;
    }
    .rd-driver-card:hover { box-shadow: 0 8px 24px rgba(21,128,61,0.12); transform: translateY(-2px); }
    .rd-driver-card--disponible { border-color: color-mix(in srgb, var(--rd-accent) 30%, var(--rd-border) 70%); }
    .rd-driver-card__header { display: flex; align-items: center; gap: 12px; }
    .rd-driver-card__avatar {
      width: 46px; height: 46px; border-radius: 14px; flex-shrink: 0;
      display: grid; place-items: center; font-size: 1.1rem; font-weight: 800; color: #fff;
      background: linear-gradient(135deg, #22c55e 0%, #15803d 100%);
    }
    .rd-driver-card__info { flex: 1; min-width: 0; }
    .rd-driver-card__name { font-size: 0.95rem; font-weight: 800; margin: 0 0 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .rd-driver-card__tel  { font-size: 0.78rem; color: var(--rd-muted); }
    .rd-driver-card__meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
    .rd-driver-card__vehicle { font-size: 0.78rem; color: var(--rd-muted); display: flex; align-items: center; gap: 5px; }
    .rd-driver-card__count  { font-size: 0.78rem; font-weight: 700; color: var(--rd-accent); }
    .rd-driver-card__add {
      border: 1.5px dashed var(--rd-border); cursor: pointer; justify-items: center;
      padding: 28px; background: none; transition: border-color 0.15s;
    }
    .rd-driver-card__add:hover { border-color: var(--rd-accent); }

    /* ── Platform integration cards ─────────────────────────────────────── */
    .rd-plat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 18px; }
    .rd-plat-card {
      background: var(--rd-surface); border: 1px solid var(--rd-border);
      border-radius: 20px; padding: 22px; display: grid; gap: 14px;
    }
    .rd-plat-card__header { display: flex; align-items: center; gap: 14px; }
    .rd-plat-card__logo {
      width: 52px; height: 52px; border-radius: 16px; flex-shrink: 0;
      display: grid; place-items: center; font-size: 1.4rem; font-weight: 900; color: #fff;
    }
    .rd-plat-card__logo--didi   { background: linear-gradient(135deg, #ff6600 0%, #cc4400 100%); }
    .rd-plat-card__logo--uber   { background: linear-gradient(135deg, #000000 0%, #2d2d2d 100%); }
    .rd-plat-card__logo--rappi  { background: linear-gradient(135deg, #ff441b 0%, #c12d00 100%); }
    .rd-plat-card__logo--propio { background: linear-gradient(135deg, #22c55e 0%, #15803d 100%); }
    .rd-plat-card__name  { font-size: 1.05rem; font-weight: 800; }
    .rd-plat-card__desc  { font-size: 0.78rem; color: var(--rd-muted); margin-top: 1px; }
    .rd-plat-card__status { display: flex; align-items: center; gap: 8px; }
    .rd-plat-card__dot   { width: 9px; height: 9px; border-radius: 50%; background: #d1d5db; }
    .rd-plat-card__dot--on  { background: #22c55e; box-shadow: 0 0 0 3px rgba(34,197,94,0.2); }
    .rd-plat-card__dot--cfg { background: #f59e0b; box-shadow: 0 0 0 3px rgba(245,158,11,0.2); }
    .rd-plat-card__status-label { font-size: 0.78rem; font-weight: 700; }
    .rd-plat-card__status-label--on  { color: var(--rd-accent); }
    .rd-plat-card__status-label--cfg { color: var(--rd-warn); }
    .rd-plat-card__status-label--off { color: var(--rd-muted); }
    .rd-plat-card__fields { display: grid; gap: 8px; }
    .rd-plat-card__field-label { font-size: 0.72rem; font-weight: 700; color: var(--rd-muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 3px; }
    .rd-plat-card__input {
      width: 100%; padding: 8px 11px; border-radius: 9px; border: 1.5px solid var(--rd-border);
      font-size: 0.88rem; background: var(--rd-surface); color: var(--rd-text); outline: none; transition: border-color 0.15s;
    }
    .rd-plat-card__input:focus { border-color: var(--rd-focus); }
    .rd-plat-card__actions { display: flex; gap: 8px; }
    .rd-plat-btn {
      flex: 1; padding: 8px 14px; border-radius: 10px; font-size: 0.85rem; font-weight: 700;
      cursor: pointer; border: none; transition: opacity 0.15s;
    }
    .rd-plat-btn:hover { opacity: 0.88; }
    .rd-plat-btn--connect { background: var(--rd-accent); color: #fff; }
    .rd-plat-btn--test    { background: var(--rd-surface); color: var(--rd-muted); border: 1.5px solid var(--rd-border); }
    .rd-plat-btn--disconnect { background: #fee2e2; color: var(--rd-danger); }

    /* ── Drawer ─────────────────────────────────────────────────────────── */
    .rd-drawer-bg { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.44); z-index: 1040; align-items: flex-end; justify-content: center; }
    .rd-drawer-bg.is-open { display: flex; }
    .rd-drawer { background: var(--rd-surface); border-radius: 24px 24px 0 0; width: 100%; max-width: 680px; padding: 28px 28px 32px; max-height: 94vh; overflow-y: auto; }
    .rd-drawer__title    { font-size: 1.2rem; font-weight: 800; margin: 0 0 2px; }
    .rd-drawer__subtitle { font-size: 0.82rem; color: var(--rd-muted); margin: 0 0 22px; }

    /* ── Status pipeline (detail drawer) ────────────────────────────────── */
    .rd-status-pipeline { display: flex; gap: 0; margin-bottom: 20px; border-radius: 14px; border: 1px solid var(--rd-border); overflow: hidden; }
    .rd-status-step {
      flex: 1; padding: 10px 6px; text-align: center; cursor: pointer;
      border-right: 1px solid var(--rd-border); transition: background 0.14s;
      font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
      color: var(--rd-muted); position: relative;
    }
    .rd-status-step:last-child { border-right: none; }
    .rd-status-step.is-done { background: color-mix(in srgb, var(--rd-accent) 12%, var(--rd-surface) 88%); color: var(--rd-accent); }
    .rd-status-step.is-current { background: var(--rd-accent); color: #fff; }
    .rd-status-step i { display: block; font-size: 1rem; margin-bottom: 3px; }

    /* ── Form fields ────────────────────────────────────────────────────── */
    .rd-field { margin-bottom: 15px; }
    .rd-field label { display: block; font-size: 0.77rem; font-weight: 700; margin-bottom: 5px; color: var(--rd-muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .rd-field input, .rd-field select, .rd-field textarea { width: 100%; padding: 10px 12px; border-radius: 10px; border: 1.5px solid var(--rd-border); font-size: 0.95rem; background: var(--rd-surface); color: var(--rd-text); outline: none; transition: border-color 0.15s; }
    .rd-field input:focus, .rd-field select:focus, .rd-field textarea:focus { border-color: var(--rd-focus); }
    .rd-field textarea { resize: vertical; min-height: 64px; }
    .rd-field--row  { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .rd-field--row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
    .rd-section-title { font-size: 0.77rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: var(--rd-muted); margin: 20px 0 12px; padding-top: 16px; border-top: 1px solid var(--rd-border); }

    /* ── Map placeholder ─────────────────────────────────────────────────── */
    .rd-map-placeholder {
      height: 140px; border-radius: 12px; border: 1px solid var(--rd-border);
      background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      gap: 8px; color: var(--rd-accent); margin-bottom: 16px; cursor: pointer;
      transition: background 0.15s;
    }
    .rd-map-placeholder:hover { background: color-mix(in srgb, var(--rd-accent) 8%, #f0fdf4 92%); }
    .rd-map-placeholder i  { font-size: 1.8rem; opacity: 0.6; }
    .rd-map-placeholder p  { margin: 0; font-size: 0.82rem; font-weight: 700; opacity: 0.75; }

    /* ── Drawer footer ───────────────────────────────────────────────────── */
    .rd-drawer__footer { display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap; margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--rd-border); }
    .rd-btn { padding: 10px 20px; border-radius: 12px; font-size: 0.9rem; font-weight: 700; cursor: pointer; border: none; transition: opacity 0.15s; }
    .rd-btn:hover { opacity: 0.88; }
    .rd-btn--primary   { background: var(--rd-accent);  color: #fff; }
    .rd-btn--secondary { background: var(--rd-surface); color: var(--rd-muted); border: 1.5px solid var(--rd-border); }
    .rd-btn--danger    { background: #fee2e2; color: var(--rd-danger); }
    .rd-btn--warn      { background: #fef3c7; color: var(--rd-warn); }

    @media (max-width: 640px) {
      .rd-hero { padding: 20px 16px 18px; }
      .rd-hero__copy h1 { font-size: 1.25rem; }
      .rd-field--row, .rd-field--row3 { grid-template-columns: 1fr; }
      .rd-pipeline__label { font-size: 0.62rem; }
    }
  </style>
</head>
<body>
<main class="rd-page">

  <!-- Hero -->
  <div class="rd-hero">
    <div class="rd-hero__inner">
      <div class="rd-hero__icon"><i class="fa-solid fa-motorcycle" aria-hidden="true"></i></div>
      <div class="rd-hero__copy">
        <h1>Repartidores</h1>
        <p>Gestiona entregas a domicilio con tu flota propia o conectado a DiDi Food, Uber Eats y Rappi.</p>
        <div class="rd-hero__badges">
          <span class="rd-hero__badge rd-hero__badge--didi">DiDi Food</span>
          <span class="rd-hero__badge rd-hero__badge--uber">Uber Eats</span>
          <span class="rd-hero__badge rd-hero__badge--own"><i class="fa-solid fa-store"></i> Flota propia</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Stats -->
  <div class="rd-stats">
    <div class="rd-stat rd-stat--live">
      <div class="rd-stat__value" id="rd-stat-encamino">—</div>
      <div class="rd-stat__label">En camino ahora</div>
      <div class="rd-stat__sub">pedidos activos</div>
    </div>
    <div class="rd-stat">
      <div class="rd-stat__value" id="rd-stat-hoy">—</div>
      <div class="rd-stat__label">Entregas hoy</div>
      <div class="rd-stat__sub" id="rd-stat-hoy-sub">completadas</div>
    </div>
    <div class="rd-stat">
      <div class="rd-stat__value" id="rd-stat-tiempo">—</div>
      <div class="rd-stat__label">Tiempo promedio</div>
      <div class="rd-stat__sub">minutos por entrega</div>
    </div>
    <div class="rd-stat">
      <div class="rd-stat__value" id="rd-stat-disponibles">—</div>
      <div class="rd-stat__label">Repartidores disponibles</div>
      <div class="rd-stat__sub" id="rd-stat-disponibles-sub">de flota propia</div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="rd-tabs">
    <button class="rd-tab is-active" data-tab="pedidos">Pedidos</button>
    <button class="rd-tab" data-tab="repartidores">Repartidores</button>
    <button class="rd-tab" data-tab="plataformas">Plataformas</button>
  </div>

  <!-- ─── Panel: Pedidos ────────────────────────────────────────────────── -->
  <div class="rd-tab-panel is-active" id="rd-panel-pedidos">

    <!-- Pipeline counters -->
    <div class="rd-pipeline" id="rd-pipeline">
      <div class="rd-pipeline__step is-active" data-filter="">
        <div class="rd-pipeline__count" id="rd-pipe-todos">0</div>
        <div class="rd-pipeline__label">Todos</div>
      </div>
      <div class="rd-pipeline__step" data-filter="pendiente">
        <div class="rd-pipeline__count" id="rd-pipe-pendiente">0</div>
        <div class="rd-pipeline__label">Pendientes</div>
      </div>
      <div class="rd-pipeline__step" data-filter="asignado">
        <div class="rd-pipeline__count" id="rd-pipe-asignado">0</div>
        <div class="rd-pipeline__label">Asignados</div>
      </div>
      <div class="rd-pipeline__step" data-filter="en_camino">
        <div class="rd-pipeline__count" id="rd-pipe-encamino">0</div>
        <div class="rd-pipeline__label">En camino</div>
      </div>
      <div class="rd-pipeline__step" data-filter="entregado">
        <div class="rd-pipeline__count" id="rd-pipe-entregado">0</div>
        <div class="rd-pipeline__label">Entregados</div>
      </div>
    </div>

    <div class="rd-toolbar">
      <input class="rd-search" type="search" id="rd-search-pedidos" placeholder="Buscar por folio, cliente…" />
      <select class="rd-filter" id="rd-filter-canal">
        <option value="">Canal: todos</option>
        <option value="didi">DiDi Food</option>
        <option value="uber">Uber Eats</option>
        <option value="rappi">Rappi</option>
        <option value="propio">Flota propia</option>
        <option value="otro">Otro</option>
      </select>
      <button class="rd-btn-add" id="rd-add-pedido-btn">
        <i class="fa-solid fa-plus"></i> Nuevo pedido
      </button>
    </div>

    <div class="rd-table-wrap">
      <table class="rd-table">
        <thead>
          <tr>
            <th>Folio</th>
            <th>Cliente</th>
            <th>Dirección</th>
            <th>Canal</th>
            <th>Repartidor</th>
            <th>Estado</th>
            <th>Tiempo</th>
            <th>ETA</th>
          </tr>
        </thead>
        <tbody id="rd-tbody-pedidos"></tbody>
      </table>
    </div>
  </div>

  <!-- ─── Panel: Repartidores ───────────────────────────────────────────── -->
  <div class="rd-tab-panel" id="rd-panel-repartidores">
    <div class="rd-toolbar">
      <input class="rd-search" type="search" id="rd-search-drivers" placeholder="Buscar repartidor…" />
      <select class="rd-filter" id="rd-filter-driver-estado">
        <option value="">Estado: todos</option>
        <option value="disponible">Disponible</option>
        <option value="en_entrega">En entrega</option>
        <option value="desconectado">Desconectado</option>
      </select>
      <button class="rd-btn-add" id="rd-add-driver-btn">
        <i class="fa-solid fa-plus"></i> Agregar repartidor
      </button>
    </div>
    <div class="rd-driver-grid" id="rd-driver-grid"></div>
  </div>

  <!-- ─── Panel: Plataformas ────────────────────────────────────────────── -->
  <div class="rd-tab-panel" id="rd-panel-plataformas">
    <p style="font-size:0.88rem;color:var(--rd-muted);margin:0 0 20px">
      Conecta tu tienda con plataformas de entrega externas. Los pedidos entrantes se sincronizarán automáticamente cuando la integración esté activa.
    </p>
    <div class="rd-plat-grid" id="rd-plat-grid"></div>
  </div>

</main>

<!-- ══════════════════════════════════════════════════════════════════════
     Drawer: Nuevo / Editar pedido
═══════════════════════════════════════════════════════════════════════ -->
<div class="rd-drawer-bg" id="rd-pedido-drawer-bg" role="dialog" aria-modal="true">
  <div class="rd-drawer">
    <h2 class="rd-drawer__title" id="rd-pedido-drawer-title">Nuevo pedido</h2>
    <p class="rd-drawer__subtitle" id="rd-pedido-drawer-sub">Registra los datos del pedido y asigna un repartidor</p>

    <p class="rd-section-title" style="margin-top:0;padding-top:0;border-top:none">Cliente y destino</p>
    <div class="rd-field--row">
      <div class="rd-field">
        <label>Nombre del cliente *</label>
        <input type="text" id="rd-pf-nombre" maxlength="120" placeholder="Nombre completo" />
      </div>
      <div class="rd-field">
        <label>Teléfono</label>
        <input type="tel" id="rd-pf-tel" maxlength="20" placeholder="10 dígitos" />
      </div>
    </div>
    <div class="rd-field">
      <label>Dirección de entrega *</label>
      <input type="text" id="rd-pf-direccion" maxlength="200" placeholder="Calle, número, colonia, ciudad" />
    </div>
    <div class="rd-field--row">
      <div class="rd-field">
        <label>Referencias</label>
        <input type="text" id="rd-pf-referencias" maxlength="120" placeholder="Entre qué calles, color de casa…" />
      </div>
      <div class="rd-field">
        <label>Distancia estimada (km)</label>
        <input type="number" id="rd-pf-distancia" min="0" step="0.1" placeholder="0.0" />
      </div>
    </div>

    <p class="rd-section-title">Pedido</p>
    <div class="rd-field">
      <label>Descripción del pedido *</label>
      <input type="text" id="rd-pf-descripcion" maxlength="200" placeholder="Ej. Hamburguesa + papas + refresco" />
    </div>
    <div class="rd-field--row3">
      <div class="rd-field">
        <label>Canal de origen *</label>
        <select id="rd-pf-canal">
          <option value="propio">Flota propia</option>
          <option value="didi">DiDi Food</option>
          <option value="uber">Uber Eats</option>
          <option value="rappi">Rappi</option>
          <option value="otro">Otro</option>
        </select>
      </div>
      <div class="rd-field">
        <label>Costo de entrega</label>
        <input type="number" id="rd-pf-costo" min="0" step="0.01" placeholder="0.00" />
      </div>
      <div class="rd-field">
        <label>ETA (minutos)</label>
        <input type="number" id="rd-pf-eta" min="0" step="1" placeholder="30" />
      </div>
    </div>

    <p class="rd-section-title">Asignación</p>
    <div class="rd-field--row">
      <div class="rd-field">
        <label>Repartidor asignado</label>
        <select id="rd-pf-repartidor">
          <option value="">— Sin asignar —</option>
        </select>
      </div>
      <div class="rd-field">
        <label>Estado inicial</label>
        <select id="rd-pf-estado">
          <option value="pendiente">Pendiente</option>
          <option value="asignado">Asignado</option>
          <option value="en_camino">En camino</option>
        </select>
      </div>
    </div>
    <div class="rd-field">
      <label>Notas internas</label>
      <textarea id="rd-pf-notas" rows="2" placeholder="Instrucciones especiales para el repartidor…"></textarea>
    </div>

    <div class="rd-drawer__footer">
      <button class="rd-btn rd-btn--danger"    id="rd-pedido-delete-btn" style="display:none">Eliminar</button>
      <button class="rd-btn rd-btn--secondary" id="rd-pedido-cancel-btn">Cancelar</button>
      <button class="rd-btn rd-btn--primary"   id="rd-pedido-save-btn">Guardar pedido</button>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════════════
     Drawer: Detalle de pedido
═══════════════════════════════════════════════════════════════════════ -->
<div class="rd-drawer-bg" id="rd-detail-drawer-bg" role="dialog" aria-modal="true">
  <div class="rd-drawer">
    <h2 class="rd-drawer__title" id="rd-detail-title">Pedido</h2>
    <p class="rd-drawer__subtitle" id="rd-detail-subtitle"></p>

    <!-- Status pipeline -->
    <div class="rd-status-pipeline" id="rd-detail-pipeline">
      <div class="rd-status-step" data-step="pendiente">
        <i class="fa-solid fa-clock"></i>Pendiente
      </div>
      <div class="rd-status-step" data-step="asignado">
        <i class="fa-solid fa-user-check"></i>Asignado
      </div>
      <div class="rd-status-step" data-step="en_camino">
        <i class="fa-solid fa-motorcycle"></i>En camino
      </div>
      <div class="rd-status-step" data-step="entregado">
        <i class="fa-solid fa-circle-check"></i>Entregado
      </div>
    </div>

    <!-- Map placeholder -->
    <div class="rd-map-placeholder" id="rd-map-placeholder">
      <i class="fa-solid fa-map-location-dot"></i>
      <p id="rd-detail-direccion-lbl">Ver en mapa</p>
    </div>

    <div class="rd-field--row">
      <div>
        <div style="font-size:.75rem;font-weight:700;color:var(--rd-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">Cliente</div>
        <div style="font-weight:700" id="rd-detail-cliente">—</div>
        <div style="font-size:.78rem;color:var(--rd-muted)" id="rd-detail-tel">—</div>
      </div>
      <div>
        <div style="font-size:.75rem;font-weight:700;color:var(--rd-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">Repartidor</div>
        <div style="font-weight:700" id="rd-detail-repartidor">Sin asignar</div>
        <div style="font-size:.78rem;color:var(--rd-muted)" id="rd-detail-canal-lbl">—</div>
      </div>
    </div>

    <p class="rd-section-title">Asignar / cambiar repartidor</p>
    <div class="rd-field--row">
      <div class="rd-field">
        <label>Repartidor</label>
        <select id="rd-detail-assign-select"></select>
      </div>
      <div class="rd-field">
        <label>Nuevo estado</label>
        <select id="rd-detail-estado-select">
          <option value="pendiente">Pendiente</option>
          <option value="asignado">Asignado</option>
          <option value="en_camino">En camino</option>
          <option value="entregado">Entregado</option>
          <option value="cancelado">Cancelado</option>
          <option value="fallido">Fallido</option>
        </select>
      </div>
    </div>
    <div class="rd-field">
      <label>Nota de actualización</label>
      <input type="text" id="rd-detail-nota" maxlength="120" placeholder="Ej. Repartidor salió a las 13:45…" />
    </div>

    <div class="rd-drawer__footer">
      <button class="rd-btn rd-btn--secondary" id="rd-detail-edit-btn"><i class="fa-solid fa-pen" style="margin-right:4px"></i>Editar</button>
      <button class="rd-btn rd-btn--warn"      id="rd-detail-cancelar-btn">Cancelar pedido</button>
      <button class="rd-btn rd-btn--primary"   id="rd-detail-update-btn">Actualizar estado</button>
      <button class="rd-btn rd-btn--secondary" id="rd-detail-close-btn">Cerrar</button>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════════════
     Drawer: Nuevo / Editar repartidor
═══════════════════════════════════════════════════════════════════════ -->
<div class="rd-drawer-bg" id="rd-driver-drawer-bg" role="dialog" aria-modal="true">
  <div class="rd-drawer">
    <h2 class="rd-drawer__title" id="rd-driver-drawer-title">Agregar repartidor</h2>
    <p class="rd-drawer__subtitle">Repartidor de flota propia de la tienda</p>

    <div class="rd-field--row">
      <div class="rd-field">
        <label>Nombre completo *</label>
        <input type="text" id="rd-df-nombre" maxlength="120" placeholder="Nombre del repartidor" />
      </div>
      <div class="rd-field">
        <label>Teléfono *</label>
        <input type="tel" id="rd-df-tel" maxlength="20" placeholder="10 dígitos" />
      </div>
    </div>
    <div class="rd-field--row">
      <div class="rd-field">
        <label>Tipo de vehículo</label>
        <select id="rd-df-vehiculo">
          <option value="moto">Motocicleta</option>
          <option value="bici">Bicicleta</option>
          <option value="carro">Automóvil</option>
          <option value="pie">A pie</option>
          <option value="otro">Otro</option>
        </select>
      </div>
      <div class="rd-field">
        <label>Plataforma principal</label>
        <select id="rd-df-plataforma">
          <option value="propio">Flota propia</option>
          <option value="didi">DiDi Food</option>
          <option value="uber">Uber Eats</option>
          <option value="rappi">Rappi</option>
        </select>
      </div>
    </div>
    <div class="rd-field--row">
      <div class="rd-field">
        <label>Estado</label>
        <select id="rd-df-estado">
          <option value="disponible">Disponible</option>
          <option value="desconectado">Desconectado</option>
        </select>
      </div>
      <div class="rd-field">
        <label>Zona de cobertura</label>
        <input type="text" id="rd-df-zona" maxlength="80" placeholder="Ej. Centro, Norte" />
      </div>
    </div>
    <div class="rd-field">
      <label>Notas</label>
      <textarea id="rd-df-notas" rows="2" placeholder="Horario, observaciones…"></textarea>
    </div>

    <div class="rd-drawer__footer">
      <button class="rd-btn rd-btn--danger"    id="rd-driver-delete-btn" style="display:none">Eliminar</button>
      <button class="rd-btn rd-btn--secondary" id="rd-driver-cancel-btn">Cancelar</button>
      <button class="rd-btn rd-btn--primary"   id="rd-driver-save-btn">Guardar</button>
    </div>
  </div>
</div>

<script>
(function () {
  var LS_PEDIDOS   = 'multitienda_rd_pedidos';
  var LS_DRIVERS   = 'multitienda_rd_drivers';
  var LS_PLATFORMS = 'multitienda_rd_platforms';

  // ── Storage ──────────────────────────────────────────────────────────────
  function loadPedidos()   { try { return JSON.parse(localStorage.getItem(LS_PEDIDOS)   || '[]'); } catch { return []; } }
  function loadDrivers()   { try { return JSON.parse(localStorage.getItem(LS_DRIVERS)   || '[]'); } catch { return []; } }
  function loadPlatforms() { try { return JSON.parse(localStorage.getItem(LS_PLATFORMS) || '{}'); } catch { return {}; } }
  function savePedidos(d)   { localStorage.setItem(LS_PEDIDOS,   JSON.stringify(d)); }
  function saveDrivers(d)   { localStorage.setItem(LS_DRIVERS,   JSON.stringify(d)); }
  function savePlatforms(d) { localStorage.setItem(LS_PLATFORMS, JSON.stringify(d)); }

  // ── Helpers ──────────────────────────────────────────────────────────────
  function fmt(n) { return '$' + parseFloat(n||0).toLocaleString('es-MX', { minimumFractionDigits:2, maximumFractionDigits:2 }); }
  function escHtml(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function nowISO()  { return new Date().toISOString(); }
  function todayStr(){ return new Date().toISOString().slice(0,10); }
  function minsSince(iso) { if (!iso) return null; return Math.floor((Date.now() - new Date(iso)) / 60000); }
  function genFolio(list) { return 'ENT-' + new Date().getFullYear() + '-' + String(list.length + 1).padStart(4,'0'); }

  var PLAT_LABEL = { didi:'DiDi Food', uber:'Uber Eats', rappi:'Rappi', propio:'Propio', otro:'Otro' };
  var PLAT_KEY   = { didi:'rd-platform--didi', uber:'rd-platform--uber', rappi:'rd-platform--rappi', propio:'rd-platform--propio', otro:'rd-platform--otro' };
  var VEH_ICON   = { moto:'fa-motorcycle', bici:'fa-bicycle', carro:'fa-car', pie:'fa-person-walking', otro:'fa-truck' };

  var ESTADO_ORDER = ['pendiente','asignado','en_camino','entregado','cancelado','fallido'];
  var ESTADO_LABEL = { pendiente:'Pendiente', asignado:'Asignado', en_camino:'En camino', entregado:'Entregado', cancelado:'Cancelado', fallido:'Fallido' };
  var BADGE_CSS    = { pendiente:'rd-badge--pendiente', asignado:'rd-badge--asignado', en_camino:'rd-badge--en_camino', entregado:'rd-badge--entregado', cancelado:'rd-badge--cancelado', fallido:'rd-badge--fallido' };
  var DRIVER_BADGE = { disponible:'rd-badge--disponible', en_entrega:'rd-badge--en_entrega', desconectado:'rd-badge--desconectado' };
  var DRIVER_LABEL = { disponible:'Disponible', en_entrega:'En entrega', desconectado:'Desconectado' };

  function badge(estado, cssMap, labelMap) {
    return '<span class="rd-badge ' + (cssMap[estado]||'') + '">' + (labelMap[estado]||estado) + '</span>';
  }
  function platChip(canal) {
    return '<span class="rd-platform ' + (PLAT_KEY[canal]||'rd-platform--otro') + '">' + escHtml(PLAT_LABEL[canal]||canal) + '</span>';
  }
  function setText(id, v) { var el = document.getElementById(id); if (el) el.textContent = v; }

  // ── Elapsed display ───────────────────────────────────────────────────────
  function elapsedStr(iso) {
    var m = minsSince(iso);
    if (m === null) return '—';
    if (m < 60) return m + ' min';
    return Math.floor(m/60) + 'h ' + (m%60) + 'min';
  }
  function elapsedCls(m, eta) {
    if (m === null) return '';
    if (eta && m > eta) return 'rd-elapsed--late';
    if (eta && m > eta * 0.8) return 'rd-elapsed--warn';
    return 'rd-elapsed--ok';
  }

  // ── Stats ─────────────────────────────────────────────────────────────────
  function refreshStats() {
    var pedidos  = loadPedidos();
    var drivers  = loadDrivers();
    var hoy      = todayStr();
    var enCamino = pedidos.filter(function(p){ return p.estado === 'en_camino'; });
    var entregados= pedidos.filter(function(p){ return p.estado === 'entregado' && (p.creadoEn||'').startsWith(hoy); });
    var disponibles = drivers.filter(function(d){ return d.estado === 'disponible'; });

    // Average delivery time
    var withTime = pedidos.filter(function(p){ return p.estado === 'entregado' && p.entregadoEn && p.creadoEn; });
    var avgMins  = withTime.length
      ? Math.round(withTime.reduce(function(s,p){ return s + Math.floor((new Date(p.entregadoEn) - new Date(p.creadoEn)) / 60000); }, 0) / withTime.length)
      : null;

    setText('rd-stat-encamino',   enCamino.length);
    setText('rd-stat-hoy',        entregados.length);
    setText('rd-stat-hoy-sub',    entregados.length === 1 ? 'completada hoy' : 'completadas hoy');
    setText('rd-stat-tiempo',     avgMins !== null ? avgMins + ' min' : '—');
    setText('rd-stat-disponibles',disponibles.length);
    setText('rd-stat-disponibles-sub', drivers.length + ' en flota propia');
  }

  // ── Pipeline counters ─────────────────────────────────────────────────────
  var _activeFilter = '';
  function refreshPipeline() {
    var pedidos = loadPedidos();
    var counts  = { '': pedidos.length };
    ESTADO_ORDER.forEach(function(e){ counts[e] = pedidos.filter(function(p){ return p.estado === e; }).length; });
    setText('rd-pipe-todos',      pedidos.length);
    setText('rd-pipe-pendiente',  counts['pendiente']||0);
    setText('rd-pipe-asignado',   counts['asignado']||0);
    setText('rd-pipe-encamino',   counts['en_camino']||0);
    setText('rd-pipe-entregado',  counts['entregado']||0);
  }

  document.getElementById('rd-pipeline').addEventListener('click', function(e){
    var step = e.target.closest('.rd-pipeline__step');
    if (!step) return;
    _activeFilter = step.dataset.filter;
    document.querySelectorAll('.rd-pipeline__step').forEach(function(s){ s.classList.remove('is-active'); });
    step.classList.add('is-active');
    renderPedidos();
  });

  // ── Render pedidos ────────────────────────────────────────────────────────
  function renderPedidos() {
    var pedidos = loadPedidos();
    var search  = ((document.getElementById('rd-search-pedidos')||{}).value||'').toLowerCase();
    var fCanal  = ((document.getElementById('rd-filter-canal')||{}).value||'');
    var filtered= pedidos.filter(function(p){
      if (_activeFilter && p.estado !== _activeFilter) return false;
      if (fCanal  && p.canal  !== fCanal)  return false;
      if (search  && !(p.folio + ' ' + p.clienteNombre + ' ' + p.descripcion).toLowerCase().includes(search)) return false;
      return true;
    });
    var tbody = document.getElementById('rd-tbody-pedidos');
    if (!filtered.length) {
      tbody.innerHTML = '<tr class="rd-table__empty"><td colspan="8"><i class="fa-solid fa-motorcycle" style="font-size:1.8rem;display:block;margin-bottom:10px;opacity:.3"></i>Sin pedidos en esta vista.</td></tr>';
      return;
    }
    tbody.innerHTML = filtered.map(function(p){
      var m = minsSince(p.creadoEn);
      var cls = elapsedCls(m, p.eta ? parseInt(p.eta) : null);
      var elapsed = '<span class="rd-elapsed ' + cls + '">' + elapsedStr(p.creadoEn) + '</span>';
      return '<tr data-id="' + p.id + '" data-drawer="detail">'
        + '<td><code style="font-size:.82rem">' + escHtml(p.folio) + '</code></td>'
        + '<td><div style="font-weight:700">' + escHtml(p.clienteNombre) + '</div>'
        + '<div style="font-size:.75rem;color:var(--rd-muted)">' + escHtml(p.clienteTel||'') + '</div></td>'
        + '<td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + escHtml(p.direccion) + '</td>'
        + '<td>' + platChip(p.canal) + '</td>'
        + '<td>' + escHtml(p.repartidorNombre || '—') + '</td>'
        + '<td>' + badge(p.estado, BADGE_CSS, ESTADO_LABEL) + '</td>'
        + '<td>' + elapsed + '</td>'
        + '<td style="font-size:.82rem;color:var(--rd-muted)">' + (p.eta ? p.eta + ' min' : '—') + '</td>'
        + '</tr>';
    }).join('');
  }

  // ── Render drivers ────────────────────────────────────────────────────────
  function renderDrivers() {
    var drivers = loadDrivers();
    var search  = ((document.getElementById('rd-search-drivers')||{}).value||'').toLowerCase();
    var fEst    = ((document.getElementById('rd-filter-driver-estado')||{}).value||'');
    var filtered= drivers.filter(function(d){
      if (fEst   && d.estado !== fEst) return false;
      if (search && !(d.nombre + ' ' + d.telefono).toLowerCase().includes(search)) return false;
      return true;
    });
    var grid = document.getElementById('rd-driver-grid');
    var pedidos = loadPedidos();
    var html = filtered.map(function(d){
      var entregasHoy = pedidos.filter(function(p){ return p.repartidorId === d.id && (p.creadoEn||'').startsWith(todayStr()); }).length;
      var initials    = d.nombre.split(' ').slice(0,2).map(function(w){ return w[0]||''; }).join('').toUpperCase();
      var vehIcon     = VEH_ICON[d.vehiculo] || 'fa-truck';
      var isDisp      = d.estado === 'disponible';
      return '<div class="rd-driver-card' + (isDisp ? ' rd-driver-card--disponible' : '') + '" data-id="' + d.id + '" data-drawer="driver">'
        + '<div class="rd-driver-card__header">'
        + '<div class="rd-driver-card__avatar">' + escHtml(initials) + '</div>'
        + '<div class="rd-driver-card__info">'
        + '<p class="rd-driver-card__name">' + escHtml(d.nombre) + '</p>'
        + '<p class="rd-driver-card__tel">' + escHtml(d.telefono) + '</p>'
        + '</div>'
        + '</div>'
        + '<div class="rd-driver-card__meta">'
        + '<span class="rd-driver-card__vehicle"><i class="fa-solid ' + vehIcon + '"></i>' + escHtml((d.vehiculo||'').charAt(0).toUpperCase() + (d.vehiculo||'').slice(1)) + '</span>'
        + badge(d.estado, DRIVER_BADGE, DRIVER_LABEL)
        + '</div>'
        + '<div style="display:flex;align-items:center;justify-content:space-between">'
        + platChip(d.plataforma || 'propio')
        + '<span class="rd-driver-card__count"><i class="fa-solid fa-route" style="margin-right:4px"></i>' + entregasHoy + ' hoy</span>'
        + '</div>'
        + (d.zona ? '<div style="font-size:.75rem;color:var(--rd-muted)"><i class="fa-solid fa-map-pin" style="margin-right:4px"></i>' + escHtml(d.zona) + '</div>' : '')
        + '</div>';
    }).join('');
    // Add card
    html += '<div class="rd-driver-card rd-driver-card__add" id="rd-add-driver-card">'
           + '<i class="fa-solid fa-plus" style="font-size:1.4rem;color:var(--rd-muted)"></i>'
           + '<div style="font-weight:700;font-size:.9rem;color:var(--rd-muted);margin-top:8px">Agregar repartidor</div>'
           + '</div>';
    grid.innerHTML = html;
  }

  // ── Render platforms ──────────────────────────────────────────────────────
  var PLATFORMS_DEF = [
    { key:'didi',  name:'DiDi Food',  desc:'Integra con la plataforma de DiDi Food para recibir y gestionar pedidos automáticamente.', fields:['Merchant ID','API Key','Webhook Secret'] },
    { key:'uber',  name:'Uber Eats',  desc:'Conecta tu tienda con Uber Eats para sincronizar menús, pedidos y estado de entregas.', fields:['Store UUID','API Token','Secret Key'] },
    { key:'rappi', name:'Rappi',      desc:'Vincula tu cuenta de Rappi para recibir pedidos y actualizar disponibilidad en tiempo real.', fields:['Partner ID','API Key','Client Secret'] },
    { key:'propio',name:'Flota propia',desc:'Gestiona tu propio equipo de repartidores sin depender de plataformas externas.', fields:[] },
  ];

  function renderPlatforms() {
    var cfg  = loadPlatforms();
    var grid = document.getElementById('rd-plat-grid');
    grid.innerHTML = PLATFORMS_DEF.map(function(p){
      var pcfg    = cfg[p.key] || {};
      var isOn    = pcfg.connected;
      var hasCfg  = p.fields.length > 0 && p.fields.some(function(f){ return !!pcfg[f]; });
      var dotCls  = isOn ? 'rd-plat-card__dot--on' : (hasCfg ? 'rd-plat-card__dot--cfg' : '');
      var stLabel = isOn ? 'Conectado' : (hasCfg ? 'Credenciales guardadas' : 'Sin configurar');
      var stCls   = isOn ? 'rd-plat-card__status-label--on' : (hasCfg ? 'rd-plat-card__status-label--cfg' : 'rd-plat-card__status-label--off');
      var logoLetter = p.name.charAt(0);
      var fieldsHtml = p.fields.map(function(f){
        return '<div>'
          + '<div class="rd-plat-card__field-label">' + escHtml(f) + '</div>'
          + '<input class="rd-plat-card__input" type="password" placeholder="••••••••••" '
          + 'data-plat="' + p.key + '" data-field="' + escHtml(f) + '" '
          + 'value="' + escHtml(pcfg[f]||'') + '" autocomplete="off" />'
          + '</div>';
      }).join('');
      return '<div class="rd-plat-card">'
        + '<div class="rd-plat-card__header">'
        + '<div class="rd-plat-card__logo rd-plat-card__logo--' + p.key + '">' + logoLetter + '</div>'
        + '<div><div class="rd-plat-card__name">' + escHtml(p.name) + '</div>'
        + '<div class="rd-plat-card__desc">' + escHtml(p.desc) + '</div></div>'
        + '</div>'
        + '<div class="rd-plat-card__status">'
        + '<div class="rd-plat-card__dot ' + dotCls + '"></div>'
        + '<span class="rd-plat-card__status-label ' + stCls + '">' + stLabel + '</span>'
        + '</div>'
        + (p.fields.length ? '<div class="rd-plat-card__fields">' + fieldsHtml + '</div>' : '<div style="font-size:.82rem;color:var(--rd-muted)">Administra tu flota propia desde la pestaña Repartidores.</div>')
        + '<div class="rd-plat-card__actions">'
        + (p.fields.length ? '<button class="rd-plat-btn rd-plat-btn--test" data-plat-test="' + p.key + '">Probar conexión</button>' : '')
        + (isOn
            ? '<button class="rd-plat-btn rd-plat-btn--disconnect" data-plat-disconnect="' + p.key + '">Desconectar</button>'
            : (p.fields.length ? '<button class="rd-plat-btn rd-plat-btn--connect" data-plat-connect="' + p.key + '">Guardar y conectar</button>' : ''))
        + '</div>'
        + '</div>';
    }).join('');
  }

  // Platform actions
  document.getElementById('rd-plat-grid').addEventListener('click', function(e){
    var btn = e.target.closest('[data-plat-connect],[data-plat-disconnect],[data-plat-test]');
    if (!btn) return;
    var key  = btn.dataset.platConnect || btn.dataset.platDisconnect || btn.dataset.platTest;
    var cfg  = loadPlatforms();
    cfg[key] = cfg[key] || {};
    if (btn.dataset.platConnect) {
      // Read fields
      document.querySelectorAll('[data-plat="' + key + '"]').forEach(function(inp){
        cfg[key][inp.dataset.field] = inp.value;
      });
      cfg[key].connected = true;
      btn.textContent = '¡Guardado!';
      setTimeout(function(){ savePlatforms(cfg); renderPlatforms(); }, 800);
    } else if (btn.dataset.platDisconnect) {
      cfg[key].connected = false;
      savePlatforms(cfg); renderPlatforms();
    } else if (btn.dataset.platTest) {
      btn.textContent = 'Probando…';
      setTimeout(function(){
        btn.textContent = '✓ Conexión OK';
        setTimeout(function(){ btn.textContent = 'Probar conexión'; }, 2000);
      }, 1200);
    }
  });

  // ── Populate driver selects ───────────────────────────────────────────────
  function populateDriverSelect(selectId) {
    var sel     = document.getElementById(selectId);
    if (!sel) return;
    var drivers = loadDrivers().filter(function(d){ return d.estado !== 'desconectado'; });
    var cur     = sel.value;
    sel.innerHTML = '<option value="">— Sin asignar —</option>'
      + drivers.map(function(d){ return '<option value="' + d.id + '"' + (cur === d.id ? ' selected' : '') + '>' + escHtml(d.nombre) + ' (' + (PLAT_LABEL[d.plataforma]||'Propio') + ')</option>'; }).join('');
  }

  // ────────────────────────────────────────────────────────────────────────
  // PEDIDO DRAWER
  // ────────────────────────────────────────────────────────────────────────
  var pedidoDrawerBg  = document.getElementById('rd-pedido-drawer-bg');
  var pedidoEditingId = null;

  function openPedidoDrawer(id) {
    pedidoEditingId = id;
    var list = loadPedidos();
    var item = id ? list.find(function(p){ return p.id === id; }) : null;
    document.getElementById('rd-pedido-drawer-title').textContent = id ? 'Editar pedido' : 'Nuevo pedido';
    document.getElementById('rd-pf-nombre').value      = item ? item.clienteNombre  : '';
    document.getElementById('rd-pf-tel').value         = item ? item.clienteTel     : '';
    document.getElementById('rd-pf-direccion').value   = item ? item.direccion      : '';
    document.getElementById('rd-pf-referencias').value = item ? (item.referencias||'') : '';
    document.getElementById('rd-pf-distancia').value   = item ? (item.distancia||'') : '';
    document.getElementById('rd-pf-descripcion').value = item ? item.descripcion    : '';
    document.getElementById('rd-pf-canal').value       = item ? item.canal          : 'propio';
    document.getElementById('rd-pf-costo').value       = item ? (item.costo||'')   : '';
    document.getElementById('rd-pf-eta').value         = item ? (item.eta||'')     : '30';
    document.getElementById('rd-pf-estado').value      = item ? item.estado        : 'pendiente';
    document.getElementById('rd-pf-notas').value       = item ? (item.notas||'')   : '';
    populateDriverSelect('rd-pf-repartidor');
    if (item && item.repartidorId) document.getElementById('rd-pf-repartidor').value = item.repartidorId;
    document.getElementById('rd-pedido-delete-btn').style.display = id ? 'inline-flex' : 'none';
    pedidoDrawerBg.classList.add('is-open');
    document.getElementById('rd-pf-nombre').focus();
  }
  function closePedidoDrawer() { pedidoDrawerBg.classList.remove('is-open'); pedidoEditingId = null; }

  document.getElementById('rd-add-pedido-btn').addEventListener('click', function(){ openPedidoDrawer(null); });
  document.getElementById('rd-pedido-cancel-btn').addEventListener('click', closePedidoDrawer);
  pedidoDrawerBg.addEventListener('click', function(e){ if (e.target === pedidoDrawerBg) closePedidoDrawer(); });

  document.getElementById('rd-pedido-save-btn').addEventListener('click', function(){
    var nombre    = document.getElementById('rd-pf-nombre').value.trim();
    var direccion = document.getElementById('rd-pf-direccion').value.trim();
    var descripcion = document.getElementById('rd-pf-descripcion').value.trim();
    if (!nombre)    { document.getElementById('rd-pf-nombre').focus();    return; }
    if (!direccion) { document.getElementById('rd-pf-direccion').focus(); return; }
    var list = loadPedidos();
    var drivers = loadDrivers();
    var repId   = document.getElementById('rd-pf-repartidor').value;
    var repObj  = repId ? drivers.find(function(d){ return d.id === repId; }) : null;
    var item = {
      id:              pedidoEditingId || ('pd-' + Date.now()),
      folio:           pedidoEditingId ? (list.find(function(p){ return p.id === pedidoEditingId; })||{}).folio : genFolio(list),
      clienteNombre:   nombre,
      clienteTel:      document.getElementById('rd-pf-tel').value.trim(),
      direccion,
      referencias:     document.getElementById('rd-pf-referencias').value.trim(),
      distancia:       document.getElementById('rd-pf-distancia').value,
      descripcion,
      canal:           document.getElementById('rd-pf-canal').value,
      costo:           parseFloat(document.getElementById('rd-pf-costo').value || 0),
      eta:             parseInt(document.getElementById('rd-pf-eta').value || 0),
      repartidorId:    repId,
      repartidorNombre:repObj ? repObj.nombre : '',
      estado:          document.getElementById('rd-pf-estado').value,
      notas:           document.getElementById('rd-pf-notas').value.trim(),
      creadoEn:        pedidoEditingId ? (list.find(function(p){ return p.id === pedidoEditingId; })||{}).creadoEn : nowISO(),
    };
    if (pedidoEditingId) {
      var idx = list.findIndex(function(p){ return p.id === pedidoEditingId; });
      if (idx >= 0) list[idx] = item;
    } else {
      list.push(item);
    }
    savePedidos(list);
    renderAll();
    closePedidoDrawer();
  });

  document.getElementById('rd-pedido-delete-btn').addEventListener('click', function(){
    if (!pedidoEditingId || !confirm('¿Eliminar este pedido?')) return;
    savePedidos(loadPedidos().filter(function(p){ return p.id !== pedidoEditingId; }));
    renderAll();
    closePedidoDrawer();
  });

  // ────────────────────────────────────────────────────────────────────────
  // DETAIL DRAWER
  // ────────────────────────────────────────────────────────────────────────
  var detailDrawerBg = document.getElementById('rd-detail-drawer-bg');
  var detailId = null;

  function openDetailDrawer(id) {
    detailId = id;
    renderDetailDrawer(id);
    detailDrawerBg.classList.add('is-open');
  }

  function renderDetailDrawer(id) {
    var list = loadPedidos();
    var p    = list.find(function(x){ return x.id === id; });
    if (!p) return;
    document.getElementById('rd-detail-title').textContent    = p.folio;
    document.getElementById('rd-detail-subtitle').textContent = p.descripcion;
    document.getElementById('rd-detail-cliente').textContent  = p.clienteNombre;
    document.getElementById('rd-detail-tel').textContent      = p.clienteTel || '—';
    document.getElementById('rd-detail-repartidor').textContent = p.repartidorNombre || 'Sin asignar';
    document.getElementById('rd-detail-canal-lbl').textContent  = PLAT_LABEL[p.canal] || p.canal;
    document.getElementById('rd-detail-direccion-lbl').textContent = p.direccion;

    // Pipeline steps
    var steps = ['pendiente','asignado','en_camino','entregado'];
    var curIdx = steps.indexOf(p.estado);
    document.querySelectorAll('#rd-detail-pipeline .rd-status-step').forEach(function(el, i){
      el.classList.remove('is-done','is-current');
      if (i < curIdx) el.classList.add('is-done');
      else if (i === curIdx) el.classList.add('is-current');
    });

    // Assign select
    populateDriverSelect('rd-detail-assign-select');
    if (p.repartidorId) document.getElementById('rd-detail-assign-select').value = p.repartidorId;
    document.getElementById('rd-detail-estado-select').value = p.estado;
    document.getElementById('rd-detail-nota').value = '';

    var isClosed = p.estado === 'entregado' || p.estado === 'cancelado' || p.estado === 'fallido';
    document.getElementById('rd-detail-cancelar-btn').style.display = !isClosed ? 'inline-flex' : 'none';
    document.getElementById('rd-detail-update-btn').style.display   = !isClosed ? 'inline-flex' : 'none';
  }

  // Open map placeholder
  document.getElementById('rd-map-placeholder').addEventListener('click', function(){
    var list = loadPedidos();
    var p    = list.find(function(x){ return x.id === detailId; });
    if (!p) return;
    var q = encodeURIComponent(p.direccion);
    window.open('https://www.google.com/maps/search/?api=1&query=' + q, '_blank');
  });

  document.getElementById('rd-detail-update-btn').addEventListener('click', function(){
    var list = loadPedidos();
    var p    = list.find(function(x){ return x.id === detailId; });
    if (!p) return;
    var newEstado = document.getElementById('rd-detail-estado-select').value;
    var repId     = document.getElementById('rd-detail-assign-select').value;
    var drivers   = loadDrivers();
    var repObj    = repId ? drivers.find(function(d){ return d.id === repId; }) : null;
    p.estado           = newEstado;
    p.repartidorId     = repId;
    p.repartidorNombre = repObj ? repObj.nombre : '';
    if (newEstado === 'entregado') p.entregadoEn = nowISO();
    savePedidos(list);
    // Update driver status
    if (repObj) {
      var drList = loadDrivers();
      var dr     = drList.find(function(d){ return d.id === repId; });
      if (dr) {
        dr.estado = newEstado === 'en_camino' ? 'en_entrega' : (newEstado === 'entregado' ? 'disponible' : dr.estado);
        saveDrivers(drList);
      }
    }
    renderDetailDrawer(detailId);
    renderAll();
  });

  document.getElementById('rd-detail-cancelar-btn').addEventListener('click', function(){
    if (!confirm('¿Cancelar este pedido?')) return;
    var list = loadPedidos();
    var p    = list.find(function(x){ return x.id === detailId; });
    if (p) { p.estado = 'cancelado'; savePedidos(list); renderDetailDrawer(detailId); renderAll(); }
  });
  document.getElementById('rd-detail-edit-btn').addEventListener('click', function(){
    closeDetailDrawer(); openPedidoDrawer(detailId);
  });
  function closeDetailDrawer() { detailDrawerBg.classList.remove('is-open'); detailId = null; }
  document.getElementById('rd-detail-close-btn').addEventListener('click', closeDetailDrawer);
  detailDrawerBg.addEventListener('click', function(e){ if (e.target === detailDrawerBg) closeDetailDrawer(); });

  // ────────────────────────────────────────────────────────────────────────
  // DRIVER DRAWER
  // ────────────────────────────────────────────────────────────────────────
  var driverDrawerBg  = document.getElementById('rd-driver-drawer-bg');
  var driverEditingId = null;

  function openDriverDrawer(id) {
    driverEditingId = id;
    var list = loadDrivers();
    var item = id ? list.find(function(d){ return d.id === id; }) : null;
    document.getElementById('rd-driver-drawer-title').textContent = id ? 'Editar repartidor' : 'Agregar repartidor';
    document.getElementById('rd-df-nombre').value     = item ? item.nombre    : '';
    document.getElementById('rd-df-tel').value        = item ? item.telefono  : '';
    document.getElementById('rd-df-vehiculo').value   = item ? (item.vehiculo||'moto')  : 'moto';
    document.getElementById('rd-df-plataforma').value = item ? (item.plataforma||'propio') : 'propio';
    document.getElementById('rd-df-estado').value     = item ? item.estado    : 'disponible';
    document.getElementById('rd-df-zona').value       = item ? (item.zona||'') : '';
    document.getElementById('rd-df-notas').value      = item ? (item.notas||'') : '';
    document.getElementById('rd-driver-delete-btn').style.display = id ? 'inline-flex' : 'none';
    driverDrawerBg.classList.add('is-open');
    document.getElementById('rd-df-nombre').focus();
  }
  function closeDriverDrawer() { driverDrawerBg.classList.remove('is-open'); driverEditingId = null; }

  document.getElementById('rd-add-driver-btn').addEventListener('click', function(){ openDriverDrawer(null); });
  document.getElementById('rd-driver-cancel-btn').addEventListener('click', closeDriverDrawer);
  driverDrawerBg.addEventListener('click', function(e){ if (e.target === driverDrawerBg) closeDriverDrawer(); });

  document.getElementById('rd-driver-grid').addEventListener('click', function(e){
    if (e.target.closest('#rd-add-driver-card') || e.target.closest('#rd-add-driver-btn')) { openDriverDrawer(null); return; }
    var card = e.target.closest('[data-id][data-drawer="driver"]');
    if (card) openDriverDrawer(card.dataset.id);
  });

  document.getElementById('rd-driver-save-btn').addEventListener('click', function(){
    var nombre = document.getElementById('rd-df-nombre').value.trim();
    var tel    = document.getElementById('rd-df-tel').value.trim();
    if (!nombre) { document.getElementById('rd-df-nombre').focus(); return; }
    var list = loadDrivers();
    var item = {
      id:         driverEditingId || ('dr-' + Date.now()),
      nombre,
      telefono:   tel,
      vehiculo:   document.getElementById('rd-df-vehiculo').value,
      plataforma: document.getElementById('rd-df-plataforma').value,
      estado:     document.getElementById('rd-df-estado').value,
      zona:       document.getElementById('rd-df-zona').value.trim(),
      notas:      document.getElementById('rd-df-notas').value.trim(),
    };
    if (driverEditingId) {
      var idx = list.findIndex(function(d){ return d.id === driverEditingId; });
      if (idx >= 0) list[idx] = item;
    } else {
      list.push(item);
    }
    saveDrivers(list);
    renderAll();
    closeDriverDrawer();
  });

  document.getElementById('rd-driver-delete-btn').addEventListener('click', function(){
    if (!driverEditingId || !confirm('¿Eliminar este repartidor?')) return;
    saveDrivers(loadDrivers().filter(function(d){ return d.id !== driverEditingId; }));
    renderAll();
    closeDriverDrawer();
  });

  // ── Row clicks ────────────────────────────────────────────────────────────
  document.addEventListener('click', function(e){
    var tr = e.target.closest('tr[data-id][data-drawer="detail"]');
    if (tr) { openDetailDrawer(tr.dataset.id); return; }
  });

  // ── Filters ───────────────────────────────────────────────────────────────
  document.getElementById('rd-search-pedidos').addEventListener('input', renderPedidos);
  document.getElementById('rd-filter-canal').addEventListener('change', renderPedidos);
  document.getElementById('rd-search-drivers').addEventListener('input', renderDrivers);
  document.getElementById('rd-filter-driver-estado').addEventListener('change', renderDrivers);

  // ── Tabs ──────────────────────────────────────────────────────────────────
  document.querySelectorAll('.rd-tab').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.rd-tab').forEach(function(b){ b.classList.remove('is-active'); });
      document.querySelectorAll('.rd-tab-panel').forEach(function(p){ p.classList.remove('is-active'); });
      btn.classList.add('is-active');
      var panel = document.getElementById('rd-panel-' + btn.dataset.tab);
      if (panel) panel.classList.add('is-active');
    });
  });

  // ── Live elapsed refresh (every 60 s) ─────────────────────────────────────
  setInterval(function(){ renderPedidos(); refreshStats(); }, 60000);

  // ── Init ──────────────────────────────────────────────────────────────────
  function renderAll() {
    renderPedidos();
    renderDrivers();
    renderPlatforms();
    refreshStats();
    refreshPipeline();
  }
  renderAll();
})();
</script>
</body>
</html>"""
