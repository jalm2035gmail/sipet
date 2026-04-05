from __future__ import annotations


def whatsapp_html() -> str:
    return _HTML


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>WhatsApp Business — Multitienda</title>
  <link rel="stylesheet" href="/multitienda/static/css/whatsapp.css" />
</head>
<body>
<main>

  <!-- Status banner -->
  <div class="wa-status-banner" id="wa-status-banner">
    <div class="wa-status-banner__dot"></div>
    <div>
      <div class="wa-status-banner__text" id="wa-status-text">Configurando integración…</div>
      <div class="wa-status-banner__sub" id="wa-status-sub">Ingresa el número de teléfono en Configuración para activar.</div>
    </div>
    <button class="wa-btn" onclick="showTab('configuracion')" style="flex-shrink:0;">
      <i class="fa-solid fa-gear"></i> Configurar
    </button>
  </div>

  <!-- Stats -->
  <div class="wa-stats">
    <div class="wa-stat">
      <div class="wa-stat__icon wa-stat__icon--green"><i class="fa-brands fa-whatsapp"></i></div>
      <div><div class="wa-stat__value" id="wa-stat-mensajes">0</div><div class="wa-stat__label">Mensajes enviados</div></div>
    </div>
    <div class="wa-stat">
      <div class="wa-stat__icon wa-stat__icon--blue"><i class="fa-solid fa-users"></i></div>
      <div><div class="wa-stat__value" id="wa-stat-contactos">0</div><div class="wa-stat__label">Contactos</div></div>
    </div>
    <div class="wa-stat">
      <div class="wa-stat__icon wa-stat__icon--amber"><i class="fa-solid fa-layer-group"></i></div>
      <div><div class="wa-stat__value" id="wa-stat-plantillas">0</div><div class="wa-stat__label">Plantillas</div></div>
    </div>
    <div class="wa-stat">
      <div class="wa-stat__icon wa-stat__icon--purple"><i class="fa-solid fa-bullhorn"></i></div>
      <div><div class="wa-stat__value" id="wa-stat-campanas">0</div><div class="wa-stat__label">Campañas</div></div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="wa-tabs">
    <button class="wa-tab is-active" data-tab="contactos" onclick="showTab('contactos')">
      <i class="fa-solid fa-address-book"></i> Contactos
    </button>
    <button class="wa-tab" data-tab="plantillas" onclick="showTab('plantillas')">
      <i class="fa-solid fa-layer-group"></i> Plantillas
    </button>
    <button class="wa-tab" data-tab="campanas" onclick="showTab('campanas')">
      <i class="fa-solid fa-bullhorn"></i> Campañas
    </button>
    <button class="wa-tab" data-tab="configuracion" onclick="showTab('configuracion')">
      <i class="fa-solid fa-gear"></i> Configuración
    </button>
  </div>

  <!-- ══ TAB: Contactos ══ -->
  <div class="wa-tab-panel is-active" id="wa-panel-contactos">
    <div class="wa-toolbar">
      <div class="wa-toolbar__left">
        <button class="wa-btn wa-btn--primary" onclick="openContactDrawer(-1)">
          <i class="fa-solid fa-plus"></i> Nuevo contacto
        </button>
        <button class="wa-btn wa-btn--danger" id="wa-contact-del-btn" disabled onclick="openConfirm('contact-bulk')">
          <i class="fa-regular fa-trash-can"></i> Eliminar
        </button>
      </div>
      <div class="wa-search">
        <i class="fa-solid fa-magnifying-glass" style="color:var(--wa-muted);font-size:.8rem;"></i>
        <input type="text" id="wa-contact-search" placeholder="Buscar nombre o teléfono…" oninput="renderContacts()" />
      </div>
    </div>
    <div class="wa-table-wrap">
      <table class="wa-table">
        <thead>
          <tr>
            <th style="width:36px;"><input type="checkbox" id="wa-contact-check-all" onchange="toggleContactAll(this.checked)" /></th>
            <th class="sortable" onclick="contactSortBy('nombre')">Nombre <span class="sarr">↕</span></th>
            <th class="sortable" onclick="contactSortBy('telefono')">Teléfono <span class="sarr">↕</span></th>
            <th class="sortable" onclick="contactSortBy('email')">Email <span class="sarr">↕</span></th>
            <th class="sortable" onclick="contactSortBy('etiqueta')">Etiqueta <span class="sarr">↕</span></th>
            <th class="sortable" onclick="contactSortBy('fecha')">Registrado <span class="sarr">↕</span></th>
          </tr>
        </thead>
        <tbody id="wa-contact-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- ══ TAB: Plantillas ══ -->
  <div class="wa-tab-panel" id="wa-panel-plantillas">
    <div class="wa-toolbar">
      <div class="wa-toolbar__left">
        <button class="wa-btn wa-btn--primary" onclick="openTplDrawer(-1)">
          <i class="fa-solid fa-plus"></i> Nueva plantilla
        </button>
        <button class="wa-btn wa-btn--danger" id="wa-tpl-del-btn" disabled onclick="openConfirm('tpl-bulk')">
          <i class="fa-regular fa-trash-can"></i> Eliminar
        </button>
      </div>
      <div class="wa-search">
        <i class="fa-solid fa-magnifying-glass" style="color:var(--wa-muted);font-size:.8rem;"></i>
        <input type="text" id="wa-tpl-search" placeholder="Buscar plantilla…" oninput="renderPlantillas()" />
      </div>
    </div>
    <div class="wa-table-wrap">
      <table class="wa-table">
        <thead>
          <tr>
            <th style="width:36px;"><input type="checkbox" id="wa-tpl-check-all" onchange="toggleTplAll(this.checked)" /></th>
            <th class="sortable" onclick="tplSortBy('nombre')">Nombre <span class="sarr">↕</span></th>
            <th class="sortable" onclick="tplSortBy('categoria')">Categoría <span class="sarr">↕</span></th>
            <th>Vista previa</th>
            <th class="sortable" onclick="tplSortBy('estado')">Estado <span class="sarr">↕</span></th>
          </tr>
        </thead>
        <tbody id="wa-tpl-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- ══ TAB: Campañas ══ -->
  <div class="wa-tab-panel" id="wa-panel-campanas">
    <div class="wa-toolbar">
      <div class="wa-toolbar__left">
        <button class="wa-btn wa-btn--primary" onclick="openCampDrawer(-1)">
          <i class="fa-solid fa-plus"></i> Nueva campaña
        </button>
        <button class="wa-btn wa-btn--danger" id="wa-camp-del-btn" disabled onclick="openConfirm('camp-bulk')">
          <i class="fa-regular fa-trash-can"></i> Eliminar
        </button>
      </div>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <select class="wa-filter-select" id="wa-camp-filter" onchange="renderCampanas()">
          <option value="">Todos los estados</option>
          <option value="borrador">Borrador</option>
          <option value="programada">Programada</option>
          <option value="enviada">Enviada</option>
          <option value="pausada">Pausada</option>
        </select>
        <div class="wa-search">
          <i class="fa-solid fa-magnifying-glass" style="color:var(--wa-muted);font-size:.8rem;"></i>
          <input type="text" id="wa-camp-search" placeholder="Buscar campaña…" oninput="renderCampanas()" />
        </div>
      </div>
    </div>
    <div class="wa-table-wrap">
      <table class="wa-table">
        <thead>
          <tr>
            <th style="width:36px;"><input type="checkbox" id="wa-camp-check-all" onchange="toggleCampAll(this.checked)" /></th>
            <th class="sortable" onclick="campSortBy('nombre')">Campaña <span class="sarr">↕</span></th>
            <th class="sortable" onclick="campSortBy('plantilla')">Plantilla <span class="sarr">↕</span></th>
            <th class="sortable" onclick="campSortBy('destinatarios')">Destinatarios <span class="sarr">↕</span></th>
            <th class="sortable" onclick="campSortBy('fecha')">Fecha envío <span class="sarr">↕</span></th>
            <th class="sortable" onclick="campSortBy('estado')">Estado <span class="sarr">↕</span></th>
          </tr>
        </thead>
        <tbody id="wa-camp-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- ══ TAB: Configuración ══ -->
  <div class="wa-tab-panel" id="wa-panel-configuracion">
    <div class="wa-config-grid">
      <div class="wa-card">
        <div class="wa-card__title"><i class="fa-brands fa-whatsapp"></i> Conexión WhatsApp Business API</div>
        <div class="wa-field">
          <label for="wa-cfg-phone">Número de teléfono (con código de país)</label>
          <input id="wa-cfg-phone" type="tel" placeholder="+52 55 1234 5678" />
          <span class="wa-field--hint">Número registrado en WhatsApp Business API.</span>
        </div>
        <div class="wa-field">
          <label for="wa-cfg-token">Token de acceso (API key)</label>
          <input id="wa-cfg-token" type="password" placeholder="EAAxxxxxxxxx…" />
          <span class="wa-field--hint">Token permanente de Meta Business / 360dialog / Twilio.</span>
        </div>
        <div class="wa-field">
          <label for="wa-cfg-phoneid">Phone ID</label>
          <input id="wa-cfg-phoneid" type="text" placeholder="1234567890" />
        </div>
        <div class="wa-field">
          <label for="wa-cfg-proveedor">Proveedor</label>
          <select id="wa-cfg-proveedor">
            <option value="meta">Meta (Cloud API)</option>
            <option value="360dialog">360dialog</option>
            <option value="twilio">Twilio</option>
            <option value="otro">Otro</option>
          </select>
        </div>
        <button class="wa-btn wa-btn--primary" style="margin-top:4px;" onclick="saveConfig()">
          <i class="fa-solid fa-floppy-disk"></i> Guardar configuración
        </button>
      </div>

      <div class="wa-card">
        <div class="wa-card__title"><i class="fa-solid fa-robot"></i> Respuestas automáticas</div>
        <div class="wa-field">
          <label for="wa-cfg-bienvenida">Mensaje de bienvenida</label>
          <textarea id="wa-cfg-bienvenida" placeholder="Hola {{nombre}}, gracias por contactarnos. ¿En qué podemos ayudarte?"></textarea>
        </div>
        <div class="wa-field">
          <label for="wa-cfg-ausencia">Mensaje de ausencia</label>
          <textarea id="wa-cfg-ausencia" placeholder="Estamos fuera de horario. Te responderemos pronto."></textarea>
        </div>
        <div class="wa-field--row">
          <div class="wa-field">
            <label for="wa-cfg-horario-desde">Horario desde</label>
            <input id="wa-cfg-horario-desde" type="time" value="09:00" />
          </div>
          <div class="wa-field">
            <label for="wa-cfg-horario-hasta">Horario hasta</label>
            <input id="wa-cfg-horario-hasta" type="time" value="18:00" />
          </div>
        </div>
        <button class="wa-btn wa-btn--primary" style="margin-top:4px;" onclick="saveAutoConfig()">
          <i class="fa-solid fa-floppy-disk"></i> Guardar
        </button>
      </div>
    </div>
  </div>

  <!-- ── Confirm ── -->
  <div class="wa-confirm" id="wa-confirm">
    <div class="wa-confirm__card">
      <div class="wa-confirm__icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div class="wa-confirm__title" id="wa-confirm-title">¿Eliminar?</div>
      <div class="wa-confirm__text" id="wa-confirm-text">Esta acción no se puede deshacer.</div>
      <div class="wa-confirm__actions">
        <button class="wa-btn" onclick="closeConfirm()">Cancelar</button>
        <button class="wa-btn wa-btn--danger" id="wa-confirm-ok">Sí, eliminar</button>
      </div>
    </div>
  </div>
