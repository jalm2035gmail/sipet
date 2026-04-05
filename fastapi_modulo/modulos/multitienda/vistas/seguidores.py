from __future__ import annotations

from html import escape


def _js_bool(value: bool) -> str:
    return "true" if value else "false"


def seguidores_html(
    max_users: int = 0,
    intelicoop_enabled: bool = False,
    intelicoop_route: str = "",
    intelicoop_api_base: str = "",
) -> str:
    return (
        _HTML
        .replace("__MAX_USERS__", escape(str(max_users)))
        .replace("__INTELICOOP_ENABLED__", _js_bool(intelicoop_enabled))
        .replace("__INTELICOOP_ROUTE__", escape(intelicoop_route or "#"))
        .replace("__INTELICOOP_API_BASE__", escape(intelicoop_api_base or ""))
        .replace("__INTELICOOP_BANNER__", _build_intelicoop_banner(intelicoop_enabled, intelicoop_route))
    )


def _build_intelicoop_banner(intelicoop_enabled: bool, intelicoop_route: str) -> str:
    if intelicoop_enabled and intelicoop_route:
        return (
            '<div class="sg-intel-banner">'
            '<i class="fa-solid fa-circle-nodes"></i>'
            '<span>Los seguidores se sincronizan con <a href="{route}" target="_blank">Intelicoop</a> como socios.</span>'
            "</div>"
        ).format(route=escape(intelicoop_route))
    return (
        '<div class="sg-intel-banner sg-intel-banner--disabled">'
        '<i class="fa-solid fa-plug-circle-xmark"></i>'
        "<span>Intelicoop no está habilitado. Esta vista permanece operativa sin sincronización financiera.</span>"
        "</div>"
    )


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Seguidores — Multitienda</title>
  <link rel="stylesheet" href="/multitienda/static/css/seguidores.css" />
