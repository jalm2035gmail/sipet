export const setText = (id, text) => {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
};

export const setStatus = (id, text, isError = false) => {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.style.color = isError ? '#dc2626' : '#64748b';
};

export const badge = (value, extra = '') => {
  const cls = (value || '').toLowerCase().replace(/\s+/g, '_');
  return `<span class="crm-badge ${cls} ${extra}">${value || ''}</span>`;
};

export const esc = (value) =>
  String(value ?? '').replace(/[&<>"']/g, (char) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]
  ));

export const formToObj = (form) => {
  const obj = {};
  new FormData(form).forEach((value, key) => {
    obj[key] = value === '' ? null : value;
  });
  return obj;
};

export const bindDeleteButtons = (root, selector, handler) => {
  root.querySelectorAll(selector).forEach((button) => {
    button.addEventListener('click', () => handler(button));
  });
};

export const createTableController = ({
  mountId,
  columns,
  rows,
  emptyMsg = 'Sin datos todavía.',
  searchPlaceholder = 'Buscar...',
  defaultSort = null,
  filterDefs = [],
}) => {
  const mount = document.getElementById(mountId);
  if (!mount) return { refresh: () => {} };

  const state = {
    query: '',
    sortKey: defaultSort?.key || null,
    sortDir: defaultSort?.dir || 'asc',
    filters: Object.fromEntries(filterDefs.map((item) => [item.key, ''])),
  };

  const serialize = (row, column) => {
    if (column.searchValue) return String(column.searchValue(row) ?? '').toLowerCase();
    return String(row[column.key] ?? '').toLowerCase();
  };

  const compare = (left, right) => {
    if (left === right) return 0;
    if (left == null) return -1;
    if (right == null) return 1;
    if (!Number.isNaN(Number(left)) && !Number.isNaN(Number(right)) && left !== '' && right !== '') {
      return Number(left) - Number(right);
    }
    return String(left).localeCompare(String(right), 'es', { numeric: true, sensitivity: 'base' });
  };

  const applyState = () => {
    let view = [...rows];
    if (state.query) {
      const query = state.query.toLowerCase();
      view = view.filter((row) => columns.some((column) => serialize(row, column).includes(query)));
    }
    filterDefs.forEach((filterDef) => {
      const value = state.filters[filterDef.key];
      if (!value) return;
      view = view.filter((row) => String(filterDef.getValue(row) ?? '') === value);
    });
    if (state.sortKey) {
      const column = columns.find((item) => item.key === state.sortKey);
      if (column) {
        view.sort((a, b) => {
          const result = compare(
            column.sortValue ? column.sortValue(a) : a[column.key],
            column.sortValue ? column.sortValue(b) : b[column.key],
          );
          return state.sortDir === 'asc' ? result : -result;
        });
      }
    }
    return view;
  };

  const render = () => {
    const filtered = applyState();
    const toolbar = `
      <div class="crm-table-tools">
        <input class="crm-table-search" data-role="search" placeholder="${esc(searchPlaceholder)}" value="${esc(state.query)}" />
        ${filterDefs.map((filterDef) => `
          <select class="crm-table-filter" data-filter-key="${esc(filterDef.key)}">
            <option value="">${esc(filterDef.label)}</option>
            ${filterDef.options.map((option) => `
              <option value="${esc(option.value)}" ${String(state.filters[filterDef.key]) === String(option.value) ? 'selected' : ''}>${esc(option.label)}</option>
            `).join('')}
          </select>
        `).join('')}
      </div>
    `;
    if (!filtered.length) {
      mount.innerHTML = `${toolbar}<p class="crm-status">${emptyMsg}</p>`;
      attachHandlers();
      return;
    }
    const head = columns.map((column) => {
      const active = state.sortKey === column.key;
      const dir = active ? state.sortDir : '';
      return `
        <th>
          <button class="crm-sort-btn ${active ? 'is-active' : ''}" data-sort-key="${esc(column.key)}">
            ${esc(column.label)}${dir === 'asc' ? ' ↑' : dir === 'desc' ? ' ↓' : ''}
          </button>
        </th>
      `;
    }).join('');
    const body = filtered.map((row) => {
      const rowClass = row._rowClass ? esc(row._rowClass) : '';
      const cols = columns.map((column) => (
        `<td>${column.render ? column.render(row[column.key], row) : esc(row[column.key])}</td>`
      )).join('');
      return `<tr class="${rowClass}">${cols}</tr>`;
    }).join('');
    mount.innerHTML = `${toolbar}<div class="crm-table-wrap"><table class="crm-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
    attachHandlers();
  };

  const attachHandlers = () => {
    const search = mount.querySelector('[data-role="search"]');
    if (search) {
      search.addEventListener('input', (event) => {
        state.query = event.target.value || '';
        render();
      });
    }
    mount.querySelectorAll('[data-filter-key]').forEach((select) => {
      select.addEventListener('change', (event) => {
        state.filters[event.target.dataset.filterKey] = event.target.value || '';
        render();
      });
    });
    mount.querySelectorAll('[data-sort-key]').forEach((button) => {
      button.addEventListener('click', () => {
        const nextKey = button.dataset.sortKey;
        if (state.sortKey === nextKey) {
          state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          state.sortKey = nextKey;
          state.sortDir = 'asc';
        }
        render();
      });
    });
  };

  render();
  return { refresh: render };
};

export const ensureModal = () => {
  let modal = document.getElementById('crm-modal');
  if (modal) return modal;
  modal = document.createElement('div');
  modal.id = 'crm-modal';
  modal.className = 'crm-modal';
  modal.innerHTML = `
    <div class="crm-modal-backdrop" data-close="1"></div>
    <div class="crm-modal-card">
      <button class="crm-modal-close" data-close="1">✕</button>
      <div class="crm-modal-body"></div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', (event) => {
    if (event.target.dataset.close) closeModal();
  });
  return modal;
};

export const openModal = (html) => {
  const modal = ensureModal();
  modal.querySelector('.crm-modal-body').innerHTML = html;
  modal.classList.add('is-open');
};

export const closeModal = () => {
  const modal = document.getElementById('crm-modal');
  if (modal) modal.classList.remove('is-open');
};

export const renderTimeline = (items) => {
  if (!items.length) {
    return '<div class="crm-timeline-empty">Sin seguimiento.</div>';
  }
  return `
    <div class="crm-timeline">
      ${items.map((item) => `
        <article class="crm-timeline-item">
          <div class="crm-timeline-dot ${esc(item.tipo)}"></div>
          <div class="crm-timeline-content">
            <div class="crm-timeline-meta">
              <strong>${esc(item.detalle || item.tipo)}</strong>
              <span>${esc((item.fecha || '').slice(0, 16).replace('T', ' '))}</span>
            </div>
            <p>${esc(item.descripcion)}</p>
            <small>${esc(item.actor || '')}</small>
          </div>
        </article>
      `).join('')}
    </div>
  `;
};