</main>

<!-- Overlays & drawers -->
<div class="wa-overlay" id="wa-overlay" onclick="closeAllDrawers()"></div>

<!-- Contact drawer -->
<aside class="wa-drawer" id="wa-contact-drawer">
  <div class="wa-drawer__head">
    <span class="wa-drawer__title" id="wa-contact-drawer-title">Nuevo contacto</span>
    <button class="wa-drawer__close" onclick="closeAllDrawers()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="wa-drawer__body">
    <div class="wa-field--row">
      <div class="wa-field">
        <label for="wa-cf-nombre">Nombre <span style="color:var(--wa-danger)">*</span></label>
        <input id="wa-cf-nombre" type="text" placeholder="Nombre" />
      </div>
      <div class="wa-field">
        <label for="wa-cf-apellido">Apellido</label>
        <input id="wa-cf-apellido" type="text" placeholder="Apellido" />
      </div>
    </div>
    <div class="wa-field">
      <label for="wa-cf-tel">Teléfono (con código de país) <span style="color:var(--wa-danger)">*</span></label>
      <input id="wa-cf-tel" type="tel" placeholder="+52 55 1234 5678" />
    </div>
    <div class="wa-field">
      <label for="wa-cf-email">Email</label>
      <input id="wa-cf-email" type="email" placeholder="correo@ejemplo.com" />
    </div>
    <div class="wa-field">
      <label for="wa-cf-etiqueta">Etiqueta</label>
      <select id="wa-cf-etiqueta">
        <option value="">Sin etiqueta</option>
        <option value="cliente">Cliente</option>
        <option value="prospecto">Prospecto</option>
        <option value="proveedor">Proveedor</option>
        <option value="vip">VIP</option>
      </select>
    </div>
    <div class="wa-field">
      <label for="wa-cf-notas">Notas</label>
      <textarea id="wa-cf-notas" placeholder="Observaciones sobre el contacto…"></textarea>
    </div>
  </div>
  <div class="wa-drawer__footer">
    <button class="wa-btn wa-btn--danger" id="wa-cf-del-btn" onclick="openConfirm('contact-single')" style="display:none;">
      <i class="fa-regular fa-trash-can"></i> Eliminar
    </button>
    <button class="wa-btn wa-btn--primary" onclick="saveContact()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<!-- Template drawer -->
