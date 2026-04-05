from __future__ import annotations


def subastas_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Subastas</title>
  <link rel="stylesheet" href="/multitienda/static/css/subastas.css" />
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
