from __future__ import annotations


def subastas_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Subastas</title>
  <style>
    :root {
      --sb-accent:   #c2410c;
      --sb-accent2:  #9a3412;
      --sb-orange:   #ea580c;
      --sb-light:    #ffedd5;
      --sb-bg:       var(--page-bg, #f5f6f8);
      --sb-surface:  var(--content-bg, #ffffff);
      --sb-border:   var(--field-border, #d1d5db);
      --sb-text:     var(--body-text, #1f2937);
      --sb-muted:    color-mix(in srgb, var(--body-text, #1f2937) 60%, #ffffff 40%);
      --sb-focus:    #c2410c;
      --sb-success:  #16a34a;
      --sb-danger:   #dc2626;
      --sb-warn:     #d97706;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: var(--sb-bg); font-family: Arial, sans-serif; color: var(--sb-text); }

    .sb-page { padding: 0 0 48px; }

    /* ── Hero ───────────────────────────────────────────────────────────── */
    .sb-hero {
      background: linear-gradient(135deg, #1a0800 0%, #431407 50%, #1f1205 100%);
      border-radius: 20px; padding: 32px 32px 28px; margin-bottom: 28px;
      position: relative; overflow: hidden;
    }
    .sb-hero::before {
      content: ""; position: absolute; inset: 0;
      background:
        radial-gradient(ellipse 58% 58% at 82% 16%, rgba(194,65,12,0.42) 0%, transparent 68%),
        radial-gradient(ellipse 36% 44% at 14% 82%, rgba(234,88,12,0.22) 0%, transparent 70%);
      pointer-events: none;
    }
    .sb-hero__inner { position: relative; z-index: 1; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
    .sb-hero__icon {
      width: 64px; height: 64px; border-radius: 20px; flex-shrink: 0;
      background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);
      display: grid; place-items: center; font-size: 1.6rem; color: #fff;
      box-shadow: 0 8px 24px rgba(194,65,12,0.5);
    }
    .sb-hero__copy { flex: 1; min-width: 200px; }
    .sb-hero__copy h1 { margin: 0 0 6px; font-size: 1.55rem; font-weight: 800; color: #fff; letter-spacing: -0.02em; }
    .sb-hero__copy p  { margin: 0; color: rgba(255,255,255,0.72); font-size: 0.92rem; line-height: 1.5; }
    .sb-hero__badges  { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
    .sb-hero__badge {
      padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
      letter-spacing: 0.04em; text-transform: uppercase;
    }
    .sb-hero__badge--live  { background: rgba(234,88,12,0.35); color: #fed7aa; border: 1px solid rgba(254,215,170,0.28); }
    .sb-hero__badge--bids  { background: rgba(194,65,12,0.35); color: #fdba74; border: 1px solid rgba(253,186,116,0.25); }

    /* ── Stats ──────────────────────────────────────────────────────────── */
    .sb-stats {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 16px; margin-bottom: 28px;
    }
    .sb-stat { background: var(--sb-surface); border: 1px solid var(--sb-border); border-radius: 16px; padding: 18px 20px; }
    .sb-stat__value { font-size: 1.75rem; font-weight: 800; color: var(--sb-accent); line-height: 1; margin-bottom: 4px; }
    .sb-stat__label { font-size: 0.8rem; color: var(--sb-muted); font-weight: 600; }
    .sb-stat__sub   { font-size: 0.72rem; color: var(--sb-muted); margin-top: 2px; }
    .sb-stat--live .sb-stat__value { color: var(--sb-orange); }

    /* ── Tabs ───────────────────────────────────────────────────────────── */
    .sb-tabs { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
    .sb-tab {
      padding: 8px 18px; border-radius: 12px; font-size: 0.88rem; font-weight: 700;
      cursor: pointer; border: 1.5px solid var(--sb-border);
      background: var(--sb-surface); color: var(--sb-muted); transition: all 0.16s;
    }
    .sb-tab.is-active { background: var(--sb-accent); color: #fff; border-color: var(--sb-accent); }
    .sb-tab-panel { display: none; }
    .sb-tab-panel.is-active { display: block; }

    /* ── Toolbar ────────────────────────────────────────────────────────── */
    .sb-toolbar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
    .sb-search {
      flex: 1; min-width: 200px; max-width: 320px;
      padding: 9px 14px; border-radius: 12px; border: 1.5px solid var(--sb-border);
      font-size: 0.9rem; background: var(--sb-surface); color: var(--sb-text);
      outline: none; transition: border-color 0.15s;
    }
    .sb-search:focus { border-color: var(--sb-focus); }
    .sb-filter {
      padding: 9px 14px; border-radius: 12px; border: 1.5px solid var(--sb-border);
      font-size: 0.88rem; background: var(--sb-surface); color: var(--sb-text); outline: none; cursor: pointer;
    }
    .sb-btn-add {
      margin-left: auto; padding: 9px 18px; border-radius: 12px;
      background: var(--sb-accent); color: #fff; font-weight: 700; font-size: 0.88rem;
      border: none; cursor: pointer; display: flex; align-items: center; gap: 7px; transition: opacity 0.15s;
    }
    .sb-btn-add:hover { opacity: 0.88; }

    /* ── Auction card grid ──────────────────────────────────────────────── */
    .sb-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
    .sb-card {
      background: var(--sb-surface); border: 1px solid var(--sb-border);
      border-radius: 20px; overflow: hidden; cursor: pointer;
      transition: box-shadow 0.18s, transform 0.18s;
      display: flex; flex-direction: column;
    }
    .sb-card:hover { box-shadow: 0 10px 32px rgba(194,65,12,0.14); transform: translateY(-3px); }
    .sb-card--ending { border-color: var(--sb-warn); box-shadow: 0 0 0 2px rgba(217,119,6,0.2); }

    .sb-card__thumb {
      height: 160px; background: linear-gradient(135deg, #1a0800 0%, #431407 100%);
      display: grid; place-items: center; position: relative;
      flex-shrink: 0;
    }
    .sb-card__thumb-icon { font-size: 3rem; opacity: 0.35; color: #fed7aa; }
    .sb-card__estado-badge {
      position: absolute; top: 10px; right: 10px;
      padding: 4px 10px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.06em;
    }
    .sb-card__estado-badge--activa     { background: rgba(22,163,74,0.88);  color: #fff; }
    .sb-card__estado-badge--programada { background: rgba(29,78,216,0.88);  color: #fff; }
    .sb-card__estado-badge--finalizada { background: rgba(107,114,128,0.88);color: #fff; }
    .sb-card__estado-badge--cancelada  { background: rgba(220,38,38,0.88);  color: #fff; }
    .sb-card__estado-badge--desierta   { background: rgba(180,83,9,0.88);   color: #fff; }

    .sb-card__body { padding: 16px 18px; display: grid; gap: 10px; flex: 1; }
    .sb-card__title { font-size: 1rem; font-weight: 800; margin: 0; line-height: 1.3;
      display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .sb-card__meta  { font-size: 0.78rem; color: var(--sb-muted); }

    .sb-card__price-row { display: flex; align-items: baseline; gap: 8px; }
    .sb-card__price-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--sb-muted); }
    .sb-card__price { font-size: 1.5rem; font-weight: 800; color: var(--sb-accent); }
    .sb-card__bids  { font-size: 0.78rem; color: var(--sb-muted); margin-left: auto; white-space: nowrap; }

    /* ── Countdown ──────────────────────────────────────────────────────── */
    .sb-countdown {
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px;
      background: color-mix(in srgb, var(--sb-accent) 7%, var(--sb-surface) 93%);
      border: 1px solid color-mix(in srgb, var(--sb-accent) 20%, var(--sb-border) 80%);
      border-radius: 12px; padding: 10px 12px;
    }
    .sb-countdown.is-urgent {
      background: color-mix(in srgb, var(--sb-danger) 8%, var(--sb-surface) 92%);
      border-color: color-mix(in srgb, var(--sb-danger) 28%, var(--sb-border) 72%);
    }
    .sb-countdown__unit { text-align: center; }
    .sb-countdown__num  { font-size: 1.25rem; font-weight: 800; color: var(--sb-accent); line-height: 1; display: block; }
    .sb-countdown.is-urgent .sb-countdown__num { color: var(--sb-danger); }
    .sb-countdown__lbl  { font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--sb-muted); }

    .sb-card__time-bar { height: 5px; border-radius: 3px; background: #e5e7eb; overflow: hidden; margin-top: -4px; }
    .sb-card__time-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #ea580c, #c2410c); transition: width 1s linear; }
    .sb-card__time-fill--warn   { background: linear-gradient(90deg, #fbbf24, #d97706); }
    .sb-card__time-fill--urgent { background: linear-gradient(90deg, #f87171, #dc2626); }

    /* ── Table ──────────────────────────────────────────────────────────── */
    .sb-table-wrap { overflow-x: auto; border-radius: 14px; border: 1px solid var(--sb-border); }
    .sb-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    .sb-table thead tr { background: color-mix(in srgb, var(--sb-surface) 82%, var(--sb-bg) 18%); }
    .sb-table th { padding: 12px 14px; text-align: left; font-size: 0.72rem; font-weight: 700; color: var(--sb-muted); text-transform: uppercase; letter-spacing: 0.08em; white-space: nowrap; }
    .sb-table td { padding: 12px 14px; border-top: 1px solid var(--sb-border); vertical-align: middle; }
    .sb-table tbody tr { cursor: pointer; transition: background 0.12s; }
    .sb-table tbody tr:hover { background: color-mix(in srgb, var(--sb-accent) 5%, var(--sb-surface) 95%); }
    .sb-table__empty td { text-align: center; padding: 56px 16px; color: var(--sb-muted); cursor: default; }

    /* ── Badges ─────────────────────────────────────────────────────────── */
    .sb-badge {
      display: inline-block; padding: 3px 10px; border-radius: 10px;
      font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
    }
    .sb-badge--activa     { background: #dcfce7; color: #166534; }
    .sb-badge--programada { background: #dbeafe; color: #1e40af; }
    .sb-badge--finalizada { background: #f3f4f6; color: #374151; }
    .sb-badge--cancelada  { background: #fee2e2; color: #991b1b; }
    .sb-badge--desierta   { background: #fef3c7; color: #92400e; }

    .sb-money { font-variant-numeric: tabular-nums; font-weight: 700; }
    .sb-money--win { color: var(--sb-success); }

    /* ── Drawer ─────────────────────────────────────────────────────────── */
    .sb-drawer-bg {
      display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.46);
      z-index: 1040; align-items: flex-end; justify-content: center;
    }
    .sb-drawer-bg.is-open { display: flex; }
    .sb-drawer {
      background: var(--sb-surface); border-radius: 24px 24px 0 0;
      width: 100%; max-width: 700px; padding: 28px 28px 32px;
      max-height: 94vh; overflow-y: auto;
    }
    .sb-drawer__title    { font-size: 1.2rem; font-weight: 800; margin: 0 0 2px; }
    .sb-drawer__subtitle { font-size: 0.82rem; color: var(--sb-muted); margin: 0 0 22px; }

    /* ── Form ────────────────────────────────────────────────────────────── */
    .sb-field { margin-bottom: 15px; }
    .sb-field label { display: block; font-size: 0.77rem; font-weight: 700; margin-bottom: 5px; color: var(--sb-muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .sb-field input, .sb-field select, .sb-field textarea {
      width: 100%; padding: 10px 12px; border-radius: 10px;
      border: 1.5px solid var(--sb-border); font-size: 0.95rem;
      background: var(--sb-surface); color: var(--sb-text); outline: none; transition: border-color 0.15s;
    }
    .sb-field input:focus, .sb-field select:focus, .sb-field textarea:focus { border-color: var(--sb-focus); }
    .sb-field textarea { resize: vertical; min-height: 64px; }
    .sb-field--row  { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .sb-field--row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
    .sb-field--ro input { background: color-mix(in srgb, var(--sb-surface) 82%, var(--sb-bg) 18%); }
    .sb-section-title {
      font-size: 0.77rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
      color: var(--sb-muted); margin: 20px 0 12px; padding-top: 16px; border-top: 1px solid var(--sb-border);
    }

    /* ── Current bid hero ────────────────────────────────────────────────── */
    .sb-bid-hero {
      background: linear-gradient(135deg, #1a0800 0%, #431407 100%);
      border-radius: 16px; padding: 20px 22px; margin-bottom: 20px;
      display: flex; align-items: center; gap: 20px; flex-wrap: wrap;
      position: relative; overflow: hidden;
    }
    .sb-bid-hero::before {
      content: ""; position: absolute; inset: 0;
      background: radial-gradient(ellipse 60% 80% at 90% 30%, rgba(234,88,12,0.32) 0%, transparent 70%);
      pointer-events: none;
    }
    .sb-bid-hero__inner { position: relative; z-index: 1; flex: 1; }
    .sb-bid-hero__label  { font-size: 0.75rem; font-weight: 700; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }
    .sb-bid-hero__amount { font-size: 2.2rem; font-weight: 800; color: #fff; line-height: 1; }
    .sb-bid-hero__sub    { font-size: 0.78rem; color: rgba(255,255,255,0.55); margin-top: 6px; }
    .sb-bid-hero__meta   { position: relative; z-index: 1; text-align: right; }
    .sb-bid-hero__bids   { font-size: 1.4rem; font-weight: 800; color: #fed7aa; }
    .sb-bid-hero__blabel { font-size: 0.72rem; color: rgba(255,255,255,0.55); text-transform: uppercase; letter-spacing: 0.08em; }

    /* ── Bid history ─────────────────────────────────────────────────────── */
    .sb-bids-list { display: grid; gap: 8px; margin-bottom: 16px; max-height: 280px; overflow-y: auto; }
    .sb-bid-row {
      display: flex; align-items: center; gap: 10px;
      padding: 10px 14px; border-radius: 12px;
      background: var(--sb-surface); border: 1px solid var(--sb-border);
    }
    .sb-bid-row--winner {
      background: color-mix(in srgb, var(--sb-success) 8%, var(--sb-surface) 92%);
      border-color: color-mix(in srgb, var(--sb-success) 28%, var(--sb-border) 72%);
    }
    .sb-bid-row--winner .sb-bid-row__monto { color: var(--sb-success); }
    .sb-bid-row__rank {
      width: 28px; height: 28px; border-radius: 8px; flex-shrink: 0;
      display: grid; place-items: center; font-size: 0.78rem; font-weight: 800;
      background: color-mix(in srgb, var(--sb-accent) 12%, var(--sb-surface) 88%);
      color: var(--sb-accent);
    }
    .sb-bid-row--winner .sb-bid-row__rank { background: color-mix(in srgb, var(--sb-success) 18%, var(--sb-surface) 82%); color: var(--sb-success); }
    .sb-bid-row__info  { flex: 1; min-width: 0; }
    .sb-bid-row__name  { font-size: 0.88rem; font-weight: 700; }
    .sb-bid-row__meta  { font-size: 0.74rem; color: var(--sb-muted); }
    .sb-bid-row__monto { font-size: 1rem; font-weight: 800; color: var(--sb-accent); white-space: nowrap; }
    .sb-bid-row__del   { background: none; border: none; cursor: pointer; color: #e5e7eb; font-size: 0.78rem; padding: 4px; transition: color 0.15s; }
    .sb-bid-row__del:hover { color: var(--sb-danger); }
    .sb-bids-empty { text-align: center; padding: 22px; color: var(--sb-muted); font-size: 0.88rem;
      background: color-mix(in srgb, var(--sb-surface) 82%, var(--sb-bg) 18%); border-radius: 12px; }

    /* ── New bid inline form ─────────────────────────────────────────────── */
    .sb-puja-form {
      background: color-mix(in srgb, var(--sb-accent) 5%, var(--sb-surface) 95%);
      border: 1.5px dashed color-mix(in srgb, var(--sb-accent) 32%, var(--sb-border) 68%);
      border-radius: 14px; padding: 16px 18px;
    }
    .sb-puja-form__title { font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: var(--sb-accent); margin-bottom: 12px; }
    .sb-puja-form__grid  { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px; }
    .sb-puja-form input  {
      width: 100%; padding: 9px 11px; border-radius: 9px;
      border: 1.5px solid var(--sb-border); font-size: 0.88rem;
      background: var(--sb-surface); color: var(--sb-text); outline: none; transition: border-color 0.15s;
    }
    .sb-puja-form input:focus { border-color: var(--sb-focus); }
    .sb-puja-form__min { font-size: 0.75rem; color: var(--sb-muted); margin-bottom: 10px; }
    .sb-puja-form__min span { font-weight: 700; color: var(--sb-accent); }
    .sb-puja-form__actions { display: flex; gap: 8px; justify-content: flex-end; }
    .sb-puja-save-btn {
      padding: 8px 18px; border-radius: 10px; background: var(--sb-accent);
      color: #fff; font-weight: 700; font-size: 0.85rem; border: none; cursor: pointer; transition: opacity 0.15s;
    }
    .sb-puja-save-btn:hover { opacity: 0.88; }

    /* ── Winner banner ───────────────────────────────────────────────────── */
    .sb-winner-banner {
      background: linear-gradient(135deg, #052e16 0%, #14532d 100%);
      border-radius: 14px; padding: 16px 18px; margin-bottom: 16px;
      display: flex; align-items: center; gap: 14px;
    }
    .sb-winner-banner__icon { font-size: 1.8rem; }
    .sb-winner-banner__copy { flex: 1; }
    .sb-winner-banner__title { font-size: 0.78rem; font-weight: 700; color: rgba(255,255,255,0.65); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; }
    .sb-winner-banner__name  { font-size: 1.05rem; font-weight: 800; color: #fff; }
    .sb-winner-banner__sub   { font-size: 0.78rem; color: rgba(255,255,255,0.6); margin-top: 2px; }
    .sb-winner-banner__price { font-size: 1.35rem; font-weight: 800; color: #86efac; white-space: nowrap; }

    /* ── Drawer footer ───────────────────────────────────────────────────── */
    .sb-drawer__footer {
      display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap;
      margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--sb-border);
    }
    .sb-btn {
      padding: 10px 20px; border-radius: 12px; font-size: 0.9rem; font-weight: 700;
      cursor: pointer; border: none; transition: opacity 0.15s;
    }
    .sb-btn:hover { opacity: 0.88; }
    .sb-btn--primary   { background: var(--sb-accent);   color: #fff; }
    .sb-btn--secondary { background: var(--sb-surface);  color: var(--sb-muted); border: 1.5px solid var(--sb-border); }
    .sb-btn--success   { background: var(--sb-success);  color: #fff; }
    .sb-btn--warn      { background: #fef3c7; color: var(--sb-warn); }
    .sb-btn--danger    { background: #fee2e2; color: var(--sb-danger); }

    /* ── Empty ────────────────────────────────────────────────────────────── */
    .sb-empty { text-align: center; padding: 60px 24px; color: var(--sb-muted); }
    .sb-empty i { font-size: 2.8rem; margin-bottom: 12px; opacity: 0.3; color: var(--sb-accent); display: block; }

    @media (max-width: 640px) {
      .sb-hero { padding: 20px 16px 18px; }
      .sb-hero__copy h1 { font-size: 1.25rem; }
      .sb-field--row, .sb-field--row3, .sb-puja-form__grid { grid-template-columns: 1fr; }
      .sb-countdown { grid-template-columns: repeat(4, 1fr); }
    }
  </style>
</head>
<body>
<main class="sb-page">

  <!-- Hero -->
  <div class="sb-hero">
    <div class="sb-hero__inner">
      <div class="sb-hero__icon"><i class="fa-solid fa-gavel" aria-hidden="true"></i></div>
      <div class="sb-hero__copy">
        <h1>Subastas</h1>
        <p>Publica artículos a subasta, recibe pujas en tiempo real y adjudica al mejor postor.</p>
        <div class="sb-hero__badges">
          <span class="sb-hero__badge sb-hero__badge--live"><i class="fa-solid fa-tower-broadcast"></i> Tiempo real</span>
          <span class="sb-hero__badge sb-hero__badge--bids"><i class="fa-solid fa-arrow-trend-up"></i> Pujas abiertas</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Stats -->
  <div class="sb-stats">
    <div class="sb-stat sb-stat--live">
      <div class="sb-stat__value" id="sb-stat-activas">—</div>
      <div class="sb-stat__label">Subastas activas</div>
      <div class="sb-stat__sub" id="sb-stat-activas-sub">en curso</div>
    </div>
    <div class="sb-stat">
      <div class="sb-stat__value" id="sb-stat-pujas">—</div>
      <div class="sb-stat__label">Total de pujas</div>
      <div class="sb-stat__sub">en todas las activas</div>
    </div>
    <div class="sb-stat">
      <div class="sb-stat__value" id="sb-stat-adjudicado">—</div>
      <div class="sb-stat__label">Adjudicado este mes</div>
      <div class="sb-stat__sub" id="sb-stat-adjudicado-n">— finalizadas</div>
    </div>
    <div class="sb-stat">
      <div class="sb-stat__value" id="sb-stat-programadas">—</div>
      <div class="sb-stat__label">Programadas</div>
      <div class="sb-stat__sub">próximas a iniciar</div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="sb-tabs">
    <button class="sb-tab is-active" data-tab="activas">Activas y programadas</button>
    <button class="sb-tab" data-tab="historial">Historial</button>
    <button class="sb-tab" data-tab="gestionar">Gestionar</button>
  </div>

  <!-- Panel: Activas -->
  <div class="sb-tab-panel is-active" id="sb-panel-activas">
    <div class="sb-toolbar">
      <input class="sb-search" type="search" id="sb-search-activas" placeholder="Buscar por título, categoría…" />
      <button class="sb-btn-add" id="sb-add-btn-activas">
        <i class="fa-solid fa-plus" aria-hidden="true"></i> Nueva subasta
      </button>
    </div>
    <div class="sb-cards" id="sb-cards-activas"></div>
  </div>

  <!-- Panel: Historial -->
  <div class="sb-tab-panel" id="sb-panel-historial">
    <div class="sb-toolbar">
      <input class="sb-search" type="search" id="sb-search-historial" placeholder="Buscar…" />
      <select class="sb-filter" id="sb-filter-historial">
        <option value="">Estado: todos</option>
        <option value="finalizada">Finalizada</option>
        <option value="desierta">Desierta</option>
        <option value="cancelada">Cancelada</option>
      </select>
    </div>
    <div class="sb-table-wrap">
      <table class="sb-table">
        <thead>
          <tr>
            <th>Folio</th>
            <th>Título</th>
            <th>Base</th>
            <th>Precio final</th>
            <th>Pujas</th>
            <th>Ganador</th>
            <th>Cierre</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody id="sb-tbody-historial"></tbody>
      </table>
    </div>
  </div>

  <!-- Panel: Gestionar -->
  <div class="sb-tab-panel" id="sb-panel-gestionar">
    <div class="sb-toolbar">
      <input class="sb-search" type="search" id="sb-search-gestionar" placeholder="Buscar…" />
      <button class="sb-btn-add" id="sb-add-btn-gestionar">
        <i class="fa-solid fa-plus" aria-hidden="true"></i> Nueva subasta
      </button>
    </div>
    <div class="sb-table-wrap">
      <table class="sb-table">
        <thead>
          <tr>
            <th>Folio</th>
            <th>Título</th>
            <th>Base</th>
            <th>Puja actual</th>
            <th>Pujas</th>
            <th>Inicio</th>
            <th>Cierre</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody id="sb-tbody-gestionar"></tbody>
      </table>
    </div>
  </div>

</main>

<!-- ══════════════════════════════════════════════════════════════════════
     Drawer: Crear / Editar subasta
═══════════════════════════════════════════════════════════════════════ -->
<div class="sb-drawer-bg" id="sb-new-drawer-bg" role="dialog" aria-modal="true" aria-labelledby="sb-new-title">
  <div class="sb-drawer">
    <h2 class="sb-drawer__title" id="sb-new-title">Nueva subasta</h2>
    <p class="sb-drawer__subtitle">Configura el artículo, precios y tiempos de la subasta</p>

    <div class="sb-field">
      <label>Título del artículo *</label>
      <input type="text" id="sb-f-titulo" maxlength="160" placeholder="Ej. Televisor 55″ OLED Samsung" />
    </div>
    <div class="sb-field--row">
      <div class="sb-field">
        <label>Categoría</label>
        <select id="sb-f-categoria">
          <option value="">Sin categoría</option>
          <option value="electronica">Electrónica</option>
          <option value="moda">Moda y accesorios</option>
          <option value="hogar">Hogar y muebles</option>
          <option value="arte">Arte y colección</option>
          <option value="vehiculos">Vehículos</option>
          <option value="inmuebles">Inmuebles</option>
          <option value="joyeria">Joyería</option>
          <option value="otro">Otro</option>
        </select>
      </div>
      <div class="sb-field">
        <label>Estado inicial</label>
        <select id="sb-f-estado-inicial">
          <option value="programada">Programada (inicia después)</option>
          <option value="activa">Activa (inicia ahora)</option>
        </select>
      </div>
    </div>
    <div class="sb-field">
      <label>Descripción del artículo</label>
      <textarea id="sb-f-descripcion" rows="3" placeholder="Características, condición, detalles relevantes para los postores…"></textarea>
    </div>

    <p class="sb-section-title">Precios</p>
    <div class="sb-field--row3">
      <div class="sb-field">
        <label>Precio base * <small style="text-transform:none;font-weight:400">(primera puja mín.)</small></label>
        <input type="number" id="sb-f-base" min="0" step="0.01" placeholder="0.00" />
      </div>
      <div class="sb-field">
        <label>Incremento mínimo *</label>
        <input type="number" id="sb-f-incremento" min="0" step="0.01" placeholder="0.00" />
      </div>
      <div class="sb-field">
        <label>Precio reserva <small style="text-transform:none;font-weight:400">(opcional, privado)</small></label>
        <input type="number" id="sb-f-reserva" min="0" step="0.01" placeholder="0.00" />
      </div>
    </div>

    <p class="sb-section-title">Tiempos</p>
    <div class="sb-field--row">
      <div class="sb-field">
        <label>Fecha y hora de inicio *</label>
        <input type="datetime-local" id="sb-f-inicio" />
      </div>
      <div class="sb-field">
        <label>Fecha y hora de cierre *</label>
        <input type="datetime-local" id="sb-f-cierre" />
      </div>
    </div>

    <p class="sb-section-title">Condiciones</p>
    <div class="sb-field">
      <label>Términos y condiciones de la subasta</label>
      <textarea id="sb-f-condiciones" rows="2" placeholder="Ej. El ganador tiene 48 h para liquidar. No se aceptan devoluciones."></textarea>
    </div>

    <div class="sb-drawer__footer">
      <button class="sb-btn sb-btn--danger" id="sb-new-delete-btn" style="display:none">Eliminar</button>
      <button class="sb-btn sb-btn--secondary" id="sb-new-cancel-btn">Cancelar</button>
      <button class="sb-btn sb-btn--primary" id="sb-new-save-btn">Guardar subasta</button>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════════════
     Drawer: Detalle de subasta + pujas
═══════════════════════════════════════════════════════════════════════ -->
<div class="sb-drawer-bg" id="sb-detail-drawer-bg" role="dialog" aria-modal="true" aria-labelledby="sb-detail-title">
  <div class="sb-drawer">
    <h2 class="sb-drawer__title" id="sb-detail-title">Subasta</h2>
    <p class="sb-drawer__subtitle" id="sb-detail-subtitle"></p>

    <!-- Winner banner (shown when finalizada/desierta) -->
    <div class="sb-winner-banner" id="sb-winner-banner" style="display:none">
      <div class="sb-winner-banner__icon">🏆</div>
      <div class="sb-winner-banner__copy">
        <div class="sb-winner-banner__title">Ganador de la subasta</div>
        <div class="sb-winner-banner__name" id="sb-winner-name">—</div>
        <div class="sb-winner-banner__sub" id="sb-winner-tel">—</div>
      </div>
      <div class="sb-winner-banner__price" id="sb-winner-price">—</div>
    </div>

    <!-- Current bid hero -->
    <div class="sb-bid-hero">
      <div class="sb-bid-hero__inner">
        <div class="sb-bid-hero__label" id="sb-dh-label">Puja más alta</div>
        <div class="sb-bid-hero__amount" id="sb-dh-amount">—</div>
        <div class="sb-bid-hero__sub" id="sb-dh-sub">—</div>
      </div>
      <div class="sb-bid-hero__meta">
        <div class="sb-bid-hero__bids" id="sb-dh-bids">0</div>
        <div class="sb-bid-hero__blabel">pujas</div>
      </div>
    </div>

    <!-- Bids list -->
    <p class="sb-section-title" style="margin-top:4px">Historial de pujas</p>
    <div class="sb-bids-list" id="sb-bids-list"></div>

    <!-- Nueva puja inline -->
    <div class="sb-puja-form" id="sb-puja-form">
      <div class="sb-puja-form__title"><i class="fa-solid fa-gavel" style="margin-right:5px"></i>Registrar puja</div>
      <div class="sb-puja-form__min">Puja mínima: <span id="sb-puja-min-label">—</span></div>
      <div class="sb-puja-form__grid">
        <div>
          <label style="font-size:.75rem;font-weight:700;color:var(--sb-muted);text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:4px">Nombre postor *</label>
          <input type="text" id="sb-puja-nombre" maxlength="80" placeholder="Nombre completo" />
        </div>
        <div>
          <label style="font-size:.75rem;font-weight:700;color:var(--sb-muted);text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:4px">Teléfono</label>
          <input type="tel" id="sb-puja-tel" maxlength="20" placeholder="10 dígitos" />
        </div>
        <div>
          <label style="font-size:.75rem;font-weight:700;color:var(--sb-muted);text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:4px">Monto de puja *</label>
          <input type="number" id="sb-puja-monto" min="0" step="0.01" placeholder="0.00" />
        </div>
      </div>
      <div class="sb-puja-form__actions">
        <button class="sb-puja-save-btn" id="sb-puja-save-btn">
          <i class="fa-solid fa-gavel" style="margin-right:5px"></i>Registrar puja
        </button>
      </div>
      <div id="sb-puja-error" style="font-size:0.8rem;color:var(--sb-danger);margin-top:8px;display:none"></div>
    </div>

    <div class="sb-drawer__footer">
      <button class="sb-btn sb-btn--secondary"  id="sb-detail-edit-btn"><i class="fa-solid fa-pen" style="margin-right:4px"></i>Editar</button>
      <button class="sb-btn sb-btn--success"     id="sb-detail-activar-btn">Activar</button>
      <button class="sb-btn sb-btn--warn"        id="sb-detail-finalizar-btn">Finalizar</button>
      <button class="sb-btn sb-btn--danger"      id="sb-detail-cancelar-btn">Cancelar subasta</button>
      <button class="sb-btn sb-btn--secondary"   id="sb-detail-close-btn">Cerrar</button>
    </div>
  </div>
</div>

<script>
(function () {
  var LS_KEY = 'multitienda_subastas';

  function load()  { try { return JSON.parse(localStorage.getItem(LS_KEY) || '[]'); } catch { return []; } }
  function save(d) { localStorage.setItem(LS_KEY, JSON.stringify(d)); }

  // ── Format helpers ───────────────────────────────────────────────────────
  function fmt(n) { return '$' + parseFloat(n||0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function escHtml(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function nowISO()   { return new Date().toISOString().slice(0,16); }
  function currentMonth() { return new Date().toISOString().slice(0,7); }
  function fmtDatetime(s) { if (!s) return '—'; return s.replace('T', ' '); }

  function topBid(sb) {
    if (!sb.pujas || !sb.pujas.length) return null;
    return sb.pujas.reduce(function(a,b){ return parseFloat(b.monto||0) > parseFloat(a.monto||0) ? b : a; });
  }
  function currentPrice(sb) {
    var top = topBid(sb);
    return top ? parseFloat(top.monto||0) : parseFloat(sb.base||0);
  }
  function nextMinBid(sb) {
    return currentPrice(sb) + parseFloat(sb.incremento||0);
  }
  function genFolio() {
    return 'SUB-' + new Date().getFullYear() + '-' + String(load().length + 1).padStart(4,'0');
  }

  // ── Stats ────────────────────────────────────────────────────────────────
  function refreshStats() {
    var list  = load();
    var activas     = list.filter(function(s){ return s.estado === 'activa'; });
    var programadas = list.filter(function(s){ return s.estado === 'programada'; });
    var mes = currentMonth();
    var finMes = list.filter(function(s){ return (s.estado === 'finalizada') && (s.cierre||'').startsWith(mes); });
    var adjMonto = finMes.reduce(function(sum, s){ var t = topBid(s); return sum + (t ? parseFloat(t.monto||0) : 0); }, 0);
    var totalPujas = activas.reduce(function(sum, s){ return sum + (s.pujas||[]).length; }, 0);

    setText('sb-stat-activas',       activas.length);
    setText('sb-stat-activas-sub',   activas.length === 1 ? 'en curso' : 'en curso ahora');
    setText('sb-stat-pujas',         totalPujas);
    setText('sb-stat-adjudicado',    fmt(adjMonto));
    setText('sb-stat-adjudicado-n',  finMes.length + ' finalizadas');
    setText('sb-stat-programadas',   programadas.length);
  }
  function setText(id, v) { var el = document.getElementById(id); if (el) el.textContent = v; }

  // ── Badges ───────────────────────────────────────────────────────────────
  var BADGE_CSS   = { activa:'sb-badge--activa', programada:'sb-badge--programada', finalizada:'sb-badge--finalizada', cancelada:'sb-badge--cancelada', desierta:'sb-badge--desierta' };
  var BADGE_LABEL = { activa:'Activa', programada:'Programada', finalizada:'Finalizada', cancelada:'Cancelada', desierta:'Desierta' };
  var CARD_ESTADO_CSS = { activa:'activa', programada:'programada', finalizada:'finalizada', cancelada:'cancelada', desierta:'desierta' };
  function badge(estado) { return '<span class="sb-badge ' + (BADGE_CSS[estado]||'') + '">' + (BADGE_LABEL[estado]||estado) + '</span>'; }

  // ── Countdown ────────────────────────────────────────────────────────────
  function secondsLeft(closeStr) {
    if (!closeStr) return 0;
    return Math.max(0, Math.floor((new Date(closeStr) - Date.now()) / 1000));
  }
  function formatCountdown(secs, cardEl) {
    var d = Math.floor(secs / 86400);
    var h = Math.floor((secs % 86400) / 3600);
    var m = Math.floor((secs % 3600) / 60);
    var s = secs % 60;
    var isUrgent = secs < 3600;
    var cdEl = cardEl.querySelector('.sb-countdown');
    if (cdEl) {
      if (isUrgent) cdEl.classList.add('is-urgent'); else cdEl.classList.remove('is-urgent');
      var nums = cdEl.querySelectorAll('.sb-countdown__num');
      if (nums[0]) nums[0].textContent = String(d).padStart(2,'0');
      if (nums[1]) nums[1].textContent = String(h).padStart(2,'0');
      if (nums[2]) nums[2].textContent = String(m).padStart(2,'0');
      if (nums[3]) nums[3].textContent = String(s).padStart(2,'0');
    }
    var fillEl = cardEl.querySelector('.sb-card__time-fill');
    if (fillEl && cardEl.dataset.totalSecs) {
      var total = parseInt(cardEl.dataset.totalSecs);
      var pct = total > 0 ? Math.min(100, Math.round(secs / total * 100)) : 0;
      fillEl.style.width = pct + '%';
      fillEl.className = 'sb-card__time-fill' + (secs < 3600 ? ' sb-card__time-fill--urgent' : secs < 86400 ? ' sb-card__time-fill--warn' : '');
    }
    if (secs === 0) {
      // Auto-finalize
      var list = load();
      var sb   = list.find(function(x){ return x.id === cardEl.dataset.id; });
      if (sb && sb.estado === 'activa') {
        var top = topBid(sb);
        var reserva = parseFloat(sb.reserva || 0);
        sb.estado = (top && (reserva <= 0 || parseFloat(top.monto) >= reserva)) ? 'finalizada' : 'desierta';
        save(list);
        renderAll();
      }
    }
  }

  var _timers = {};
  function startCountdownFor(cardEl, closeStr, startStr) {
    var id = cardEl.dataset.id;
    if (_timers[id]) clearInterval(_timers[id]);
    var totalSecs = Math.max(0, Math.floor((new Date(closeStr) - new Date(startStr)) / 1000));
    cardEl.dataset.totalSecs = totalSecs;
    function tick() {
      var left = secondsLeft(closeStr);
      formatCountdown(left, cardEl);
      if (left <= 0) { clearInterval(_timers[id]); delete _timers[id]; }
    }
    tick();
    _timers[id] = setInterval(tick, 1000);
  }

  // ── Render cards (Activas) ────────────────────────────────────────────────
  var CAT_ICONS = { electronica:'fa-microchip', moda:'fa-shirt', hogar:'fa-couch', arte:'fa-palette', vehiculos:'fa-car', inmuebles:'fa-house', joyeria:'fa-gem', otro:'fa-tag' };

  function renderCards(list, containerId, searchId) {
    var search = ((document.getElementById(searchId)||{}).value||'').toLowerCase();
    var filtered = list.filter(function(s){
      if (s.estado !== 'activa' && s.estado !== 'programada') return false;
      if (search && !(s.titulo + ' ' + (s.categoria||'')).toLowerCase().includes(search)) return false;
      return true;
    });
    var container = document.getElementById(containerId);
    if (!filtered.length) {
      container.innerHTML = '<div class="sb-empty"><i class="fa-solid fa-gavel"></i><p>No hay subastas activas ni programadas.</p></div>';
      return;
    }
    container.innerHTML = filtered.map(function(s){
      var icon    = CAT_ICONS[s.categoria] || 'fa-tag';
      var top     = topBid(s);
      var price   = top ? parseFloat(top.monto) : parseFloat(s.base||0);
      var nPujas  = (s.pujas||[]).length;
      var isEnding = secondsLeft(s.cierre) < 86400 && s.estado === 'activa';
      return '<div class="sb-card' + (isEnding ? ' sb-card--ending' : '') + '" data-id="' + s.id + '" data-close="' + escHtml(s.cierre||'') + '">'
        + '<div class="sb-card__thumb">'
        + '<i class="fa-solid ' + icon + ' sb-card__thumb-icon"></i>'
        + '<span class="sb-card__estado-badge sb-card__estado-badge--' + escHtml(CARD_ESTADO_CSS[s.estado]||'') + '">' + escHtml(BADGE_LABEL[s.estado]||s.estado) + '</span>'
        + '</div>'
        + '<div class="sb-card__body">'
        + '<h3 class="sb-card__title">' + escHtml(s.titulo) + '</h3>'
        + '<div class="sb-card__meta">' + (s.categoria ? escHtml(s.categoria.charAt(0).toUpperCase()+s.categoria.slice(1)) : '') + (s.folio ? ' · ' + escHtml(s.folio) : '') + '</div>'
        + '<div class="sb-card__price-row">'
        + '<span class="sb-card__price-label">' + (top ? 'Puja actual' : 'Base') + '</span>'
        + '<span class="sb-card__price">' + fmt(price) + '</span>'
        + '<span class="sb-card__bids"><i class="fa-solid fa-gavel" style="margin-right:4px;font-size:.75rem"></i>' + nPujas + ' puja' + (nPujas!==1?'s':'') + '</span>'
        + '</div>'
        + (s.estado === 'activa'
            ? '<div class="sb-countdown" data-countdown>'
              + '<div class="sb-countdown__unit"><span class="sb-countdown__num">00</span><span class="sb-countdown__lbl">Días</span></div>'
              + '<div class="sb-countdown__unit"><span class="sb-countdown__num">00</span><span class="sb-countdown__lbl">Horas</span></div>'
              + '<div class="sb-countdown__unit"><span class="sb-countdown__num">00</span><span class="sb-countdown__lbl">Min</span></div>'
              + '<div class="sb-countdown__unit"><span class="sb-countdown__num">00</span><span class="sb-countdown__lbl">Seg</span></div>'
              + '</div>'
              + '<div class="sb-card__time-bar"><div class="sb-card__time-fill" style="width:100%"></div></div>'
            : '<div style="font-size:0.78rem;color:var(--sb-muted)">Inicia: ' + escHtml(fmtDatetime(s.inicio)) + '</div>'
          )
        + '</div></div>';
    }).join('');

    // Start countdowns
    filtered.forEach(function(s){
      if (s.estado !== 'activa') return;
      var cardEl = container.querySelector('[data-id="' + s.id + '"]');
      if (cardEl) startCountdownFor(cardEl, s.cierre, s.inicio);
    });
  }

  // ── Render historial table ────────────────────────────────────────────────
  function renderHistorial() {
    var list   = load();
    var search = ((document.getElementById('sb-search-historial')||{}).value||'').toLowerCase();
    var fEst   = ((document.getElementById('sb-filter-historial')||{}).value||'');
    var filtered = list.filter(function(s){
      if (s.estado !== 'finalizada' && s.estado !== 'desierta' && s.estado !== 'cancelada') return false;
      if (fEst && s.estado !== fEst) return false;
      if (search && !(s.titulo + ' ' + (s.folio||'')).toLowerCase().includes(search)) return false;
      return true;
    });
    var tbody = document.getElementById('sb-tbody-historial');
    if (!filtered.length) {
      tbody.innerHTML = '<tr class="sb-table__empty"><td colspan="8"><i class="fa-solid fa-clock-rotate-left" style="font-size:1.8rem;display:block;margin-bottom:10px;opacity:.3"></i>Sin historial aún.</td></tr>';
      return;
    }
    tbody.innerHTML = filtered.map(function(s){
      var top    = topBid(s);
      var ganador = top ? escHtml(top.nombre) : '<span style="color:var(--sb-muted)">Desierta</span>';
      return '<tr data-id="' + s.id + '">'
        + '<td><code style="font-size:.82rem">' + escHtml(s.folio||'') + '</code></td>'
        + '<td>' + escHtml(s.titulo) + '</td>'
        + '<td class="sb-money">' + fmt(s.base) + '</td>'
        + '<td class="sb-money sb-money--win">' + (top ? fmt(top.monto) : '—') + '</td>'
        + '<td>' + (s.pujas||[]).length + '</td>'
        + '<td>' + ganador + '</td>'
        + '<td style="white-space:nowrap;font-size:.82rem">' + escHtml(fmtDatetime(s.cierre)) + '</td>'
        + '<td>' + badge(s.estado) + '</td>'
        + '</tr>';
    }).join('');
  }

  // ── Render gestionar table ────────────────────────────────────────────────
  function renderGestionar() {
    var list   = load();
    var search = ((document.getElementById('sb-search-gestionar')||{}).value||'').toLowerCase();
    var filtered = list.filter(function(s){
      if (search && !(s.titulo + ' ' + (s.folio||'')).toLowerCase().includes(search)) return false;
      return true;
    });
    var tbody = document.getElementById('sb-tbody-gestionar');
    if (!filtered.length) {
      tbody.innerHTML = '<tr class="sb-table__empty"><td colspan="8"><i class="fa-solid fa-gavel" style="font-size:1.8rem;display:block;margin-bottom:10px;opacity:.3"></i>Sin subastas registradas.</td></tr>';
      return;
    }
    tbody.innerHTML = filtered.map(function(s){
      var top = topBid(s);
      return '<tr data-id="' + s.id + '">'
        + '<td><code style="font-size:.82rem">' + escHtml(s.folio||'') + '</code></td>'
        + '<td>' + escHtml(s.titulo) + '</td>'
        + '<td class="sb-money">' + fmt(s.base) + '</td>'
        + '<td class="sb-money">' + (top ? fmt(top.monto) : '—') + '</td>'
        + '<td>' + (s.pujas||[]).length + '</td>'
        + '<td style="white-space:nowrap;font-size:.82rem">' + escHtml(fmtDatetime(s.inicio)) + '</td>'
        + '<td style="white-space:nowrap;font-size:.82rem">' + escHtml(fmtDatetime(s.cierre)) + '</td>'
        + '<td>' + badge(s.estado) + '</td>'
        + '</tr>';
    }).join('');
  }

  function renderAll() {
    var list = load();
    renderCards(list, 'sb-cards-activas', 'sb-search-activas');
    renderHistorial();
    renderGestionar();
    refreshStats();
  }

  // ── Tabs ─────────────────────────────────────────────────────────────────
  document.querySelectorAll('.sb-tab').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.sb-tab').forEach(function(b){ b.classList.remove('is-active'); });
      document.querySelectorAll('.sb-tab-panel').forEach(function(p){ p.classList.remove('is-active'); });
      btn.classList.add('is-active');
      var panel = document.getElementById('sb-panel-' + btn.dataset.tab);
      if (panel) panel.classList.add('is-active');
    });
  });

  // ── Row / card click ──────────────────────────────────────────────────────
  document.addEventListener('click', function(e){
    var card = e.target.closest('.sb-card[data-id]');
    if (card) { openDetailDrawer(card.dataset.id); return; }
    var tr = e.target.closest('tr[data-id]');
    if (tr && tr.dataset.id) { openDetailDrawer(tr.dataset.id); return; }
  });

  // ── Search / filter ───────────────────────────────────────────────────────
  document.getElementById('sb-search-activas').addEventListener('input', function(){ renderCards(load(), 'sb-cards-activas', 'sb-search-activas'); });
  document.getElementById('sb-search-historial').addEventListener('input', renderHistorial);
  document.getElementById('sb-filter-historial').addEventListener('change', renderHistorial);
  document.getElementById('sb-search-gestionar').addEventListener('input', renderGestionar);

  // ────────────────────────────────────────────────────────────────────────
  // NEW / EDIT DRAWER
  // ────────────────────────────────────────────────────────────────────────
  var newDrawerBg  = document.getElementById('sb-new-drawer-bg');
  var newEditingId = null;

  function openNewDrawer(id) {
    newEditingId = id;
    var list = load();
    var item = id ? list.find(function(s){ return s.id === id; }) : null;
    document.getElementById('sb-new-title').textContent = id ? 'Editar subasta' : 'Nueva subasta';
    document.getElementById('sb-f-titulo').value          = item ? item.titulo      : '';
    document.getElementById('sb-f-categoria').value       = item ? (item.categoria||'') : '';
    document.getElementById('sb-f-estado-inicial').value  = item ? item.estado      : 'programada';
    document.getElementById('sb-f-descripcion').value     = item ? (item.descripcion||'') : '';
    document.getElementById('sb-f-base').value            = item ? item.base        : '';
    document.getElementById('sb-f-incremento').value      = item ? item.incremento  : '';
    document.getElementById('sb-f-reserva').value         = item ? (item.reserva||'') : '';
    document.getElementById('sb-f-inicio').value          = item ? item.inicio      : nowISO();
    document.getElementById('sb-f-cierre').value          = item ? item.cierre      : '';
    document.getElementById('sb-f-condiciones').value     = item ? (item.condiciones||'') : '';
    document.getElementById('sb-new-delete-btn').style.display = id ? 'inline-flex' : 'none';
    newDrawerBg.classList.add('is-open');
    document.getElementById('sb-f-titulo').focus();
  }

  function closeNewDrawer() { newDrawerBg.classList.remove('is-open'); newEditingId = null; }

  ['sb-add-btn-activas','sb-add-btn-gestionar'].forEach(function(id){
    var el = document.getElementById(id);
    if (el) el.addEventListener('click', function(){ openNewDrawer(null); });
  });
  document.getElementById('sb-new-cancel-btn').addEventListener('click', closeNewDrawer);
  newDrawerBg.addEventListener('click', function(e){ if (e.target === newDrawerBg) closeNewDrawer(); });

  document.getElementById('sb-new-save-btn').addEventListener('click', function(){
    var titulo     = document.getElementById('sb-f-titulo').value.trim();
    var base       = parseFloat(document.getElementById('sb-f-base').value || 0);
    var incremento = parseFloat(document.getElementById('sb-f-incremento').value || 0);
    var inicio     = document.getElementById('sb-f-inicio').value;
    var cierre     = document.getElementById('sb-f-cierre').value;
    if (!titulo)     { document.getElementById('sb-f-titulo').focus(); return; }
    if (!base)       { document.getElementById('sb-f-base').focus();   return; }
    if (!cierre)     { document.getElementById('sb-f-cierre').focus(); return; }

    var list = load();
    var old  = newEditingId ? list.find(function(s){ return s.id === newEditingId; }) : null;
    var item = {
      id:          newEditingId || ('sb-' + Date.now()),
      folio:       old ? old.folio : genFolio(),
      titulo,
      categoria:   document.getElementById('sb-f-categoria').value,
      descripcion: document.getElementById('sb-f-descripcion').value.trim(),
      base,
      incremento:  incremento || 1,
      reserva:     parseFloat(document.getElementById('sb-f-reserva').value || 0),
      inicio,
      cierre,
      condiciones: document.getElementById('sb-f-condiciones').value.trim(),
      estado:      document.getElementById('sb-f-estado-inicial').value,
      pujas:       old ? (old.pujas || []) : [],
    };
    if (newEditingId) {
      var idx = list.findIndex(function(s){ return s.id === newEditingId; });
      if (idx >= 0) list[idx] = item;
    } else {
      list.push(item);
    }
    save(list);
    renderAll();
    closeNewDrawer();
  });

  document.getElementById('sb-new-delete-btn').addEventListener('click', function(){
    if (!newEditingId) return;
    if (!confirm('¿Eliminar esta subasta permanentemente?')) return;
    save(load().filter(function(s){ return s.id !== newEditingId; }));
    renderAll();
    closeNewDrawer();
  });

  // ────────────────────────────────────────────────────────────────────────
  // DETAIL DRAWER
  // ────────────────────────────────────────────────────────────────────────
  var detailDrawerBg = document.getElementById('sb-detail-drawer-bg');
  var detailId = null;

  function openDetailDrawer(id) {
    detailId = id;
    renderDetailDrawer(id);
    document.getElementById('sb-puja-nombre').value = '';
    document.getElementById('sb-puja-tel').value    = '';
    document.getElementById('sb-puja-monto').value  = '';
    document.getElementById('sb-puja-error').style.display = 'none';
    detailDrawerBg.classList.add('is-open');
  }

  function renderDetailDrawer(id) {
    var list = load();
    var sb   = list.find(function(s){ return s.id === id; });
    if (!sb) return;

    var top    = topBid(sb);
    var price  = top ? parseFloat(top.monto) : parseFloat(sb.base||0);
    var minNext= nextMinBid(sb);
    var nPujas = (sb.pujas||[]).length;
    var isClosed = sb.estado !== 'activa' && sb.estado !== 'programada';

    document.getElementById('sb-detail-title').textContent    = sb.folio || sb.titulo;
    document.getElementById('sb-detail-subtitle').textContent = sb.titulo + (sb.categoria ? ' · ' + sb.categoria : '');
    document.getElementById('sb-dh-label').textContent  = top ? 'Puja más alta' : 'Precio base';
    document.getElementById('sb-dh-amount').textContent = fmt(price);
    document.getElementById('sb-dh-sub').textContent    = top ? ('por ' + top.nombre + (top.telefono ? ' · ' + top.telefono : '')) : ('Incremento mínimo: ' + fmt(sb.incremento));
    document.getElementById('sb-dh-bids').textContent   = nPujas;
    document.getElementById('sb-puja-min-label').textContent = fmt(minNext);

    // Winner banner
    var winnerBanner = document.getElementById('sb-winner-banner');
    if ((sb.estado === 'finalizada' || sb.estado === 'desierta') && top && sb.estado !== 'desierta') {
      winnerBanner.style.display = 'flex';
      document.getElementById('sb-winner-name').textContent  = top.nombre;
      document.getElementById('sb-winner-tel').textContent   = top.telefono || '';
      document.getElementById('sb-winner-price').textContent = fmt(top.monto);
    } else {
      winnerBanner.style.display = 'none';
    }

    // Bids list (sorted high-to-low)
    var sortedPujas = (sb.pujas||[]).slice().sort(function(a,b){ return parseFloat(b.monto)-parseFloat(a.monto); });
    var bidsList = document.getElementById('sb-bids-list');
    if (!sortedPujas.length) {
      bidsList.innerHTML = '<div class="sb-bids-empty">Sin pujas aún. ¡Sé el primero en ofertar!</div>';
    } else {
      bidsList.innerHTML = sortedPujas.map(function(p, i){
        var isWinner = i === 0 && isClosed && sb.estado === 'finalizada';
        return '<div class="sb-bid-row' + (isWinner ? ' sb-bid-row--winner' : '') + '" data-puja-ts="' + escHtml(String(p.ts||'')) + '">'
          + '<div class="sb-bid-row__rank">' + (isWinner ? '🏆' : ('#' + (i+1))) + '</div>'
          + '<div class="sb-bid-row__info">'
          + '<div class="sb-bid-row__name">' + escHtml(p.nombre) + '</div>'
          + '<div class="sb-bid-row__meta">' + (p.telefono ? escHtml(p.telefono) + ' · ' : '') + escHtml(p.ts||'') + '</div>'
          + '</div>'
          + '<span class="sb-bid-row__monto">' + fmt(p.monto) + '</span>'
          + (!isClosed ? '<button class="sb-bid-row__del" data-del-ts="' + escHtml(String(p.ts||'')) + '" title="Eliminar puja"><i class="fa-solid fa-trash"></i></button>' : '')
          + '</div>';
      }).join('');
    }

    // Show/hide form & buttons
    var isActive = sb.estado === 'activa';
    document.getElementById('sb-puja-form').style.display          = isActive ? 'block' : 'none';
    document.getElementById('sb-detail-activar-btn').style.display  = sb.estado === 'programada' ? 'inline-flex' : 'none';
    document.getElementById('sb-detail-finalizar-btn').style.display= isActive ? 'inline-flex' : 'none';
    document.getElementById('sb-detail-cancelar-btn').style.display = (!isClosed) ? 'inline-flex' : 'none';
    document.getElementById('sb-detail-edit-btn').style.display     = (!isClosed) ? 'inline-flex' : 'none';
  }

  // Delete bid
  document.getElementById('sb-bids-list').addEventListener('click', function(e){
    var btn = e.target.closest('[data-del-ts]');
    if (!btn) return;
    var ts = btn.dataset.delTs;
    if (!confirm('¿Eliminar esta puja?')) return;
    var list = load();
    var sb   = list.find(function(s){ return s.id === detailId; });
    if (!sb) return;
    sb.pujas = (sb.pujas||[]).filter(function(p){ return String(p.ts||'') !== ts; });
    save(list);
    renderDetailDrawer(detailId);
    renderAll();
  });

  // Register bid
  document.getElementById('sb-puja-save-btn').addEventListener('click', function(){
    var nombre = document.getElementById('sb-puja-nombre').value.trim();
    var monto  = parseFloat(document.getElementById('sb-puja-monto').value || 0);
    var errEl  = document.getElementById('sb-puja-error');
    errEl.style.display = 'none';
    if (!nombre) { document.getElementById('sb-puja-nombre').focus(); return; }
    var list = load();
    var sb   = list.find(function(s){ return s.id === detailId; });
    if (!sb) return;
    var minReq = nextMinBid(sb);
    if (monto < minReq) {
      errEl.textContent = 'La puja mínima es ' + fmt(minReq) + '. Ingresa un monto mayor o igual.';
      errEl.style.display = 'block';
      document.getElementById('sb-puja-monto').focus();
      return;
    }
    sb.pujas = sb.pujas || [];
    sb.pujas.push({
      nombre,
      telefono: document.getElementById('sb-puja-tel').value.trim(),
      monto,
      ts: new Date().toISOString().replace('T', ' ').slice(0, 19),
    });
    save(list);
    renderDetailDrawer(detailId);
    renderAll();
    document.getElementById('sb-puja-nombre').value = '';
    document.getElementById('sb-puja-tel').value    = '';
    document.getElementById('sb-puja-monto').value  = '';
    // Suggest next min
    var newSb = load().find(function(s){ return s.id === detailId; });
    document.getElementById('sb-puja-min-label').textContent = fmt(nextMinBid(newSb));
  });

  // Control buttons
  document.getElementById('sb-detail-activar-btn').addEventListener('click', function(){
    var list = load(); var sb = list.find(function(s){ return s.id === detailId; });
    if (sb) { sb.estado = 'activa'; save(list); renderDetailDrawer(detailId); renderAll(); }
  });
  document.getElementById('sb-detail-finalizar-btn').addEventListener('click', function(){
    if (!confirm('¿Finalizar la subasta ahora?')) return;
    var list = load(); var sb = list.find(function(s){ return s.id === detailId; });
    if (!sb) return;
    var top = topBid(sb);
    var reserva = parseFloat(sb.reserva || 0);
    sb.estado = (top && (reserva <= 0 || parseFloat(top.monto) >= reserva)) ? 'finalizada' : 'desierta';
    save(list); renderDetailDrawer(detailId); renderAll();
  });
  document.getElementById('sb-detail-cancelar-btn').addEventListener('click', function(){
    if (!confirm('¿Cancelar esta subasta? No se podrá reactivar.')) return;
    var list = load(); var sb = list.find(function(s){ return s.id === detailId; });
    if (sb) { sb.estado = 'cancelada'; save(list); renderDetailDrawer(detailId); renderAll(); }
  });
  document.getElementById('sb-detail-edit-btn').addEventListener('click', function(){
    closeDetailDrawer(); openNewDrawer(detailId);
  });
  function closeDetailDrawer() { detailDrawerBg.classList.remove('is-open'); detailId = null; }
  document.getElementById('sb-detail-close-btn').addEventListener('click', closeDetailDrawer);
  detailDrawerBg.addEventListener('click', function(e){ if (e.target === detailDrawerBg) closeDetailDrawer(); });

  // ── Init ──────────────────────────────────────────────────────────────────
  renderAll();
})();
</script>
</body>
</html>"""
