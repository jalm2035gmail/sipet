from __future__ import annotations


def videos_html() -> str:
    return _HTML


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Videos — Multitienda</title>
  <style>
    :root {
      --vd-bg: var(--page-bg, #f4f6fb);
      --vd-surface: var(--content-bg, #ffffff);
      --vd-border: var(--field-border, #d1d5db);
      --vd-text: var(--body-text, #1f2937);
      --vd-muted: color-mix(in srgb, var(--body-text, #1f2937) 58%, #ffffff 42%);
      --vd-accent: var(--button-bg, #1a6b3c);
      --vd-accent-fg: var(--button-text, #ffffff);
      --vd-danger: #dc2626;
      --vd-danger-soft: color-mix(in srgb, #dc2626 10%, var(--vd-surface));
    }

    html, body { margin: 0; padding: 0; background: var(--vd-bg); font-family: system-ui, Arial, sans-serif; color: var(--vd-text); }
    * { box-sizing: border-box; }

    /* ── Toolbar ── */
    .vd-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }

    .vd-toolbar__left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

    .vd-btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 38px;
      padding: 0 16px;
      border-radius: 10px;
      border: 1px solid var(--vd-border);
      background: var(--vd-surface);
      color: var(--vd-text);
      font-size: 0.86rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.14s ease, border-color 0.14s ease, transform 0.14s ease;
      text-decoration: none;
    }
    .vd-btn:hover { background: color-mix(in srgb, var(--vd-surface) 85%, var(--vd-bg)); transform: translateY(-1px); }
    .vd-btn--primary {
      background: var(--vd-accent);
      color: var(--vd-accent-fg);
      border-color: var(--vd-accent);
    }
    .vd-btn--primary:hover { background: color-mix(in srgb, var(--vd-accent) 85%, #000 15%); border-color: color-mix(in srgb, var(--vd-accent) 85%, #000 15%); }
    .vd-btn--danger { color: var(--vd-danger); border-color: color-mix(in srgb, var(--vd-danger) 35%, var(--vd-border)); }
    .vd-btn--danger:hover { background: var(--vd-danger-soft); }
    .vd-btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }

    /* ── Search ── */
    .vd-search {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 38px;
      padding: 0 12px;
      border: 1px solid var(--vd-border);
      border-radius: 10px;
      background: var(--vd-surface);
    }
    .vd-search input {
      border: none;
      outline: none;
      background: transparent;
      color: var(--vd-text);
      font-size: 0.86rem;
      width: 180px;
    }
    .vd-search input::placeholder { color: var(--vd-muted); }

    /* ── Upload zone ── */
    .vd-upload-zone {
      border: 2px dashed var(--vd-border);
      border-radius: 16px;
      padding: 32px 20px;
      text-align: center;
      background: color-mix(in srgb, var(--vd-surface) 96%, var(--vd-bg) 4%);
      margin-bottom: 20px;
      transition: border-color 0.2s ease, background 0.2s ease;
      cursor: pointer;
    }
    .vd-upload-zone.drag-over {
      border-color: var(--vd-accent);
      background: color-mix(in srgb, var(--vd-accent) 6%, var(--vd-surface));
    }
    .vd-upload-zone__icon { font-size: 2rem; color: var(--vd-muted); margin-bottom: 10px; }
    .vd-upload-zone__title { font-size: 1rem; font-weight: 700; margin: 0 0 6px; color: var(--vd-text); }
    .vd-upload-zone__hint { font-size: 0.82rem; color: var(--vd-muted); margin: 0; }
    .vd-upload-zone__formats { font-size: 0.78rem; color: var(--vd-muted); margin-top: 6px; }
    #vd-file-input { display: none; }

    /* ── Progress bar ── */
    .vd-upload-progress {
      margin-bottom: 16px;
      display: none;
    }
    .vd-upload-progress.visible { display: block; }
    .vd-progress-label { font-size: 0.83rem; color: var(--vd-muted); margin-bottom: 4px; display: flex; justify-content: space-between; }
    .vd-progress-track { height: 6px; border-radius: 999px; background: var(--vd-border); overflow: hidden; }
    .vd-progress-fill { height: 100%; border-radius: 999px; background: var(--vd-accent); width: 0%; transition: width 0.3s ease; }

    /* ── Video grid ── */
    .vd-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 16px;
    }

    .vd-card {
      background: var(--vd-surface);
      border: 1px solid var(--vd-border);
      border-radius: 14px;
      overflow: hidden;
      position: relative;
      transition: box-shadow 0.16s ease, transform 0.16s ease;
    }
    .vd-card:hover { box-shadow: 0 8px 24px rgba(0,0,0,0.10); transform: translateY(-2px); }

    .vd-card__thumb {
      position: relative;
      aspect-ratio: 16/9;
      background: #0f172a;
      cursor: pointer;
    }
    .vd-card__thumb video {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }
    .vd-card__thumb-placeholder {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: rgba(255,255,255,0.5);
      font-size: 2rem;
    }
    .vd-card__play-btn {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0,0,0,0.3);
      color: #fff;
      font-size: 1.6rem;
      opacity: 0;
      transition: opacity 0.16s ease;
    }
    .vd-card__thumb:hover .vd-card__play-btn { opacity: 1; }

    .vd-card__check {
      position: absolute;
      top: 8px;
      left: 8px;
      width: 20px;
      height: 20px;
      border-radius: 6px;
      border: 2px solid rgba(255,255,255,0.8);
      background: rgba(255,255,255,0.15);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: background 0.14s ease, border-color 0.14s ease;
    }
    .vd-card__check.checked { background: var(--vd-accent); border-color: var(--vd-accent); color: #fff; }
    .vd-card__check i { font-size: 0.65rem; }

    .vd-card__duration {
      position: absolute;
      bottom: 6px;
      right: 8px;
      background: rgba(0,0,0,0.65);
      color: #fff;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
    }

    .vd-card__body { padding: 12px 14px; }
    .vd-card__name {
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--vd-text);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin: 0 0 4px;
    }
    .vd-card__meta {
      font-size: 0.76rem;
      color: var(--vd-muted);
      display: flex;
      gap: 10px;
    }

    .vd-card__actions {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 0 14px 12px;
    }
    .vd-card__action-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 30px;
      height: 30px;
      border-radius: 8px;
      border: 1px solid var(--vd-border);
      background: var(--vd-surface);
      color: var(--vd-muted);
      cursor: pointer;
      font-size: 0.78rem;
      transition: background 0.12s ease, color 0.12s ease;
    }
    .vd-card__action-btn:hover { background: var(--vd-bg); color: var(--vd-text); }
    .vd-card__action-btn--danger:hover { background: var(--vd-danger-soft); color: var(--vd-danger); border-color: color-mix(in srgb, var(--vd-danger) 30%, var(--vd-border)); }

    /* ── Empty state ── */
    .vd-empty {
      grid-column: 1 / -1;
      text-align: center;
      padding: 48px 20px;
      color: var(--vd-muted);
    }
    .vd-empty i { font-size: 3rem; margin-bottom: 12px; display: block; }
    .vd-empty p { margin: 0; font-size: 0.92rem; }

    /* ── Modal player ── */
    .vd-modal {
      position: fixed;
      inset: 0;
      z-index: 1200;
      background: rgba(0,0,0,0.78);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .vd-modal[hidden] { display: none; }
    .vd-modal__inner {
      position: relative;
      width: min(820px, 100%);
      background: #0f172a;
      border-radius: 18px;
      overflow: hidden;
    }
    .vd-modal__close {
      position: absolute;
      top: 10px;
      right: 10px;
      width: 34px;
      height: 34px;
      border-radius: 50%;
      border: none;
      background: rgba(255,255,255,0.18);
      color: #fff;
      font-size: 0.9rem;
      cursor: pointer;
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .vd-modal__close:hover { background: rgba(255,255,255,0.3); }
    .vd-modal__video { width: 100%; display: block; max-height: 70vh; }
    .vd-modal__info { padding: 14px 18px; }
    .vd-modal__title { margin: 0; font-size: 0.95rem; font-weight: 700; color: #f1f5f9; }
    .vd-modal__meta { font-size: 0.8rem; color: rgba(241,245,249,0.6); margin-top: 4px; }

    /* ── Confirm dialog ── */
    .vd-confirm {
      position: fixed;
      inset: 0;
      z-index: 1300;
      background: rgba(0,0,0,0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .vd-confirm[hidden] { display: none; }
    .vd-confirm__card {
      width: min(420px, 100%);
      background: var(--vd-surface);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 24px 60px rgba(0,0,0,0.2);
    }
    .vd-confirm__title { margin: 0 0 8px; font-size: 1.05rem; font-weight: 800; color: var(--vd-danger); }
    .vd-confirm__msg { margin: 0 0 18px; font-size: 0.88rem; color: var(--vd-muted); }
    .vd-confirm__actions { display: flex; gap: 10px; justify-content: flex-end; }

    /* ── Toast ── */
    .vd-toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 1400;
      background: #1e293b;
      color: #f1f5f9;
      padding: 12px 18px;
      border-radius: 12px;
      font-size: 0.87rem;
      font-weight: 600;
      box-shadow: 0 8px 24px rgba(0,0,0,0.22);
      transform: translateY(8px);
      opacity: 0;
      transition: opacity 0.2s ease, transform 0.2s ease;
      pointer-events: none;
    }
    .vd-toast.visible { opacity: 1; transform: translateY(0); }
    .vd-toast.success { background: #14532d; }
    .vd-toast.error { background: #7f1d1d; }

    /* ── Stats bar ── */
    .vd-stats {
      display: flex;
      gap: 18px;
      flex-wrap: wrap;
      margin-bottom: 16px;
      font-size: 0.84rem;
      color: var(--vd-muted);
    }
    .vd-stats strong { color: var(--vd-text); }
  </style>
</head>
<body>
<main>

  <!-- Toolbar -->
  <div class="vd-toolbar">
    <div class="vd-toolbar__left">
      <button class="vd-btn vd-btn--primary" id="vd-upload-btn">
        <i class="fa-solid fa-cloud-arrow-up"></i> Subir video
      </button>
      <button class="vd-btn vd-btn--danger" id="vd-delete-selected-btn" disabled>
        <i class="fa-solid fa-trash"></i> Eliminar seleccionados
      </button>
    </div>
    <div class="vd-search">
      <i class="fa-solid fa-magnifying-glass" style="color:var(--vd-muted);font-size:0.82rem"></i>
      <input id="vd-search-input" type="search" placeholder="Buscar videos…" />
    </div>
  </div>

  <!-- Stats -->
  <div class="vd-stats" id="vd-stats">
    <span><strong id="vd-count">0</strong> videos</span>
    <span><strong id="vd-size-total">0 MB</strong> usados</span>
    <span id="vd-selected-info" style="display:none"><strong id="vd-selected-count">0</strong> seleccionados</span>
  </div>

  <!-- Upload zone -->
  <div class="vd-upload-zone" id="vd-drop-zone">
    <input type="file" id="vd-file-input" accept="video/mp4,video/webm,video/ogg,video/quicktime,video/x-msvideo" multiple />
    <div class="vd-upload-zone__icon"><i class="fa-solid fa-film"></i></div>
    <p class="vd-upload-zone__title">Arrastra videos aquí o haz clic para seleccionar</p>
    <p class="vd-upload-zone__hint">Máximo 500 MB por archivo</p>
    <p class="vd-upload-zone__formats">MP4 · WebM · OGG · MOV · AVI</p>
  </div>

  <!-- Progress -->
  <div class="vd-upload-progress" id="vd-upload-progress">
    <div class="vd-progress-label">
      <span id="vd-progress-filename">Subiendo…</span>
      <span id="vd-progress-pct">0%</span>
    </div>
    <div class="vd-progress-track"><div class="vd-progress-fill" id="vd-progress-fill"></div></div>
  </div>

  <!-- Grid -->
  <div class="vd-grid" id="vd-grid">
    <div class="vd-empty" id="vd-empty-state">
      <i class="fa-regular fa-film"></i>
      <p>No hay videos subidos aún.<br>Arrastra archivos o usa el botón de arriba.</p>
    </div>
  </div>

  <!-- Modal player -->
  <div class="vd-modal" id="vd-modal" hidden>
    <div class="vd-modal__inner">
      <button class="vd-modal__close" id="vd-modal-close"><i class="fa-solid fa-xmark"></i></button>
      <video class="vd-modal__video" id="vd-modal-video" controls></video>
      <div class="vd-modal__info">
        <p class="vd-modal__title" id="vd-modal-title"></p>
        <p class="vd-modal__meta" id="vd-modal-meta"></p>
      </div>
    </div>
  </div>

  <!-- Confirm delete -->
  <div class="vd-confirm" id="vd-confirm" hidden>
    <div class="vd-confirm__card">
      <h3 class="vd-confirm__title"><i class="fa-solid fa-triangle-exclamation"></i> Eliminar video(s)</h3>
      <p class="vd-confirm__msg" id="vd-confirm-msg">¿Confirmar eliminación?</p>
      <div class="vd-confirm__actions">
        <button class="vd-btn" id="vd-confirm-cancel">Cancelar</button>
        <button class="vd-btn vd-btn--danger" id="vd-confirm-ok">Eliminar</button>
      </div>
    </div>
  </div>

  <!-- Toast -->
  <div class="vd-toast" id="vd-toast"></div>

</main>
<script>
(function () {
  'use strict';

  /* ── Storage key ── */
  var STORAGE_KEY = 'multitienda_videos';

  /* ── State ── */
  var videos = [];        // { id, name, size, mimeType, date, dataUrl, duration }
  var selected = new Set();
  var pendingDeleteIds = [];

  /* ── Elements ── */
  var grid          = document.getElementById('vd-grid');
  var emptyState    = document.getElementById('vd-empty-state');
  var uploadBtn     = document.getElementById('vd-upload-btn');
  var fileInput     = document.getElementById('vd-file-input');
  var dropZone      = document.getElementById('vd-drop-zone');
  var deleteSelBtn  = document.getElementById('vd-delete-selected-btn');
  var searchInput   = document.getElementById('vd-search-input');
  var progressWrap  = document.getElementById('vd-upload-progress');
  var progressFill  = document.getElementById('vd-progress-fill');
  var progressName  = document.getElementById('vd-progress-filename');
  var progressPct   = document.getElementById('vd-progress-pct');
  var modal         = document.getElementById('vd-modal');
  var modalVideo    = document.getElementById('vd-modal-video');
  var modalTitle    = document.getElementById('vd-modal-title');
  var modalMeta     = document.getElementById('vd-modal-meta');
  var modalClose    = document.getElementById('vd-modal-close');
  var confirm_      = document.getElementById('vd-confirm');
  var confirmMsg    = document.getElementById('vd-confirm-msg');
  var confirmOk     = document.getElementById('vd-confirm-ok');
  var confirmCancel = document.getElementById('vd-confirm-cancel');
  var toast         = document.getElementById('vd-toast');
  var countEl       = document.getElementById('vd-count');
  var sizeTotalEl   = document.getElementById('vd-size-total');
  var selectedInfo  = document.getElementById('vd-selected-info');
  var selectedCount = document.getElementById('vd-selected-count');

  /* ── Load from localStorage ── */
  function load() {
    try {
      var raw = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '[]');
      videos = Array.isArray(raw) ? raw : [];
    } catch (e) { videos = []; }
  }

  function save() {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(videos));
    } catch (e) {
      showToast('Almacenamiento lleno. Elimina videos para liberar espacio.', 'error');
    }
  }

  /* ── Utils ── */
  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2); }

  function fmtSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  function fmtDuration(secs) {
    if (!secs || isNaN(secs)) return '';
    var m = Math.floor(secs / 60), s = Math.floor(secs % 60);
    return m + ':' + (s < 10 ? '0' : '') + s;
  }

  function fmtDate(iso) {
    try { return new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium' }).format(new Date(iso)); }
    catch (e) { return iso ? iso.slice(0, 10) : ''; }
  }

  function escHtml(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  /* ── Toast ── */
  var _toastTimer;
  function showToast(msg, type) {
    toast.textContent = msg;
    toast.className = 'vd-toast visible' + (type ? ' ' + type : '');
    clearTimeout(_toastTimer);
    _toastTimer = setTimeout(function () { toast.className = 'vd-toast'; }, 3200);
  }

  /* ── Update stats ── */
  function updateStats() {
    var query = (searchInput.value || '').toLowerCase();
    var visible = query ? videos.filter(function (v) { return v.name.toLowerCase().includes(query); }) : videos;
    if (countEl) countEl.textContent = String(visible.length);
    var total = videos.reduce(function (acc, v) { return acc + (v.size || 0); }, 0);
    if (sizeTotalEl) sizeTotalEl.textContent = fmtSize(total);
    if (selected.size > 0) {
      if (selectedInfo) selectedInfo.style.display = '';
      if (selectedCount) selectedCount.textContent = String(selected.size);
    } else {
      if (selectedInfo) selectedInfo.style.display = 'none';
    }
    if (deleteSelBtn) deleteSelBtn.disabled = selected.size === 0;
  }

  /* ── Render ── */
  function render() {
    var query = (searchInput ? searchInput.value : '').toLowerCase();
    var filtered = query ? videos.filter(function (v) { return v.name.toLowerCase().includes(query); }) : videos;

    /* remove existing cards */
    Array.from(grid.querySelectorAll('.vd-card')).forEach(function (el) { el.remove(); });

    if (!filtered.length) {
      emptyState.style.display = '';
      updateStats();
      return;
    }
    emptyState.style.display = 'none';

    filtered.forEach(function (v) {
      var card = document.createElement('div');
      card.className = 'vd-card';
      card.dataset.id = v.id;

      var isChecked = selected.has(v.id);
      card.innerHTML =
        '<div class="vd-card__thumb" data-play="' + escHtml(v.id) + '">' +
          (v.dataUrl
            ? '<video src="' + escHtml(v.dataUrl) + '" preload="metadata" muted></video>'
            : '<div class="vd-card__thumb-placeholder"><i class="fa-solid fa-film"></i></div>') +
          '<div class="vd-card__play-btn"><i class="fa-solid fa-circle-play"></i></div>' +
          (v.duration ? '<span class="vd-card__duration">' + escHtml(fmtDuration(v.duration)) + '</span>' : '') +
          '<div class="vd-card__check ' + (isChecked ? 'checked' : '') + '" data-check="' + escHtml(v.id) + '">' +
            (isChecked ? '<i class="fa-solid fa-check"></i>' : '') +
          '</div>' +
        '</div>' +
        '<div class="vd-card__body">' +
          '<p class="vd-card__name" title="' + escHtml(v.name) + '">' + escHtml(v.name) + '</p>' +
          '<div class="vd-card__meta">' +
            '<span>' + escHtml(fmtSize(v.size || 0)) + '</span>' +
            '<span>' + escHtml(fmtDate(v.date)) + '</span>' +
          '</div>' +
        '</div>' +
        '<div class="vd-card__actions">' +
          '<button class="vd-card__action-btn" title="Reproducir" data-play="' + escHtml(v.id) + '"><i class="fa-solid fa-play"></i></button>' +
          '<button class="vd-card__action-btn" title="Copiar URL" data-copy="' + escHtml(v.id) + '"><i class="fa-solid fa-link"></i></button>' +
          '<button class="vd-card__action-btn vd-card__action-btn--danger" title="Eliminar" data-delete="' + escHtml(v.id) + '"><i class="fa-solid fa-trash"></i></button>' +
        '</div>';
      grid.insertBefore(card, emptyState);
    });
    updateStats();
  }

  /* ── Play modal ── */
  function openPlayer(id) {
    var v = videos.find(function (x) { return x.id === id; });
    if (!v || !v.dataUrl) return;
    modalVideo.src = v.dataUrl;
    if (modalTitle) modalTitle.textContent = v.name;
    if (modalMeta) modalMeta.textContent = fmtSize(v.size || 0) + ' · ' + fmtDate(v.date) + (v.duration ? ' · ' + fmtDuration(v.duration) : '');
    modal.hidden = false;
    modalVideo.play().catch(function () {});
  }

  function closePlayer() {
    modal.hidden = true;
    modalVideo.pause();
    modalVideo.src = '';
  }

  if (modalClose) modalClose.addEventListener('click', closePlayer);
  modal.addEventListener('click', function (e) { if (e.target === modal) closePlayer(); });

  /* ── Selection ── */
  function toggleSelect(id) {
    if (selected.has(id)) { selected.delete(id); } else { selected.add(id); }
    render();
  }

  /* ── Delete confirm ── */
  function askDelete(ids, label) {
    pendingDeleteIds = ids;
    if (confirmMsg) confirmMsg.textContent = label;
    confirm_.hidden = false;
  }

  if (confirmCancel) confirmCancel.addEventListener('click', function () { confirm_.hidden = true; pendingDeleteIds = []; });
  if (confirmOk) confirmOk.addEventListener('click', function () {
    confirm_.hidden = true;
    pendingDeleteIds.forEach(function (id) {
      videos = videos.filter(function (v) { return v.id !== id; });
      selected.delete(id);
    });
    pendingDeleteIds = [];
    save();
    render();
    showToast('Video(s) eliminado(s).', 'success');
  });

  /* ── Grid event delegation ── */
  grid.addEventListener('click', function (e) {
    var playEl = e.target.closest('[data-play]');
    var checkEl = e.target.closest('[data-check]');
    var copyEl = e.target.closest('[data-copy]');
    var deleteEl = e.target.closest('[data-delete]');
    if (checkEl) { toggleSelect(checkEl.dataset.check); return; }
    if (deleteEl) {
      var id = deleteEl.dataset.delete;
      var v = videos.find(function (x) { return x.id === id; });
      askDelete([id], '¿Eliminar "' + (v ? v.name : id) + '"? Esta acción no se puede deshacer.');
      return;
    }
    if (copyEl) {
      var vid = videos.find(function (x) { return x.id === copyEl.dataset.copy; });
      if (vid && vid.dataUrl) {
        navigator.clipboard.writeText(vid.dataUrl).then(function () { showToast('URL copiada.', 'success'); }).catch(function () { showToast('No se pudo copiar.', 'error'); });
      }
      return;
    }
    if (playEl) { openPlayer(playEl.dataset.play); }
  });

  /* ── Delete selected ── */
  if (deleteSelBtn) deleteSelBtn.addEventListener('click', function () {
    if (!selected.size) return;
    askDelete(Array.from(selected), '¿Eliminar ' + selected.size + ' video(s) seleccionado(s)? Esta acción no se puede deshacer.');
  });

  /* ── Search ── */
  if (searchInput) searchInput.addEventListener('input', function () { render(); });

  /* ── File processing ── */
  function processFiles(files) {
    var arr = Array.from(files).filter(function (f) { return f.type.startsWith('video/'); });
    if (!arr.length) { showToast('Selecciona archivos de video válidos.', 'error'); return; }
    var maxMB = 500;
    arr = arr.filter(function (f) {
      if (f.size > maxMB * 1048576) {
        showToast('"' + f.name + '" supera los ' + maxMB + ' MB.', 'error');
        return false;
      }
      return true;
    });
    if (!arr.length) return;
    processNext(arr, 0);
  }

  function processNext(files, idx) {
    if (idx >= files.length) {
      save();
      render();
      showToast(files.length + ' video(s) subido(s).', 'success');
      progressWrap.classList.remove('visible');
      return;
    }
    var file = files[idx];
    progressWrap.classList.add('visible');
    if (progressName) progressName.textContent = file.name;
    if (progressPct) progressPct.textContent = '0%';
    if (progressFill) progressFill.style.width = '0%';

    var reader = new FileReader();
    reader.onprogress = function (e) {
      if (e.lengthComputable) {
        var pct = Math.round((e.loaded / e.total) * 100);
        if (progressFill) progressFill.style.width = pct + '%';
        if (progressPct) progressPct.textContent = pct + '%';
      }
    };
    reader.onload = function (e) {
      var dataUrl = e.target.result;
      /* get duration via temp video element */
      var tmpVideo = document.createElement('video');
      tmpVideo.preload = 'metadata';
      tmpVideo.src = dataUrl;
      tmpVideo.onloadedmetadata = function () {
        var duration = isFinite(tmpVideo.duration) ? tmpVideo.duration : 0;
        tmpVideo.src = '';
        videos.unshift({
          id: uid(),
          name: file.name,
          size: file.size,
          mimeType: file.type,
          date: new Date().toISOString(),
          dataUrl: dataUrl,
          duration: duration,
        });
        if (progressFill) progressFill.style.width = '100%';
        if (progressPct) progressPct.textContent = '100%';
        processNext(files, idx + 1);
      };
      tmpVideo.onerror = function () {
        videos.unshift({
          id: uid(),
          name: file.name,
          size: file.size,
          mimeType: file.type,
          date: new Date().toISOString(),
          dataUrl: dataUrl,
          duration: 0,
        });
        processNext(files, idx + 1);
      };
    };
    reader.onerror = function () {
      showToast('Error leyendo "' + file.name + '".', 'error');
      processNext(files, idx + 1);
    };
    reader.readAsDataURL(file);
  }

  /* ── Upload button / file input ── */
  if (uploadBtn) uploadBtn.addEventListener('click', function () { fileInput.click(); });
  if (dropZone) dropZone.addEventListener('click', function (e) {
    if (e.target === dropZone || e.target.closest('.vd-upload-zone__icon, .vd-upload-zone__title, .vd-upload-zone__hint, .vd-upload-zone__formats')) {
      fileInput.click();
    }
  });
  if (fileInput) fileInput.addEventListener('change', function () { if (fileInput.files.length) processFiles(fileInput.files); fileInput.value = ''; });

  /* ── Drag & drop ── */
  if (dropZone) {
    dropZone.addEventListener('dragover', function (e) { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', function () { dropZone.classList.remove('drag-over'); });
    dropZone.addEventListener('drop', function (e) {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      if (e.dataTransfer && e.dataTransfer.files.length) processFiles(e.dataTransfer.files);
    });
  }

  /* ── Init ── */
  load();
  render();

})();
</script>
</body>
</html>
"""
