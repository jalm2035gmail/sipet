from __future__ import annotations


def institucion_financiera_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Institución financiera</title>
  <link rel="stylesheet" href="/multitienda/static/css/institucion-financiera.css" />
</head>
<body>
<main class="if-page">

  <!-- Hero -->
  <div class="if-hero">
    <div class="if-hero__inner">
      <div class="if-hero__icon"><i class="fa-solid fa-building-columns" aria-hidden="true"></i></div>
      <div class="if-hero__copy">
        <h1>Institución financiera</h1>
        <p>Control de comisiones por colocación de créditos y ventas con recursos de la institución financiera.</p>
        <div class="if-hero__badges">
          <span class="if-hero__badge if-hero__badge--credito"><i class="fa-solid fa-hand-holding-dollar"></i> Colocación</span>
          <span class="if-hero__badge if-hero__badge--venta"><i class="fa-solid fa-receipt"></i> Ventas</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Stats -->
  <div class="if-stats">
    <div class="if-stat">
      <div class="if-stat__value" id="if-stat-pendiente">—</div>
      <div class="if-stat__label">Pendiente de cobro</div>
      <div class="if-stat__sub" id="if-stat-pendiente-n">— registros</div>
    </div>
    <div class="if-stat">
      <div class="if-stat__value" id="if-stat-pagado">—</div>
      <div class="if-stat__label">Cobrado este mes</div>
      <div class="if-stat__sub" id="if-stat-pagado-n">— pagos</div>
    </div>
    <div class="if-stat">
      <div class="if-stat__value" id="if-stat-creditos">—</div>
      <div class="if-stat__label">Créditos colocados</div>
      <div class="if-stat__sub" id="if-stat-creditos-sub">activos</div>
    </div>
    <div class="if-stat">
      <div class="if-stat__value" id="if-stat-tasa">—</div>
      <div class="if-stat__label">Tasa promedio comisión</div>
      <div class="if-stat__sub">sobre monto colocado</div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="if-tabs">
    <button class="if-tab is-active" data-tab="comisiones">Comisiones</button>
    <button class="if-tab" data-tab="creditos">Créditos colocados</button>
    <button class="if-tab" data-tab="edc">Estado de cuenta</button>
  </div>

  <!-- Panel: Comisiones -->
  <div class="if-tab-panel is-active" id="if-panel-comisiones">
    <div class="if-toolbar">
      <input class="if-search" type="search" id="if-com-search" placeholder="Buscar por folio, socio…" />
      <select class="if-filter" id="if-com-filter-tipo">
        <option value="">Tipo: todos</option>
        <option value="credito">Crédito</option>
        <option value="venta">Venta</option>
      </select>
      <select class="if-filter" id="if-com-filter-estado">
        <option value="">Estado: todos</option>
        <option value="pendiente">Pendiente</option>
        <option value="aprobada">Aprobada</option>
        <option value="pagada">Pagada</option>
        <option value="rechazada">Rechazada</option>
      </select>
      <button class="if-btn-add" id="if-com-add-btn">
        <i class="fa-solid fa-plus" aria-hidden="true"></i> Registrar comisión
      </button>
    </div>
    <div class="if-table-wrap">
      <table class="if-table" id="if-com-table">
        <thead>
          <tr>
            <th>Folio</th>
            <th>Tipo</th>
            <th>Socio / Cliente</th>
            <th>Monto base</th>
            <th>% Comisión</th>
            <th>Comisión</th>
            <th>Estado</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody id="if-com-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- Panel: Créditos colocados -->
  <div class="if-tab-panel" id="if-panel-creditos">
    <div class="if-toolbar">
      <input class="if-search" type="search" id="if-cred-search" placeholder="Buscar por folio, socio…" />
      <select class="if-filter" id="if-cred-filter-estado">
        <option value="">Estado: todos</option>
        <option value="vigente">Vigente</option>
        <option value="colocado">Colocado</option>
        <option value="vencido">Vencido</option>
        <option value="cancelado">Cancelado</option>
      </select>
      <button class="if-btn-add" id="if-cred-add-btn">
        <i class="fa-solid fa-plus" aria-hidden="true"></i> Registrar crédito
      </button>
    </div>
    <div class="if-table-wrap">
      <table class="if-table" id="if-cred-table">
        <thead>
          <tr>
            <th>Folio</th>
            <th>Socio / Cliente</th>
            <th>Producto</th>
            <th>Monto crédito</th>
            <th>Plazo</th>
            <th>Comisión generada</th>
            <th>Estado</th>
            <th>Fecha colocación</th>
          </tr>
        </thead>
        <tbody id="if-cred-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- Panel: Estado de cuenta -->
  <div class="if-tab-panel" id="if-panel-edc">
    <div class="if-edc">
      <div class="if-edc-header">
        <div>
          <label>Período</label>
          <input type="month" id="if-edc-mes" />
        </div>
        <div>
          <label>Tipo</label>
          <select id="if-edc-tipo-filter">
            <option value="">Todos</option>
            <option value="credito">Crédito</option>
            <option value="venta">Venta</option>
          </select>
        </div>
        <button class="if-edc-download" id="if-edc-download-btn">
          <i class="fa-solid fa-file-arrow-down" aria-hidden="true"></i> Exportar resumen
        </button>
      </div>

      <div class="if-edc-summary" id="if-edc-summary-cards">
        <div class="if-edc-card">
          <div class="if-edc-card__label">Comisiones del período</div>
          <div class="if-edc-card__value" id="if-edc-total">$0.00</div>
          <div class="if-edc-card__sub" id="if-edc-total-n">0 registros</div>
        </div>
        <div class="if-edc-card">
          <div class="if-edc-card__label">Pendientes</div>
          <div class="if-edc-card__value" id="if-edc-pend">$0.00</div>
          <div class="if-edc-card__sub" id="if-edc-pend-n">0 registros</div>
        </div>
        <div class="if-edc-card">
          <div class="if-edc-card__label">Cobradas</div>
          <div class="if-edc-card__value" id="if-edc-cob">$0.00</div>
          <div class="if-edc-card__sub" id="if-edc-cob-n">0 registros</div>
        </div>
        <div class="if-edc-card">
          <div class="if-edc-card__label">Créditos colocados</div>
          <div class="if-edc-card__value" id="if-edc-cred-monto">$0.00</div>
          <div class="if-edc-card__sub" id="if-edc-cred-n">0 créditos</div>
        </div>
      </div>

      <div class="if-edc-table-wrap">
        <table class="if-edc-table">
          <thead>
            <tr>
              <th>Folio</th>
              <th>Tipo</th>
              <th>Concepto</th>
              <th>Monto base</th>
              <th>% Com.</th>
              <th>Comisión</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody id="if-edc-tbody"></tbody>
          <tfoot>
            <tr>
              <td colspan="5" style="text-align:right">Total comisiones del período</td>
              <td id="if-edc-foot-total">$0.00</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>

