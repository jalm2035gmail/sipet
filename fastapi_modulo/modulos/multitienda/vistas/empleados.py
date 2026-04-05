from __future__ import annotations

from html import escape


def empleados_html(max_users: int = 0) -> str:
    return _HTML.replace("__MAX_USERS__", escape(str(max_users)))


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Equipo — Multitienda</title>
  <link rel="stylesheet" href="/multitienda/static/css/empleados.css" />
</head>
<body>
<main>

  <!-- Capacity bar -->
  <div class="em-capacity" id="em-capacity">
    <div class="em-capacity__icon"><i class="fa-solid fa-users"></i></div>
    <div class="em-capacity__info">
      <div class="em-capacity__title">Capacidad del equipo</div>
      <div class="em-capacity__bar-wrap">
        <div class="em-capacity__bar" id="em-cap-bar" style="width:0%"></div>
      </div>
      <div class="em-capacity__numbers" id="em-cap-numbers">Cargando…</div>
    </div>
    <div class="em-capacity__tag" id="em-cap-tag">0 / __MAX_USERS__</div>
  </div>

  <!-- Toolbar -->
  <div class="em-toolbar">
    <div class="em-toolbar__left">
      <button class="em-btn em-btn--primary" id="em-nuevo-btn" onclick="openDrawer(-1)">
        <i class="fa-solid fa-user-plus"></i> Agregar integrante
      </button>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
      <select class="em-filter-select" id="em-filter-rol" onchange="renderGrid()">
        <option value="">Todos los roles</option>
        <option value="superadministrador">Superadmin</option>
        <option value="administrador">Administrador</option>
        <option value="usuario">Usuario</option>
      </select>
      <select class="em-filter-select" id="em-filter-estado" onchange="renderGrid()">
        <option value="">Todos los estados</option>
        <option value="Activo">Activo</option>
        <option value="Inactivo">Inactivo</option>
      </select>
      <div class="em-search">
        <i class="fa-solid fa-magnifying-glass" style="color:var(--em-muted);font-size:.8rem;"></i>
        <input type="text" id="em-search" placeholder="Buscar nombre o usuario…" oninput="renderGrid()" />
      </div>
    </div>
  </div>

  <!-- Grid -->
  <div id="em-container">
    <div class="em-skeleton">
      <div class="em-skeleton-card">
        <div class="em-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="em-skeleton-line" style="width:80%;"></div>
        <div class="em-skeleton-line" style="width:60%;"></div>
        <div class="em-skeleton-line" style="width:70%;"></div>
      </div>
      <div class="em-skeleton-card">
        <div class="em-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="em-skeleton-line" style="width:80%;"></div>
        <div class="em-skeleton-line" style="width:60%;"></div>
        <div class="em-skeleton-line" style="width:70%;"></div>
      </div>
      <div class="em-skeleton-card">
        <div class="em-skeleton-line" style="width:40%;height:40px;border-radius:12px;margin-bottom:12px;"></div>
        <div class="em-skeleton-line" style="width:80%;"></div>
        <div class="em-skeleton-line" style="width:60%;"></div>
        <div class="em-skeleton-line" style="width:70%;"></div>
      </div>
    </div>
  </div>

  <!-- Confirm -->
  <div class="em-confirm" id="em-confirm">
    <div class="em-confirm__card">
      <div class="em-confirm__icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div class="em-confirm__title" id="em-confirm-title">¿Desactivar integrante?</div>
      <div class="em-confirm__text" id="em-confirm-text">El usuario perderá acceso al sistema.</div>
      <div class="em-confirm__actions">
        <button class="em-btn" onclick="closeConfirm()">Cancelar</button>
        <button class="em-btn em-btn--danger" id="em-confirm-ok">Confirmar</button>
      </div>
    </div>
  </div>

  <!-- Limit reached modal -->
  <div class="em-limit" id="em-limit">
    <div class="em-limit__card">
      <div class="em-limit__icon"><i class="fa-solid fa-users-slash"></i></div>
      <div class="em-limit__title">Límite de vendedores alcanzado</div>
      <div class="em-limit__text">No puede agregar más vendedores. Contacta al administrador si necesitas agregar más personal a tu tienda.</div>
      <div class="em-limit__actions">
        <button class="em-btn" onclick="document.getElementById('em-limit').classList.remove('is-open')">Cerrar</button>
        <a class="em-btn em-btn--whatsapp"
           href="https://wa.me/523327633869?text=Hola%2C+necesito+agregar+m%C3%A1s+vendedores+a+mi+tienda+en+SIPET.+%C2%BFMe+pueden+ayudar%3F"
           target="_blank" rel="noopener">
          <i class="fa-brands fa-whatsapp"></i> Enviar WhatsApp
        </a>
      </div>
    </div>
  </div>

  <!-- Overlay -->
  <div class="em-overlay" id="em-overlay" onclick="closeDrawer()"></div>

  <!-- Drawer -->
  <aside class="em-drawer" id="em-drawer">
  <div class="em-drawer__head">
    <span class="em-drawer__title" id="em-drawer-title">Nuevo integrante</span>
    <button class="em-drawer__close" onclick="closeDrawer()"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div class="em-drawer__body">
    <!-- Tabs -->
    <div class="em-dtabs">
      <button class="em-dtab is-active" data-tab="info" onclick="showDTab('info')">
        <i class="fa-solid fa-user"></i> Información
      </button>
      <button class="em-dtab" data-tab="acceso" onclick="showDTab('acceso')">
        <i class="fa-solid fa-key"></i> Acceso
      </button>
    </div>

    <!-- Panel: Información -->
    <div class="em-dpanel is-active" id="em-dpanel-info">
      <div class="em-field--row">
        <div class="em-field">
          <label for="em-f-nombre">Nombre completo <span style="color:var(--em-danger)">*</span></label>
          <input id="em-f-nombre" type="text" placeholder="Nombre Apellido" />
        </div>
        <div class="em-field">
          <label for="em-f-puesto">Puesto</label>
          <input id="em-f-puesto" type="text" placeholder="Ej. Encargado de tienda" />
        </div>
      </div>
      <div class="em-field">
        <label for="em-f-departamento">Departamento</label>
        <input id="em-f-departamento" type="text" placeholder="Ej. Ventas" />
      </div>
      <div class="em-field">
        <label for="em-f-correo">Correo electrónico</label>
        <input id="em-f-correo" type="email" placeholder="correo@ejemplo.com" />
      </div>
      <div class="em-field">
        <label for="em-f-celular">Teléfono / celular</label>
        <input id="em-f-celular" type="tel" placeholder="+52 55 1234 5678" />
      </div>
    </div>

    <!-- Panel: Acceso -->
    <div class="em-dpanel" id="em-dpanel-acceso">
      <div class="em-field">
        <label for="em-f-usuario">Usuario (login) <span style="color:var(--em-danger)">*</span></label>
        <input id="em-f-usuario" type="text" placeholder="usuario_login" autocomplete="off" />
        <span class="em-field--hint">Nombre de usuario para iniciar sesión. Sin espacios.</span>
      </div>
      <div class="em-field">
        <label for="em-f-rol">Rol</label>
        <select id="em-f-rol">
          <option value="usuario">Usuario</option>
          <option value="administrador">Administrador</option>
        </select>
      </div>
      <div class="em-field">
        <label for="em-f-estado">Estado</label>
        <select id="em-f-estado">
          <option value="activo">Activo</option>
          <option value="inactivo">Inactivo</option>
        </select>
      </div>

      <!-- Password block (only for new) -->
      <div class="em-pwd-section" id="em-pwd-new-block">
        <h4><i class="fa-solid fa-lock" style="margin-right:6px;color:var(--em-muted);"></i>Contraseña inicial</h4>
        <div class="em-field">
          <label for="em-f-pwd">Contraseña <span style="color:var(--em-danger)">*</span></label>
          <input id="em-f-pwd" type="password" placeholder="Contraseña de acceso" autocomplete="new-password" />
        </div>
      </div>

      <!-- Password block (only for existing) -->
      <div class="em-pwd-section" id="em-pwd-change-block" style="display:none;">
        <h4><i class="fa-solid fa-lock-open" style="margin-right:6px;color:var(--em-muted);"></i>Cambiar contraseña</h4>
        <div class="em-pwd-row">
          <div class="em-field">
            <label for="em-f-newpwd">Nueva contraseña</label>
            <input id="em-f-newpwd" type="password" placeholder="Dejar vacío para no cambiar" autocomplete="new-password" />
          </div>
          <button class="em-btn" onclick="changePwd()">
            <i class="fa-solid fa-floppy-disk"></i> Guardar
          </button>
        </div>
      </div>
    </div>
  </div>
  <div class="em-drawer__footer">
    <button class="em-btn em-btn--danger" id="em-f-delete-btn" onclick="openConfirm('delete')" style="display:none;">
      <i class="fa-regular fa-trash-can"></i> Eliminar
    </button>
    <button class="em-btn em-btn--danger" id="em-f-toggle-btn" onclick="openConfirm('toggle')" style="display:none;">
      <i class="fa-solid fa-user-slash"></i> Desactivar
    </button>
    <button class="em-btn em-btn--primary" onclick="saveEmployee()">
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>
  </aside>

  <!-- Toast -->
  <div class="em-toast" id="em-toast"></div>