</head>
<body>
<main>

  <!-- Capacity bar -->
  <div class="sg-capacity">
    <div class="sg-capacity__icon"><i class="fa-solid fa-user-group"></i></div>
    <div class="sg-capacity__info">
      <div class="sg-capacity__title">Capacidad de seguidores</div>
      <div class="sg-capacity__bar-wrap">
        <div class="sg-capacity__bar" id="sg-cap-bar" style="width:0%"></div>
      </div>
      <div class="sg-capacity__numbers" id="sg-cap-numbers">Cargando…</div>
    </div>
    <div class="sg-capacity__tag" id="sg-cap-tag">0 / __MAX_USERS__</div>
  </div>

  <!-- Stats -->
  <div class="sg-stats">
    <div class="sg-stat">
      <div class="sg-stat__icon sg-stat__icon--purple"><i class="fa-solid fa-users"></i></div>
      <div><div class="sg-stat__value" id="sg-stat-total">0</div><div class="sg-stat__label">Total seguidores</div></div>
    </div>
    <div class="sg-stat">
      <div class="sg-stat__icon sg-stat__icon--green"><i class="fa-solid fa-circle-check"></i></div>
      <div><div class="sg-stat__value" id="sg-stat-activos">0</div><div class="sg-stat__label">Activos</div></div>
    </div>
    <div class="sg-stat">
      <div class="sg-stat__icon sg-stat__icon--blue"><i class="fa-solid fa-user-plus"></i></div>
      <div><div class="sg-stat__value" id="sg-stat-prospectos">0</div><div class="sg-stat__label">Prospectos</div></div>
    </div>
    <div class="sg-stat">
      <div class="sg-stat__icon sg-stat__icon--amber"><i class="fa-solid fa-user-clock"></i></div>
      <div><div class="sg-stat__value" id="sg-stat-inactivos">0</div><div class="sg-stat__label">Inactivos</div></div>
    </div>
  </div>

  <!-- Toolbar -->
  <div class="sg-toolbar">
    <div class="sg-toolbar__left">
      <button class="sg-btn sg-btn--primary" id="sg-nuevo-btn" onclick="openDrawer(null)">
        <i class="fa-solid fa-user-plus"></i> Agregar seguidor
      </button>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
      <select class="sg-filter-select" id="sg-filter-seg" onchange="renderGrid()">
        <option value="">Todos los segmentos</option>
        <option value="activo">Activo</option>
        <option value="prospecto">Prospecto</option>
        <option value="hormiga">Hormiga</option>
        <option value="gran_ahorrador">Gran ahorrador</option>
        <option value="inactivo">Inactivo</option>
      </select>
      <div class="sg-search">
        <i class="fa-solid fa-magnifying-glass" style="color:var(--sg-muted);font-size:.8rem;"></i>
        <input type="text" id="sg-search" placeholder="Buscar nombre o email…" oninput="renderGrid()" />
      </div>
    </div>
  </div>

  <!-- Grid -->
  <div id="sg-container">
    <div class="sg-skeleton">
      <div class="sg-skeleton-card">
        <div class="sg-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="sg-skeleton-line" style="width:80%;"></div>
        <div class="sg-skeleton-line" style="width:60%;"></div>
      </div>
      <div class="sg-skeleton-card">
        <div class="sg-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="sg-skeleton-line" style="width:80%;"></div>
        <div class="sg-skeleton-line" style="width:60%;"></div>
      </div>
      <div class="sg-skeleton-card">
        <div class="sg-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="sg-skeleton-line" style="width:80%;"></div>
        <div class="sg-skeleton-line" style="width:60%;"></div>
      </div>
    </div>
  </div>

  <!-- Confirm -->
  <div class="sg-confirm" id="sg-confirm">
    <div class="sg-confirm__card">
      <div class="sg-confirm__icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div class="sg-confirm__title" id="sg-confirm-title">¿Eliminar seguidor?</div>
      <div class="sg-confirm__text" id="sg-confirm-text">Esta acción no se puede deshacer.</div>
      <div class="sg-confirm__actions">
        <button class="sg-btn" onclick="closeConfirm()">Cancelar</button>
        <button class="sg-btn sg-btn--danger" id="sg-confirm-ok">Sí, eliminar</button>
      </div>
    </div>
  </div>
</main>

<!-- Overlay -->
<div class="sg-overlay" id="sg-overlay" onclick="closeDrawer()"></div>

<!-- Drawer -->
<aside class="sg-drawer" id="sg-drawer">
  <div class="sg-drawer__head">
    <span class="sg-drawer__title" id="sg-drawer-title">Nuevo seguidor</span>
    <button class="sg-drawer__close" onclick="closeDrawer()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="sg-drawer__body">

    <!-- Intelicoop banner -->
    __INTELICOOP_BANNER__

    <div class="sg-field">
      <label for="sg-f-nombre">Nombre completo <span style="color:var(--sg-danger)">*</span></label>
      <input id="sg-f-nombre" type="text" placeholder="Nombre Apellido" />
    </div>
    <div class="sg-field">
      <label for="sg-f-email">Correo electrónico <span style="color:var(--sg-danger)">*</span></label>
      <input id="sg-f-email" type="email" placeholder="correo@ejemplo.com" />
    </div>
    <div class="sg-field--row">
      <div class="sg-field">
        <label for="sg-f-tel">Teléfono</label>
        <input id="sg-f-tel" type="tel" placeholder="+52 55 1234 5678" />
      </div>
      <div class="sg-field">
        <label for="sg-f-tipo">Tipo de socio</label>
        <select id="sg-f-tipo">
          <option value="activo">Activo</option>
          <option value="prospecto">Prospecto</option>
          <option value="inactivo">Inactivo</option>
        </select>
      </div>
    </div>
    <div class="sg-field">
      <label for="sg-f-segmento">Segmento (Intelicoop)</label>
      <select id="sg-f-segmento">
        <option value="activo">Activo</option>
        <option value="prospecto">Prospecto</option>
        <option value="hormiga">Hormiga</option>
        <option value="gran_ahorrador">Gran ahorrador</option>
        <option value="inactivo">Inactivo</option>
      </select>
    </div>
    <div class="sg-field">
      <label for="sg-f-dir">Dirección</label>
      <input id="sg-f-dir" type="text" placeholder="Ciudad, Estado" />
    </div>
    <div class="sg-field--row">
      <div class="sg-field">
        <label for="sg-f-genero">Género</label>
        <select id="sg-f-genero">
          <option value="">Sin especificar</option>
          <option value="femenino">Femenino</option>
          <option value="masculino">Masculino</option>
          <option value="otro">Otro</option>
        </select>
      </div>
      <div class="sg-field">
        <label for="sg-f-nacimiento">Fecha de nacimiento</label>
        <input id="sg-f-nacimiento" type="date" />
      </div>
    </div>
    <div class="sg-field">
      <label for="sg-f-ocupacion">Ocupación</label>
      <input id="sg-f-ocupacion" type="text" placeholder="Ej. Comerciante" />
    </div>
  </div>
  <div class="sg-drawer__footer">
    <button class="sg-btn sg-btn--danger" id="sg-f-del-btn" onclick="openConfirm('single')" style="display:none;">
      <i class="fa-regular fa-trash-can"></i> Eliminar
    </button>
    <button class="sg-btn sg-btn--primary" onclick="saveSeguidor()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
