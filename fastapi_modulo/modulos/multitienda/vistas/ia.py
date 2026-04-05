from __future__ import annotations


def ia_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>IA del negocio</title>
  <link rel="stylesheet" href="/multitienda/static/css/ia.css" />
</head>
<body>
<main class="ia-page">

  <!-- Hero -->
  <div class="ia-hero">
    <div class="ia-hero__inner">
      <div class="ia-hero__icon"><i class="fa-solid fa-robot" aria-hidden="true"></i></div>
      <div class="ia-hero__copy">
        <h1>Inteligencia Artificial</h1>
        <p>Activa asistentes de IA para gestión del negocio o ventas directas con tus clientes.</p>
        <div class="ia-hero__badges">
          <span class="ia-hero__badge ia-hero__badge--gestion"><i class="fa-solid fa-chart-line"></i> Gestión</span>
          <span class="ia-hero__badge ia-hero__badge--ventas"><i class="fa-solid fa-comments"></i> Ventas directas</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Stats -->
  <div class="ia-stats">
    <div class="ia-stat">
      <div class="ia-stat__value" id="ia-stat-activos">—</div>
      <div class="ia-stat__label">Asistentes activos</div>
    </div>
    <div class="ia-stat">
      <div class="ia-stat__value" id="ia-stat-conversaciones">—</div>
      <div class="ia-stat__label">Conversaciones hoy</div>
    </div>
    <div class="ia-stat">
      <div class="ia-stat__value" id="ia-stat-resueltos">—</div>
      <div class="ia-stat__label">Resueltos sin humano</div>
    </div>
    <div class="ia-stat">
      <div class="ia-stat__value" id="ia-stat-canales">—</div>
      <div class="ia-stat__label">Canales conectados</div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="ia-tabs">
    <button class="ia-tab is-active" data-tab="asistentes">Asistentes</button>
    <button class="ia-tab" data-tab="conversaciones">Conversaciones</button>
    <button class="ia-tab" data-tab="config">Configuración</button>
  </div>

  <!-- Panel: Asistentes -->
  <div class="ia-tab-panel is-active" id="ia-panel-asistentes">
    <div class="ia-cards" id="ia-cards-container">
      <!-- populated by JS -->
    </div>
  </div>

  <!-- Panel: Conversaciones -->
  <div class="ia-tab-panel" id="ia-panel-conversaciones">
    <div class="ia-table-wrap">
      <table class="ia-table">
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Asistente</th>
            <th>Canal</th>
            <th>Mensajes</th>
            <th>Resuelto</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody id="ia-conv-tbody">
          <tr><td colspan="6" style="text-align:center;padding:32px;color:var(--ia-muted);">Cargando conversaciones…</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Panel: Configuración -->
  <div class="ia-tab-panel" id="ia-panel-config">
    <div class="ia-config-section">
      <h3><i class="fa-solid fa-key" style="margin-right:8px;color:var(--ia-accent)"></i>Proveedor de IA</h3>
      <div class="ia-field">
        <label>Proveedor</label>
        <select id="ia-cfg-provider">
          <option value="">Seleccionar…</option>
          <option value="openai">OpenAI (ChatGPT)</option>
          <option value="anthropic">Anthropic (Claude)</option>
          <option value="gemini">Google Gemini</option>
          <option value="custom">API personalizada</option>
        </select>
      </div>
      <div class="ia-field">
        <label>API Key</label>
        <input type="password" id="ia-cfg-apikey" placeholder="sk-…" autocomplete="off" />
      </div>
      <div class="ia-field" id="ia-cfg-endpoint-wrap" style="display:none">
        <label>Endpoint personalizado</label>
        <input type="url" id="ia-cfg-endpoint" placeholder="https://…" />
      </div>
      <div class="ia-field">
        <label>Modelo preferido</label>
        <input type="text" id="ia-cfg-model" placeholder="Ej. gpt-4o, claude-3-5-sonnet…" />
      </div>
      <button class="ia-save-btn" id="ia-cfg-save-btn">Guardar configuración</button>
    </div>

    <div class="ia-config-section">
      <h3><i class="fa-solid fa-sliders" style="margin-right:8px;color:var(--ia-accent)"></i>Funciones globales</h3>
      <div class="ia-config-row">
        <div>
          <div class="ia-config-row__label">Respuestas automáticas 24/7</div>
          <div class="ia-config-row__hint">El asistente responde fuera de horario sin intervención humana.</div>
        </div>
        <button class="ia-config-toggle" id="ia-cfg-24h"></button>
      </div>
      <div class="ia-config-row">
        <div>
          <div class="ia-config-row__label">Escalado a humano</div>
          <div class="ia-config-row__hint">Derivar a un agente cuando el asistente no sepa responder.</div>
        </div>
        <button class="ia-config-toggle" id="ia-cfg-escalado"></button>
      </div>
      <div class="ia-config-row">
        <div>
          <div class="ia-config-row__label">Historial de conversaciones</div>
          <div class="ia-config-row__hint">Guardar y analizar todas las conversaciones del asistente.</div>
        </div>
        <button class="ia-config-toggle" id="ia-cfg-historial"></button>
      </div>
      <button class="ia-save-btn" id="ia-cfg-global-save-btn">Guardar preferencias</button>
    </div>
  </div>

