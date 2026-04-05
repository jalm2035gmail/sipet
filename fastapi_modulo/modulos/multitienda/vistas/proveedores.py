from __future__ import annotations

from html import escape


def _js_bool(value: bool) -> str:
    return "true" if value else "false"


def proveedores_html(
    intelicoop_enabled: bool = False,
    intelicoop_route: str = "",
    intelicoop_api_base: str = "",
) -> str:
    return (
        _HTML
        .replace("__INTELICOOP_ENABLED__", _js_bool(intelicoop_enabled))
        .replace("__INTELICOOP_ROUTE__", intelicoop_route or "#")
        .replace("__INTELICOOP_API_BASE__", intelicoop_api_base or "")
        .replace("__INTELICOOP_CONTACT_BANNER__", _build_contact_banner(intelicoop_enabled, intelicoop_route))
        .replace("__INTELICOOP_CAMPAIGN_BANNER__", _build_campaign_banner(intelicoop_enabled, intelicoop_route))
    )


def _build_contact_banner(intelicoop_enabled: bool, intelicoop_route: str) -> str:
    if intelicoop_enabled and intelicoop_route:
        return (
            '<div class="pv-intel-banner">'
            '<i class="fa-solid fa-circle-nodes"></i>'
            '<span>Guardado en <a href="{route}" target="_blank">Intelicoop</a> como prospecto.</span>'
            "</div>"
        ).format(route=escape(intelicoop_route))
    return (
        '<div class="pv-intel-banner pv-intel-banner--disabled">'
        '<i class="fa-solid fa-plug-circle-xmark"></i>'
        "<span>Intelicoop no está habilitado. Esta vista sigue disponible sin sincronización financiera.</span>"
        "</div>"
    )


def _build_campaign_banner(intelicoop_enabled: bool, intelicoop_route: str) -> str:
    if intelicoop_enabled and intelicoop_route:
        return (
            '<div class="pv-intel-banner">'
            '<i class="fa-solid fa-circle-nodes"></i>'
            '<span>Sincronizado con <a href="{route}" target="_blank">Intelicoop</a>.</span>'
            "</div>"
        ).format(route=escape(intelicoop_route))
    return (
        '<div class="pv-intel-banner pv-intel-banner--disabled">'
        '<i class="fa-solid fa-plug-circle-xmark"></i>'
        "<span>Intelicoop no está habilitado. Las campañas quedan desacopladas del módulo financiero.</span>"
        "</div>"
    )


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Proveedores — Multitienda</title>
  <link rel="stylesheet" href="/multitienda/static/css/proveedores.css" />
