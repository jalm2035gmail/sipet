from __future__ import annotations


def ia_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>IA del negocio</title>
  <style>
    :root {
      --ia-accent: #6d28d9;
      --ia-accent2: #4f46e5;
      --ia-bg: var(--page-bg, #f5f6f8);
      --ia-surface: var(--content-bg, #ffffff);
      --ia-border: var(--field-border, #d1d5db);
      --ia-text: var(--body-text, #1f2937);
      --ia-muted: color-mix(in srgb, var(--body-text, #1f2937) 60%, #ffffff 40%);
      --ia-focus: #6d28d9;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: var(--ia-bg); font-family: Arial, sans-serif; color: var(--ia-text); }

    .ia-page { padding: 0 0 40px; }

    /* Hero */
    .ia-hero {
      background: linear-gradient(135deg, #1e0a3c 0%, #2d1264 50%, #1e3a5f 100%);
      border-radius: 20px;
      padding: 32px 32px 28px;
      margin-bottom: 28px;
      position: relative;
      overflow: hidden;
    }
    .ia-hero::before {
      content: "";
      position: absolute;
      inset: 0;
      background: radial-gradient(ellipse 60% 60% at 80% 20%, rgba(109,40,217,0.35) 0%, transparent 70%),
                  radial-gradient(ellipse 40% 50% at 20% 80%, rgba(79,70,229,0.25) 0%, transparent 70%);
      pointer-events: none;
    }
    .ia-hero__inner { position: relative; z-index: 1; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
    .ia-hero__icon {
      width: 64px; height: 64px; border-radius: 20px; flex-shrink: 0;
      background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
      display: grid; place-items: center; font-size: 1.6rem; color: #fff;
      box-shadow: 0 8px 24px rgba(109,40,217,0.45);
    }
    .ia-hero__copy { flex: 1; min-width: 200px; }
    .ia-hero__copy h1 { margin: 0 0 6px; font-size: 1.55rem; font-weight: 800; color: #fff; letter-spacing: -0.02em; }
    .ia-hero__copy p { margin: 0; color: rgba(255,255,255,0.72); font-size: 0.92rem; line-height: 1.5; }
    .ia-hero__badges { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 18px; }
    .ia-hero__badge {
      padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
      letter-spacing: 0.04em; text-transform: uppercase;
    }
    .ia-hero__badge--gestion { background: rgba(109,40,217,0.35); color: #c4b5fd; border: 1px solid rgba(196,181,253,0.25); }
    .ia-hero__badge--ventas  { background: rgba(79,70,229,0.35);  color: #a5b4fc; border: 1px solid rgba(165,180,252,0.25); }

    /* Stats */
    .ia-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }
    .ia-stat {
      background: var(--ia-surface);
      border: 1px solid var(--ia-border);
      border-radius: 16px;
      padding: 18px 20px;
    }
    .ia-stat__value { font-size: 1.75rem; font-weight: 800; color: var(--ia-accent); line-height: 1; margin-bottom: 4px; }
    .ia-stat__label { font-size: 0.8rem; color: var(--ia-muted); font-weight: 600; }

    /* Tabs */
    .ia-tabs { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
    .ia-tab {
      padding: 8px 18px; border-radius: 12px; font-size: 0.88rem; font-weight: 700;
      cursor: pointer; border: none; background: var(--ia-surface);
      border: 1px solid var(--ia-border); color: var(--ia-muted); transition: all 0.16s;
    }
    .ia-tab.is-active { background: var(--ia-accent); color: #fff; border-color: var(--ia-accent); }
    .ia-tab-panel { display: none; }
    .ia-tab-panel.is-active { display: block; }

    /* Card grid */
    .ia-cards {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 18px;
    }
    .ia-card {
      background: var(--ia-surface);
      border: 1px solid var(--ia-border);
      border-radius: 18px;
      padding: 22px 22px 18px;
      display: grid;
      gap: 10px;
      transition: box-shadow 0.16s, transform 0.16s;
      cursor: pointer;
    }
    .ia-card:hover { box-shadow: 0 8px 24px rgba(109,40,217,0.12); transform: translateY(-2px); }
    .ia-card.is-active-config { border-color: var(--ia-accent); box-shadow: 0 0 0 2px rgba(109,40,217,0.2); }
    .ia-card__header { display: flex; align-items: flex-start; gap: 14px; }
    .ia-card__icon {
      width: 44px; height: 44px; border-radius: 14px; flex-shrink: 0;
      background: linear-gradient(135deg, rgba(109,40,217,0.15) 0%, rgba(79,70,229,0.15) 100%);
      display: grid; place-items: center; font-size: 1.1rem; color: var(--ia-accent);
    }
    .ia-card__info { flex: 1; min-width: 0; }
    .ia-card__name { font-size: 1rem; font-weight: 800; margin: 0 0 3px; }
    .ia-card__desc { font-size: 0.82rem; color: var(--ia-muted); margin: 0; line-height: 1.4; }
    .ia-card__footer { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
    .ia-card__status {
      padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.06em;
    }
    .ia-card__status--activo    { background: #dcfce7; color: #166534; }
    .ia-card__status--inactivo  { background: #f3f4f6; color: #6b7280; }
    .ia-card__status--config    { background: #ede9fe; color: #5b21b6; }
    .ia-card__toggle {
      position: relative; width: 44px; height: 24px; border-radius: 12px;
      background: #e5e7eb; border: none; cursor: pointer; transition: background 0.2s;
      flex-shrink: 0;
    }
    .ia-card__toggle::after {
      content: ""; position: absolute; top: 3px; left: 3px;
      width: 18px; height: 18px; border-radius: 50%; background: #fff;
      transition: transform 0.2s; box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    }
    .ia-card__toggle.is-on { background: var(--ia-accent); }
    .ia-card__toggle.is-on::after { transform: translateX(20px); }

    /* Conversations table */
    .ia-table-wrap { overflow-x: auto; border-radius: 14px; border: 1px solid var(--ia-border); }
    .ia-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    .ia-table thead tr { background: color-mix(in srgb, var(--ia-surface) 85%, var(--ia-bg) 15%); }
    .ia-table th { padding: 12px 14px; text-align: left; font-size: 0.75rem; font-weight: 700; color: var(--ia-muted); text-transform: uppercase; letter-spacing: 0.08em; white-space: nowrap; }
    .ia-table td { padding: 12px 14px; border-top: 1px solid var(--ia-border); vertical-align: middle; }
    .ia-table tbody tr:hover { background: color-mix(in srgb, var(--ia-accent) 4%, var(--ia-surface) 96%); }
    .ia-chip {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 3px 10px; border-radius: 10px; font-size: 0.75rem; font-weight: 700;
    }
    .ia-chip--gestion { background: rgba(109,40,217,0.12); color: #5b21b6; }
    .ia-chip--ventas  { background: rgba(79,70,229,0.12);  color: #3730a3; }
    .ia-chip--canal   { background: rgba(16,185,129,0.12); color: #065f46; }

    /* Drawer */
    .ia-drawer-bg {
      display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4);
      z-index: 1040; align-items: flex-end;
    }
    .ia-drawer-bg.is-open { display: flex; }
    .ia-drawer {
      background: var(--ia-surface); border-radius: 24px 24px 0 0; width: 100%;
      max-width: 640px; margin: 0 auto; padding: 28px 28px 32px;
      max-height: 90vh; overflow-y: auto;
    }
    .ia-drawer__title { font-size: 1.2rem; font-weight: 800; margin: 0 0 20px; }
    .ia-field { margin-bottom: 16px; }
    .ia-field label { display: block; font-size: 0.8rem; font-weight: 700; margin-bottom: 5px; color: var(--ia-muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .ia-field input, .ia-field select, .ia-field textarea {
      width: 100%; padding: 10px 12px; border-radius: 10px;
      border: 1.5px solid var(--ia-border); font-size: 0.95rem;
      background: var(--ia-surface); color: var(--ia-text);
      outline: none; transition: border-color 0.15s;
    }
    .ia-field input:focus, .ia-field select:focus, .ia-field textarea:focus { border-color: var(--ia-focus); }
    .ia-field textarea { resize: vertical; min-height: 80px; }
    .ia-field--row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .ia-drawer__footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--ia-border); }
    .ia-btn {
      padding: 10px 22px; border-radius: 12px; font-size: 0.9rem; font-weight: 700;
      cursor: pointer; border: none; transition: opacity 0.15s;
    }
    .ia-btn:hover { opacity: 0.88; }
    .ia-btn--primary { background: var(--ia-accent); color: #fff; }
    .ia-btn--secondary { background: var(--ia-surface); color: var(--ia-muted); border: 1.5px solid var(--ia-border); }
    .ia-btn--danger { background: #fee2e2; color: #dc2626; }

    /* Empty state */
    .ia-empty { text-align: center; padding: 56px 24px; color: var(--ia-muted); }
    .ia-empty i { font-size: 2.5rem; margin-bottom: 12px; opacity: 0.4; color: var(--ia-accent); }
    .ia-empty p { margin: 0; font-size: 0.9rem; }

    /* Config section */
    .ia-config-section {
      background: var(--ia-surface);
      border: 1px solid var(--ia-border);
      border-radius: 18px;
      padding: 24px;
      margin-bottom: 18px;
    }
    .ia-config-section h3 { margin: 0 0 16px; font-size: 1rem; font-weight: 800; }
    .ia-config-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--ia-border); }
    .ia-config-row:last-child { border-bottom: none; }
    .ia-config-row__label { font-size: 0.9rem; font-weight: 600; }
    .ia-config-row__hint  { font-size: 0.78rem; color: var(--ia-muted); margin-top: 2px; }
    .ia-config-toggle {
      position: relative; width: 48px; height: 26px; border-radius: 13px;
      background: #e5e7eb; border: none; cursor: pointer; transition: background 0.2s; flex-shrink: 0;
    }
    .ia-config-toggle::after {
      content: ""; position: absolute; top: 3px; left: 3px;
      width: 20px; height: 20px; border-radius: 50%; background: #fff;
      transition: transform 0.2s; box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    }
    .ia-config-toggle.is-on { background: var(--ia-accent); }
    .ia-config-toggle.is-on::after { transform: translateX(22px); }
    .ia-save-btn {
      margin-top: 16px; padding: 10px 24px; border-radius: 12px;
      background: var(--ia-accent); color: #fff; font-weight: 700;
      border: none; cursor: pointer; font-size: 0.9rem; transition: opacity 0.15s;
    }
    .ia-save-btn:hover { opacity: 0.88; }

    @media (max-width: 640px) {
      .ia-hero { padding: 22px 18px 18px; }
      .ia-hero__copy h1 { font-size: 1.25rem; }
      .ia-card__name { font-size: 0.92rem; }
      .ia-field--row { grid-template-columns: 1fr; }
    }
  </style>
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
