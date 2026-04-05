  (function () {
    var tabs   = document.querySelectorAll(".cfg-notebook-tab");
    var panels = document.querySelectorAll(".cfg-notebook-panel");
    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () {
        tabs.forEach(function (t) { t.classList.remove("active"); t.setAttribute("aria-selected", "false"); });
        panels.forEach(function (p) { p.hidden = true; });
        tab.classList.add("active");
        tab.setAttribute("aria-selected", "true");
        panels[i].hidden = false;
      });
    });
  })();

  /* Personal de la tienda */
  (function () {
    var listView   = document.getElementById("personal-list-view");
    var formView   = document.getElementById("personal-form-view");
    var addBtn     = document.getElementById("personalAddBtn");
    var cancelBtn  = document.getElementById("personalCancelBtn");
    var cancelBtn2 = document.getElementById("personalCancelBtn2");
    var usedEl     = document.getElementById("personalUsed");
    var maxEl      = document.getElementById("personalMax");
    var listRows   = document.getElementById("personalListRows");
    var emptyMsg   = document.getElementById("personalEmpty");
    if (!listView) return;

    var vendors = [];
    var maxUsers = parseInt(localStorage.getItem("multitienda_max_internal_users") || "0", 10) || null;
    if (maxEl) maxEl.textContent = maxUsers || "∞";

    function showList() {
      listView.hidden = false;
      formView.hidden = true;
    }
    function showForm() {
      listView.hidden = true;
      formView.hidden = false;
      loadStores();
    }
    function renderList() {
      listRows.innerHTML = "";
      if (usedEl) usedEl.textContent = vendors.length;
      emptyMsg.style.display = vendors.length === 0 ? "" : "none";
      if (addBtn) addBtn.disabled = maxUsers ? vendors.length >= maxUsers : false;
      vendors.forEach(function (v, i) {
        var row = document.createElement("div");
        row.className = "personal-list-row";
        row.innerHTML =
          '<img class="personal-list-avatar" src="' + (v.photo || "/multitienda/multitienda/static/imagenes/cc.png") + '" alt="" />' +
          '<span>' + (v.name || "—") + '</span>' +
          '<span>' + (v.email || "—") + '</span>' +
          '<span>' + (v.role || "—") + '</span>' +
          '<span>' + (v.access || "—") + '</span>' +
          '<button style="background:none;border:none;color:#ef4444;cursor:pointer;font-size:0.9rem;" data-idx="' + i + '" title="Eliminar">✕</button>';
        row.querySelector("button").addEventListener("click", function () {
          vendors.splice(parseInt(this.dataset.idx, 10), 1);
          renderList();
        });
        listRows.appendChild(row);
      });
    }

    async function loadStores() {
      var sel = document.getElementById("user-store");
      if (!sel) return;
      try {
        var r = await fetch("/multitienda/api/stores", { headers: { Accept: "application/json" } });
        if (!r.ok) throw new Error();
        var payload = await r.json();
        var stores = Array.isArray(payload && payload.data) ? payload.data : [];
        sel.innerHTML = '<option value="">Selecciona una tienda</option>';
        (stores || []).forEach(function (s) {
          var o = document.createElement("option");
          o.value = s.id || "";
          o.textContent = s.name || s.store_name || ("Tienda #" + s.id);
          sel.appendChild(o);
        });
        if (stores.length === 1 && stores[0] && stores[0].id) {
          sel.value = String(stores[0].id);
        }
      } catch (e) {
        sel.innerHTML = '<option value="">No disponible</option>';
      }
    }

    /* Rol → acceso sugerido */
    document.addEventListener("change", function (e) {
      if (e.target && e.target.id === "user-role") {
        var map = { superadministrador: "total", administrador_tienda: "administrativo", vendedor: "operativo", auditor: "consulta" };
        var acc = document.getElementById("user-access-level");
        if (acc && map[e.target.value]) acc.value = map[e.target.value];
      }
    });

    /* Foto */
    document.addEventListener("change", function (e) {
      if (e.target && e.target.id === "user-photo") {
        var file = e.target.files && e.target.files[0];
        var img = document.getElementById("photoImage");
        if (file && img) img.src = URL.createObjectURL(file);
      }
    });
    document.addEventListener("click", function (e) {
      if (e.target && e.target.id === "editPhotoBtn") document.getElementById("user-photo").click();
      if (e.target && e.target.id === "deletePhotoBtn") {
        document.getElementById("user-photo").value = "";
        document.getElementById("photoImage").src = "/multitienda/multitienda/static/imagenes/cc.png";
      }
    });

    /* Guardar */
    var saveBtn = document.getElementById("personalSaveBtn");
    if (saveBtn) saveBtn.addEventListener("click", function () {
      var name  = document.getElementById("user-name").value.trim();
      var email = document.getElementById("user-email").value.trim();
      var role  = document.getElementById("user-role").value;
      var access = document.getElementById("user-access-level").value;
      if (!name) { alert("El nombre es requerido."); return; }
      vendors.push({ name: name, email: email, role: role, access: access });
      renderList();
      showList();
    });

    if (addBtn)    addBtn.addEventListener("click", showForm);
    if (cancelBtn) cancelBtn.addEventListener("click", showList);
    if (cancelBtn2) cancelBtn2.addEventListener("click", showList);

    renderList();
  })();

  (function () {
    var pairs = [
      ["lp-input-banner", "lp-img-banner"],
      ["lp-input-movil",  "lp-img-movil"],
      ["lp-input-lista",  "lp-img-lista"],
    ];
    pairs.forEach(function (pair) {
      var input = document.getElementById(pair[0]);
      var img   = document.getElementById(pair[1]);
      if (!input || !img) return;
      input.addEventListener("change", function () {
        var file = input.files && input.files[0];
        if (!file) return;
        img.src = URL.createObjectURL(file);
        img.hidden = false;
        var empty = img.parentElement.querySelector(".lp-banner-empty");
        if (empty) empty.style.display = "none";
      });
      img.parentElement.addEventListener("click", function () { input.click(); });
    });
  })();


  /* Nombre cooperativa en Landing page */
  (function () {
    var nombreInput = document.getElementById("lp-store-name");
    var coopSpan    = document.getElementById("lp-coop-name");
    if (!nombreInput || !coopSpan) return;
    function sync() {
      var val = nombreInput.value.trim();
      coopSpan.textContent = val || "tu tienda";
    }
    nombreInput.addEventListener("input", sync);
    sync();
  })();

  /* RTE — Políticas de la tienda */
  (function () {
    document.querySelectorAll(".rte-toolbar").forEach(function (toolbar) {
      var editorId = toolbar.getAttribute("data-target");
      var editor   = document.getElementById(editorId);
      if (!editor) return;
      toolbar.querySelectorAll("button[data-cmd]").forEach(function (btn) {
        btn.addEventListener("mousedown", function (e) {
          e.preventDefault();
          editor.focus();
          document.execCommand(btn.getAttribute("data-cmd"), false, null);
        });
      });
    });
  })();
