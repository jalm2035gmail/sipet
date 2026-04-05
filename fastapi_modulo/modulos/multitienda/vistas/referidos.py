from __future__ import annotations


def referidos_html() -> str:
    return _HTML


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Referidos — Multitienda</title>
  <link rel="stylesheet" href="/multitienda/static/css/referidos.css" />
</head>
<body>
<main>

  <!-- Toolbar -->
  <div class="rf-toolbar">
    <div class="rf-toolbar__left">
      <button class="rf-btn rf-btn--primary" id="rf-nuevo-btn">
        <i class="fa-solid fa-user-plus"></i> Nuevo referido
      </button>
      <button class="rf-btn rf-btn--danger" id="rf-eliminar-btn" disabled>
        <i class="fa-solid fa-trash"></i> Eliminar
      </button>
    </div>
    <div class="rf-search">
      <i class="fa-solid fa-magnifying-glass" style="color:var(--rf-muted);font-size:.82rem"></i>
      <input id="rf-search" type="search" placeholder="Buscar referido…" />
    </div>
  </div>

  <!-- Stats -->
  <div class="rf-stats">
    <div class="rf-stat">
      <div class="rf-stat__icon rf-stat__icon--blue"><i class="fa-solid fa-users"></i></div>
      <div><div class="rf-stat__value" id="rf-stat-total">0</div><div class="rf-stat__label">Total referidos</div></div>
    </div>
    <div class="rf-stat">
      <div class="rf-stat__icon rf-stat__icon--green"><i class="fa-solid fa-circle-check"></i></div>
      <div><div class="rf-stat__value" id="rf-stat-activos">0</div><div class="rf-stat__label">Activos</div></div>
    </div>
    <div class="rf-stat">
      <div class="rf-stat__icon rf-stat__icon--amber"><i class="fa-solid fa-hourglass-half"></i></div>
      <div><div class="rf-stat__value" id="rf-stat-pendientes">0</div><div class="rf-stat__label">Pendientes</div></div>
    </div>
    <div class="rf-stat">
      <div class="rf-stat__icon rf-stat__icon--violet"><i class="fa-solid fa-coins"></i></div>
      <div><div class="rf-stat__value" id="rf-stat-comisiones">$0</div><div class="rf-stat__label">Comisiones</div></div>
    </div>
  </div>

  <!-- Tabla -->
  <div class="rf-table-wrap">
    <table class="rf-table">
      <thead>
        <tr>
          <th style="width:32px"><input type="checkbox" id="rf-select-all" /></th>
          <th class="sortable" data-col="nombre">Nombre <span class="sarr">↕</span></th>
          <th class="sortable" data-col="email">Email <span class="sarr">↕</span></th>
          <th class="sortable" data-col="codigo">Código <span class="sarr">↕</span></th>
          <th class="sortable" data-col="estado">Estado <span class="sarr">↕</span></th>
          <th class="sortable" data-col="comision">Comisión % <span class="sarr">↕</span></th>
          <th class="sortable" data-col="fecha">Fecha <span class="sarr">↕</span></th>
          <th style="width:32px"></th>
        </tr>
      </thead>
      <tbody id="rf-tbody"></tbody>
    </table>
    <div id="rf-empty" class="rf-empty" hidden>
      <i class="fa-regular fa-user-group"></i>
      Sin referidos registrados. Haz clic en <strong>Nuevo referido</strong> para agregar el primero.
    </div>
  </div>

  <!-- Drawer / Formulario -->
  <div class="rf-drawer" id="rf-drawer" role="dialog" aria-modal="true" aria-labelledby="rf-drawer-title">
    <div class="rf-drawer__head">
      <h2 class="rf-drawer__title" id="rf-drawer-title">Nuevo referido</h2>
      <button class="rf-drawer__close" id="rf-drawer-close"><i class="fa-solid fa-xmark"></i></button>
    </div>
    <div class="rf-drawer__body">
      <div class="rf-row-2">
        <div class="rf-field">
          <label for="rf-nombre">Nombre *</label>
          <input class="rf-input" id="rf-nombre" type="text" placeholder="Nombre completo" />
        </div>
        <div class="rf-field">
          <label for="rf-apellido">Apellido</label>
          <input class="rf-input" id="rf-apellido" type="text" placeholder="Apellido" />
        </div>
      </div>
      <div class="rf-field">
        <label for="rf-email">Correo electrónico</label>
        <input class="rf-input" id="rf-email" type="email" placeholder="correo@ejemplo.com" />
      </div>
      <div class="rf-field">
        <label for="rf-telefono">Teléfono</label>
        <input class="rf-input" id="rf-telefono" type="tel" placeholder="55 1234 5678" />
      </div>
      <div class="rf-row-2">
        <div class="rf-field">
          <label for="rf-codigo">Código de referido</label>
          <input class="rf-input" id="rf-codigo" type="text" placeholder="Ej. REF-001" />
        </div>
        <div class="rf-field">
          <label for="rf-comision">Comisión (%)</label>
          <input class="rf-input" id="rf-comision" type="number" min="0" max="100" step="0.5" placeholder="0" />
        </div>
      </div>
      <div class="rf-field">
        <label for="rf-estado">Estado</label>
        <select class="rf-select" id="rf-estado">
          <option value="pendiente">Pendiente</option>
          <option value="activo">Activo</option>
          <option value="inactivo">Inactivo</option>
        </select>
      </div>
      <div class="rf-field">
        <label for="rf-notas">Notas</label>
        <textarea class="rf-textarea" id="rf-notas" placeholder="Observaciones internas…"></textarea>
      </div>
    </div>
    <div class="rf-drawer__foot">
      <div class="rf-drawer__foot-left">
        <button class="rf-btn rf-btn--primary" id="rf-guardar-btn">Guardar</button>
        <button class="rf-btn" id="rf-descartar-btn">Cancelar</button>
      </div>
      <button class="rf-btn rf-btn--danger" id="rf-form-eliminar-btn" style="display:none">
        <i class="fa-solid fa-trash"></i> Eliminar
      </button>
    </div>
  </div>

  <!-- Confirm delete -->
  <div class="rf-confirm" id="rf-confirm" hidden>
    <div class="rf-confirm__card">
      <h3 class="rf-confirm__title"><i class="fa-solid fa-triangle-exclamation"></i> Eliminar referido(s)</h3>
      <p class="rf-confirm__msg" id="rf-confirm-msg">¿Confirmar eliminación?</p>
      <div class="rf-confirm__actions">
        <button class="rf-btn" id="rf-confirm-cancel">Cancelar</button>
        <button class="rf-btn rf-btn--danger" id="rf-confirm-ok">Eliminar</button>
      </div>
    </div>
  </div>

  <!-- Toast -->
  <div class="rf-toast" id="rf-toast"></div>

