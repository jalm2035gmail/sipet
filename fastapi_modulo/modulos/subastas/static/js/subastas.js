/* ─────────────────────────────────────────────────────────────────────────────
   Subastas · SIPET — frontend administrativo
   Vanilla JS, sin dependencias externas.
   ───────────────────────────────────────────────────────────────────────── */
(function () {
  'use strict';

  const API = '/subastas/api';

  /* ── Utilidades ─────────────────────────────────────────────────────── */

  async function req(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const res = await fetch(API + path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
    return data;
  }
  const get  = p       => req('GET',   p);
  const post = (p, b)  => req('POST',  p, b);
  const patch= (p, b)  => req('PATCH', p, b);

  function badge(state) {
    const labels = {
      draft:'Borrador', scheduled:'Programada', published:'Publicada',
      live:'En curso', suspended:'Suspendida', closed:'Cerrada',
      awarded:'Adjudicada', deserted:'Desierta', cancelled:'Cancelada',
      pending:'Pendiente', payment_pending:'Pago pendiente', paid:'Pagada',
      expired:'Vencida', reassigned:'Reasignada',
      approved:'Aprobado', rejected:'Rechazado',
      in_transit:'En tránsito', delivered:'Entregado',
    };
    const cls = state ? state.replace(/_/g, '_') : '';
    return `<span class="badge badge-${cls}">${labels[state] || state}</span>`;
  }

  function fmt(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('es-MX', {
      day:'2-digit', month:'short', year:'numeric',
      hour:'2-digit', minute:'2-digit',
    });
  }

  function fmtMoney(n) {
    return Number(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function setFeedback(el, msg, isError = false) {
    el.textContent = msg;
    el.className = 'feedback' + (isError ? ' error' : '');
    if (msg && !isError) setTimeout(() => { el.textContent = ''; }, 4000);
  }

  function formToObj(form) {
    const fd = new FormData(form);
    const obj = {};
    for (const [k, v] of fd.entries()) {
      if (v !== '') obj[k] = v;
    }
    return obj;
  }

  /* ── Countdown timer ────────────────────────────────────────────────── */

  let _timerInterval = null;

  function startTimer(endAtIso, el) {
    if (_timerInterval) clearInterval(_timerInterval);
    if (!endAtIso || !el) return;
    function tick() {
      const diff = Math.max(0, new Date(endAtIso) - Date.now());
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      el.textContent = diff === 0
        ? 'Tiempo agotado'
        : `${h}h ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s`;
      el.className = 'timer' + (diff < 300000 ? ' urgent' : '');
    }
    tick();
    _timerInterval = setInterval(tick, 1000);
  }

  /* ══════════════════════════════════════════════════════════════════════
     TAB MANAGER
  ══════════════════════════════════════════════════════════════════════ */

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
  });

  /* ══════════════════════════════════════════════════════════════════════
     DASHBOARD STATS
  ══════════════════════════════════════════════════════════════════════ */

  async function loadStats() {
    try {
      const d = await get('/dashboard');
      document.getElementById('kpiTotal').textContent    = d.total_auctions;
      document.getElementById('kpiLive').textContent     = d.live_auctions;
      document.getElementById('kpiAwarded').textContent  = d.awarded_auctions;
      document.getElementById('kpiBidders').textContent  = d.total_bidders;
      document.getElementById('kpiAmountVal').textContent= fmtMoney(d.awarded_amount);
      document.getElementById('kpiConversion').textContent = `Conversión: ${d.conversion_rate}%`;
      document.getElementById('kpiPending').textContent  =
        d.pending_payments > 0 ? `${d.pending_payments} pagos pendientes` : '';
    } catch (_) {}
  }

  /* ══════════════════════════════════════════════════════════════════════
     AUCTIONS TABLE
  ══════════════════════════════════════════════════════════════════════ */

  async function loadAuctions() {
    const state = document.getElementById('filterState').value;
    const tbody = document.getElementById('auctionRows');
    tbody.innerHTML = '<tr class="empty-row"><td colspan="8" class="loading">Cargando...</td></tr>';
    try {
      const data = await get('/auctions' + (state ? `?state=${state}` : ''));
      const items = data.items || data; // soporta paginado o lista plana
      if (!items.length) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="8">Sin subastas.</td></tr>';
        return;
      }
      tbody.innerHTML = items.map(a => `
        <tr>
          <td class="font-mono">${a.id}</td>
          <td><a href="#" class="text-accent auction-link" data-id="${a.id}">${a.name}</a></td>
          <td>${badge(a.state)}</td>
          <td class="text-muted" style="font-size:.82rem;">${a.auction_type}</td>
          <td class="text-muted" style="font-size:.82rem;">${fmt(a.start_at)}</td>
          <td class="text-muted" style="font-size:.82rem;">${fmt(a.end_at)}</td>
          <td id="timer-${a.id}">
            ${['published','live'].includes(a.state) && a.end_at
              ? `<span class="timer" data-end="${a.end_at}">—</span>` : '—'}
          </td>
          <td class="td-actions">${renderAuctionActions(a)}</td>
        </tr>
      `).join('');

      // Timers en tabla
      tbody.querySelectorAll('.timer[data-end]').forEach(el => {
        const iv = setInterval(() => {
          const diff = Math.max(0, new Date(el.dataset.end) - Date.now());
          const h = Math.floor(diff / 3600000);
          const m = Math.floor((diff % 3600000) / 60000);
          const s = Math.floor((diff % 60000) / 1000);
          el.textContent = diff === 0 ? 'Agotado' : `${h}h ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s`;
          el.className = 'timer' + (diff < 300000 ? ' urgent' : '');
          if (diff === 0) clearInterval(iv);
        }, 1000);
      });

      // Links a detalle
      tbody.querySelectorAll('.auction-link').forEach(a =>
        a.addEventListener('click', e => { e.preventDefault(); openDrawer(a.dataset.id); })
      );

      // Botones de acción en tabla
      tbody.querySelectorAll('[data-action]').forEach(btn =>
        btn.addEventListener('click', () => handleAuctionAction(btn.dataset.action, btn.dataset.id))
      );

    } catch (e) {
      tbody.innerHTML = `<tr class="empty-row"><td colspan="8" class="text-red">${e.message}</td></tr>`;
    }
  }

  function renderAuctionActions(a) {
    const id = a.id;
    const btns = [];
    if (a.state === 'draft' || a.state === 'scheduled')
      btns.push(`<button class="btn btn-ghost btn-sm" data-action="publish" data-id="${id}">Publicar</button>`);
    if (a.state === 'published')
      btns.push(`<button class="btn btn-ghost btn-sm" data-action="live" data-id="${id}">Iniciar</button>`);
    if (['published','live'].includes(a.state))
      btns.push(`<button class="btn btn-primary btn-sm" data-action="close" data-id="${id}">Cerrar</button>`);
    if (['published','live','suspended'].includes(a.state))
      btns.push(`<button class="btn btn-warn btn-sm" data-action="suspend" data-id="${id}">Suspender</button>`);
    if (['draft','scheduled','published','live','suspended'].includes(a.state))
      btns.push(`<button class="btn btn-danger btn-sm" data-action="cancel" data-id="${id}">Cancelar</button>`);
    return btns.join('');
  }

  async function handleAuctionAction(action, id) {
    const labels = { publish:'publicar', live:'iniciar', close:'cerrar', suspend:'suspender', cancel:'cancelar' };
    if (!confirm(`¿Confirmas ${labels[action]} la subasta ${id}?`)) return;
    try {
      await post(`/auctions/${id}/${action}`);
      await loadAuctions();
      await loadStats();
    } catch (e) {
      alert(e.message);
    }
  }

  document.getElementById('filterState').addEventListener('change', loadAuctions);
  document.getElementById('btnRefresh').addEventListener('click', async () => {
    await Promise.all([loadStats(), loadAuctions()]);
  });

  /* ══════════════════════════════════════════════════════════════════════
     MODAL: NUEVA SUBASTA
  ══════════════════════════════════════════════════════════════════════ */

  const modalOverlay   = document.getElementById('modalNuevaSubasta');
  const auctionForm    = document.getElementById('auctionForm');
  const auctionFb      = document.getElementById('auctionFeedback');

  document.getElementById('btnNuevaSubasta').addEventListener('click', () => {
    modalOverlay.classList.add('open');
  });
  document.getElementById('btnCerrarModal').addEventListener('click', () => {
    modalOverlay.classList.remove('open');
  });
  modalOverlay.addEventListener('click', e => {
    if (e.target === modalOverlay) modalOverlay.classList.remove('open');
  });

  auctionForm.addEventListener('submit', async e => {
    e.preventDefault();
    setFeedback(auctionFb, 'Guardando...');
    const payload = formToObj(auctionForm);
    payload.min_increment     = Number(payload.min_increment || 0);
    payload.auto_extend_seconds = Number(payload.auto_extend_seconds || 0);
    if (payload.reserve_price) payload.reserve_price = Number(payload.reserve_price);
    else delete payload.reserve_price;
    if (!payload.start_at) delete payload.start_at;
    if (!payload.end_at)   delete payload.end_at;
    if (!payload.description) delete payload.description;
    if (!payload.terms)    delete payload.terms;
    try {
      const res = await post('/auctions', payload);
      setFeedback(auctionFb, `Subasta creada — ID ${res.id}`);
      auctionForm.reset();
      setTimeout(() => modalOverlay.classList.remove('open'), 1200);
      await loadAuctions();
      await loadStats();
    } catch (err) {
      setFeedback(auctionFb, err.message, true);
    }
  });

  /* ══════════════════════════════════════════════════════════════════════
     DRAWER: DETALLE DE SUBASTA
  ══════════════════════════════════════════════════════════════════════ */

  const drawerOverlay  = document.getElementById('drawerOverlay');
  let _drawerAuctionId = null;
  let _pollInterval    = null;

  document.getElementById('btnCerrarDrawer').addEventListener('click', closeDrawer);
  drawerOverlay.addEventListener('click', e => {
    if (e.target === drawerOverlay) closeDrawer();
  });

  function closeDrawer() {
    drawerOverlay.classList.remove('open');
    if (_timerInterval) clearInterval(_timerInterval);
    if (_pollInterval)  clearInterval(_pollInterval);
    _drawerAuctionId = null;
  }

  async function openDrawer(id) {
    _drawerAuctionId = id;
    drawerOverlay.classList.add('open');
    await renderDrawer(id);
    // Polling cada 5s para subastas activas
    if (_pollInterval) clearInterval(_pollInterval);
    _pollInterval = setInterval(async () => {
      if (!_drawerAuctionId) return;
      const a = await get(`/auctions/${_drawerAuctionId}`).catch(() => null);
      if (!a || !['published','live'].includes(a.state)) {
        clearInterval(_pollInterval);
        return;
      }
      await renderDrawer(_drawerAuctionId);
    }, 5000);
  }

  async function renderDrawer(id) {
    try {
      const a    = await get(`/auctions/${id}`);
      const bids = await get(`/auctions/${id}/bids`).catch(() => []);

      document.getElementById('drawerTitle').textContent = a.name;
      document.getElementById('drawerBadge').innerHTML   = badge(a.state);
      document.getElementById('drawerType').textContent  = a.auction_type;

      // Meta
      const meta = document.getElementById('drawerMeta');
      meta.innerHTML = `
        <div><span class="text-muted">Moneda</span><br>${a.currency}</div>
        <div><span class="text-muted">Incremento mín.</span><br>$${fmtMoney(a.min_increment)}</div>
        <div><span class="text-muted">Precio reserva</span><br>${a.reserve_price ? '$'+fmtMoney(a.reserve_price) : '—'}</div>
        <div><span class="text-muted">Extensión auto</span><br>${a.auto_extend_seconds ? a.auto_extend_seconds+'s' : '—'}</div>
        <div><span class="text-muted">Inicio</span><br>${fmt(a.start_at)}</div>
        <div><span class="text-muted">Cierre</span><br>${fmt(a.end_at)}</div>
      `;

      // Timer
      const timerSec = document.getElementById('drawerTimerSection');
      if (['published','live'].includes(a.state) && a.end_at) {
        timerSec.style.display = '';
        startTimer(a.end_at, document.getElementById('drawerTimer'));
      } else {
        timerSec.style.display = 'none';
      }

      // Mejor puja
      document.getElementById('drawerHighestBid').textContent = '$' + fmtMoney(a.highest_bid);
      document.getElementById('drawerBidsCount').textContent  = `${a.bids_count} puja(s)`;

      // Lotes
      const lotsEl = document.getElementById('drawerLots');
      document.getElementById('drawerLotsCount').textContent = a.lots.length;
      if (a.lots.length) {
        lotsEl.innerHTML = a.lots.map(l =>
          `<div style="padding:6px 0; border-bottom:1px solid var(--line);">
            <strong>${l.code}</strong> — ${l.name}
            <span class="text-muted">(base: $${fmtMoney(l.base_price)})</span>
          </div>`
        ).join('');
      } else {
        lotsEl.innerHTML = '<span class="text-muted">Sin lotes registrados.</span>';
      }

      // Historial pujas
      const feedEl = document.getElementById('drawerBids');
      if (bids.length) {
        feedEl.innerHTML = bids.slice(0, 20).map((b, i) =>
          `<div class="bid-item ${i===0?'top':''}">
            <span>Postor #${b.bidder_id} · ${fmt(b.created_at)}</span>
            <span class="bid-amount">$${fmtMoney(b.amount)}</span>
          </div>`
        ).join('');
      } else {
        feedEl.innerHTML = '<div class="text-muted" style="padding:8px 0;">Sin pujas registradas.</div>';
      }

      // Acciones contextuales
      renderDrawerActions(a);

    } catch (e) {
      document.getElementById('drawerFeedback').textContent = e.message;
    }
  }

  function renderDrawerActions(a) {
    const el = document.getElementById('drawerActions');
    const fb = document.getElementById('drawerFeedback');
    el.innerHTML = '';
    fb.textContent = '';

    const add = (label, cls, action) => {
      const b = document.createElement('button');
      b.className = `btn ${cls} btn-sm`;
      b.textContent = label;
      b.addEventListener('click', async () => {
        if (!confirm(`¿Confirmas la acción: ${label}?`)) return;
        try {
          await post(`/auctions/${a.id}/${action}`);
          setFeedback(fb, `Acción "${label}" aplicada.`);
          await renderDrawer(a.id);
          await loadAuctions();
          await loadStats();
        } catch (err) { setFeedback(fb, err.message, true); }
      });
      el.appendChild(b);
    };

    if (a.state === 'draft' || a.state === 'scheduled') add('Publicar',   'btn-ghost',   'publish');
    if (a.state === 'published')                        add('Iniciar',    'btn-ghost',   'live');
    if (['published','live'].includes(a.state))         add('Cerrar',     'btn-primary', 'close');
    if (['published','live','suspended'].includes(a.state)) add('Suspender', 'btn-warn', 'suspend');
    if (['draft','scheduled','published','live','suspended'].includes(a.state))
      add('Cancelar', 'btn-danger', 'cancel');
    if (!el.children.length)
      el.innerHTML = '<span class="text-muted">No hay acciones disponibles para este estado.</span>';
  }

  /* ══════════════════════════════════════════════════════════════════════
     TAB: POSTORES
  ══════════════════════════════════════════════════════════════════════ */

  const bidderForm = document.getElementById('bidderForm');
  const bidderFb   = document.getElementById('bidderFeedback');

  bidderForm.addEventListener('submit', async e => {
    e.preventDefault();
    setFeedback(bidderFb, 'Guardando...');
    const payload = formToObj(bidderForm);
    payload.guarantee_amount = Number(payload.guarantee_amount || 0);
    try {
      const res = await post('/bidders', payload);
      setFeedback(bidderFb, `Postor registrado — ID ${res.id}`);
      bidderForm.reset();
      await loadBidders();
    } catch (err) {
      setFeedback(bidderFb, err.message, true);
    }
  });

  document.getElementById('btnLoadBidders').addEventListener('click', loadBidders);
  document.getElementById('filterBidderState').addEventListener('change', loadBidders);

  async function loadBidders() {
    const state = document.getElementById('filterBidderState').value;
    const tbody = document.getElementById('bidderRows');
    tbody.innerHTML = '<tr class="empty-row"><td colspan="5" class="loading">Cargando...</td></tr>';
    try {
      const data = await get('/bidders' + (state ? `?state=${state}` : ''));
      const items = data.items || data;
      if (!items.length) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="5">Sin postores.</td></tr>';
        return;
      }
      tbody.innerHTML = items.map(b => `
        <tr>
          <td class="font-mono">${b.id}</td>
          <td>${b.full_name}</td>
          <td class="text-muted">${b.email}</td>
          <td>${badge(b.state)}</td>
          <td class="td-actions">
            ${b.state !== 'approved'
              ? `<button class="btn btn-primary btn-sm" data-bidder="${b.id}" data-act="approve">Aprobar</button>`
              : ''}
            ${b.state === 'approved'
              ? `<button class="btn btn-warn btn-sm" data-bidder="${b.id}" data-act="suspend">Suspender</button>`
              : ''}
          </td>
        </tr>
      `).join('');
      tbody.querySelectorAll('[data-act]').forEach(btn =>
        btn.addEventListener('click', () => handleBidderAction(btn.dataset.act, btn.dataset.bidder))
      );
    } catch (e) {
      tbody.innerHTML = `<tr class="empty-row"><td colspan="5" class="text-red">${e.message}</td></tr>`;
    }
  }

  async function handleBidderAction(action, id) {
    try {
      if (action === 'approve') {
        await post(`/bidders/${id}/approve`);
      } else if (action === 'suspend') {
        await patch(`/bidders/${id}`, { state: 'suspended' });
      }
      await loadBidders();
    } catch (e) { alert(e.message); }
  }

  /* ══════════════════════════════════════════════════════════════════════
     TAB: ADJUDICACIONES
  ══════════════════════════════════════════════════════════════════════ */

  document.getElementById('btnLoadAwards').addEventListener('click', loadAwards);
  document.getElementById('filterAwardState').addEventListener('change', loadAwards);

  let _activeAwardId = null;

  async function loadAwards() {
    const state = document.getElementById('filterAwardState').value;
    const tbody = document.getElementById('awardRows');
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7" class="loading">Cargando...</td></tr>';
    try {
      const items = await get('/awards' + (state ? `?state=${state}` : ''));
      if (!items.length) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="7">Sin adjudicaciones.</td></tr>';
        return;
      }
      tbody.innerHTML = items.map(a => `
        <tr>
          <td class="font-mono">${a.id}</td>
          <td class="font-mono">${a.auction_id}</td>
          <td class="font-mono">${a.bidder_id || '—'}</td>
          <td class="text-accent" style="font-weight:700;">$${fmtMoney(a.final_amount)}</td>
          <td>${badge(a.state)}</td>
          <td class="text-muted" style="font-size:.82rem;">${fmt(a.due_at)}</td>
          <td class="td-actions">
            ${['awarded','payment_pending'].includes(a.state)
              ? `<button class="btn btn-primary btn-sm" data-award="${a.id}" data-act="pay">Registrar pago</button>`
              : ''}
            ${a.state === 'expired'
              ? `<button class="btn btn-warn btn-sm" data-award="${a.id}" data-act="reassign">Reasignar</button>`
              : ''}
          </td>
        </tr>
      `).join('');
      tbody.querySelectorAll('[data-act]').forEach(btn =>
        btn.addEventListener('click', () => handleAwardAction(btn.dataset.act, btn.dataset.award))
      );
    } catch (e) {
      tbody.innerHTML = `<tr class="empty-row"><td colspan="7" class="text-red">${e.message}</td></tr>`;
    }
  }

  function handleAwardAction(action, awardId) {
    if (action === 'pay') {
      _activeAwardId = awardId;
      document.getElementById('payAwardId').textContent = awardId;
      document.getElementById('paymentPanel').style.display = '';
      document.getElementById('paymentPanel').scrollIntoView({ behavior: 'smooth' });
    } else if (action === 'reassign') {
      const newBidder = prompt('ID del postor al que se reasigna:');
      if (!newBidder) return;
      post(`/awards/${awardId}/reassign?new_bidder_id=${newBidder}`)
        .then(() => loadAwards())
        .catch(e => alert(e.message));
    }
  }

  document.getElementById('btnClosePayment').addEventListener('click', () => {
    document.getElementById('paymentPanel').style.display = 'none';
    _activeAwardId = null;
  });

  const paymentForm = document.getElementById('paymentForm');
  const paymentFb   = document.getElementById('paymentFeedback');

  paymentForm.addEventListener('submit', async e => {
    e.preventDefault();
    if (!_activeAwardId) return;
    setFeedback(paymentFb, 'Registrando...');
    const payload = formToObj(paymentForm);
    payload.award_id = Number(_activeAwardId);
    payload.amount   = Number(payload.amount);
    payload.state    = 'paid';
    try {
      await post('/payments', payload);
      setFeedback(paymentFb, 'Pago registrado correctamente.');
      paymentForm.reset();
      document.getElementById('paymentPanel').style.display = 'none';
      await loadAwards();
      await loadStats();
    } catch (err) {
      setFeedback(paymentFb, err.message, true);
    }
  });

  /* ══════════════════════════════════════════════════════════════════════
     INIT
  ══════════════════════════════════════════════════════════════════════ */

  (async function init() {
    await Promise.all([loadStats(), loadAuctions()]);
  })();

})();
