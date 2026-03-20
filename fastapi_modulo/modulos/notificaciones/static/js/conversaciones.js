(() => {
  "use strict";

  // ---------------------------------------------------------------------------
  // Referencias al DOM
  // ---------------------------------------------------------------------------
  const $ = (s) => document.querySelector(s);

  const pageEl           = $(".wa-page");
  const shellEl          = $(".wa-shell");
  const listEl           = $("#wa-list");
  const searchEl         = $("#wa-search");
  const messagesEl       = $("#wa-messages");
  const formEl           = $("#wa-form");
  const inputEl          = $("#wa-input");
  const topkEl           = $("#wa-topk");
  const topkWrap         = $("#wa-topk-wrap");
  const notifyScopeWrap  = $("#wa-notify-scope-wrap");
  const notifyScopeEl    = $("#wa-notify-scope");
  const chatTitleEl      = $("#wa-chat-title");
  const chatSubtitleEl   = $("#wa-chat-subtitle");
  const chatAvatarEl     = $("#wa-chat-avatar-el");
  const indexBtn         = $("#wa-index-btn");
  const newBtn           = $("#wa-new-btn");
  const newGroupBtn      = $("#wa-new-group-btn");
  const notifyBtn        = $("#wa-notify-btn");
  const indexStatusEl    = $("#wa-index-status");
  const delBtn           = $("#wa-del-conv");
  const modal            = $("#wa-modal");
  const modalClose       = $("#wa-modal-close");
  const modalSearch      = $("#wa-modal-search");
  const modalList        = $("#wa-modal-list");
  const groupModal       = $("#wa-group-modal");
  const groupModalClose  = $("#wa-group-modal-close");
  const groupNameEl      = $("#wa-group-name");
  const groupSearchEl    = $("#wa-group-search");
  const groupListEl      = $("#wa-group-list");
  const groupCreateBtn   = $("#wa-group-create");
  const groupSelectedEl  = $("#wa-group-selected");
  const floatingStack    = $("#wa-floating-stack");
  const sendBtn          = $("#wa-send-btn");

  const avanAvatarUrl = String(
    pageEl?.getAttribute("data-wa-avatar") || "/templates/imagenes/lobo.jpg"
  );

  // ---------------------------------------------------------------------------
  // Estado de la aplicación
  // ---------------------------------------------------------------------------
  let currentConvId   = "";
  let currentConvType = "";
  let avanConvs       = [];
  let dmConvs         = [];
  let groupConvs      = [];
  let allUsers        = [];
  let sending         = false;
  let moduleAccess    = null;
  let hasInternalConversationAccess = false;
  let selectedGroupUsers = new Set();

  // Control de peticiones en vuelo para cancelarlas si el usuario cambia de conv
  let fetchConvController = null;

  // ---------------------------------------------------------------------------
  // Utilidades
  // ---------------------------------------------------------------------------

  const getCookieValue = (name) => {
    const prefix = `${name}=`;
    const found = String(document.cookie || "")
      .split(";")
      .map((p) => p.trim())
      .find((p) => p.startsWith(prefix));
    return found ? decodeURIComponent(found.slice(prefix.length)) : "";
  };

  const currentUsername = String(getCookieValue("user_name") || "").trim().toLowerCase();

  /** Escapa HTML para evitar XSS en cualquier contenido interpolado. */
  const esc = (s) =>
    String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const initials = (s) => {
    const t = String(s ?? "").trim();
    if (!t) return "??";
    const parts = t.split(/\s+/).filter(Boolean);
    return parts.length === 1
      ? parts[0].slice(0, 2).toUpperCase()
      : (parts[0][0] + parts[1][0]).toUpperCase();
  };

  const avatarHtml = (label, imgUrl) =>
    imgUrl
      ? `<img src="${esc(imgUrl)}" alt="${esc(label)}" loading="lazy" onerror="this.style.display='none'">`
      : esc(initials(label));

  /** Elimina referencias de fuentes [S1], [S2]… del texto del asistente. */
  const cleanAssistantText = (value) =>
    String(value ?? "")
      .replace(/\s*\[S\d+\]/gi, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();

  const fmtTime = (iso) => {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      const now = new Date();
      return d.toDateString() === now.toDateString()
        ? d.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" })
        : d.toLocaleDateString("es", { day: "2-digit", month: "2-digit" });
    } catch {
      return String(iso).slice(0, 10);
    }
  };

  const dmConversationId = (otherUsername) => {
    const other = String(otherUsername || "").trim().toLowerCase();
    if (!other || !currentUsername) return "";
    const pair = [currentUsername, other].sort((a, b) => a.localeCompare(b));
    return `dm-${pair[0]}_${pair[1]}`;
  };

  /** Crea una función debounced para reducir llamadas redundantes (p.ej. búsqueda). */
  const debounce = (fn, ms = 250) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), ms);
    };
  };

  // ---------------------------------------------------------------------------
  // Notificaciones flotantes
  // ---------------------------------------------------------------------------

  const showIndexStatus = (text, isErr = false) => {
    if (!indexStatusEl) return;
    indexStatusEl.style.display = "block";
    indexStatusEl.textContent = String(text || "");
    indexStatusEl.style.color = isErr ? "var(--fallback-er, oklch(var(--er)))" : "";
  };

  const showFloatingNotification = (title, message) => {
    if (!floatingStack) return;
    const card = document.createElement("article");
    card.className = "wa-floating-note";
    card.innerHTML = `<strong>${esc(title || "Notificación")}</strong><div>${esc(message || "")}</div>`;
    floatingStack.appendChild(card);
    requestAnimationFrame(() => card.classList.add("show"));
    window.setTimeout(() => {
      card.classList.remove("show");
      window.setTimeout(() => card.remove(), 220);
    }, 4200);
  };

  // ---------------------------------------------------------------------------
  // Render de estados vacíos / sin acceso
  // ---------------------------------------------------------------------------

  const renderNoAccess = (message) => {
    if (!shellEl) return;
    shellEl.innerHTML = `<article class="wa-empty-state">${esc(
      message || "Sin acceso a Conversaciones."
    )}</article>`;
  };

  // ---------------------------------------------------------------------------
  // Lista de conversaciones unificada
  // ---------------------------------------------------------------------------

  const getUnifiedConversations = () => {
    const latestAvan = avanConvs[0] ?? null;
    const avanEntry = {
      conv_id: latestAvan?.conv_id || "conv-avan",
      type: "avan",
      label: "AVAN",
      img: avanAvatarUrl,
      last_at: latestAvan?.last_at || "",
      last_message: latestAvan?.last_message || "Nueva conversación con AVAN",
      unread: 0,
    };
    return [avanEntry, ...groupConvs, ...dmConvs];
  };

  const renderList = () => {
    const term = (searchEl?.value ?? "").trim().toLowerCase();
    const filtered = getUnifiedConversations().filter((c) => {
      if (!term) return true;
      return `${c.label || ""} ${c.last_message || ""} ${c.conv_id || ""}`
        .toLowerCase()
        .includes(term);
    });

    if (!listEl) return;

    if (!filtered.length) {
      listEl.innerHTML = `<div class="wa-empty">Sin conversaciones. Usa + o 👥 para iniciar una.</div>`;
      return;
    }

    listEl.innerHTML = filtered
      .map((c) => {
        const active = currentConvId === c.conv_id ? "active" : "";
        const badge =
          c.unread > 0
            ? `<span class="wa-unread-badge">${c.unread > 99 ? "99+" : c.unread}</span>`
            : "";
        const subtitle =
          c.type === "group" ? "Grupo" : c.type === "dm" ? "Directo" : "IA";
        return `
          <button
            type="button"
            class="wa-item ${active}"
            data-id="${esc(c.conv_id)}"
            data-type="${esc(c.type)}"
            aria-current="${active ? "true" : "false"}"
          >
            <div class="wa-item-avatar">${avatarHtml(c.label, c.img)}</div>
            <div class="wa-item-main">
              <div class="wa-item-top">
                <div class="wa-item-name">${esc(c.label)}</div>
                <div class="wa-item-time">${esc(fmtTime(c.last_at))} ${badge}</div>
              </div>
              <div class="wa-item-msg">${esc(c.last_message || subtitle)}</div>
            </div>
          </button>`;
      })
      .join("");

    listEl.querySelectorAll(".wa-item").forEach((btn) => {
      btn.addEventListener("click", () =>
        openConv(btn.getAttribute("data-id"), btn.getAttribute("data-type"))
      );
    });
  };

  // ---------------------------------------------------------------------------
  // Carga de datos desde la API
  // ---------------------------------------------------------------------------

  const refreshModuleAccess = async () => {
    const res = await fetch("/api/v1/conversaciones/access");
    const data = await res.json();

    if (!res.ok || !data?.success) {
      if (res.status === 403) {
        hasInternalConversationAccess = false;
        moduleAccess = {
          role: "",
          can_create_groups: false,
          can_send_notifications: false,
          can_access_ai: true,
        };
        if (newGroupBtn) newGroupBtn.style.display = "none";
        return moduleAccess;
      }
      throw new Error((data?.error || data?.detail) || "Sin acceso");
    }

    moduleAccess = { ...(data.data || {}), can_access_ai: true };
    hasInternalConversationAccess = true;
    if (newGroupBtn) {
      newGroupBtn.style.display = moduleAccess.can_create_groups ? "inline-flex" : "none";
    }
    return moduleAccess;
  };

  const loadModuleUsers = async () => {
    if (!hasInternalConversationAccess) { allUsers = []; return; }
    const res = await fetch("/api/v1/conversaciones/users");
    const data = await res.json();
    if (!res.ok || !data?.success) {
      throw new Error((data?.error || data?.detail) || "No se pudieron cargar usuarios");
    }
    allUsers = Array.isArray(data.data) ? data.data : [];
  };

  const loadAvanConvs = async () => {
    try {
      const res = await fetch("/api/v1/ia/rag/conversations?limit=80");
      const data = await res.json();
      avanConvs = data?.success
        ? (data.data || []).map((item) => ({
            conv_id: item.conversation_id,
            type: "avan",
            label: "AVAN",
            img: avanAvatarUrl,
            last_at: item.last_at,
            last_message: item.last_answer || item.last_question || "",
            unread: 0,
          }))
        : [];
    } catch {
      avanConvs = [];
    }
  };

  const loadDmConvs = async () => {
    if (!hasInternalConversationAccess) { dmConvs = []; return; }
    const res = await fetch("/api/v1/conversaciones/direct");
    const data = await res.json();
    if (!res.ok || !data?.success) {
      throw new Error((data?.error || data?.detail) || "No se pudieron cargar conversaciones directas");
    }
    dmConvs = (data.data || []).map((item) => {
      const user = allUsers.find((u) => u.username === item.other_user);
      return {
        conv_id: item.conversation_id,
        type: "dm",
        label: user?.full_name || item.other_user || "Usuario",
        img: user?.imagen || "",
        last_at: item.last_at,
        last_message: item.last_message || "",
        unread: item.unread || 0,
      };
    });
  };

  const loadGroupConvs = async () => {
    if (!hasInternalConversationAccess) { groupConvs = []; return; }
    const res = await fetch("/api/v1/conversaciones/groups");
    const data = await res.json();
    if (!res.ok || !data?.success) {
      throw new Error((data?.error || data?.detail) || "No se pudieron cargar grupos");
    }
    groupConvs = (data.data || []).map((item) => ({
      conv_id: item.conversation_id,
      type: "group",
      label: item.group_name || "Grupo",
      img: "",
      last_at: item.last_at,
      last_message: item.last_message || "",
      unread: item.unread || 0,
      members: item.member_usernames || [],
    }));
  };

  const loadAll = async () => {
    await Promise.all([loadAvanConvs(), loadDmConvs(), loadGroupConvs()]);
    renderList();
  };

  // ---------------------------------------------------------------------------
  // Render de mensajes
  // ---------------------------------------------------------------------------

  const renderMessages = (rows, type) => {
    if (!messagesEl) return;
    if (!rows?.length) {
      messagesEl.innerHTML = '<div class="wa-empty">No hay mensajes aún. Escribe el primero.</div>';
      return;
    }
    messagesEl.innerHTML = rows
      .map((row) => {
        const isMine =
          type === "avan"
            ? String(row.message_type || "").toLowerCase() === "user"
            : row.is_mine === true;
        const css = isMine ? "wa-msg wa-msg--out" : "wa-msg wa-msg--in";
        const meta = isMine
          ? fmtTime(row.created_at) || "Tú"
          : type === "avan"
          ? "AVAN"
          : esc(row.from_username || "");
        const body =
          !isMine && type === "avan"
            ? cleanAssistantText(row.message_text ?? row.message ?? "")
            : String(row.message_text ?? row.message ?? "");
        return `<div class="${css}">
          <div class="wa-msg-body">${esc(body)}</div>
          <div class="wa-msg-meta">${meta}</div>
        </div>`;
      })
      .join("");
    messagesEl.scrollTop = messagesEl.scrollHeight;
  };

  // ---------------------------------------------------------------------------
  // Cabecera de chat — visibilidad de controles
  // ---------------------------------------------------------------------------

  const updateHeaderActions = () => {
    if (topkWrap) topkWrap.style.display = currentConvType === "avan" ? "flex" : "none";

    const isInternal = hasInternalConversationAccess;
    const isDmOrGroup = currentConvType === "dm" || currentConvType === "group";

    if (delBtn) delBtn.style.display = isInternal && isDmOrGroup ? "inline-flex" : "none";

    const canNotify = moduleAccess?.can_send_notifications && isInternal && isDmOrGroup;
    if (notifyBtn) notifyBtn.style.display = canNotify ? "inline-flex" : "none";

    if (notifyScopeWrap && notifyScopeEl) {
      const maxScope = String(moduleAccess?.notification_scope || "").trim().toLowerCase();
      const allowed = new Set(["conversation"]);
      if (maxScope === "department" || maxScope === "company") allowed.add("department");
      if (maxScope === "company") allowed.add("company");

      Array.from(notifyScopeEl.options).forEach((opt) => {
        opt.hidden = !allowed.has(String(opt.value || "").trim().toLowerCase());
      });
      if (!allowed.has(String(notifyScopeEl.value || "").trim().toLowerCase())) {
        notifyScopeEl.value = [...allowed][0];
      }
      notifyScopeWrap.style.display = canNotify ? "flex" : "none";
    }

    if (newBtn) newBtn.style.display = isInternal ? "inline-flex" : "none";
  };

  // ---------------------------------------------------------------------------
  // Abrir conversación
  // ---------------------------------------------------------------------------

  const startDmWithUser = (username) => {
    const user = allUsers.find((u) => u.username === username);
    const convId = dmConversationId(username);
    if (!convId) return;
    if (!dmConvs.find((c) => c.conv_id === convId)) {
      dmConvs.unshift({
        conv_id: convId,
        type: "dm",
        label: user?.full_name || username,
        img: user?.imagen || "",
        last_at: "",
        last_message: "",
        unread: 0,
      });
    }
    currentConvId = convId;
    currentConvType = "dm";
    if (chatTitleEl) chatTitleEl.textContent = user?.full_name || username;
    if (chatSubtitleEl) chatSubtitleEl.textContent = "Mensaje directo";
    if (chatAvatarEl) chatAvatarEl.innerHTML = avatarHtml(user?.full_name || username, user?.imagen || "");
    updateHeaderActions();
    renderMessages([], "dm");
    renderList();
  };

  const openConv = async (convId, type) => {
    // Cancela petición anterior si sigue en vuelo
    if (fetchConvController) fetchConvController.abort();
    fetchConvController = new AbortController();
    const { signal } = fetchConvController;

    currentConvId   = convId || "";
    currentConvType = type  || "";
    renderList();
    updateHeaderActions();

    let label = convId;
    let img   = "";

    if (type === "avan") {
      label = "AVAN";
      img   = avanAvatarUrl;
    } else if (type === "group") {
      const group = groupConvs.find((c) => c.conv_id === convId);
      label = group?.label || "Grupo";
    } else {
      const direct = dmConvs.find((c) => c.conv_id === convId);
      label = direct?.label || convId;
      img   = direct?.img  || "";
    }

    if (chatTitleEl)    chatTitleEl.textContent    = label || "Conversación";
    if (chatSubtitleEl) chatSubtitleEl.textContent =
      type === "avan" ? "Agente IA AVAN" : type === "group" ? "Grupo" : "Mensaje directo";
    if (chatAvatarEl)   chatAvatarEl.innerHTML = avatarHtml(label, img);

    if (type === "avan" && !avanConvs.find((c) => c.conv_id === convId)) {
      renderMessages(
        [{ message_text: "Conversación iniciada. Escribe tu mensaje.", is_mine: false, created_at: "" }],
        "avan"
      );
      return;
    }

    try {
      const url =
        type === "avan"
          ? `/api/v1/ia/rag/conversations/${encodeURIComponent(convId)}`
          : type === "group"
          ? `/api/v1/conversaciones/groups/${encodeURIComponent(convId)}`
          : `/api/v1/conversaciones/direct/${encodeURIComponent(convId)}`;

      const res  = await fetch(url, { signal });
      const data = await res.json();

      if (!res.ok || !data?.success) {
        throw new Error((data?.error || data?.detail) || "No se pudo cargar la conversación");
      }
      renderMessages(data.data || [], type);
    } catch (err) {
      if (err.name === "AbortError") return; // petición cancelada intencionalmente
      renderMessages(
        [{ message_text: err?.message || "No se pudo cargar.", is_mine: false, created_at: "" }],
        type
      );
    }

    await loadAll();
  };

  // ---------------------------------------------------------------------------
  // Envío de mensajes
  // ---------------------------------------------------------------------------

  const sendMsg = async (event) => {
    event.preventDefault();
    const txt = String(inputEl?.value || "").trim();
    if (!txt || sending) return;
    if (!currentConvId) {
      window.alert("Selecciona una conversación primero.");
      return;
    }

    sending = true;
    if (sendBtn) sendBtn.disabled = true;
    if (inputEl) inputEl.value = "";

    try {
      if (currentConvType === "avan") {
        const res = await fetch("/api/v1/ia/rag/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_id: currentConvId,
            message: txt,
            top_k: Number(topkEl?.value || 6),
          }),
        });
        const data = await res.json();
        if (!res.ok || !data?.success)
          throw new Error((data?.error || data?.detail) || "No se pudo enviar");
        currentConvId = data.data?.conversation_id || currentConvId;

      } else if (currentConvType === "group") {
        const res = await fetch(
          `/api/v1/conversaciones/groups/${encodeURIComponent(currentConvId)}/send`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: txt }),
          }
        );
        const data = await res.json();
        if (!res.ok || !data?.success)
          throw new Error((data?.error || data?.detail) || "No se pudo enviar");

      } else {
        const res = await fetch("/api/v1/conversaciones/direct/send", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ conversation_id: currentConvId, message: txt }),
        });
        const data = await res.json();
        if (!res.ok || !data?.success)
          throw new Error((data?.error || data?.detail) || "No se pudo enviar");
        currentConvId = data.data?.conversation_id || currentConvId;
      }

      await openConv(currentConvId, currentConvType);
    } catch (err) {
      window.alert(err?.message || "No se pudo enviar");
      if (inputEl) inputEl.value = txt;
    } finally {
      sending = false;
      if (sendBtn) sendBtn.disabled = false;
      inputEl?.focus();
    }
  };

  // ---------------------------------------------------------------------------
  // Eliminar conversación
  // ---------------------------------------------------------------------------

  const deleteConv = async () => {
    if (!currentConvId || (currentConvType !== "dm" && currentConvType !== "group")) return;
    if (!window.confirm("¿Eliminar esta conversación?")) return;
    try {
      const url =
        currentConvType === "group"
          ? `/api/v1/conversaciones/groups/${encodeURIComponent(currentConvId)}`
          : `/api/v1/conversaciones/direct/${encodeURIComponent(currentConvId)}`;
      const res  = await fetch(url, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok || !data?.success)
        throw new Error((data?.error || data?.detail) || "No se pudo eliminar");

      currentConvId   = "";
      currentConvType = "";
      if (chatTitleEl)    chatTitleEl.textContent    = "Selecciona una conversación";
      if (chatSubtitleEl) chatSubtitleEl.textContent = "—";
      if (chatAvatarEl)   chatAvatarEl.innerHTML     = "AV";
      updateHeaderActions();
      if (messagesEl) messagesEl.innerHTML = '<div class="wa-empty">Conversación eliminada.</div>';
      await loadAll();
    } catch (err) {
      window.alert(err?.message || "No se pudo eliminar");
    }
  };

  // ---------------------------------------------------------------------------
  // Modal de nuevo DM
  // ---------------------------------------------------------------------------

  const openUserModal = () => {
    if (!modal) return;
    modal.style.display = "flex";
    if (modalSearch) modalSearch.value = "";
    renderModalList();
    modalSearch?.focus();
  };

  const renderModalList = () => {
    if (!modalList) return;
    const term = String(modalSearch?.value || "").trim().toLowerCase();
    const filtered = allUsers.filter(
      (u) => !term || `${u.full_name} ${u.username}`.toLowerCase().includes(term)
    );
    if (!filtered.length) {
      modalList.innerHTML = '<li class="wa-empty">Sin usuarios encontrados.</li>';
      return;
    }
    modalList.innerHTML = filtered
      .map(
        (u) => `
        <li class="wa-modal-user" data-username="${esc(u.username)}">
          <div class="wa-modal-avatar">${avatarHtml(u.full_name || u.username, u.imagen)}</div>
          <div class="wa-modal-info">
            <strong>${esc(u.full_name || u.username)}</strong>
            <small>${esc(u.conversation_access?.role || u.role || u.username)}</small>
          </div>
        </li>`
      )
      .join("");
    modalList.querySelectorAll(".wa-modal-user").forEach((item) => {
      item.addEventListener("click", () => {
        const username = item.getAttribute("data-username");
        if (modal) modal.style.display = "none";
        if (username) startDmWithUser(username);
      });
    });
  };

  // ---------------------------------------------------------------------------
  // Modal de nuevo grupo
  // ---------------------------------------------------------------------------

  const openGroupModal = () => {
    if (!moduleAccess?.can_create_groups || !groupModal) return;
    selectedGroupUsers = new Set();
    groupModal.style.display = "flex";
    if (groupNameEl) groupNameEl.value = "";
    if (groupSearchEl) groupSearchEl.value = "";
    renderGroupList();
    groupNameEl?.focus();
  };

  const renderGroupList = () => {
    if (!groupListEl) return;
    const term = String(groupSearchEl?.value || "").trim().toLowerCase();
    const filtered = allUsers.filter(
      (u) => !term || `${u.full_name} ${u.username}`.toLowerCase().includes(term)
    );
    if (!filtered.length) {
      groupListEl.innerHTML = '<li class="wa-empty">Sin usuarios encontrados.</li>';
      return;
    }
    groupListEl.innerHTML = filtered
      .map(
        (u) => `
        <li class="wa-modal-user">
          <div class="wa-modal-avatar">${avatarHtml(u.full_name || u.username, u.imagen)}</div>
          <div class="wa-modal-info">
            <strong>${esc(u.full_name || u.username)}</strong>
            <small>${esc(u.username)}</small>
          </div>
          <input
            type="checkbox"
            data-group-user="${esc(u.username)}"
            ${selectedGroupUsers.has(u.username) ? "checked" : ""}
          >
        </li>`
      )
      .join("");

    groupListEl
      .querySelectorAll("input[type='checkbox'][data-group-user]")
      .forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
          const username = checkbox.getAttribute("data-group-user");
          if (!username) return;
          checkbox.checked ? selectedGroupUsers.add(username) : selectedGroupUsers.delete(username);
          if (groupSelectedEl) groupSelectedEl.textContent = `${selectedGroupUsers.size} seleccionados`;
        });
      });

    if (groupSelectedEl) groupSelectedEl.textContent = `${selectedGroupUsers.size} seleccionados`;
  };

  const createGroup = async () => {
    const groupName = String(groupNameEl?.value || "").trim();
    const members   = Array.from(selectedGroupUsers);
    if (!groupName) { window.alert("Escribe un nombre para el grupo."); return; }
    if (!members.length) { window.alert("Selecciona al menos un usuario."); return; }

    if (groupCreateBtn) groupCreateBtn.disabled = true;
    try {
      const res  = await fetch("/api/v1/conversaciones/groups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ group_name: groupName, member_usernames: members }),
      });
      const data = await res.json();
      if (!res.ok || !data?.success)
        throw new Error((data?.error || data?.detail) || "No se pudo crear el grupo");

      if (groupModal) groupModal.style.display = "none";
      await loadAll();
      await openConv(data.data?.conversation_id, "group");
    } catch (err) {
      window.alert(err?.message || "No se pudo crear el grupo");
    } finally {
      if (groupCreateBtn) groupCreateBtn.disabled = false;
    }
  };

  // ---------------------------------------------------------------------------
  // Notificación de módulo
  // ---------------------------------------------------------------------------

  const sendModuleNotification = async () => {
    if (
      !moduleAccess?.can_send_notifications ||
      !currentConvId ||
      (currentConvType !== "dm" && currentConvType !== "group")
    ) return;

    const message = window.prompt("Mensaje de notificación");
    if (!message?.trim()) return;
    const scope = String(notifyScopeEl?.value || "conversation").trim().toLowerCase() || "conversation";

    try {
      const res  = await fetch("/api/v1/conversaciones/notifications/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: currentConvId,
          message: message.trim(),
          scope,
        }),
      });
      const data = await res.json();
      if (!res.ok || !data?.success)
        throw new Error((data?.error || data?.detail) || "No se pudo enviar la notificación");
      showFloatingNotification("Notificación enviada", message.trim());
    } catch (err) {
      window.alert(err?.message || "No se pudo enviar la notificación");
    }
  };

  // ---------------------------------------------------------------------------
  // Índice RAG
  // ---------------------------------------------------------------------------

  const refreshIndexStatus = async () => {
    try {
      const res  = await fetch("/api/v1/ia/rag/index-status");
      const data = await res.json();
      if (!data?.success) {
        if (res.status === 403 && indexBtn) indexBtn.disabled = true;
        return;
      }
      const info = data.data || {};
      showIndexStatus(`Índice: ${info.documents ?? 0} docs · ${info.chunks ?? 0} chunks`);
    } catch (err) {
      showIndexStatus(err?.message || "Error índice", true);
    }
  };

  const runIndex = async () => {
    if (indexBtn) indexBtn.disabled = true;
    showIndexStatus("Indexando documentos…");
    try {
      const res  = await fetch("/api/v1/ia/rag/index-documents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limit: 500 }),
      });
      const data = await res.json();
      if (!res.ok || !data?.success)
        throw new Error((data?.error || data?.detail) || "Error");
      const info = data.data || {};
      showIndexStatus(
        `Indexación lista: ${info.indexed_documents ?? 0} docs, ${info.indexed_chunks ?? 0} chunks`
      );
      await loadAll();
    } catch (err) {
      showIndexStatus(err?.message || "Error", true);
    } finally {
      if (indexBtn) indexBtn.disabled = false;
      refreshIndexStatus();
    }
  };

  // ---------------------------------------------------------------------------
  // Tiempo real: SSE para conteo de no leídos + notificaciones flotantes
  // Reemplaza los setInterval de polling de la versión anterior.
  // ---------------------------------------------------------------------------

  let sseSource = null;

  const startSSE = () => {
    if (!hasInternalConversationAccess) return;
    if (sseSource) { sseSource.close(); sseSource = null; }

    sseSource = new EventSource("/api/v1/notificaciones/stream");

    sseSource.onmessage = async (event) => {
      let payload;
      try { payload = JSON.parse(event.data); } catch { return; }

      // Actualiza badge de no leídas en el botón de nueva conversación
      const unread = payload?.unread ?? 0;
      if (newBtn) {
        newBtn.setAttribute(
          "title",
          unread > 0 ? `Nueva conversación · ${unread} pendientes` : "Nueva conversación"
        );
      }

      // Recarga lista para reflejar nuevos mensajes
      await loadAll();
    };

    sseSource.onerror = () => {
      // El navegador reconecta automáticamente tras un error de red.
      // Solo cerramos si la conexión se dio de baja explícitamente.
    };
  };

  /** Sondeo de notificaciones flotantes pendientes (bandeja inbox). */
  const pollFloatingNotifications = async () => {
    if (!hasInternalConversationAccess) return;
    try {
      const res  = await fetch("/api/v1/conversaciones/notifications/inbox");
      const data = await res.json();
      if (!res.ok || !data?.success) return;
      (data.data || []).forEach((item) => {
        showFloatingNotification(
          `Mensaje de ${item.from_username || "Sistema"}`,
          item.message_text || ""
        );
      });
    } catch { /* silencioso */ }
  };

  /** Sondeo ligero de la conversación activa para nuevos mensajes. */
  const pollCurrentConversation = async () => {
    if (!hasInternalConversationAccess) return;
    if (!currentConvId || (currentConvType !== "dm" && currentConvType !== "group")) return;
    try {
      const url =
        currentConvType === "group"
          ? `/api/v1/conversaciones/groups/${encodeURIComponent(currentConvId)}`
          : `/api/v1/conversaciones/direct/${encodeURIComponent(currentConvId)}`;
      const res  = await fetch(url);
      const data = await res.json();
      if (data?.success) renderMessages(data.data || [], currentConvType);
    } catch { /* silencioso */ }
  };

  // ---------------------------------------------------------------------------
  // Event listeners
  // ---------------------------------------------------------------------------

  searchEl?.addEventListener("input", debounce(renderList, 200));
  formEl?.addEventListener("submit", sendMsg);
  indexBtn?.addEventListener("click", runIndex);
  newBtn?.addEventListener("click", openUserModal);
  newGroupBtn?.addEventListener("click", openGroupModal);
  notifyBtn?.addEventListener("click", sendModuleNotification);
  delBtn?.addEventListener("click", deleteConv);

  modalClose?.addEventListener("click", () => { if (modal) modal.style.display = "none"; });
  modal?.addEventListener("click", (e) => { if (e.target === modal) modal.style.display = "none"; });
  modalSearch?.addEventListener("input", debounce(renderModalList, 200));

  groupModalClose?.addEventListener("click", () => { if (groupModal) groupModal.style.display = "none"; });
  groupModal?.addEventListener("click", (e) => { if (e.target === groupModal) groupModal.style.display = "none"; });
  groupSearchEl?.addEventListener("input", debounce(renderGroupList, 200));
  groupCreateBtn?.addEventListener("click", createGroup);

  // Cierra modales con Escape
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (modal?.style.display === "flex")      modal.style.display = "none";
    if (groupModal?.style.display === "flex") groupModal.style.display = "none";
  });

  // ---------------------------------------------------------------------------
  // Bootstrap
  // ---------------------------------------------------------------------------

  (async () => {
    try {
      await refreshModuleAccess();
      await loadModuleUsers();
    } catch (err) {
      renderNoAccess(err?.message || "Sin acceso a Conversaciones.");
      return;
    }

    await loadAll();
    refreshIndexStatus();

    if (hasInternalConversationAccess) {
      await pollFloatingNotifications();

      // SSE reemplaza los setInterval de unread-count y loadAll
      startSSE();

      // Sondeo ligero de mensajes de la conv activa (no cubierto por SSE)
      window.setInterval(pollCurrentConversation, 8000);

      // Notificaciones flotantes cada 10 s
      window.setInterval(pollFloatingNotifications, 10000);
    }

    // Estado del índice RAG (no depende de acceso a conversaciones)
    window.setInterval(refreshIndexStatus, 30000);

    // Abre la primera conversación disponible
    if (!currentConvId) {
      const first = getUnifiedConversations()[0];
      if (first?.conv_id) await openConv(first.conv_id, first.type);
    }
  })();
})();
