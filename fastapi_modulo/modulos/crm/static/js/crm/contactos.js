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

export const createContactosModule = ({ root, state, refreshResumen, refreshCatalogos }) => {
  const openEditModal = (row) => {
    openModal(`
      <h3 class="crm-modal-title">Editar contacto</h3>
      <form class="crm-form" id="crm-modal-contacto-form">
        <div class="crm-form-grid">
          <input name="nombre" value="${esc(row.nombre)}" placeholder="Nombre *" required />
          <input name="email" type="email" value="${esc(row.email)}" placeholder="Email" />
          <input name="telefono" value="${esc(row.telefono)}" placeholder="Teléfono" />
          <input name="empresa" value="${esc(row.empresa)}" placeholder="Empresa" />
          <input name="puesto" value="${esc(row.puesto)}" placeholder="Puesto" />
          <input name="sucursal" value="${esc(row.sucursal)}" placeholder="Sucursal" />
          <select name="tipo">
            <option value="prospecto" ${row.tipo === 'prospecto' ? 'selected' : ''}>Prospecto</option>
            <option value="cliente" ${row.tipo === 'cliente' ? 'selected' : ''}>Cliente</option>
            <option value="inactivo" ${row.tipo === 'inactivo' ? 'selected' : ''}>Inactivo</option>
          </select>
          <input name="fuente_detalle" value="${esc(row.fuente_detalle)}" placeholder="Origen detallado" />
        </div>
        <textarea name="notas" placeholder="Notas">${esc(row.notas)}</textarea>
        <div class="crm-actions">
          <button type="submit">Guardar cambios</button>
        </div>
        <p class="crm-status" id="crm-modal-contacto-status"></p>
      </form>
    `);
    const form = document.getElementById('crm-modal-contacto-form');
    form?.addEventListener('submit', async (event) => {
      event.preventDefault();
      setStatus('crm-modal-contacto-status', 'Guardando...');
      try {
        await apiPut(`/api/crm/contactos/${row.id}`, formToObj(form));
        closeModal();
        await loadContactos();
        await refreshResumen();
        await refreshCatalogos();
      } catch (error) {
        setStatus('crm-modal-contacto-status', `Error: ${error.message}`, true);
      }
    });
  };

  const openDetailModal = async (row) => {
    const timeline = await apiGet(`/api/crm/seguimiento?contacto_id=${row.id}`);
    openModal(`
      <div class="crm-detail-head">
        <div>
          <h3 class="crm-modal-title">${esc(row.nombre)}</h3>
          <p class="crm-detail-subtitle">${badge(row.tipo)} ${badge(row.fuente_detalle || row.fuente)}</p>
        </div>
        <div class="crm-detail-score">${esc(row.lead_score)}</div>
      </div>
      <div class="crm-detail-grid">
        <div><strong>Email</strong><span>${esc(row.email || 'Sin email')}</span></div>
        <div><strong>Teléfono</strong><span>${esc(row.telefono || 'Sin teléfono')}</span></div>
        <div><strong>Empresa</strong><span>${esc(row.empresa || 'Sin empresa')}</span></div>
        <div><strong>Sucursal</strong><span>${esc(row.sucursal || 'Sin sucursal')}</span></div>
      </div>
      <h4 class="crm-detail-title">Timeline del contacto</h4>
      ${renderTimeline(timeline)}
    `);
  };

  const loadContactos = async () => {
    setStatus('crm-contactos-status', 'Cargando...');
    try {
      const rows = await apiGet('/api/crm/contactos');
      state.contactos = rows;
      setStatus('crm-contactos-status', '');
      createTableController({
        mountId: 'crm-contactos-table',
        rows,
        searchPlaceholder: 'Buscar contacto, empresa, sucursal...',
        defaultSort: { key: 'lead_score', dir: 'desc' },
        filterDefs: [
          {
            key: 'tipo',
            label: 'Tipo',
            getValue: (row) => row.tipo,
            options: [...new Set(rows.map((row) => row.tipo).filter(Boolean))].map((value) => ({ value, label: value })),
          },
          {
            key: 'sucursal',
            label: 'Sucursal',
            getValue: (row) => row.sucursal,
            options: [...new Set(rows.map((row) => row.sucursal).filter(Boolean))].map((value) => ({ value, label: value })),
          },
        ],
        columns: [
          { key: 'nombre', label: 'Nombre', render: (v) => `<strong>${esc(v)}</strong>`, searchValue: (row) => `${row.nombre} ${row.empresa} ${row.sucursal}` },
          { key: 'email', label: 'Email', render: (v) => esc(v) },
          { key: 'empresa', label: 'Empresa', render: (v) => esc(v) },
          { key: 'sucursal', label: 'Sucursal', render: (v) => esc(v), sortValue: (row) => row.sucursal || '' },
          { key: 'tipo', label: 'Tipo', render: (v) => badge(v) },
          { key: 'fuente', label: 'Fuente', render: (v, row) => esc(row.fuente_detalle || v) },
          { key: 'lead_score', label: 'Score', render: (v) => `<strong>${esc(v)}</strong>`, sortValue: (row) => Number(row.lead_score || 0) },
          {
            key: 'id',
            label: 'Acciones',
            render: (id, row) => `
              <div class="crm-inline-actions">
                <button class="crm-btn-soft crm-btn-det-contacto" data-id="${id}">Detalle</button>
                <button class="crm-btn-soft crm-btn-edit-contacto" data-id="${id}">Editar</button>
                <button class="crm-btn-soft is-danger crm-btn-del-contacto" data-id="${id}">Eliminar</button>
              </div>
            `,
          },
        ],
      });

      bindDeleteButtons(root, '.crm-btn-det-contacto', async (button) => {
        const row = rows.find((item) => String(item.id) === String(button.dataset.id));
        if (row) await openDetailModal(row);
      });
      bindDeleteButtons(root, '.crm-btn-edit-contacto', async (button) => {
        const row = rows.find((item) => String(item.id) === String(button.dataset.id));
        if (row) openEditModal(row);
      });
      bindDeleteButtons(root, '.crm-btn-del-contacto', async (button) => {
        if (!confirm('¿Eliminar contacto?')) return;
        try {
          await apiDelete(`/api/crm/contactos/${button.dataset.id}`);
          await loadContactos();
          await refreshResumen();
          await refreshCatalogos();
        } catch (error) {
          alert(error.message);
        }
      });
    } catch (error) {
      setStatus('crm-contactos-status', `Error: ${error.message}`, true);
    }
  };

  const initFormContacto = () => {
    const form = document.getElementById('crm-form-contacto');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      setStatus('crm-contacto-form-status', 'Guardando...');
      try {
        await apiPost('/api/crm/contactos', formToObj(form));
        form.reset();
        setStatus('crm-contacto-form-status', 'Contacto agregado.');
        await loadContactos();
        await refreshResumen();
        await refreshCatalogos();
      } catch (error) {
        setStatus('crm-contacto-form-status', `Error: ${error.message}`, true);
      }
    });
  };

  return { loadContactos, initFormContacto };
};
