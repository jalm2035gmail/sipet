import { apiDelete, apiGet, apiPost, apiPut } from './api.js';
import { badge, closeModal, createTableController, esc, formToObj, openModal, setStatus } from './ui.js';

export const createCampaniasModule = ({ refreshResumen, state }) => {
  const openContactosModal = async (row) => {
    const relaciones = await apiGet(`/api/crm/campanias/${row.id}/contactos`);
    const available = (state?.contactos || []).filter((contacto) => !relaciones.some((item) => item.contacto_id === contacto.id));
    openModal(`
      <h3 class="crm-modal-title">Contactos en campaña</h3>
      <p class="crm-detail-subtitle"><strong>${esc(row.nombre)}</strong></p>
      <form class="crm-form" id="crm-modal-campania-contacto-form">
        <div class="crm-form-grid">
          <select name="contacto_id" required>
            <option value="">Seleccionar contacto</option>
            ${available.map((contacto) => `<option value="${contacto.id}">${esc(contacto.nombre)}</option>`).join('')}
          </select>
          <select name="estado">
            <option value="pendiente">Pendiente</option>
            <option value="contactado">Contactado</option>
            <option value="convertido">Convertido</option>
          </select>
        </div>
        <div class="crm-actions">
          <button type="submit">Agregar contacto</button>
        </div>
        <p class="crm-status" id="crm-modal-campania-contacto-status"></p>
      </form>
      <div class="crm-campania-contactos-list">
        ${relaciones.length ? relaciones.map((item) => {
          const contacto = (state?.contactos || []).find((rowContacto) => rowContacto.id === item.contacto_id);
          return `
            <div class="crm-dashboard-row">
              <span>${esc(contacto?.nombre || `Contacto ${item.contacto_id}`)} ${badge(item.estado)}</span>
              <button class="crm-btn-soft is-danger crm-btn-remove-campania-contacto" data-campania-id="${row.id}" data-contacto-id="${item.contacto_id}">Remover</button>
            </div>
          `;
        }).join('') : '<p class="crm-status">Sin contactos asociados.</p>'}
      </div>
    `);
    const form = document.getElementById('crm-modal-campania-contacto-form');
    form?.addEventListener('submit', async (event) => {
      event.preventDefault();
      setStatus('crm-modal-campania-contacto-status', 'Guardando...');
      try {
        const body = formToObj(form);
        body.contacto_id = parseInt(body.contacto_id, 10);
        body.campania_id = row.id;
        await apiPost('/api/crm/campanias/contactos', body);
        await loadCampanias();
        await refreshResumen();
        await openContactosModal(row);
      } catch (error) {
        setStatus('crm-modal-campania-contacto-status', `Error: ${error.message}`, true);
      }
    });
    document.querySelectorAll('.crm-btn-remove-campania-contacto').forEach((button) => {
      button.addEventListener('click', async () => {
        await apiDelete(`/api/crm/campanias/${button.dataset.campaniaId}/contactos/${button.dataset.contactoId}`);
        await loadCampanias();
        await refreshResumen();
        await openContactosModal(row);
      });
    });
  };

  const openEditModal = (row) => {
    openModal(`
      <h3 class="crm-modal-title">Editar campaña</h3>
      <form class="crm-form" id="crm-modal-campania-form">
        <div class="crm-form-grid">
          <input name="nombre" value="${esc(row.nombre)}" placeholder="Nombre *" required />
          <select name="tipo">
            <option value="email" ${row.tipo === 'email' ? 'selected' : ''}>Email</option>
            <option value="llamada" ${row.tipo === 'llamada' ? 'selected' : ''}>Llamada</option>
            <option value="evento" ${row.tipo === 'evento' ? 'selected' : ''}>Evento</option>
            <option value="promocion" ${row.tipo === 'promocion' ? 'selected' : ''}>Promoción</option>
          </select>
          <select name="estado">
            <option value="borrador" ${row.estado === 'borrador' ? 'selected' : ''}>Borrador</option>
            <option value="activa" ${row.estado === 'activa' ? 'selected' : ''}>Activa</option>
            <option value="finalizada" ${row.estado === 'finalizada' ? 'selected' : ''}>Finalizada</option>
          </select>
          <input name="fecha_inicio" type="date" value="${esc(row.fecha_inicio)}" />
          <input name="fecha_fin" type="date" value="${esc(row.fecha_fin)}" />
        </div>
        <textarea name="descripcion" placeholder="Descripción">${esc(row.descripcion)}</textarea>
        <div class="crm-actions">
          <button type="submit">Guardar cambios</button>
        </div>
        <p class="crm-status" id="crm-modal-campania-status"></p>
      </form>
    `);
    const form = document.getElementById('crm-modal-campania-form');
    form?.addEventListener('submit', async (event) => {
      event.preventDefault();
      setStatus('crm-modal-campania-status', 'Guardando...');
      try {
        await apiPut(`/api/crm/campanias/${row.id}`, formToObj(form));
        closeModal();
        await loadCampanias();
        await refreshResumen();
      } catch (error) {
        setStatus('crm-modal-campania-status', `Error: ${error.message}`, true);
      }
    });
  };

  const loadCampanias = async () => {
    setStatus('crm-campanias-status', 'Cargando...');
    try {
      const rows = await apiGet('/api/crm/campanias');
      setStatus('crm-campanias-status', '');
      createTableController({
        mountId: 'crm-campanias-table',
        rows,
        searchPlaceholder: 'Buscar campaña...',
        defaultSort: { key: 'fecha_inicio', dir: 'desc' },
        filterDefs: [
          {
            key: 'estado',
            label: 'Estado',
            getValue: (row) => row.estado,
            options: [...new Set(rows.map((row) => row.estado).filter(Boolean))].map((value) => ({ value, label: value })),
          },
        ],
        columns: [
          { key: 'nombre', label: 'Nombre', render: (v) => `<strong>${esc(v)}</strong>`, searchValue: (row) => `${row.nombre} ${row.descripcion}` },
          { key: 'tipo', label: 'Tipo', render: (v) => esc(v) },
          { key: 'estado', label: 'Estado', render: (v) => badge(v, 'is-strong') },
          { key: 'fecha_inicio', label: 'Inicio', render: (v) => esc(v) },
          { key: 'fecha_fin', label: 'Fin', render: (v) => esc(v) },
          { key: 'descripcion', label: 'Descripción', render: (v) => esc(v) },
          {
            key: 'id',
            label: 'Acciones',
            render: (id) => `
              <div class="crm-inline-actions">
                <button class="crm-btn-soft crm-btn-contactos-campania" data-id="${id}">Contactos</button>
                <button class="crm-btn-soft crm-btn-edit-campania" data-id="${id}">Editar</button>
              </div>
            `,
          },
        ],
      });
      document.querySelectorAll('.crm-btn-contactos-campania').forEach((button) => {
        button.addEventListener('click', async () => {
          const row = rows.find((item) => String(item.id) === String(button.dataset.id));
          if (row) await openContactosModal(row);
        });
      });
      document.querySelectorAll('.crm-btn-edit-campania').forEach((button) => {
        button.addEventListener('click', () => {
          const row = rows.find((item) => String(item.id) === String(button.dataset.id));
          if (row) openEditModal(row);
        });
      });
    } catch (error) {
      setStatus('crm-campanias-status', `Error: ${error.message}`, true);
    }
  };

  const initFormCampania = () => {
    const form = document.getElementById('crm-form-campania');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      setStatus('crm-campania-form-status', 'Guardando...');
      try {
        await apiPost('/api/crm/campanias', formToObj(form));
        form.reset();
        setStatus('crm-campania-form-status', 'Campaña creada.');
        await loadCampanias();
        await refreshResumen();
      } catch (error) {
        setStatus('crm-campania-form-status', `Error: ${error.message}`, true);
      }
    });
  };

  return { loadCampanias, initFormCampania };
};
