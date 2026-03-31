from __future__ import annotations


def inicio_html() -> str:
    return _HTML


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Inicio — Multitienda</title>
  <style>
    :root {
      --db-bg: var(--page-bg, #f4f6fb);
      --db-surface: var(--content-bg, #ffffff);
      --db-border: var(--field-border, #d1d5db);
      --db-text: var(--body-text, #1f2937);
      --db-muted: color-mix(in srgb, var(--body-text, #1f2937) 60%, #ffffff 40%);
      --db-accent: var(--button-bg, #1a6b3c);
      --db-accent-fg: var(--button-text, #ffffff);
    }

    html, body {
      margin: 0;
      padding: 0;
      background: var(--db-bg);
      font-family: system-ui, Arial, sans-serif;
      color: var(--db-text);
    }

    * { box-sizing: border-box; }

    /* ── Welcome banner ── */
    .db-welcome {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 20px 24px;
      border-radius: 18px;
      background: linear-gradient(135deg,
        color-mix(in srgb, var(--db-accent) 14%, var(--db-surface)) 0%,
        var(--db-surface) 100%);
      border: 1px solid color-mix(in srgb, var(--db-border) 70%, transparent);
      margin-bottom: 20px;
    }

    .db-welcome__avatar {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: color-mix(in srgb, var(--db-accent) 18%, var(--db-surface));
      border: 2px solid color-mix(in srgb, var(--db-accent) 30%, transparent);
      display: grid;
      place-items: center;
      flex-shrink: 0;
      font-size: 1.5rem;
      color: var(--db-accent);
    }

    .db-welcome__copy { min-width: 0; }
    .db-welcome__copy h2 {
      margin: 0 0 4px;
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--db-text);
    }
    .db-welcome__copy p {
      margin: 0;
      font-size: 0.85rem;
      color: var(--db-muted);
    }

    /* ── Stats row ── */
    .db-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 14px;
      margin-bottom: 20px;
    }

    .db-stat {
      background: var(--db-surface);
      border: 1px solid var(--db-border);
      border-radius: 16px;
      padding: 16px 18px;
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .db-stat__icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: grid;
      place-items: center;
      font-size: 1.1rem;
      flex-shrink: 0;
    }

    .db-stat__icon--blue   { background: #dbeafe; color: #1d4ed8; }
    .db-stat__icon--green  { background: #dcfce7; color: #15803d; }
    .db-stat__icon--amber  { background: #fef9c3; color: #b45309; }
    .db-stat__icon--violet { background: #ede9fe; color: #7c3aed; }

    .db-stat__body { min-width: 0; }
    .db-stat__value {
      font-size: 1.55rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1;
      color: var(--db-text);
    }
    .db-stat__label {
      font-size: 0.78rem;
      color: var(--db-muted);
      margin-top: 3px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* ── Two-column grid ── */
    .db-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
      gap: 16px;
      margin-bottom: 20px;
    }

    .db-card {
      background: var(--db-surface);
      border: 1px solid var(--db-border);
      border-radius: 16px;
      overflow: hidden;
    }

    .db-card__head {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 18px;
      border-bottom: 1px solid var(--db-border);
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--db-text);
    }

    .db-card__head i {
      font-size: 0.9rem;
      color: var(--db-muted);
    }

    .db-card__body { padding: 18px; }

    /* ── Chart canvas ── */
    .db-chart-wrap {
      position: relative;
      height: 200px;
    }

    /* ── Product stats bars ── */
    .db-bars {
      display: grid;
      gap: 12px;
    }

    .db-bar-item { display: grid; gap: 4px; }
    .db-bar-label {
      display: flex;
      justify-content: space-between;
      font-size: 0.82rem;
      color: var(--db-muted);
    }
    .db-bar-track {
      height: 8px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--db-border) 80%, transparent);
      overflow: hidden;
    }
    .db-bar-fill {
      height: 100%;
      border-radius: 999px;
      transition: width 0.6s ease;
    }
    .db-bar-fill--blue   { background: #3b82f6; }
    .db-bar-fill--green  { background: #22c55e; }
    .db-bar-fill--amber  { background: #f59e0b; }

    /* ── Bottom row ── */
    .db-bottom {
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
      gap: 16px;
    }

    /* ── Notifications ── */
    .db-notif-list { list-style: none; margin: 0; padding: 0; }
    .db-notif-item {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 10px 0;
      border-bottom: 1px solid color-mix(in srgb, var(--db-border) 60%, transparent);
      font-size: 0.85rem;
    }
    .db-notif-item:last-child { border-bottom: none; }
    .db-notif-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin-top: 5px;
      flex-shrink: 0;
      background: #3b82f6;
    }
    .db-notif-dot--green { background: #22c55e; }
    .db-notif-dot--amber { background: #f59e0b; }
    .db-notif-text { color: var(--db-text); line-height: 1.45; }
    .db-notif-when { color: var(--db-muted); font-size: 0.78rem; }

    /* ── Quick actions ── */
    .db-actions { display: grid; gap: 10px; }
    .db-action-btn {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid var(--db-border);
      background: color-mix(in srgb, var(--db-surface) 95%, var(--db-bg) 5%);
      color: var(--db-text);
      text-decoration: none;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
    }
    .db-action-btn:hover {
      background: color-mix(in srgb, var(--db-accent) 8%, var(--db-surface));
      border-color: color-mix(in srgb, var(--db-accent) 40%, transparent);
      transform: translateY(-1px);
    }
    .db-action-btn i {
      width: 32px;
      height: 32px;
      border-radius: 10px;
      display: grid;
      place-items: center;
      font-size: 0.9rem;
      flex-shrink: 0;
      background: color-mix(in srgb, var(--db-accent) 12%, var(--db-surface));
      color: var(--db-accent);
    }

    /* ── Empty state ── */
    .db-empty {
      text-align: center;
      padding: 28px 16px;
      color: var(--db-muted);
      font-size: 0.88rem;
    }

    @media (max-width: 900px) {
      .db-grid, .db-bottom {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
<main id="db-root">

  <!-- Welcome -->
  <div class="db-welcome">
    <div class="db-welcome__avatar"><i class="fa-regular fa-user"></i></div>
    <div class="db-welcome__copy">
      <h2>Bienvenido, <span id="db-username">...</span></h2>
      <p><i class="fa-regular fa-clock" style="margin-right:4px"></i>Último acceso: <span id="db-last-access">—</span></p>
    </div>
  </div>

  <!-- Stats -->
  <div class="db-stats">
    <div class="db-stat">
      <div class="db-stat__icon db-stat__icon--blue"><i class="fa-solid fa-store"></i></div>
      <div class="db-stat__body">
        <div class="db-stat__value" id="db-stat-stores">0</div>
        <div class="db-stat__label">Tiendas activas</div>
      </div>
    </div>
    <div class="db-stat">
      <div class="db-stat__icon db-stat__icon--green"><i class="fa-solid fa-box"></i></div>
      <div class="db-stat__body">
        <div class="db-stat__value" id="db-stat-products">0</div>
        <div class="db-stat__label">Productos publicados</div>
      </div>
    </div>
    <div class="db-stat">
      <div class="db-stat__icon db-stat__icon--amber"><i class="fa-solid fa-id-card"></i></div>
      <div class="db-stat__body">
        <div class="db-stat__value" id="db-stat-membership" style="font-size:1rem">—</div>
        <div class="db-stat__label">Membresía</div>
      </div>
    </div>
    <div class="db-stat">
      <div class="db-stat__icon db-stat__icon--violet"><i class="fa-solid fa-warehouse"></i></div>
      <div class="db-stat__body">
        <div class="db-stat__value" id="db-stat-inventory" style="font-size:1rem">—</div>
        <div class="db-stat__label">Inventario</div>
      </div>
    </div>
  </div>

  <!-- Main grid -->
  <div class="db-grid">
    <!-- Analítica de tienda -->
    <div class="db-card">
      <div class="db-card__head">
        <i class="fa-solid fa-chart-line"></i> Analítica de tienda
      </div>
      <div class="db-card__body">
        <div class="db-chart-wrap">
          <canvas id="db-analytics-chart"></canvas>
        </div>
      </div>
    </div>

    <!-- Estadísticas de productos -->
    <div class="db-card">
      <div class="db-card__head">
        <i class="fa-solid fa-chart-bar"></i> Estado de productos
      </div>
      <div class="db-card__body">
        <div class="db-bars">
          <div class="db-bar-item">
            <div class="db-bar-label">
              <span>Publicados</span>
              <span id="db-bar-online-count">0</span>
            </div>
            <div class="db-bar-track">
              <div class="db-bar-fill db-bar-fill--green" id="db-bar-online" style="width:0%"></div>
            </div>
          </div>
          <div class="db-bar-item">
            <div class="db-bar-label">
              <span>Pendientes</span>
              <span id="db-bar-pending-count">0</span>
            </div>
            <div class="db-bar-track">
              <div class="db-bar-fill db-bar-fill--amber" id="db-bar-pending" style="width:0%"></div>
            </div>
          </div>
          <div class="db-bar-item">
            <div class="db-bar-label">
              <span>Borradores</span>
              <span id="db-bar-draft-count">0</span>
            </div>
            <div class="db-bar-track">
              <div class="db-bar-fill db-bar-fill--blue" id="db-bar-draft" style="width:0%"></div>
            </div>
          </div>
        </div>
        <!-- Tiendas con mapa simplificado -->
        <div style="margin-top:20px">
          <div class="db-card__head" style="padding:0 0 10px; border:none; font-size:0.82rem">
            <i class="fa-solid fa-building-user"></i> Tiendas registradas
          </div>
          <div id="db-store-list" style="display:grid;gap:6px;font-size:0.82rem">
            <div class="db-empty">Cargando tiendas…</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Bottom grid -->
  <div class="db-bottom">
    <!-- Notificaciones -->
    <div class="db-card">
      <div class="db-card__head">
        <i class="fa-solid fa-bell"></i> Actividad reciente
      </div>
      <div class="db-card__body">
        <ul class="db-notif-list" id="db-notif-list">
          <li class="db-empty">Sin actividad registrada.</li>
        </ul>
      </div>
    </div>

    <!-- Accesos rápidos -->
    <div class="db-card">
      <div class="db-card__head">
        <i class="fa-solid fa-bolt"></i> Accesos rápidos
      </div>
      <div class="db-card__body">
        <div class="db-actions">
          <a class="db-action-btn" href="/multitienda/productos">
            <i class="fa-solid fa-box"></i>
            <span>Gestionar productos</span>
          </a>
          <a class="db-action-btn" href="/multitienda/configuracion">
            <i class="fa-solid fa-gear"></i>
            <span>Configurar tienda</span>
          </a>
          <a class="db-action-btn" href="/multitienda/administracion_tiendas" id="db-link-gestion" style="display:none">
            <i class="fa-solid fa-store"></i>
            <span>Administrar tiendas</span>
          </a>
          <a class="db-action-btn" href="/tiendas" target="_blank">
            <i class="fa-solid fa-arrow-up-right-from-square"></i>
            <span>Ver marketplace público</span>
          </a>
        </div>
      </div>
    </div>
  </div>

</main>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<script>
(function () {
  'use strict';

  /* ── helpers ── */
  function setText(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = String(val);
  }

  function setWidth(id, pct) {
    var el = document.getElementById(id);
    if (el) el.style.width = Math.min(100, Math.max(0, pct)) + '%';
  }

  /* ── username + last access ── */
  var username = (
    document.cookie.split(';').map(function(c){ return c.trim(); })
      .filter(function(c){ return c.startsWith('user_name=') || c.startsWith('usuario='); })
      .map(function(c){ return decodeURIComponent(c.split('=')[1] || ''); })[0]
    || 'Usuario'
  );
  setText('db-username', username);

  var now = new Date();
  try {
    setText('db-last-access', new Intl.DateTimeFormat('es-MX', {
      dateStyle: 'medium', timeStyle: 'short'
    }).format(now));
  } catch(e) {
    setText('db-last-access', now.toLocaleString());
  }

  /* ── local product count ── */
  var localProducts = 0;
  try {
    var raw = JSON.parse(window.localStorage.getItem('multitienda_productos') || '[]');
    localProducts = Array.isArray(raw) ? raw.length : 0;
  } catch(e) {}
  setText('db-stat-products', localProducts);

  /* ── analítica chart (últimos 7 días simulados hasta que haya endpoint real) ── */
  function buildAnalyticsChart(values) {
    var canvas = document.getElementById('db-analytics-chart');
    if (!canvas || typeof Chart === 'undefined') return;
    var labels = [];
    for (var i = 6; i >= 0; i--) {
      var d = new Date(now);
      d.setDate(d.getDate() - i);
      labels.push(new Intl.DateTimeFormat('es-MX', { month: 'short', day: 'numeric' }).format(d));
    }
    var accent = getComputedStyle(document.documentElement)
      .getPropertyValue('--button-bg').trim() || '#1a6b3c';
    new Chart(canvas, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Visitas',
          data: values,
          borderColor: accent,
          backgroundColor: accent.replace(')', ', 0.12)').replace('rgb', 'rgba').replace('#', 'rgba(').replace(/rgba\(([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2}), 0.12\)/, function(m,r,g,b){ return 'rgba('+parseInt(r,16)+','+parseInt(g,16)+','+parseInt(b,16)+',0.12)'; }),
          tension: 0.38,
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: true,
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 11 } } },
          y: { beginAtZero: true, ticks: { precision: 0, font: { size: 11 } }, grid: { color: 'rgba(0,0,0,0.05)' } }
        }
      }
    });
  }

  /* placeholder data — replace with real API when available */
  buildAnalyticsChart([0, 0, 0, 0, 0, 0, 0]);

  /* ── stores ── */
  fetch('/multitienda/api/stores', { headers: { 'Accept': 'application/json' } })
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(payload) {
      var stores = payload && Array.isArray(payload.data) ? payload.data : [];

      setText('db-stat-stores', stores.length);

      if (!stores.length) {
        setText('db-stat-membership', 'Sin membresía');
        setText('db-stat-inventory', 'No configurado');
        var storeList = document.getElementById('db-store-list');
        if (storeList) storeList.innerHTML = '<div class="db-empty">Sin tiendas registradas.</div>';
        buildNotifications([]);
        return;
      }

      var first = stores[0];
      setText('db-stat-membership', first.membership || 'Sin membresía');
      setText('db-stat-inventory', first.inventoryEnabled ? 'Activo' : 'No activo');

      /* bar chart: use total products from local + spread among states */
      var total = localProducts || stores.length;
      var online  = stores.filter(function(s){ return s.isActive; }).length;
      var pending = Math.max(0, total - online);
      var draft   = 0;
      var maxVal  = Math.max(1, online + pending + draft);

      setText('db-bar-online-count', online);
      setText('db-bar-pending-count', pending);
      setText('db-bar-draft-count', draft);
      setWidth('db-bar-online',  (online / maxVal) * 100);
      setWidth('db-bar-pending', (pending / maxVal) * 100);
      setWidth('db-bar-draft',   (draft   / maxVal) * 100);

      /* store list */
      var storeList = document.getElementById('db-store-list');
      if (storeList) {
        storeList.innerHTML = stores.slice(0, 5).map(function(s) {
          return '<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(0,0,0,0.06)">' +
            '<span style="width:8px;height:8px;border-radius:50%;flex-shrink:0;background:' + (s.isActive ? '#22c55e' : '#f59e0b') + '"></span>' +
            '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + (s.name || s.slug || 'Tienda') + '</span>' +
            '<span style="font-size:0.75rem;color:var(--db-muted)">' + (s.isActive ? 'Activa' : 'Inactiva') + '</span>' +
            '</div>';
        }).join('');
      }

      buildNotifications(stores);
    })
    .catch(function() {
      setText('db-stat-stores', '0');
      setText('db-stat-membership', 'Error');
      setText('db-stat-inventory', 'Error');
      buildNotifications([]);
    });

  function buildNotifications(stores) {
    var list = document.getElementById('db-notif-list');
    if (!list) return;
    var items = [];
    stores.slice(0, 3).forEach(function(s) {
      items.push({
        color: s.isActive ? 'green' : 'amber',
        text: 'Tienda <strong>' + (s.name || s.slug) + '</strong> está ' + (s.isActive ? 'activa' : 'pendiente de activación') + '.',
        when: 'Hoy'
      });
    });
    if (!items.length) {
      list.innerHTML = '<li class="db-empty">Sin actividad reciente.</li>';
      return;
    }
    list.innerHTML = items.map(function(item) {
      return '<li class="db-notif-item">' +
        '<span class="db-notif-dot db-notif-dot--' + item.color + '"></span>' +
        '<div><div class="db-notif-text">' + item.text + '</div>' +
        '<div class="db-notif-when">' + item.when + '</div></div>' +
        '</li>';
    }).join('');
  }

  /* ── mostrar enlace gestion solo a superadmin ── */
  try {
    var roleMeta = document.querySelector('meta[name="user-role"]');
    var roleName = roleMeta ? roleMeta.content : '';
    if (/superadmin/i.test(roleName)) {
      var linkGestion = document.getElementById('db-link-gestion');
      if (linkGestion) linkGestion.style.display = '';
    }
  } catch(e) {}

  /* fallback: show gestion link based on localStorage flag set by sipet auth */
  try {
    var storedRole = window.localStorage.getItem('sipet_user_role') || '';
    if (/superadmin/i.test(storedRole)) {
      var lg = document.getElementById('db-link-gestion');
      if (lg) lg.style.display = '';
    }
  } catch(e) {}

})();
</script>
</body>
</html>
"""