</main>

<!-- Drawer: Asistente -->
<div class="ia-drawer-bg" id="ia-drawer-bg" role="dialog" aria-modal="true" aria-labelledby="ia-drawer-title">
  <div class="ia-drawer">
    <h2 class="ia-drawer__title" id="ia-drawer-title">Configurar asistente</h2>

    <div class="ia-field--row">
      <div class="ia-field">
        <label>Nombre del asistente *</label>
        <input type="text" id="ia-f-nombre" maxlength="80" placeholder="Ej. Asistente de ventas" />
      </div>
      <div class="ia-field">
        <label>Función</label>
        <select id="ia-f-funcion">
          <option value="gestion">Gestión del negocio</option>
          <option value="ventas">Ventas directas</option>
        </select>
      </div>
    </div>

    <div class="ia-field">
      <label>Canal de atención</label>
      <select id="ia-f-canal">
        <option value="whatsapp">WhatsApp</option>
        <option value="web">Chat web</option>
        <option value="instagram">Instagram DM</option>
        <option value="email">Correo electrónico</option>
        <option value="interno">Uso interno</option>
      </select>
    </div>

    <div class="ia-field">
      <label>Instrucción base (system prompt)</label>
      <textarea id="ia-f-prompt" rows="4" placeholder="Eres un asistente de ventas amigable para…"></textarea>
    </div>

    <div class="ia-field--row">
      <div class="ia-field">
        <label>Tono de comunicación</label>
        <select id="ia-f-tono">
          <option value="formal">Formal</option>
          <option value="amigable">Amigable</option>
          <option value="tecnico">Técnico</option>
        </select>
      </div>
      <div class="ia-field">
        <label>Idioma</label>
        <select id="ia-f-idioma">
          <option value="es">Español</option>
          <option value="en">Inglés</option>
          <option value="es-en">Bilingüe</option>
        </select>
      </div>
    </div>

    <div class="ia-field">
      <label>Temperatura (creatividad 0–1)</label>
      <input type="range" id="ia-f-temperatura" min="0" max="1" step="0.1" value="0.7"
             oninput="document.getElementById('ia-f-temp-val').textContent = this.value" />
      <span id="ia-f-temp-val" style="font-size:0.85rem;color:var(--ia-muted)">0.7</span>
    </div>

    <div class="ia-field">
      <label>Estado</label>
      <select id="ia-f-estado">
        <option value="activo">Activo</option>
        <option value="inactivo">Inactivo</option>
        <option value="config">En configuración</option>
      </select>
    </div>

    <div class="ia-drawer__footer">
      <button class="ia-btn ia-btn--danger" id="ia-delete-btn" style="display:none">Eliminar</button>
      <button class="ia-btn ia-btn--secondary" id="ia-cancel-btn">Cancelar</button>
      <button class="ia-btn ia-btn--primary" id="ia-save-btn">Guardar</button>
    </div>
  </div>
</div>

