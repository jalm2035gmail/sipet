import { apiDelete, apiGet, apiPost, apiPut } from './api.js';
import { bindDeleteButtons, closeModal, createTableController, esc, formToObj, openModal, setStatus } from './ui.js';

export const createActividadesModule = ({ root, refreshResumen }) => {
  const openEditModal = (row) => {
    openModal(`
      <h3 class="crm-modal-title">Editar actividad</h3>
      <form class="crm-form" id="crm-modal-actividad-form">
        <div class="crm-form-grid">
          <input name="titulo" value="${esc(row.titulo)}" placeholder="Título *" required />
          <select name="tipo">
            <option value="tarea" ${row.tipo === 'tarea' ? 'selected' : ''}>Tarea</option>
            <option value="llamada" ${row.tipo === 'llamada' ? 'selected' : ''}>Llamada</option>
            <option value="reunion" ${row.tipo === 'reunion' ? 'selected' : ''}>Reunión</option>
            <option value="email" ${row.tipo === 'email' ? 'selected' : ''}>Email</option>
            <option value="visita" ${row.tipo === 'visita' ? 'selected' : ''}>Visita</option>
          </select>
          <input name="fecha" type="datetime-local" value="${esc((row.fecha || '').slice(0, 16))}" />
          <input name="responsable" value="${esc(row.responsable)}" placeholder="Responsable" />
        </div>
        <textarea name="descripcion" placeholder="Descripción">${esc(row.descripcion)}</textarea>
        <div class="crm-actions">
          <button type="submit">Guardar cambios</button>
        </div>
        <p class="crm-status" id="crm-modal-actividad-status"></p>
      </form>
    `);
    const form = document.getElementById('crm-modal-actividad-form');
    form?.addEventListener('submit', async (event) => {
      event.preventDefault();
      setStatus('crm-modal-actividad-status', 'Guardando...');
      try {
        await apiPut(`/api/crm/actividades/${row.id}`, formToObj(form));
        closeModal();
        await loadActividades();
        await refreshResumen();
      } catch (error) {
        setStatus('crm-modal-actividad-status', `Error: ${error.message}`, true);
      }
    });
  };

  const loadActividades = async () => {
    setStatus('crm-actividades-status', 'Cargando...');
    try {
      const rows = await apiGet('/api/crm/actividades?completada=false');
      const now = Date.now();
      const view = rows.map((row) => ({
        ...row,
        _rowClass: row.fecha && new Date(row.fecha).getTime() < now ? 'is-overdue' : '',
      }));
      setStatus('crm-actividades-status', '');
      createTableController({
        mountId: 'crm-actividades-table',
        rows: view,
        searchPlaceholder: 'Buscar actividad o responsable...',
        defaultSort: { key: 'fecha', dir: 'asc' },
        filterDefs: [
          {
            key: 'tipo',
            label: 'Tipo',
            getValue: (row) => row.tipo,
            options: [...new Set(view.map((row) => row.tipo).filter(Boolean))].map((value) => ({ value, label: value })),
          },
          {
            key: 'responsable',
            label: 'Responsable',
            getValue: (row) => row.responsable,
            options: [...new Set(view.map((row) => row.responsable).filter(Boolean))].map((value) => ({ value, label: value })),
          },
        ],
        columns: [
          { key: 'tipo', label: 'Tipo', render: (v) => esc(v) },
          { key: 'titulo', label: 'Título', render: (v) => `<strong>${esc(v)}</strong>`, searchValue: (row) => `${row.titulo} ${row.descripcion} ${row.responsable}` },
          {
            key: 'fecha',
            label: 'Fecha',
            render: (v, row) => `<span class="${row._rowClass ? 'crm-alert-date' : ''}">${esc((v || '').slice(0, 16).replace('T', ' '))}</span>`,
            sortValue: (row) => row.fecha || '',
          },
          { key: 'responsable', label: 'Responsable', render: (v) => esc(v) },
          {
            key: 'id',
            label: 'Acciones',
            render: (id) => `
              <div class="crm-inline-actions">
                <button class="crm-btn-soft crm-btn-edit-act" data-id="${id}">Editar</button>
                <button class="crm-btn-soft crm-btn-done-act" data-id="${id}">Completar</button>
                <button class="crm-btn-soft is-danger crm-btn-del-act" data-id="${id}">Eliminar</button>
              </div>
            `,
          },
        ],
      });

      bindDeleteButtons(root, '.crm-btn-edit-act', async (button) => {
        const row = view.find((item) => String(item.id) === String(button.dataset.id));
        if (row) openEditModal(row);
      });
      bindDeleteButtons(root, '.crm-btn-done-act', async (button) => {
        try {
          await apiPost(`/api/crm/actividades/${button.dataset.id}/completar`, {});
          await loadActividades();
          await refreshResumen();
        } catch (error) {
          alert(error.message);
        }
      });
      bindDeleteButtons(root, '.crm-btn-del-act', async (button) => {
        if (!confirm('¿Eliminar actividad?')) return;
        try {
          await apiDelete(`/api/crm/actividades/${button.dataset.id}`);
          await loadActividades();
          await refreshResumen();
        } catch (error) {
          alert(error.message);
        }
      });
    } catch (error) {
      setStatus('crm-actividades-status', `Error: ${error.message}`, true);
    }
  };

  const initFormActividad = () => {
    const form = document.getElementById('crm-form-actividad');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      setStatus('crm-actividad-form-status', 'Guardando...');
      try {
        const body = formToObj(form);
        if (body.contacto_id) body.contacto_id = parseInt(body.contacto_id, 10) || null;
        if (body.oportunidad_id) body.oportunidad_id = parseInt(body.oportunidad_id, 10) || null;
        await apiPost('/api/crm/actividades', body);
        form.reset();
        setStatus('crm-actividad-form-status', 'Actividad agregada.');
        await loadActividades();
        await refreshResumen();
      } catch (error) {
        setStatus('crm-actividad-form-status', `Error: ${error.message}`, true);
      }
    });
  };

  return { loadActividades, initFormActividad };
};