</main>

<script>
(function () {
  var MAX_USERS = parseInt('__MAX_USERS__', 10) || 0;
  var employees = [];
  var editId = null; // null = new

  /* ── Load from API ── */
  function loadEmployees() {
    fetch('/multitienda/api/empleados', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.success) {
          employees = res.data || [];
        } else {
          employees = [];
        }
        renderGrid();
        updateCapacity();
      })
      .catch(function () {
        employees = [];
        renderGrid();
        updateCapacity();
      });
  }

  /* ── Capacity bar ── */
  function updateCapacity() {
    var count = employees.length;
    var max   = MAX_USERS;
    var pct   = max > 0 ? Math.min(100, Math.round(count / max * 100)) : 0;
    var bar   = document.getElementById('em-cap-bar');
    var nums  = document.getElementById('em-cap-numbers');
    var tag   = document.getElementById('em-cap-tag');
    var btn   = document.getElementById('em-nuevo-btn');
    var full  = max > 0 && count >= max;
    bar.style.width = pct + '%';
    bar.className   = 'em-capacity__bar' + (full ? ' is-full' : '');
    nums.textContent = count + ' integrante' + (count !== 1 ? 's' : '') + ' de ' + (max > 0 ? max + ' permitido' + (max !== 1 ? 's' : '') : 'sin límite');
    tag.textContent  = count + ' / ' + (max > 0 ? max : '∞');
    tag.className    = 'em-capacity__tag' + (full ? ' is-full' : '');
    if (btn) {
      btn.disabled = full;
      btn.onclick = full
        ? function () { document.getElementById('em-limit').classList.add('is-open'); }
        : function () { openDrawer(-1); };
    }
  }

  /* ── Grid ── */
  window.renderGrid = function () {
    var q  = (document.getElementById('em-search').value || '').toLowerCase();
    var fr = document.getElementById('em-filter-rol').value.toLowerCase();
    var fe = document.getElementById('em-filter-estado').value.toLowerCase();

    var rows = employees.filter(function (e) {
      if (fr && (e.rol || '').toLowerCase() !== fr) return false;
      if (fe && (e.estado || '').toLowerCase() !== fe.toLowerCase()) return false;
      if (q) {
        var hay = ((e.nombre || '') + ' ' + (e.full_name || '') + ' ' + (e.usuario || '')).toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });

    var container = document.getElementById('em-container');
    if (!rows.length) {
      container.innerHTML = '<div class="em-empty"><i class="fa-solid fa-users"></i>No hay integrantes que coincidan.</div>';
      return;
    }

    container.innerHTML = '<div class="em-grid">' + rows.map(function (e) {
      var name    = (e.full_name || e.nombre || '').trim() || e.usuario || '?';
      var initials = name.split(' ').slice(0, 2).map(function (p) { return p[0] || ''; }).join('').toUpperCase();
      var avatar  = e.imagen
        ? '<img src="' + esc(e.imagen) + '" alt="' + esc(name) + '" />'
        : initials;
      var isActive = (e.estado || 'Activo').toLowerCase() !== 'inactivo';
      var badgeEstado = isActive
        ? '<span class="em-badge em-badge--active"><i class="fa-solid fa-circle" style="font-size:.5rem;"></i>Activo</span>'
        : '<span class="em-badge em-badge--inactive"><i class="fa-solid fa-circle" style="font-size:.5rem;"></i>Inactivo</span>';
      var rolLabel = rolNice(e.rol || 'usuario');
      return '<div class="em-card" onclick="openDrawer(' + e.id + ')">'
        + '<div class="em-card__head">'
        + '<div class="em-card__avatar">' + avatar + '</div>'
        + '<div><div class="em-card__name">' + esc(name) + '</div>'
        + '<div class="em-card__user">@' + esc(e.usuario || '') + '</div></div>'
        + '</div>'
        + '<div class="em-card__meta">'
        + (e.puesto ? '<div class="em-card__row"><i class="fa-solid fa-briefcase"></i>' + esc(e.puesto) + '</div>' : '')
        + (e.departamento ? '<div class="em-card__row"><i class="fa-solid fa-building"></i>' + esc(e.departamento) + '</div>' : '')
        + (e.correo ? '<div class="em-card__row"><i class="fa-solid fa-envelope"></i>' + esc(e.correo) + '</div>' : '')
        + '</div>'
        + '<div class="em-card__foot">'
        + '<span class="em-badge em-badge--role">' + esc(rolLabel) + '</span>'
        + badgeEstado
        + '</div>'
        + '</div>';
    }).join('') + '</div>';
  };

  function rolNice(r) {
    var m = { superadministrador: 'Superadmin', administrador: 'Admin', usuario: 'Usuario' };
    return m[(r || '').toLowerCase()] || r;
  }

  /* ── Drawer tabs ── */
  window.showDTab = function (id) {
    document.querySelectorAll('.em-dtab').forEach(function (t) { t.classList.toggle('is-active', t.dataset.tab === id); });
    document.querySelectorAll('.em-dpanel').forEach(function (p) { p.classList.toggle('is-active', p.id === 'em-dpanel-' + id); });
  };

  /* ── Open drawer ── */
  window.openDrawer = function (id) {
    editId = id === -1 ? null : id;
    showDTab('info');

    var emp = editId !== null ? employees.find(function (e) { return e.id === editId; }) : null;
    document.getElementById('em-drawer-title').textContent = emp ? 'Editar integrante' : 'Nuevo integrante';
    document.getElementById('em-f-nombre').value      = emp ? (emp.full_name || emp.nombre || '') : '';
    document.getElementById('em-f-puesto').value      = emp ? (emp.puesto || '') : '';
    document.getElementById('em-f-departamento').value= emp ? (emp.departamento || '') : '';
    document.getElementById('em-f-correo').value      = emp ? (emp.correo || '') : '';
    document.getElementById('em-f-celular').value     = emp ? (emp.celular || '') : '';
    document.getElementById('em-f-usuario').value     = emp ? (emp.usuario || '') : '';
    document.getElementById('em-f-rol').value         = emp ? (emp.rol || 'usuario').toLowerCase() : 'usuario';
    var isActive = emp ? (emp.estado || 'Activo').toLowerCase() !== 'inactivo' : true;
    document.getElementById('em-f-estado').value      = isActive ? 'activo' : 'inactivo';
    document.getElementById('em-f-pwd').value         = '';
    document.getElementById('em-f-newpwd').value      = '';

    // Blocks
    document.getElementById('em-pwd-new-block').style.display    = emp ? 'none' : '';
    document.getElementById('em-pwd-change-block').style.display = emp ? '' : 'none';
    document.getElementById('em-f-delete-btn').style.display = emp ? '' : 'none';
    var toggleBtn = document.getElementById('em-f-toggle-btn');
    toggleBtn.style.display = emp ? '' : 'none';
    if (emp) {
      toggleBtn.innerHTML = isActive
        ? '<i class="fa-solid fa-user-slash"></i> Desactivar'
        : '<i class="fa-solid fa-user-check"></i> Activar';
      toggleBtn.className = isActive ? 'em-btn em-btn--danger' : 'em-btn';
    }

    document.getElementById('em-drawer').classList.add('is-open');
    document.getElementById('em-overlay').classList.add('is-open');
  };

  window.closeDrawer = function () {
    document.getElementById('em-drawer').classList.remove('is-open');
    document.getElementById('em-overlay').classList.remove('is-open');
    editId = null;
  };

  /* ── Save ── */
  window.saveEmployee = function () {
    var nombre  = (document.getElementById('em-f-nombre').value || '').trim();
    var usuario = (document.getElementById('em-f-usuario').value || '').trim();
    var correo  = (document.getElementById('em-f-correo').value || '').trim();
    var pwd     = document.getElementById('em-f-pwd').value;
    var isNew   = editId === null;

    if (!nombre)  { showToast('El nombre es obligatorio.'); showDTab('info');   return; }
    if (!usuario) { showToast('El usuario es obligatorio.'); showDTab('acceso'); return; }
    if (isNew && !pwd) { showToast('La contraseña es obligatoria para nuevos integrantes.'); showDTab('acceso'); return; }

    var payload = {
      nombre:       nombre,
      usuario:      usuario,
      correo:       correo,
      puesto:       document.getElementById('em-f-puesto').value.trim(),
      celular:      document.getElementById('em-f-celular').value.trim(),
      departamento: document.getElementById('em-f-departamento').value.trim(),
      rol:          document.getElementById('em-f-rol').value,
    };
    if (isNew) {
      payload.contrasena = pwd;
    }

    var url    = isNew ? '/multitienda/api/empleados' : '/multitienda/api/empleados/' + editId;
    var method = isNew ? 'POST' : 'PUT';

    fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    })
      .then(function (r) {
        if (r.status === 422) {
          return r.json().then(function (res) {
            if ((res.detail || '') === 'LIMIT_REACHED') {
              closeDrawer();
              document.getElementById('em-limit').classList.add('is-open');
            } else {
              showToast(res.detail || res.error || 'Error al guardar.');
            }
          });
        }
        return r.json().then(function (res) {
          if (res.success) {
            closeDrawer();
            showToast(isNew ? 'Vendedor agregado.' : 'Integrante actualizado.');
            loadEmployees();
          } else {
            showToast(res.detail || res.error || 'Error al guardar.');
          }
        });
      })
      .catch(function () { showToast('Error de conexión.'); });
  };

  /* ── Change password ── */
  window.changePwd = function () {
    var pwd = (document.getElementById('em-f-newpwd').value || '').trim();
    if (!pwd) { showToast('Ingresa una nueva contraseña.'); return; }
    if (editId === null) { showToast('Guarda el integrante primero.'); return; }
    fetch('/multitienda/api/empleados/' + editId + '/password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ password: pwd }),
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.success) {
          document.getElementById('em-f-newpwd').value = '';
          showToast('Contraseña actualizada.');
        } else {
          showToast(res.error || 'Error al cambiar contraseña.');
        }
      })
      .catch(function () { showToast('Error de conexión.'); });
  };

  /* ── Toggle active/inactive ── */
  var confirmCallback = null;
  window.openConfirm = function (mode) {
    var emp = editId !== null ? employees.find(function (e) { return e.id === editId; }) : null;
    if (!emp) return;
    if (mode === 'delete') {
      document.getElementById('em-confirm-title').textContent = '¿Eliminar integrante?';
      document.getElementById('em-confirm-text').textContent  = 'Esta acción elimina el registro del integrante de forma definitiva.';
      document.getElementById('em-confirm-ok').textContent = 'Sí, eliminar';
      document.getElementById('em-confirm-ok').className   = 'em-btn em-btn--danger';
      confirmCallback = function () {
        fetch('/multitienda/api/empleados/' + editId, {
          method: 'DELETE',
          credentials: 'same-origin',
        })
          .then(function (r) { return r.json(); })
          .then(function (res) {
            if (res.success) {
              closeDrawer();
              showToast('Integrante eliminado.');
              loadEmployees();
            } else {
              showToast(res.error || 'Error al eliminar.');
            }
          })
          .catch(function () { showToast('Error de conexión.'); });
      };
      document.getElementById('em-confirm').classList.add('is-open');
      return;
    }
    var isActive = (emp.estado || 'Activo').toLowerCase() !== 'inactivo';
    document.getElementById('em-confirm-title').textContent = isActive ? '¿Desactivar integrante?' : '¿Activar integrante?';
    document.getElementById('em-confirm-text').textContent  = isActive
      ? 'El usuario no podrá iniciar sesión hasta que sea reactivado.'
      : 'El usuario podrá volver a iniciar sesión.';
    document.getElementById('em-confirm-ok').textContent = isActive ? 'Sí, desactivar' : 'Sí, activar';
    document.getElementById('em-confirm-ok').className   = isActive ? 'em-btn em-btn--danger' : 'em-btn em-btn--primary';
    confirmCallback = function () {
      var newActive = !isActive;
      fetch('/multitienda/api/empleados/' + editId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ is_active: newActive }),
      })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (res.success) {
            closeDrawer();
            showToast(isActive ? 'Integrante desactivado.' : 'Integrante activado.');
            loadEmployees();
          } else {
            showToast(res.error || 'Error.');
          }
        })
        .catch(function () { showToast('Error de conexión.'); });
    };
    document.getElementById('em-confirm').classList.add('is-open');
  };
  window.closeConfirm = function () { document.getElementById('em-confirm').classList.remove('is-open'); };
  document.getElementById('em-confirm-ok').addEventListener('click', function () {
    closeConfirm();
    if (confirmCallback) { confirmCallback(); confirmCallback = null; }
  });

  /* ── Helpers ── */
  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function showToast(msg) {
    var t = document.getElementById('em-toast');
    t.textContent = msg; t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 2800);
  }

  /* ── Init ── */
  loadEmployees();
})();
</script>
</body>
</html>
"""
