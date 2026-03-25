(function () {
  const root = document.getElementById('intelicoop-root');
  if (!root) return;
  if (root.dataset.booted === '1') return;
  root.dataset.booted = '1';

  const apiGet = async (url) => {
    const res = await fetch(url, { credentials: 'same-origin' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  };

  const apiPost = async (url, body) => {
    const res = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || data.error || `HTTP ${res.status}`);
    }
    return res.json();
  };

  const apiPostForm = async (url, formData) => {
    const res = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      body: formData,
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || data.error || `HTTP ${res.status}`);
    }
    return res.json();
  };

  const setStatus = (id, text) => {
    const node = document.getElementById(id);
    if (node) node.textContent = text;
  };

  const renderTable = (mountId, columns, rows) => {
    const mount = document.getElementById(mountId);
    if (!mount) return;
    if (!rows.length) {
      mount.innerHTML = '<p class="intelicoop-status">Sin datos todavia.</p>';
      return;
    }
    const head = columns.map((col) => `<th>${col.label}</th>`).join('');
    const body = rows.map((row) => {
      const cols = columns.map((col) => `<td>${row[col.key] ?? ''}</td>`).join('');
      return `<tr>${cols}</tr>`;
    }).join('');
    mount.innerHTML = `<table class="intelicoop-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  };

  const updateTabs = () => {
    const buttons = Array.from(document.querySelectorAll('#intelicoop-nav button'));
    const panels = Array.from(document.querySelectorAll('[data-panel-id]'));
    const activatePanel = (target) => {
      buttons.forEach((item) => item.classList.toggle('is-active', item.getAttribute('data-panel') === target));
      panels.forEach((panel) => panel.classList.toggle('is-active', panel.getAttribute('data-panel-id') === target));
    };
    buttons.forEach((button) => {
      button.addEventListener('click', () => {
        const target = button.getAttribute('data-panel');
        activatePanel(target);
      });
    });
    return activatePanel;
  };

  const bindImportShortcut = (activatePanel) => {
    const importLink = document.querySelector('a[href="#intelicoop-creditos-import-form"]');
    const importForm = document.getElementById('intelicoop-creditos-import-form');
    if (!importLink || !importForm || typeof activatePanel !== 'function') return;

    const openImportSection = () => {
      activatePanel('creditos');
      requestAnimationFrame(() => {
        importForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    };

    importLink.addEventListener('click', (event) => {
      event.preventDefault();
      if (window.location.hash !== '#intelicoop-creditos-import-form') {
        history.replaceState(null, '', '#intelicoop-creditos-import-form');
      }
      openImportSection();
    });

    if (window.location.hash === '#intelicoop-creditos-import-form') {
      openImportSection();
    }
  };

  const bindDeleteDataAction = () => {
    const button = document.getElementById('intelicoop-delete-data');
    if (!button) return;
    button.addEventListener('click', async () => {
      const firstConfirm = window.confirm('Esto eliminara todos los datos de Intelicoop. Esta accion no se puede deshacer. Deseas continuar?');
      if (!firstConfirm) return;
      const typed = window.prompt('Escribe exactamente ELIMINAR INTELICOOP para confirmar.');
      if (typed !== 'ELIMINAR INTELICOOP') {
        setFormResult('intelicoop-governance-result', 'Eliminacion cancelada. Confirmacion invalida.', true);
        return;
      }
      setFormResult('intelicoop-governance-result', 'Eliminando datos de Intelicoop...', false);
      try {
        const data = await apiPost('/api/intelicoop/datos/eliminar', { confirmation: typed });
        setFormResult(
          'intelicoop-governance-result',
          `Datos eliminados. Tablas: ${data.deleted_tables || 0}. Registros: ${data.deleted_rows || 0}.`,
          false
        );
        await Promise.all([
          loadCatalogs(),
          loadKpis(),
          loadDashboard(),
          loadSocios(),
          loadCreditos(),
          loadAhorros(),
          loadCampanas(),
          loadProspectos(),
          loadScoring(),
          loadSegmentacion(),
          loadFoundation(),
          loadBatch(),
          loadGovernance(),
        ]);
      } catch (error) {
        setFormResult('intelicoop-governance-result', `No se pudieron eliminar los datos: ${error.message}`, true);
      }
    });
  };

  const setFormResult = (id, text, isError) => {
    const node = document.getElementById(id);
    if (!node) return;
    node.innerHTML = `<p class="intelicoop-status" style="color:${isError ? '#991b1b' : '#0f766e'};">${text}</p>`;
  };

  const loadCatalogs = async () => {
    const [data, creditos, campanias] = await Promise.all([
      apiGet('/api/intelicoop/catalogos/basicos'),
      apiGet('/api/intelicoop/creditos'),
      apiGet('/api/intelicoop/campanas'),
    ]);
    const socioSelect = document.getElementById('intelicoop-credito-socio');
    const cuentaSocioSelect = document.getElementById('intelicoop-cuenta-socio');
    const cuentaSelect = document.getElementById('intelicoop-transaccion-cuenta');
    const pagoCreditoSelect = document.getElementById('intelicoop-pago-credito');
    const contactoSocioSelect = document.getElementById('intelicoop-contacto-socio');
    const seguimientoSocioSelect = document.getElementById('intelicoop-seguimiento-socio');
    const socioOptions = '<option value="">Selecciona un socio</option>' + (data.socios || []).map((row) => (
      `<option value="${row.id}">${row.nombre} (#${row.id})</option>`
    )).join('');
    if (socioSelect) {
      const current = socioSelect.value;
      socioSelect.innerHTML = socioOptions;
      if (current) socioSelect.value = current;
    }
    if (cuentaSocioSelect) {
      const current = cuentaSocioSelect.value;
      cuentaSocioSelect.innerHTML = socioOptions;
      if (current) cuentaSocioSelect.value = current;
    }
    if (cuentaSelect) {
      const current = cuentaSelect.value;
      cuentaSelect.innerHTML = '<option value="">Selecciona una cuenta</option>' + (data.cuentas || []).map((row) => (
        `<option value="${row.id}">Cuenta #${row.id} / Socio #${row.socio_id} / ${row.tipo}</option>`
      )).join('');
      if (current) cuentaSelect.value = current;
    }
    if (pagoCreditoSelect) {
      const current = pagoCreditoSelect.value;
      pagoCreditoSelect.innerHTML = '<option value="">Selecciona un credito</option>' + (creditos || []).map((row) => (
        `<option value="${row.id}">Credito #${row.id} / ${row.socio_nombre || 'Sin socio'}</option>`
      )).join('');
      if (current) pagoCreditoSelect.value = current;
    }
    if (contactoSocioSelect) {
      const current = contactoSocioSelect.value;
      contactoSocioSelect.innerHTML = socioOptions;
      if (current) contactoSocioSelect.value = current;
    }
    if (seguimientoSocioSelect) {
      const current = seguimientoSocioSelect.value;
      seguimientoSocioSelect.innerHTML = socioOptions;
      if (current) seguimientoSocioSelect.value = current;
    }
    const campaniaOptions = '<option value="">Selecciona una campana</option>' + (campanias || []).map((row) => (
      `<option value="${row.id}">${row.nombre} (#${row.id})</option>`
    )).join('');
    const contactoCampaniaSelect = document.getElementById('intelicoop-contacto-campania');
    const seguimientoCampaniaSelect = document.getElementById('intelicoop-seguimiento-campania');
    if (contactoCampaniaSelect) {
      const current = contactoCampaniaSelect.value;
      contactoCampaniaSelect.innerHTML = campaniaOptions;
      if (current) contactoCampaniaSelect.value = current;
    }
    if (seguimientoCampaniaSelect) {
      const current = seguimientoCampaniaSelect.value;
      seguimientoCampaniaSelect.innerHTML = campaniaOptions;
      if (current) seguimientoCampaniaSelect.value = current;
    }
  };

  const loadKpis = async () => {
    const data = await apiGet('/api/intelicoop/dashboard/resumen');
    const kpis = document.getElementById('intelicoop-kpis');
    if (!kpis) return;
    kpis.innerHTML = [
      ['Socios', data.socios || 0],
      ['Creditos', data.creditos || 0],
      ['Campanas', data.campanas || 0],
      ['Scoring', data.scoring_total || 0],
    ].map(([label, value]) => (
      `<article class="intelicoop-card"><span class="intelicoop-kpi-label">${label}</span><strong class="intelicoop-kpi-value">${value}</strong></article>`
    )).join('');
  };

  const loadDashboard = async () => {
    setStatus('intelicoop-dashboard-status', 'Cargando resumen del modulo...');
    const data = await apiGet('/api/intelicoop/dashboard/resumen');
    const mount = document.getElementById('intelicoop-dashboard-content');
    if (mount) {
      const semaforoBadge = (value) => {
        const palette = {
          verde: '#166534',
          amarillo: '#a16207',
          rojo: '#991b1b',
        };
        const bg = {
          verde: '#dcfce7',
          amarillo: '#fef3c7',
          rojo: '#fee2e2',
        };
        const color = palette[value] || '#334155';
        const background = bg[value] || '#e2e8f0';
        return `<span style="display:inline-flex;padding:4px 8px;border-radius:999px;background:${background};color:${color};font-size:12px;font-weight:700;text-transform:uppercase;">${value}</span>`;
      };
      mount.innerHTML = `
        <div class="intelicoop-grid">
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Prospectos</span><strong class="intelicoop-kpi-value">${data.prospectos || 0}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Riesgo bajo</span><strong class="intelicoop-kpi-value">${(data.riesgo || {}).bajo || 0}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Riesgo medio</span><strong class="intelicoop-kpi-value">${(data.riesgo || {}).medio || 0}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Riesgo alto</span><strong class="intelicoop-kpi-value">${(data.riesgo || {}).alto || 0}</strong></article>
        </div>
        <div class="intelicoop-grid" style="margin-top:16px;">
          <article class="intelicoop-card">
            <span class="intelicoop-kpi-label">Salud de cartera</span>
            <p style="margin:0 0 8px;">Cartera total: $${Number((data.salud_cartera || {}).cartera_total || 0).toFixed(2)}</p>
            <p style="margin:0 0 8px;">Cartera vigente: $${Number((data.salud_cartera || {}).cartera_vigente || 0).toFixed(2)}</p>
            <p style="margin:0;">IMOR estimado: ${Number((data.salud_cartera || {}).imor_pct || 0).toFixed(2)}%</p>
          </article>
          <article class="intelicoop-card">
            <span class="intelicoop-kpi-label">Colocacion</span>
            <p style="margin:0 0 8px;">Solicitados: ${(data.colocacion || {}).solicitados || 0}</p>
            <p style="margin:0 0 8px;">Aprobados: ${(data.colocacion || {}).aprobados || 0}</p>
            <p style="margin:0;">Ticket promedio: $${Number((data.colocacion || {}).ticket_promedio || 0).toFixed(2)}</p>
          </article>
          <article class="intelicoop-card">
            <span class="intelicoop-kpi-label">Captacion</span>
            <p style="margin:0 0 8px;">Depositos: $${Number((data.captacion || {}).depositos_total || 0).toFixed(2)}</p>
            <p style="margin:0 0 8px;">Retiros: $${Number((data.captacion || {}).retiros_total || 0).toFixed(2)}</p>
            <p style="margin:0;">Neta: $${Number((data.captacion || {}).captacion_neta || 0).toFixed(2)}</p>
          </article>
          <article class="intelicoop-card">
            <span class="intelicoop-kpi-label">Comercial</span>
            <p style="margin:0 0 8px;">Campanas activas: ${(data.comercial || {}).campanas_activas || 0}</p>
            <p style="margin:0 0 8px;">Prospectos: ${(data.comercial || {}).prospectos_total || 0}</p>
            <p style="margin:0 0 8px;">Contactos: ${(data.comercial || {}).contactos_total || 0}</p>
            <p style="margin:0 0 8px;">Conversiones: ${(data.comercial || {}).conversiones_total || 0}</p>
            <p style="margin:0;">Conversion %: ${Number((data.comercial || {}).conversion_pct || 0).toFixed(2)}%</p>
          </article>
          <article class="intelicoop-card">
            <span class="intelicoop-kpi-label">Segmentacion</span>
            <p style="margin:0 0 8px;">Segmentos activos: ${(data.segmentacion || {}).segmentos_total || 0}</p>
            <p style="margin:0 0 8px;">Oportunidades: ${(data.segmentacion || {}).oportunidades_comerciales || 0}</p>
            <p style="margin:0 0 8px;">Alertas tempranas: ${(data.segmentacion || {}).alertas_tempranas || 0}</p>
            <p style="margin:0;">Abandono alto: ${(data.segmentacion || {}).abandono_alto || 0}</p>
          </article>
        </div>
        <div class="intelicoop-card" style="margin-top:16px;">
          <span class="intelicoop-kpi-label">Semaforos</span>
          <div class="intelicoop-grid">
            ${(data.semaforos || []).map((item) => `
              <div style="border:1px solid rgba(15,23,42,.08);border-radius:12px;padding:12px;background:#fff;">
                <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;">
                  <strong>${item.label}</strong>
                  ${semaforoBadge(item.semaforo)}
                </div>
                <p style="margin:8px 0 0;">Valor: ${item.valor}</p>
                <p style="margin:4px 0 0;">Meta: ${item.meta}</p>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }
    setStatus('intelicoop-dashboard-status', 'Modulo conectado al backend principal de SIPET.');
  };

  const loadSocios = async () => {
    setStatus('intelicoop-socios-status', 'Cargando socios...');
    const rows = await apiGet('/api/intelicoop/socios');
    renderTable('intelicoop-socios-table', [
      { key: 'id', label: 'ID' },
      { key: 'nombre', label: 'Nombre' },
      { key: 'email', label: 'Email' },
      { key: 'edad', label: 'Edad' },
      { key: 'ocupacion', label: 'Ocupacion' },
      { key: 'tipo_socio', label: 'Tipo socio' },
      { key: 'segmento', label: 'Segmento' },
    ], rows);
    setStatus('intelicoop-socios-status', `${rows.length} socios cargados.`);
  };

  const loadCreditos = async () => {
    setStatus('intelicoop-creditos-status', 'Cargando creditos...');
    const rows = await apiGet('/api/intelicoop/creditos');
    const mount = document.getElementById('intelicoop-creditos-table');
    if (!mount) return;
    if (!rows.length) {
      mount.innerHTML = '<p class="intelicoop-status">Sin datos todavia.</p>';
    } else {
      const head = ['ID', 'Socio', 'Monto', 'Estado', 'Acciones'].map((label) => `<th>${label}</th>`).join('');
      const body = rows.map((row) => `
        <tr>
          <td>${row.id ?? ''}</td>
          <td>${row.socio_nombre ?? ''}</td>
          <td>${row.monto ?? ''}</td>
          <td>${row.estado ?? ''}</td>
          <td><button type="button" class="intelicoop-detail-credito" data-credito-id="${row.id}">Ver detalle</button></td>
        </tr>
      `).join('');
      mount.innerHTML = `<table class="intelicoop-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
      mount.querySelectorAll('.intelicoop-detail-credito').forEach((button) => {
        button.addEventListener('click', () => {
          const creditoId = Number(button.getAttribute('data-credito-id'));
          loadCreditoDetail(creditoId).catch(() => {});
        });
      });
    }
    setStatus('intelicoop-creditos-status', `${rows.length} creditos cargados.`);
  };

  const loadCreditoDetail = async (creditoId) => {
    const statusNode = document.getElementById('intelicoop-credito-detail-status');
    const mount = document.getElementById('intelicoop-credito-detail');
    if (statusNode) statusNode.textContent = 'Cargando detalle del credito...';
    const data = await apiGet(`/api/intelicoop/creditos/${creditoId}/detalle`);
    if (mount) {
      const pagos = data.historial_pagos || [];
      mount.innerHTML = `
        <div class="intelicoop-grid">
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Credito</span><strong class="intelicoop-kpi-value">#${data.id}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Monto</span><strong class="intelicoop-kpi-value">$${Number(data.monto || 0).toFixed(2)}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Abonos</span><strong class="intelicoop-kpi-value">${Number(data.numero_abonos || 0)}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Periodicidad</span><strong class="intelicoop-kpi-value">${data.periodicidad || 'mensual'}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Tasa</span><strong class="intelicoop-kpi-value">${Number(data.tasa || 0).toFixed(2)}%</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Mora actual</span><strong class="intelicoop-kpi-value">${Number(data.dias_mora_actual || 0)}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Pagado</span><strong class="intelicoop-kpi-value">$${Number((data.resumen_pagos || {}).monto_pagado || 0).toFixed(2)}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Saldo estimado</span><strong class="intelicoop-kpi-value">$${Number((data.resumen_pagos || {}).saldo_estimado || 0).toFixed(2)}</strong></article>
        </div>
      `;
      if (pagos.length) {
        mount.innerHTML += `
          <div style="margin-top:16px;">
            <h4>Historial de pagos</h4>
            <table class="intelicoop-table">
              <thead><tr><th>ID</th><th>Monto</th><th>Puntual</th><th>Dias atraso</th><th>Fecha</th></tr></thead>
              <tbody>
                ${pagos.map((row) => `<tr><td>${row.id}</td><td>${row.monto}</td><td>${row.pago_puntual ? 'Si' : 'No'}</td><td>${row.dias_atraso ?? 0}</td><td>${(row.fecha || '').slice(0, 19)}</td></tr>`).join('')}
              </tbody>
            </table>
          </div>
        `;
      }
    }
    if (statusNode) statusNode.textContent = `Detalle del credito #${data.id}.`;
    const pagoCreditoSelect = document.getElementById('intelicoop-pago-credito');
    if (pagoCreditoSelect) pagoCreditoSelect.value = String(data.id);
  };

  const loadAhorros = async () => {
    setStatus('intelicoop-ahorros-status', 'Cargando resumen de ahorros...');
    const [data, cuentas, movimientos] = await Promise.all([
      apiGet('/api/intelicoop/ahorros/resumen'),
      apiGet('/api/intelicoop/ahorros/cuentas'),
      apiGet('/api/intelicoop/ahorros/transacciones'),
    ]);
    const mount = document.getElementById('intelicoop-ahorros-content');
    if (mount) {
      mount.innerHTML = `
        <div class="intelicoop-grid">
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Cuentas</span><strong class="intelicoop-kpi-value">${data.cuentas || 0}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Movimientos</span><strong class="intelicoop-kpi-value">${data.movimientos || 0}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Captacion</span><strong class="intelicoop-kpi-value">$${Number(data.captacion || 0).toFixed(2)}</strong></article>
        </div>
      `;
    }
    renderTable('intelicoop-cuentas-table', [
      { key: 'id', label: 'ID' },
      { key: 'socio_nombre', label: 'Socio' },
      { key: 'tipo', label: 'Tipo' },
      { key: 'saldo', label: 'Saldo' },
    ], cuentas);
    renderTable('intelicoop-transacciones-table', [
      { key: 'id', label: 'ID' },
      { key: 'socio_nombre', label: 'Socio' },
      { key: 'tipo', label: 'Tipo' },
      { key: 'monto', label: 'Monto' },
    ], movimientos);
    setStatus('intelicoop-ahorros-status', 'Resumen de ahorros disponible.');
  };

  const loadCampanas = async () => {
    setStatus('intelicoop-campanas-status', 'Cargando campanas...');
    const [rows, contactos, seguimientos] = await Promise.all([
      apiGet('/api/intelicoop/campanas'),
      apiGet('/api/intelicoop/campanas/contactos'),
      apiGet('/api/intelicoop/campanas/seguimientos'),
    ]);
    renderTable('intelicoop-campanas-table', [
      { key: 'id', label: 'ID' },
      { key: 'nombre', label: 'Nombre' },
      { key: 'tipo', label: 'Tipo' },
      { key: 'estado', label: 'Estado' },
    ], rows);
    renderTable('intelicoop-contactos-table', [
      { key: 'campania_nombre', label: 'Campana' },
      { key: 'socio_nombre', label: 'Socio' },
      { key: 'canal', label: 'Canal' },
      { key: 'estado_contacto', label: 'Estado' },
    ], contactos);
    renderTable('intelicoop-seguimientos-table', [
      { key: 'campania_nombre', label: 'Campana' },
      { key: 'socio_nombre', label: 'Socio' },
      { key: 'etapa', label: 'Etapa' },
      { key: 'conversion', label: 'Conversion' },
      { key: 'monto_colocado', label: 'Monto' },
    ], seguimientos.map((row) => ({ ...row, conversion: row.conversion ? 'Si' : 'No' })));
    setStatus('intelicoop-campanas-status', `${rows.length} campanas cargadas.`);
  };

  const loadProspectos = async () => {
    setStatus('intelicoop-prospectos-status', 'Cargando prospectos...');
    const rows = await apiGet('/api/intelicoop/prospectos');
    renderTable('intelicoop-prospectos-table', [
      { key: 'id', label: 'ID' },
      { key: 'nombre', label: 'Nombre' },
      { key: 'fuente', label: 'Fuente' },
      { key: 'score_propension', label: 'Score' },
    ], rows);
    setStatus('intelicoop-prospectos-status', `${rows.length} prospectos cargados.`);
  };

  const loadScoring = async () => {
    setStatus('intelicoop-scoring-status', 'Cargando resumen de scoring...');
    const data = await apiGet('/api/intelicoop/scoring/resumen');
    const mount = document.getElementById('intelicoop-scoring-content');
    if (mount) {
      mount.innerHTML = `
        <div class="intelicoop-grid">
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Inferencias</span><strong class="intelicoop-kpi-value">${data.total_inferencias || 0}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Score promedio</span><strong class="intelicoop-kpi-value">${Number(data.score_promedio || 0).toFixed(2)}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Aprobar</span><strong class="intelicoop-kpi-value">${(data.por_recomendacion || {}).aprobar || 0}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Rechazar</span><strong class="intelicoop-kpi-value">${(data.por_recomendacion || {}).rechazar || 0}</strong></article>
        </div>
      `;
    }
    setStatus('intelicoop-scoring-status', 'Resumen de scoring disponible.');
  };

  const loadSegmentacion = async () => {
    setStatus('intelicoop-segmentacion-status', 'Cargando segmentacion automatica...');
    const data = await apiGet('/api/intelicoop/segmentacion/resumen');
    const mount = document.getElementById('intelicoop-segmentacion-content');
    if (!mount) return;
    const resumen = data.resumen || {};
    const segmentos = data.segmentos || [];
    const topOportunidades = data.top_oportunidades || [];
    const alertas = data.alertas_tempranas || [];
    const abandono = data.riesgo_abandono || [];
    const prospectos = data.prospectos || [];
    mount.innerHTML = `
      <div class="intelicoop-grid">
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Socios evaluados</span><strong class="intelicoop-kpi-value">${resumen.total_socios || 0}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Comercial promedio</span><strong class="intelicoop-kpi-value">${Number(resumen.comercial_promedio || 0).toFixed(2)}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Riesgo temprano</span><strong class="intelicoop-kpi-value">${Number(resumen.riesgo_temprano_promedio || 0).toFixed(2)}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Abandono promedio</span><strong class="intelicoop-kpi-value">${Number(resumen.abandono_promedio || 0).toFixed(2)}</strong></article>
      </div>
      <div style="margin-top:16px;">
        <h3>Segmentos automaticos</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Segmento</th><th>Total</th><th>Socios ejemplo</th></tr></thead>
          <tbody>
            ${segmentos.map((row) => `<tr><td>${row.label || row.segmento || ''}</td><td>${row.total || 0}</td><td>${(row.socios || []).map((item) => item.socio_nombre).join(', ') || '-'}</td></tr>`).join('')}
          </tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Top oportunidad comercial</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Socio</th><th>Segmento</th><th>Comercial</th><th>Conversion</th></tr></thead>
          <tbody>
            ${topOportunidades.map((row) => `<tr><td>${row.socio_nombre || ''}</td><td>${row.segmento_label || ''}</td><td>${Number(row.comercial_score || 0).toFixed(2)}</td><td>${Number(row.conversion_score || 0).toFixed(2)}</td></tr>`).join('')}
          </tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Alertas tempranas</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Socio</th><th>Riesgo</th><th>Deuda/ingreso</th><th>Mora</th></tr></thead>
          <tbody>
            ${alertas.map((row) => `<tr><td>${row.socio_nombre || ''}</td><td>${Number(row.riesgo_temprano_score || 0).toFixed(2)}</td><td>${Number(row.ratio_deuda_ingreso || 0).toFixed(2)}</td><td>${row.creditos_mora || 0}</td></tr>`).join('')}
          </tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Riesgo de abandono</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Socio</th><th>Abandono</th><th>Transacciones</th><th>Productos</th></tr></thead>
          <tbody>
            ${abandono.map((row) => `<tr><td>${row.socio_nombre || ''}</td><td>${Number(row.abandono_score || 0).toFixed(2)}</td><td>${row.transacciones_total || 0}</td><td>${row.num_productos || 0}</td></tr>`).join('')}
          </tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Prospectos con mayor propension</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Prospecto</th><th>Fuente</th><th>Propension</th><th>Conversion estimada</th></tr></thead>
          <tbody>
            ${prospectos.map((row) => `<tr><td>${row.nombre || ''}</td><td>${row.fuente || ''}</td><td>${Number(row.score_propension || 0).toFixed(2)}</td><td>${Number(row.conversion_estimada || 0).toFixed(2)}</td></tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
    setStatus('intelicoop-segmentacion-status', `Segmentacion calculada${data.cut_key ? ` sobre ${data.cut_key}` : ' en vivo'}.`);
  };

  const loadFoundations = async () => {
    setStatus('intelicoop-foundation-status', 'Cargando fundamentos del modulo...');
    const data = await apiGet('/api/intelicoop/fundamentos/resumen');
    const mount = document.getElementById('intelicoop-foundation-content');
    if (!mount) return;
    const entityModel = data.entity_model || {};
    const transactional = entityModel.transactional || [];
    const analytical = entityModel.analytical || [];
    const relationships = entityModel.relationships || [];
    const quality = data.minimum_quality || [];
    const timeCuts = data.time_cuts || {};
    const storage = data.storage_contract || {};
    mount.innerHTML = `
      <div class="intelicoop-grid">
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Tablas transaccionales</span><strong class="intelicoop-kpi-value">${transactional.length}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Tablas analiticas</span><strong class="intelicoop-kpi-value">${analytical.length}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Relaciones</span><strong class="intelicoop-kpi-value">${relationships.length}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Reglas de calidad</span><strong class="intelicoop-kpi-value">${quality.length}</strong></article>
      </div>
      <div style="margin-top:16px;">
        <h3>Entidades transaccionales</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Entidad</th><th>Tabla</th><th>Granularidad</th><th>Registros</th></tr></thead>
          <tbody>${transactional.map((row) => `<tr><td>${row.key || ''}</td><td>${row.table || ''}</td><td>${row.grain || ''}</td><td>${row.records || 0}</td></tr>`).join('')}</tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Entidades analiticas</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Entidad</th><th>Tabla</th><th>Granularidad</th><th>Registros</th></tr></thead>
          <tbody>${analytical.map((row) => `<tr><td>${row.key || ''}</td><td>${row.table || ''}</td><td>${row.grain || ''}</td><td>${row.records || 0}</td></tr>`).join('')}</tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Relaciones</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Origen</th><th>Destino</th><th>Tipo</th><th>Clave</th></tr></thead>
          <tbody>${relationships.map((row) => `<tr><td>${row.from || ''}</td><td>${row.to || ''}</td><td>${row.type || ''}</td><td>${row.key || ''}</td></tr>`).join('')}</tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Calidad minima</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Scope</th><th>Regla</th><th>Total</th><th>Fallidos</th><th>Status</th></tr></thead>
          <tbody>${quality.map((row) => `<tr><td>${row.scope || ''}</td><td>${row.rule_key || ''}</td><td>${row.total_records || 0}</td><td>${row.failed_records || 0}</td><td>${row.status || ''}</td></tr>`).join('')}</tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Cortes de tiempo</h3>
        <div class="intelicoop-grid">
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Cut key activo</span><strong class="intelicoop-kpi-value" style="font-size:18px;">${timeCuts.active_cut_key || '-'}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Inicio diario</span><strong class="intelicoop-kpi-value" style="font-size:18px;">${timeCuts.daily_window_start || '-'}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Fin diario</span><strong class="intelicoop-kpi-value" style="font-size:18px;">${timeCuts.daily_window_end || '-'}</strong></article>
          <article class="intelicoop-card"><span class="intelicoop-kpi-label">Ultimo corte materializado</span><strong class="intelicoop-kpi-value" style="font-size:18px;">${(storage.latest_materialized_cut || {}).cut_key || 'pendiente'}</strong></article>
        </div>
      </div>
    `;
    setStatus('intelicoop-foundation-status', 'Fundamentos de datos disponibles.');
  };

  const loadBatch = async () => {
    setStatus('intelicoop-batch-status', 'Cargando automatizacion batch...');
    const data = await apiGet('/api/intelicoop/batch/resumen');
    const mount = document.getElementById('intelicoop-batch-content');
    if (!mount) return;
    const jobs = data.jobs || [];
    const runs = data.runs || [];
    const alerts = data.alerts || [];
    mount.innerHTML = `
      <div class="intelicoop-grid">
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Jobs</span><strong class="intelicoop-kpi-value">${jobs.length}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Pendientes</span><strong class="intelicoop-kpi-value">${(data.due_jobs || []).length}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Bitacora</span><strong class="intelicoop-kpi-value">${runs.length}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Alertas</span><strong class="intelicoop-kpi-value">${alerts.length}</strong></article>
      </div>
      <div style="margin-top:16px;">
        <h3>Jobs programados</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Job</th><th>Cadencia</th><th>Estado</th><th>Ultima corrida</th><th>Proxima corrida</th></tr></thead>
          <tbody>${jobs.map((row) => `<tr><td>${row.job_label || row.job_key || ''}</td><td>${row.cadence_minutes || 0} min</td><td>${row.last_status || ''}</td><td>${row.last_run_at || '-'}</td><td>${row.next_run_at || '-'}</td></tr>`).join('')}</tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Bitacora de ejecucion</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Run</th><th>Job</th><th>Status</th><th>Calidad</th><th>Procesados</th><th>Creados</th></tr></thead>
          <tbody>${runs.map((row) => `<tr><td>${row.run_key || ''}</td><td>${row.job_key || ''}</td><td>${row.status || ''}</td><td>${row.quality_status || ''}</td><td>${row.records_processed || 0}</td><td>${row.records_created || 0}</td></tr>`).join('')}</tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Alertas recientes</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Tipo</th><th>Severidad</th><th>Entidad</th><th>Score</th><th>Status</th></tr></thead>
          <tbody>${alerts.map((row) => `<tr><td>${row.alert_type || ''}</td><td>${row.severity || ''}</td><td>${row.entity_label || ''}</td><td>${Number(row.score || 0).toFixed(2)}</td><td>${row.status || ''}</td></tr>`).join('')}</tbody>
        </table>
      </div>
    `;
    setStatus('intelicoop-batch-status', 'Automatizacion batch disponible.');
  };

  const loadGovernance = async () => {
    setStatus('intelicoop-governance-status', 'Cargando gobernanza del modelo...');
    const data = await apiGet('/api/intelicoop/gobernanza/resumen');
    const mount = document.getElementById('intelicoop-governance-content');
    if (!mount) return;
    const latest = data.latest_snapshot || {};
    const monitoring = latest.monitoring || {};
    const explainability = latest.explainability || {};
    const driftRows = data.drift_rows || [];
    const recalibrations = data.recalibrations || [];
    const audits = data.audit_logs || [];
    const rules = data.business_rules || [];
    mount.innerHTML = `
      <div class="intelicoop-grid">
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Estado</span><strong class="intelicoop-kpi-value">${latest.governance_status || 'pending'}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Version modelo</span><strong class="intelicoop-kpi-value" style="font-size:18px;">${latest.model_version || '-'}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Drift max</span><strong class="intelicoop-kpi-value">${Number(Math.max(0, ...driftRows.map((row) => Number(row.drift_score || 0)))).toFixed(2)}</strong></article>
        <article class="intelicoop-card"><span class="intelicoop-kpi-label">Cobertura explicacion</span><strong class="intelicoop-kpi-value">${Number(explainability.cobertura_explicacion || 0).toFixed(2)}</strong></article>
      </div>
      <div style="margin-top:16px;">
        <h3>Monitoreo</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Metrica</th><th>Valor</th></tr></thead>
          <tbody>
            <tr><td>Total inferencias</td><td>${monitoring.total_inferencias || 0}</td></tr>
            <tr><td>Muestra reciente</td><td>${monitoring.muestra_reciente || 0}</td></tr>
            <tr><td>Score promedio reciente</td><td>${Number(monitoring.score_promedio_reciente || 0).toFixed(4)}</td></tr>
            <tr><td>Confianza promedio</td><td>${Number(monitoring.confianza_promedio_reciente || 0).toFixed(4)}</td></tr>
            <tr><td>Share alto riesgo</td><td>${Number(monitoring.share_riesgo_alto_reciente || 0).toFixed(4)}</td></tr>
            <tr><td>Ratio deuda/ingreso promedio</td><td>${Number(monitoring.ratio_deuda_ingreso_promedio_reciente || 0).toFixed(4)}</td></tr>
          </tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Drift del modelo</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Feature</th><th>Baseline</th><th>Actual</th><th>Drift</th><th>Nivel</th></tr></thead>
          <tbody>${driftRows.map((row) => `<tr><td>${row.feature_key || ''}</td><td>${Number(row.baseline_value || 0).toFixed(4)}</td><td>${Number(row.current_value || 0).toFixed(4)}</td><td>${Number(row.drift_score || 0).toFixed(4)}</td><td>${row.drift_level || ''}</td></tr>`).join('')}</tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Reglas de negocio</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Regla</th><th>Severidad</th><th>Umbral</th><th>Status</th></tr></thead>
          <tbody>${rules.map((row) => `<tr><td>${row.rule_label || row.rule_key || ''}</td><td>${row.severity || ''}</td><td>${row.threshold_value ?? '-'}</td><td>${((monitoring.rules || []).find((item) => item.rule_key === row.rule_key) || {}).status || 'pending'}</td></tr>`).join('')}</tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Recalibracion</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Fecha</th><th>Motivo</th><th>Status</th><th>Modelo</th></tr></thead>
          <tbody>${recalibrations.map((row) => `<tr><td>${row.created_at || ''}</td><td>${row.trigger_reason || ''}</td><td>${row.status || ''}</td><td>${row.model_version || ''}</td></tr>`).join('')}</tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <h3>Auditoria</h3>
        <table class="intelicoop-table">
          <thead><tr><th>Evento</th><th>Entidad</th><th>Actor</th><th>Modelo</th><th>Fecha</th></tr></thead>
          <tbody>${audits.map((row) => `<tr><td>${row.event_type || ''}</td><td>${row.entity_type || ''} ${row.entity_id || ''}</td><td>${row.actor || ''}</td><td>${row.model_version || ''}</td><td>${row.created_at || ''}</td></tr>`).join('')}</tbody>
        </table>
      </div>
    `;
    setStatus('intelicoop-governance-status', 'Gobernanza del modelo disponible.');
  };

  const bindFoundationMaterialize = () => {
    const button = document.getElementById('intelicoop-foundation-materialize');
    if (!button) return;
    button.addEventListener('click', async () => {
      button.disabled = true;
      setFormResult('intelicoop-foundation-result', 'Materializando corte analitico...', false);
      try {
        const data = await apiPost('/api/intelicoop/fundamentos/materializar', { cut_type: 'daily_close' });
        setFormResult(
          'intelicoop-foundation-result',
          `Corte ${data.cut_key || ''} materializado. Features: ${data.feature_rows || 0}, KPIs: ${data.kpi_rows || 0}, calidad: ${data.quality_rules || 0}.`,
          false
        );
        await loadFoundations();
      } catch (error) {
        setFormResult('intelicoop-foundation-result', `No se pudo materializar el corte: ${error.message}`, true);
      } finally {
        button.disabled = false;
      }
    });
  };

  const bindBatchActions = () => {
    const dueButton = document.getElementById('intelicoop-batch-run-due');
    if (dueButton) {
      dueButton.addEventListener('click', async () => {
        dueButton.disabled = true;
        setFormResult('intelicoop-batch-result', 'Ejecutando jobs programados...', false);
        try {
          const data = await apiPost('/api/intelicoop/batch/ejecutar-programados', {});
          setFormResult('intelicoop-batch-result', `Jobs ejecutados: ${(data.executed_jobs || []).join(', ') || 'ninguno'}.`, false);
          await Promise.all([loadBatch(), loadFoundations(), loadSegmentacion(), loadScoring(), loadDashboard(), loadKpis(), loadSocios(), loadGovernance()]);
        } catch (error) {
          setFormResult('intelicoop-batch-result', `No se pudieron ejecutar los programados: ${error.message}`, true);
        } finally {
          dueButton.disabled = false;
        }
      });
    }
    document.querySelectorAll('.intelicoop-batch-run').forEach((button) => {
      button.addEventListener('click', async () => {
        const jobKey = button.getAttribute('data-job-key');
        button.disabled = true;
        setFormResult('intelicoop-batch-result', `Ejecutando ${jobKey}...`, false);
        try {
          const data = await apiPost('/api/intelicoop/batch/ejecutar', { job_key: jobKey });
          setFormResult('intelicoop-batch-result', `Job ${data.job_key || jobKey} ejecutado.`, false);
          await Promise.all([loadBatch(), loadFoundations(), loadSegmentacion(), loadScoring(), loadDashboard(), loadKpis(), loadSocios(), loadGovernance()]);
        } catch (error) {
          setFormResult('intelicoop-batch-result', `No se pudo ejecutar ${jobKey}: ${error.message}`, true);
        } finally {
          button.disabled = false;
        }
      });
    });
  };

  const bindGovernanceRefresh = () => {
    const button = document.getElementById('intelicoop-governance-refresh');
    if (!button) return;
    button.addEventListener('click', async () => {
      button.disabled = true;
      setFormResult('intelicoop-governance-result', 'Actualizando gobernanza...', false);
      try {
        const data = await apiPost('/api/intelicoop/gobernanza/refresh', {});
        setFormResult('intelicoop-governance-result', `Gobernanza actualizada. Estado: ${data.governance_status || 'pass'}.`, false);
        await Promise.all([loadGovernance(), loadBatch()]);
      } catch (error) {
        setFormResult('intelicoop-governance-result', `No se pudo actualizar la gobernanza: ${error.message}`, true);
      } finally {
        button.disabled = false;
      }
    });
  };

  const bindScoringForm = () => {
    const form = document.getElementById('intelicoop-scoring-form');
    const result = document.getElementById('intelicoop-scoring-result');
    if (!form || !result) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const payload = {
        solicitud_id: formData.get('solicitud_id') || null,
        socio_id: formData.get('socio_id') ? Number(formData.get('socio_id')) : null,
        ingreso_mensual: Number(formData.get('ingreso_mensual') || 0),
        deuda_actual: Number(formData.get('deuda_actual') || 0),
        antiguedad_meses: Number(formData.get('antiguedad_meses') || 0),
      };
      result.innerHTML = '<p class="intelicoop-status">Evaluando scoring...</p>';
      try {
        const data = await apiPost('/api/intelicoop/scoring/evaluar', payload);
        const razones = Array.isArray(data.razones) ? data.razones.slice(0, 3) : [];
        result.innerHTML = `
          <div class="intelicoop-card">
            <strong>Resultado</strong>
            <p>Score: ${Number(data.score || 0).toFixed(4)}</p>
            <p>Recomendacion: ${data.recomendacion || '-'}</p>
            <p>Riesgo: ${data.riesgo || '-'}</p>
            <p>Version: ${data.model_version || '-'}</p>
            <p>Motor: ${data.motor || '-'}</p>
            <p>Confianza: ${data.confianza != null ? Number(data.confianza).toFixed(4) : '-'}</p>
            <p>Traza: ${data.traza_id || '-'} / ${data.traza_version || '-'}</p>
            ${razones.length ? `<p>Razones: ${razones.join(' | ')}</p>` : ''}
          </div>
        `;
        loadScoring().catch(() => {});
        loadDashboard().catch(() => {});
        loadKpis().catch(() => {});
      } catch (error) {
        result.innerHTML = `<p class="intelicoop-status">No se pudo evaluar el scoring: ${error.message}</p>`;
      }
    });
  };

  const bindSociosForm = () => {
    const form = document.getElementById('intelicoop-socios-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        await apiPost('/api/intelicoop/socios', {
          nombre: formData.get('nombre'),
          email: formData.get('email'),
          telefono: formData.get('telefono'),
          direccion: formData.get('direccion'),
          fecha_nacimiento: formData.get('fecha_nacimiento') || null,
          genero: formData.get('genero') || null,
          estado_civil: formData.get('estado_civil') || null,
          nivel_educativo: formData.get('nivel_educativo') || null,
          ocupacion: formData.get('ocupacion') || null,
          sector_economico: formData.get('sector_economico') || null,
          ubicacion_estado: formData.get('ubicacion_estado') || null,
          ubicacion_municipio: formData.get('ubicacion_municipio') || null,
          tipo_socio: formData.get('tipo_socio') || 'individual',
          segmento: formData.get('segmento'),
        });
        form.reset();
        form.querySelector('[name="tipo_socio"]').value = 'individual';
        form.querySelector('[name="segmento"]').value = 'inactivo';
        setFormResult('intelicoop-socios-form-result', 'Socio creado correctamente.', false);
        await Promise.all([loadSocios(), loadCatalogs(), loadDashboard(), loadKpis()]);
        loadSegmentacion().catch(() => {});
      } catch (error) {
        setFormResult('intelicoop-socios-form-result', `No se pudo crear el socio: ${error.message}`, true);
      }
    });
  };

  const bindCreditosForm = () => {
    const form = document.getElementById('intelicoop-creditos-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        const response = await apiPost('/api/intelicoop/creditos', {
          socio_id: Number(formData.get('socio_id')),
          monto: Number(formData.get('monto') || 0),
          numero_abonos: Number(formData.get('numero_abonos') || 0),
          periodicidad: formData.get('periodicidad') || 'mensual',
          ingreso_mensual: Number(formData.get('ingreso_mensual') || 0),
          deuda_actual: Number(formData.get('deuda_actual') || 0),
          antiguedad_meses: Number(formData.get('antiguedad_meses') || 0),
          tasa: Number(formData.get('tasa') || 0),
          dias_mora_actual: Number(formData.get('dias_mora_actual') || 0),
          max_dias_mora: Number(formData.get('max_dias_mora') || 0),
          num_reestructuras: Number(formData.get('num_reestructuras') || 0),
          estado: formData.get('estado'),
        });
        form.reset();
        form.querySelector('[name="periodicidad"]').value = 'mensual';
        form.querySelector('[name="estado"]').value = 'solicitado';
        const scoring = response.scoring || {};
        setFormResult(
          'intelicoop-creditos-form-result',
          `Credito registrado. Scoring: ${Number(scoring.score || 0).toFixed(4)} / ${scoring.recomendacion || 'sin dato'} / ${scoring.riesgo || 'sin dato'} / traza ${scoring.traza_id || '-'}.`,
          false
        );
        await Promise.all([loadCreditos(), loadScoring(), loadDashboard(), loadKpis()]);
        loadSegmentacion().catch(() => {});
      } catch (error) {
        setFormResult('intelicoop-creditos-form-result', `No se pudo registrar el credito: ${error.message}`, true);
      }
    });
  };

  const bindCreditosImportForm = () => {
    const form = document.getElementById('intelicoop-creditos-import-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const fileInput = form.querySelector('[name="archivo"]');
      const file = fileInput && fileInput.files ? fileInput.files[0] : null;
      if (!file) {
        setFormResult('intelicoop-creditos-import-result', 'Selecciona un archivo CSV.', true);
        return;
      }
      const payload = new FormData();
      payload.append('file', file);
      setFormResult('intelicoop-creditos-import-result', 'Importando creditos...', false);
      try {
        const data = await apiPostForm('/api/intelicoop/creditos/importacion', payload);
        const errores = Array.isArray(data.errores) ? data.errores : [];
        const modo = data.modo_importacion === 'batch_sin_scoring'
          ? ' Modo batch aplicado; scoring omitido para acelerar la carga.'
          : '';
        const textoErrores = errores.length
          ? ` Errores: ${errores.map((item) => `linea ${item.linea}: ${item.error}`).join(' | ')}`
          : '';
        setFormResult(
          'intelicoop-creditos-import-result',
          `Archivo ${data.archivo || ''} procesado. Filas: ${data.total_filas || 0}. Importados: ${data.importados || 0}.${modo}${textoErrores}`,
          errores.length > 0
        );
        form.reset();
        await Promise.all([loadCreditos(), loadCatalogs(), loadScoring(), loadDashboard(), loadKpis()]);
        loadSegmentacion().catch(() => {});
      } catch (error) {
        setFormResult('intelicoop-creditos-import-result', `No se pudo importar el archivo: ${error.message}`, true);
      }
    });
  };

  const bindCampanasForm = () => {
    const form = document.getElementById('intelicoop-campanas-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        await apiPost('/api/intelicoop/campanas', {
          nombre: formData.get('nombre'),
          tipo: formData.get('tipo'),
          fecha_inicio: formData.get('fecha_inicio'),
          fecha_fin: formData.get('fecha_fin'),
          estado: formData.get('estado'),
        });
        form.reset();
        form.querySelector('[name="estado"]').value = 'borrador';
        setFormResult('intelicoop-campanas-form-result', 'Campana creada correctamente.', false);
        await Promise.all([loadCampanas(), loadDashboard(), loadKpis()]);
      } catch (error) {
        setFormResult('intelicoop-campanas-form-result', `No se pudo crear la campana: ${error.message}`, true);
      }
    });
  };

  const bindContactosForm = () => {
    const form = document.getElementById('intelicoop-contactos-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        await apiPost('/api/intelicoop/campanas/contactos', {
          campania_id: Number(formData.get('campania_id')),
          socio_id: Number(formData.get('socio_id')),
          ejecutivo_id: formData.get('ejecutivo_id'),
          canal: formData.get('canal'),
          estado_contacto: formData.get('estado_contacto'),
        });
        form.reset();
        form.querySelector('[name="ejecutivo_id"]').value = 'ejecutivo_general';
        form.querySelector('[name="canal"]').value = 'telefono';
        form.querySelector('[name="estado_contacto"]').value = 'pendiente';
        setFormResult('intelicoop-contactos-form-result', 'Contacto comercial registrado.', false);
        await Promise.all([loadCatalogs(), loadCampanas(), loadDashboard(), loadKpis()]);
        loadSegmentacion().catch(() => {});
      } catch (error) {
        setFormResult('intelicoop-contactos-form-result', `No se pudo registrar el contacto: ${error.message}`, true);
      }
    });
  };

  const bindSeguimientosForm = () => {
    const form = document.getElementById('intelicoop-seguimientos-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        await apiPost('/api/intelicoop/campanas/seguimientos', {
          campania_id: Number(formData.get('campania_id')),
          socio_id: Number(formData.get('socio_id')),
          lista: formData.get('lista'),
          etapa: formData.get('etapa'),
          conversion: String(formData.get('conversion')) === '1',
          monto_colocado: Number(formData.get('monto_colocado') || 0),
        });
        form.reset();
        form.querySelector('[name="lista"]').value = 'general';
        form.querySelector('[name="etapa"]').value = 'contactado';
        form.querySelector('[name="conversion"]').value = '0';
        form.querySelector('[name="monto_colocado"]').value = '0';
        setFormResult('intelicoop-seguimientos-form-result', 'Seguimiento comercial registrado.', false);
        await Promise.all([loadCatalogs(), loadCampanas(), loadDashboard(), loadKpis()]);
        loadSegmentacion().catch(() => {});
      } catch (error) {
        setFormResult('intelicoop-seguimientos-form-result', `No se pudo registrar el seguimiento: ${error.message}`, true);
      }
    });
  };

  const bindProspectosForm = () => {
    const form = document.getElementById('intelicoop-prospectos-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        await apiPost('/api/intelicoop/prospectos', {
          nombre: formData.get('nombre'),
          telefono: formData.get('telefono'),
          direccion: formData.get('direccion'),
          fuente: formData.get('fuente'),
          score_propension: Number(formData.get('score_propension') || 0),
        });
        form.reset();
        setFormResult('intelicoop-prospectos-form-result', 'Prospecto creado correctamente.', false);
        await Promise.all([loadProspectos(), loadDashboard(), loadKpis()]);
        loadSegmentacion().catch(() => {});
      } catch (error) {
        setFormResult('intelicoop-prospectos-form-result', `No se pudo crear el prospecto: ${error.message}`, true);
      }
    });
  };

  const bindCuentasForm = () => {
    const form = document.getElementById('intelicoop-cuentas-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        await apiPost('/api/intelicoop/ahorros/cuentas', {
          socio_id: Number(formData.get('socio_id')),
          tipo: formData.get('tipo'),
          saldo: Number(formData.get('saldo') || 0),
        });
        form.reset();
        form.querySelector('[name="tipo"]').value = 'ahorro';
        setFormResult('intelicoop-cuentas-form-result', 'Cuenta creada correctamente.', false);
        await Promise.all([loadCatalogs(), loadAhorros(), loadDashboard(), loadKpis()]);
      } catch (error) {
        setFormResult('intelicoop-cuentas-form-result', `No se pudo crear la cuenta: ${error.message}`, true);
      }
    });
  };

  const bindTransaccionesForm = () => {
    const form = document.getElementById('intelicoop-transacciones-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        await apiPost('/api/intelicoop/ahorros/transacciones', {
          cuenta_id: Number(formData.get('cuenta_id')),
          tipo: formData.get('tipo'),
          monto: Number(formData.get('monto') || 0),
          canal: formData.get('canal') || 'ventanilla',
        });
        form.reset();
        form.querySelector('[name="tipo"]').value = 'deposito';
        form.querySelector('[name="canal"]').value = 'ventanilla';
        setFormResult('intelicoop-transacciones-form-result', 'Movimiento registrado correctamente.', false);
        await Promise.all([loadCatalogs(), loadAhorros(), loadDashboard(), loadKpis()]);
      } catch (error) {
        setFormResult('intelicoop-transacciones-form-result', `No se pudo registrar el movimiento: ${error.message}`, true);
      }
    });
  };

  const bindPagosForm = () => {
    const form = document.getElementById('intelicoop-pagos-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const creditoId = Number(formData.get('credito_id'));
      try {
        await apiPost('/api/intelicoop/creditos/pagos', {
          credito_id: creditoId,
          monto: Number(formData.get('monto') || 0),
          pago_puntual: String(formData.get('pago_puntual')) === '1',
          dias_atraso: Number(formData.get('dias_atraso') || 0),
        });
        form.reset();
        form.querySelector('[name="pago_puntual"]').value = '1';
        form.querySelector('[name="dias_atraso"]').value = '0';
        setFormResult('intelicoop-pagos-form-result', 'Pago registrado correctamente.', false);
        await Promise.all([loadCreditos(), loadCatalogs(), loadDashboard(), loadKpis()]);
        if (creditoId) {
          await loadCreditoDetail(creditoId);
        }
      } catch (error) {
        setFormResult('intelicoop-pagos-form-result', `No se pudo registrar el pago: ${error.message}`, true);
      }
    });
  };

  const bootstrap = async () => {
    const activatePanel = updateTabs();
    bindImportShortcut(activatePanel);
    bindScoringForm();
    bindSociosForm();
    bindCreditosForm();
    bindCreditosImportForm();
    bindPagosForm();
    bindCuentasForm();
    bindTransaccionesForm();
    bindCampanasForm();
    bindContactosForm();
    bindSeguimientosForm();
    bindProspectosForm();
    bindDeleteDataAction();
    bindFoundationMaterialize();
    bindBatchActions();
    bindGovernanceRefresh();
    try {
        await Promise.all([
          loadCatalogs(),
          loadKpis(),
          loadDashboard(),
          loadSocios(),
        loadCreditos(),
        loadAhorros(),
        loadCampanas(),
          loadProspectos(),
          loadScoring(),
          loadSegmentacion(),
          loadFoundations(),
          loadBatch(),
          loadGovernance(),
        ]);
    } catch (error) {
      console.error('Intelicoop bootstrap error', error);
    }
  };

  bootstrap();
})();
