from __future__ import annotations


def repartidores_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Repartidores</title>
  <link rel="stylesheet" href="/multitienda/static/css/repartidores.css" />
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
