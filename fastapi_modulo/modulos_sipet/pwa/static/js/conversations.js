/**
 * conversations.js — Módulo de canal de conversaciones institucional.
 *
 * Expone:
 *   ConvApp.init(containerId)  — monta la lista de conversaciones
 *   ConvApp.openChat(convId)   — monta la pantalla de chat de una conversación
 */
const ConvApp = (() => {
  const BASE = "/api/v2/pwa/conversations";

  // ── helpers ────────────────────────────────────────────────────────────────

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  function formatTime(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    const now = new Date();
    if (d.toDateString() === now.toDateString()) {
      return d.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
    }
    return d.toLocaleDateString("es", { day: "2-digit", month: "short" });
  }

  // ── Conversation list ───────────────────────────────────────────────────────

  async function loadConversations() {
    const res = await apiFetch(BASE);
    if (!res.ok) throw new Error("No se pudieron cargar las conversaciones");
    return res.json();
  }

  function renderConvItem(conv) {
    const item = el("div", "conv-item");
    item.dataset.id = conv.id;

    const avatar = el("div", "conv-avatar", (conv.title || "?")[0].toUpperCase());
    const body = el("div", "conv-body");
    const top = el("div", "conv-top");
    const name = el("span", "conv-name", conv.title || `conversación #${conv.id}`);
    const time = el("span", "conv-time", formatTime(conv.updated_at));

    top.append(name, time);

    const preview = el("p", "conv-preview", conv.last_message?.body || "Sin mensajes aún");
    const row = el("div", "conv-row");

    if (conv.unread_count > 0) {
      const badge = el("span", "conv-badge", String(conv.unread_count));
      row.appendChild(badge);
    }

    body.append(top, preview, row);
    item.append(avatar, body);

    item.addEventListener("click", () => {
      window.location.href = `/conversations/${conv.id}`;
    });
    return item;
  }

  async function init(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '<p class="loading-text">Cargando conversaciones…</p>';

    try {
      const convs = await loadConversations();
      container.innerHTML = "";
      if (!convs.length) {
        container.innerHTML = '<p class="empty-state">No tienes conversaciones activas.</p>';
        return;
      }
      convs.forEach((c) => container.appendChild(renderConvItem(c)));
    } catch (err) {
      container.innerHTML = `<p class="error-state">${err.message}</p>`;
    }
  }

  // ── Chat screen ─────────────────────────────────────────────────────────────

  let _chatConvId = null;
  let _chatPool = null;

  async function loadMessages(convId, beforeId = null) {
    const qs = beforeId ? `?before_id=${beforeId}&limit=30` : "?limit=30";
    const res = await apiFetch(`${BASE}/${convId}/messages${qs}`);
    if (!res.ok) throw new Error("No se pudieron cargar los mensajes");
    return res.json();
  }

  async function sendMessage(convId, body, replyToId = null) {
    const payload = { conversation_id: convId, body };
    if (replyToId) payload.reply_to_id = replyToId;
    const res = await apiFetchWithQueue(`${BASE}/${convId}/messages`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Error al enviar mensaje");
    return res.json();
  }

  async function markRead(convId, lastMsgId) {
    await apiFetch(`${BASE}/${convId}/read?last_message_id=${lastMsgId}`, { method: "POST" });
  }

  function renderMessage(msg, currentUserId) {
    const isOwn = msg.sender_id === currentUserId;
    const wrap = el("div", `msg-wrap ${isOwn ? "msg-own" : "msg-other"}`);
    const bubble = el("div", "msg-bubble");
    const text = el("p", "msg-text", msg.body);
    bubble.appendChild(text);

    if (msg.edited_at) {
      bubble.appendChild(el("span", "msg-edited", "editado"));
    }

    const meta = el("div", "msg-meta", formatTime(msg.created_at));
    bubble.appendChild(meta);

    if (msg.attachments?.length) {
      msg.attachments.forEach((att) => {
        const link = el("a", "msg-attachment", `📎 ${att.filename}`);
        link.href = att.file_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        bubble.appendChild(link);
      });
    }

    wrap.appendChild(bubble);
    return wrap;
  }

  function openChat(convId) {
    _chatConvId = convId;

    const list = document.getElementById("chat-messages");
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    if (!list || !form || !input) return;

    // load initial messages
    loadMessages(convId).then((msgs) => {
      list.innerHTML = "";
      if (!msgs.length) {
        list.innerHTML = '<p class="empty-state">No hay mensajes aún. ¡Sé el primero en escribir!</p>';
        return;
      }
      const currentUserId = _parseUserId();
      msgs.forEach((m) => list.appendChild(renderMessage(m, currentUserId)));
      list.scrollTop = list.scrollHeight;

      const lastId = msgs[msgs.length - 1]?.id;
      if (lastId) markRead(convId, lastId);
    }).catch((err) => {
      list.innerHTML = `<p class="error-state">${err.message}</p>`;
    });

    // send handler
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      try {
        const msg = await sendMessage(convId, text);
        const currentUserId = _parseUserId();
        list.appendChild(renderMessage(msg, currentUserId));
        list.scrollTop = list.scrollHeight;
        markRead(convId, msg.id);
      } catch (err) {
        toast(err.message, "error");
      }
    });

    // poll every 5 s for new messages
    _chatPool = setInterval(async () => {
      const items = list.querySelectorAll(".msg-wrap");
      const lastId = [...items].pop()?.dataset?.id;
      if (!lastId) return;
      try {
        const newer = await loadMessages(convId, null);
        const existingIds = new Set([...items].map((n) => n.dataset?.id));
        const currentUserId = _parseUserId();
        newer.forEach((m) => {
          if (!existingIds.has(String(m.id))) {
            const node = renderMessage(m, currentUserId);
            node.dataset.id = m.id;
            list.appendChild(node);
          }
        });
        list.scrollTop = list.scrollHeight;
        const newLast = newer[newer.length - 1]?.id;
        if (newLast) markRead(convId, newLast);
      } catch (_) { /* ignore */ }
    }, 5000);
  }

  function destroyChat() {
    if (_chatPool) clearInterval(_chatPool);
    _chatPool = null;
  }

  function _parseUserId() {
    // JWT payload is base64url — decode sub claim
    const token = Auth.getAccess();
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
      return Number(payload.sub);
    } catch (_) {
      return null;
    }
  }

  return { init, openChat, destroyChat };
})();

window.ConvApp = ConvApp;
