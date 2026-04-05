from __future__ import annotations


def apartados_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Apartados</title>
  <link rel="stylesheet" href="/multitienda/static/css/apartados.css" />
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
      <button class="ap-btn ap-btn--primary" id="ap-detail-reactivar-btn" style="display:none">
        <i class="fa-solid fa-rotate-right" style="margin-right:5px"></i>Reactivar
      </button>
      <button class="ap-btn ap-btn--success" id="ap-detail-entregar-btn">
        <i class="fa-solid fa-box-open" style="margin-right:5px"></i>Marcar entregado
      </button>
      <button class="ap-btn ap-btn--secondary" id="ap-detail-close-btn">Cerrar</button>
    </div>
  </div>
</div>

<script>
(function () {

  // ── State ─────────────────────────────────────────────────────────────────
  var allApartados = [];

  // ── Helpers ───────────────────────────────────────────────────────────────
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
    // balance_due is kept current by the API; paid = total - balance_due
    var total = parseFloat(ap.total_amount || ap.precio || 0);
    var bal   = parseFloat(ap.balance_due || 0);
    return Math.max(0, total - bal);
  }
  function setText(id, val) { var el = document.getElementById(id); if (el) el.textContent = val; }

  // ── API ───────────────────────────────────────────────────────────────────
  function apiGet(url)           { return fetch(url).then(function(r){ return r.json(); }); }
  function apiPost(url, body)    { return fetch(url, { method: 'POST',   headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }).then(function(r){ return r.json(); }); }
  function apiPut(url, body)     { return fetch(url, { method: 'PUT',    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }).then(function(r){ return r.json(); }); }
  function apiDelete(url)        { return fetch(url, { method: 'DELETE' }).then(function(r){ return r.json(); }); }

  // ── Load + render all ─────────────────────────────────────────────────────
  function loadAll() {
    // First mark overdue, then load list
    apiPost('/multitienda/api/apartados/vencer', {}).catch(function(){}).finally(function(){
      apiGet('/multitienda/api/apartados').then(function(j) {
        allApartados = j.success ? (j.data || []) : [];
        refreshStats();
        renderAll();
      }).catch(function(){ allApartados = []; renderAll(); });
    });
  }

  // ── Stats ─────────────────────────────────────────────────────────────────
  function refreshStats() {
    var list        = allApartados;
    var activos     = list.filter(function(a){ return a.status === 'active'; });
    var vencer      = activos.filter(function(a){ return inDays(a.due_date, 7); });
    var mes         = currentMonth();
    var completados = list.filter(function(a){
      return (a.status === 'completado' || a.status === 'entregado') &&
             (a.updated_at || '').slice(0,7) === mes;
    });
    var pendTotal    = activos.reduce(function(s,a){ return s + parseFloat(a.balance_due || 0); }, 0);
    var activosMonto = activos.reduce(function(s,a){ return s + parseFloat(a.total_amount || 0); }, 0);
    var compMonto    = completados.reduce(function(s,a){ return s + parseFloat(a.total_amount || 0); }, 0);

    setText('ap-stat-activos',           activos.length);
    setText('ap-stat-activos-monto',     fmt(activosMonto) + ' en productos');
    setText('ap-stat-vencer',            vencer.length);
    setText('ap-stat-completados',       completados.length);
    setText('ap-stat-completados-monto', fmt(compMonto) + ' recuperado');
    setText('ap-stat-pendiente',         fmt(pendTotal));
  }

  // ── Badge helpers ──────────────────────────────────────────────────────────
  var BADGE_CSS   = { active:'ap-badge--activo', completado:'ap-badge--completado', entregado:'ap-badge--entregado', cancelado:'ap-badge--cancelado', vencido:'ap-badge--vencido' };
  var BADGE_LABEL = { active:'Activo', completado:'Liquidado', entregado:'Entregado', cancelado:'Cancelado', vencido:'Vencido' };
  function badge(status) { return '<span class="ap-badge ' + (BADGE_CSS[status]||'') + '">' + (BADGE_LABEL[status]||status) + '</span>'; }

  // ── Row renderers ──────────────────────────────────────────────────────────
  function rowActivo(ap) {
    var precio   = parseFloat(ap.total_amount || 0);
    var pagado   = totalPagado(ap);
    var pend     = Math.max(0, parseFloat(ap.balance_due || 0));
    var pct      = precio > 0 ? Math.min(100, Math.round(pagado / precio * 100)) : 0;
    var overdue  = isOverdue(ap.due_date);
    var fillCls  = pct >= 100 ? ' ap-prog-fill--done' : (overdue ? ' ap-prog-fill--warn' : '');
    var prog     = '<div class="ap-prog-wrap">'
                 + '<div class="ap-prog-bar"><div class="ap-prog-fill' + fillCls + '" style="width:' + pct + '%"></div></div>'
                 + '<span class="ap-prog-pct">' + pct + '%</span>'
                 + '</div>';
    var fechaLbl = ap.due_date
      ? (overdue ? '<span class="ap-overdue-dot"></span>' : '') + escHtml(ap.due_date)
      : '—';
    return '<tr data-id="' + ap.id + '" data-drawer="detail">'
      + '<td><code style="font-size:0.82rem">' + escHtml(ap.folio || ('#' + ap.id)) + '</code></td>'
      + '<td><div class="ap-client"><span class="ap-client__name">' + escHtml(ap.customer_name || '') + '</span>'
      + '<span class="ap-client__tel">' + escHtml(ap.customer_phone || '') + '</span></div></td>'
      + '<td>' + escHtml(ap.product_name || '') + '</td>'
      + '<td class="ap-money">' + fmt(precio) + '</td>'
      + '<td class="ap-money ap-money--paid">' + fmt(pagado) + '</td>'
      + '<td class="ap-money ap-money--pend">' + fmt(pend) + '</td>'
      + '<td>' + prog + '</td>'
      + '<td style="white-space:nowrap">' + fechaLbl + '</td>'
      + '<td>' + badge(ap.status) + '</td>'
      + '</tr>';
  }

  function rowCompletado(ap) {
    var precio = parseFloat(ap.total_amount || 0);
    return '<tr data-id="' + ap.id + '" data-drawer="detail">'
      + '<td><code style="font-size:0.82rem">' + escHtml(ap.folio || ('#' + ap.id)) + '</code></td>'
      + '<td><div class="ap-client"><span class="ap-client__name">' + escHtml(ap.customer_name || '') + '</span>'
      + '<span class="ap-client__tel">' + escHtml(ap.customer_phone || '') + '</span></div></td>'
      + '<td>' + escHtml(ap.product_name || '') + '</td>'
      + '<td class="ap-money">' + fmt(precio) + '</td>'
      + '<td>—</td>'
      + '<td style="white-space:nowrap">' + escHtml((ap.updated_at || '').slice(0,10)) + '</td>'
      + '<td>' + badge(ap.status) + '</td>'
      + '</tr>';
  }

  function rowCancelado(ap) {
    var precio  = parseFloat(ap.total_amount || 0);
    var pagado  = totalPagado(ap);
    return '<tr data-id="' + ap.id + '" data-drawer="detail">'
      + '<td><code style="font-size:0.82rem">' + escHtml(ap.folio || ('#' + ap.id)) + '</code></td>'
      + '<td><div class="ap-client"><span class="ap-client__name">' + escHtml(ap.customer_name || '') + '</span>'
      + '<span class="ap-client__tel">' + escHtml(ap.customer_phone || '') + '</span></div></td>'
      + '<td>' + escHtml(ap.product_name || '') + '</td>'
      + '<td class="ap-money">' + fmt(precio) + '</td>'
      + '<td class="ap-money ap-money--warn">' + fmt(pagado) + '</td>'
      + '<td style="white-space:nowrap">' + escHtml(ap.due_date || '') + '</td>'
      + '<td>' + badge(ap.status) + '</td>'
      + '</tr>';
  }

  function emptyRow(cols, icon, msg) {
    return '<tr class="ap-table__empty"><td colspan="' + cols + '"><i class="fa-solid ' + icon + '" style="font-size:1.8rem;margin-bottom:10px;display:block;opacity:.3"></i>' + msg + '</td></tr>';
  }

  function filterList(list, tab, search) {
    return list.filter(function(ap){
      if (tab === 'activos'    && ap.status !== 'active')     return false;
      if (tab === 'completados'&& ap.status !== 'completado' && ap.status !== 'entregado') return false;
      if (tab === 'cancelados' && ap.status !== 'cancelado'  && ap.status !== 'vencido')   return false;
      if (search) {
        var hay = ((ap.folio||'') + ' ' + (ap.customer_name||'') + ' ' + (ap.product_name||'')).toLowerCase();
        if (hay.indexOf(search.toLowerCase()) < 0) return false;
      }
      return true;
    });
  }

  function renderTab(tab, searchId) {
    var search   = (document.getElementById(searchId) && document.getElementById(searchId).value) || '';
    var filtered = filterList(allApartados, tab, search);
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

  function renderAll() {
    renderTab('activos',     'ap-search-activos');
    renderTab('completados', 'ap-search-completados');
    renderTab('cancelados',  'ap-search-cancelados');
  }

  // ── Tab switching ──────────────────────────────────────────────────────────
  document.querySelectorAll('.ap-tab').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.ap-tab').forEach(function(b){ b.classList.remove('is-active'); });
      document.querySelectorAll('.ap-tab-panel').forEach(function(p){ p.classList.remove('is-active'); });
      btn.classList.add('is-active');
      var panel = document.getElementById('ap-panel-' + btn.dataset.tab);
      if (panel) panel.classList.add('is-active');
    });
  });

  // ── Search ─────────────────────────────────────────────────────────────────
  ['activos','completados','cancelados'].forEach(function(tab){
    var el = document.getElementById('ap-search-' + tab);
    if (el) el.addEventListener('input', function(){ renderTab(tab, 'ap-search-' + tab); });
  });

  // ── Row click → detail drawer ──────────────────────────────────────────────
  document.addEventListener('click', function(e){
    var tr = e.target.closest('tr[data-id][data-drawer]');
    if (!tr) return;
    if (tr.dataset.drawer === 'detail') openDetailDrawer(parseInt(tr.dataset.id));
  });

  // ──────────────────────────────────────────────────────────────────────────
  // NEW / EDIT DRAWER
  // ──────────────────────────────────────────────────────────────────────────
  var newDrawerBg = document.getElementById('ap-new-drawer-bg');
  var newEditingId = null;

  function openNewDrawer(id) {
    newEditingId = id;
    var ap = id ? allApartados.find(function(a){ return a.id === id; }) : null;
    document.getElementById('ap-new-title').textContent = id ? 'Editar apartado' : 'Nuevo apartado';
    document.getElementById('ap-f-nombre').value       = ap ? (ap.customer_name  || '') : '';
    document.getElementById('ap-f-tel').value          = ap ? (ap.customer_phone || '') : '';
    document.getElementById('ap-f-email').value        = ap ? (ap.customer_email || '') : '';
    document.getElementById('ap-f-producto').value     = ap ? (ap.product_name   || '') : '';
    document.getElementById('ap-f-sku').value          = ap ? (ap.product_sku    || '') : '';
    document.getElementById('ap-f-precio').value       = ap ? (ap.total_amount   || '') : '';
    document.getElementById('ap-f-enganche').value     = ap ? (ap.downpayment    || '') : '';
    document.getElementById('ap-f-saldo').value        = ap ? (ap.balance_due    || '') : '';
    document.getElementById('ap-f-modalidad').value    = ap ? (ap.modalidad || 'libre') : 'libre';
    document.getElementById('ap-f-cuotas').value       = ap ? (ap.cuotas || '')         : '';
    document.getElementById('ap-f-periodicidad').value = ap ? (ap.periodicidad || 'mensual') : 'mensual';
    document.getElementById('ap-f-fecha-inicio').value = ap ? (ap.start_date || '')     : today();
    document.getElementById('ap-f-fecha-limite').value = ap ? (ap.due_date   || '')     : '';
    document.getElementById('ap-f-notas').value        = ap ? (ap.notes      || '')     : '';
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
    document.getElementById('ap-f-cuotas-wrap').style.display      = val === 'cuotas' ? 'block' : 'none';
    document.getElementById('ap-f-cuota-monto-row').style.display  = val === 'cuotas' ? 'grid'  : 'none';
  }
  document.getElementById('ap-f-modalidad').addEventListener('change', toggleModalidad);

  document.getElementById('ap-new-save-btn').addEventListener('click', function(){
    var nombre   = document.getElementById('ap-f-nombre').value.trim();
    var producto = document.getElementById('ap-f-producto').value.trim();
    var precio   = parseFloat(document.getElementById('ap-f-precio').value || 0);
    var enganche = parseFloat(document.getElementById('ap-f-enganche').value || 0);
    var fechaLim = document.getElementById('ap-f-fecha-limite').value;
    if (!nombre)   { document.getElementById('ap-f-nombre').focus();        return; }
    if (!producto) { document.getElementById('ap-f-producto').focus();      return; }
    if (!precio)   { document.getElementById('ap-f-precio').focus();        return; }
    if (!fechaLim) { document.getElementById('ap-f-fecha-limite').focus();  return; }

    var payload = {
      customer_name:  nombre,
      customer_phone: document.getElementById('ap-f-tel').value.trim(),
      customer_email: document.getElementById('ap-f-email').value.trim(),
      product_name:   producto,
      product_sku:    document.getElementById('ap-f-sku').value.trim(),
      total_amount:   precio,
      downpayment:    enganche,
      balance_due:    Math.max(0, precio - enganche),
      modalidad:      document.getElementById('ap-f-modalidad').value,
      cuotas:         parseInt(document.getElementById('ap-f-cuotas').value || 0),
      periodicidad:   document.getElementById('ap-f-periodicidad').value,
      start_date:     document.getElementById('ap-f-fecha-inicio').value,
      due_date:       fechaLim,
      notes:          document.getElementById('ap-f-notas').value.trim(),
    };

    var saveBtn = document.getElementById('ap-new-save-btn');
    saveBtn.disabled = true;

    var req = newEditingId
      ? apiPut('/multitienda/api/apartados/' + newEditingId + '/editar', payload)
      : apiPost('/multitienda/api/apartados/crear', payload);

    req.then(function(j){
      saveBtn.disabled = false;
      if (j.success) { closeNewDrawer(); loadAll(); }
      else { alert('Error al guardar: ' + (j.detail || '')); }
    }).catch(function(){ saveBtn.disabled = false; alert('Error de conexión.'); });
  });

  document.getElementById('ap-new-delete-btn').addEventListener('click', function(){
    if (!newEditingId) return;
    if (!confirm('¿Eliminar este apartado permanentemente?')) return;
    apiDelete('/multitienda/api/apartados/' + newEditingId)
      .then(function(j){ if (j.success) { closeNewDrawer(); loadAll(); } });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // DETAIL DRAWER (abonos)
  // ──────────────────────────────────────────────────────────────────────────
  var detailDrawerBg = document.getElementById('ap-detail-drawer-bg');
  var detailId = null;
  var detailAp = null;
  var detailPayments = [];

  function openDetailDrawer(id) {
    detailId = id;
    detailAp = allApartados.find(function(a){ return a.id === id; }) || null;
    document.getElementById('ap-abono-fecha').value = today();
    document.getElementById('ap-abono-monto').value = '';
    document.getElementById('ap-abono-ref').value   = '';
    detailDrawerBg.classList.add('is-open');
    loadDetailPayments();
  }

  function loadDetailPayments() {
    if (!detailId) return;
    apiGet('/multitienda/api/apartados/' + detailId + '/pagos').then(function(j){
      detailPayments = j.success ? (j.data || []) : [];
      renderDetailDrawer();
    }).catch(function(){ renderDetailDrawer(); });
  }

  function renderDetailDrawer() {
    if (!detailAp) return;
    var ap       = detailAp;
    var precio   = parseFloat(ap.total_amount || 0);
    var pagado   = totalPagado(ap);
    var pend     = parseFloat(ap.balance_due || 0);
    var pct      = precio > 0 ? Math.min(100, Math.round(pagado / precio * 100)) : 0;

    document.getElementById('ap-detail-title').textContent    = ap.folio || ('#' + ap.id);
    document.getElementById('ap-detail-subtitle').textContent = (ap.product_name || '') + ' · ' + (ap.customer_name || '');
    document.getElementById('ap-dp-pct').textContent  = pct + '%';
    document.getElementById('ap-dp-total').textContent    = fmt(precio);
    document.getElementById('ap-dp-pagado').textContent   = fmt(pagado);
    document.getElementById('ap-dp-pendiente').textContent = fmt(pend);

    var bar = document.getElementById('ap-dp-bar');
    bar.style.width = pct + '%';
    bar.className   = 'ap-detail-fill' + (pct >= 100 ? ' ap-detail-fill--done' : '');

    // Abonos list (enganche as first row + real payments)
    var abonosList  = document.getElementById('ap-abonos-list');
    var engancheRow = { amount: ap.downpayment, paid_at: ap.start_date, method: 'enganche', reference: 'Enganche inicial', _eng: true };
    var allPayRows  = [engancheRow].concat(detailPayments);

    if (!allPayRows.length || (allPayRows.length === 1 && !parseFloat(allPayRows[0].amount))) {
      abonosList.innerHTML = '<div class="ap-abonos-empty">Sin abonos registrados aún.</div>';
    } else {
      abonosList.innerHTML = allPayRows.map(function(ab){
        var isEng = !!ab._eng;
        return '<div class="ap-abono-row">'
          + '<div class="ap-abono-row__icon"><i class="fa-solid ' + (isEng ? 'fa-handshake' : 'fa-coins') + '"></i></div>'
          + '<div class="ap-abono-row__info">'
          + '<div class="ap-abono-row__fecha">' + escHtml(ab.paid_at || '') + (isEng ? ' — <strong>Enganche</strong>' : '') + '</div>'
          + '<div class="ap-abono-row__metodo">' + escHtml(ab.method || '') + (ab.reference ? ' · ' + escHtml(ab.reference) : '') + '</div>'
          + '</div>'
          + '<span class="ap-abono-row__monto">' + fmt(ab.amount) + '</span>'
          + (!isEng ? '<button class="ap-abono-row__del" data-pay-id="' + ab.id + '" title="Eliminar abono"><i class="fa-solid fa-trash"></i></button>' : '')
          + '</div>';
      }).join('');
    }

    // Buttons visibility
    var isActive = ap.status === 'active';
    var isDone   = ap.status === 'completado';
    document.getElementById('ap-abono-form').style.display            = isActive ? 'block'       : 'none';
    document.getElementById('ap-detail-entregar-btn').style.display   = isDone   ? 'inline-flex' : 'none';
    document.getElementById('ap-detail-cancel-ap-btn').style.display  = isActive ? 'inline-flex' : 'none';
    document.getElementById('ap-detail-reactivar-btn').style.display  = (ap.status === 'cancelado' || ap.status === 'vencido') ? 'inline-flex' : 'none';
  }

  // Delete payment
  document.getElementById('ap-abonos-list').addEventListener('click', function(e){
    var btn = e.target.closest('[data-pay-id]');
    if (!btn) return;
    var payId = parseInt(btn.dataset.payId);
    if (!confirm('¿Eliminar este abono?')) return;
    apiDelete('/multitienda/api/apartados/' + detailId + '/pagos/' + payId)
      .then(function(j){
        if (j.success) {
          // refresh the ap in allApartados
          loadAllAndKeepDrawer();
        }
      });
  });

  // Save abono
  document.getElementById('ap-abono-save-btn').addEventListener('click', function(){
    var monto = parseFloat(document.getElementById('ap-abono-monto').value || 0);
    if (!monto) { document.getElementById('ap-abono-monto').focus(); return; }
    var payload = {
      amount:    monto,
      paid_at:   document.getElementById('ap-abono-fecha').value || today(),
      method:    document.getElementById('ap-abono-metodo').value,
      reference: document.getElementById('ap-abono-ref').value.trim(),
    };
    apiPost('/multitienda/api/apartados/' + detailId + '/pagos', payload).then(function(j){
      if (j.success) {
        document.getElementById('ap-abono-monto').value = '';
        document.getElementById('ap-abono-ref').value   = '';
        loadAllAndKeepDrawer();
      } else { alert('Error al registrar abono.'); }
    }).catch(function(){ alert('Error de conexión.'); });
  });

  // Marcar entregado
  document.getElementById('ap-detail-entregar-btn').addEventListener('click', function(){
    apiPost('/multitienda/api/apartados/' + detailId + '/entregar', {}).then(function(j){
      if (j.success) { loadAllAndKeepDrawer(); }
    });
  });

  // Cancelar apartado
  document.getElementById('ap-detail-cancel-ap-btn').addEventListener('click', function(){
    if (!detailAp) return;
    if (!confirm('¿Cancelar este apartado? El cliente ha pagado ' + fmt(totalPagado(detailAp)) + ' hasta ahora.')) return;
    apiPost('/multitienda/api/apartados/' + detailId + '/cancelar', {}).then(function(j){
      if (j.success) { loadAllAndKeepDrawer(); }
    });
  });

  // Reactivar apartado (button is dynamically shown for cancelado/vencido)
  document.getElementById('ap-detail-reactivar-btn').addEventListener('click', function(){
    if (!confirm('¿Reactivar este apartado?')) return;
    apiPost('/multitienda/api/apartados/' + detailId + '/reactivar', {}).then(function(j){
      if (j.success) { loadAllAndKeepDrawer(); }
    });
  });

  // Edit from detail drawer
  document.getElementById('ap-detail-edit-btn').addEventListener('click', function(){
    closeDetailDrawer();
    openNewDrawer(detailId);
  });

  function loadAllAndKeepDrawer() {
    apiPost('/multitienda/api/apartados/vencer', {}).catch(function(){}).finally(function(){
      apiGet('/multitienda/api/apartados').then(function(j){
        allApartados = j.success ? (j.data || []) : [];
        refreshStats();
        renderAll();
        // refresh detailAp and payments if drawer still open
        if (detailId) {
          detailAp = allApartados.find(function(a){ return a.id === detailId; }) || null;
          loadDetailPayments();
        }
      });
    });
  }

  function closeDetailDrawer() { detailDrawerBg.classList.remove('is-open'); detailId = null; detailAp = null; detailPayments = []; }
  document.getElementById('ap-detail-close-btn').addEventListener('click', closeDetailDrawer);
  detailDrawerBg.addEventListener('click', function(e){ if (e.target === detailDrawerBg) closeDetailDrawer(); });

  // ── Init ──────────────────────────────────────────────────────────────────
  loadAll();
})();
</script>
</body>
</html>"""
