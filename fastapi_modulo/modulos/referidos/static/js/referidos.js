/* ── Referidos Module JS ──────────────────────────────────── */

function showToast(msg, type = 'success') {
  const el = document.getElementById('toastRef');
  const msgEl = document.getElementById('toastMsg');
  if (!el || !msgEl) return;
  msgEl.textContent = msg;
  el.className = `toast align-items-center text-white border-0 bg-${type}`;
  const t = new bootstrap.Toast(el, { delay: 3000 });
  t.show();
}

async function api(method, url, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

// ── Acciones directas (cualificar / pagar) ────────────────────────────────
async function accion(id, tipo) {
  const endpoints = {
    cualificar: `/api/referidos/${id}/cualificar`,
    pagar: `/api/referidos/${id}/pagar`,
  };
  try {
    await api('POST', endpoints[tipo]);
    showToast(`Referido ${tipo === 'cualificar' ? 'cualificado' : 'liquidado'} exitosamente.`);
    setTimeout(() => location.reload(), 1000);
  } catch (e) {
    showToast(e.message, 'danger');
  }
}

// ── Convertir ─────────────────────────────────────────────────────────────
function abrirConvertir(id) {
  document.getElementById('convertirId').value = id;
  new bootstrap.Modal(document.getElementById('modalConvertir')).show();
}

async function ejecutarConvertir(e) {
  e.preventDefault();
  const form = e.target;
  const id = form.referido_id.value;
  const body = {
    conversion_amount: parseFloat(form.conversion_amount.value) || null,
    product_acquired: form.product_acquired.value || null,
  };
  try {
    await api('POST', `/api/referidos/${id}/convertir`, body);
    showToast('Referido convertido exitosamente.');
    bootstrap.Modal.getInstance(document.getElementById('modalConvertir')).hide();
    setTimeout(() => location.reload(), 1000);
  } catch (e) {
    showToast(e.message, 'danger');
  }
}

// ── Rechazar ──────────────────────────────────────────────────────────────
function abrirRechazar(id) {
  document.getElementById('rechazarId').value = id;
  new bootstrap.Modal(document.getElementById('modalRechazar')).show();
}

async function ejecutarRechazar(e) {
  e.preventDefault();
  const form = e.target;
  const id = form.referido_id.value;
  try {
    await api('POST', `/api/referidos/${id}/rechazar`, { reason: form.reason.value || null });
    showToast('Referido rechazado.', 'warning');
    bootstrap.Modal.getInstance(document.getElementById('modalRechazar')).hide();
    setTimeout(() => location.reload(), 1000);
  } catch (e) {
    showToast(e.message, 'danger');
  }
}

// ── Crear Referente ───────────────────────────────────────────────────────
async function crearReferente(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api('POST', '/api/referidos/referentes', Object.fromEntries(fd));
    showToast('Referente creado con MIU generado.');
    bootstrap.Modal.getInstance(document.getElementById('modalNuevoReferente')).hide();
    setTimeout(() => location.reload(), 1000);
  } catch (e) {
    showToast(e.message, 'danger');
  }
}

// ── Crear Referido ────────────────────────────────────────────────────────
async function crearReferido(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = Object.fromEntries(fd);
  body.referente_id = parseInt(body.referente_id);
  if (body.program_assignment_id) {
    body.program_assignment_id = parseInt(body.program_assignment_id);
  } else {
    delete body.program_assignment_id;
  }
  try {
    await api('POST', '/api/referidos/crear', body);
    showToast('Referido creado exitosamente.');
    bootstrap.Modal.getInstance(document.getElementById('modalNuevoReferido')).hide();
    setTimeout(() => location.reload(), 1000);
  } catch (e) {
    showToast(e.message, 'danger');
  }
}

// ── Crear Incentivo ───────────────────────────────────────────────────────
async function crearIncentivo(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = Object.fromEntries(fd);
  body.percentage_value = parseFloat(body.percentage_value) || 0;
  body.fixed_value = parseFloat(body.fixed_value) || 0;
  body.max_amount = parseFloat(body.max_amount) || 0;
  try {
    await api('POST', '/api/referidos/incentivos', body);
    showToast('Incentivo creado exitosamente.');
    bootstrap.Modal.getInstance(document.getElementById('modalNuevoIncentivo')).hide();
    setTimeout(() => location.reload(), 1000);
  } catch (e) {
    showToast(e.message, 'danger');
  }
}

// ── Guardar Configuración ─────────────────────────────────────────────────
async function guardarConfig(e, crear = false) {
  if (e) e.preventDefault();
  const form = document.getElementById('formConfig');
  if (!form && !crear) return;
  const body = crear
    ? { name: 'Parámetros del Programa', is_active: true }
    : {
        name: form.name?.value,
        ca_description: form.ca_description?.value,
        scenario_type: form.scenario_type?.value,
        kpi_target: parseFloat(form.kpi_target?.value) || 0,
        validity_start: form.validity_start?.value || null,
        validity_end: form.validity_end?.value || null,
        use_whatsapp: form.use_whatsapp?.checked || false,
        use_email: form.use_email?.checked || false,
        whatsapp_webhook_url: form.whatsapp_webhook_url?.value || null,
      };
  try {
    await api('PUT', '/api/referidos/configuracion', body);
    showToast('Configuración guardada.');
    if (crear) setTimeout(() => location.reload(), 1000);
  } catch (e) {
    showToast(e.message, 'danger');
  }
}

async function guardarProgramaTienda(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = Object.fromEntries(fd);
  // user_id eliminado, se obtiene del usuario autenticado en backend
  body.max_referrals = parseInt(body.max_referrals || '0', 10);
  body.commission_rate = parseFloat(body.commission_rate || '0');
  try {
    await api('POST', '/api/referidos/programas', body);
    showToast('Tienda registrada en el programa de referidos.');
    setTimeout(() => location.reload(), 700);
  } catch (error) {
    showToast(error.message, 'danger');
  }
}

// ── Toggle campos de incentivo ────────────────────────────────────────────
function toggleIncentiveFields(sel) {
  const isPercent = sel.value === 'percent';
  const isFixed = sel.value === 'absolute';
  document.getElementById('fieldPercent')?.classList.toggle('d-none', !isPercent);
  document.getElementById('fieldFixed')?.classList.toggle('d-none', !isFixed);
}

function referidosApp() {
  return {
    init() {
      return null;
    },
  };
}