</main>

<!-- Drawer: Comisión -->
<div class="if-drawer-bg" id="if-com-drawer-bg" role="dialog" aria-modal="true" aria-labelledby="if-com-drawer-title">
  <div class="if-drawer">
    <h2 class="if-drawer__title" id="if-com-drawer-title">Registrar comisión</h2>
    <p class="if-drawer__subtitle" id="if-com-drawer-subtitle">Comisión por crédito o venta con recursos de la institución financiera</p>

    <div class="if-field--row">
      <div class="if-field">
        <label>Folio *</label>
        <input type="text" id="if-cf-folio" maxlength="40" placeholder="Ej. COM-2024-001" />
      </div>
      <div class="if-field">
        <label>Tipo *</label>
        <select id="if-cf-tipo">
          <option value="credito">Crédito colocado</option>
          <option value="venta">Venta con recurso inst.</option>
        </select>
      </div>
    </div>

    <div class="if-field">
      <label>Socio / Cliente *</label>
      <input type="text" id="if-cf-socio" maxlength="120" placeholder="Nombre completo" />
    </div>

    <div class="if-field--row3">
      <div class="if-field">
        <label>Monto base *</label>
        <input type="number" id="if-cf-monto-base" min="0" step="0.01" placeholder="0.00" />
      </div>
      <div class="if-field">
        <label>% Comisión</label>
        <input type="number" id="if-cf-pct" min="0" max="100" step="0.01" placeholder="0.00" />
      </div>
      <div class="if-field">
        <label>Comisión (monto)</label>
        <input type="number" id="if-cf-monto-com" min="0" step="0.01" placeholder="Auto" readonly style="background:color-mix(in srgb,var(--if-surface) 85%,var(--if-bg) 15%)" />
      </div>
    </div>

    <div class="if-field--row">
      <div class="if-field">
        <label>Fecha de operación</label>
        <input type="date" id="if-cf-fecha" />
      </div>
      <div class="if-field">
        <label>Estado</label>
        <select id="if-cf-estado">
          <option value="pendiente">Pendiente</option>
          <option value="aprobada">Aprobada</option>
          <option value="pagada">Pagada</option>
          <option value="rechazada">Rechazada</option>
        </select>
      </div>
    </div>

    <div class="if-field">
      <label>Referencia institucional</label>
      <input type="text" id="if-cf-ref" maxlength="80" placeholder="Folio o referencia de la institución financiera" />
    </div>

    <div class="if-field">
      <label>Notas</label>
      <textarea id="if-cf-notas" rows="3" placeholder="Observaciones adicionales…"></textarea>
    </div>

    <div class="if-drawer__footer">
      <button class="if-btn if-btn--danger" id="if-com-delete-btn" style="display:none">Eliminar</button>
      <button class="if-btn if-btn--secondary" id="if-com-cancel-btn">Cancelar</button>
      <button class="if-btn if-btn--primary" id="if-com-save-btn">Guardar</button>
    </div>
  </div>