</head>
<body>
<main>

  <!-- Stats -->
  <div class="pv-stats">
    <div class="pv-stat">
      <div class="pv-stat__icon pv-stat__icon--teal"><i class="fa-solid fa-handshake"></i></div>
      <div><div class="pv-stat__value" id="pv-stat-total">0</div><div class="pv-stat__label">Total contactos</div></div>
    </div>
    <div class="pv-stat">
      <div class="pv-stat__icon pv-stat__icon--green"><i class="fa-solid fa-star"></i></div>
      <div><div class="pv-stat__value" id="pv-stat-alta">0</div><div class="pv-stat__label">Alta propensión</div></div>
    </div>
    <div class="pv-stat">
      <div class="pv-stat__icon pv-stat__icon--blue"><i class="fa-solid fa-bullhorn"></i></div>
      <div><div class="pv-stat__value" id="pv-stat-campanas">0</div><div class="pv-stat__label">Campañas activas</div></div>
    </div>
    <div class="pv-stat">
      <div class="pv-stat__icon pv-stat__icon--amber"><i class="fa-solid fa-clock-rotate-left"></i></div>
      <div><div class="pv-stat__value" id="pv-stat-nuevos">0</div><div class="pv-stat__label">Nuevos este mes</div></div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="pv-tabs">
    <button class="pv-tab is-active" data-tab="contactos" onclick="showTab('contactos')">
      <i class="fa-solid fa-address-card"></i> Red de contactos
    </button>
    <button class="pv-tab" data-tab="campanas" onclick="showTab('campanas')">
      <i class="fa-solid fa-bullhorn"></i> Campañas
    </button>
  </div>

  <!-- ═══ TAB: Contactos ═══ -->
  <div class="pv-tab-panel is-active" id="pv-panel-contactos">
    <div class="pv-toolbar">
      <div class="pv-toolbar__left">
        <button class="pv-btn pv-btn--primary" onclick="openContactDrawer(null)">
          <i class="fa-solid fa-plus"></i> Nuevo contacto
        </button>
        <button class="pv-btn pv-btn--danger" id="pv-del-btn" disabled onclick="openConfirm('bulk')">
          <i class="fa-regular fa-trash-can"></i> Eliminar
        </button>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
        <select class="pv-filter-select" id="pv-filter-fuente" onchange="renderContactos()">
          <option value="">Todas las fuentes</option>
          <option value="referido">Referido</option>
          <option value="directo">Directo</option>
          <option value="feria">Feria / evento</option>
          <option value="online">Online</option>
          <option value="campana">Campaña</option>
          <option value="otro">Otro</option>
        </select>
        <div class="pv-search">
          <i class="fa-solid fa-magnifying-glass" style="color:var(--pv-muted);font-size:.8rem;"></i>
          <input type="text" id="pv-search" placeholder="Buscar nombre o teléfono…" oninput="renderContactos()" />
        </div>
      </div>
    </div>
    <div class="pv-table-wrap">
      <table class="pv-table">
        <thead>
          <tr>
            <th style="width:36px;"><input type="checkbox" id="pv-check-all" onchange="toggleAll(this.checked)" /></th>
            <th class="sortable" onclick="sortBy('nombre')">Nombre <span class="sarr">↕</span></th>
            <th class="sortable" onclick="sortBy('telefono')">Teléfono <span class="sarr">↕</span></th>
            <th class="sortable" onclick="sortBy('fuente')">Fuente <span class="sarr">↕</span></th>
            <th class="sortable" onclick="sortBy('score_propension')">Propensión <span class="sarr">↕</span></th>
            <th class="sortable" onclick="sortBy('fecha_creacion')">Registro <span class="sarr">↕</span></th>
          </tr>
        </thead>
        <tbody id="pv-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- ═══ TAB: Campañas ═══ -->
  <div class="pv-tab-panel" id="pv-panel-campanas">
    <div class="pv-toolbar">
      <div class="pv-toolbar__left">
        <button class="pv-btn pv-btn--primary" onclick="openCampDrawer(null)">
          <i class="fa-solid fa-plus"></i> Nueva campaña
        </button>
      </div>
      <div style="display:flex;gap:10px;align-items:center;">
        <select class="pv-filter-select" id="pv-camp-filter" onchange="renderCampanas()">
          <option value="">Todos los estados</option>
          <option value="activa">Activa</option>
          <option value="borrador">Borrador</option>
          <option value="cerrada">Cerrada</option>
        </select>
      </div>
    </div>
    <div id="pv-camp-container">
      <div class="pv-empty"><i class="fa-solid fa-bullhorn"></i>Cargando campañas…</div>
    </div>
  </div>

  <!-- Confirm -->
  <div class="pv-confirm" id="pv-confirm">
    <div class="pv-confirm__card">
      <div class="pv-confirm__icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div class="pv-confirm__title" id="pv-confirm-title">¿Eliminar?</div>
      <div class="pv-confirm__text" id="pv-confirm-text">Esta acción eliminará también el registro en Intelicoop.</div>
      <div class="pv-confirm__actions">
        <button class="pv-btn" onclick="closeConfirm()">Cancelar</button>
        <button class="pv-btn pv-btn--danger" id="pv-confirm-ok">Sí, eliminar</button>
      </div>
    </div>
  </div>
