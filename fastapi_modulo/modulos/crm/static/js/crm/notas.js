import { apiDelete, apiGet, apiPost } from './api.js';
import { bindDeleteButtons, createTableController, esc, formToObj, setStatus } from './ui.js';

export const createNotasModule = ({ root }) => {
  const loadNotas = async () => {
    setStatus('crm-notas-status', 'Cargando...');
    try {
      const rows = await apiGet('/api/crm/notas');
      setStatus('crm-notas-status', '');
      createTableController({
        mountId: 'crm-notas-list',
        rows,
        searchPlaceholder: 'Buscar nota o autor...',
        defaultSort: { key: 'creado_en', dir: 'desc' },
        filterDefs: [],
        columns: [
          { key: 'contenido', label: 'Nota', render: (v) => `<div class="crm-note-content">${esc(v)}</div>`, searchValue: (row) => `${row.contenido} ${row.autor}` },
          { key: 'autor', label: 'Autor', render: (v) => esc(v) },
          { key: 'creado_en', label: 'Fecha', render: (v) => esc((v || '').slice(0, 16).replace('T', ' ')) },
          {
            key: 'id',
            label: 'Acciones',
            render: (id) => `<button class="crm-btn-soft is-danger crm-btn-del-nota" data-id="${id}">Eliminar</button>`,
          },
        ],
      });
      bindDeleteButtons(root, '.crm-btn-del-nota', async (button) => {
        if (!confirm('¿Eliminar nota?')) return;
        try {
          await apiDelete(`/api/crm/notas/${button.dataset.id}`);
          await loadNotas();
        } catch (error) {
          alert(error.message);
        }
      });
    } catch (error) {
      setStatus('crm-notas-status', `Error: ${error.message}`, true);
    }
  };

  const initFormNota = () => {
    const form = document.getElementById('crm-form-nota');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      setStatus('crm-nota-form-status', 'Guardando...');
      try {
        const body = formToObj(form);
        if (body.contacto_id) body.contacto_id = parseInt(body.contacto_id, 10) || null;
        if (body.oportunidad_id) body.oportunidad_id = parseInt(body.oportunidad_id, 10) || null;
        await apiPost('/api/crm/notas', body);
        form.reset();
        setStatus('crm-nota-form-status', 'Nota guardada.');
        await loadNotas();
      } catch (error) {
        setStatus('crm-nota-form-status', `Error: ${error.message}`, true);
      }
    });
  };

  return { loadNotas, initFormNota };
};
