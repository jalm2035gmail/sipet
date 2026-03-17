(function () {
  var root = document.getElementById("applications-root");
  if (!root) return;

  var bootstrap = JSON.parse(root.getAttribute("data-bootstrap") || "{\"modules\":[]}");
  var modules = Array.isArray(bootstrap.modules) ? bootstrap.modules : [];
  var state = { filter: "all", term: "", selected: [], focusedKey: "" };
  var grid = document.getElementById("apps-grid");
  var toastNode = document.getElementById("apps-toast");
  var toastText = toastNode ? toastNode.querySelector("span") : null;
  var uploadInput = document.getElementById("apps-upload-input");
  var uploadModal = document.getElementById("apps-upload-modal");
  var uploadApplyButton = document.getElementById("apps-upload-apply");
  var uploadSummary = document.getElementById("apps-upload-summary");
  var uploadWarnings = document.getElementById("apps-upload-warnings");
  var uploadPreview = document.getElementById("apps-upload-preview");
  var activeUploadModule = "";
  var pendingUploadFile = null;
  var pendingUploadInspection = null;

  function toast(message, tone) {
    if (!toastNode || !toastText) return;
    toastText.textContent = message || "";
    toastNode.className = "alert shadow-lg transition-opacity duration-200 is-visible " + (tone || "alert-info");
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () {
      toastNode.className = "alert shadow-lg opacity-0 transition-opacity duration-200";
    }, 2800);
  }

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatBytes(value) {
    var size = Number(value || 0);
    var units = ["B", "KB", "MB", "GB"];
    var unit = 0;
    while (size >= 1024 && unit < units.length - 1) {
      size = size / 1024;
      unit += 1;
    }
    return (unit === 0 ? Math.round(size) : size.toFixed(1)) + " " + units[unit];
  }

  function resetUploadState() {
    pendingUploadFile = null;
    pendingUploadInspection = null;
    if (uploadInput) uploadInput.value = "";
    if (uploadApplyButton) uploadApplyButton.disabled = true;
    if (uploadSummary) uploadSummary.classList.add("hidden");
    if (uploadWarnings) {
      uploadWarnings.classList.add("hidden");
      uploadWarnings.textContent = "";
    }
    if (uploadPreview) uploadPreview.innerHTML = "";
    [["apps-upload-checksum", "-"], ["apps-upload-total-files", "0"], ["apps-upload-file-size", "0 B"], ["apps-upload-new-files", "0"], ["apps-upload-changed-files", "0"], ["apps-upload-unchanged-files", "0"], ["apps-upload-total-size", "0 B"]].forEach(function (entry) {
      var node = document.getElementById(entry[0]);
      if (node) node.textContent = entry[1];
    });
  }

  async function pollTask(taskName, taskId) {
    var attempts = 0;
    while (attempts < 120) {
      attempts += 1;
      var res = await fetch("/api/aplicaciones/tareas/" + encodeURIComponent(taskName) + "/" + encodeURIComponent(taskId));
      var data = await res.json();
      if (!res.ok) throw new Error(data.detail || "No se pudo consultar la tarea.");
      if (data.status === "success") return data.result || {};
      if (data.status === "error") throw new Error(data.error || "La tarea falló.");
      await new Promise(function (resolve) { window.setTimeout(resolve, 1000); });
    }
    throw new Error("La tarea excedió el tiempo de espera.");
  }

  function renderUploadInspection(data) {
    pendingUploadInspection = data || null;
    if (!data || !uploadSummary) return;
    uploadSummary.classList.remove("hidden");
    document.getElementById("apps-upload-checksum").textContent = String(data.checksum || "").slice(0, 12) || "-";
    document.getElementById("apps-upload-total-files").textContent = String(data.total_files || 0);
    document.getElementById("apps-upload-file-size").textContent = formatBytes(data.file_size || 0);
    document.getElementById("apps-upload-new-files").textContent = String(data.new_files || 0);
    document.getElementById("apps-upload-changed-files").textContent = String(data.changed_files || 0);
    document.getElementById("apps-upload-unchanged-files").textContent = String(data.unchanged_files || 0);
    document.getElementById("apps-upload-total-size").textContent = formatBytes(data.total_uncompressed_size || 0);
    if (uploadWarnings) {
      var warnings = Array.isArray(data.warnings) ? data.warnings : [];
      uploadWarnings.textContent = warnings.join(" ");
      uploadWarnings.classList.toggle("hidden", !warnings.length);
    }
    if (uploadPreview) {
      uploadPreview.innerHTML = (Array.isArray(data.preview_files) ? data.preview_files : []).map(function (item) {
        var status = String(item.status || "");
        var badge = status === "new" ? "badge-success" : (status === "changed" ? "badge-warning" : "badge-ghost");
        return '<li class="flex items-center justify-between gap-3 px-3 py-2"><div class="min-w-0"><div class="truncate font-medium">' + esc(item.path || "") + '</div><div class="text-xs text-base-content/60">' + formatBytes(item.size || 0) + '</div></div><span class="badge ' + badge + '">' + esc(status) + '</span></li>';
      }).join("");
    }
    if (uploadApplyButton) uploadApplyButton.disabled = !pendingUploadFile || !pendingUploadInspection;
  }

  function selectedSet() {
    return new Set(state.selected);
  }

  function protocolLabel(item) {
    if (item.protocol_ok) return "Protocolo OK";
    var missing = Array.isArray(item.protocol_missing) ? item.protocol_missing : [];
    var issues = Array.isArray(item.issues) ? item.issues : [];
    return [missing.join(", "), issues.join(", ")].filter(Boolean).join(" · ") || "Requiere atención";
  }

  function matches(item) {
    if (state.filter === "ok" && !item.protocol_ok) return false;
    if (state.filter === "missing" && item.protocol_ok) return false;
    if (!state.term) return true;
    var haystack = [
      item.label, item.key, item.route, item.description, item.module_dir,
      (item.protocol_missing || []).join(" "), (item.issues || []).join(" ")
    ].join(" ").toLowerCase();
    return haystack.indexOf(state.term) >= 0;
  }

  function visibleModules() {
    return modules.filter(matches);
  }

  function updateSummary() {
    var total = modules.length;
    var ok = modules.filter(function (item) { return item.protocol_ok; }).length;
    var missing = total - ok;
    var enabled = modules.filter(function (item) { return item.enabled; }).length;
    var uploadable = modules.filter(function (item) { return item.package_upload_enabled; }).length;
    var routed = modules.filter(function (item) { return !!item.route; }).length;
    var selected = state.selected.length;

    document.getElementById("apps-total-count").textContent = String(total);
    document.getElementById("apps-ok-count").textContent = String(ok);
    document.getElementById("apps-missing-count").textContent = String(missing);
    document.getElementById("apps-selected-count").textContent = String(selected);
    document.getElementById("apps-enabled-count").textContent = String(enabled);
    document.getElementById("apps-uploadable-count").textContent = String(uploadable);
    document.getElementById("apps-routed-count").textContent = String(routed);
    document.getElementById("apps-selection-summary").textContent = selected
      ? "Seleccionados " + String(selected) + " módulo(s) para acción por lote."
      : "Selecciona módulos para ejecutar acciones por lote o revisar auditoría.";
    document.getElementById("apps-select-all").checked = !!visibleModules().length && visibleModules().every(function (item) {
      return selectedSet().has(item.key);
    });
  }

  function renderAuditPanel() {
    var panel = document.getElementById("apps-audit-panel");
    var pill = document.getElementById("apps-audit-pill");
    var item = modules.find(function (candidate) { return candidate.key === state.focusedKey; }) || null;
    if (!item) {
      pill.textContent = "Sin selección";
      panel.innerHTML = '<div class="alert border border-dashed border-base-300 bg-base-200/60 text-sm"><i class="fa-regular fa-compass"></i><span>Selecciona un módulo para ver protocolo, ruta, dependencias y capacidad de importación.</span></div>';
      return;
    }
    pill.textContent = item.label || item.key;
    panel.innerHTML = [
      '<div class="space-y-4">',
      '<div><h3 class="text-xl font-black">' + esc(item.label) + '</h3><p class="mt-1 text-sm text-base-content/60">' + esc(item.description || "Sin descripción") + '</p></div>',
      '<div class="grid gap-2 sm:grid-cols-2">',
      '<div class="rounded-2xl bg-base-200 p-3"><div class="text-xs uppercase tracking-[0.18em] text-base-content/50">Ruta</div><div class="mt-1 font-semibold">' + esc(item.route || "Sin ruta") + '</div></div>',
      '<div class="rounded-2xl bg-base-200 p-3"><div class="text-xs uppercase tracking-[0.18em] text-base-content/50">Directorio</div><div class="mt-1 break-all font-semibold text-sm">' + esc(item.module_dir || "-") + '</div></div>',
      '</div>',
      '<div class="space-y-2">',
      '<div class="flex items-center justify-between rounded-2xl border border-base-300 px-4 py-3"><span>README</span><span class="badge ' + (item.has_readme ? 'badge-success' : 'badge-error') + '">' + (item.has_readme ? 'OK' : 'Falta') + '</span></div>',
      '<div class="flex items-center justify-between rounded-2xl border border-base-300 px-4 py-3"><span>Controladores</span><span class="badge ' + (item.has_controladores_dir ? 'badge-success' : 'badge-error') + '">' + (item.has_controladores_dir ? 'OK' : 'Falta') + '</span></div>',
      '<div class="flex items-center justify-between rounded-2xl border border-base-300 px-4 py-3"><span>Tests</span><span class="badge ' + (item.has_tests_dir ? 'badge-success' : 'badge-error') + '">' + (item.has_tests_dir ? 'OK' : 'Falta') + '</span></div>',
      '<div class="flex items-center justify-between rounded-2xl border border-base-300 px-4 py-3"><span>Routers importables</span><span class="badge ' + (item.routers_importable ? 'badge-success' : 'badge-error') + '">' + (item.routers_importable ? 'Sí' : 'No') + '</span></div>',
      '</div>',
      '<div><div class="mb-2 text-xs uppercase tracking-[0.18em] text-base-content/50">Hallazgos</div><div class="flex flex-wrap gap-2">' +
        (item.protocol_missing || []).concat(item.issues || []).map(function (tag) { return '<span class="badge badge-outline">' + esc(tag) + '</span>'; }).join("") +
        (((item.protocol_missing || []).length || (item.issues || []).length) ? '' : '<span class="badge badge-success">Sin hallazgos</span>') +
      '</div></div>',
      '</div>'
    ].join("");
  }

  function render() {
    updateSummary();
    renderAuditPanel();
    var visible = visibleModules();
    var selected = selectedSet();
    if (!visible.length) {
      grid.innerHTML = '<div class="alert md:col-span-2 2xl:col-span-3"><i class="fa-regular fa-folder-open"></i><span>No hay aplicaciones que coincidan.</span></div>';
      return;
    }
    grid.innerHTML = visible.map(function (item) {
      var initials = esc(String(item.label || "A").split(/\s+/).filter(Boolean).slice(0, 2).map(function (part) {
        return part.charAt(0);
      }).join("").toUpperCase());
      var iconHtml = item.image_url
        ? '<img src="' + esc(item.image_url) + '" alt="' + esc(item.label) + '">'
        : (item.icon ? '<i class="' + esc(item.icon) + ' text-3xl"></i>' : '<span class="text-2xl font-black">' + initials + '</span>');
      var selectedClass = selected.has(item.key) ? ' is-selected' : '';
      return '' +
        '<article class="gov-app-card card border border-base-300 bg-base-100 shadow-sm' + selectedClass + '" data-focus-module="' + esc(item.key) + '">' +
          '<div class="card-body gap-4 p-5">' +
            '<div class="flex items-start justify-between gap-3">' +
              '<label class="label cursor-pointer gap-3 p-0">' +
                '<input type="checkbox" class="checkbox checkbox-sm" data-select-module="' + esc(item.key) + '"' + (selected.has(item.key) ? ' checked' : '') + '>' +
                '<span class="label-text text-xs uppercase tracking-[0.18em] text-base-content/50">Lote</span>' +
              '</label>' +
              '<div class="gov-app-icon flex h-16 w-16 items-center justify-center rounded-3xl border border-base-300 text-primary">' + iconHtml + '</div>' +
            '</div>' +
            '<div class="space-y-2">' +
              '<div class="flex items-start justify-between gap-3">' +
                '<div><h3 class="text-xl font-black leading-tight">' + esc(item.label) + '</h3><div class="mt-1 text-xs font-semibold uppercase tracking-[0.18em] text-base-content/50">' + esc(item.key) + '</div></div>' +
                '<span class="badge ' + (item.enabled ? 'badge-success' : 'badge-ghost') + '">' + (item.enabled ? 'Activo' : 'Inactivo') + '</span>' +
              '</div>' +
              '<p class="min-h-[3.5rem] text-sm leading-6 text-base-content/70">' + esc(item.description || "Sin descripción") + '</p>' +
            '</div>' +
            '<div class="flex flex-wrap gap-2">' +
              '<span class="badge ' + (item.protocol_ok ? 'badge-success' : 'badge-warning') + '">' + esc(protocolLabel(item)) + '</span>' +
              '<span class="badge badge-outline">' + esc(String(item.router_count || 0)) + ' routers</span>' +
              '<span class="badge ' + (item.package_upload_enabled ? 'badge-info' : 'badge-ghost') + '">' + (item.package_upload_enabled ? 'Importable' : 'Sin ZIP') + '</span>' +
            '</div>' +
            '<div class="mt-1 flex items-center justify-between gap-3 rounded-2xl bg-base-200 px-4 py-3">' +
              '<span class="text-sm font-semibold">Estado operativo</span>' +
              '<input type="checkbox" class="toggle toggle-primary" data-toggle-module="' + esc(item.key) + '"' + (item.enabled ? ' checked' : '') + '>' +
            '</div>' +
            '<div class="card-actions mt-1 justify-between">' +
              '<button class="btn btn-outline btn-sm gap-2" type="button" data-open-upload="' + esc(item.key) + '"' + (item.package_upload_enabled ? '' : ' disabled') + '><i class="fa-solid fa-file-import"></i>Importar</button>' +
              (item.route ? '<a class="btn btn-primary btn-sm gap-2" href="' + esc(item.route) + '"><i class="fa-solid fa-arrow-up-right-from-square"></i>Abrir</a>' : '<button class="btn btn-disabled btn-sm">Sin ruta</button>') +
            '</div>' +
          '</div>' +
        '</article>';
    }).join("");
  }

  async function refreshModules() {
    var res = await fetch("/api/aplicaciones/modulos");
    modules = await res.json();
    state.selected = state.selected.filter(function (key) {
      return modules.some(function (item) { return item.key === key; });
    });
    if (!modules.some(function (item) { return item.key === state.focusedKey; })) {
      state.focusedKey = state.selected[0] || "";
    }
    render();
  }

  async function updateModule(key, enabled, input) {
    try {
      var res = await fetch("/api/aplicaciones/modulos/" + encodeURIComponent(key), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !!enabled })
      });
      var data = await res.json();
      if (!res.ok) throw new Error(data.detail || "No se pudo actualizar.");
      modules = modules.map(function (item) {
        return item.key === key ? Object.assign({}, item, data) : item;
      });
      render();
      toast("Aplicación actualizada.", "alert-success");
    } catch (error) {
      if (input) input.checked = !enabled;
      toast(error.message || "No se pudo actualizar.", "alert-error");
    } finally {
      if (input) input.disabled = false;
    }
  }

  async function bulkUpdate(enabled) {
    if (!state.selected.length) {
      toast("Selecciona al menos un módulo.", "alert-warning");
      return;
    }
    for (var index = 0; index < state.selected.length; index += 1) {
      var key = state.selected[index];
      await updateModule(key, enabled);
    }
    toast(enabled ? "Lote activado." : "Lote desactivado.", "alert-success");
  }

  async function syncProtocol() {
    try {
      var syncPassword = window.prompt("Confirma tu contraseña para sincronizar el protocolo:");
      if (!syncPassword) {
        toast("Confirmación cancelada.", "alert-warning");
        return;
      }
      var syncChallenge = await fetch("/api/aplicaciones/security/challenge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "protocol_sync", password: syncPassword, module_key: "" })
      });
      var syncChallengeData = await syncChallenge.json();
      if (!syncChallenge.ok) throw new Error(syncChallengeData.detail || "No se pudo confirmar la operación.");
      var res = await fetch("/api/aplicaciones/protocolo/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "repair_missing_only", challenge_token: syncChallengeData.token || "" })
      });
      var data = await res.json();
      if (!res.ok) throw new Error(data.detail || "No se pudo sincronizar.");
      if (data.status === "queued" && data.task_id) {
        toast("Sincronización encolada. Esperando resultado...", "alert-info");
        await pollTask(String(data.task_name || "protocol_sync"), String(data.task_id || ""));
      }
      await refreshModules();
      toast("Protocolo sincronizado.", "alert-success");
    } catch (error) {
      toast(error.message || "No se pudo sincronizar.", "alert-error");
    }
  }

  function openUploadModal(moduleKey) {
    activeUploadModule = moduleKey;
    resetUploadState();
    var item = modules.find(function (candidate) { return candidate.key === moduleKey; });
    document.getElementById("apps-upload-label").textContent = item
      ? "Selecciona un ZIP para actualizar " + item.label + "."
      : "Selecciona un ZIP para actualizar el módulo.";
    if (uploadModal && typeof uploadModal.showModal === "function") uploadModal.showModal();
  }

  async function inspectModulePackage(key, file) {
    try {
      var formData = new FormData();
      formData.append("package", file);
      formData.append("dry_run", "true");
      var res = await fetch("/api/aplicaciones/modulos/" + encodeURIComponent(key) + "/upload", {
        method: "POST",
        body: formData
      });
      var data = await res.json();
      if (!res.ok) throw new Error(data.detail || "No se pudo inspeccionar el módulo.");
      pendingUploadFile = file;
      renderUploadInspection(data);
      toast("ZIP inspeccionado. Revisa el resumen antes de aplicar.", "alert-success");
    } catch (error) {
      resetUploadState();
      toast(error.message || "No se pudo inspeccionar el módulo.", "alert-error");
    }
  }

  async function applyModulePackage(key) {
    if (!pendingUploadFile || !pendingUploadInspection) {
      toast("Primero inspecciona un ZIP válido.", "alert-warning");
      return;
    }
    try {
      var uploadPassword = window.prompt("Confirma tu contraseña para aplicar el ZIP inspeccionado:");
      if (!uploadPassword) {
        toast("Confirmación cancelada.", "alert-warning");
        return;
      }
      var challengeRes = await fetch("/api/aplicaciones/security/challenge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "package_upload", password: uploadPassword, module_key: key })
      });
      var challengeData = await challengeRes.json();
      if (!challengeRes.ok) throw new Error(challengeData.detail || "No se pudo confirmar la operación.");
      var formData = new FormData();
      formData.append("package", pendingUploadFile);
      formData.append("dry_run", "false");
      formData.append("expected_checksum", String(pendingUploadInspection.checksum || ""));
      formData.append("challenge_token", challengeData.token || "");
      var res = await fetch("/api/aplicaciones/modulos/" + encodeURIComponent(key) + "/upload", {
        method: "POST",
        body: formData
      });
      var data = await res.json();
      if (!res.ok) throw new Error(data.detail || "No se pudo importar el módulo.");
      if (data.status === "queued" && data.task_id) {
        toast("Importación encolada. Esperando resultado...", "alert-info");
        data = await pollTask(String(data.task_name || "package_apply"), String(data.task_id || ""));
      }
      if (uploadModal) uploadModal.close();
      await refreshModules();
      toast("Paquete aplicado en " + String(data.updated_files || 0) + " archivo(s).", "alert-success");
    } catch (error) {
      toast(error.message || "No se pudo importar el módulo.", "alert-error");
    } finally {
      activeUploadModule = "";
      resetUploadState();
    }
  }

  document.querySelectorAll("[data-filter]").forEach(function (button) {
    button.addEventListener("click", function () {
      state.filter = button.getAttribute("data-filter") || "all";
      document.querySelectorAll("[data-filter]").forEach(function (candidate) {
        candidate.classList.toggle("tab-active", candidate === button);
      });
      render();
    });
  });

  document.getElementById("apps-search-input").addEventListener("input", function (event) {
    state.term = String(event.target.value || "").trim().toLowerCase();
    render();
  });

  document.getElementById("apps-select-all").addEventListener("change", function (event) {
    state.selected = event.target.checked ? visibleModules().map(function (item) { return item.key; }) : [];
    if (!state.focusedKey && state.selected.length) state.focusedKey = state.selected[0];
    render();
  });

  document.getElementById("apps-sync-protocol").addEventListener("click", syncProtocol);
  document.getElementById("apps-bulk-enable").addEventListener("click", function () { bulkUpdate(true); });
  document.getElementById("apps-bulk-disable").addEventListener("click", function () { bulkUpdate(false); });

  grid.addEventListener("change", function (event) {
    var selectBox = event.target.closest("[data-select-module]");
    if (selectBox) {
      var moduleKey = selectBox.getAttribute("data-select-module") || "";
      var selected = selectedSet();
      if (selectBox.checked) selected.add(moduleKey);
      else selected.delete(moduleKey);
      state.selected = Array.from(selected);
      if (moduleKey) state.focusedKey = moduleKey;
      render();
      return;
    }
    var input = event.target.closest("[data-toggle-module]");
    if (!input) return;
    input.disabled = true;
    updateModule(input.getAttribute("data-toggle-module") || "", !!input.checked, input);
  });

  grid.addEventListener("click", function (event) {
    var uploadButton = event.target.closest("[data-open-upload]");
    if (uploadButton && !uploadButton.disabled) {
      openUploadModal(uploadButton.getAttribute("data-open-upload") || "");
      return;
    }
    var article = event.target.closest("[data-focus-module]");
    if (article) {
      state.focusedKey = article.getAttribute("data-focus-module") || "";
      renderAuditPanel();
    }
  });

  uploadInput.addEventListener("change", function () {
    var file = uploadInput.files && uploadInput.files[0];
    if (!file || !activeUploadModule) return;
    if (!/\.zip$/i.test(file.name || "")) {
      toast("Selecciona un archivo ZIP.", "alert-warning");
      resetUploadState();
      return;
    }
    inspectModulePackage(activeUploadModule, file);
  });

  if (uploadApplyButton) {
    uploadApplyButton.addEventListener("click", function () {
      applyModulePackage(activeUploadModule);
    });
  }

  if (uploadModal) {
    uploadModal.addEventListener("close", function () {
      activeUploadModule = "";
      resetUploadState();
    });
  }

  render();
}());