</div>

<!-- Drawer: Crédito -->
<div class="if-drawer-bg" id="if-cred-drawer-bg" role="dialog" aria-modal="true" aria-labelledby="if-cred-drawer-title">
  <div class="if-drawer">
    <h2 class="if-drawer__title" id="if-cred-drawer-title">Registrar crédito colocado</h2>
    <p class="if-drawer__subtitle">Crédito intermediado o colocado con recursos de la institución financiera</p>

    <div class="if-field--row">
      <div class="if-field">
        <label>Folio *</label>
        <input type="text" id="if-kf-folio" maxlength="40" placeholder="Ej. CRED-2024-001" />
      </div>
      <div class="if-field">
        <label>Producto / Línea *</label>
        <select id="if-kf-producto">
          <option value="personal">Crédito personal</option>
          <option value="nomina">Crédito nómina</option>
          <option value="pyme">Crédito PyME</option>
          <option value="hipotecario">Hipotecario</option>
          <option value="automotriz">Automotriz</option>
          <option value="otro">Otro</option>
        </select>
      </div>
    </div>

    <div class="if-field">
      <label>Socio / Acreditado *</label>
      <input type="text" id="if-kf-socio" maxlength="120" placeholder="Nombre completo" />
    </div>

    <div class="if-field--row3">
      <div class="if-field">
        <label>Monto del crédito *</label>
        <input type="number" id="if-kf-monto" min="0" step="0.01" placeholder="0.00" />
      </div>
      <div class="if-field">
        <label>Plazo</label>
        <input type="text" id="if-kf-plazo" maxlength="30" placeholder="Ej. 24 meses" />
      </div>
      <div class="if-field">
        <label>Tasa anual (%)</label>
        <input type="number" id="if-kf-tasa" min="0" max="200" step="0.01" placeholder="0.00" />
      </div>
    </div>

    <div class="if-field--row">
      <div class="if-field">
        <label>% Comisión por colocación</label>
        <input type="number" id="if-kf-pct-com" min="0" max="100" step="0.01" placeholder="0.00" />
      </div>
      <div class="if-field">
        <label>Comisión generada</label>
        <input type="number" id="if-kf-com-monto" min="0" step="0.01" placeholder="Auto" readonly style="background:color-mix(in srgb,var(--if-surface) 85%,var(--if-bg) 15%)" />
      </div>
    </div>

    <div class="if-field--row">
      <div class="if-field">
        <label>Fecha de colocación</label>
        <input type="date" id="if-kf-fecha" />
      </div>
      <div class="if-field">
        <label>Estado</label>
        <select id="if-kf-estado">
          <option value="vigente">Vigente</option>
          <option value="colocado">Colocado</option>
          <option value="vencido">Vencido</option>
          <option value="cancelado">Cancelado</option>
        </select>
      </div>
    </div>

    <div class="if-field">
      <label>Referencia institucional</label>
      <input type="text" id="if-kf-ref" maxlength="80" placeholder="Folio de la institución financiera" />
    </div>

    <div class="if-field">
      <label>Notas</label>
      <textarea id="if-kf-notas" rows="2" placeholder="Observaciones…"></textarea>
    </div>

    <div class="if-drawer__footer">
      <button class="if-btn if-btn--danger" id="if-cred-delete-btn" style="display:none">Eliminar</button>
      <button class="if-btn if-btn--secondary" id="if-cred-cancel-btn">Cancelar</button>
      <button class="if-btn if-btn--primary" id="if-cred-save-btn">Guardar</button>
    </div>
  </div>