<div class="pv-overlay" id="pv-overlay" onclick="closeAllDrawers()"></div>

<!-- Contact drawer -->
<aside class="pv-drawer" id="pv-contact-drawer">
  <div class="pv-drawer__head">
    <span class="pv-drawer__title" id="pv-contact-drawer-title">Nuevo contacto</span>
    <button class="pv-drawer__close" onclick="closeAllDrawers()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="pv-drawer__body">
    __INTELICOOP_CONTACT_BANNER__
    <div class="pv-field">
      <label for="pv-f-nombre">Nombre completo <span style="color:var(--pv-danger)">*</span></label>
      <input id="pv-f-nombre" type="text" placeholder="Nombre Apellido / Empresa" />
    </div>
    <div class="pv-field--row">
      <div class="pv-field">
        <label for="pv-f-tel">Teléfono</label>
        <input id="pv-f-tel" type="tel" placeholder="+52 55 1234 5678" />
      </div>
      <div class="pv-field">
        <label for="pv-f-fuente">Fuente</label>
        <select id="pv-f-fuente">
          <option value="directo">Directo</option>
          <option value="referido">Referido</option>
          <option value="feria">Feria / evento</option>
          <option value="online">Online</option>
          <option value="campana">Campaña</option>
          <option value="otro">Otro</option>
        </select>
      </div>
    </div>
    <div class="pv-field">
      <label for="pv-f-dir">Dirección / Ubicación</label>
      <input id="pv-f-dir" type="text" placeholder="Ciudad, Estado" />
    </div>
    <div class="pv-field">
      <label for="pv-f-score">Propensión (0 – 1)</label>
      <input id="pv-f-score" type="number" min="0" max="1" step="0.01" placeholder="0.50" />
      <span class="pv-field--hint">Probabilidad estimada de conversión. Intelicoop la recalcula automáticamente.</span>
    </div>
    <div class="pv-field">
      <label for="pv-f-notas">Notas</label>
      <textarea id="pv-f-notas" placeholder="Observaciones sobre este contacto…"></textarea>
    </div>
  </div>
  <div class="pv-drawer__footer">
    <button class="pv-btn pv-btn--danger" id="pv-f-del-btn" onclick="openConfirm('single')" style="display:none;">
      <i class="fa-regular fa-trash-can"></i> Eliminar
    </button>
    <button class="pv-btn pv-btn--primary" onclick="saveContact()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<!-- Campaign drawer -->
<aside class="pv-drawer" id="pv-camp-drawer">
  <div class="pv-drawer__head">
    <span class="pv-drawer__title" id="pv-camp-drawer-title">Nueva campaña</span>
    <button class="pv-drawer__close" onclick="closeAllDrawers()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="pv-drawer__body">
    __INTELICOOP_CAMPAIGN_BANNER__
    <div class="pv-field">
      <label for="pv-cf-nombre">Nombre de la campaña <span style="color:var(--pv-danger)">*</span></label>
      <input id="pv-cf-nombre" type="text" placeholder="Ej. Captación proveedores Q2" />
    </div>
    <div class="pv-field">
      <label for="pv-cf-tipo">Tipo</label>
      <select id="pv-cf-tipo">
        <option value="Colocacion">Colocación</option>
        <option value="Recuperacion">Recuperación</option>
        <option value="Captacion">Captación</option>
        <option value="Retencion">Retención</option>
        <option value="Otro">Otro</option>
      </select>
    </div>
    <div class="pv-field--row">
      <div class="pv-field">
        <label for="pv-cf-inicio">Fecha inicio</label>
        <input id="pv-cf-inicio" type="date" />
      </div>
      <div class="pv-field">
        <label for="pv-cf-fin">Fecha fin</label>
        <input id="pv-cf-fin" type="date" />
      </div>
    </div>
    <div class="pv-field">
      <label for="pv-cf-estado">Estado</label>
      <select id="pv-cf-estado">
        <option value="borrador">Borrador</option>
        <option value="activa">Activa</option>
        <option value="cerrada">Cerrada</option>
      </select>
    </div>
  </div>
  <div class="pv-drawer__footer">
    <button class="pv-btn pv-btn--primary" onclick="saveCampaña()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<div class="pv-toast" id="pv-toast"></div>
