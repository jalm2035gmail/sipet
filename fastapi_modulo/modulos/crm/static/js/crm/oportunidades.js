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

export const createOportunidadesModule = ({ root, state, refreshResumen, refreshCatalogos }) => {
  const renderKanban = (rows) => {
    const mount = document.getElementById('crm-oportunidades-kanban');
    if (!mount) return;
    const stages = ['prospecto', 'negociacion', 'propuesta', 'cerrado_ganado', 'cerrado_perdido'];
    mount.innerHTML = `
      <div class="crm-kanban">
        ${stages.map((stage) => {
          const cards = rows.filter((row) => row.etapa === stage);
          return `
            <section class="crm-kanban-col">
              <header class="crm-kanban-head">${badge(stage, 'is-strong')} <span>${cards.length}</span></header>
              <div class="crm-kanban-list">
                ${cards.length ? cards.map((row) => `
                  <article class="crm-kanban-card">
                    <strong>${esc(row.nombre)}</strong>
                    <span>${esc(row.contacto_nombre || 'Sin contacto')}</span>
                    <small>${esc(row.responsable || 'Sin responsable')}</small>
                    <b>$${Number(row.valor_estimado || 0).toLocaleString()}</b>
                  </article>
                `).join('') : '<div class="crm-kanban-empty">Sin oportunidades.</div>'}
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
            <option value="prospecto" ${row.etapa === 'prospecto' ? 'selected' : ''}>Prospecto</option>
            <option value="negociacion" ${row.etapa === 'negociacion' ? 'selected' : ''}>Negociación</option>
            <option value="propuesta" ${row.etapa === 'propuesta' ? 'selected' : ''}>Propuesta</option>
            <option value="cerrado_ganado" ${row.etapa === 'cerrado_ganado' ? 'selected' : ''}>Cerrado ganado</option>
            <option value="cerrado_perdido" ${row.etapa === 'cerrado_perdido' ? 'selected' : ''}>Cerrado perdido</option>
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
    const timeline = await apiGet(`/api/crm/seguimiento?oportunidad_id=${row.id}`);
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
        <div><strong>Último movimiento</strong><span>${esc((row.ultimo_movimiento_en || '').slice(0, 16).replace('T', ' '))}</span></div>
      </div>
      <h4 class="crm-detail-title">Timeline de oportunidad</h4>
      ${renderTimeline(timeline)}
    `);
  };

  const loadOportunidades = async () => {
    setStatus('crm-oportunidades-status', 'Cargando...');
    try {
      const rows = await apiGet('/api/crm/oportunidades');
      state.oportunidades = rows;
      renderKanban(rows);
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