<aside class="wa-drawer" id="wa-tpl-drawer">
  <div class="wa-drawer__head">
    <span class="wa-drawer__title" id="wa-tpl-drawer-title">Nueva plantilla</span>
    <button class="wa-drawer__close" onclick="closeAllDrawers()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="wa-drawer__body">
    <div class="wa-field">
      <label for="wa-tf-nombre">Nombre de la plantilla <span style="color:var(--wa-danger)">*</span></label>
      <input id="wa-tf-nombre" type="text" placeholder="bienvenida_cliente" style="text-transform:lowercase;" />
      <span class="wa-field--hint">Solo minúsculas, números y guiones bajos.</span>
    </div>
    <div class="wa-field">
      <label for="wa-tf-categoria">Categoría</label>
      <select id="wa-tf-categoria">
        <option value="marketing">Marketing</option>
        <option value="utilidad">Utilidad</option>
        <option value="autenticacion">Autenticación</option>
      </select>
    </div>
    <div class="wa-field">
      <label for="wa-tf-idioma">Idioma</label>
      <select id="wa-tf-idioma">
        <option value="es">Español</option>
        <option value="en">Inglés</option>
        <option value="pt">Portugués</option>
      </select>
    </div>
    <div class="wa-field">
      <label for="wa-tf-cuerpo">Cuerpo del mensaje <span style="color:var(--wa-danger)">*</span></label>
      <textarea id="wa-tf-cuerpo" placeholder="Hola {{1}}, tu pedido #{{2}} está listo." oninput="updateTplPreview()"></textarea>
      <span class="wa-field--hint">Usa {{1}}, {{2}}… para variables dinámicas.</span>
    </div>
    <div class="wa-field">
      <label>Vista previa</label>
      <div class="wa-tpl-preview">
        <div class="wa-tpl-bubble" id="wa-tpl-preview-text">Hola {{1}}, tu pedido #{{2}} está listo.</div>
        <div class="wa-tpl-time">12:00 ✓✓</div>
      </div>
    </div>
    <div class="wa-field">
      <label for="wa-tf-estado">Estado</label>
      <select id="wa-tf-estado">
        <option value="borrador">Borrador</option>
        <option value="aprobada">Aprobada</option>
        <option value="rechazada">Rechazada</option>
      </select>
    </div>
  </div>
  <div class="wa-drawer__footer">
    <button class="wa-btn wa-btn--danger" id="wa-tf-del-btn" onclick="openConfirm('tpl-single')" style="display:none;">
      <i class="fa-regular fa-trash-can"></i> Eliminar
    </button>
    <button class="wa-btn wa-btn--primary" onclick="saveTpl()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<!-- Campaign drawer -->