</main>

<script>
(function () {
  var INTELICOOP_ENABLED = __INTELICOOP_ENABLED__;
  var INTELICOOP_API_BASE = '__INTELICOOP_API_BASE__';
  var LOCAL_API = '/multitienda/api/proveedores';
  var prospectos = [];
  var campanas   = [];
  var sortCol = 'nombre';
  var sortAsc = true;
  var editContactId  = null;
  var confirmMode    = '';
  var confirmCallback = null;

  function normalizeLocal(s) {
    return {
      id:               s.id,
      nombre:           s.name || s.nombre || '',
      telefono:         s.phone || s.telefono || '',
      fuente:           s.fuente || 'directo',
      direccion:        s.address || s.direccion || '',
      score_propension: parseFloat(s.score_propension || 0),
      fecha_creacion:   s.created_at || s.fecha_creacion || '',
      notas:            s.notes || s.notas || '',
    };
  }

  /* ── Load ── */
  function load() {
    function loadLocalFallback() {
      fetch(LOCAL_API, { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          prospectos = (res.data || []).map(normalizeLocal);
          campanas = [];
          renderContactos();
          renderCampanas();
          updateStats();
        })
        .catch(function () {
          prospectos = []; campanas = [];
          renderContactos();
          renderCampanas();
          updateStats();
        });
    }

    if (!INTELICOOP_ENABLED || !INTELICOOP_API_BASE) {
      loadLocalFallback();
      return;
    }
    Promise.all([
      fetch(INTELICOOP_API_BASE + '/prospectos', { credentials: 'same-origin' }).then(function (r) {
        if (!r.ok) throw new Error(String(r.status || 500));
        return r.json();
      }),
      fetch(INTELICOOP_API_BASE + '/campanas',   { credentials: 'same-origin' }).then(function (r) {
        if (!r.ok) throw new Error(String(r.status || 500));
        return r.json();
      }),
    ]).then(function (results) {
      prospectos = Array.isArray(results[0]) ? results[0] : (results[0].data || []);
      campanas   = Array.isArray(results[1]) ? results[1] : (results[1].data || []);
      renderContactos();
      renderCampanas();
      updateStats();
    }).catch(function (error) {
      if (String(error && error.message || '') === '403') {
        loadLocalFallback();
        return;
      }
      prospectos = []; campanas = [];
      renderContactos();
      renderCampanas();
      updateStats();
    });
  }

  /* ── Stats ── */
  function updateStats() {
    var thisMonth = new Date().toISOString().slice(0, 7);
    var alta = 0, nuevos = 0;
    prospectos.forEach(function (p) {
      if (parseFloat(p.score_propension || 0) >= 0.6) alta++;
      if ((p.fecha_creacion || '').slice(0, 7) === thisMonth) nuevos++;
    });
    var activasCamp = campanas.filter(function (c) { return c.estado === 'activa'; }).length;
    document.getElementById('pv-stat-total').textContent   = prospectos.length;
    document.getElementById('pv-stat-alta').textContent    = alta;
    document.getElementById('pv-stat-campanas').textContent= activasCamp;
    document.getElementById('pv-stat-nuevos').textContent  = nuevos;
  }

  /* ── Tabs ── */
  window.showTab = function (id) {
    document.querySelectorAll('.pv-tab').forEach(function (t) { t.classList.toggle('is-active', t.dataset.tab === id); });
    document.querySelectorAll('.pv-tab-panel').forEach(function (p) { p.classList.toggle('is-active', p.id === 'pv-panel-' + id); });
  };

  /* ─── CONTACTOS ─── */
  window.sortBy = function (col) {
    if (sortCol === col) { sortAsc = !sortAsc; } else { sortCol = col; sortAsc = true; }
    renderContactos();
  };
  window.toggleAll = function (v) {
    document.querySelectorAll('.pv-row-check').forEach(function (cb) { cb.checked = v; });
    syncDelBtn();
  };
  window.syncDelBtn = function () {
    document.getElementById('pv-del-btn').disabled = !document.querySelectorAll('.pv-row-check:checked').length;
  };

  window.renderContactos = function () {
    var q  = (document.getElementById('pv-search').value || '').toLowerCase();
    var ff = document.getElementById('pv-filter-fuente').value;
    var rows = prospectos.filter(function (p, i) {
      p._idx = i;
      if (ff && (p.fuente || '').toLowerCase() !== ff) return false;
      if (q && ((p.nombre || '') + ' ' + (p.telefono || '')).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    rows.sort(function (a, b) {
      var av = String(a[sortCol] || '').toLowerCase();
      var bv = String(b[sortCol] || '').toLowerCase();
      return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    var tbody = document.getElementById('pv-tbody');
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="6"><div class="pv-empty"><i class="fa-solid fa-handshake"></i>No hay contactos todavía.</div></td></tr>';
      syncDelBtn(); updateStats(); return;
    }
    tbody.innerHTML = rows.map(function (p) {
      var score = parseFloat(p.score_propension || 0);
      var pct   = Math.round(score * 100);
      var cls   = score >= 0.6 ? 'is-high' : score < 0.3 ? 'is-low' : '';
      var fuente = (p.fuente || 'otro').toLowerCase();
      var fuenteLabel = { referido:'Referido', directo:'Directo', feria:'Feria', online:'Online', campana:'Campaña', otro:'Otro' }[fuente] || fuente;
      return '<tr onclick="openContactDrawer(' + p.id + ')">'
        + '<td onclick="event.stopPropagation()"><input type="checkbox" class="pv-row-check" data-id="' + p.id + '" onchange="syncDelBtn()" /></td>'
        + '<td><strong>' + esc(p.nombre || '') + '</strong></td>'
        + '<td>' + esc(p.telefono || '—') + '</td>'
        + '<td><span class="pv-fuente pv-fuente--' + esc(fuente) + '">' + esc(fuenteLabel) + '</span></td>'
        + '<td><div class="pv-score-wrap"><div class="pv-score-bar"><div class="pv-score-fill ' + cls + '" style="width:' + pct + '%"></div></div><span class="pv-score-num">' + pct + '%</span></div></td>'
        + '<td>' + esc((p.fecha_creacion || '').slice(0, 10) || '—') + '</td>'
        + '</tr>';
    }).join('');
    document.getElementById('pv-check-all').checked = false;
    syncDelBtn(); updateStats();
  };

  window.openContactDrawer = function (id) {
    editContactId = id;
    var p = id !== null ? prospectos.find(function (x) { return x.id === id; }) : null;
    document.getElementById('pv-contact-drawer-title').textContent = p ? 'Editar contacto' : 'Nuevo contacto';
    document.getElementById('pv-f-nombre').value  = p ? (p.nombre || '') : '';
    document.getElementById('pv-f-tel').value     = p ? (p.telefono || '') : '';
    document.getElementById('pv-f-fuente').value  = p ? (p.fuente || 'directo') : 'directo';
    document.getElementById('pv-f-dir').value     = p ? (p.direccion || '') : '';
    document.getElementById('pv-f-score').value   = p ? (p.score_propension !== undefined ? p.score_propension : '') : '';
    document.getElementById('pv-f-notas').value   = p ? (p.notas || '') : '';
    document.getElementById('pv-f-del-btn').style.display = p ? '' : 'none';
    openDrawer('pv-contact-drawer');
  };

  window.saveContact = function () {
    var nombre = (document.getElementById('pv-f-nombre').value || '').trim();
    if (!nombre) { showToast('El nombre es obligatorio.'); return; }
    var payload = {
      nombre:           nombre,
      telefono:         document.getElementById('pv-f-tel').value.trim(),
      fuente:           document.getElementById('pv-f-fuente').value,
      direccion:        document.getElementById('pv-f-dir').value.trim(),
      score_propension: parseFloat(document.getElementById('pv-f-score').value || '0') || 0,
      notas:            document.getElementById('pv-f-notas').value.trim(),
    };
    var isNew = editContactId === null;
    var url, method;
    if (INTELICOOP_ENABLED && INTELICOOP_API_BASE) {
      url    = isNew ? INTELICOOP_API_BASE + '/prospectos' : INTELICOOP_API_BASE + '/prospectos/' + editContactId;
      method = isNew ? 'POST' : 'PUT';
    } else {
      url    = isNew ? LOCAL_API : LOCAL_API + '/' + editContactId;
      method = isNew ? 'POST' : 'PUT';
    }
    fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.id || res.success) {
          closeAllDrawers(); showToast(isNew ? 'Proveedor agregado.' : 'Proveedor actualizado.'); load();
        } else { showToast(res.detail || res.error || 'Error al guardar.'); }
      })
      .catch(function () { showToast('Error de conexión.'); });
  };

  /* ─── CAMPAÑAS ─── */
  window.renderCampanas = function () {
    var fe = document.getElementById('pv-camp-filter').value;
    var rows = campanas.filter(function (c) { return !fe || c.estado === fe; });
    var container = document.getElementById('pv-camp-container');
    if (!rows.length) {
      container.innerHTML = '<div class="pv-empty"><i class="fa-solid fa-bullhorn"></i>No hay campañas todavía.</div>';
      return;
    }
    var badgeMap = { activa: 'pv-badge--activa', borrador: 'pv-badge--borrador', cerrada: 'pv-badge--cerrada' };
    container.innerHTML = '<div class="pv-camp-grid">' + rows.map(function (c) {
      var badge = '<span class="pv-badge ' + (badgeMap[c.estado] || 'pv-badge--borrador') + '">' + esc(c.estado || '') + '</span>';
      var inicio = (c.fecha_inicio || '').slice(0, 10);
      var fin    = (c.fecha_fin || '').slice(0, 10);
      return '<div class="pv-camp-card" onclick="openCampDrawer(' + c.id + ')">'
        + '<div class="pv-camp-card__name">' + esc(c.nombre || '') + '</div>'
        + '<div class="pv-camp-card__meta">'
        + '<span>' + esc(c.tipo || '') + '</span>'
        + badge
        + (inicio ? '<span>' + inicio + '</span>' : '')
        + (fin ? '<span>→ ' + fin + '</span>' : '')
        + '</div>'
        + '</div>';
    }).join('') + '</div>';
    updateStats();
  };

  window.openCampDrawer = function (id) {
    var c = id !== null ? campanas.find(function (x) { return x.id === id; }) : null;
    document.getElementById('pv-camp-drawer-title').textContent = c ? 'Editar campaña' : 'Nueva campaña';
    document.getElementById('pv-cf-nombre').value = c ? (c.nombre || '') : '';
    document.getElementById('pv-cf-tipo').value   = c ? (c.tipo || 'Colocacion') : 'Colocacion';
    document.getElementById('pv-cf-inicio').value = c ? ((c.fecha_inicio || '').slice(0, 10)) : '';
    document.getElementById('pv-cf-fin').value    = c ? ((c.fecha_fin || '').slice(0, 10)) : '';
    document.getElementById('pv-cf-estado').value = c ? (c.estado || 'borrador') : 'borrador';
    openDrawer('pv-camp-drawer');
  };

  window.saveCampaña = function () {
    if (!INTELICOOP_ENABLED || !INTELICOOP_API_BASE) { showToast('Intelicoop no está habilitado.'); return; }
    var nombre = (document.getElementById('pv-cf-nombre').value || '').trim();
    if (!nombre) { showToast('El nombre es obligatorio.'); return; }
    var payload = {
      nombre:       nombre,
      tipo:         document.getElementById('pv-cf-tipo').value,
      fecha_inicio: document.getElementById('pv-cf-inicio').value || null,
      fecha_fin:    document.getElementById('pv-cf-fin').value || null,
      estado:       document.getElementById('pv-cf-estado').value,
    };
    fetch(INTELICOOP_API_BASE + '/campanas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.id || res.success) {
          closeAllDrawers(); showToast('Campaña guardada.'); load();
        } else { showToast(res.detail || res.error || 'Error al guardar.'); }
      })
      .catch(function () { showToast('Error de conexión.'); });
  };

  /* ─── CONFIRM / DELETE ─── */
  window.openConfirm = function (mode) {
    confirmMode = mode;
    if (mode === 'bulk') {
      var n = document.querySelectorAll('.pv-row-check:checked').length;
      document.getElementById('pv-confirm-title').textContent = '¿Eliminar ' + n + ' proveedor' + (n !== 1 ? 'es' : '') + '?';
      document.getElementById('pv-confirm-text').textContent  = (INTELICOOP_ENABLED && INTELICOOP_API_BASE)
        ? 'Se eliminarán también de Intelicoop.' : 'Esta acción no se puede deshacer.';
      confirmCallback = function () {
        var ids = [];
        document.querySelectorAll('.pv-row-check:checked').forEach(function (cb) { ids.push(parseInt(cb.dataset.id, 10)); });
        var base = (INTELICOOP_ENABLED && INTELICOOP_API_BASE) ? INTELICOOP_API_BASE + '/prospectos' : LOCAL_API;
        Promise.all(ids.map(function (id) {
          return fetch(base + '/' + id, { method: 'DELETE', credentials: 'same-origin' });
        })).then(function () { showToast('Proveedores eliminados.'); load(); });
      };
    } else {
      var p = editContactId !== null ? prospectos.find(function (x) { return x.id === editContactId; }) : null;
      document.getElementById('pv-confirm-title').textContent = '¿Eliminar "' + ((p && p.nombre) || 'este proveedor') + '"?';
      document.getElementById('pv-confirm-text').textContent  = (INTELICOOP_ENABLED && INTELICOOP_API_BASE)
        ? 'Se eliminará también de Intelicoop.' : 'Esta acción no se puede deshacer.';
      confirmCallback = function () {
        var base = (INTELICOOP_ENABLED && INTELICOOP_API_BASE) ? INTELICOOP_API_BASE + '/prospectos' : LOCAL_API;
        fetch(base + '/' + editContactId, { method: 'DELETE', credentials: 'same-origin' })
          .then(function () { closeAllDrawers(); showToast('Proveedor eliminado.'); load(); });
      };
    }
    document.getElementById('pv-confirm').classList.add('is-open');
  };
  window.closeConfirm = function () { document.getElementById('pv-confirm').classList.remove('is-open'); };
  document.getElementById('pv-confirm-ok').addEventListener('click', function () {
    closeConfirm();
    if (confirmCallback) { confirmCallback(); confirmCallback = null; }
  });

  /* ─── DRAWERS ─── */
  function openDrawer(id) {
    document.querySelectorAll('.pv-drawer').forEach(function (d) { d.classList.remove('is-open'); });
    document.getElementById(id).classList.add('is-open');
    document.getElementById('pv-overlay').classList.add('is-open');
  }
  window.closeAllDrawers = function () {
    document.querySelectorAll('.pv-drawer').forEach(function (d) { d.classList.remove('is-open'); });
    document.getElementById('pv-overlay').classList.remove('is-open');
    editContactId = null;
  };

  /* ─── HELPERS ─── */
  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function showToast(msg) {
    var t = document.getElementById('pv-toast');
    t.textContent = msg; t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 2800);
  }

  /* ─── INIT ─── */
  load();
})();
</script>
</body>
</html>
"""
