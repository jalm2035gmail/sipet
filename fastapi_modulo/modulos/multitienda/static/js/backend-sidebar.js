  (function () {
    const STORAGE_KEY = "backend_template_sidebar_settings";
    const DEFAULTS = {
      logo: "/multitienda/static/imagenes/tu-negocio.png",
      textColor: "#164723",
      iconColor: "#164723",
      topBg: "#fff5ee",
      bottomBg: "#ffe8d7",
      animation: "slide-lr"
    };

    const btn = document.getElementById("menuBtn");
    const panel = document.getElementById("menuPanel");
    const personalizarItem = document.getElementById("personalizarItem");
    const configuracionItem = document.getElementById("configuracionItem");
    const sidebarLogo = document.getElementById("sidebarLogo");

    const openEditorBtn = document.getElementById("openSidebarEditor");
    const closeEditorBtn = document.getElementById("closeSidebarEditor");
    const editor = document.getElementById("sidebarEditor");

    const logoInput = document.getElementById("sidebarLogoInput");
    const logoPreview = document.getElementById("sidebarLogoPreview");
    const textColorInput = document.getElementById("sidebarTextColor");
    const iconColorInput = document.getElementById("sidebarIconColor");
    const topBgInput = document.getElementById("sidebarTopBg");
    const bottomBgInput = document.getElementById("sidebarBottomBg");
    const animationInput = document.getElementById("sidebarAnimation");
    const resetBtn = document.getElementById("resetSidebarStyle");

    function readStoredToken() {
      const keys = ["access_token", "token", "auth_token"];
      for (let i = 0; i < keys.length; i += 1) {
        const key = keys[i];
        const localValue = window.localStorage.getItem(key);
        if (localValue) return localValue;
        const sessionValue = window.sessionStorage.getItem(key);
        if (sessionValue) return sessionValue;
      }
      return "";
    }

    function parsePayload(tokenValue) {
      const token = tokenValue.startsWith("Bearer ") ? tokenValue.slice(7) : tokenValue;
      const parts = token.split(".");
      if (parts.length < 2) return null;
      const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
      const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
      return JSON.parse(window.atob(padded));
    }

    function getUserType() {
      try {
        const token = readStoredToken();
        if (!token) return "";
        const payload = parsePayload(token);
        return payload && payload.user_type ? String(payload.user_type).toLowerCase() : "";
      } catch (error) {
        return "";
      }
    }

    function isSuperadmin() {
      return getUserType() === "superadmin";
    }

    function isAdminOrSuperadmin() {
      const userType = getUserType();
      return userType === "superadmin" || userType === "administrador";
    }

    if (personalizarItem) {
      personalizarItem.style.display = isSuperadmin() ? "" : "none";
    }
    if (configuracionItem) {
      configuracionItem.style.display = isAdminOrSuperadmin() ? "" : "none";
    }

    function setMenuState(open) {
      panel.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", String(open));
      panel.setAttribute("aria-hidden", String(!open));
    }

    function setEditorState(open) {
      editor.classList.toggle("open", open);
      editor.setAttribute("aria-hidden", String(!open));
    }

    function saveSettings(settings) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    }

    function loadSettings() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return { ...DEFAULTS };
        const parsed = JSON.parse(raw);
        return { ...DEFAULTS, ...parsed };
      } catch (error) {
        return { ...DEFAULTS };
      }
    }

    function applyAnimation(animation) {
      panel.classList.remove("anim-slide-lr", "anim-slide-rl", "anim-slide-td", "anim-slide-bu");
      panel.classList.add(`anim-${animation}`);
    }

    function applySettings(settings) {
      document.documentElement.style.setProperty("--sidebar-text-color", settings.textColor);
      document.documentElement.style.setProperty("--sidebar-icon-color", settings.iconColor);
      document.documentElement.style.setProperty("--sidebar-top-bg", settings.topBg);
      document.documentElement.style.setProperty("--sidebar-bottom-bg", settings.bottomBg);
      sidebarLogo.src = settings.logo || DEFAULTS.logo;
      if (logoPreview) logoPreview.src = settings.logo || DEFAULTS.logo;
      applyAnimation(settings.animation);

      textColorInput.value = settings.textColor;
      iconColorInput.value = settings.iconColor;
      topBgInput.value = settings.topBg;
      bottomBgInput.value = settings.bottomBg;
      animationInput.value = settings.animation;
    }

    let currentSettings = loadSettings();
    applySettings(currentSettings);

    btn.addEventListener("click", function () {
      setMenuState(!panel.classList.contains("open"));
    });

    document.addEventListener("click", function (event) {
      const isInsideMenu = panel.contains(event.target) || btn.contains(event.target);
      const isInsideEditor = editor.contains(event.target) || openEditorBtn.contains(event.target);
      if (!isInsideMenu) setMenuState(false);
      if (!isInsideEditor) setEditorState(false);
    });

    openEditorBtn.addEventListener("click", function (event) {
      event.stopPropagation();
      setEditorState(true);
      setMenuState(true);
    });

    closeEditorBtn.addEventListener("click", function () {
      setEditorState(false);
    });

    function updateSetting(key, value) {
      currentSettings = { ...currentSettings, [key]: value };
      applySettings(currentSettings);
      saveSettings(currentSettings);
    }

    textColorInput.addEventListener("input", function () {
      updateSetting("textColor", textColorInput.value);
    });

    iconColorInput.addEventListener("input", function () {
      updateSetting("iconColor", iconColorInput.value);
    });

    topBgInput.addEventListener("input", function () {
      updateSetting("topBg", topBgInput.value);
    });

    bottomBgInput.addEventListener("input", function () {
      updateSetting("bottomBg", bottomBgInput.value);
    });

    animationInput.addEventListener("change", function () {
      updateSetting("animation", animationInput.value);
      if (panel.classList.contains("open")) {
        setMenuState(false);
        setTimeout(function () { setMenuState(true); }, 40);
      }
    });

    /* click on logo image or change button opens file picker */
    const configLogoChangeBtn = document.getElementById("configLogoChangeBtn");
    if (configLogoChangeBtn) {
      configLogoChangeBtn.addEventListener("click", function () { logoInput.click(); });
    }
    if (logoPreview) {
      logoPreview.addEventListener("click", function () { logoInput.click(); });
    }

    logoInput.addEventListener("change", function () {
      const file = logoInput.files && logoInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function (event) {
        const result = event.target && event.target.result;
        if (typeof result === "string") {
          updateSetting("logo", result);
        }
      };
      reader.readAsDataURL(file);
    });

    resetBtn.addEventListener("click", function () {
      currentSettings = { ...DEFAULTS };
      applySettings(currentSettings);
      saveSettings(currentSettings);
      logoInput.value = "";
    });
  })();
