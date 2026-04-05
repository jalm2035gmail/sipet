import { apiDelete, apiGet, apiPost, apiPut } from './api.js';
import {
  badge,
  bindDeleteButtons,
  closeModal,
  createTableController,
  esc,
  formToObj,
  openModal,
  renderTimeline,
  setStatus,
} from './ui.js';

// Columnas del kanban en orden lógico del embudo
const KANBAN_COLS = [
  { key: 'nuevo_lead',            label: 'Nuevo lead' },
  { key: 'por_contactar',         label: 'Por contactar' },
  { key: 'contactado',            label: 'Contactado' },
  { key: 'calificado',            label: 'Calificado' },
  { key: 'diagnostico',           label: 'Diagnóstico' },
  { key: 'negociacion',           label: 'Negociación' },
  { key: 'propuesta_enviada',     label: 'Propuesta enviada' },
  { key: 'seguimiento_propuesta', label: 'Seguimiento propuesta' },
  { key: 'decision',              label: 'Decisión' },
  { key: 'cerrado_ganado',        label: 'Ganado' },
  { key: 'cerrado_perdido',       label: 'Perdido' },
];

const SEMAFORO_COLOR = { verde: '#16a34a', amarillo: '#ca8a04', rojo: '#dc2626' };

export const createOportunidadesModule = ({ root, state, refreshResumen, refreshCatalogos }) => {
  // Estado de filtros del kanban
  let kanbanFilters = { ejecutivo: '', sucursal: '' };
  let allRows = [];

  const renderKanbanFilters = () => {
    const mount = document.getElementById('crm-kanban-filters');
    if (!mount) return;
    const ejecutivos = [...new Set(allRows.map((r) => r.responsable || r.asignado_a).filter(Boolean))].sort();
    const sucursales = [...new Set(allRows.map((r) => r.sucursal).filter(Boolean))].sort();
    mount.innerHTML = `
      <div class="crm-kanban-filter-bar">
        <select id="crm-kanban-fil-ejecutivo">
          <option value="">Todos los ejecutivos</option>
          ${ejecutivos.map((e) => `<option value="${esc(e)}" ${kanbanFilters.ejecutivo === e ? 'selected' : ''}>${esc(e)}</option>`).join('')}
        </select>
        <select id="crm-kanban-fil-sucursal">
          <option value="">Todas las sucursales</option>
          ${sucursales.map((s) => `<option value="${esc(s)}" ${kanbanFilters.sucursal === s ? 'selected' : ''}>${esc(s)}</option>`).join('')}
        </select>
      </div>
    `;
    document.getElementById('crm-kanban-fil-ejecutivo')?.addEventListener('change', (ev) => {
      kanbanFilters.ejecutivo = ev.target.value;
      renderKanban(allRows);
    });
    document.getElementById('crm-kanban-fil-sucursal')?.addEventListener('change', (ev) => {
      kanbanFilters.sucursal = ev.target.value;
      renderKanban(allRows);
    });
  };

  const renderKanban = (rows) => {
    const mount = document.getElementById('crm-oportunidades-kanban');
    if (!mount) return;

    let filtered = rows;
    if (kanbanFilters.ejecutivo)
      filtered = filtered.filter((r) => (r.responsable || r.asignado_a) === kanbanFilters.ejecutivo);
    if (kanbanFilters.sucursal)
      filtered = filtered.filter((r) => r.sucursal === kanbanFilters.sucursal);

    mount.innerHTML = `
      <div class="crm-kanban">
        ${KANBAN_COLS.map(({ key, label }) => {
          const cards = filtered.filter((r) => r.etapa === key);
          const monto = cards.reduce((sum, r) => sum + Number(r.valor_estimado || 0), 0);
          return `
            <section class="crm-kanban-col" data-kanban-stage="${esc(key)}" ondragover="event.preventDefault()" ondrop="window._crmKanbanDrop(event,'${esc(key)}')">
              <header class="crm-kanban-head">
                ${badge(key, 'is-strong')}
                <span class="crm-kanban-count">${cards.length}</span>
                <small class="crm-kanban-monto">$${monto.toLocaleString()}</small>
              </header>
              <div class="crm-kanban-list">
                ${cards.length ? cards.map((row) => {
                  const color = SEMAFORO_COLOR[row.semaforo] || '#94a3b8';
                  return `
                    <article class="crm-kanban-card" draggable="true" data-op-id="${row.id}"
                      ondragstart="window._crmKanbanDragStart(event,${row.id})">
                      <div class="crm-kanban-card-top">
                        <strong>${esc(row.nombre)}</strong>
                        <span class="crm-kanban-sema" title="Semáforo: ${esc(row.semaforo || 'verde')}" style="background:${color}"></span>
                      </div>
                      <span>${esc(row.contacto_nombre || 'Sin contacto')}</span>
                      <small>${esc((row.responsable || row.asignado_a || 'Sin responsable').trim())}</small>
                      <div class="crm-kanban-card-foot">
                        <b>$${Number(row.valor_estimado || 0).toLocaleString()}</b>
                        <em>${esc(row.probabilidad || 0)}%</em>
                      </div>
                    </article>
                  `;
                }).join('') : '<div class="crm-kanban-empty">—</div>'}
              </div>
            </section>
          `;
        }).join('')}
      </div>
    `;
  };

  const openEditModal = (row) => {
    openModal(`
      <h3 class="crm-modal-title">Editar oportunidad</h3>
      <form class="crm-form" id="crm-modal-oportunidad-form">
        <div class="crm-form-grid">
          <input name="nombre" value="${esc(row.nombre)}" placeholder="Nombre oportunidad *" required />
          <select name="etapa">
            ${KANBAN_COLS.map(({ key, label }) => `<option value="${esc(key)}" ${row.etapa === key ? 'selected' : ''}>${esc(label)}</option>`).join('')}
          </select>
          <input name="valor_estimado" type="number" step="0.01" min="0" value="${esc(row.valor_estimado)}" placeholder="Valor estimado" />
          <input name="probabilidad" type="number" min="0" max="100" value="${esc(row.probabilidad)}" placeholder="Probabilidad %" />
          <input name="fecha_cierre_est" type="date" value="${esc(row.fecha_cierre_est)}" />
          <input name="responsable" value="${esc(row.responsable)}" placeholder="Responsable" />
          <input name="sucursal" value="${esc(row.sucursal)}" placeholder="Sucursal" />
        </div>
        <textarea name="descripcion" placeholder="Descripción">${esc(row.descripcion)}</textarea>
        <div class="crm-actions">
          <button type="submit">Guardar cambios</button>
        </div>
        <p class="crm-status" id="crm-modal-oportunidad-status"></p>
      </form>
    `);
    const form = document.getElementById('crm-modal-oportunidad-form');
    form?.addEventListener('submit', async (event) => {
      event.preventDefault();
      setStatus('crm-modal-oportunidad-status', 'Guardando...');
      try {
        const body = formToObj(form);
        if (body.valor_estimado) body.valor_estimado = parseFloat(body.valor_estimado);
        if (body.probabilidad) body.probabilidad = parseInt(body.probabilidad, 10);
        await apiPut(`/api/crm/oportunidades/${row.id}`, body);
        closeModal();
        await loadOportunidades();
        await refreshResumen();
        await refreshCatalogos();
      } catch (error) {
        setStatus('crm-modal-oportunidad-status', `Error: ${error.message}`, true);
      }
    });
  };

  const openTimelineModal = async (row) => {
    openModal(`<p class="crm-status">Cargando timeline…</p>`);
    const [seguimiento, actividadesResp, notasResp] = await Promise.all([
      apiGet(`/api/crm/seguimiento?oportunidad_id=${row.id}`).catch(() => []),
      apiGet(`/api/crm/actividades?oportunidad_id=${row.id}`).catch(() => ({})),
      apiGet(`/api/crm/notas?oportunidad_id=${row.id}`).catch(() => []),
    ]);
    const actividades = Array.isArray(actividadesResp) ? actividadesResp : (actividadesResp.items || []);
    const notas = Array.isArray(notasResp) ? notasResp : (notasResp.items || []);
    const timelineItems = [
      ...(Array.isArray(seguimiento) ? seguimiento : []),
      ...actividades.map((a) => ({ tipo: 'actividad', detalle: `${a.tipo_actividad || 'Actividad'}: ${a.titulo || ''}`, fecha: a.fecha_actividad || a.creado_en, descripcion: a.descripcion || '', actor: a.responsable || '' })),
      ...notas.map((n) => ({ tipo: 'nota', detalle: n.titulo || 'Nota', fecha: n.creado_en, descripcion: n.contenido || '', actor: n.autor || '' })),
    ].sort((a, b) => new Date(b.fecha || 0) - new Date(a.fecha || 0));
    openModal(`
      <div class="crm-detail-head">
        <div>
          <h3 class="crm-modal-title">${esc(row.nombre)}</h3>
          <p class="crm-detail-subtitle">${badge(row.etapa)} ${esc(row.contacto_nombre)}</p>
        </div>
        <div class="crm-detail-score">${esc(`${row.probabilidad}%`)}</div>
      </div>
      <div class="crm-detail-grid">
        <div><strong>Valor</strong><span>$${Number(row.valor_estimado || 0).toLocaleString()}</span></div>
        <div><strong>Responsable</strong><span>${esc(row.responsable || 'Sin responsable')}</span></div>
        <div><strong>Sucursal</strong><span>${esc(row.sucursal || 'Sin sucursal')}</span></div>
        <div><strong>Últ. mov.</strong><span>${esc((row.ultimo_movimiento_en || '').slice(0, 16).replace('T', ' '))}</span></div>
      </div>
      <h4 class="crm-detail-title">Timeline de oportunidad</h4>
      ${renderTimeline(timelineItems)}
    `);
  };

  const loadOportunidades = async () => {
    setStatus('crm-oportunidades-status', 'Cargando...');
    try {
      const resp = await apiGet('/api/crm/oportunidades');
      const rows = Array.isArray(resp) ? resp : (resp.items || []);
      allRows = rows;
      state.oportunidades = rows;
      renderKanbanFilters();
      renderKanban(rows);

      // Drag & drop handlers expuestos globalmente para los event handlers inline
      window._crmKanbanDragStart = (ev, id) => ev.dataTransfer.setData('text/plain', String(id));
      window._crmKanbanDrop = async (ev, newStage) => {
        ev.preventDefault();
        const id = ev.dataTransfer.getData('text/plain');
        if (!id) return;
        const row = allRows.find((r) => String(r.id) === id);
        if (!row || row.etapa === newStage) return;
        try {
          await apiPut(`/api/crm/oportunidades/${id}`, { etapa: newStage, version: row.version });
          await loadOportunidades();
          await refreshResumen();
        } catch (err) {
          alert(`No se pudo mover la oportunidad: ${err.message}`);
        }
      };

      setStatus('crm-oportunidades-status', '');
      createTableController({
        mountId: 'crm-oportunidades-table',
        rows,
        searchPlaceholder: 'Buscar oportunidad, contacto, responsable...',
        defaultSort: { key: 'valor_estimado', dir: 'desc' },
        filterDefs: [
          {
            key: 'etapa',
            label: 'Etapa',
            getValue: (row) => row.etapa,
            options: [...new Set(rows.map((row) => row.etapa).filter(Boolean))].map((value) => ({ value, label: value })),
          },
          {
            key: 'sucursal',
            label: 'Sucursal',
            getValue: (row) => row.sucursal,
            options: [...new Set(rows.map((row) => row.sucursal).filter(Boolean))].map((value) => ({ value, label: value })),
          },
        ],
        columns: [
          { key: 'nombre', label: 'Oportunidad', render: (v) => `<strong>${esc(v)}</strong>`, searchValue: (row) => `${row.nombre} ${row.contacto_nombre} ${row.responsable}` },
          { key: 'contacto_nombre', label: 'Contacto', render: (v) => esc(v) },
          { key: 'etapa', label: 'Etapa', render: (v) => badge(v, 'is-strong') },
          { key: 'sucursal', label: 'Sucursal', render: (v) => esc(v) },
          { key: 'valor_estimado', label: 'Valor', render: (v) => `$${Number(v).toLocaleString()}`, sortValue: (row) => Number(row.valor_estimado || 0) },
          { key: 'probabilidad', label: '%', render: (v) => `${v}%`, sortValue: (row) => Number(row.probabilidad || 0) },
          { key: 'ultimo_movimiento_en', label: 'Últ. mov.', render: (v) => esc((v || '').slice(0, 16).replace('T', ' ')) },
          { key: 'responsable', label: 'Responsable', render: (v) => esc(v) },
          {
            key: 'id',
            label: 'Acciones',
            render: (id) => `
              <div class="crm-inline-actions">
                <button class="crm-btn-soft crm-btn-det-op" data-id="${id}">Timeline</button>
                <button class="crm-btn-soft crm-btn-edit-op" data-id="${id}">Editar</button>
                <button class="crm-btn-soft is-danger crm-btn-del-op" data-id="${id}">Eliminar</button>
              </div>
            `,
          },
        ],
      });

      bindDeleteButtons(root, '.crm-btn-det-op', async (button) => {
        const row = rows.find((item) => String(item.id) === String(button.dataset.id));
        if (row) await openTimelineModal(row);
      });
      bindDeleteButtons(root, '.crm-btn-edit-op', async (button) => {
        const row = rows.find((item) => String(item.id) === String(button.dataset.id));
        if (row) openEditModal(row);
      });
      bindDeleteButtons(root, '.crm-btn-del-op', async (button) => {
        if (!confirm('¿Eliminar oportunidad?')) return;
        try {
          await apiDelete(`/api/crm/oportunidades/${button.dataset.id}`);
          await loadOportunidades();
          await refreshResumen();
          await refreshCatalogos();
        } catch (error) {
          alert(error.message);
        }
      });
    } catch (error) {
      setStatus('crm-oportunidades-status', `Error: ${error.message}`, true);
    }
  };

  const initFormOportunidad = () => {
    const form = document.getElementById('crm-form-oportunidad');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      setStatus('crm-oportunidad-form-status', 'Guardando...');
      try {
        const body = formToObj(form);
        if (body.contacto_id) body.contacto_id = parseInt(body.contacto_id, 10);
        if (body.valor_estimado) body.valor_estimado = parseFloat(body.valor_estimado);
        if (body.probabilidad) body.probabilidad = parseInt(body.probabilidad, 10);
        await apiPost('/api/crm/oportunidades', body);
        form.reset();
        setStatus('crm-oportunidad-form-status', 'Oportunidad agregada.');
        await loadOportunidades();
        await refreshResumen();
        await refreshCatalogos();
      } catch (error) {
        setStatus('crm-oportunidad-form-status', `Error: ${error.message}`, true);
      }
    });
  };

  return { loadOportunidades, initFormOportunidad };
};
