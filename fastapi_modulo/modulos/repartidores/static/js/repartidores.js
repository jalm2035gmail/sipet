/* =========================================================
   REPARTIDORES — frontend operativo          (SIPET 2025)
   ========================================================= */
(function () {
  'use strict';

  /* ── helpers ──────────────────────────────────────────── */
  const $ = id => document.getElementById(id);
  const esc = v => (v == null ? '' : String(v)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'));
  const fmt = v => (v == null || v === '' ? '—' : v);
  const pct = v => `${Number(v || 0).toFixed(1)}%`;

  async function GET(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }
  async function POST(url, body) {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }
  async function PATCH(url, body) {
    const r = await fetch(url, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  function toast(msg, type = 'info') {
    const t = document.createElement('div');
    t.className = `rep-toast rep-toast-${type}`;
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.classList.add('rep-toast-show'), 10);
    setTimeout(() => { t.classList.remove('rep-toast-show'); setTimeout(() => t.remove(), 350); }, 3200);
  }

  /* ── state labels & classes ────────────────────────────── */
  const STATE_LABELS = {
    draft: 'Pendiente', assigned: 'Asignada', picked_up: 'Recolectada',
    in_transit: 'En tránsito', delivered: 'Entregada',
    cancelled: 'Cancelada', failed: 'Fallida',
    available: 'Disponible', busy: 'Ocupado',
    offline: 'Desconectado', suspended: 'Suspendido'
  };
  const ENT_STATE_CLS = {
    draft: 'rep-badge-soft', assigned: 'rep-badge-blue',
    picked_up: 'rep-badge-amber', in_transit: 'rep-badge-blue',
    delivered: 'rep-badge-green', cancelled: 'rep-badge-soft', failed: 'rep-badge-red'
  };
  const REP_STATE_CLS = {
    available: 'rep-badge-green', busy: 'rep-badge-amber',
    offline: 'rep-badge-soft', suspended: 'rep-badge-red'
  };
  const PRI_CLS = { baja: 'rep-badge-soft', normal: '', alta: 'rep-badge-amber', urgente: 'rep-badge-red' };
  const SEVERITY_CLS = { baja: 'rep-badge-soft', media: 'rep-badge-amber', alta: 'rep-badge-red', critica: 'rep-badge-red' };

  /* ── app state ─────────────────────────────────────────── */
  const S = {
    repartidores: [], zonas: [], vehiculos: [],
    entregas: [], incidencias: [], liquidaciones: []
  };

  /* ── modals ────────────────────────────────────────────── */
  function openModal(id) { $(id).classList.add('rep-modal-open'); }
  function closeModal(id) { $(id).classList.remove('rep-modal-open'); }

  function initModals() {
    document.querySelectorAll('[data-close]').forEach(btn => {
      btn.addEventListener('click', () => closeModal(btn.dataset.close));
    });
    document.querySelectorAll('.rep-modal-backdrop').forEach(bd => {
      bd.addEventListener('click', e => { if (e.target === bd) closeModal(bd.id); });
    });
  }

  /* ── tabs ──────────────────────────────────────────────── */
  function initTabs() {
    document.querySelectorAll('.rep-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.rep-tab-btn').forEach(b => b.classList.remove('rep-tab-active'));
        document.querySelectorAll('.rep-tab-pane').forEach(p => { p.style.display = 'none'; p.classList.remove('rep-tab-pane-active'); });
        btn.classList.add('rep-tab-active');
        const pane = $(btn.dataset.tab);
        pane.style.display = '';
        pane.classList.add('rep-tab-pane-active');
        if (btn.dataset.tab === 'tabDashboard') loadDashboard();
        if (btn.dataset.tab === 'tabAnalitica') loadAnalitica();
        if (btn.dataset.tab === 'tabMapa') loadMapa();
      });
    });
  }

  /* ── view toggle (kanban / list) ───────────────────────── */
  function initViewToggle() {
    $('btnViewKanban').addEventListener('click', () => {
      $('viewKanban').style.display = '';
      $('viewList').style.display = 'none';
      $('btnViewKanban').classList.add('rep-view-active');
      $('btnViewList').classList.remove('rep-view-active');
    });
    $('btnViewList').addEventListener('click', () => {
      $('viewKanban').style.display = 'none';
      $('viewList').style.display = '';
      $('btnViewList').classList.add('rep-view-active');
      $('btnViewKanban').classList.remove('rep-view-active');
      renderEntregasList();
    });
  }

  /* ── select sync ───────────────────────────────────────── */
  function syncSelects() {
    const zonasOpts = '<option value="">Sin zona</option>' +
      S.zonas.map(z => `<option value="${z.id}">${esc(z.name)}</option>`).join('');
    const vehOpts = '<option value="">Sin vehículo</option>' +
      S.vehiculos.map(v => `<option value="${v.id}">${esc(v.name)} (${esc(v.tipo)})</option>`).join('');
    const repOpts = '<option value="">Sin asignar</option>' +
      S.repartidores.filter(r => r.state === 'available')
        .map(r => `<option value="${r.id}">${esc(r.nombre)}</option>`).join('');
    const repAllOpts = '<option value="">Todos los repartidores</option>' +
      S.repartidores.map(r => `<option value="${r.id}">${esc(r.nombre)}</option>`).join('');
    const repAllFull = '<option value="">Seleccionar...</option>' +
      S.repartidores.map(r => `<option value="${r.id}">${esc(r.nombre)}</option>`).join('');

    ['repZonaId', 'entZonaId'].forEach(id => { if ($(id)) $(id).innerHTML = zonasOpts; });
    ['repVehiculoId'].forEach(id => { if ($(id)) $(id).innerHTML = vehOpts; });
    ['entRepartidorId'].forEach(id => { if ($(id)) $(id).innerHTML = repOpts; });
    ['filtEntregaRepartidor', 'filtLiqRepartidor', 'anRepartidorId'].forEach(id => {
      if ($(id)) $(id).innerHTML = repAllOpts;
    });
    ['asignarRepartidorId', 'liqRepartidorId'].forEach(id => {
      if ($(id)) $(id).innerHTML = repAllFull;
    });
    const zones2 = '<option value="">Todas las zonas</option>' +
      S.zonas.map(z => `<option value="${z.id}">${esc(z.name)}</option>`).join('');
    if ($('filtRepZona')) $('filtRepZona').innerHTML = zones2;

    const entOpts = '<option value="">Todas las entregas</option>' +
      S.entregas.map(e => `<option value="${e.id}">#${e.id} — ${esc(e.cliente_nombre)}</option>`).join('');
    if ($('filtIncEntrega')) $('filtIncEntrega').innerHTML = entOpts;
    const incEntOpts = '<option value="">Seleccionar entrega...</option>' +
      S.entregas.map(e => `<option value="${e.id}">#${e.id} — ${esc(e.cliente_nombre)}</option>`).join('');
    if ($('incEntregaId')) $('incEntregaId').innerHTML = incEntOpts;
  }

  /* ── stats ─────────────────────────────────────────────── */
  async function loadStats() {
    const { data: s } = await GET('/api/repartidores/stats');
    $('statRepartidores').textContent = s.repartidores;
    $('statDisponibles').textContent = s.disponibles;
    $('statOcupados').textContent = s.ocupados;
    $('statEntregas').textContent = s.entregas;
    $('statTransito').textContent = (s.by_state || {}).in_transit || 0;
    $('statEntregadas').textContent = (s.by_state || {}).delivered || 0;
    $('statIncidencias').textContent = s.incidencias_abiertas;
    $('statLiquidaciones').textContent = s.liquidaciones_borrador;
    return s;
  }

  /* ── loaders ────────────────────────────────────────────── */
  async function loadRepartidores() {
    const { data } = await GET('/api/repartidores/repartidores');
    S.repartidores = data;
  }
  async function loadZonas() {
    const { data } = await GET('/api/repartidores/zonas');
    S.zonas = data;
  }
  async function loadVehiculos() {
    const { data } = await GET('/api/repartidores/vehiculos');
    S.vehiculos = data;
  }
  async function loadEntregas() {
    const params = new URLSearchParams();
    const st = $('filtEntregaState').value;
    const pr = $('filtEntregaPrioridad').value;
    const rp = $('filtEntregaRepartidor').value;
    if (st) params.append('state', st);
    if (pr) params.append('prioridad', pr);
    if (rp) params.append('repartidor_id', rp);
    const { data } = await GET('/api/repartidores/entregas?' + params);
    S.entregas = data;
  }
  async function loadIncidencias() {
    const params = new URLSearchParams();
    const st = $('filtIncState').value;
    const eid = $('filtIncEntrega').value;
    if (st) params.append('state', st);
    if (eid) params.append('entrega_id', eid);
    const { data } = await GET('/api/repartidores/incidencias?' + params);
    S.incidencias = data;
  }
  async function loadLiquidaciones() {
    const { data } = await GET('/api/repartidores/liquidaciones');
    S.liquidaciones = data;
  }

  /* ── renderers ────────────────────────────────────────────── */
  function renderKanban() {
    const states = ['draft','assigned','picked_up','in_transit','delivered','failed','cancelled'];
    const groups = {};
    states.forEach(s => { groups[s] = []; });
    S.entregas.forEach(e => { if (groups[e.state]) groups[e.state].push(e); });

    states.forEach(st => {
      $('kcount-' + st).textContent = groups[st].length;
      $('kcards-' + st).innerHTML = groups[st].map(e => {
        const repNombre = e.repartidor_id
          ? (S.repartidores.find(r => r.id === e.repartidor_id) || {}).nombre || '—'
          : '—';
        return `<div class="rep-kcard">
          <div class="rep-kcard-head">
            <span class="rep-badge ${PRI_CLS[e.prioridad] || ''}">${esc(e.prioridad)}</span>
            <span class="rep-muted">#${e.id}</span>
          </div>
          <strong>${esc(e.cliente_nombre)}</strong>
          <div class="rep-kcard-dest"><i class="fa-solid fa-location-dot"></i> ${esc(e.destino_direccion)}</div>
          <div class="rep-kcard-rep"><i class="fa-solid fa-person-biking"></i> ${esc(repNombre)}</div>
          <div class="rep-kcard-actions">
            ${st === 'draft' ? `<button class="rep-btn rep-btn-sm rep-btn-primary" onclick="REP.openAsignar(${e.id})">Asignar</button>` : ''}
            ${['assigned','picked_up','in_transit'].includes(st) ? `<button class="rep-btn rep-btn-sm rep-btn-primary" onclick="REP.openEstadoNext(${e.id})">Avanzar</button>` : ''}
            ${['draft','assigned','picked_up','in_transit'].includes(st) ? `<button class="rep-btn rep-btn-sm rep-btn-danger" onclick="REP.openEstado(${e.id},'cancelled')">Cancelar</button>` : ''}
          </div>
        </div>`;
      }).join('') || '<div class="rep-empty-col">—</div>';
    });
  }

  function renderEntregasList() {
    const el = $('repEntregasList');
    if (!S.entregas.length) { el.className = 'rep-list-empty'; el.textContent = 'Sin entregas.'; return; }
    el.className = '';
    el.innerHTML = `<table class="rep-table">
      <thead><tr><th>#</th><th>Cliente</th><th>Destino</th><th>Estado</th><th>Prioridad</th><th>Repartidor</th><th>Acciones</th></tr></thead>
      <tbody>${S.entregas.map(e => {
        const rep = S.repartidores.find(r => r.id === e.repartidor_id);
        return `<tr>
          <td>${e.id}</td>
          <td>${esc(e.cliente_nombre)}</td>
          <td>${esc(e.destino_direccion)}</td>
          <td><span class="rep-badge ${ENT_STATE_CLS[e.state]||''}">${STATE_LABELS[e.state]||e.state}</span></td>
          <td><span class="rep-badge ${PRI_CLS[e.prioridad]||''}">${esc(e.prioridad)}</span></td>
          <td>${rep ? esc(rep.nombre) : '—'}</td>
          <td>
            ${e.state==='draft' ? `<button class="rep-btn rep-btn-sm rep-btn-primary" onclick="REP.openAsignar(${e.id})">Asignar</button>` : ''}
            ${['assigned','picked_up','in_transit'].includes(e.state) ? `<button class="rep-btn rep-btn-sm" onclick="REP.openEstadoNext(${e.id})">Avanzar</button>` : ''}
          </td>
        </tr>`;
      }).join('')}</tbody>
    </table>`;
  }

  function renderRepartidores() {
    const el = $('repRepartidoresList');
    const st = $('filtRepState').value;
    const zn = $('filtRepZona').value;
    const data = S.repartidores.filter(r =>
      (!st || r.state === st) && (!zn || String(r.zona_id) === zn)
    );
    if (!data.length) { el.className = 'rep-list-empty'; el.textContent = 'Sin repartidores.'; return; }
    el.className = '';
    el.innerHTML = `<table class="rep-table">
      <thead><tr><th>Código</th><th>Nombre</th><th>Tipo</th><th>Estado</th><th>Zona</th><th>Vehículo</th><th></th></tr></thead>
      <tbody>${data.map(r => {
        const zona = S.zonas.find(z => z.id === r.zona_id);
        const veh = S.vehiculos.find(v => v.id === r.vehiculo_id);
        return `<tr>
          <td>${esc(r.codigo)}</td>
          <td>${esc(r.nombre)}</td>
          <td>${esc(r.tipo)}</td>
          <td><span class="rep-badge ${REP_STATE_CLS[r.state]||''}">${STATE_LABELS[r.state]||r.state}</span></td>
          <td>${zona ? esc(zona.name) : '—'}</td>
          <td>${veh ? esc(veh.name) : '—'}</td>
          <td><button class="rep-btn rep-btn-sm" onclick="REP.editRepartidor(${r.id})">Editar</button></td>
        </tr>`;
      }).join('')}</tbody>
    </table>`;
  }

  function renderZonas() {
    const el = $('repZonasList');
    if (!S.zonas.length) { el.className = 'rep-list-empty'; el.textContent = 'Sin zonas.'; return; }
    el.className = '';
    el.innerHTML = `<table class="rep-table">
      <thead><tr><th>Código</th><th>Nombre</th><th>Ciudad</th><th>Radio km</th></tr></thead>
      <tbody>${S.zonas.map(z => `<tr>
        <td>${esc(z.code)}</td><td>${esc(z.name)}</td>
        <td>${esc(z.ciudad)}</td><td>${fmt(z.radio_km)}</td>
      </tr>`).join('')}</tbody>
    </table>`;
  }

  function renderVehiculos() {
    const el = $('repVehiculosList');
    if (!S.vehiculos.length) { el.className = 'rep-list-empty'; el.textContent = 'Sin vehículos.'; return; }
    el.className = '';
    el.innerHTML = `<table class="rep-table">
      <thead><tr><th>Nombre</th><th>Tipo</th><th>Placa</th><th>Cap.(kg)</th><th>Cap.(ped.)</th></tr></thead>
      <tbody>${S.vehiculos.map(v => `<tr>
        <td>${esc(v.name)}</td><td>${esc(v.tipo)}</td>
        <td>${fmt(v.placa)}</td><td>${fmt(v.capacidad_kg)}</td><td>${fmt(v.capacidad_pedidos)}</td>
      </tr>`).join('')}</tbody>
    </table>`;
  }

  function renderIncidencias() {
    const el = $('repIncidenciasList');
    if (!S.incidencias.length) { el.className = 'rep-list-empty'; el.textContent = 'Sin incidencias.'; return; }
    el.className = '';
    el.innerHTML = `<table class="rep-table">
      <thead><tr><th>#</th><th>Entrega</th><th>Tipo</th><th>Severidad</th><th>Estado</th><th>Descripción</th></tr></thead>
      <tbody>${S.incidencias.map(i => `<tr>
        <td>${i.id}</td>
        <td>${i.entrega_id ? '#'+i.entrega_id : '—'}</td>
        <td>${esc(i.tipo)}</td>
        <td><span class="rep-badge ${SEVERITY_CLS[i.severidad]||''}">${esc(i.severidad)}</span></td>
        <td><span class="rep-badge ${i.state==='open'?'rep-badge-red':'rep-badge-green'}">${esc(i.state)}</span></td>
        <td class="rep-td-desc">${esc(i.descripcion)}</td>
      </tr>`).join('')}</tbody>
    </table>`;
  }

  function renderLiquidaciones() {
    const el = $('repLiquidacionesList');
    if (!S.liquidaciones.length) { el.className = 'rep-list-empty'; el.textContent = 'Sin liquidaciones.'; return; }
    el.className = '';
    el.innerHTML = `<table class="rep-table">
      <thead><tr><th>#</th><th>Repartidor</th><th>Periodo</th><th>Total</th><th>Estado</th><th></th></tr></thead>
      <tbody>${S.liquidaciones.map(l => {
        const rep = S.repartidores.find(r => r.id === l.repartidor_id);
        return `<tr>
          <td>${l.id}</td>
          <td>${rep ? esc(rep.nombre) : l.repartidor_id}</td>
          <td>${esc(l.fecha_inicio)} — ${esc(l.fecha_fin)}</td>
          <td>$${(+l.total || 0).toFixed(2)}</td>
          <td><span class="rep-badge ${l.state==='paid'?'rep-badge-green':l.state==='approved'?'rep-badge-blue':'rep-badge-soft'}">${esc(l.state)}</span></td>
          <td><button class="rep-btn rep-btn-sm" onclick="REP.verLiquidacion(${l.id})">Ver</button></td>
        </tr>`;
      }).join('')}</tbody>
    </table>`;
  }

  /* ── dashboard ────────────────────────────────────────────── */
  async function loadDashboard() {
    try {
      const { data: stats } = await GET('/api/repartidores/stats');
      renderBarChart('dashChartEstados', stats.by_state || {}, STATE_LABELS, ENT_STATE_CLS);
      drawDonut(stats.by_state || {});
      await loadEntregas();
      buildZonaChart();
      renderTopRepartidores();
    } catch (e) {
      console.error('Dashboard error:', e);
    }
  }

  function renderBarChart(containerId, dataObj, labels, clsMap) {
    const total = Object.values(dataObj).reduce((a, b) => a + b, 0) || 1;
    const el = $(containerId);
    if (!el) return;
    el.innerHTML = Object.entries(dataObj).map(([k, v]) => `
      <div class="rep-bar-row">
        <span class="rep-bar-label">${esc(labels[k] || k)}</span>
        <div class="rep-bar-track">
          <div class="rep-bar-fill ${clsMap[k] || ''}" style="width:${Math.round(v / total * 100)}%"></div>
        </div>
        <span class="rep-bar-val">${v}</span>
      </div>`).join('');
  }

  function buildZonaChart() {
    const counts = {};
    S.zonas.forEach(z => { counts[z.name] = 0; });
    S.entregas.forEach(e => {
      if (e.zona_id) {
        const z = S.zonas.find(z => z.id === e.zona_id);
        if (z) counts[z.name] = (counts[z.name] || 0) + 1;
        else counts['Sin zona'] = (counts['Sin zona'] || 0) + 1;
      } else {
        counts['Sin zona'] = (counts['Sin zona'] || 0) + 1;
      }
    });
    const el = $('dashChartZonas');
    if (!el) return;
    const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
    el.innerHTML = Object.entries(counts).map(([k, v]) => `
      <div class="rep-bar-row">
        <span class="rep-bar-label">${esc(k)}</span>
        <div class="rep-bar-track">
          <div class="rep-bar-fill" style="width:${Math.round(v / total * 100)}%"></div>
        </div>
        <span class="rep-bar-val">${v}</span>
      </div>`).join('');
  }

  function renderTopRepartidores() {
    const el = $('dashTopRepartidores');
    if (!el) return;
    const topData = S.repartidores.map(r => ({
      r,
      delivered: S.entregas.filter(e => e.repartidor_id === r.id && e.state === 'delivered').length,
      total: S.entregas.filter(e => e.repartidor_id === r.id).length
    })).sort((a, b) => b.delivered - a.delivered).slice(0, 10);

    if (!topData.length) { el.innerHTML = '<p class="rep-muted">Sin datos.</p>'; return; }
    const maxDel = Math.max(1, topData[0].delivered);

    el.innerHTML = `<table class="rep-table">
      <thead><tr><th>#</th><th>Repartidor</th><th>Estado</th><th>Completadas</th><th>Total asignadas</th><th>Rendimiento</th></tr></thead>
      <tbody>${topData.map((item, i) => `<tr>
        <td>${i + 1}</td>
        <td>${esc(item.r.nombre)}</td>
        <td><span class="rep-badge ${REP_STATE_CLS[item.r.state] || ''}">${STATE_LABELS[item.r.state] || item.r.state}</span></td>
        <td><strong>${item.delivered}</strong></td>
        <td>${item.total}</td>
        <td>
          <div class="rep-bar-track rep-bar-inline">
            <div class="rep-bar-fill rep-badge-green" style="width:${Math.round(item.delivered / maxDel * 100)}%"></div>
          </div>
        </td>
      </tr>`).join('')}</tbody>
    </table>`;
  }

  function drawDonut(byState) {
    const canvas = $('dashDonutCanvas');
    if (!canvas || !canvas.getContext) return;
    const ctx = canvas.getContext('2d');
    const PALETTE = {
      draft: '#94a3b8', assigned: '#3b82f6', picked_up: '#f59e0b',
      in_transit: '#0ea5e9', delivered: '#22c55e', cancelled: '#cbd5e1', failed: '#ef4444'
    };
    const total = Object.values(byState).reduce((a, b) => a + b, 0) || 1;
    const cx = 80, cy = 80, R = 60, r = 32;
    ctx.clearRect(0, 0, 160, 160);
    let angle = -Math.PI / 2;
    Object.entries(byState).forEach(([k, v]) => {
      const slice = (v / total) * 2 * Math.PI;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, R, angle, angle + slice);
      ctx.closePath();
      ctx.fillStyle = PALETTE[k] || '#94a3b8';
      ctx.fill();
      angle += slice;
    });
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, 2 * Math.PI);
    ctx.fillStyle = '#fff';
    ctx.fill();
    ctx.fillStyle = '#1e293b';
    ctx.font = 'bold 22px system-ui';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(total, cx, cy - 6);
    ctx.font = '11px system-ui';
    ctx.fillStyle = '#64748b';
    ctx.fillText('entregas', cx, cy + 12);

    const legend = $('dashDonutLegend');
    if (legend) {
      legend.innerHTML = Object.entries(byState).map(([k, v]) => `
        <div class="rep-donut-item">
          <span class="rep-donut-dot" style="background:${PALETTE[k]||'#94a3b8'}"></span>
          <span>${STATE_LABELS[k] || k}</span>
          <span class="rep-bar-val">${v}</span>
        </div>`).join('');
    }
  }

  function renderSimpleTable(mountId, columns, rows, empty = 'Sin datos.') {
    const el = $(mountId);
    if (!el) return;
    if (!rows.length) {
      el.className = 'rep-list-empty';
      el.textContent = empty;
      return;
    }
    el.className = '';
    el.innerHTML = `<table class="rep-table">
      <thead><tr>${columns.map(col => `<th>${col.label}</th>`).join('')}</tr></thead>
      <tbody>${rows.map(row => `<tr>${columns.map(col => `<td>${col.render ? col.render(row) : esc(row[col.key])}</td>`).join('')}</tr>`).join('')}</tbody>
    </table>`;
  }

  function analyticsParams() {
    const params = new URLSearchParams();
    if ($('anFechaInicio') && $('anFechaInicio').value) params.append('fecha_inicio', $('anFechaInicio').value);
    if ($('anFechaFin') && $('anFechaFin').value) params.append('fecha_fin', $('anFechaFin').value);
    if ($('anRepartidorId') && $('anRepartidorId').value) params.append('repartidor_id', $('anRepartidorId').value);
    return params;
  }

  async function loadAnalitica() {
    try {
      const params = analyticsParams();
      const trendParams = new URLSearchParams(params);
      if ($('anAgrupacion') && $('anAgrupacion').value) trendParams.append('agrupacion', $('anAgrupacion').value);
      const [kpisRes, prodRes, zonasRes, margenRes, tendenciaRes, incidenciasRes] = await Promise.allSettled([
        GET('/api/repartidores/analitica/kpis?' + params.toString()),
        GET('/api/repartidores/analitica/productividad?' + params.toString()),
        GET('/api/repartidores/analitica/zonas?' + params.toString()),
        GET('/api/repartidores/analitica/margen?' + params.toString()),
        GET('/api/repartidores/analitica/tendencia?' + trendParams.toString()),
        GET('/api/repartidores/analitica/incidencias?' + params.toString()),
      ]);
      const kpis = kpisRes.status === 'fulfilled' ? (kpisRes.value.data || {}) : {};
      const productividad = prodRes.status === 'fulfilled' ? (prodRes.value.data || []) : [];
      const zonas = zonasRes.status === 'fulfilled' ? (zonasRes.value.data || []) : [];
      const margen = margenRes.status === 'fulfilled' ? (margenRes.value.data || {}) : {};
      const tendencia = tendenciaRes.status === 'fulfilled' ? (tendenciaRes.value.data || []) : [];
      const incidencias = incidenciasRes.status === 'fulfilled' ? (incidenciasRes.value.data || {}) : {};

      const kpiGrid = $('anKpisGrid');
      if (kpiGrid) {
        kpiGrid.innerHTML = [
          ['Total', kpis.total || 0, `En curso ${kpis.en_curso || 0}`],
          ['Entregadas', kpis.entregadas || 0, `Éxito ${pct(kpis.tasa_exito_pct)}`],
          ['Canceladas', kpis.canceladas || 0, `Cancelación ${pct(kpis.tasa_cancelacion_pct)}`],
          ['Fallidas', kpis.fallidas || 0, `Promedio ${Number(kpis.tiempo_promedio_min || 0).toFixed(1)} min`],
        ].map(([label, value, sub]) => `
          <article class="rep-analytics-card">
            <span>${label}</span>
            <strong>${value}</strong>
            <p>${sub}</p>
          </article>
        `).join('');
      }

      renderBarChart(
        'anTrendChart',
        Object.fromEntries((tendencia || []).map(row => [row.periodo, row.total || 0])),
        {},
        {}
      );
      renderBarChart(
        'anZonasChart',
        Object.fromEntries((zonas || []).map(row => [row.zona_name, row.total || 0])),
        {},
        {}
      );

      const margenCard = $('anMargenCard');
      if (margenCard) {
        margenCard.innerHTML = [
          ['Ingresos', `$${Number(margen.ingreso_total || 0).toFixed(2)}`],
          ['Costos', `$${Number(margen.costo_total || 0).toFixed(2)}`],
          ['Margen', `$${Number(margen.margen_total || 0).toFixed(2)}`],
          ['Margen %', pct(margen.margen_pct)],
        ].map(([label, value]) => `
          <article class="rep-analytics-card">
            <span>${label}</span>
            <strong>${value}</strong>
          </article>
        `).join('');
      }

      renderSimpleTable('anProductividadTable', [
        { label: 'Repartidor', key: 'nombre' },
        { label: 'Zona', key: 'zona' },
        { label: 'Entregas', render: row => row.total_entregas || 0 },
        { label: 'Éxito', render: row => pct(row.tasa_exito_pct) },
        { label: 'Tiempo prom.', render: row => `${Number(row.tiempo_promedio_min || 0).toFixed(1)} min` },
        { label: 'Incidencias', render: row => row.incidencias || 0 },
      ], productividad, 'Sin productividad calculada.');

      renderSimpleTable('anIncidenciasTable', [
        { label: 'Tipo', render: row => esc(row.tipo || row.nombre || '-') },
        { label: 'Total', render: row => row.total || row.abiertas || 0 },
        { label: 'Detalle', render: row => esc(row.detalle || row.severidad || '-') },
      ], [
        ...Object.entries(incidencias.por_tipo || {}).map(([tipo, total]) => ({ tipo, total, detalle: 'Por tipo' })),
        ...Object.entries(incidencias.por_severidad || {}).map(([severidad, total]) => ({ tipo: severidad, total, detalle: 'Por severidad' })),
      ], 'Sin incidencias agregadas.');
    } catch (e) {
      console.error('Analítica error:', e);
      toast('No se pudo cargar la analítica', 'error');
    }
  }

  function projectPoint(bounds, lat, lng) {
    const width = 1000;
    const height = 520;
    const pad = 36;
    const latSpan = Math.max((bounds.maxLat - bounds.minLat) || 0.01, 0.01);
    const lngSpan = Math.max((bounds.maxLng - bounds.minLng) || 0.01, 0.01);
    const x = pad + ((lng - bounds.minLng) / lngSpan) * (width - pad * 2);
    const y = height - pad - ((lat - bounds.minLat) / latSpan) * (height - pad * 2);
    return { x, y };
  }

  function buildMapBounds(zonas, entregas, repartidores) {
    const points = [];
    zonas.forEach(z => { if (z.lat_centro != null && z.lng_centro != null) points.push([z.lat_centro, z.lng_centro]); });
    entregas.forEach(e => { if (e.lat_destino != null && e.lng_destino != null) points.push([e.lat_destino, e.lng_destino]); });
    repartidores.forEach(r => { if (r.lat != null && r.lng != null) points.push([r.lat, r.lng]); });
    if (!points.length) return null;
    const lats = points.map(p => Number(p[0]));
    const lngs = points.map(p => Number(p[1]));
    return {
      minLat: Math.min(...lats) - 0.01,
      maxLat: Math.max(...lats) + 0.01,
      minLng: Math.min(...lngs) - 0.01,
      maxLng: Math.max(...lngs) + 0.01,
    };
  }

  function renderMapaSvg(zonas, entregas, repartidores) {
    const svg = $('repMapaSvg');
    if (!svg) return;
    const bounds = buildMapBounds(zonas, entregas, repartidores);
    if (!bounds) {
      svg.innerHTML = '<foreignObject x="0" y="0" width="1000" height="520"><div xmlns="http://www.w3.org/1999/xhtml" class="rep-map-empty">Sin coordenadas suficientes para dibujar el mapa.</div></foreignObject>';
      return;
    }
    const zoneLayer = zonas.filter(z => z.lat_centro != null && z.lng_centro != null).map((z) => {
      const center = projectPoint(bounds, Number(z.lat_centro), Number(z.lng_centro));
      const radius = Math.max(20, Math.min(110, Number(z.radio_km || 1) * 8));
      return `
        <circle cx="${center.x}" cy="${center.y}" r="${radius}" fill="rgba(14,165,233,.10)" stroke="rgba(14,165,233,.45)" stroke-dasharray="6 6"></circle>
        <text x="${center.x}" y="${center.y - radius - 6}" text-anchor="middle" font-size="11" fill="#0369a1">${esc(z.name)}</text>
      `;
    }).join('');
    const entregaLayer = entregas.filter(e => e.lat_destino != null && e.lng_destino != null).map((e) => {
      const point = projectPoint(bounds, Number(e.lat_destino), Number(e.lng_destino));
      const color = e.state === 'delivered' ? '#16a34a' : e.state === 'failed' ? '#dc2626' : '#0f766e';
      return `<g>
        <circle cx="${point.x}" cy="${point.y}" r="7" fill="${color}" stroke="#fff" stroke-width="2"></circle>
        <title>${esc(e.folio || '')} · ${esc(e.cliente_nombre || '')} · ${esc(e.state || '')}</title>
      </g>`;
    }).join('');
    const repartidorLayer = repartidores.filter(r => r.lat != null && r.lng != null).map((r) => {
      const point = projectPoint(bounds, Number(r.lat), Number(r.lng));
      const color = r.state === 'available' ? '#2563eb' : r.state === 'busy' ? '#f59e0b' : '#64748b';
      return `<g>
        <rect x="${point.x - 6}" y="${point.y - 6}" width="12" height="12" rx="3" fill="${color}" stroke="#fff" stroke-width="2"></rect>
        <title>${esc(r.nombre || '')} · ${esc(r.state || '')} · activas ${r.entregas_activas || 0}</title>
      </g>`;
    }).join('');
    svg.innerHTML = `
      <rect x="0" y="0" width="1000" height="520" fill="transparent"></rect>
      ${zoneLayer}
      ${entregaLayer}
      ${repartidorLayer}
    `;
  }

  async function loadMapa() {
    try {
      const params = new URLSearchParams();
      if ($('mapEntregaState') && $('mapEntregaState').value) params.append('state', $('mapEntregaState').value);
      if ($('mapSoloCoords') && $('mapSoloCoords').checked) params.append('solo_con_coords', 'true');
      const [entregasRes, repartidoresRes, zonasRes] = await Promise.all([
        GET('/api/repartidores/mapa/entregas?' + params.toString()),
        GET('/api/repartidores/mapa/repartidores'),
        GET('/api/repartidores/mapa/zonas'),
      ]);
      const entregas = entregasRes.data || [];
      const repartidores = repartidoresRes.data || [];
      const zonas = zonasRes.data || [];
      renderMapaSvg(zonas, entregas, repartidores);

      const resumen = $('mapResumenCard');
      if (resumen) {
        resumen.innerHTML = [
          ['Zonas con radio', zonas.length],
          ['Entregas visibles', entregas.length],
          ['Repartidores con posición', repartidores.filter(r => r.lat != null && r.lng != null).length],
          ['Entregas en tránsito', entregas.filter(e => e.state === 'in_transit').length],
        ].map(([label, value]) => `
          <article class="rep-analytics-card">
            <span>${label}</span>
            <strong>${value}</strong>
          </article>
        `).join('');
      }

      let cercanos = [];
      const firstEntrega = entregas.find(e => e.lat_destino != null && e.lng_destino != null);
      if (firstEntrega) {
        const closeRes = await GET(`/api/repartidores/repartidores/cercanos?lat=${firstEntrega.lat_destino}&lng=${firstEntrega.lng_destino}&radio_km=8`);
        cercanos = closeRes.data || [];
      }
      renderSimpleTable('mapCercanosTable', [
        { label: 'Repartidor', key: 'nombre' },
        { label: 'Estado', key: 'state' },
        { label: 'Zona', key: 'zona_name' },
        { label: 'Distancia', render: row => `${Number(row.distancia_km || 0).toFixed(2)} km` },
      ], cercanos, 'Sin repartidores cercanos para la referencia actual.');

      renderSimpleTable('mapEntregasTable', [
        { label: 'Folio', key: 'folio' },
        { label: 'Cliente', key: 'cliente_nombre' },
        { label: 'Zona', key: 'zona_name' },
        { label: 'Estado', key: 'state' },
        { label: 'Distancia', render: row => `${Number(row.distancia_km || 0).toFixed(2)} km` },
      ], entregas.slice(0, 20), 'Sin entregas georreferenciadas.');
    } catch (e) {
      console.error('Mapa error:', e);
      toast('No se pudo cargar el mapa operativo', 'error');
    }
  }

  /* ── asignar ────────────────────────────────────────────── */
  function openAsignar(entregaId) {
    const e = S.entregas.find(e => e.id === entregaId);
    $('asignarEntregaId').value = entregaId;
    $('asignarEntregaInfo').textContent = e
      ? `Entrega #${e.id} — ${e.cliente_nombre} → ${e.destino_direccion}` : '';
    openModal('modalAsignar');
  }

  async function confirmarAsignacion() {
    const eid = +$('asignarEntregaId').value;
    const rid = +$('asignarRepartidorId').value;
    if (!rid) { toast('Selecciona un repartidor', 'error'); return; }
    try {
      await PATCH(`/api/repartidores/entregas/${eid}/asignar`, { repartidor_id: rid });
      toast('Repartidor asignado', 'success');
      closeModal('modalAsignar');
      await refreshEntregas();
    } catch (err) { toast('Error: ' + err.message, 'error'); }
  }

  /* ── estado ─────────────────────────────────────────────── */
  const NEXT_STATE = {
    draft: 'assigned', assigned: 'picked_up',
    picked_up: 'in_transit', in_transit: 'delivered'
  };

  function openEstado(entregaId, newState) {
    const e = S.entregas.find(e => e.id === entregaId);
    $('estadoEntregaId').value = entregaId;
    $('estadoNuevo').value = newState;
    $('modalEstadoTitle').textContent = `→ ${STATE_LABELS[newState] || newState}`;
    $('estadoInfo').textContent = e
      ? `Entrega #${e.id} — ${e.cliente_nombre}` : '';
    $('fieldEvidencia').style.display = newState === 'delivered' ? '' : 'none';
    $('fieldMotivo').style.display = ['cancelled', 'failed'].includes(newState) ? '' : 'none';
    $('fieldTiempoReal').style.display = newState === 'delivered' ? '' : 'none';
    openModal('modalEstado');
  }

  function openEstadoNext(entregaId) {
    const e = S.entregas.find(e => e.id === entregaId);
    if (!e) return;
    const next = NEXT_STATE[e.state];
    if (!next) { toast('No hay transición disponible', 'error'); return; }
    openEstado(entregaId, next);
  }

  async function confirmarEstado() {
    const eid = +$('estadoEntregaId').value;
    const newState = $('estadoNuevo').value;
    const body = { state: newState };
    if (newState === 'delivered') {
      body.evidencia = $('estadoEvidencia').value || null;
      body.tiempo_real = +$('estadoTiempoReal').value || null;
    }
    if (['cancelled', 'failed'].includes(newState)) {
      body.motivo = $('estadoMotivo').value;
    }
    try {
      await PATCH(`/api/repartidores/entregas/${eid}/estado`, body);
      toast('Estado actualizado', 'success');
      closeModal('modalEstado');
      await refreshEntregas();
    } catch (err) { toast('Error: ' + err.message, 'error'); }
  }

  /* ── liquidación detalle ────────────────────────────────── */
  async function verLiquidacion(id) {
    const l = S.liquidaciones.find(l => l.id === id);
    const rep = l ? S.repartidores.find(r => r.id === l.repartidor_id) : null;
    $('modalLiqDetalleTitle').textContent = `Liquidación #${id}${rep ? ' — ' + rep.nombre : ''}`;
    $('liqDetalleContent').innerHTML = '<p class="rep-muted">Cargando...</p>';
    openModal('modalLiqDetalle');
    try {
      const { data } = await GET(`/api/repartidores/liquidaciones/${id}`);
      const lineas = data.lineas || [];
      $('liqDetalleContent').innerHTML = `
        <div class="rep-liq-meta">
          <span>Periodo: ${esc(data.fecha_inicio)} — ${esc(data.fecha_fin)}</span>
          <span>Estado: <span class="rep-badge ${data.state==='paid'?'rep-badge-green':'rep-badge-soft'}">${esc(data.state)}</span></span>
          <span>Total: <strong>$${(+data.total||0).toFixed(2)}</strong></span>
        </div>
        <table class="rep-table">
          <thead><tr><th>Entrega</th><th>Descripción</th><th>Monto</th></tr></thead>
          <tbody>${lineas.map(l => `<tr>
            <td>${l.entrega_id ? '#'+l.entrega_id : '—'}</td>
            <td>${esc(l.descripcion)}</td>
            <td>$${(+l.monto||0).toFixed(2)}</td>
          </tr>`).join('')}</tbody>
        </table>`;
    } catch (e) { $('liqDetalleContent').innerHTML = '<p class="rep-muted">Error al cargar detalle.</p>'; }
  }

  /* ── edit repartidor ─────────────────────────────────────── */
  function editRepartidor(id) {
    const r = S.repartidores.find(r => r.id === id);
    if (!r) return;
    $('repId').value = r.id;
    $('repNombre').value = r.nombre || '';
    $('repCodigo').value = r.codigo || '';
    $('repTelefono').value = r.telefono || '';
    $('repEmail').value = r.email || '';
    $('repTipo').value = r.tipo || 'interno';
    $('repState').value = r.state || 'available';
    $('repZonaId').value = r.zona_id || '';
    $('repVehiculoId').value = r.vehiculo_id || '';
    $('repNegocio').value = r.negocio || '';
    $('repSucursal').value = r.sucursal || '';
    $('repTarifa').value = r.tarifa_base || 0;
    $('repBono').value = r.bono_por_entrega || 0;
    $('repMeta').value = r.meta_entregas_dia || 10;
    $('repNotas').value = r.notas || '';
    $('modalRepartidorTitle').textContent = 'Editar repartidor';
    openModal('modalRepartidor');
  }

  /* ── refresh helpers ─────────────────────────────────────── */
  async function refreshEntregas() {
    await loadEntregas();
    renderKanban();
    renderEntregasList();
    syncSelects();
  }

  async function refreshAll() {
    try {
      await Promise.all([loadRepartidores(), loadZonas(), loadVehiculos(), loadEntregas(), loadIncidencias(), loadLiquidaciones()]);
      await loadStats();
      syncSelects();
      renderKanban();
      renderRepartidores();
      renderZonas();
      renderVehiculos();
      renderIncidencias();
      renderLiquidaciones();
      const activeTab = document.querySelector('.rep-tab-btn.rep-tab-active');
      if (activeTab && activeTab.dataset.tab === 'tabDashboard') loadDashboard();
      if (activeTab && activeTab.dataset.tab === 'tabAnalitica') loadAnalitica();
      if (activeTab && activeTab.dataset.tab === 'tabMapa') loadMapa();
      toast('Datos actualizados', 'success');
    } catch (err) { toast('Error al cargar datos: ' + err.message, 'error'); }
  }

  /* ── form events ─────────────────────────────────────────── */
  function initEvents() {
    $('btnRefreshAll').addEventListener('click', refreshAll);
    $('btnRefreshAnalitica').addEventListener('click', () => loadAnalitica());
    $('btnRefreshMapa').addEventListener('click', () => loadMapa());
    $('btnConfirmarAsignacion').addEventListener('click', confirmarAsignacion);
    $('btnConfirmarEstado').addEventListener('click', confirmarEstado);
    $('btnAnaliticaCsv').addEventListener('click', () => {
      const params = analyticsParams();
      window.location.href = '/api/repartidores/analitica/exportar-csv?' + params.toString();
    });

    $('btnNuevoRepartidor').addEventListener('click', () => {
      $('repId').value = '';
      $('formRepartidor').reset();
      $('modalRepartidorTitle').textContent = 'Nuevo repartidor';
      openModal('modalRepartidor');
    });

    $('formRepartidor').addEventListener('submit', async (e) => {
      e.preventDefault();
      const body = {
        nombre: $('repNombre').value,
        codigo: $('repCodigo').value,
        telefono: $('repTelefono').value || null,
        email: $('repEmail').value || null,
        tipo: $('repTipo').value,
        state: $('repState').value,
        zona_id: +$('repZonaId').value || null,
        vehiculo_id: +$('repVehiculoId').value || null,
        negocio: $('repNegocio').value || null,
        sucursal: $('repSucursal').value || null,
        tarifa_base: +$('repTarifa').value || 0,
        bono_por_entrega: +$('repBono').value || 0,
        meta_entregas_dia: +$('repMeta').value || 10,
        notas: $('repNotas').value || null
      };
      const id = $('repId').value;
      try {
        if (id) await PATCH(`/api/repartidores/repartidores/${id}`, body);
        else await POST('/api/repartidores/repartidores', body);
        toast('Repartidor guardado', 'success');
        closeModal('modalRepartidor');
        await loadRepartidores();
        syncSelects();
        renderRepartidores();
      } catch (err) { toast('Error: ' + err.message, 'error'); }
    });

    $('btnNuevaZona').addEventListener('click', () => { $('formZona').reset(); openModal('modalZona'); });
    $('formZona').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await POST('/api/repartidores/zonas', {
          name: $('zonaName').value, code: $('zonaCode').value,
          ciudad: $('zonaCiudad').value || null,
          radio_km: +$('zonaRadio').value || 5,
          descripcion: $('zonaDesc').value || null
        });
        toast('Zona guardada', 'success');
        closeModal('modalZona');
        await loadZonas(); syncSelects(); renderZonas();
      } catch (err) { toast('Error: ' + err.message, 'error'); }
    });

    $('btnNuevoVehiculo').addEventListener('click', () => { $('formVehiculo').reset(); openModal('modalVehiculo'); });
    $('formVehiculo').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await POST('/api/repartidores/vehiculos', {
          name: $('vehName').value, tipo: $('vehTipo').value,
          placa: $('vehPlaca').value || null,
          capacidad_kg: +$('vehCapKg').value || 20,
          capacidad_pedidos: +$('vehCapPed').value || 5
        });
        toast('Vehículo guardado', 'success');
        closeModal('modalVehiculo');
        await loadVehiculos(); syncSelects(); renderVehiculos();
      } catch (err) { toast('Error: ' + err.message, 'error'); }
    });

    $('btnNuevaEntrega').addEventListener('click', () => {
      $('formEntrega').reset();
      const now = new Date();
      now.setHours(now.getHours() + 2);
      $('entFecha').value = now.toISOString().slice(0, 16);
      openModal('modalEntrega');
    });
    $('formEntrega').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await POST('/api/repartidores/entregas', {
          cliente_nombre: $('entCliente').value,
          cliente_telefono: $('entClienteTel').value || null,
          origen_direccion: $('entOrigen').value || null,
          destino_direccion: $('entDestino').value,
          referencia_externa: $('entRef').value || null,
          prioridad: $('entPrioridad').value,
          zona_id: +$('entZonaId').value || null,
          repartidor_id: +$('entRepartidorId').value || null,
          costo_envio: +$('entCosto').value || 0,
          distancia_km: +$('entDistancia').value || 0,
          tiempo_estimado_min: +$('entTiempo').value || 0,
          fecha_programada: $('entFecha').value || null,
          descripcion: $('entDesc').value || null
        });
        toast('Entrega creada', 'success');
        closeModal('modalEntrega');
        await refreshEntregas();
        await loadStats();
      } catch (err) { toast('Error: ' + err.message, 'error'); }
    });

    $('btnNuevaIncidencia').addEventListener('click', () => { $('formIncidencia').reset(); openModal('modalIncidencia'); });
    $('formIncidencia').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await POST('/api/repartidores/incidencias', {
          entrega_id: +$('incEntregaId').value || null,
          tipo: $('incTipo').value,
          severidad: $('incSeveridad').value,
          descripcion: $('incDescripcion').value
        });
        toast('Incidencia registrada', 'success');
        closeModal('modalIncidencia');
        await loadIncidencias(); renderIncidencias(); await loadStats();
      } catch (err) { toast('Error: ' + err.message, 'error'); }
    });

    $('btnGenerarLiquidacion').addEventListener('click', () => { $('formLiquidacion').reset(); openModal('modalLiquidacion'); });
    $('formLiquidacion').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await POST('/api/repartidores/liquidaciones', {
          repartidor_id: +$('liqRepartidorId').value,
          fecha_inicio: $('liqFechaInicio').value,
          fecha_fin: $('liqFechaFin').value,
          descuentos: +$('liqDescuentos').value || 0,
          notas: $('liqNotas').value || null
        });
        toast('Liquidación generada', 'success');
        closeModal('modalLiquidacion');
        await loadLiquidaciones(); renderLiquidaciones(); await loadStats();
      } catch (err) { toast('Error: ' + err.message, 'error'); }
    });

    $('filtEntregaState').addEventListener('change', () => refreshEntregas());
    $('filtEntregaPrioridad').addEventListener('change', () => refreshEntregas());
    $('filtEntregaRepartidor').addEventListener('change', () => refreshEntregas());
    $('filtRepState').addEventListener('change', () => renderRepartidores());
    $('filtRepZona').addEventListener('change', () => renderRepartidores());
    $('filtIncState').addEventListener('change', () => { loadIncidencias().then(renderIncidencias); });
    $('filtIncEntrega').addEventListener('change', () => { loadIncidencias().then(renderIncidencias); });
    $('anFechaInicio').addEventListener('change', () => loadAnalitica());
    $('anFechaFin').addEventListener('change', () => loadAnalitica());
    $('anRepartidorId').addEventListener('change', () => loadAnalitica());
    $('anAgrupacion').addEventListener('change', () => loadAnalitica());
    $('mapEntregaState').addEventListener('change', () => loadMapa());
    $('mapSoloCoords').addEventListener('change', () => loadMapa());
  }

  /* ── init ────────────────────────────────────────────────── */
  async function init() {
    initTabs();
    initViewToggle();
    initModals();
    initEvents();
    await refreshAll();
    loadDashboard();
    loadAnalitica();
    loadMapa();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  /* ── public API ──────────────────────────────────────────── */
  window.REP = {
    editRepartidor,
    openAsignar,
    openEstado,
    openEstadoNext,
    verLiquidacion
  };

})();
