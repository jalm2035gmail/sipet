import { apiGet } from './api.js';
import { esc, setStatus, setText } from './ui.js';
import { createActividadesModule } from './actividades.js';
import { createCampaniasModule } from './campanias.js';
import { createContactosModule } from './contactos.js';
import { createNotasModule } from './notas.js';
import { createOportunidadesModule } from './oportunidades.js';

const root = document.getElementById('crm-root');

if (root) {
  const state = {
    contactos: [],
    oportunidades: [],
  };

  const loadResumen = async () => {
    try {
      const data = await apiGet('/api/crm/resumen');
      setText('crm-kpi-contactos', data.total_contactos);
      setText('crm-kpi-oportunidades', data.oportunidades_abiertas);
      setText('crm-kpi-actividades', data.actividades_pendientes);
      setText('crm-kpi-campanias', data.campanias_activas);
      renderInsights(data);
    } catch (error) {
      console.error('CRM resumen:', error);
    }
  };

  const formatCurrency = (value) => `$${Number(value || 0).toLocaleString()}`;

  const renderList = (id, rows, renderRow) => {
    const mount = document.getElementById(id);
    if (!mount) return;
    if (!rows.length) {
      mount.innerHTML = '<div class="crm-dashboard-empty">Sin datos.</div>';
      return;
    }
    mount.innerHTML = rows.map(renderRow).join('');
  };

  const renderInsights = (data) => {
    setText('crm-insight-pipeline', formatCurrency(data.total_pipeline_monto));
    setText('crm-insight-forecast', `Forecast ${formatCurrency(data.forecast_periodo)} · Meta ${formatCurrency(data.meta_ventas_periodo)} · ${Number(data.avance_meta_ventas || 0).toFixed(2)}%`);

    renderList('crm-insight-monto-etapa', data.monto_por_etapa || [], (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.etapa)}</span>
        <strong>${formatCurrency(row.monto)}</strong>
      </div>
    `);

    renderList('crm-insight-conversion', [
      { label: 'Conversión prospecto a cliente', value: `${Number(data.tasa_conversion_prospecto_cliente || 0).toFixed(2)}%` },
      { label: 'Oportunidades ganadas', value: data.oportunidades_ganadas ?? 0 },
      { label: 'Oportunidades perdidas', value: data.oportunidades_perdidas ?? 0 },
      { label: 'Valor ganado del periodo', value: formatCurrency(data.valor_ganado_periodo) },
    ], (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.label)}</span>
        <strong>${esc(row.value)}</strong>
      </div>
    `);

    renderList('crm-insight-embudo', data.embudo_comercial || [], (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.etapa)}</span>
        <strong>${esc(row.total)}</strong>
      </div>
    `);

    renderList('crm-insight-actividades', [
      { label: 'Pendientes', value: data.actividades_pendientes ?? 0 },
      { label: 'Vencidas', value: data.actividades_vencidas ?? 0 },
      ...(data.actividades_por_responsable || []).slice(0, 3).map((row) => ({
        label: row.responsable,
        value: row.total,
      })),
    ], (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.label)}</span>
        <strong>${esc(row.value)}</strong>
      </div>
    `);

    renderList('crm-insight-comercial', (data.top_responsables_por_cierre || []).slice(0, 4), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.responsable)}</span>
        <strong>${esc(row.cierres)} / ${formatCurrency(row.monto)}</strong>
      </div>
    `);

    renderList('crm-insight-fuentes', (data.contactos_por_fuente || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.fuente)}</span>
        <strong>${esc(row.total)}</strong>
      </div>
    `);

    renderList('crm-insight-campanias', (data.campanias_por_efectividad || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.nombre)}</span>
        <strong>${esc(row.efectividad)}%</strong>
      </div>
    `);

    renderList('crm-insight-sucursales', (data.pipeline_por_sucursal || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.sucursal)}</span>
        <strong>${formatCurrency(row.monto)}</strong>
      </div>
    `);

    renderList('crm-insight-ejecutivos', (data.pipeline_por_ejecutivo || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.ejecutivo)}</span>
        <strong>${formatCurrency(row.monto)}</strong>
      </div>
    `);

    renderList('crm-insight-semaforo', (data.oportunidades_sin_movimiento || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.nombre)} <small>(${esc(row.semaforo)})</small></span>
        <strong>${esc(row.dias)} d</strong>
      </div>
    `);

    renderList('crm-insight-scoring', (data.scoring_leads || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.nombre)}</span>
        <strong>${esc(row.score)}</strong>
      </div>
    `);

    renderList('crm-insight-vencimientos', (data.proximos_vencimientos || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.titulo)}</span>
        <strong>${esc((row.fecha || '').slice(0, 16).replace('T', ' '))}</strong>
      </div>
    `);

    renderList('crm-insight-historial', (data.historial_cambios || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.descripcion)}</span>
        <strong>${esc((row.fecha || '').slice(0, 16).replace('T', ' '))}</strong>
      </div>
    `);

    renderList('crm-insight-asesor', (data.dashboard_por_asesor || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.asesor)}</span>
        <strong>${formatCurrency(row.pipeline)} / ${formatCurrency(row.ganado)}</strong>
      </div>
    `);

    renderList('crm-insight-dashboard-sucursal', (data.dashboard_por_sucursal || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.sucursal)}</span>
        <strong>${formatCurrency(row.pipeline)} / ${formatCurrency(row.ganado)}</strong>
      </div>
    `);

    renderList('crm-insight-dashboard-campania', (data.dashboard_por_campania || []).slice(0, 5), (row) => `
      <div class="crm-dashboard-row">
        <span>${esc(row.nombre)}</span>
        <strong>${esc(row.efectividad)}% / ${esc(row.tasa_cierre)}%</strong>
      </div>
    `);
  };

  const loadCatalogos = async () => {
    try {
      state.contactos = await apiGet('/api/crm/contactos');
      state.oportunidades = await apiGet('/api/crm/oportunidades');
      const contactoOpts = '<option value="">Contacto (opcional)</option>' +
        state.contactos.map((contacto) => `<option value="${contacto.id}">${contacto.nombre}</option>`).join('');
      const contactoOptsReq = '<option value="">Seleccionar contacto *</option>' +
        state.contactos.map((contacto) => `<option value="${contacto.id}">${contacto.nombre}</option>`).join('');
      const oportunidadOpts = '<option value="">Oportunidad (opcional)</option>' +
        state.oportunidades.map((oportunidad) => `<option value="${oportunidad.id}">${oportunidad.nombre}</option>`).join('');

      ['crm-op-contacto-select'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = contactoOptsReq;
      });
      ['crm-act-contacto-select', 'crm-nota-contacto-select'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = contactoOpts;
      });
      ['crm-act-op-select', 'crm-nota-op-select'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = oportunidadOpts;
      });
    } catch (_) {
      // silencioso
    }
  };

  const contactos = createContactosModule({
    root,
    state,
    refreshResumen: loadResumen,
    refreshCatalogos: loadCatalogos,
  });
  const oportunidades = createOportunidadesModule({
    root,
    state,
    refreshResumen: loadResumen,
    refreshCatalogos: loadCatalogos,
  });
  const actividades = createActividadesModule({
    root,
    refreshResumen: loadResumen,
  });
  const notas = createNotasModule({ root });
  const campanias = createCampaniasModule({ refreshResumen: loadResumen, state });

  const initNav = () => {
    const buttons = Array.from(root.querySelectorAll('#crm-nav button'));
    const panels = Array.from(root.querySelectorAll('[data-panel-id]'));
    buttons.forEach((button) => {
      button.addEventListener('click', async () => {
        const target = button.dataset.panel;
        buttons.forEach((candidate) => candidate.classList.toggle('is-active', candidate === button));
        panels.forEach((panel) => panel.classList.toggle('is-active', panel.dataset.panelId === target));
        if (target === 'oportunidades') await oportunidades.loadOportunidades();
        if (target === 'actividades') await actividades.loadActividades();
        if (target === 'notas') await notas.loadNotas();
        if (target === 'campanias') await campanias.loadCampanias();
      });
    });
  };

  const init = async () => {
    initNav();
    contactos.initFormContacto();
    oportunidades.initFormOportunidad();
    actividades.initFormActividad();
    notas.initFormNota();
    campanias.initFormCampania();
    await loadResumen();
    await loadCatalogos();
    await contactos.loadContactos();
  };

  init().catch((error) => {
    setStatus('crm-contactos-status', `Error: ${error.message}`, true);
  });
}