</aside>

<!-- Toast -->
<div class="sg-toast" id="sg-toast"></div>

<script>
(function () {
  var MAX_USERS = parseInt('__MAX_USERS__', 10) || 0;
  var INTELICOOP_ENABLED = __INTELICOOP_ENABLED__;
  var INTELICOOP_API_BASE = '__INTELICOOP_API_BASE__';
  var socios = [];
  var editId = null;
  var confirmCallback = null;

  /* ── Load ── */
  function load() {
    if (!INTELICOOP_ENABLED || !INTELICOOP_API_BASE) {
      socios = [];
      renderGrid();
      updateCapacity();
      updateStats();
      return;
    }
    fetch(INTELICOOP_API_BASE + '/socios', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        socios = Array.isArray(res) ? res : (res.data || []);
        renderGrid();
        updateCapacity();
        updateStats();
      })
      .catch(function () {
        socios = [];
        renderGrid();
        updateCapacity();
        updateStats();
      });
  }

  /* ── Capacity ── */
  function updateCapacity() {
    var count = socios.length;
    var max   = MAX_USERS;
    var pct   = max > 0 ? Math.min(100, Math.round(count / max * 100)) : 0;
    document.getElementById('sg-cap-bar').style.width = pct + '%';
    document.getElementById('sg-cap-bar').className   = 'sg-capacity__bar' + (count >= max && max > 0 ? ' is-full' : '');
    document.getElementById('sg-cap-numbers').textContent = count + ' seguidor' + (count !== 1 ? 'es' : '') + ' de ' + (max > 0 ? max + ' permitido' + (max !== 1 ? 's' : '') : 'sin límite');
    document.getElementById('sg-cap-tag').textContent  = count + ' / ' + (max > 0 ? max : '∞');
    document.getElementById('sg-cap-tag').className    = 'sg-capacity__tag' + (count >= max && max > 0 ? ' is-full' : '');
    var btn = document.getElementById('sg-nuevo-btn');
    if (btn) btn.disabled = max > 0 && count >= max;
  }

  /* ── Stats ── */
  function updateStats() {
    var total = socios.length, activos = 0, prospectos = 0, inactivos = 0;
    socios.forEach(function (s) {
      var seg = (s.segmento || s.tipo_socio || '').toLowerCase();
      if (seg === 'activo' || seg === 'hormiga' || seg === 'gran_ahorrador') activos++;
      else if (seg === 'prospecto') prospectos++;
      else inactivos++;
    });
    document.getElementById('sg-stat-total').textContent     = total;
    document.getElementById('sg-stat-activos').textContent   = activos;
    document.getElementById('sg-stat-prospectos').textContent= prospectos;
    document.getElementById('sg-stat-inactivos').textContent = inactivos;
  }

  /* ── Grid ── */
  window.renderGrid = function () {
    var q  = (document.getElementById('sg-search').value || '').toLowerCase();
    var fs = document.getElementById('sg-filter-seg').value;
    var rows = socios.filter(function (s) {
      var seg = (s.segmento || s.tipo_socio || '').toLowerCase();
      if (fs && seg !== fs) return false;
      if (q) {
        var hay = ((s.nombre || '') + ' ' + (s.email || '')).toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });
    var container = document.getElementById('sg-container');
    if (!rows.length) {
      container.innerHTML = '<div class="sg-empty"><i class="fa-solid fa-user-group"></i>No hay seguidores que coincidan.</div>';
      return;
    }
    container.innerHTML = '<div class="sg-grid">' + rows.map(function (s) {
      var name     = (s.nombre || s.name || '').trim() || s.email || '?';
      var initials = name.split(' ').slice(0, 2).map(function (p) { return p[0] || ''; }).join('').toUpperCase();
      var seg      = (s.segmento || s.tipo_socio || 'default').toLowerCase();
      var segLabel = segLabels[seg] || seg;
      var regDate  = s.fecha_registro ? s.fecha_registro.slice(0, 10) : '';
      return '<div class="sg-card" onclick="openDrawer(' + s.id + ')">'
        + '<div class="sg-card__head">'
        + '<div class="sg-card__avatar">' + initials + '</div>'
        + '<div><div class="sg-card__name">' + esc(name) + '</div>'
        + '<div class="sg-card__email">' + esc(s.email || '') + '</div></div>'
        + '</div>'
        + '<div class="sg-card__meta">'
        + (s.telefono ? '<div class="sg-card__row"><i class="fa-solid fa-phone"></i>' + esc(s.telefono) + '</div>' : '')
        + (s.ocupacion ? '<div class="sg-card__row"><i class="fa-solid fa-briefcase"></i>' + esc(s.ocupacion) + '</div>' : '')
        + (s.direccion ? '<div class="sg-card__row"><i class="fa-solid fa-location-dot"></i>' + esc(s.direccion) + '</div>' : '')
        + '</div>'
        + '<div class="sg-card__foot">'
        + '<span class="sg-seg sg-seg--' + esc(seg) + '">' + esc(segLabel) + '</span>'
        + (regDate ? '<span style="font-size:.72rem;color:var(--sg-muted);">' + esc(regDate) + '</span>' : '')
        + '</div>'
        + '</div>';
    }).join('') + '</div>';
  };

  var segLabels = {
    activo: 'Activo', prospecto: 'Prospecto',
    hormiga: 'Hormiga', gran_ahorrador: 'Gran ahorrador', inactivo: 'Inactivo',
  };

  /* ── Drawer ── */
  window.openDrawer = function (id) {
    editId = id;
    var s = id !== null ? socios.find(function (x) { return x.id === id; }) : null;
    document.getElementById('sg-drawer-title').textContent = s ? 'Editar seguidor' : 'Nuevo seguidor';
    document.getElementById('sg-f-nombre').value     = s ? (s.nombre || '') : '';
    document.getElementById('sg-f-email').value      = s ? (s.email || '') : '';
    document.getElementById('sg-f-tel').value        = s ? (s.telefono || '') : '';
    document.getElementById('sg-f-tipo').value       = s ? (s.tipo_socio || 'activo') : 'activo';
    document.getElementById('sg-f-segmento').value   = s ? (s.segmento || 'activo') : 'activo';
    document.getElementById('sg-f-dir').value        = s ? (s.direccion || '') : '';
    document.getElementById('sg-f-genero').value     = s ? (s.genero || '') : '';
    document.getElementById('sg-f-nacimiento').value = s ? (s.fecha_nacimiento || '') : '';
    document.getElementById('sg-f-ocupacion').value  = s ? (s.ocupacion || '') : '';
    document.getElementById('sg-f-del-btn').style.display = s ? '' : 'none';
    document.getElementById('sg-drawer').classList.add('is-open');
    document.getElementById('sg-overlay').classList.add('is-open');
  };

  window.closeDrawer = function () {
    document.getElementById('sg-drawer').classList.remove('is-open');
    document.getElementById('sg-overlay').classList.remove('is-open');
    editId = null;
  };

  /* ── Save ── */
  window.saveSeguidor = function () {
    if (!INTELICOOP_ENABLED || !INTELICOOP_API_BASE) { showToast('Intelicoop no está habilitado.'); return; }
    var nombre = (document.getElementById('sg-f-nombre').value || '').trim();
    var email  = (document.getElementById('sg-f-email').value || '').trim();
    if (!nombre) { showToast('El nombre es obligatorio.'); return; }
    if (!email)  { showToast('El correo es obligatorio.'); return; }

    var payload = {
      nombre:          nombre,
      email:           email,
      telefono:        document.getElementById('sg-f-tel').value.trim(),
      tipo_socio:      document.getElementById('sg-f-tipo').value,
      segmento:        document.getElementById('sg-f-segmento').value,
      direccion:       document.getElementById('sg-f-dir').value.trim(),
      genero:          document.getElementById('sg-f-genero').value,
      fecha_nacimiento:document.getElementById('sg-f-nacimiento').value,
      ocupacion:       document.getElementById('sg-f-ocupacion').value.trim(),
    };

    var url    = editId !== null ? INTELICOOP_API_BASE + '/socios/' + editId : INTELICOOP_API_BASE + '/socios';
    var method = editId !== null ? 'PUT' : 'POST';

    fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.id || res.success || res.email) {
          closeDrawer();
          showToast(editId !== null ? 'Seguidor actualizado.' : 'Seguidor agregado.');
          load();
        } else {
          showToast(res.detail || res.error || 'Error al guardar.');
        }
      })
      .catch(function () { showToast('Error de conexión.'); });
  };

  /* ── Confirm / delete ── */
  window.openConfirm = function (mode) {
    if (!INTELICOOP_ENABLED || !INTELICOOP_API_BASE) { showToast('Intelicoop no está habilitado.'); return; }
    var s = editId !== null ? socios.find(function (x) { return x.id === editId; }) : null;
    document.getElementById('sg-confirm-title').textContent = '¿Eliminar "' + ((s && s.nombre) || 'este seguidor') + '"?';
    document.getElementById('sg-confirm-text').textContent  = 'Se eliminará también del módulo Intelicoop.';
    confirmCallback = function () {
      if (editId === null) return;
      fetch(INTELICOOP_API_BASE + '/socios/' + editId, {
        method: 'DELETE',
        credentials: 'same-origin',
      })
        .then(function (r) { return r.ok ? {} : r.json(); })
        .then(function (res) {
          closeDrawer();
          showToast('Seguidor eliminado.');
          load();
        })
        .catch(function () { showToast('Error de conexión.'); });
    };
    document.getElementById('sg-confirm').classList.add('is-open');
  };

  window.closeConfirm = function () { document.getElementById('sg-confirm').classList.remove('is-open'); };
  document.getElementById('sg-confirm-ok').addEventListener('click', function () {
    closeConfirm();
    if (confirmCallback) { confirmCallback(); confirmCallback = null; }
  });

  /* ── Helpers ── */
  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function showToast(msg) {
    var t = document.getElementById('sg-toast');
    t.textContent = msg; t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 2800);
  }

  /* ── Init ── */
  load();
})();
</script>
</body>
</html>
"""