</div>

<script>
(function () {
  var LS_COM  = 'multitienda_if_comisiones';
  var LS_CRED = 'multitienda_if_creditos';

  // ── Storage ──────────────────────────────────────────────────────────────
  function loadCom()  { try { return JSON.parse(localStorage.getItem(LS_COM)  || '[]'); } catch { return []; } }
  function loadCred() { try { return JSON.parse(localStorage.getItem(LS_CRED) || '[]'); } catch { return []; } }
  function saveCom(d)  { localStorage.setItem(LS_COM,  JSON.stringify(d)); }
  function saveCred(d) { localStorage.setItem(LS_CRED, JSON.stringify(d)); }

  // ── Format ───────────────────────────────────────────────────────────────
  function fmt(n) { return '$' + parseFloat(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function escHtml(s) { return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function today() { return new Date().toISOString().slice(0, 10); }
  function currentMonth() { return new Date().toISOString().slice(0, 7); }

  // ── Stats ────────────────────────────────────────────────────────────────
  function refreshStats() {
    var coms  = loadCom();
    var creds = loadCred();
    var pend  = coms.filter(function(c){ return c.estado === 'pendiente' || c.estado === 'aprobada'; });
    var paid  = coms.filter(function(c){ return c.estado === 'pagada'; });
    var mes   = currentMonth();
    var paidMes = paid.filter(function(c){ return (c.fecha || '').startsWith(mes); });

    var pendMonto = pend.reduce(function(s,c){ return s + parseFloat(c.montoComision || 0); }, 0);
    var paidMonto = paidMes.reduce(function(s,c){ return s + parseFloat(c.montoComision || 0); }, 0);
    var creditosActivos = creds.filter(function(c){ return c.estado === 'vigente' || c.estado === 'colocado'; }).length;

    var totalBase  = coms.filter(function(c){ return c.montoBase > 0; }).reduce(function(s,c){ return s + parseFloat(c.montoBase || 0); }, 0);
    var totalCom   = coms.reduce(function(s,c){ return s + parseFloat(c.montoComision || 0); }, 0);
    var tasa = totalBase > 0 ? ((totalCom / totalBase) * 100).toFixed(2) + '%' : '—';

    setText('if-stat-pendiente',   fmt(pendMonto));
    setText('if-stat-pendiente-n', pend.length + ' registros');
    setText('if-stat-pagado',      fmt(paidMonto));
    setText('if-stat-pagado-n',    paidMes.length + ' pagos');
    setText('if-stat-creditos',    creditosActivos);
    setText('if-stat-creditos-sub','activos');
    setText('if-stat-tasa',        tasa);
  }

  function setText(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  // ── BADGE helpers ────────────────────────────────────────────────────────
  var BADGE_COM  = { pendiente:'if-badge--pendiente', aprobada:'if-badge--aprobada', pagada:'if-badge--pagada', rechazada:'if-badge--rechazada' };
  var BADGE_CRED = { vigente:'if-badge--vigente', colocado:'if-badge--colocado', vencido:'if-badge--vencido', cancelado:'if-badge--cancelado' };
  var BADGE_TIPO = { credito:'if-badge--credito', venta:'if-badge--venta' };
  var LABEL_COM  = { pendiente:'Pendiente', aprobada:'Aprobada', pagada:'Pagada', rechazada:'Rechazada' };
  var LABEL_CRED = { vigente:'Vigente', colocado:'Colocado', vencido:'Vencido', cancelado:'Cancelado' };
  var LABEL_TIPO = { credito:'Crédito', venta:'Venta' };

  function badge(css, label) { return '<span class="if-badge ' + css + '">' + escHtml(label) + '</span>'; }

  // ── Render comisiones ─────────────────────────────────────────────────────
  function renderCom() {
    var list   = loadCom();
    var search = (document.getElementById('if-com-search').value || '').toLowerCase();
    var fTipo  = document.getElementById('if-com-filter-tipo').value;
    var fEst   = document.getElementById('if-com-filter-estado').value;

    var filtered = list.filter(function(c){
      if (fTipo  && c.tipo   !== fTipo)  return false;
      if (fEst   && c.estado !== fEst)   return false;
      if (search && !(c.folio + ' ' + c.socio).toLowerCase().includes(search)) return false;
      return true;
    });

    var tbody = document.getElementById('if-com-tbody');
    if (!filtered.length) {
      tbody.innerHTML = '<tr class="if-table__empty"><td colspan="8"><i class="fa-solid fa-receipt" style="font-size:1.6rem;margin-bottom:8px;display:block;opacity:.3"></i>Sin comisiones registradas.</td></tr>';
      return;
    }
    tbody.innerHTML = filtered.map(function(c){
      return '<tr data-id="' + c.id + '">'
        + '<td><code style="font-size:0.82rem">' + escHtml(c.folio) + '</code></td>'
        + '<td>' + badge(BADGE_TIPO[c.tipo] || '', LABEL_TIPO[c.tipo] || c.tipo) + '</td>'
        + '<td>' + escHtml(c.socio) + '</td>'
        + '<td class="if-money">' + fmt(c.montoBase) + '</td>'
        + '<td>' + parseFloat(c.pct || 0).toFixed(2) + '%</td>'
        + '<td class="if-money if-money--pos">' + fmt(c.montoComision) + '</td>'
        + '<td>' + badge(BADGE_COM[c.estado] || '', LABEL_COM[c.estado] || c.estado) + '</td>'
        + '<td style="white-space:nowrap">' + escHtml(c.fecha || '') + '</td>'
        + '</tr>';
    }).join('');
  }

  // ── Render créditos ───────────────────────────────────────────────────────
  function renderCred() {
    var list   = loadCred();
    var search = (document.getElementById('if-cred-search').value || '').toLowerCase();
    var fEst   = document.getElementById('if-cred-filter-estado').value;

    var filtered = list.filter(function(c){
      if (fEst   && c.estado !== fEst)   return false;
      if (search && !(c.folio + ' ' + c.socio).toLowerCase().includes(search)) return false;
      return true;
    });

    var tbody = document.getElementById('if-cred-tbody');
    if (!filtered.length) {
      tbody.innerHTML = '<tr class="if-table__empty"><td colspan="8"><i class="fa-solid fa-hand-holding-dollar" style="font-size:1.6rem;margin-bottom:8px;display:block;opacity:.3"></i>Sin créditos colocados.</td></tr>';
      return;
    }
    tbody.innerHTML = filtered.map(function(c){
      return '<tr data-id="' + c.id + '" data-table="cred">'
        + '<td><code style="font-size:0.82rem">' + escHtml(c.folio) + '</code></td>'
        + '<td>' + escHtml(c.socio) + '</td>'
        + '<td>' + escHtml(c.producto || '') + '</td>'
        + '<td class="if-money">' + fmt(c.monto) + '</td>'
        + '<td>' + escHtml(c.plazo || '—') + '</td>'
        + '<td class="if-money if-money--pos">' + fmt(c.comMonto) + '</td>'
        + '<td>' + badge(BADGE_CRED[c.estado] || '', LABEL_CRED[c.estado] || c.estado) + '</td>'
        + '<td style="white-space:nowrap">' + escHtml(c.fecha || '') + '</td>'
        + '</tr>';
    }).join('');
  }

  // ── Estado de cuenta ──────────────────────────────────────────────────────
  function renderEdc() {
    var mes  = document.getElementById('if-edc-mes').value || currentMonth();
    var tipo = document.getElementById('if-edc-tipo-filter').value;
    var coms = loadCom().filter(function(c){
      if (!(c.fecha || '').startsWith(mes)) return false;
      if (tipo && c.tipo !== tipo) return false;
      return true;
    });
    var creds = loadCred().filter(function(c){ return (c.fecha || '').startsWith(mes); });

    var totalCom  = coms.reduce(function(s,c){ return s + parseFloat(c.montoComision || 0); }, 0);
    var pendCom   = coms.filter(function(c){ return c.estado === 'pendiente' || c.estado === 'aprobada'; });
    var pendMonto = pendCom.reduce(function(s,c){ return s + parseFloat(c.montoComision || 0); }, 0);
    var cobCom    = coms.filter(function(c){ return c.estado === 'pagada'; });
    var cobMonto  = cobCom.reduce(function(s,c){ return s + parseFloat(c.montoComision || 0); }, 0);
    var credMonto = creds.reduce(function(s,c){ return s + parseFloat(c.monto || 0); }, 0);

    setText('if-edc-total',     fmt(totalCom));
    setText('if-edc-total-n',   coms.length + ' registros');
    setText('if-edc-pend',      fmt(pendMonto));
    setText('if-edc-pend-n',    pendCom.length + ' registros');
    setText('if-edc-cob',       fmt(cobMonto));
    setText('if-edc-cob-n',     cobCom.length + ' registros');
    setText('if-edc-cred-monto',fmt(credMonto));
    setText('if-edc-cred-n',    creds.length + ' créditos');
    setText('if-edc-foot-total',fmt(totalCom));

    var tbody = document.getElementById('if-edc-tbody');
    if (!coms.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--if-muted)">Sin movimientos en el período seleccionado.</td></tr>';
      return;
    }
    tbody.innerHTML = coms.map(function(c){
      return '<tr>'
        + '<td><code style="font-size:0.82rem">' + escHtml(c.folio) + '</code></td>'
        + '<td>' + badge(BADGE_TIPO[c.tipo] || '', LABEL_TIPO[c.tipo] || c.tipo) + '</td>'
        + '<td>' + escHtml(c.socio) + '</td>'
        + '<td class="if-money">' + fmt(c.montoBase) + '</td>'
        + '<td>' + parseFloat(c.pct || 0).toFixed(2) + '%</td>'
        + '<td class="if-money if-money--pos">' + fmt(c.montoComision) + '</td>'
        + '<td>' + badge(BADGE_COM[c.estado] || '', LABEL_COM[c.estado] || c.estado) + '</td>'
        + '</tr>';
    }).join('');
  }

  // ── Auto-calc comisión ────────────────────────────────────────────────────
  function calcCom() {
    var base = parseFloat(document.getElementById('if-cf-monto-base').value || 0);
    var pct  = parseFloat(document.getElementById('if-cf-pct').value || 0);
    var el   = document.getElementById('if-cf-monto-com');
    if (base > 0 && pct > 0) el.value = (base * pct / 100).toFixed(2);
    else el.value = '';
  }
  document.getElementById('if-cf-monto-base').addEventListener('input', calcCom);
  document.getElementById('if-cf-pct').addEventListener('input', calcCom);

  function calcCredCom() {
    var monto = parseFloat(document.getElementById('if-kf-monto').value || 0);
    var pct   = parseFloat(document.getElementById('if-kf-pct-com').value || 0);
    var el    = document.getElementById('if-kf-com-monto');
    if (monto > 0 && pct > 0) el.value = (monto * pct / 100).toFixed(2);
    else el.value = '';
  }
  document.getElementById('if-kf-monto').addEventListener('input', calcCredCom);
  document.getElementById('if-kf-pct-com').addEventListener('input', calcCredCom);

  // ── Comisión drawer ───────────────────────────────────────────────────────
  var comEditingId = null;
  var comDrawerBg  = document.getElementById('if-com-drawer-bg');

  function openComDrawer(id) {
    comEditingId = id;
    var list = loadCom();
    var item = id ? list.find(function(c){ return c.id === id; }) : null;
    document.getElementById('if-com-drawer-title').textContent = id ? 'Editar comisión' : 'Registrar comisión';
    document.getElementById('if-cf-folio').value      = item ? item.folio      : '';
    document.getElementById('if-cf-tipo').value       = item ? item.tipo       : 'credito';
    document.getElementById('if-cf-socio').value      = item ? item.socio      : '';
    document.getElementById('if-cf-monto-base').value = item ? item.montoBase  : '';
    document.getElementById('if-cf-pct').value        = item ? item.pct        : '';
    document.getElementById('if-cf-monto-com').value  = item ? item.montoComision : '';
    document.getElementById('if-cf-fecha').value      = item ? item.fecha      : today();
    document.getElementById('if-cf-estado').value     = item ? item.estado     : 'pendiente';
    document.getElementById('if-cf-ref').value        = item ? item.ref        : '';
    document.getElementById('if-cf-notas').value      = item ? item.notas      : '';
    document.getElementById('if-com-delete-btn').style.display = id ? 'inline-flex' : 'none';
    comDrawerBg.classList.add('is-open');
    document.getElementById('if-cf-folio').focus();
  }

  function closeComDrawer() { comDrawerBg.classList.remove('is-open'); comEditingId = null; }

  document.getElementById('if-com-cancel-btn').addEventListener('click', closeComDrawer);
  comDrawerBg.addEventListener('click', function(e){ if (e.target === comDrawerBg) closeComDrawer(); });
  document.getElementById('if-com-add-btn').addEventListener('click', function(){ openComDrawer(null); });

  document.getElementById('if-com-tbody').addEventListener('click', function(e){
    var tr = e.target.closest('tr[data-id]');
    if (tr) openComDrawer(tr.dataset.id);
  });

  document.getElementById('if-com-save-btn').addEventListener('click', function(){
    var folio = document.getElementById('if-cf-folio').value.trim();
    var socio = document.getElementById('if-cf-socio').value.trim();
    if (!folio || !socio) {
      if (!folio) document.getElementById('if-cf-folio').focus();
      else document.getElementById('if-cf-socio').focus();
      return;
    }
    var pct       = parseFloat(document.getElementById('if-cf-pct').value || 0);
    var montoBase = parseFloat(document.getElementById('if-cf-monto-base').value || 0);
    var montoComRaw = parseFloat(document.getElementById('if-cf-monto-com').value || 0);
    var montoComision = montoComRaw || (montoBase > 0 && pct > 0 ? montoBase * pct / 100 : 0);
    var list = loadCom();
    var item = {
      id:            comEditingId || ('com-' + Date.now()),
      folio,
      tipo:          document.getElementById('if-cf-tipo').value,
      socio,
      montoBase,
      pct,
      montoComision,
      fecha:         document.getElementById('if-cf-fecha').value,
      estado:        document.getElementById('if-cf-estado').value,
      ref:           document.getElementById('if-cf-ref').value.trim(),
      notas:         document.getElementById('if-cf-notas').value.trim(),
    };
    if (comEditingId) {
      var idx = list.findIndex(function(c){ return c.id === comEditingId; });
      if (idx >= 0) list[idx] = item;
    } else {
      list.push(item);
    }
    saveCom(list);
    renderCom();
    refreshStats();
    closeComDrawer();
  });

  document.getElementById('if-com-delete-btn').addEventListener('click', function(){
    if (!comEditingId) return;
    saveCom(loadCom().filter(function(c){ return c.id !== comEditingId; }));
    renderCom();
    refreshStats();
    closeComDrawer();
  });

  // ── Crédito drawer ────────────────────────────────────────────────────────
  var credEditingId = null;
  var credDrawerBg  = document.getElementById('if-cred-drawer-bg');

  function openCredDrawer(id) {
    credEditingId = id;
    var list = loadCred();
    var item = id ? list.find(function(c){ return c.id === id; }) : null;
    document.getElementById('if-cred-drawer-title').textContent = id ? 'Editar crédito' : 'Registrar crédito colocado';
    document.getElementById('if-kf-folio').value    = item ? item.folio    : '';
    document.getElementById('if-kf-producto').value = item ? item.producto : 'personal';
    document.getElementById('if-kf-socio').value    = item ? item.socio    : '';
    document.getElementById('if-kf-monto').value    = item ? item.monto    : '';
    document.getElementById('if-kf-plazo').value    = item ? item.plazo    : '';
    document.getElementById('if-kf-tasa').value     = item ? item.tasa     : '';
    document.getElementById('if-kf-pct-com').value  = item ? item.pctCom   : '';
    document.getElementById('if-kf-com-monto').value= item ? item.comMonto : '';
    document.getElementById('if-kf-fecha').value    = item ? item.fecha    : today();
    document.getElementById('if-kf-estado').value   = item ? item.estado   : 'vigente';
    document.getElementById('if-kf-ref').value      = item ? item.ref      : '';
    document.getElementById('if-kf-notas').value    = item ? item.notas    : '';
    document.getElementById('if-cred-delete-btn').style.display = id ? 'inline-flex' : 'none';
    credDrawerBg.classList.add('is-open');
    document.getElementById('if-kf-folio').focus();
  }

  function closeCredDrawer() { credDrawerBg.classList.remove('is-open'); credEditingId = null; }

  document.getElementById('if-cred-cancel-btn').addEventListener('click', closeCredDrawer);
  credDrawerBg.addEventListener('click', function(e){ if (e.target === credDrawerBg) closeCredDrawer(); });
  document.getElementById('if-cred-add-btn').addEventListener('click', function(){ openCredDrawer(null); });

  document.getElementById('if-cred-tbody').addEventListener('click', function(e){
    var tr = e.target.closest('tr[data-id]');
    if (tr) openCredDrawer(tr.dataset.id);
  });

  document.getElementById('if-cred-save-btn').addEventListener('click', function(){
    var folio = document.getElementById('if-kf-folio').value.trim();
    var socio = document.getElementById('if-kf-socio').value.trim();
    if (!folio || !socio) {
      if (!folio) document.getElementById('if-kf-folio').focus();
      else document.getElementById('if-kf-socio').focus();
      return;
    }
    var monto   = parseFloat(document.getElementById('if-kf-monto').value || 0);
    var pctCom  = parseFloat(document.getElementById('if-kf-pct-com').value || 0);
    var comRaw  = parseFloat(document.getElementById('if-kf-com-monto').value || 0);
    var comMonto = comRaw || (monto > 0 && pctCom > 0 ? monto * pctCom / 100 : 0);
    var list = loadCred();
    var item = {
      id:       credEditingId || ('cred-' + Date.now()),
      folio,
      producto: document.getElementById('if-kf-producto').value,
      socio,
      monto,
      plazo:    document.getElementById('if-kf-plazo').value.trim(),
      tasa:     parseFloat(document.getElementById('if-kf-tasa').value || 0),
      pctCom,
      comMonto,
      fecha:    document.getElementById('if-kf-fecha').value,
      estado:   document.getElementById('if-kf-estado').value,
      ref:      document.getElementById('if-kf-ref').value.trim(),
      notas:    document.getElementById('if-kf-notas').value.trim(),
    };
    if (credEditingId) {
      var idx = list.findIndex(function(c){ return c.id === credEditingId; });
      if (idx >= 0) list[idx] = item;
    } else {
      list.push(item);
    }
    saveCred(list);
    renderCred();
    refreshStats();
    closeCredDrawer();
  });

  document.getElementById('if-cred-delete-btn').addEventListener('click', function(){
    if (!credEditingId) return;
    saveCred(loadCred().filter(function(c){ return c.id !== credEditingId; }));
    renderCred();
    refreshStats();
    closeCredDrawer();
  });

  // ── Filters ───────────────────────────────────────────────────────────────
  ['if-com-search','if-com-filter-tipo','if-com-filter-estado'].forEach(function(id){
    document.getElementById(id).addEventListener('input', renderCom);
  });
  ['if-cred-search','if-cred-filter-estado'].forEach(function(id){
    document.getElementById(id).addEventListener('input', renderCred);
  });
  ['if-edc-mes','if-edc-tipo-filter'].forEach(function(id){
    document.getElementById(id).addEventListener('change', renderEdc);
  });

  // ── Export (CSV) ──────────────────────────────────────────────────────────
  document.getElementById('if-edc-download-btn').addEventListener('click', function(){
    var mes  = document.getElementById('if-edc-mes').value || currentMonth();
    var tipo = document.getElementById('if-edc-tipo-filter').value;
    var coms = loadCom().filter(function(c){
      if (!(c.fecha || '').startsWith(mes)) return false;
      if (tipo && c.tipo !== tipo) return false;
      return true;
    });
    var rows = [['Folio','Tipo','Socio/Cliente','Monto base','% Comisión','Comisión','Estado','Fecha']];
    coms.forEach(function(c){
      rows.push([c.folio, c.tipo, c.socio, c.montoBase, c.pct, c.montoComision, c.estado, c.fecha]);
    });
    var csv = rows.map(function(r){ return r.map(function(v){ return '"' + String(v||'').replace(/"/g,'""') + '"'; }).join(','); }).join('\\n');
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    var url  = URL.createObjectURL(blob);
    var a    = document.createElement('a'); a.href = url;
    a.download = 'estado_cuenta_' + mes + '.csv';
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  });

  // ── Tabs ──────────────────────────────────────────────────────────────────
  document.querySelectorAll('.if-tab').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.if-tab').forEach(function(b){ b.classList.remove('is-active'); });
      document.querySelectorAll('.if-tab-panel').forEach(function(p){ p.classList.remove('is-active'); });
      btn.classList.add('is-active');
      var panel = document.getElementById('if-panel-' + btn.dataset.tab);
      if (panel) panel.classList.add('is-active');
      if (btn.dataset.tab === 'edc') renderEdc();
    });
  });

  // ── Init ──────────────────────────────────────────────────────────────────
  var edcMes = document.getElementById('if-edc-mes');
  if (edcMes) edcMes.value = currentMonth();

  renderCom();
  renderCred();
  refreshStats();
})();
</script>
</body>
</html>"""