<aside class="wa-drawer" id="wa-camp-drawer">
  <div class="wa-drawer__head">
    <span class="wa-drawer__title" id="wa-camp-drawer-title">Nueva campaña</span>
    <button class="wa-drawer__close" onclick="closeAllDrawers()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="wa-drawer__body">
    <div class="wa-field">
      <label for="wa-kf-nombre">Nombre de la campaña <span style="color:var(--wa-danger)">*</span></label>
      <input id="wa-kf-nombre" type="text" placeholder="Promoción Semana Santa" />
    </div>
    <div class="wa-field">
      <label for="wa-kf-plantilla">Plantilla</label>
      <select id="wa-kf-plantilla"><option value="">— Seleccionar plantilla —</option></select>
    </div>
    <div class="wa-field">
      <label for="wa-kf-dest">Destinatarios (segmento)</label>
      <select id="wa-kf-dest">
        <option value="todos">Todos los contactos</option>
        <option value="clientes">Solo clientes</option>
        <option value="prospectos">Solo prospectos</option>
        <option value="vip">Solo VIP</option>
      </select>
    </div>
    <div class="wa-field">
      <label for="wa-kf-fecha">Fecha y hora de envío</label>
      <input id="wa-kf-fecha" type="datetime-local" />
    </div>
    <div class="wa-field">
      <label for="wa-kf-estado">Estado</label>
      <select id="wa-kf-estado">
        <option value="borrador">Borrador</option>
        <option value="programada">Programada</option>
        <option value="pausada">Pausada</option>
      </select>
    </div>
    <div class="wa-field">
      <label for="wa-kf-notas">Notas</label>
      <textarea id="wa-kf-notas" placeholder="Descripción o notas internas…"></textarea>
    </div>
  </div>
  <div class="wa-drawer__footer">
    <button class="wa-btn wa-btn--danger" id="wa-kf-del-btn" onclick="openConfirm('camp-single')" style="display:none;">
      <i class="fa-regular fa-trash-can"></i> Eliminar
    </button>
    <button class="wa-btn wa-btn--primary" onclick="saveCamp()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<!-- Toast -->
<div class="wa-toast" id="wa-toast"></div>