</main>
<script>
(function () {
  'use strict';

  var STORAGE_KEY = 'multitienda_referidos';

  /* ── State ── */
  var referidos = [];
  var filtered  = [];
  var selected  = new Set();
  var editId    = null;
  var pendingDeleteIds = [];
  var sortCol = 'nombre', sortAsc = true;

  /* ── Elements ── */
  var tbody        = document.getElementById('rf-tbody');
  var emptyEl      = document.getElementById('rf-empty');
  var selectAll    = document.getElementById('rf-select-all');
  var searchInput  = document.getElementById('rf-search');
  var nuevoBtn     = document.getElementById('rf-nuevo-btn');
  var eliminarBtn  = document.getElementById('rf-eliminar-btn');
  var drawer       = document.getElementById('rf-drawer');
  var drawerTitle  = document.getElementById('rf-drawer-title');
  var drawerClose  = document.getElementById('rf-drawer-close');
  var guardarBtn   = document.getElementById('rf-guardar-btn');
  var descartarBtn = document.getElementById('rf-descartar-btn');
  var formElimBtn  = document.getElementById('rf-form-eliminar-btn');
  var confirm_     = document.getElementById('rf-confirm');
  var confirmMsg   = document.getElementById('rf-confirm-msg');
  var confirmOk    = document.getElementById('rf-confirm-ok');
  var confirmCancel= document.getElementById('rf-confirm-cancel');
  var toast        = document.getElementById('rf-toast');

  /* ── Persistence ── */
  function load() {
    try { referidos = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
    catch (e) { referidos = []; }
    referidos.forEach(function (r) { if (!r._id) r._id = uid(); });
  }
  function save() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(referidos)); }
    catch (e) { showToast('Almacenamiento lleno.', 'error'); }
  }

  /* ── Utils ── */
  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2); }
  function esc(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function fmtDate(iso) {
    try { return new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium' }).format(new Date(iso)); }
    catch (e) { return iso ? iso.slice(0, 10) : ''; }
  }

  /* ── Toast ── */
  var _toastT;
  function showToast(msg, type) {
    toast.textContent = msg;
    toast.className = 'rf-toast visible' + (type ? ' ' + type : '');
    clearTimeout(_toastT);
    _toastT = setTimeout(function () { toast.className = 'rf-toast'; }, 3000);
  }

  /* ── Stats ── */
  function updateStats() {
    document.getElementById('rf-stat-total').textContent = String(referidos.length);
    document.getElementById('rf-stat-activos').textContent = String(referidos.filter(function(r){ return r.estado === 'activo'; }).length);
    document.getElementById('rf-stat-pendientes').textContent = String(referidos.filter(function(r){ return r.estado === 'pendiente'; }).length);
    var totalComision = referidos.reduce(function(acc, r){ return acc + (parseFloat(r.comision) || 0); }, 0);
    document.getElementById('rf-stat-comisiones').textContent = totalComision.toFixed(1) + '%';
  }

  /* ── Filter / Sort ── */
  function applyFilterSort() {
    var q = (searchInput.value || '').toLowerCase();
    filtered = referidos.filter(function (r) {
      if (!q) return true;
      return (r.nombre||'').toLowerCase().includes(q) ||
             (r.apellido||'').toLowerCase().includes(q) ||
             (r.email||'').toLowerCase().includes(q) ||
             (r.codigo||'').toLowerCase().includes(q);
    });
    filtered.sort(function (a, b) {
      var va = String(a[sortCol] || ''), vb = String(b[sortCol] || '');
      if (sortCol === 'comision') { va = parseFloat(va)||0; vb = parseFloat(vb)||0; return sortAsc ? va-vb : vb-va; }
      return sortAsc ? va.localeCompare(vb, 'es') : vb.localeCompare(va, 'es');
    });
    render();
  }

  /* ── Render table ── */
  function render() {
    tbody.innerHTML = '';
    emptyEl.hidden = filtered.length > 0;
    filtered.forEach(function (r) {
      var tr = document.createElement('tr');
      tr.dataset.id = r._id;
      var estadoClass = r.estado === 'activo' ? 'green' : r.estado === 'pendiente' ? 'amber' : 'gray';
      var estadoLabel = r.estado === 'activo' ? 'Activo' : r.estado === 'pendiente' ? 'Pendiente' : 'Inactivo';
      tr.innerHTML =
        '<td><input type="checkbox" class="rf-check" data-id="' + esc(r._id) + '" ' + (selected.has(r._id) ? 'checked' : '') + ' /></td>' +
        '<td>' + esc((r.nombre||'') + (r.apellido ? ' ' + r.apellido : '')) + '</td>' +
        '<td style="color:var(--rf-muted)">' + esc(r.email||'—') + '</td>' +
        '<td><code style="font-size:.78rem;background:var(--rf-bg);padding:2px 6px;border-radius:4px">' + esc(r.codigo||'—') + '</code></td>' +
        '<td><span class="rf-badge rf-badge--' + estadoClass + '">' + estadoLabel + '</span></td>' +
        '<td>' + (r.comision ? r.comision + '%' : '—') + '</td>' +
        '<td style="color:var(--rf-muted);font-size:.8rem">' + (r.fecha ? fmtDate(r.fecha) : '—') + '</td>' +
        '<td><button class="rf-btn" style="min-height:28px;padding:0 10px;font-size:.76rem" data-edit="' + esc(r._id) + '"><i class="fa-solid fa-pen"></i></button></td>';
      tbody.appendChild(tr);
    });
    /* sort arrows */
    document.querySelectorAll('.rf-table th.sortable').forEach(function (th) {
      var sp = th.querySelector('.sarr'); if (!sp) return;
      if (th.dataset.col === sortCol) { sp.textContent = sortAsc ? '↑' : '↓'; sp.style.color = 'var(--rf-accent)'; }
      else { sp.textContent = '↕'; sp.style.color = 'var(--rf-muted)'; }
    });
    syncEliminarBtn();
    updateStats();
    /* selectAll state */
    selectAll.checked = filtered.length > 0 && filtered.every(function (r) { return selected.has(r._id); });
    selectAll.indeterminate = !selectAll.checked && filtered.some(function (r) { return selected.has(r._id); });
  }

  /* ── Selection ── */
  function syncEliminarBtn() {
    eliminarBtn.disabled = selected.size === 0;
  }

  tbody.addEventListener('change', function (e) {
    var cb = e.target.closest('.rf-check'); if (!cb) return;
    if (cb.checked) selected.add(cb.dataset.id); else selected.delete(cb.dataset.id);
    render();
  });

  selectAll.addEventListener('change', function () {
    filtered.forEach(function (r) { if (selectAll.checked) selected.add(r._id); else selected.delete(r._id); });
    render();
  });

  document.querySelectorAll('.rf-table th.sortable').forEach(function (th) {
    th.addEventListener('click', function () {
      if (sortCol === th.dataset.col) sortAsc = !sortAsc; else { sortCol = th.dataset.col; sortAsc = true; }
      applyFilterSort();
    });
  });

  searchInput.addEventListener('input', applyFilterSort);

  /* Edit btn in row */
  tbody.addEventListener('click', function (e) {
    var editBtn = e.target.closest('[data-edit]');
    if (editBtn) { openDrawer(editBtn.dataset.edit); return; }
    /* click on row */
    var tr = e.target.closest('tr[data-id]');
    if (tr && !e.target.closest('.rf-check') && !e.target.closest('[data-edit]')) {
      openDrawer(tr.dataset.id);
    }
  });

  /* ── Drawer ── */
  function openDrawer(id) {
    editId = id || null;
    var r = id ? referidos.find(function (x) { return x._id === id; }) : null;
    drawerTitle.textContent = r ? 'Editar referido' : 'Nuevo referido';
    document.getElementById('rf-nombre').value   = r ? (r.nombre   || '') : '';
    document.getElementById('rf-apellido').value = r ? (r.apellido || '') : '';
    document.getElementById('rf-email').value    = r ? (r.email    || '') : '';
    document.getElementById('rf-telefono').value = r ? (r.telefono || '') : '';
    document.getElementById('rf-codigo').value   = r ? (r.codigo   || '') : '';
    document.getElementById('rf-comision').value = r ? (r.comision || '') : '';
    document.getElementById('rf-estado').value   = r ? (r.estado   || 'pendiente') : 'pendiente';
    document.getElementById('rf-notas').value    = r ? (r.notas    || '') : '';
    formElimBtn.style.display = r ? '' : 'none';
    drawer.classList.add('open');
    document.getElementById('rf-nombre').focus();
  }

  function closeDrawer() { drawer.classList.remove('open'); editId = null; }

  drawerClose.addEventListener('click', closeDrawer);
  descartarBtn.addEventListener('click', closeDrawer);
  nuevoBtn.addEventListener('click', function () { openDrawer(null); });

  /* ── Save ── */
  guardarBtn.addEventListener('click', function () {
    var nombre = document.getElementById('rf-nombre').value.trim();
    if (!nombre) { showToast('El nombre es obligatorio.', 'error'); return; }
    var r = {
      nombre:   nombre,
      apellido: document.getElementById('rf-apellido').value.trim(),
      email:    document.getElementById('rf-email').value.trim(),
      telefono: document.getElementById('rf-telefono').value.trim(),
      codigo:   document.getElementById('rf-codigo').value.trim(),
      comision: document.getElementById('rf-comision').value,
      estado:   document.getElementById('rf-estado').value,
      notas:    document.getElementById('rf-notas').value.trim(),
    };
    if (editId) {
      var idx = referidos.findIndex(function (x) { return x._id === editId; });
      if (idx >= 0) { r._id = editId; r.fecha = referidos[idx].fecha || new Date().toISOString(); referidos[idx] = r; }
    } else {
      r._id = uid(); r.fecha = new Date().toISOString(); referidos.push(r);
    }
    save(); closeDrawer(); applyFilterSort();
    showToast(editId ? 'Referido actualizado.' : 'Referido agregado.', 'success');
  });

  /* ── Delete ── */
  function askDelete(ids, msg) { pendingDeleteIds = ids; confirmMsg.textContent = msg; confirm_.hidden = false; }

  confirmCancel.addEventListener('click', function () { confirm_.hidden = true; pendingDeleteIds = []; });
  confirmOk.addEventListener('click', function () {
    pendingDeleteIds.forEach(function (id) {
      referidos = referidos.filter(function (r) { return r._id !== id; });
      selected.delete(id);
    });
    confirm_.hidden = true; pendingDeleteIds = [];
    save(); closeDrawer(); applyFilterSort();
    showToast('Referido(s) eliminado(s).', 'success');
  });

  eliminarBtn.addEventListener('click', function () {
    if (!selected.size) return;
    askDelete(Array.from(selected), '¿Eliminar ' + selected.size + ' referido(s)? Esta acción no se puede deshacer.');
  });

  formElimBtn.addEventListener('click', function () {
    if (!editId) return;
    var r = referidos.find(function (x) { return x._id === editId; });
    askDelete([editId], '¿Eliminar "' + (r ? r.nombre : editId) + '"? Esta acción no se puede deshacer.');
  });

  /* ── Init ── */
  load(); applyFilterSort();
})();
</script>
</body>
</html>
"""
