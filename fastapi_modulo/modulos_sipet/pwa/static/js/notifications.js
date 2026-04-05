/**
 * notifications.js — Centro de notificaciones institucional.
 *
 * Expone:
 *   NotifApp.init(containerId)          — monta la lista de notificaciones
 *   NotifApp.loadUnreadBadge(badgeId)   — actualiza el badge del ícono de campana
 *   NotifApp.markAllRead()              — marca todas como leídas
 */
const NotifApp = (() => {
  const BASE = "/api/v2/pwa/notifications";

  const SEVERITY_CLASS = {
    informativa: "notif-info",
    preventiva:  "notif-warning",
    "crítica":   "notif-danger",
  };

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  function formatRelative(iso) {
    if (!iso) return "";
    const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
    if (diff < 60) return "hace un momento";
    if (diff < 3600) return `hace ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `hace ${Math.floor(diff / 3600)} h`;
    return new Date(iso).toLocaleDateString("es", { day: "2-digit", month: "short" });
  }

  // ── Load functions ──────────────────────────────────────────────────────────

  async function fetchNotifications(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const res = await apiFetch(`${BASE}${qs ? "?" + qs : ""}`);
    if (!res.ok) throw new Error("No se pudieron cargar las notificaciones");
    return res.json();
  }

  async function fetchUnreadCount() {
    const res = await apiFetch(`${BASE}/unread-count`);
    if (!res.ok) return 0;
    const data = await res.json();
    return data.unread || 0;
  }

  async function markRead(ids) {
    if (!ids.length) return;
    await apiFetch(`${BASE}/read`, {
      method: "POST",
      body: JSON.stringify(ids),
    });
  }

  async function archiveNotif(id) {
    await apiFetch(`${BASE}/${id}/archive`, { method: "POST" });
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  function renderNotifItem(notif, onArchive) {
    const sevClass = SEVERITY_CLASS[notif.severity] || "notif-info";
    const item = el("div", `notif-item ${sevClass} ${notif.is_read ? "notif-read" : "notif-unread"}`);
    item.dataset.id = notif.id;

    const header = el("div", "notif-header");
    const title = el("span", "notif-title", notif.title);
    const time = el("span", "notif-time", formatRelative(notif.created_at));
    header.append(title, time);

    const body = el("p", "notif-body", notif.body || "");

    const actions = el("div", "notif-actions");
    if (!notif.is_read) {
      const readBtn = el("button", "btn-link", "Marcar leída");
      readBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        await markRead([notif.id]);
        item.classList.replace("notif-unread", "notif-read");
        readBtn.remove();
        updateBadgeCount(-1);
      });
      actions.appendChild(readBtn);
    }

    const archiveBtn = el("button", "btn-link notif-archive", "Archivar");
    archiveBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      await archiveNotif(notif.id);
      item.remove();
      if (onArchive) onArchive(notif.id);
    });
    actions.appendChild(archiveBtn);

    if (notif.ref_type) {
      const link = el("a", "notif-ref", `Ver ${notif.ref_type}`);
      link.href = buildRefUrl(notif.ref_type, notif.ref_id);
      actions.appendChild(link);
    }

    item.append(header, body, actions);
    return item;
  }

  function buildRefUrl(refType, refId) {
    const map = {
      activity: `/activities`,
      conversation: `/conversations/${refId}`,
      evidence: `/activities`,
    };
    return map[refType] || "/dashboard";
  }

  // ── Badge ───────────────────────────────────────────────────────────────────

  let _badgeEl = null;
  let _badgeCount = 0;

  function setBadge(count) {
    _badgeCount = count;
    if (_badgeEl) {
      _badgeEl.textContent = count > 99 ? "99+" : String(count);
      _badgeEl.classList.toggle("is-hidden", count === 0);
    }
    if ("setAppBadge" in navigator) {
      count > 0 ? navigator.setAppBadge(count) : navigator.clearAppBadge();
    }
  }

  function updateBadgeCount(delta) {
    setBadge(Math.max(0, _badgeCount + delta));
  }

  async function loadUnreadBadge(badgeId) {
    _badgeEl = document.getElementById(badgeId);
    const count = await fetchUnreadCount();
    setBadge(count);
  }

  // ── Init ────────────────────────────────────────────────────────────────────

  async function init(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '<p class="loading-text">Cargando notificaciones…</p>';

    const markAllBtn = document.getElementById("notif-mark-all");
    if (markAllBtn) {
      markAllBtn.addEventListener("click", () => markAllRead());
    }

    try {
      const notifs = await fetchNotifications({ limit: 50 });
      container.innerHTML = "";
      if (!notifs.length) {
        container.innerHTML = '<p class="empty-state">No tienes notificaciones.</p>';
        return;
      }

      const unreadIds = notifs.filter((n) => !n.is_read).map((n) => n.id);
      notifs.forEach((n) => container.appendChild(renderNotifItem(n, null)));

      // mark visible ones as read after 2 s
      if (unreadIds.length) {
        setTimeout(async () => {
          await markRead(unreadIds);
          container.querySelectorAll(".notif-unread").forEach((el) => {
            el.classList.replace("notif-unread", "notif-read");
          });
          setBadge(0);
        }, 2000);
      }
    } catch (err) {
      container.innerHTML = `<p class="error-state">${err.message}</p>`;
    }
  }

  async function markAllRead() {
    const unread = document.querySelectorAll(".notif-unread");
    const ids = [...unread].map((el) => Number(el.dataset.id));
    if (!ids.length) return;
    await markRead(ids);
    unread.forEach((el) => el.classList.replace("notif-unread", "notif-read"));
    setBadge(0);
    toast("Todas marcadas como leídas", "success");
  }

  return { init, loadUnreadBadge, markAllRead };
})();

window.NotifApp = NotifApp;
