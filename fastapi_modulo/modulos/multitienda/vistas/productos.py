from __future__ import annotations


def productos_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Productos</title>
  <style>
    :root {
      --mp-surface: var(--content-bg, #ffffff);
      --mp-surface-soft: color-mix(in srgb, var(--content-bg, #ffffff) 88%, var(--page-bg, #f4f6fb) 12%);
      --mp-border: var(--field-border, #d1d5db);
      --mp-border-soft: color-mix(in srgb, var(--field-border, #d1d5db) 68%, #ffffff 32%);
      --mp-text: var(--body-text, #1f2937);
      --mp-muted: color-mix(in srgb, var(--body-text, #1f2937) 64%, #ffffff 36%);
      --mp-accent: var(--button-bg, #2d7bb5);
      --mp-accent-contrast: var(--button-text, #ffffff);
      --mp-focus: var(--field-focus, var(--button-bg, #2d7bb5));
      --mp-success-bg: color-mix(in srgb, #16a34a 14%, var(--content-bg, #ffffff) 86%);
      --mp-success-border: color-mix(in srgb, #16a34a 30%, transparent);
      --mp-success-text: color-mix(in srgb, #16a34a 76%, var(--body-text, #1f2937) 24%);
      --mp-danger-text: color-mix(in srgb, #dc2626 78%, var(--body-text, #1f2937) 22%);
      --mp-overlay: color-mix(in srgb, var(--mp-text) 55%, transparent);
      --mp-shadow: color-mix(in srgb, var(--mp-text) 16%, transparent);
    }
    html, body { margin:0; padding:0; font-family:system-ui,-apple-system,sans-serif; background:var(--mp-surface); color:var(--mp-text); font-size:14px; }
    .page { padding:0; }

    /* ══════════════════════════════
       TOOLBAR COMPARTIDO
    ══════════════════════════════ */
    .pv-toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 20px;
      border-bottom: 1px solid var(--mp-border-soft);
      background: var(--mp-surface);
      flex-wrap: wrap;
    }
    .pv-toolbar-left   { display:flex; align-items:center; gap:10px; flex-shrink:0; }
    .pv-toolbar-center { flex:1; display:flex; justify-content:center; }
    .pv-toolbar-right  { display:flex; align-items:center; gap:6px; flex-shrink:0; font-size:.85rem; color:var(--mp-muted); white-space:nowrap; }

    .btn-nuevo, .btn-guardar {
      padding: 7px 14px;
      background: var(--mp-accent);
      color: var(--mp-accent-contrast);
      border: none;
      border-radius: 5px;
      font-size: .875rem;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-nuevo:hover, .btn-guardar:hover { background: var(--institutional-button-hover, var(--mp-accent)); }

    .btn-descartar {
      padding: 7px 14px;
      background: var(--mp-surface);
      color: var(--mp-text);
      border: 1px solid var(--mp-border);
      border-radius: 5px;
      font-size: .875rem;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-descartar:hover { background: color-mix(in srgb, var(--mp-accent) 10%, var(--mp-surface) 90%); }

    .btn-eliminar {
      padding: 7px 14px;
      background: var(--mp-surface);
      color: var(--mp-danger-text);
      border: 1px solid color-mix(in srgb, var(--mp-danger-text) 30%, var(--mp-border));
      border-radius: 5px;
      font-size: .875rem;
      font-weight: 600;
      cursor: pointer;
      transition: background .14s;
    }
    .btn-eliminar:hover:not(:disabled) { background: color-mix(in srgb, var(--mp-danger-text) 8%, var(--mp-surface)); }
    .btn-eliminar:disabled { opacity: .35; cursor: not-allowed; }

    /* ── Confirm dialog ── */
    .pv-confirm-overlay {
      position: fixed; inset: 0; z-index: 1200;
      background: rgba(15,23,42,.48);
      display: flex; align-items: center; justify-content: center; padding: 20px;
    }
    .pv-confirm-overlay[hidden] { display: none; }
    .pv-confirm-card {
      width: min(400px, 100%);
      background: var(--mp-surface);
      border-radius: 14px;
      padding: 22px;
      box-shadow: 0 20px 56px rgba(15,23,42,.18);
      display: grid; gap: 12px;
    }
    .pv-confirm-title { margin: 0; font-size: 1rem; font-weight: 800; color: var(--mp-danger-text); }
    .pv-confirm-msg   { margin: 0; font-size: .88rem; color: var(--mp-muted); }
    .pv-confirm-actions { display: flex; gap: 10px; justify-content: flex-end; }

    .btn-publicar {
      padding: 7px 16px;
      border-radius: 5px;
      font-size: .875rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--mp-border);
      background: var(--mp-surface-soft);
      color: var(--mp-muted);
      transition: all .15s;
    }
    .btn-publicar.publicado {
      background: var(--mp-success-bg);
      border-color: var(--mp-success-border);
      color: var(--mp-success-text);
    }
    .btn-publicar:hover { filter: brightness(.96); }

    .pv-breadcrumb { font-size:.875rem; color:var(--mp-text); }
    .pv-breadcrumb a { color:var(--mp-accent); text-decoration:none; cursor:pointer; }
    .pv-breadcrumb a:hover { text-decoration:underline; }
    .pv-breadcrumb-sep { margin:0 4px; color:color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%); }
    .pv-page-title { font-size:.82rem; color:var(--mp-muted); display:flex; align-items:center; gap:5px; }
    .gear-btn { background:none; border:none; cursor:pointer; color:color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%); font-size:.9rem; padding:0; }
    .gear-btn:hover { color:var(--mp-text); }

    .pv-search-wrap {
      display: flex;
      align-items: center;
      border: 1px solid var(--mp-border);
      border-radius: 20px;
      padding: 5px 12px;
      gap: 6px;
      width: 340px;
      max-width: 100%;
      background: var(--field-color, var(--mp-surface));
    }
    .pv-search-wrap:focus-within { border-color:var(--mp-focus); box-shadow:0 0 0 3px color-mix(in srgb, var(--mp-focus) 16%, transparent); }
    .pv-search-icon { color:color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%); }
    .pv-search-input { border:none; outline:none; flex:1; font-size:.875rem; background:transparent; color:var(--field-text, var(--mp-text)); }
    .pv-search-input::placeholder { color:color-mix(in srgb, var(--field-text, var(--mp-text)) 38%, #ffffff 62%); }
    .pv-search-drop { background:none; border:none; cursor:pointer; color:var(--mp-muted); padding:0 2px; font-size:.75rem; }

    .pv-pag-btn { background:none; border:1px solid var(--mp-border); border-radius:4px; cursor:pointer; padding:3px 8px; font-size:.95rem; color:var(--mp-text); }
    .pv-pag-btn:hover:not(:disabled) { background:color-mix(in srgb, var(--mp-accent) 10%, var(--mp-surface) 90%); }
    .pv-pag-btn:disabled { opacity:.35; cursor:default; }

    /* ══════════════════════════════
       LISTA
    ══════════════════════════════ */
    .pv-table-wrap { overflow-x:auto; }
    .pv-table { width:100%; border-collapse:collapse; }
    .pv-table thead tr { border-bottom:2px solid var(--mp-border-soft); }
    .pv-table th {
      padding:9px 12px; text-align:left;
      font-size:.82rem; font-weight:700; color:var(--mp-text);
      white-space:nowrap; user-select:none;
    }
    .pv-table th.col-num  { text-align:right; }
    .pv-table th.col-cfg  { text-align:right; width:32px; }
    .pv-table th.col-cb   { width:32px; padding-right:4px; }
    .pv-table th.col-star { width:28px; padding:9px 4px; }
    .pv-table th.sortable { cursor:pointer; }
    .pv-table th.sortable:hover { color:var(--mp-text); }
    .pv-table th .sort-arrow { margin-left:3px; color:color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%); font-size:.7rem; }
    .pv-table tbody tr { border-bottom:1px solid color-mix(in srgb, var(--mp-border-soft) 60%, #ffffff 40%); cursor:pointer; }
    .pv-table tbody tr:hover td { background:color-mix(in srgb, var(--mp-accent) 8%, var(--mp-surface) 92%); }
    .pv-table tbody tr.selected td { background:color-mix(in srgb, var(--mp-accent) 14%, var(--mp-surface) 86%); }
    .pv-table td { padding:9px 12px; font-size:.875rem; color:var(--mp-text); vertical-align:middle; }
    .pv-table td.col-num  { text-align:right; font-variant-numeric:tabular-nums; }
    .pv-table td.col-cb   { width:32px; padding-right:4px; }
    .pv-table td.col-star { width:28px; padding:9px 4px; }
    .cb-input  { width:15px; height:15px; accent-color:var(--mp-accent); cursor:pointer; }
    .star-btn  { background:none; border:none; cursor:pointer; color:var(--mp-border); font-size:1rem; padding:0; line-height:1; }
    .star-btn.active, .star-btn:hover { color:var(--mp-accent); }
    .tag-badge { display:inline-block; padding:1px 7px; border-radius:10px; font-size:.75rem; font-weight:500; background:color-mix(in srgb, var(--mp-accent) 12%, var(--mp-surface) 88%); color:var(--mp-text); margin:1px 2px; }
    .col-settings-btn { background:none; border:none; cursor:pointer; color:var(--mp-muted); font-size:1rem; padding:2px 4px; border-radius:4px; }
    .col-settings-btn:hover { background:color-mix(in srgb, var(--mp-accent) 10%, var(--mp-surface) 90%); }
    .pv-empty { text-align:center; padding:60px 20px; color:color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%); font-size:.9rem; }

    /* ══════════════════════════════
       FORM
    ══════════════════════════════ */
    #pf-view { background:var(--mp-surface-soft); min-height:calc(100vh - 51px); }

    .pf-body {
      display: grid;
      grid-template-columns: 1fr 200px;
      gap: 24px;
      padding: 24px 24px 48px;
      max-width: 1100px;
    }
    @media (max-width:700px) { .pf-body { grid-template-columns:1fr; } }

    /* Nombre del producto */
    .pf-nombre-wrap { margin-bottom: 20px; }
    .pf-nombre-input {
      width: 100%;
      font-size: 1.45rem;
      font-weight: 700;
      color: var(--mp-text);
      border: none;
      border-bottom: 2px solid transparent;
      background: transparent;
      outline: none;
      padding: 4px 0;
      transition: border-color .15s;
      box-sizing: border-box;
    }
    .pf-nombre-input:focus { border-bottom-color: var(--mp-focus); }
    .pf-nombre-input::placeholder { color:var(--mp-border); font-weight:400; }

    /* Notebook */
    .pf-notebook {
      background: var(--mp-surface);
      border: 1px solid var(--mp-border-soft);
      border-radius: 10px;
      overflow: hidden;
    }
    .pf-notebook-tabs {
      display: flex;
      border-bottom: 1px solid var(--mp-border-soft);
      background: var(--mp-surface-soft);
      flex-wrap: wrap;
    }
    .pf-nb-tab {
      padding: 10px 20px;
      font-size: .875rem;
      font-weight: 600;
      color: var(--mp-muted);
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      cursor: pointer;
      transition: color .15s, border-color .15s;
      white-space: nowrap;
    }
    .pf-nb-tab:hover { color:var(--mp-text); }
    .pf-nb-tab.active { color:var(--mp-accent); border-bottom-color:var(--mp-accent); background:var(--mp-surface); }
    .pf-nb-panel { padding:20px; }
    .pf-nb-panel[hidden] { display:none !important; }

    /* Campos */
    .pf-field { display:flex; flex-direction:column; gap:5px; margin-bottom:16px; }
    .pf-field label { font-size:.8rem; font-weight:600; color:var(--mp-text); }
    .pf-input, .pf-select, .pf-textarea {
      padding: 7px 10px;
      border: 1px solid var(--mp-border);
      border-radius: 6px;
      font-size: .875rem;
      background: var(--field-color, var(--mp-surface));
      outline: none;
      color: var(--field-text, var(--mp-text));
      transition: border-color .15s;
    }
    .pf-input:focus, .pf-select:focus, .pf-textarea:focus { border-color:var(--mp-focus); box-shadow:0 0 0 3px color-mix(in srgb, var(--mp-focus) 16%, transparent); }
    .pf-textarea { min-height:80px; resize:vertical; }
    .pf-row-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    .pf-row-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }
    @media (max-width:600px) { .pf-row-2, .pf-row-3 { grid-template-columns:1fr; } }

    .pf-section-title {
      font-size:.8rem; font-weight:700; text-transform:uppercase;
      letter-spacing:.06em; color:color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%); margin:20px 0 10px;
    }
    .pf-section-title:first-child { margin-top:0; }

    /* ── Layout dos columnas (Información general) ── */
    .pf-ig-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0 32px;
      padding: 4px 0;
    }
    @media (max-width:800px) { .pf-ig-grid { grid-template-columns:1fr; } }

    .pf-ig-row {
      display: grid;
      grid-template-columns: 160px 1fr;
      gap: 8px;
      align-items: start;
      padding: 9px 0;
      border-bottom: 1px solid color-mix(in srgb, var(--mp-border-soft) 60%, #ffffff 40%);
    }
    .pf-ig-row:last-child { border-bottom:none; }
    .pf-ig-label {
      font-size: .875rem;
      font-weight: 600;
      color: var(--mp-text);
      padding-top: 7px;
      line-height: 1.3;
    }
    .pf-ig-val { display:flex; flex-direction:column; gap:4px; }

    .pf-hint {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 14px; height: 14px;
      border-radius: 50%;
      background: color-mix(in srgb, var(--mp-accent) 12%, var(--mp-surface) 88%);
      color: var(--mp-muted);
      font-size: .65rem;
      font-weight: 700;
      cursor: help;
      vertical-align: middle;
      margin-left: 2px;
    }
    .pf-ig-hint {
      font-size: .78rem;
      color: color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%);
      font-style: italic;
      margin: 2px 0 0;
    }

    /* Radios */
    .pf-radio-group { display:flex; align-items:center; gap:16px; padding-top:6px; flex-wrap:wrap; }
    .pf-radio-label { display:flex; align-items:center; gap:5px; font-size:.875rem; cursor:pointer; color:var(--mp-text); }
    .pf-radio { accent-color:var(--mp-accent); width:15px; height:15px; cursor:pointer; }

    /* Input de dinero */
    .pf-money-input { font-variant-numeric:tabular-nums; }

    /* Tag input de impuestos */
    .pf-tax-wrap {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 4px;
      border: 1px solid var(--mp-border);
      border-radius: 6px;
      padding: 4px 8px;
      background: var(--field-color, var(--mp-surface));
      min-height: 34px;
      cursor: text;
    }
    .pf-tax-wrap:focus-within { border-color:var(--mp-focus); box-shadow:0 0 0 3px color-mix(in srgb, var(--mp-focus) 16%, transparent); }
    .pf-tax-tag {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      background: color-mix(in srgb, var(--mp-accent) 12%, var(--mp-surface) 88%);
      border-radius: 10px;
      font-size: .78rem;
      font-weight: 600;
      color: var(--mp-text);
      white-space: nowrap;
    }
    .pf-tax-remove {
      background: none; border: none; cursor: pointer;
      color: color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%); font-size: .75rem; padding: 0 1px;
      line-height: 1;
    }
    .pf-tax-remove:hover { color:var(--mp-danger-text); }
    .pf-tax-input {
      border: none; outline: none; font-size: .82rem;
      background: transparent; width: 80px; min-width:60px; color:var(--mp-text);
    }
    .pf-tax-calc { font-size:.78rem; color:var(--mp-muted); margin:2px 0 0; }

    /* ── Ventas ── */
    .pf-ventas-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0 40px;
    }
    @media (max-width:800px) { .pf-ventas-grid { grid-template-columns:1fr; } }

    .pf-ventas-section-title {
      font-size: .78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .07em;
      color: var(--mp-text);
      margin: 16px 0 6px;
    }
    .pf-ventas-section-title:first-child { margin-top: 4px; }
    .pf-ventas-divider { border-bottom: 1px solid var(--mp-border-soft); margin-bottom: 4px; }

    .pf-ventas-desc {
      width: 100%;
      box-sizing: border-box;
      min-height: 90px;
      resize: vertical;
      margin-top: 8px;
      font-family: inherit;
    }

    /* Multimedia */
    .pf-media-area { padding: 12px 0; }
    .pf-media-list { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:10px; }
    .pf-media-thumb {
      position: relative;
      width: 80px; height: 80px;
      border: 1px solid var(--mp-border-soft);
      border-radius: 8px;
      overflow: hidden;
      background: var(--mp-surface-soft);
    }
    .pf-media-thumb img { width:100%; height:100%; object-fit:cover; }
    .pf-media-thumb .pf-media-del {
      position: absolute; top:3px; right:3px;
      background: var(--mp-overlay); color:var(--mp-accent-contrast);
      border: none; border-radius: 50%;
      width:18px; height:18px; font-size:.7rem;
      cursor: pointer; display:flex; align-items:center; justify-content:center;
    }
    .pf-media-add-btn {
      padding: 7px 16px;
      background: color-mix(in srgb, var(--mp-accent) 10%, var(--mp-surface) 90%);
      color: var(--mp-text);
      border: 1px solid var(--mp-border);
      border-radius: 6px;
      font-size: .875rem;
      font-weight: 600;
      cursor: pointer;
    }
    .pf-media-add-btn:hover { background: color-mix(in srgb, var(--mp-accent) 16%, var(--mp-surface) 84%); }

    /* Toggle switch */
    .pf-toggle { position:relative; display:inline-flex; align-items:center; cursor:pointer; }
    .pf-toggle input { opacity:0; width:0; height:0; position:absolute; }
    .pf-toggle-track {
      width:40px; height:22px; background:var(--mp-border); border-radius:11px;
      transition:background .2s; display:flex; align-items:center; padding:2px;
    }
    .pf-toggle input:checked + .pf-toggle-track { background:var(--mp-accent); }
    .pf-toggle-thumb {
      width:18px; height:18px; background:var(--mp-surface); border-radius:50%;
      box-shadow:0 1px 3px var(--mp-shadow);
      transition:transform .2s;
    }
    .pf-toggle input:checked + .pf-toggle-track .pf-toggle-thumb { transform:translateX(18px); }

    /* RTE */
    .pf-rte-wrap { border:1px solid var(--mp-border); border-radius:6px; overflow:hidden; }
    .pf-rte-wrap:focus-within { border-color:var(--mp-focus); box-shadow:0 0 0 3px color-mix(in srgb, var(--mp-focus) 16%, transparent); }
    .pf-rte-toolbar {
      display:flex; align-items:center; gap:2px;
      padding:5px 8px; border-bottom:1px solid var(--mp-border-soft); background:var(--mp-surface-soft);
      opacity:0; transition:opacity .15s; pointer-events:none;
    }
    .pf-rte-wrap:focus-within .pf-rte-toolbar { opacity:1; pointer-events:all; }
    .pf-rte-btn {
      width:28px; height:26px; display:inline-flex; align-items:center; justify-content:center;
      border:none; background:none; border-radius:4px; cursor:pointer; font-size:.85rem; color:var(--mp-text);
    }
    .pf-rte-btn:hover { background:color-mix(in srgb, var(--mp-accent) 10%, var(--mp-surface) 90%); }
    .pf-rte-editor {
      min-height:120px; padding:10px 12px;
      font-size:.875rem; color:var(--mp-text); line-height:1.6;
      outline:none; background:var(--field-color, var(--mp-surface));
    }
    .pf-rte-editor:empty::before {
      content: attr(data-placeholder);
      color: color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%); pointer-events:none;
    }

    /* Notas internas */
    .pf-notas-section { margin-top:24px; border-top:1px solid var(--mp-border-soft); padding-top:16px; }
    .pf-notas-title {
      font-size:.78rem; font-weight:700; text-transform:uppercase;
      letter-spacing:.07em; color:var(--mp-text); margin:0 0 10px;
    }
    .pf-notas-textarea {
      width: 100%; box-sizing:border-box;
      min-height: 90px; resize: vertical;
      border: none; outline: none;
      font-size: .875rem; color: var(--mp-muted);
      font-style: italic; background: transparent;
      font-family: inherit;
    }
    .pf-notas-textarea::placeholder { color:color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%); }

    /* Foto principal */
    .pf-photo-col { display:flex; flex-direction:column; align-items:center; gap:10px; padding-top:4px; }
    .pf-photo-box {
      width: 160px;
      height: 160px;
      border: 2px dashed var(--mp-border);
      border-radius: 10px;
      overflow: hidden;
      cursor: pointer;
      background: var(--mp-surface-soft);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: border-color .15s;
    }
    .pf-photo-box:hover { border-color:var(--mp-accent); }
    .pf-photo-box img { width:100%; height:100%; object-fit:cover; }
    .pf-photo-hint { font-size:.75rem; color:color-mix(in srgb, var(--mp-text) 38%, #ffffff 62%); text-align:center; line-height:1.4; }
    .pf-photo-actions { display:flex; gap:6px; }
    .pf-photo-btn {
      padding:4px 10px; border:1px solid var(--mp-border); border-radius:5px;
      background:var(--mp-surface); font-size:.78rem; cursor:pointer; color:var(--mp-text);
    }
    .pf-photo-btn:hover { background:color-mix(in srgb, var(--mp-accent) 10%, var(--mp-surface) 90%); }
  </style>
</head>
<body>
__BACKEND_SHARED_SIDEBAR_HTML__
<main class="page">

  <!-- ══════════ VISTA LISTA ══════════ -->
  <div id="pv-view">
    <div class="pv-toolbar">
      <div class="pv-toolbar-left">
        <button class="btn-nuevo" id="pv-nuevo-btn" type="button">Nuevo</button>
        <button class="btn-eliminar" id="pv-eliminar-btn" type="button" disabled>Eliminar</button>
        <div>
          <div class="pv-breadcrumb">
            <a id="pv-breadcrumb-tiendas">Tiendas</a>
            <span class="pv-breadcrumb-sep">/</span>
            <span id="pv-breadcrumb-tienda">Tu Negocio VALE</span>
          </div>
          <div class="pv-page-title">
            Productos de la tienda
            <button class="gear-btn" type="button" title="Configuración">⚙</button>
          </div>
        </div>
      </div>
      <div class="pv-toolbar-center">
        <div class="pv-search-wrap">
          <span class="pv-search-icon">🔍</span>
          <input class="pv-search-input" id="pv-search" type="text" placeholder="Buscar..." />
          <button class="pv-search-drop" type="button">▾</button>
        </div>
      </div>
      <div class="pv-toolbar-right">
        <span id="pv-pag-label">0 / 0</span>
        <button class="pv-pag-btn" id="pv-prev-btn" type="button" disabled>&#8249;</button>
        <button class="pv-pag-btn" id="pv-next-btn" type="button" disabled>&#8250;</button>
      </div>
    </div>

    <div class="pv-table-wrap">
      <table class="pv-table">
        <thead>
          <tr>
            <th class="col-cb"><input class="cb-input" type="checkbox" id="pv-select-all" title="Seleccionar todo" /></th>
            <th class="col-star"></th>
            <th class="sortable" data-col="nombre">Nombre del producto <span class="sort-arrow">↕</span></th>
            <th class="sortable" data-col="referencia">Referencia interna <span class="sort-arrow">↕</span></th>
            <th>Etiquetas</th>
            <th class="col-num sortable" data-col="precio">Precio de venta <span class="sort-arrow">↕</span></th>
            <th class="col-num sortable" data-col="costo">Costo <span class="sort-arrow">↕</span></th>
            <th class="col-cfg"><button class="col-settings-btn" type="button" title="Columnas">⇌</button></th>
          </tr>
        </thead>
        <tbody id="pv-tbody"></tbody>
      </table>
      <div id="pv-empty" class="pv-empty" hidden>
        No hay productos registrados. Haz clic en <strong>Nuevo</strong> para agregar el primero.
      </div>
    </div>
  </div>

  <!-- ══════════ VISTA FORM ══════════ -->
  <div id="pf-view" hidden>

    <!-- Toolbar form -->
    <div class="pv-toolbar">
      <div class="pv-toolbar-left">
        <button class="btn-guardar" id="pf-guardar-btn" type="button">Guardar</button>
        <button class="btn-descartar" id="pf-descartar-btn" type="button">Descartar</button>
        <button class="btn-eliminar" id="pf-eliminar-btn" type="button" style="display:none">Eliminar</button>
        <div>
          <div class="pv-breadcrumb">
            <a id="pf-breadcrumb-back">Productos</a>
            <span class="pv-breadcrumb-sep">/</span>
            <span id="pf-breadcrumb-nombre">Nuevo</span>
          </div>
          <div class="pv-page-title">Producto</div>
        </div>
      </div>
      <div class="pv-toolbar-right">
        <button class="btn-publicar" id="pf-publicar-btn" type="button">Sin publicar</button>
      </div>
    </div>

    <!-- Cuerpo del form -->
    <div class="pf-body">

      <!-- Columna principal -->
      <div>
        <!-- Nombre -->
        <div class="pf-nombre-wrap">
          <input class="pf-nombre-input" id="pf-nombre" type="text" placeholder="Nombre del producto" />
        </div>

        <!-- Notebook -->
        <div class="pf-notebook">
          <div class="pf-notebook-tabs" role="tablist">
            <button class="pf-nb-tab active" role="tab" aria-selected="true"
                    aria-controls="pf-panel-1" id="pf-tab-1" type="button">Información general</button>
            <button class="pf-nb-tab" role="tab" aria-selected="false"
                    aria-controls="pf-panel-2" id="pf-tab-2" type="button">Ventas</button>
            <button class="pf-nb-tab" role="tab" aria-selected="false"
                    aria-controls="pf-panel-3" id="pf-tab-3" type="button">Características del producto</button>
            <button class="pf-nb-tab" role="tab" aria-selected="false"
                    aria-controls="pf-panel-4" id="pf-tab-4" type="button">Detalles del artículo</button>
            <button class="pf-nb-tab" role="tab" aria-selected="false"
                    aria-controls="pf-panel-5" id="pf-tab-5" type="button">Especificaciones</button>
            <button class="pf-nb-tab" role="tab" aria-selected="false"
                    aria-controls="pf-panel-6" id="pf-tab-6" type="button">Condiciones especiales</button>
          </div>

          <!-- ── Información general ── -->
          <div class="pf-nb-panel" id="pf-panel-1" role="tabpanel" aria-labelledby="pf-tab-1">

            <!-- Grid dos columnas estilo Odoo -->
            <div class="pf-ig-grid">

              <!-- ── Columna izquierda ── -->
              <div class="pf-ig-col">

                <div class="pf-ig-row">
                  <label class="pf-ig-label">Tipo de producto <span class="pf-hint" title="Determina cómo se gestiona el inventario">?</span></label>
                  <div class="pf-ig-val pf-radio-group">
                    <label class="pf-radio-label">
                      <input type="radio" name="pf-tipo-producto" value="bienes" id="pf-tipo-bienes" checked class="pf-radio" />
                      Bienes
                    </label>
                    <label class="pf-radio-label">
                      <input type="radio" name="pf-tipo-producto" value="servicio" id="pf-tipo-servicio" class="pf-radio" />
                      Servicio
                    </label>
                    <label class="pf-radio-label">
                      <input type="radio" name="pf-tipo-producto" value="combo" id="pf-tipo-combo" class="pf-radio" />
                      Combo
                    </label>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-politica-facturacion">Política de facturación <span class="pf-hint" title="Define cuándo se factura este producto">?</span></label>
                  <div class="pf-ig-val">
                    <select class="pf-input" id="pf-politica-facturacion">
                      <option value="cantidad_ordenada">Cantidad ordenada</option>
                      <option value="cantidad_entregada">Cantidad entregada</option>
                      <option value="anticipo">Anticipo</option>
                    </select>
                    <p class="pf-ig-hint" id="pf-politica-hint">Puede facturar los bienes antes de entregarlos.</p>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-unidad">Unidad de medida</label>
                  <div class="pf-ig-val">
                    <select class="pf-input" id="pf-unidad">
                      <option value="pieza">Pieza</option>
                      <option value="kg">Kilogramo</option>
                      <option value="litro">Litro</option>
                      <option value="metro">Metro</option>
                      <option value="caja">Caja</option>
                      <option value="par">Par</option>
                    </select>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-etiquetas">Etiquetas</label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-etiquetas" type="text" placeholder="Ej. nuevo, oferta, temporada" />
                  </div>
                </div>

              </div><!-- /col izq -->

              <!-- ── Columna derecha ── -->
              <div class="pf-ig-col">

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-precio">Precio de venta <span class="pf-hint" title="Precio al público">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input pf-money-input" id="pf-precio" type="number" min="0" step="0.01" placeholder="0.00" />
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label">Impuesto de ventas <span class="pf-hint" title="Impuestos aplicados al precio de venta">?</span></label>
                  <div class="pf-ig-val">
                    <div class="pf-tax-wrap" id="pf-tax-venta-wrap" data-key="taxVenta">
                      <div class="pf-tax-tags" id="pf-tax-venta-tags"></div>
                      <input class="pf-tax-input" id="pf-tax-venta-input" type="text" placeholder="Agregar %" />
                    </div>
                    <p class="pf-tax-calc" id="pf-tax-venta-calc"></p>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-costo">Costo <span class="pf-hint" title="Costo de adquisición del producto">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input pf-money-input" id="pf-costo" type="number" min="0" step="0.01" placeholder="0.00" />
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label">Impuestos de compra <span class="pf-hint" title="Impuestos aplicados al costo de compra">?</span></label>
                  <div class="pf-ig-val">
                    <div class="pf-tax-wrap" id="pf-tax-compra-wrap" data-key="taxCompra">
                      <div class="pf-tax-tags" id="pf-tax-compra-tags"></div>
                      <input class="pf-tax-input" id="pf-tax-compra-input" type="text" placeholder="Agregar %" />
                    </div>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-categoria">Categoría</label>
                  <div class="pf-ig-val">
                    <select class="pf-input" id="pf-categoria">
                      <option value="">Sin categoría</option>
                    </select>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-referencia">Referencia</label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-referencia" type="text" placeholder="" />
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-codigo-barras">Código de barras</label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-codigo-barras" type="text" placeholder="" />
                  </div>
                </div>

              </div><!-- /col der -->
            </div><!-- /pf-ig-grid -->

            <!-- NOTAS INTERNAS -->
            <div class="pf-notas-section">
              <p class="pf-notas-title">NOTAS INTERNAS</p>
              <textarea class="pf-notas-textarea" id="pf-notas-internas" placeholder="Esta nota es solo para fines internos."></textarea>
            </div>

          </div><!-- /pf-panel-1 -->

          <!-- ── Ventas ── -->
          <div class="pf-nb-panel" id="pf-panel-2" role="tabpanel" aria-labelledby="pf-tab-2" hidden>
            <div class="pf-ventas-grid">

              <!-- ── Columna izquierda ── -->
              <div>

                <p class="pf-ventas-section-title">VENTAS ADICIONALES Y VENTAS CRUZADAS</p>
                <div class="pf-ventas-divider"></div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-productos-opcionales">Productos opcionales <span class="pf-hint" title="Se recomiendan al hacer clic en 'Agregar al carrito' o al cotizar">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-productos-opcionales" type="text"
                           placeholder="Recomendar al "Agregar al carrito" o a la cotización…" />
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-accesorios">Accesorios <span class="pf-hint" title="Accesorios sugeridos en el carrito de comercio electrónico">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-accesorios" type="text"
                           placeholder="Accesorios sugeridos en el carrito de comercio electrónico…" />
                  </div>
                </div>

                <div class="pf-ig-row" style="border-bottom:none;">
                  <label class="pf-ig-label" for="pf-productos-alternos">Productos alternos <span class="pf-hint" title="Aparecen en la parte inferior de las páginas del producto">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-productos-alternos" type="text"
                           placeholder="Aparecen en la parte inferior de las páginas del producto…" />
                  </div>
                </div>

                <p class="pf-ventas-section-title" style="margin-top:28px;">MEDIOS DE COMERCIO ELECTRÓNICO</p>
                <div class="pf-ventas-divider"></div>

                <div class="pf-media-area">
                  <div class="pf-media-list" id="pf-media-list"></div>
                  <button class="pf-media-add-btn" id="pf-media-add-btn" type="button">Agregar archivo multimedia</button>
                  <input type="file" id="pf-media-input" accept="image/*,video/*,.pdf" multiple style="display:none" />
                </div>

                <p class="pf-ventas-section-title" style="margin-top:28px;">DESCRIPCIÓN DE LA COTIZACIÓN</p>
                <div class="pf-ventas-divider"></div>
                <textarea class="pf-input pf-ventas-desc" id="pf-desc-cotizacion"
                          placeholder="Esta nota se agrega a las órdenes de ventas y facturas."></textarea>

              </div>

              <!-- ── Columna derecha ── -->
              <div>

                <p class="pf-ventas-section-title">TIENDA DE COMERCIO ELECTRÓNICO</p>
                <div class="pf-ventas-divider"></div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-ecom-etiquetas">Etiquetas</label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-ecom-etiquetas" type="text" placeholder="" />
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-ecom-publicado">Está publicado</label>
                  <div class="pf-ig-val" style="padding-top:7px;">
                    <input type="checkbox" id="pf-ecom-publicado" class="cb-input" />
                  </div>
                </div>

                <div class="pf-ig-row" style="border-bottom:none;">
                  <label class="pf-ig-label" for="pf-ecom-categorias">Categorías <span class="pf-hint" title="Categorías visibles en la tienda en línea">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-ecom-categorias" type="text" placeholder="" />
                  </div>
                </div>

                <p class="pf-ventas-section-title" style="margin-top:28px;">DESCRIPCIÓN DE COMERCIO ELECTRÓNICO</p>
                <div class="pf-ventas-divider"></div>
                <textarea class="pf-input pf-ventas-desc" id="pf-desc-ecom"
                          placeholder="Una descripción detallada y con formato para promocionar su producto en la tienda en línea."></textarea>

              </div>

            </div>
          </div><!-- /pf-panel-2 -->

          <!-- ── Características del producto ── -->
          <div class="pf-nb-panel" id="pf-panel-3" role="tabpanel" aria-labelledby="pf-tab-3" hidden>

            <div class="pf-ig-row">
              <label class="pf-ig-label" for="pf-nuevo">Nuevo</label>
              <div class="pf-ig-val" style="padding-top:7px;">
                <input type="checkbox" id="pf-nuevo" class="cb-input" />
              </div>
            </div>

            <div class="pf-ig-row">
              <label class="pf-ig-label" for="pf-desc-corta">Descripción corta</label>
              <div class="pf-ig-val">
                <input class="pf-input" id="pf-desc-corta" type="text" placeholder="" />
              </div>
            </div>

            <div class="pf-ig-row" style="border-bottom:none;align-items:start;">
              <label class="pf-ig-label" for="pf-desc-larga" style="padding-top:7px;">Descripción larga</label>
              <div class="pf-ig-val">
                <textarea class="pf-input" id="pf-desc-larga" rows="5"
                          style="resize:vertical;font-family:inherit;" placeholder=""></textarea>
              </div>
            </div>

          </div><!-- /pf-panel-3 -->

          <!-- ── Detalles del artículo ── -->
          <div class="pf-nb-panel" id="pf-panel-4" role="tabpanel" aria-labelledby="pf-tab-4" hidden>

            <div class="pf-ig-row">
              <label class="pf-ig-label" for="pf-mostrar-detalles">
                Mostrar pestaña Detalles del artículo en la web
                <span class="pf-hint" title="Muestra u oculta esta sección en la página del producto en la tienda">?</span>
              </label>
              <div class="pf-ig-val" style="padding-top:6px;">
                <label class="pf-toggle">
                  <input type="checkbox" id="pf-mostrar-detalles" checked />
                  <span class="pf-toggle-track"><span class="pf-toggle-thumb"></span></span>
                </label>
              </div>
            </div>

            <div class="pf-ig-row" style="border-bottom:none;align-items:start;">
              <label class="pf-ig-label" style="padding-top:10px;">
                Detalles del producto (producto)
                <span class="pf-hint" title="Descripción enriquecida visible en la ficha del producto">?</span>
              </label>
              <div class="pf-ig-val" style="flex:1;">
                <div class="pf-rte-wrap" id="pf-detalles-rte-wrap">
                  <div class="pf-rte-toolbar" id="pf-detalles-toolbar">
                    <button type="button" class="pf-rte-btn" data-cmd="insertTable"   title="Tabla">⊞</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertUnorderedList" title="Lista">≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertOrderedList"   title="Lista numerada"><span style="font-size:.7rem;font-weight:700;">1.</span>≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertCheckbox" title="Casilla">☑</button>
                    <button type="button" class="pf-rte-btn" data-cmd="createLink"    title="Enlace">⛓</button>
                    <button type="button" class="pf-rte-btn" data-cmd="bold"          title="Negrita" style="font-weight:700;">B</button>
                    <button type="button" class="pf-rte-btn" data-cmd="italic"        title="Cursiva" style="font-style:italic;">I</button>
                    <button type="button" class="pf-rte-btn" data-cmd="removeFormat"  title="Limpiar formato" style="color:var(--mp-muted);">✕</button>
                  </div>
                  <div class="pf-rte-editor" id="pf-detalles-editor"
                       contenteditable="true"
                       data-placeholder='Escriba "/" para acceder a los comandos'></div>
                </div>
              </div>
            </div>

          </div><!-- /pf-panel-4 -->

          <!-- ── Especificaciones ── -->
          <div class="pf-nb-panel" id="pf-panel-5" role="tabpanel" aria-labelledby="pf-tab-5" hidden>

            <div class="pf-ig-row">
              <label class="pf-ig-label" for="pf-mostrar-especificaciones">
                Mostrar pestaña Especificaciones en la web
                <span class="pf-hint" title="Muestra u oculta esta sección en la página del producto en la tienda">?</span>
              </label>
              <div class="pf-ig-val" style="padding-top:6px;">
                <label class="pf-toggle">
                  <input type="checkbox" id="pf-mostrar-especificaciones" checked />
                  <span class="pf-toggle-track"><span class="pf-toggle-thumb"></span></span>
                </label>
              </div>
            </div>

            <div class="pf-ig-row" style="border-bottom:none;align-items:start;">
              <label class="pf-ig-label" style="padding-top:10px;">
                Especificaciones del producto (producto)
                <span class="pf-hint" title="Especificaciones técnicas visibles en la ficha del producto">?</span>
              </label>
              <div class="pf-ig-val" style="flex:1;">
                <div class="pf-rte-wrap" id="pf-especificaciones-rte-wrap">
                  <div class="pf-rte-toolbar" id="pf-especificaciones-toolbar">
                    <button type="button" class="pf-rte-btn" data-cmd="insertTable"   title="Tabla">⊞</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertUnorderedList" title="Lista">≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertOrderedList"   title="Lista numerada"><span style="font-size:.7rem;font-weight:700;">1.</span>≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertCheckbox" title="Casilla">☑</button>
                    <button type="button" class="pf-rte-btn" data-cmd="createLink"    title="Enlace">⛓</button>
                    <button type="button" class="pf-rte-btn" data-cmd="bold"          title="Negrita" style="font-weight:700;">B</button>
                    <button type="button" class="pf-rte-btn" data-cmd="italic"        title="Cursiva" style="font-style:italic;">I</button>
                    <button type="button" class="pf-rte-btn" data-cmd="removeFormat"  title="Limpiar formato" style="color:var(--mp-muted);">✕</button>
                  </div>
                  <div class="pf-rte-editor" id="pf-especificaciones-editor"
                       contenteditable="true"
                       data-placeholder='Escriba "/" para acceder a los comandos'></div>
                </div>
              </div>
            </div>

          </div><!-- /pf-panel-5 -->

          <!-- ── Condiciones especiales ── -->
          <div class="pf-nb-panel" id="pf-panel-6" role="tabpanel" aria-labelledby="pf-tab-6" hidden>

            <div class="pf-ig-row">
              <label class="pf-ig-label" for="pf-mostrar-condiciones">
                Mostrar pestaña Condiciones especiales en la web
                <span class="pf-hint" title="Muestra u oculta esta sección en la página del producto en la tienda">?</span>
              </label>
              <div class="pf-ig-val" style="padding-top:6px;">
                <label class="pf-toggle">
                  <input type="checkbox" id="pf-mostrar-condiciones" checked />
                  <span class="pf-toggle-track"><span class="pf-toggle-thumb"></span></span>
                </label>
              </div>
            </div>

            <div class="pf-ig-row" style="border-bottom:none;align-items:start;">
              <label class="pf-ig-label" style="padding-top:10px;">
                Condiciones especiales (producto)
                <span class="pf-hint" title="Garantías, restricciones o condiciones de venta visibles en la ficha del producto">?</span>
              </label>
              <div class="pf-ig-val" style="flex:1;">
                <div class="pf-rte-wrap" id="pf-condiciones-rte-wrap">
                  <div class="pf-rte-toolbar" id="pf-condiciones-toolbar">
                    <button type="button" class="pf-rte-btn" data-cmd="insertTable"   title="Tabla">⊞</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertUnorderedList" title="Lista">≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertOrderedList"   title="Lista numerada"><span style="font-size:.7rem;font-weight:700;">1.</span>≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertCheckbox" title="Casilla">☑</button>
                    <button type="button" class="pf-rte-btn" data-cmd="createLink"    title="Enlace">⛓</button>
                    <button type="button" class="pf-rte-btn" data-cmd="bold"          title="Negrita" style="font-weight:700;">B</button>
                    <button type="button" class="pf-rte-btn" data-cmd="italic"        title="Cursiva" style="font-style:italic;">I</button>
                    <button type="button" class="pf-rte-btn" data-cmd="removeFormat"  title="Limpiar formato" style="color:var(--mp-muted);">✕</button>
                  </div>
                  <div class="pf-rte-editor" id="pf-condiciones-editor"
                       contenteditable="true"
                       data-placeholder='Escriba "/" para acceder a los comandos'></div>
                </div>
              </div>
            </div>

          </div><!-- /pf-panel-6 -->

        </div><!-- /pf-notebook -->
      </div><!-- /columna principal -->

      <!-- Columna foto -->
      <div class="pf-photo-col">
        <div class="pf-photo-box" id="pf-photo-box" title="Haz clic para cambiar la foto">
          <img id="pf-photo-preview" src="/static/imagenes/banner.png" alt="Foto del producto" />
        </div>
        <p class="pf-photo-hint">Fotografía principal<br>Haz clic para subir</p>
        <div class="pf-photo-actions">
          <button class="pf-photo-btn" id="pf-photo-change-btn" type="button">Cambiar</button>
          <button class="pf-photo-btn" id="pf-photo-remove-btn" type="button">Quitar</button>
        </div>
        <input type="file" id="pf-photo-input" accept="image/*" style="display:none" />
        <input type="hidden" id="pf-stock" value="" />
        <input type="hidden" id="pf-stock-min" value="" />
      </div>

    </div><!-- /pf-body -->
  </div><!-- /pf-view -->

  <!-- Diálogo de confirmación eliminación -->
  <div class="pv-confirm-overlay" id="pv-confirm-overlay" hidden>
    <div class="pv-confirm-card">
      <h3 class="pv-confirm-title">&#9888; Eliminar producto(s)</h3>
      <p class="pv-confirm-msg" id="pv-confirm-msg">¿Confirmar eliminación?</p>
      <div class="pv-confirm-actions">
        <button class="btn-descartar" id="pv-confirm-cancel" type="button">Cancelar</button>
        <button class="btn-eliminar" id="pv-confirm-ok" type="button">Eliminar</button>
      </div>
    </div>
  </div>

</main>
<script src="/static/js/backend-sidebar-core.js"></script>
<script>
  (function () {
    if (window.initBackendSidebarCore) window.initBackendSidebarCore();
  })();
</script>
<script src="/static/js/sidebar-theme-editor.js"></script>
<script src="/static/js/backend-navbar.js"></script>
<script>
(function () {
  /* ════════════════════════════════
     ESTADO
  ════════════════════════════════ */
  var STORAGE_KEY   = "multitienda_productos";
  var CAT_KEY       = "multitienda_categorias";
  var PAGE_SIZE     = 15;
  var DEFAULT_PHOTO = "/static/imagenes/banner.png";

  var allProducts      = [];
  var filteredProducts = [];
  var currentPage      = 1;
  var sortCol          = "nombre";
  var sortAsc          = true;
  var selectedIds      = new Set();
  var editIndex        = -1;   /* -1 = nuevo */
  var isPublicado      = false;
  var photoDataUrl     = null; /* foto pendiente (blob URL o data URL) */

  /* ── persistencia ── */
  function load() {
    try { allProducts = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); }
    catch(e) { allProducts = []; }
    allProducts.forEach(function(p,i){ if (!p._id) p._id = "p" + Date.now() + i; });
  }
  function saveAll() { localStorage.setItem(STORAGE_KEY, JSON.stringify(allProducts)); }

  function loadCategories() {
    try { return JSON.parse(localStorage.getItem(CAT_KEY) || "[]"); }
    catch(e) { return []; }
  }

  /* ── helpers ── */
  function esc(s) { return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function fmtMoney(v) {
    var n = parseFloat(v);
    if (isNaN(n)) return "";
    return "$ " + n.toLocaleString("es-MX",{minimumFractionDigits:2,maximumFractionDigits:2});
  }

  /* ════════════════════════════════
     VISTA LISTA
  ════════════════════════════════ */
  function applyFilterSort() {
    var q = (document.getElementById("pv-search").value || "").toLowerCase();
    filteredProducts = allProducts.filter(function(p) {
      if (!q) return true;
      return (p.nombre    ||"").toLowerCase().includes(q) ||
             (p.referencia||"").toLowerCase().includes(q) ||
             (p.etiquetas ||"").toLowerCase().includes(q);
    });
    filteredProducts.sort(function(a,b){
      var va = a[sortCol]||"", vb = b[sortCol]||"";
      if (sortCol==="precio"||sortCol==="costo") {
        va=parseFloat(va)||0; vb=parseFloat(vb)||0;
        return sortAsc ? va-vb : vb-va;
      }
      return sortAsc
        ? String(va).localeCompare(String(vb),"es")
        : String(vb).localeCompare(String(va),"es");
    });
    currentPage = 1;
    renderTable();
  }

  function renderTable() {
    var tbody   = document.getElementById("pv-tbody");
    var empty   = document.getElementById("pv-empty");
    var pagLbl  = document.getElementById("pv-pag-label");
    var prevBtn = document.getElementById("pv-prev-btn");
    var nextBtn = document.getElementById("pv-next-btn");
    tbody.innerHTML = "";

    if (filteredProducts.length === 0) {
      empty.hidden = false;
      pagLbl.textContent = "0 / 0";
      prevBtn.disabled = nextBtn.disabled = true;
      return;
    }
    empty.hidden = true;
    var totalPages = Math.ceil(filteredProducts.length / PAGE_SIZE);
    if (currentPage > totalPages) currentPage = totalPages;
    var start = (currentPage-1)*PAGE_SIZE;
    var end   = Math.min(start+PAGE_SIZE, filteredProducts.length);
    pagLbl.textContent = (start+1)+"-"+end+" / "+filteredProducts.length;
    prevBtn.disabled = currentPage<=1;
    nextBtn.disabled = currentPage>=totalPages;

    filteredProducts.slice(start,end).forEach(function(p){
      var tr = document.createElement("tr");
      if (selectedIds.has(p._id)) tr.classList.add("selected");
      var tags = (p.etiquetas||"").split(",").map(function(t){
        t=t.trim(); return t?'<span class="tag-badge">'+esc(t)+'</span>':"";
      }).join("");
      tr.innerHTML =
        '<td class="col-cb"><input class="cb-input" type="checkbox" data-id="'+esc(p._id)+'" '+(selectedIds.has(p._id)?"checked":"")+' /></td>'+
        '<td class="col-star"><button class="star-btn'+(p._star?" active":"")+'" data-star="'+esc(p._id)+'" type="button">★</button></td>'+
        '<td>'+esc(p.nombre||"—")+'</td>'+
        '<td style="color:var(--mp-muted);">'+esc(p.referencia||"")+'</td>'+
        '<td>'+(tags||"")+'</td>'+
        '<td class="col-num">'+fmtMoney(p.precio)+'</td>'+
        '<td class="col-num">'+fmtMoney(p.costo)+'</td>'+
        '<td></td>';
      tr.addEventListener("click", function(e){
        if (e.target.closest("[data-id]")||e.target.closest("[data-star]")) return;
        openForm(allProducts.indexOf(p));
      });
      document.getElementById("pv-tbody").appendChild(tr);
    });

    /* sort arrows */
    document.querySelectorAll(".pv-table th.sortable").forEach(function(th){
      var a = th.querySelector(".sort-arrow"); if (!a) return;
      if (th.dataset.col===sortCol){ a.textContent=sortAsc?"↑":"↓"; a.style.color="var(--mp-accent)"; }
      else { a.textContent="↕"; a.style.color="var(--mp-muted)"; }
    });
    var pageSlice = filteredProducts.slice(start,end);
    document.getElementById("pv-select-all").checked =
      pageSlice.length>0 && pageSlice.every(function(p){ return selectedIds.has(p._id); });
  }

  /* eventos lista */
  document.getElementById("pv-tbody").addEventListener("change", function(e){
    var cb = e.target.closest("[data-id]"); if (!cb) return;
    if (cb.checked) selectedIds.add(cb.dataset.id); else selectedIds.delete(cb.dataset.id);
    renderTable();
  });
  document.getElementById("pv-tbody").addEventListener("click", function(e){
    var s = e.target.closest("[data-star]"); if (!s) return;
    var p = allProducts.find(function(x){ return x._id===s.dataset.star; });
    if (p){ p._star=!p._star; saveAll(); renderTable(); }
  });
  document.getElementById("pv-select-all").addEventListener("change", function(){
    var start=(currentPage-1)*PAGE_SIZE;
    filteredProducts.slice(start,start+PAGE_SIZE).forEach(function(p){
      if (this.checked) selectedIds.add(p._id); else selectedIds.delete(p._id);
    },this);
    renderTable();
  });
  document.querySelectorAll(".pv-table th.sortable").forEach(function(th){
    th.addEventListener("click",function(){
      if (sortCol===th.dataset.col) sortAsc=!sortAsc; else { sortCol=th.dataset.col; sortAsc=true; }
      applyFilterSort();
    });
  });
  document.getElementById("pv-search").addEventListener("input", applyFilterSort);
  document.getElementById("pv-prev-btn").addEventListener("click",function(){
    if (currentPage>1){ currentPage--; renderTable(); }
  });
  document.getElementById("pv-next-btn").addEventListener("click",function(){
    if (currentPage<Math.ceil(filteredProducts.length/PAGE_SIZE)){ currentPage++; renderTable(); }
  });
  document.getElementById("pv-nuevo-btn").addEventListener("click",function(){ openForm(-1); });

  /* ════════════════════════════════
     VISTA FORM
  ════════════════════════════════ */
  function openForm(idx) {
    editIndex    = idx;
    isPublicado  = false;
    photoDataUrl = null;

    /* rellenar categorías */
    var catSel = document.getElementById("pf-categoria");
    catSel.innerHTML = '<option value="">Sin categoría</option>';
    loadCategories().forEach(function(c){
      var o=document.createElement("option"); o.value=c.nombre; o.textContent=c.nombre;
      catSel.appendChild(o);
    });

    var p = idx>=0 ? allProducts[idx] : {};
    isPublicado = !!p.publicado;

    /* campos */
    document.getElementById("pf-nombre").value              = p.nombre             || "";
    document.getElementById("pf-precio").value              = p.precio             || "";
    document.getElementById("pf-costo").value               = p.costo              || "";
    document.getElementById("pf-referencia").value          = p.referencia         || "";
    document.getElementById("pf-etiquetas").value           = p.etiquetas          || "";
    document.getElementById("pf-stock").value               = p.stock              || "";
    document.getElementById("pf-stock-min").value           = p.stockMin           || "";
    document.getElementById("pf-unidad").value              = p.unidad             || "pieza";
    document.getElementById("pf-codigo-barras").value       = p.codigoBarras       || "";
    document.getElementById("pf-notas-internas").value      = p.notasInternas      || "";
    document.getElementById("pf-politica-facturacion").value= p.politicaFacturacion|| "cantidad_ordenada";
    document.getElementById("pf-politica-hint").textContent = ({
      "cantidad_ordenada":  "Puede facturar los bienes antes de entregarlos.",
      "cantidad_entregada": "Solo puede facturar después de registrar la entrega.",
      "anticipo":           "Se factura un anticipo al confirmar el pedido."
    })[p.politicaFacturacion || "cantidad_ordenada"];
    catSel.value = p.categoria || "";

    /* tipo de producto */
    var tipo = p.tipoProducto || "bienes";
    document.querySelectorAll("[name='pf-tipo-producto']").forEach(function(r){ r.checked = r.value === tipo; });

    /* impuestos */
    taxVenta  = (p.taxVenta  || []).slice();
    taxCompra = (p.taxCompra || []).slice();
    renderTaxTags(document.getElementById("pf-tax-venta-tags"),  document.getElementById("pf-tax-venta-input"),  taxVenta,  document.getElementById("pf-tax-venta-calc"));
    renderTaxTags(document.getElementById("pf-tax-compra-tags"), document.getElementById("pf-tax-compra-input"), taxCompra, null);

    /* ventas */
    document.getElementById("pf-productos-opcionales").value = p.productosOpcionales || "";
    document.getElementById("pf-accesorios").value           = p.accesorios          || "";
    document.getElementById("pf-productos-alternos").value   = p.productosAlternos   || "";
    document.getElementById("pf-desc-cotizacion").value      = p.descCotizacion      || "";
    document.getElementById("pf-ecom-etiquetas").value       = p.ecomEtiquetas       || "";
    document.getElementById("pf-ecom-publicado").checked     = !!p.ecomPublicado;
    document.getElementById("pf-ecom-categorias").value      = p.ecomCategorias      || "";
    document.getElementById("pf-desc-ecom").value            = p.descEcom            || "";
    mediaFiles = (p.mediaFiles || []).slice();
    renderMedia();

    /* características */
    document.getElementById("pf-nuevo").checked     = !!p.nuevo;
    document.getElementById("pf-desc-corta").value = p.descCorta || "";
    document.getElementById("pf-desc-larga").value = p.descLarga || "";

    /* detalles del artículo */
    document.getElementById("pf-mostrar-detalles").checked       = p.mostrarDetalles !== false;
    document.getElementById("pf-detalles-editor").innerHTML      = p.detallesHtml || "";
    /* especificaciones */
    document.getElementById("pf-mostrar-especificaciones").checked    = p.mostrarEspecificaciones !== false;
    document.getElementById("pf-especificaciones-editor").innerHTML   = p.especificacionesHtml || "";
    /* condiciones especiales */
    document.getElementById("pf-mostrar-condiciones").checked    = p.mostrarCondiciones !== false;
    document.getElementById("pf-condiciones-editor").innerHTML   = p.condicionesHtml || "";

    /* foto */
    document.getElementById("pf-photo-preview").src = p.imagen || DEFAULT_PHOTO;

    /* breadcrumb + publicar */
    document.getElementById("pf-breadcrumb-nombre").textContent = p.nombre || "Nuevo";
    syncPublicar();

    /* tabs (reset a primera pestaña) */
    document.querySelectorAll(".pf-nb-tab").forEach(function(t){ t.classList.remove("active"); t.setAttribute("aria-selected","false"); });
    document.querySelectorAll(".pf-nb-panel").forEach(function(p){ p.hidden=true; });
    document.getElementById("pf-tab-1").classList.add("active");
    document.getElementById("pf-tab-1").setAttribute("aria-selected","true");
    document.getElementById("pf-panel-1").hidden=false;

    /* mostrar/ocultar btn eliminar en form */
    document.getElementById("pf-eliminar-btn").style.display = idx >= 0 ? "" : "none";

    /* mostrar form */
    document.getElementById("pv-view").hidden = true;
    document.getElementById("pf-view").hidden = false;
  }

  function showList() {
    document.getElementById("pf-view").hidden = true;
    document.getElementById("pv-view").hidden = false;
    load(); applyFilterSort();
  }

  function syncPublicar() {
    var btn = document.getElementById("pf-publicar-btn");
    if (isPublicado) {
      btn.textContent = "Publicado";
      btn.classList.add("publicado");
    } else {
      btn.textContent = "Sin publicar";
      btn.classList.remove("publicado");
    }
  }

  function saveForm() {
    var nombre = document.getElementById("pf-nombre").value.trim();
    if (!nombre){ alert("El nombre del producto es obligatorio."); return; }

    var tipoChecked = document.querySelector("[name='pf-tipo-producto']:checked");
    var prod = {
      nombre:              nombre,
      precio:              document.getElementById("pf-precio").value,
      costo:               document.getElementById("pf-costo").value,
      referencia:          document.getElementById("pf-referencia").value.trim(),
      etiquetas:           document.getElementById("pf-etiquetas").value.trim(),
      stock:               document.getElementById("pf-stock").value,
      stockMin:            document.getElementById("pf-stock-min").value,
      unidad:              document.getElementById("pf-unidad").value,
      codigoBarras:        document.getElementById("pf-codigo-barras").value.trim(),
      notasInternas:       document.getElementById("pf-notas-internas").value.trim(),
      politicaFacturacion: document.getElementById("pf-politica-facturacion").value,
      tipoProducto:        tipoChecked ? tipoChecked.value : "bienes",
      taxVenta:            taxVenta.slice(),
      taxCompra:           taxCompra.slice(),
      /* ventas */
      productosOpcionales: document.getElementById("pf-productos-opcionales").value.trim(),
      accesorios:          document.getElementById("pf-accesorios").value.trim(),
      productosAlternos:   document.getElementById("pf-productos-alternos").value.trim(),
      descCotizacion:      document.getElementById("pf-desc-cotizacion").value.trim(),
      ecomEtiquetas:       document.getElementById("pf-ecom-etiquetas").value.trim(),
      ecomPublicado:       document.getElementById("pf-ecom-publicado").checked,
      ecomCategorias:      document.getElementById("pf-ecom-categorias").value.trim(),
      descEcom:            document.getElementById("pf-desc-ecom").value.trim(),
      mediaFiles:          mediaFiles.slice(),
      /* características */
      nuevo:               document.getElementById("pf-nuevo").checked,
      descCorta:           document.getElementById("pf-desc-corta").value.trim(),
      descLarga:           document.getElementById("pf-desc-larga").value.trim(),
      /* detalles del artículo */
      mostrarDetalles:     document.getElementById("pf-mostrar-detalles").checked,
      detallesHtml:        document.getElementById("pf-detalles-editor").innerHTML,
      /* especificaciones */
      mostrarEspecificaciones: document.getElementById("pf-mostrar-especificaciones").checked,
      especificacionesHtml:    document.getElementById("pf-especificaciones-editor").innerHTML,
      /* condiciones especiales */
      mostrarCondiciones:  document.getElementById("pf-mostrar-condiciones").checked,
      condicionesHtml:     document.getElementById("pf-condiciones-editor").innerHTML,
      categoria:           document.getElementById("pf-categoria").value,
      publicado:           isPublicado,
      imagen:              photoDataUrl || document.getElementById("pf-photo-preview").src,
    };

    if (editIndex>=0) {
      prod._id    = allProducts[editIndex]._id;
      prod._star  = allProducts[editIndex]._star;
      allProducts[editIndex] = prod;
    } else {
      prod._id = "p" + Date.now();
      allProducts.push(prod);
    }
    saveAll();
    showList();
  }

  /* eventos form */
  document.getElementById("pf-guardar-btn").addEventListener("click", saveForm);
  document.getElementById("pf-descartar-btn").addEventListener("click", showList);
  document.getElementById("pf-breadcrumb-back").addEventListener("click", showList);

  document.getElementById("pf-publicar-btn").addEventListener("click",function(){
    isPublicado = !isPublicado;
    syncPublicar();
  });

  /* actualiza breadcrumb dinámicamente con el nombre */
  document.getElementById("pf-nombre").addEventListener("input", function(){
    document.getElementById("pf-breadcrumb-nombre").textContent = this.value.trim() || "Nuevo";
  });

  /* foto */
  document.getElementById("pf-photo-box").addEventListener("click",function(){
    document.getElementById("pf-photo-input").click();
  });
  document.getElementById("pf-photo-change-btn").addEventListener("click",function(){
    document.getElementById("pf-photo-input").click();
  });
  document.getElementById("pf-photo-remove-btn").addEventListener("click",function(){
    photoDataUrl = DEFAULT_PHOTO;
    document.getElementById("pf-photo-preview").src = DEFAULT_PHOTO;
  });
  document.getElementById("pf-photo-input").addEventListener("change",function(){
    var f = this.files[0]; if (!f) return;
    var url = URL.createObjectURL(f);
    photoDataUrl = url;
    document.getElementById("pf-photo-preview").src = url;
  });

  /* ── Impuestos (tag input) ── */
  var taxVenta  = [];
  var taxCompra = [];

  function renderTaxTags(tagsEl, inputEl, taxArr, calcEl) {
    tagsEl.innerHTML = "";
    taxArr.forEach(function(t, i) {
      var span = document.createElement("span");
      span.className = "pf-tax-tag";
      span.innerHTML = t + '% <button class="pf-tax-remove" data-ti="' + i + '" type="button">×</button>';
      tagsEl.appendChild(span);
    });
    if (calcEl) updateTaxCalc(calcEl, taxArr);
    tagsEl.querySelectorAll(".pf-tax-remove").forEach(function(btn) {
      btn.addEventListener("click", function() {
        taxArr.splice(Number(btn.dataset.ti), 1);
        renderTaxTags(tagsEl, inputEl, taxArr, calcEl);
      });
    });
  }

  function updateTaxCalc(calcEl, taxArr) {
    var precio = parseFloat(document.getElementById("pf-precio").value) || 0;
    if (!precio || !taxArr.length) { calcEl.textContent = ""; return; }
    var total = taxArr.reduce(function(acc, t) { return acc + precio * (parseFloat(t) / 100); }, 0);
    calcEl.textContent = "(= $ " + (precio + total).toLocaleString("es-MX", {minimumFractionDigits:2,maximumFractionDigits:2}) + " impuestos incluidos)";
  }

  function setupTaxInput(inputId, tagsId, taxArr, calcId) {
    var input  = document.getElementById(inputId);
    var tags   = document.getElementById(tagsId);
    var calcEl = calcId ? document.getElementById(calcId) : null;
    input.addEventListener("keydown", function(e) {
      if (e.key === "Enter" || e.key === "Tab" || e.key === ",") {
        e.preventDefault();
        var val = parseFloat(input.value.replace(/[^0-9.]/g,""));
        if (!isNaN(val) && val > 0 && val <= 100) {
          taxArr.push(val);
          input.value = "";
          renderTaxTags(tags, input, taxArr, calcEl);
        }
      }
    });
    /* click en el wrap enfoca el input */
    input.closest(".pf-tax-wrap").addEventListener("click", function() { input.focus(); });
  }

  setupTaxInput("pf-tax-venta-input",  "pf-tax-venta-tags",  taxVenta,  "pf-tax-venta-calc");
  setupTaxInput("pf-tax-compra-input", "pf-tax-compra-tags", taxCompra, null);

  /* recalcular cuando cambia el precio */
  document.getElementById("pf-precio").addEventListener("input", function() {
    updateTaxCalc(document.getElementById("pf-tax-venta-calc"), taxVenta);
  });

  /* ── Política de facturación — hint dinámico ── */
  var politicaHints = {
    "cantidad_ordenada":  "Puede facturar los bienes antes de entregarlos.",
    "cantidad_entregada": "Solo puede facturar después de registrar la entrega.",
    "anticipo":           "Se factura un anticipo al confirmar el pedido."
  };
  document.getElementById("pf-politica-facturacion").addEventListener("change", function() {
    document.getElementById("pf-politica-hint").textContent = politicaHints[this.value] || "";
  });

  /* ── Tipo de producto — ajusta opciones de política ── */
  document.querySelectorAll("[name='pf-tipo-producto']").forEach(function(radio) {
    radio.addEventListener("change", function() {
      var pol = document.getElementById("pf-politica-facturacion");
      if (this.value === "servicio") {
        pol.querySelector("[value='cantidad_ordenada']").textContent = "Cantidad ordenada";
        pol.querySelector("[value='cantidad_entregada']").textContent = "Cantidad manual";
      } else {
        pol.querySelector("[value='cantidad_ordenada']").textContent = "Cantidad ordenada";
        pol.querySelector("[value='cantidad_entregada']").textContent = "Cantidad entregada";
      }
      pol.dispatchEvent(new Event("change"));
    });
  });

  /* ── Multimedia (Ventas) ── */
  var mediaFiles = [];   /* { name, url } */

  function renderMedia() {
    var list = document.getElementById("pf-media-list");
    list.innerHTML = "";
    mediaFiles.forEach(function(f, i) {
      var div = document.createElement("div");
      div.className = "pf-media-thumb";
      div.innerHTML = '<img src="' + f.url + '" alt="' + f.name + '" />' +
        '<button class="pf-media-del" data-mi="' + i + '" type="button" title="Quitar">×</button>';
      list.appendChild(div);
    });
    list.querySelectorAll(".pf-media-del").forEach(function(btn) {
      btn.addEventListener("click", function() {
        mediaFiles.splice(Number(btn.dataset.mi), 1);
        renderMedia();
      });
    });
  }

  document.getElementById("pf-media-add-btn").addEventListener("click", function() {
    document.getElementById("pf-media-input").click();
  });
  document.getElementById("pf-media-input").addEventListener("change", function() {
    Array.from(this.files).forEach(function(f) {
      mediaFiles.push({ name: f.name, url: URL.createObjectURL(f) });
    });
    renderMedia();
    this.value = "";
  });

  /* ── RTE helpers (shared) ── */
  function setupRteToolbar(toolbarId) {
    var toolbar = document.getElementById(toolbarId);
    toolbar.querySelectorAll(".pf-rte-btn").forEach(function(btn){
      btn.addEventListener("mousedown", function(e){
        e.preventDefault();
        var cmd = btn.dataset.cmd;
        if (cmd === "createLink") {
          var url = prompt("URL del enlace:");
          if (url) document.execCommand("createLink", false, url);
        } else if (cmd === "insertTable") {
          document.execCommand("insertHTML", false,
            '<table style="border-collapse:collapse;width:100%;"><tr>' +
            '<td style="border:1px solid var(--mp-border);padding:6px;">&nbsp;</td>' +
            '<td style="border:1px solid var(--mp-border);padding:6px;">&nbsp;</td>' +
            '</tr></table><p></p>');
        } else if (cmd === "insertCheckbox") {
          document.execCommand("insertHTML", false,
            '<label style="display:flex;align-items:center;gap:6px;">' +
            '<input type="checkbox" /><span>Elemento</span></label>');
        } else {
          document.execCommand(cmd, false, null);
        }
      });
    });
  }
  setupRteToolbar("pf-detalles-toolbar");
  setupRteToolbar("pf-especificaciones-toolbar");
  setupRteToolbar("pf-condiciones-toolbar");

  /* notebook tabs */
  document.querySelectorAll(".pf-nb-tab").forEach(function(tab,i){
    tab.addEventListener("click",function(){
      document.querySelectorAll(".pf-nb-tab").forEach(function(t){
        t.classList.remove("active"); t.setAttribute("aria-selected","false");
      });
      document.querySelectorAll(".pf-nb-panel").forEach(function(p){ p.hidden=true; });
      tab.classList.add("active"); tab.setAttribute("aria-selected","true");
      document.getElementById("pf-panel-"+(i+1)).hidden=false;
    });
  });

  /* ════════════════════════════════
     ELIMINACIÓN
  ════════════════════════════════ */
  var pendingDeleteIds = [];   /* ids a eliminar al confirmar */

  function openConfirm(msg, ids) {
    pendingDeleteIds = ids;
    document.getElementById("pv-confirm-msg").textContent = msg;
    document.getElementById("pv-confirm-overlay").hidden = false;
  }

  function closeConfirm() {
    document.getElementById("pv-confirm-overlay").hidden = true;
    pendingDeleteIds = [];
  }

  document.getElementById("pv-confirm-cancel").addEventListener("click", closeConfirm);

  document.getElementById("pv-confirm-ok").addEventListener("click", function() {
    pendingDeleteIds.forEach(function(id) {
      allProducts = allProducts.filter(function(p) { return p._id !== id; });
      selectedIds.delete(id);
    });
    closeConfirm();
    saveAll();
    /* si veníamos del form, volver a lista */
    if (!document.getElementById("pf-view").hidden) {
      document.getElementById("pf-view").hidden = true;
      document.getElementById("pv-view").hidden = false;
    }
    load(); applyFilterSort();
  });

  /* Eliminar seleccionados desde lista */
  var pvEliminarBtn = document.getElementById("pv-eliminar-btn");
  pvEliminarBtn.addEventListener("click", function() {
    if (!selectedIds.size) return;
    var count = selectedIds.size;
    openConfirm(
      count === 1
        ? "¿Eliminar 1 producto? Esta acción no se puede deshacer."
        : "¿Eliminar " + count + " productos? Esta acción no se puede deshacer.",
      Array.from(selectedIds)
    );
  });

  /* Activar/desactivar btn eliminar lista según selección */
  function syncEliminarBtn() {
    pvEliminarBtn.disabled = selectedIds.size === 0;
  }

  /* Eliminar producto actual desde formulario */
  document.getElementById("pf-eliminar-btn").addEventListener("click", function() {
    if (editIndex < 0) return;
    var p = allProducts[editIndex];
    openConfirm(
      "¿Eliminar \"" + (p.nombre || "este producto") + "\"? Esta acción no se puede deshacer.",
      [p._id]
    );
  });

  /* Sobrescribir renderTable para sincronizar btn eliminar */
  var _origRenderTable = renderTable;
  renderTable = function() {
    _origRenderTable();
    syncEliminarBtn();
  };

  /* breadcrumb nombre tienda */
  (function(){
    var n = localStorage.getItem("multitienda_store_name");
    if (n) document.getElementById("pv-breadcrumb-tienda").textContent = n;
  })();

  /* ── init ── */
  load();
  applyFilterSort();
})();
</script>
</body>
</html>"""