<script>
(function () {
  const LS_KEY = 'multitienda_ia';
  const LS_CFG = 'multitienda_ia_config';

  // ── Storage helpers ──────────────────────────────────────────────────────
  function loadAsistentes() {
    try { return JSON.parse(localStorage.getItem(LS_KEY) || '[]'); } catch { return []; }
  }
  function saveAsistentes(list) {
    localStorage.setItem(LS_KEY, JSON.stringify(list));
  }
  function loadConfig() {
    try { return JSON.parse(localStorage.getItem(LS_CFG) || '{}'); } catch { return {}; }
  }
  function saveConfig(cfg) {
    localStorage.setItem(LS_CFG, JSON.stringify(cfg));
  }

  // ── DOM refs ─────────────────────────────────────────────────────────────
  const cardsContainer = document.getElementById('ia-cards-container');
  const convTbody      = document.getElementById('ia-conv-tbody');
  const drawerBg       = document.getElementById('ia-drawer-bg');
  const saveBtn        = document.getElementById('ia-save-btn');
  const cancelBtn      = document.getElementById('ia-cancel-btn');
  const deleteBtn      = document.getElementById('ia-delete-btn');

  // form fields
  const fNombre     = document.getElementById('ia-f-nombre');
  const fFuncion    = document.getElementById('ia-f-funcion');
  const fCanal      = document.getElementById('ia-f-canal');
  const fPrompt     = document.getElementById('ia-f-prompt');
  const fTono       = document.getElementById('ia-f-tono');
  const fIdioma     = document.getElementById('ia-f-idioma');
  const fTemperatura = document.getElementById('ia-f-temperatura');
  const fTempVal    = document.getElementById('ia-f-temp-val');
  const fEstado     = document.getElementById('ia-f-estado');

  // config fields
  const cfgProvider   = document.getElementById('ia-cfg-provider');
  const cfgApikey     = document.getElementById('ia-cfg-apikey');
  const cfgEndpointW  = document.getElementById('ia-cfg-endpoint-wrap');
  const cfgEndpoint   = document.getElementById('ia-cfg-endpoint');
  const cfgModel      = document.getElementById('ia-cfg-model');
  const cfgSaveBtn    = document.getElementById('ia-cfg-save-btn');
  const cfgGlobalSave = document.getElementById('ia-cfg-global-save-btn');
  const cfg24h        = document.getElementById('ia-cfg-24h');
  const cfgEscalado   = document.getElementById('ia-cfg-escalado');
  const cfgHistorial  = document.getElementById('ia-cfg-historial');

  let editingId = null;

  // ── Default asistentes ───────────────────────────────────────────────────
  function defaultAsistentes() {
    return [
      { id: 'ast-1', nombre: 'Asistente de ventas', funcion: 'ventas', canal: 'whatsapp', prompt: 'Eres un asistente de ventas amigable que ayuda a los clientes a encontrar productos y realizar pedidos.', tono: 'amigable', idioma: 'es', temperatura: '0.7', estado: 'inactivo' },
      { id: 'ast-2', nombre: 'Gestor de inventario', funcion: 'gestion', canal: 'interno', prompt: 'Eres un asistente interno que responde preguntas sobre stock, pedidos y reportes del negocio.', tono: 'formal', idioma: 'es', temperatura: '0.3', estado: 'inactivo' },
    ];
  }

  // ── Stats ────────────────────────────────────────────────────────────────
  function refreshStats(list) {
    const activos = list.filter(a => a.estado === 'activo').length;
    document.getElementById('ia-stat-activos').textContent = activos;
    const canales = new Set(list.filter(a => a.estado === 'activo').map(a => a.canal)).size;
    document.getElementById('ia-stat-canales').textContent = canales;
    // Conversations & resolved are demo values
    document.getElementById('ia-stat-conversaciones').textContent = 0;
    document.getElementById('ia-stat-resueltos').textContent = '0%';
  }

  // ── Render cards ─────────────────────────────────────────────────────────
  const FUNCION_ICONS = { gestion: 'fa-chart-line', ventas: 'fa-comments', default: 'fa-robot' };
  const STATUS_CSS    = { activo: 'ia-card__status--activo', inactivo: 'ia-card__status--inactivo', config: 'ia-card__status--config' };
  const STATUS_LABEL  = { activo: 'Activo', inactivo: 'Inactivo', config: 'Config' };
  const FUNCION_LABEL = { gestion: 'Gestión', ventas: 'Ventas' };

  function renderCards(list) {
    if (!list.length) {
      cardsContainer.innerHTML = '<div class="ia-empty"><i class="fa-solid fa-robot"></i><p>No hay asistentes configurados.</p></div>';
      return;
    }
    cardsContainer.innerHTML = list.map(a => {
      const icon    = FUNCION_ICONS[a.funcion] || FUNCION_ICONS.default;
      const stCss   = STATUS_CSS[a.estado]  || 'ia-card__status--inactivo';
      const stLabel = STATUS_LABEL[a.estado] || a.estado;
      const isOn    = a.estado === 'activo';
      return `<div class="ia-card${isOn ? ' is-active-config' : ''}" data-id="${a.id}">
        <div class="ia-card__header">
          <div class="ia-card__icon"><i class="fa-solid ${icon}" aria-hidden="true"></i></div>
          <div class="ia-card__info">
            <p class="ia-card__name">${escHtml(a.nombre)}</p>
            <p class="ia-card__desc">${escHtml(FUNCION_LABEL[a.funcion] || a.funcion)} · ${escHtml(a.canal)}</p>
          </div>
        </div>
        <div class="ia-card__footer">
          <span class="ia-card__status ${stCss}">${stLabel}</span>
          <button class="ia-card__toggle${isOn ? ' is-on' : ''}" data-toggle="${a.id}" title="Activar/Desactivar" onclick="event.stopPropagation()"></button>
        </div>
      </div>`;
    }).join('') + `<div class="ia-card" style="border-style:dashed;cursor:pointer;justify-items:center;padding:32px" id="ia-add-card">
      <div class="ia-card__icon"><i class="fa-solid fa-plus" aria-hidden="true"></i></div>
      <div style="font-weight:700;font-size:0.9rem;margin-top:8px">Agregar asistente</div>
    </div>`;
  }

  function escHtml(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── Toggle activo/inactivo ───────────────────────────────────────────────
  cardsContainer.addEventListener('click', function (e) {
    const toggleBtn = e.target.closest('[data-toggle]');
    if (toggleBtn) {
      const id = toggleBtn.dataset.toggle;
      const list = loadAsistentes();
      const idx = list.findIndex(a => a.id === id);
      if (idx < 0) return;
      list[idx].estado = list[idx].estado === 'activo' ? 'inactivo' : 'activo';
      saveAsistentes(list);
      renderCards(list);
      refreshStats(list);
      return;
    }
    const card = e.target.closest('.ia-card[data-id]');
    if (card) {
      openDrawer(card.dataset.id);
    }
    if (e.target.closest('#ia-add-card')) {
      openDrawer(null);
    }
  });

  // ── Drawer ───────────────────────────────────────────────────────────────
  function openDrawer(id) {
    editingId = id;
    const list = loadAsistentes();
    const item = id ? list.find(a => a.id === id) : null;
    fNombre.value      = item ? item.nombre   : '';
    fFuncion.value     = item ? item.funcion  : 'ventas';
    fCanal.value       = item ? item.canal    : 'whatsapp';
    fPrompt.value      = item ? item.prompt   : '';
    fTono.value        = item ? item.tono     : 'amigable';
    fIdioma.value      = item ? item.idioma   : 'es';
    fTemperatura.value = item ? (item.temperatura || '0.7') : '0.7';
    fTempVal.textContent = item ? (item.temperatura || '0.7') : '0.7';
    fEstado.value      = item ? item.estado   : 'inactivo';
    deleteBtn.style.display = id ? 'inline-flex' : 'none';
    drawerBg.classList.add('is-open');
    fNombre.focus();
  }

  function closeDrawer() {
    drawerBg.classList.remove('is-open');
    editingId = null;
  }

  cancelBtn.addEventListener('click', closeDrawer);
  drawerBg.addEventListener('click', e => { if (e.target === drawerBg) closeDrawer(); });

  saveBtn.addEventListener('click', function () {
    const nombre = fNombre.value.trim();
    if (!nombre) { fNombre.focus(); return; }
    const list = loadAsistentes();
    const item = {
      id: editingId || ('ast-' + Date.now()),
      nombre,
      funcion:     fFuncion.value,
      canal:       fCanal.value,
      prompt:      fPrompt.value.trim(),
      tono:        fTono.value,
      idioma:      fIdioma.value,
      temperatura: fTemperatura.value,
      estado:      fEstado.value,
    };
    if (editingId) {
      const idx = list.findIndex(a => a.id === editingId);
      if (idx >= 0) list[idx] = item;
    } else {
      list.push(item);
    }
    saveAsistentes(list);
    renderCards(list);
    refreshStats(list);
    closeDrawer();
  });

  deleteBtn.addEventListener('click', function () {
    if (!editingId) return;
    const list = loadAsistentes().filter(a => a.id !== editingId);
    saveAsistentes(list);
    renderCards(list);
    refreshStats(list);
    closeDrawer();
  });

  // ── Conversations (demo) ─────────────────────────────────────────────────
  function renderConversaciones() {
    convTbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--ia-muted);font-size:0.88rem;">No hay conversaciones registradas aún.</td></tr>';
  }

  // ── Config panel ─────────────────────────────────────────────────────────
  function loadConfigPanel() {
    const cfg = loadConfig();
    if (cfgProvider)   cfgProvider.value   = cfg.provider  || '';
    if (cfgApikey)     cfgApikey.value     = cfg.apikey    || '';
    if (cfgEndpoint)   cfgEndpoint.value   = cfg.endpoint  || '';
    if (cfgModel)      cfgModel.value      = cfg.model     || '';
    toggleEndpointField();
    setToggle(cfg24h,        cfg.auto24h    !== false);
    setToggle(cfgEscalado,   cfg.escalado   !== false);
    setToggle(cfgHistorial,  cfg.historial  !== false);
  }

  function setToggle(btn, on) {
    if (!btn) return;
    btn.classList.toggle('is-on', !!on);
  }

  function toggleEndpointField() {
    if (!cfgEndpointW) return;
    cfgEndpointW.style.display = (cfgProvider && cfgProvider.value === 'custom') ? 'block' : 'none';
  }

  cfgProvider && cfgProvider.addEventListener('change', toggleEndpointField);

  [cfg24h, cfgEscalado, cfgHistorial].forEach(btn => {
    btn && btn.addEventListener('click', () => btn.classList.toggle('is-on'));
  });

  cfgSaveBtn && cfgSaveBtn.addEventListener('click', function () {
    const cfg = loadConfig();
    cfg.provider = cfgProvider ? cfgProvider.value : cfg.provider;
    cfg.apikey   = cfgApikey   ? cfgApikey.value   : cfg.apikey;
    cfg.endpoint = cfgEndpoint ? cfgEndpoint.value : cfg.endpoint;
    cfg.model    = cfgModel    ? cfgModel.value    : cfg.model;
    saveConfig(cfg);
    cfgSaveBtn.textContent = '¡Guardado!';
    setTimeout(() => { cfgSaveBtn.textContent = 'Guardar configuración'; }, 2000);
  });

  cfgGlobalSave && cfgGlobalSave.addEventListener('click', function () {
    const cfg = loadConfig();
    cfg.auto24h   = cfg24h      ? cfg24h.classList.contains('is-on')      : cfg.auto24h;
    cfg.escalado  = cfgEscalado ? cfgEscalado.classList.contains('is-on') : cfg.escalado;
    cfg.historial = cfgHistorial? cfgHistorial.classList.contains('is-on'): cfg.historial;
    saveConfig(cfg);
    cfgGlobalSave.textContent = '¡Guardado!';
    setTimeout(() => { cfgGlobalSave.textContent = 'Guardar preferencias'; }, 2000);
  });

  // ── Tabs ─────────────────────────────────────────────────────────────────
  document.querySelectorAll('.ia-tab').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.ia-tab').forEach(b => b.classList.remove('is-active'));
      document.querySelectorAll('.ia-tab-panel').forEach(p => p.classList.remove('is-active'));
      btn.classList.add('is-active');
      const panel = document.getElementById('ia-panel-' + btn.dataset.tab);
      if (panel) panel.classList.add('is-active');
      if (btn.dataset.tab === 'conversaciones') renderConversaciones();
    });
  });

  // ── Init ─────────────────────────────────────────────────────────────────
  let list = loadAsistentes();
  if (!list.length) {
    list = defaultAsistentes();
    saveAsistentes(list);
  }
  renderCards(list);
  refreshStats(list);
  loadConfigPanel();
})();
</script>
</body>
</html>"""