<script>
(function () {
  /* ── Storage ── */
  var SK_CONTACTS  = 'multitienda_wa_contactos';
  var SK_TEMPLATES = 'multitienda_wa_plantillas';
  var SK_CAMPAIGNS = 'multitienda_wa_campanas';
  var SK_CONFIG    = 'multitienda_wa_config';

  var contacts  = [];
  var templates = [];
  var campaigns = [];
  var config    = {};

  var cSort = { col: 'nombre', asc: true };
  var tSort = { col: 'nombre', asc: true };
  var kSort = { col: 'nombre', asc: true };

  var editContact = -1;
  var editTpl     = -1;
  var editCamp    = -1;
  var confirmMode = '';

  function load() {
    try { contacts  = JSON.parse(localStorage.getItem(SK_CONTACTS)  || '[]'); } catch (e) { contacts  = []; }
    try { templates = JSON.parse(localStorage.getItem(SK_TEMPLATES) || '[]'); } catch (e) { templates = []; }
    try { campaigns = JSON.parse(localStorage.getItem(SK_CAMPAIGNS) || '[]'); } catch (e) { campaigns = []; }
    try { config    = JSON.parse(localStorage.getItem(SK_CONFIG)    || '{}'); } catch (e) { config    = {}; }
  }
  function saveAll() {
    try { localStorage.setItem(SK_CONTACTS,  JSON.stringify(contacts));  } catch (e) {}
    try { localStorage.setItem(SK_TEMPLATES, JSON.stringify(templates)); } catch (e) {}
    try { localStorage.setItem(SK_CAMPAIGNS, JSON.stringify(campaigns)); } catch (e) {}
    try { localStorage.setItem(SK_CONFIG,    JSON.stringify(config));    } catch (e) {}
  }

  /* ── Stats ── */
  function updateStats() {
    var mensajes = 0;
    campaigns.forEach(function (c) { if (c.estado === 'enviada') mensajes += parseInt(c.destinatariosN || 0, 10); });
    document.getElementById('wa-stat-mensajes').textContent   = mensajes;
    document.getElementById('wa-stat-contactos').textContent  = contacts.length;
    document.getElementById('wa-stat-plantillas').textContent = templates.length;
    document.getElementById('wa-stat-campanas').textContent   = campaigns.length;
  }

  /* ── Status banner ── */
  function updateStatusBanner() {
    var banner = document.getElementById('wa-status-banner');
    var textEl = document.getElementById('wa-status-text');
    var subEl  = document.getElementById('wa-status-sub');
    if (config.phone && config.token) {
      banner.className = 'wa-status-banner wa-status-banner--ok';
      textEl.textContent = 'Conectado · ' + config.phone;
      subEl.textContent  = 'Proveedor: ' + (config.proveedor || 'Meta') + ' · Integración configurada.';
    } else {
      banner.className = 'wa-status-banner wa-status-banner--warn';
      textEl.textContent = 'Sin configurar';
      subEl.textContent  = 'Ingresa el número y token en la pestaña Configuración para activar.';
    }
  }

  /* ── Tabs ── */
  window.showTab = function (id) {
    document.querySelectorAll('.wa-tab').forEach(function (t) { t.classList.toggle('is-active', t.dataset.tab === id); });
    document.querySelectorAll('.wa-tab-panel').forEach(function (p) { p.classList.toggle('is-active', p.id === 'wa-panel-' + id); });
    if (id === 'configuracion') loadConfigForm();
  };

  /* ─── CONTACTS ─── */
  window.renderContacts = function () {
    var q = (document.getElementById('wa-contact-search').value || '').toLowerCase();
    var rows = contacts.filter(function (c, i) {
      c._idx = i;
      return !q || (c.nombre + ' ' + c.apellido + ' ' + c.telefono).toLowerCase().indexOf(q) >= 0;
    });
    rows.sort(function (a, b) {
      var av = (a[cSort.col] || '').toLowerCase();
      var bv = (b[cSort.col] || '').toLowerCase();
      return cSort.asc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    var tbody = document.getElementById('wa-contact-tbody');
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="6"><div class="wa-empty"><i class="fa-solid fa-address-book"></i>No hay contactos todavía.</div></td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (c) {
      return '<tr onclick="openContactDrawer(' + c._idx + ')">'
        + '<td onclick="event.stopPropagation()"><input type="checkbox" class="wa-contact-check" data-idx="' + c._idx + '" onchange="syncContactDel()" /></td>'
        + '<td>' + esc(c.nombre + ' ' + (c.apellido || '')) + '</td>'
        + '<td><span class="wa-phone"><i class="fa-brands fa-whatsapp"></i>' + esc(c.telefono || '—') + '</span></td>'
        + '<td>' + esc(c.email || '—') + '</td>'
        + '<td>' + esc(c.etiqueta || '—') + '</td>'
        + '<td>' + esc(c.fecha || '—') + '</td>'
        + '</tr>';
    }).join('');
    document.getElementById('wa-contact-check-all').checked = false;
    syncContactDel();
    updateStats();
  };
  window.contactSortBy = function (col) {
    if (cSort.col === col) { cSort.asc = !cSort.asc; } else { cSort.col = col; cSort.asc = true; }
    renderContacts();
  };
  window.toggleContactAll = function (v) {
    document.querySelectorAll('.wa-contact-check').forEach(function (cb) { cb.checked = v; });
    syncContactDel();
  };
  window.syncContactDel = function () {
    document.getElementById('wa-contact-del-btn').disabled = !document.querySelectorAll('.wa-contact-check:checked').length;
  };
  window.openContactDrawer = function (idx) {
    editContact = idx;
    var c = idx >= 0 ? contacts[idx] : null;
    document.getElementById('wa-contact-drawer-title').textContent = c ? 'Editar contacto' : 'Nuevo contacto';
    document.getElementById('wa-cf-nombre').value   = c ? (c.nombre || '') : '';
    document.getElementById('wa-cf-apellido').value = c ? (c.apellido || '') : '';
    document.getElementById('wa-cf-tel').value      = c ? (c.telefono || '') : '';
    document.getElementById('wa-cf-email').value    = c ? (c.email || '') : '';
    document.getElementById('wa-cf-etiqueta').value = c ? (c.etiqueta || '') : '';
    document.getElementById('wa-cf-notas').value    = c ? (c.notas || '') : '';
    document.getElementById('wa-cf-del-btn').style.display = c ? '' : 'none';
    openDrawer('wa-contact-drawer');
  };
  window.saveContact = function () {
    var nombre = (document.getElementById('wa-cf-nombre').value || '').trim();
    var tel    = (document.getElementById('wa-cf-tel').value || '').trim();
    if (!nombre) { showToast('El nombre es obligatorio.'); return; }
    if (!tel)    { showToast('El teléfono es obligatorio.'); return; }
    var rec = {
      nombre:   nombre,
      apellido: document.getElementById('wa-cf-apellido').value.trim(),
      telefono: tel,
      email:    document.getElementById('wa-cf-email').value.trim(),
      etiqueta: document.getElementById('wa-cf-etiqueta').value,
      notas:    document.getElementById('wa-cf-notas').value.trim(),
      fecha:    editContact >= 0 ? (contacts[editContact].fecha || today()) : today(),
    };
    if (editContact >= 0) { contacts[editContact] = rec; } else { contacts.push(rec); }
    saveAll(); closeAllDrawers(); renderContacts(); showToast(editContact >= 0 ? 'Contacto actualizado.' : 'Contacto guardado.');
  };

  /* ─── TEMPLATES ─── */
  window.renderPlantillas = function () {
    var q = (document.getElementById('wa-tpl-search').value || '').toLowerCase();
    var rows = templates.filter(function (t, i) { t._idx = i; return !q || (t.nombre || '').toLowerCase().indexOf(q) >= 0; });
    rows.sort(function (a, b) {
      var av = (a[tSort.col] || '').toLowerCase();
      var bv = (b[tSort.col] || '').toLowerCase();
      return tSort.asc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    var tbody = document.getElementById('wa-tpl-tbody');
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="5"><div class="wa-empty"><i class="fa-solid fa-layer-group"></i>No hay plantillas todavía.</div></td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (t) {
      var stMap = { aprobada: 'wa-badge--approved', rechazada: 'wa-badge--rejected', borrador: 'wa-badge--draft' };
      var badge = '<span class="wa-badge ' + (stMap[t.estado] || 'wa-badge--draft') + '">' + esc(t.estado || 'borrador') + '</span>';
      var preview = (t.cuerpo || '').substring(0, 60) + ((t.cuerpo || '').length > 60 ? '…' : '');
      return '<tr onclick="openTplDrawer(' + t._idx + ')">'
        + '<td onclick="event.stopPropagation()"><input type="checkbox" class="wa-tpl-check" data-idx="' + t._idx + '" onchange="syncTplDel()" /></td>'
        + '<td><strong>' + esc(t.nombre || '') + '</strong></td>'
        + '<td>' + esc(t.categoria || '') + '</td>'
        + '<td style="font-size:.82rem;color:var(--wa-muted);font-style:italic;">' + esc(preview) + '</td>'
        + '<td>' + badge + '</td>'
        + '</tr>';
    }).join('');
    document.getElementById('wa-tpl-check-all').checked = false;
    syncTplDel();
    updateStats();
    populateTplSelect();
  };
  window.tplSortBy = function (col) {
    if (tSort.col === col) { tSort.asc = !tSort.asc; } else { tSort.col = col; tSort.asc = true; }
    renderPlantillas();
  };
  window.toggleTplAll = function (v) {
    document.querySelectorAll('.wa-tpl-check').forEach(function (cb) { cb.checked = v; });
    syncTplDel();
  };
  window.syncTplDel = function () {
    document.getElementById('wa-tpl-del-btn').disabled = !document.querySelectorAll('.wa-tpl-check:checked').length;
  };
  window.openTplDrawer = function (idx) {
    editTpl = idx;
    var t = idx >= 0 ? templates[idx] : null;
    document.getElementById('wa-tpl-drawer-title').textContent = t ? 'Editar plantilla' : 'Nueva plantilla';
    document.getElementById('wa-tf-nombre').value    = t ? (t.nombre || '') : '';
    document.getElementById('wa-tf-categoria').value = t ? (t.categoria || 'marketing') : 'marketing';
    document.getElementById('wa-tf-idioma').value    = t ? (t.idioma || 'es') : 'es';
    document.getElementById('wa-tf-cuerpo').value    = t ? (t.cuerpo || '') : '';
    document.getElementById('wa-tf-estado').value    = t ? (t.estado || 'borrador') : 'borrador';
    document.getElementById('wa-tf-del-btn').style.display = t ? '' : 'none';
    updateTplPreview();
    openDrawer('wa-tpl-drawer');
  };
  window.updateTplPreview = function () {
    var cuerpo = document.getElementById('wa-tf-cuerpo').value || '';
    document.getElementById('wa-tpl-preview-text').textContent = cuerpo || '(sin contenido)';
  };
  window.saveTpl = function () {
    var nombre = (document.getElementById('wa-tf-nombre').value || '').trim().toLowerCase().replace(/[^a-z0-9_]/g, '_');
    var cuerpo = (document.getElementById('wa-tf-cuerpo').value || '').trim();
    if (!nombre) { showToast('El nombre es obligatorio.'); return; }
    if (!cuerpo) { showToast('El cuerpo del mensaje es obligatorio.'); return; }
    var rec = {
      nombre:    nombre,
      categoria: document.getElementById('wa-tf-categoria').value,
      idioma:    document.getElementById('wa-tf-idioma').value,
      cuerpo:    cuerpo,
      estado:    document.getElementById('wa-tf-estado').value,
    };
    if (editTpl >= 0) { templates[editTpl] = rec; } else { templates.push(rec); }
    saveAll(); closeAllDrawers(); renderPlantillas(); showToast(editTpl >= 0 ? 'Plantilla actualizada.' : 'Plantilla guardada.');
  };

  /* ─── CAMPAIGNS ─── */
  function populateTplSelect() {
    var sel = document.getElementById('wa-kf-plantilla');
    var val = sel.value;
    sel.innerHTML = '<option value="">— Seleccionar plantilla —</option>'
      + templates.map(function (t) { return '<option value="' + esc(t.nombre) + '">' + esc(t.nombre) + '</option>'; }).join('');
    if (val) sel.value = val;
  }
  window.renderCampanas = function () {
    var q  = (document.getElementById('wa-camp-search').value || '').toLowerCase();
    var fe = document.getElementById('wa-camp-filter').value;
    var rows = campaigns.filter(function (c, i) {
      c._idx = i;
      if (fe && c.estado !== fe) return false;
      return !q || (c.nombre || '').toLowerCase().indexOf(q) >= 0;
    });
    rows.sort(function (a, b) {
      var av = (a[kSort.col] || '').toLowerCase();
      var bv = (b[kSort.col] || '').toLowerCase();
      return kSort.asc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    var tbody = document.getElementById('wa-camp-tbody');
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="6"><div class="wa-empty"><i class="fa-solid fa-bullhorn"></i>No hay campañas todavía.</div></td></tr>';
      return;
    }
    var stMap = { borrador: 'wa-badge--draft', programada: 'wa-badge--pending', enviada: 'wa-badge--delivered', pausada: 'wa-badge--failed' };
    tbody.innerHTML = rows.map(function (c) {
      var badge = '<span class="wa-badge ' + (stMap[c.estado] || 'wa-badge--draft') + '">' + esc(c.estado || 'borrador') + '</span>';
      var n = contacts.filter(function (x) { return c.destinatarios === 'todos' || x.etiqueta === c.destinatarios; }).length;
      c.destinatariosN = n;
      return '<tr onclick="openCampDrawer(' + c._idx + ')">'
        + '<td onclick="event.stopPropagation()"><input type="checkbox" class="wa-camp-check" data-idx="' + c._idx + '" onchange="syncCampDel()" /></td>'
        + '<td><strong>' + esc(c.nombre || '') + '</strong></td>'
        + '<td>' + esc(c.plantilla || '—') + '</td>'
        + '<td>' + n + ' contacto' + (n !== 1 ? 's' : '') + '</td>'
        + '<td>' + esc(c.fecha ? c.fecha.replace('T', ' ') : '—') + '</td>'
        + '<td>' + badge + '</td>'
        + '</tr>';
    }).join('');
    document.getElementById('wa-camp-check-all').checked = false;
    syncCampDel();
    updateStats();
  };
  window.campSortBy = function (col) {
    if (kSort.col === col) { kSort.asc = !kSort.asc; } else { kSort.col = col; kSort.asc = true; }
    renderCampanas();
  };
  window.toggleCampAll = function (v) {
    document.querySelectorAll('.wa-camp-check').forEach(function (cb) { cb.checked = v; });
    syncCampDel();
  };
  window.syncCampDel = function () {
    document.getElementById('wa-camp-del-btn').disabled = !document.querySelectorAll('.wa-camp-check:checked').length;
  };
  window.openCampDrawer = function (idx) {
    editCamp = idx;
    var c = idx >= 0 ? campaigns[idx] : null;
    populateTplSelect();
    document.getElementById('wa-camp-drawer-title').textContent = c ? 'Editar campaña' : 'Nueva campaña';
    document.getElementById('wa-kf-nombre').value    = c ? (c.nombre || '') : '';
    document.getElementById('wa-kf-plantilla').value = c ? (c.plantilla || '') : '';
    document.getElementById('wa-kf-dest').value      = c ? (c.destinatarios || 'todos') : 'todos';
    document.getElementById('wa-kf-fecha').value     = c ? (c.fecha || '') : '';
    document.getElementById('wa-kf-estado').value    = c ? (c.estado || 'borrador') : 'borrador';
    document.getElementById('wa-kf-notas').value     = c ? (c.notas || '') : '';
    document.getElementById('wa-kf-del-btn').style.display = c ? '' : 'none';
    openDrawer('wa-camp-drawer');
  };
  window.saveCamp = function () {
    var nombre = (document.getElementById('wa-kf-nombre').value || '').trim();
    if (!nombre) { showToast('El nombre de la campaña es obligatorio.'); return; }
    var rec = {
      nombre:       nombre,
      plantilla:    document.getElementById('wa-kf-plantilla').value,
      destinatarios:document.getElementById('wa-kf-dest').value,
      fecha:        document.getElementById('wa-kf-fecha').value,
      estado:       document.getElementById('wa-kf-estado').value,
      notas:        document.getElementById('wa-kf-notas').value.trim(),
    };
    if (editCamp >= 0) { campaigns[editCamp] = rec; } else { campaigns.push(rec); }
    saveAll(); closeAllDrawers(); renderCampanas(); showToast(editCamp >= 0 ? 'Campaña actualizada.' : 'Campaña guardada.');
  };

  /* ─── CONFIG ─── */
  function loadConfigForm() {
    document.getElementById('wa-cfg-phone').value      = config.phone || '';
    document.getElementById('wa-cfg-token').value      = config.token || '';
    document.getElementById('wa-cfg-phoneid').value    = config.phoneId || '';
    document.getElementById('wa-cfg-proveedor').value  = config.proveedor || 'meta';
    document.getElementById('wa-cfg-bienvenida').value = config.bienvenida || '';
    document.getElementById('wa-cfg-ausencia').value   = config.ausencia || '';
    document.getElementById('wa-cfg-horario-desde').value = config.desde || '09:00';
    document.getElementById('wa-cfg-horario-hasta').value = config.hasta || '18:00';
  }
  window.saveConfig = function () {
    config.phone     = document.getElementById('wa-cfg-phone').value.trim();
    config.token     = document.getElementById('wa-cfg-token').value.trim();
    config.phoneId   = document.getElementById('wa-cfg-phoneid').value.trim();
    config.proveedor = document.getElementById('wa-cfg-proveedor').value;
    saveAll(); updateStatusBanner(); showToast('Configuración guardada.');
  };
  window.saveAutoConfig = function () {
    config.bienvenida = document.getElementById('wa-cfg-bienvenida').value.trim();
    config.ausencia   = document.getElementById('wa-cfg-ausencia').value.trim();
    config.desde      = document.getElementById('wa-cfg-horario-desde').value;
    config.hasta      = document.getElementById('wa-cfg-horario-hasta').value;
    saveAll(); showToast('Respuestas automáticas guardadas.');
  };

  /* ─── DRAWERS ─── */
  function openDrawer(id) {
    document.querySelectorAll('.wa-drawer').forEach(function (d) { d.classList.remove('is-open'); });
    document.getElementById(id).classList.add('is-open');
    document.getElementById('wa-overlay').classList.add('is-open');
  }
  window.closeAllDrawers = function () {
    document.querySelectorAll('.wa-drawer').forEach(function (d) { d.classList.remove('is-open'); });
    document.getElementById('wa-overlay').classList.remove('is-open');
    editContact = editTpl = editCamp = -1;
  };

  /* ─── CONFIRM ─── */
  window.openConfirm = function (mode) {
    confirmMode = mode;
    var n, label;
    if (mode === 'contact-bulk') {
      n = document.querySelectorAll('.wa-contact-check:checked').length;
      label = n + ' contacto' + (n !== 1 ? 's' : '');
    } else if (mode === 'tpl-bulk') {
      n = document.querySelectorAll('.wa-tpl-check:checked').length;
      label = n + ' plantilla' + (n !== 1 ? 's' : '');
    } else if (mode === 'camp-bulk') {
      n = document.querySelectorAll('.wa-camp-check:checked').length;
      label = n + ' campaña' + (n !== 1 ? 's' : '');
    } else if (mode === 'contact-single') {
      label = editContact >= 0 ? (contacts[editContact].nombre || 'este contacto') : 'este contacto';
    } else if (mode === 'tpl-single') {
      label = editTpl >= 0 ? (templates[editTpl].nombre || 'esta plantilla') : 'esta plantilla';
    } else {
      label = editCamp >= 0 ? (campaigns[editCamp].nombre || 'esta campaña') : 'esta campaña';
    }
    document.getElementById('wa-confirm-title').textContent = '¿Eliminar ' + label + '?';
    document.getElementById('wa-confirm-text').textContent  = 'Esta acción no se puede deshacer.';
    document.getElementById('wa-confirm').classList.add('is-open');
  };
  window.closeConfirm = function () { document.getElementById('wa-confirm').classList.remove('is-open'); };

  document.getElementById('wa-confirm-ok').addEventListener('click', function () {
    closeConfirm();
    function bulkDelete(arr, checkClass, renderFn) {
      var toDelete = [];
      document.querySelectorAll(checkClass + ':checked').forEach(function (cb) { toDelete.push(parseInt(cb.dataset.idx, 10)); });
      toDelete.sort(function (a, b) { return b - a; });
      toDelete.forEach(function (i) { arr.splice(i, 1); });
      saveAll(); renderFn(); showToast('Eliminado.');
    }
    if (confirmMode === 'contact-bulk')  { bulkDelete(contacts,  '.wa-contact-check', renderContacts);   }
    else if (confirmMode === 'tpl-bulk') { bulkDelete(templates, '.wa-tpl-check',     renderPlantillas); }
    else if (confirmMode === 'camp-bulk'){ bulkDelete(campaigns,  '.wa-camp-check',    renderCampanas);   }
    else if (confirmMode === 'contact-single' && editContact >= 0) {
      contacts.splice(editContact, 1); saveAll(); closeAllDrawers(); renderContacts(); showToast('Contacto eliminado.');
    } else if (confirmMode === 'tpl-single' && editTpl >= 0) {
      templates.splice(editTpl, 1); saveAll(); closeAllDrawers(); renderPlantillas(); showToast('Plantilla eliminada.');
    } else if (confirmMode === 'camp-single' && editCamp >= 0) {
      campaigns.splice(editCamp, 1); saveAll(); closeAllDrawers(); renderCampanas(); showToast('Campaña eliminada.');
    }
  });

  /* ─── HELPERS ─── */
  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function today() { return new Date().toISOString().slice(0, 10); }

  /* ─── TOAST ─── */
  function showToast(msg) {
    var t = document.getElementById('wa-toast');
    t.textContent = msg; t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 2800);
  }

  /* ─── INIT ─── */
  load();
  renderContacts();
  renderPlantillas();
  renderCampanas();
  updateStats();
  updateStatusBanner();
})();
</script>
</body>
</html>
"""
