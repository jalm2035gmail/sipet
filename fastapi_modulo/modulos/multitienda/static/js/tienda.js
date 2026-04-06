(function () {
  var DEFAULT_LOGO = "/static/imagenes/logo_vale.png";
  var DEFAULT_BANNER = "/multitienda/static/imagenes/banner.png";

  function applyHeroBanner(url) {
    var img = document.getElementById("sl-hero-banner-img");
    if (img) img.src = url && url.trim() ? url.trim() : DEFAULT_BANNER;
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function setHtml(id, value) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = value || "";
  }

  function setSrc(id, value) {
    var el = document.getElementById(id);
    if (el && value) el.src = value;
  }

  function setHidden(id, hidden) {
    var el = document.getElementById(id);
    if (el) el.hidden = !!hidden;
  }

  function setLink(id, href, label) {
    var el = document.getElementById(id);
    if (!el) return;
    el.href = href || "#";
    el.textContent = label || "";
  }

  function joinText(values) {
    return values.filter(function (value) { return normalizeText(value); }).join(", ");
  }

  function buildAddress(info) {
    return joinText([
      joinText([info.street, info.between_streets ? "Entre " + info.between_streets : ""]),
      info.neighborhood,
      info.locality,
      info.municipality,
      info.state,
      info.postal_code,
      info.country,
    ]);
  }

  function buildMapUrl(info, address) {
    var lat = normalizeText(info.latitude);
    var lng = normalizeText(info.longitude);
    if (lat && lng) return "https://www.google.com/maps?q=" + encodeURIComponent(lat + "," + lng);
    if (address) return "https://www.google.com/maps?q=" + encodeURIComponent(address);
    return "";
  }

  function textToHtml(value) {
    return escapeHtml(normalizeText(value)).replace(/\n/g, "<br>");
  }

  function hydrateStoreSections(info) {
    var address = buildAddress(info);
    var mapUrl = buildMapUrl(info, address);
    var showAboutCopy = !info.hide_about && !!(normalizeText(info.slogan) || normalizeText(info.mission) || normalizeText(info.vision));
    var showBenefits = !info.hide_partner_benefits && !!normalizeText(info.partner_benefits);
    var showEmail = !info.hide_email && !!normalizeText(info.email);
    var showPhone = !info.hide_phone && !!normalizeText(info.phone);
    var showWebsite = !info.hide_website && !!normalizeText(info.website);
    var showAddress = !info.hide_address && !!address;
    var showMap = !info.hide_map && !!mapUrl;
    var showContact = showEmail || showPhone || showWebsite || showAddress;
    var showAboutPanel = showAboutCopy || showContact || showMap;
    var showPolicies = !info.hide_policies && !!(
      normalizeText(info.consumer_rights) ||
      normalizeText(info.data_privacy) ||
      normalizeText(info.additional_conditions)
    );
    var showRights = !info.hide_policies && !!normalizeText(info.consumer_rights);
    var showPrivacy = !info.hide_policies && !!normalizeText(info.data_privacy);

    setHidden("sl-about-card", !showAboutCopy);
    setHidden("sl-benefits-card", !showBenefits);
    setHidden("sl-contact-card", !showContact);
    setHidden("sl-map-card", !showMap);
    setHidden("sl-policy-rights-card", !normalizeText(info.consumer_rights) || !!info.hide_policies);
    setHidden("sl-policy-privacy-card", !normalizeText(info.data_privacy) || !!info.hide_policies);
    setHidden("sl-policy-conditions-card", !normalizeText(info.additional_conditions) || !!info.hide_policies);

    setText("sl-store-slogan", normalizeText(info.slogan));
    setHidden("sl-store-slogan", !normalizeText(info.slogan));
    setText("sl-store-mission", normalizeText(info.mission));
    setHidden("sl-mission-block", !normalizeText(info.mission));
    setText("sl-store-vision", normalizeText(info.vision));
    setHidden("sl-vision-block", !normalizeText(info.vision));

    setText("sl-store-benefits", normalizeText(info.partner_benefits));

    setHidden("sl-contact-email-wrap", !showEmail);
    setText("sl-contact-email", normalizeText(info.email));
    setHidden("sl-contact-phone-wrap", !showPhone);
    setText("sl-contact-phone", normalizeText(info.phone));
    setHidden("sl-contact-website-wrap", !showWebsite);
    setLink("sl-contact-website", normalizeText(info.website), normalizeText(info.website));
    setHidden("sl-contact-address-wrap", !showAddress);
    setText("sl-contact-address", address);

    setText("sl-map-copy", address || "Ubicación disponible para esta tienda.");
    setLink("sl-map-link", mapUrl, "Abrir mapa");
    setHtml("sl-store-benefits-panel", textToHtml(info.partner_benefits));
    setHtml("sl-policy-rights", textToHtml(info.consumer_rights));
    setHtml("sl-policy-privacy", textToHtml(info.data_privacy));
    setHtml("sl-policy-conditions", textToHtml(info.additional_conditions));

    return {
      showBenefits: showBenefits,
      showAbout: showAboutPanel,
      showPolicies: showPolicies,
      showRights: showRights,
      showPrivacy: showPrivacy,
      showContact: showContact,
      showMap: showMap,
      mapUrl: mapUrl,
    };
  }

  var _RESERVED_SLUGS = ["tiendas","destacados","multitienda","configuracion","api","static","templates","icon",""];

  function _parsePath() {
    var parts = window.location.pathname.replace(/\/+$/, "").split("/").filter(Boolean);
    // /{store_slug}/{product_slug}
    if (parts.length >= 2
        && _RESERVED_SLUGS.indexOf(parts[parts.length - 2].toLowerCase()) === -1
        && _RESERVED_SLUGS.indexOf(parts[parts.length - 1].toLowerCase()) === -1) {
      return { storeSlug: parts[parts.length - 2], productSlug: parts[parts.length - 1] };
    }
    // /{store_slug}
    if (parts.length >= 1 && _RESERVED_SLUGS.indexOf(parts[parts.length - 1].toLowerCase()) === -1) {
      return { storeSlug: parts[parts.length - 1], productSlug: "" };
    }
    return { storeSlug: "", productSlug: "" };
  }

  function detectStoreSlugFromPath() {
    return _parsePath().storeSlug;
  }

  function openStoreDrawer(panelKey, title) {
    var drawer = document.getElementById("sl-store-drawer");
    var overlay = document.getElementById("sl-store-drawer-overlay");
    var titleEl = document.getElementById("sl-store-drawer-title");
    if (!drawer || !overlay) return;
    if (titleEl) titleEl.textContent = title || "Información";
    document.querySelectorAll("[data-store-drawer-panel]").forEach(function (panel) {
      var isActive = panel.getAttribute("data-store-drawer-panel") === panelKey;
      panel.hidden = !isActive;
      panel.classList.toggle("is-active", isActive);
    });
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    overlay.hidden = false;
    document.body.classList.add("sl-store-drawer-open");
  }

  function closeStoreDrawer() {
    var drawer = document.getElementById("sl-store-drawer");
    var overlay = document.getElementById("sl-store-drawer-overlay");
    if (drawer) {
      drawer.classList.remove("is-open");
      drawer.setAttribute("aria-hidden", "true");
    }
    if (overlay) overlay.hidden = true;
    document.body.classList.remove("sl-store-drawer-open");
  }

  function renderStoreActions(items) {
    var root = document.getElementById("sl-store-actions");
    var grid = document.getElementById("sl-store-actions-grid");
    if (!root || !grid) return;
    if (!items.length) {
      root.hidden = true;
      grid.innerHTML = "";
      return;
    }
    grid.innerHTML = items.map(function (item) {
      return (
        '<button class="sl-store-action-btn" type="button" data-store-action="' + escapeHtml(item.key) + '">' +
          '<span class="sl-store-action-btn__icon" aria-hidden="true">' + escapeHtml(item.icon || "•") + '</span>' +
          '<strong>' + escapeHtml(item.label) + '</strong>' +
          '<span>' + escapeHtml(item.description) + '</span>' +
        '</button>'
      );
    }).join("");
    root.hidden = false;
    grid.querySelectorAll("[data-store-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        var key = button.getAttribute("data-store-action");
        var selected = items.find(function (item) { return item.key === key; });
        if (selected && selected.href) {
          window.open(selected.href, "_blank", "noopener,noreferrer");
          return;
        }
        openStoreDrawer(key, selected ? selected.label : "Información");
      });
    });
  }

  function hydrateStoreInfo() {
    var pathInfo = _parsePath();
    var slug = pathInfo.storeSlug;
    if (!slug) return;
    // Mostrar el hero-banner sólo en páginas de tienda individual
    var hero = document.getElementById("heroMarketplace");
    if (hero) hero.removeAttribute("hidden");
    fetch("/multitienda/api/store-info?store_slug=" + encodeURIComponent(slug), { headers: { Accept: "application/json" } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (payload) {
        var info = payload && payload.success && payload.data ? payload.data : null;
        if (!info) return;
        currentStoreInfo = info;
        if (info.landing_banner) applyHeroBanner(info.landing_banner);
        setSrc("sl-nav-logo", info.logo || DEFAULT_LOGO);
        setSrc("sl-sticky-logo", info.logo || DEFAULT_LOGO);
        setText("sl-nav-brand-name", info.store_name || "");
        var nameEl = document.getElementById("sl-store-name");
        var logoEl = document.getElementById("sl-store-logo");
        var emailEl = document.getElementById("sl-store-email");
        var phoneEl = document.getElementById("sl-store-phone");
        var copyEl = document.getElementById("sl-store-copy");
        var titleEl = document.getElementById("sl-page-title");
        if (nameEl && info.store_name) nameEl.textContent = info.store_name;
        if (logoEl && info.logo) logoEl.src = info.logo;
        if (emailEl && info.email) emailEl.textContent = info.email;
        if (phoneEl && info.phone) phoneEl.textContent = info.phone;
        if (copyEl && info.slogan) copyEl.textContent = info.slogan;
        if (titleEl && info.store_name && !selectedCategory) titleEl.textContent = info.store_name;
        var visibility = hydrateStoreSections(info);
        if (!pathInfo.productSlug) {
          document.body.classList.add("sl-mode-store");
          setSrc("sl-store-showcase-logo", info.logo || DEFAULT_LOGO);
          setText("sl-store-showcase-title", info.store_name || "Tienda");
          setText("sl-store-showcase-copy", normalizeText(info.slogan));
          setHidden("sl-store-showcase-copy", !normalizeText(info.slogan));
          setHidden("sl-store-showcase", false);

          var meta = [];
          if (!info.hide_phone && normalizeText(info.phone)) meta.push("Tel. " + normalizeText(info.phone));
          if (!info.hide_website && normalizeText(info.website)) meta.push(normalizeText(info.website));
          if (!info.hide_address && buildAddress(info)) meta.push(buildAddress(info));
          setHtml("sl-store-showcase-meta", meta.map(function (item) {
            return '<span class="sl-store-showcase__meta-pill">' + escapeHtml(item) + "</span>";
          }).join(""));

          var cta = document.getElementById("sl-store-showcase-cta");
          if (cta) cta.href = "#sl-store-panel-products";

          renderStoreActions(
            [
              visibility.showAbout ? { key: "nosotros", label: "Nosotros", icon: "◫", description: "Slogan, visión y misión de la tienda." } : null,
              visibility.showRights ? { key: "rights", label: "Derechos del consumidor", icon: "§", description: "Información pública para clientes y compradores." } : null,
              visibility.showPrivacy ? { key: "privacy", label: "Privacidad de los datos", icon: "◌", description: "Tratamiento y resguardo de información personal." } : null,
              visibility.showContact ? { key: "contact", label: "Datos de contacto", icon: "@", description: "Correo, teléfono, sitio web y dirección publicada." } : null,
              visibility.showMap ? { key: "location", label: "Ubicación", icon: "⌖", description: "Abrir mapa de la tienda en una nueva pestaña.", href: visibility.mapUrl } : null
            ].filter(Boolean)
          );
        }
        if (!pathInfo.productSlug && allProducts.length) renderAll();
      })
      .catch(function () {});
  }
  var allProducts = [];
  var allCategories = [];
  var allStores = [];
  var currentStoreInfo = null;
  var featuredCategories = [];
  var selectedCategory = "";
  var selectedStore = "";
  var selectedOffer = "all";
  var searchQ = "";
  var viewMode = "grid";
  var sortMode = "featured";

  var storeDrawerClose = document.getElementById("sl-store-drawer-close");
  if (storeDrawerClose) storeDrawerClose.addEventListener("click", closeStoreDrawer);
  var storeDrawerOverlay = document.getElementById("sl-store-drawer-overlay");
  if (storeDrawerOverlay) storeDrawerOverlay.addEventListener("click", closeStoreDrawer);
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeStoreDrawer();
  });

  // ── Wishlist ──────────────────────────────────────────────────────────────
  var _WL_KEY = "mt_wishlist";        // localStorage key  → Set of product_id strings
  var _SESSION_COOKIE = "mt_session";

  function _getOrCreateSessionKey() {
    var match = document.cookie.match(/(?:^|;\s*)mt_session=([^;]+)/);
    if (match) return match[1];
    var key = ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, function (c) {
      return (c ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))).toString(16);
    });
    var expires = new Date();
    expires.setFullYear(expires.getFullYear() + 1);
    document.cookie = _SESSION_COOKIE + "=" + key + "; path=/; expires=" + expires.toUTCString() + "; SameSite=Lax";
    return key;
  }

  var _wishSet = new Set(safeParse(localStorage.getItem(_WL_KEY), []));

  function _saveWishSet() {
    localStorage.setItem(_WL_KEY, JSON.stringify(Array.from(_wishSet)));
  }

  function isWishlisted(productId) {
    return _wishSet.has(String(productId));
  }

  function _wishBtnInContainer(container, productId) {
    var btn = container.querySelector('[data-wish-id="' + productId + '"]');
    return btn;
  }

  async function toggleWishlist(productId, productData, buttonEl) {
    var id = String(productId);
    if (isWishlisted(id)) {
      _wishSet.delete(id);
      _saveWishSet();
      if (buttonEl) { buttonEl.classList.remove("active"); buttonEl.setAttribute("aria-label", "Guardar en favoritos"); buttonEl.textContent = "♡"; }
      try { await fetch("/api/wishlist/" + encodeURIComponent(id), { method: "DELETE", headers: { "X-Session-Key": _getOrCreateSessionKey() } }); } catch (e) {}
    } else {
      _wishSet.add(id);
      _saveWishSet();
      if (buttonEl) { buttonEl.classList.add("active"); buttonEl.setAttribute("aria-label", "Quitar de favoritos"); buttonEl.textContent = "♥"; }
      try {
        await fetch("/api/wishlist/", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Session-Key": _getOrCreateSessionKey() },
          body: JSON.stringify({
            product_id: id,
            product_name: productData.nombre || "",
            product_price: String(productData.precio || ""),
            product_image: (productData.imagen && !String(productData.imagen).startsWith("data:")) ? productData.imagen : "",
            store_name: deriveStoreName(productData),
          }),
        });
      } catch (e) {}
    }
  }

  function makeWishButton(product) {
    var id = String(product.id || product.nombre || "");
    var wishlisted = isWishlisted(id);
    return '<button class="sl-card-wish' + (wishlisted ? " active" : "") + '" ' +
      'type="button" data-wish-id="' + escapeHtml(id) + '" ' +
      'aria-label="' + (wishlisted ? "Quitar de favoritos" : "Guardar en favoritos") + '">' +
      (wishlisted ? "♥" : "♡") +
      "</button>";
  }

  function makeCartLink() {
    if (currentStoreInfo && currentStoreInfo.hide_cart_buttons) return "";
    return '<a class="sl-card-cart-link" href="/carrito" aria-label="Ir al carrito">🛒</a>';
  }
  // ─────────────────────────────────────────────────────────────────────────

  function safeParse(raw, fallback) {
    try { return JSON.parse(raw || ""); } catch (error) { return fallback; }
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function normalizeText(value) {
    return String(value || "").trim();
  }

  function normalizeCategoryName(category) {
    if (!category) return "";
    if (typeof category === "string") return normalizeText(category);
    return normalizeText(category.nombre || category.name || category.label || "");
  }

  function deriveStoreName(product) {
    var candidates = [
      product.tienda,
      product.store,
      product.storeName,
      product.vendor,
      product.vendor_name,
      product.marca,
    ];
    for (var i = 0; i < candidates.length; i += 1) {
      var value = normalizeText(candidates[i]);
      if (value) return value;
    }
    return normalizeText(localStorage.getItem("multitienda_store_name")) || "Calidad y precio a tu alcance";
  }

  function isProductPublished(product) {
    return !!(product && (product.publicado || product.ecomPublicado));
  }

  function getProductCategory(product) {
    var direct = normalizeCategoryName(product.categoria);
    if (direct) return direct;
    var ecommerce = normalizeText(product.ecomCategorias);
    if (ecommerce) return ecommerce.split(",")[0].trim();
    return "";
  }

  function hasOffer(product) {
    return !!(product.nuevo || /oferta|promo|descuento/i.test(normalizeText(product.etiquetas)));
  }

  function hasImage(product) {
    return !!(product.imagen && !String(product.imagen).includes("undefined"));
  }

  function getDisplayProducts() {
    var filtered = allProducts.filter(function (product) {
      if (!isProductPublished(product)) return false;
      var productCategory = getProductCategory(product);
      var productStore = deriveStoreName(product);
      var haystack = [
        product.nombre,
        product.descCorta,
        product.descLarga,
        productCategory,
        productStore,
        product.etiquetas,
      ].join(" ").toLowerCase();

      if (selectedCategory && productCategory !== selectedCategory) return false;
      if (selectedStore && productStore !== selectedStore) return false;
      if (selectedOffer === "offers" && !hasOffer(product)) return false;
      if (selectedOffer === "new" && !product.nuevo) return false;
      if (selectedOffer === "ready" && !hasImage(product)) return false;
      if (searchQ && haystack.indexOf(searchQ.toLowerCase()) === -1) return false;
      return true;
    });

    filtered.sort(function (a, b) {
      if (sortMode === "price-asc") return getNumericPrice(a) - getNumericPrice(b);
      if (sortMode === "price-desc") return getNumericPrice(b) - getNumericPrice(a);
      if (sortMode === "name-asc") return normalizeText(a.nombre).localeCompare(normalizeText(b.nombre), "es");
      var scoreA = (a.nuevo ? 2 : 0) + (hasImage(a) ? 1 : 0);
      var scoreB = (b.nuevo ? 2 : 0) + (hasImage(b) ? 1 : 0);
      return scoreB - scoreA;
    });

    return filtered;
  }

  function getNumericPrice(product) {
    var price = parseFloat(product && product.precio);
    return isNaN(price) ? 0 : price;
  }

  function formatPrice(value) {
    if (value === "" || value === null || value === undefined) return "Consultar";
    var numeric = parseFloat(value);
    if (isNaN(numeric)) return "Consultar";
    return "$" + numeric.toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function buildDerivedCategories() {
    var map = {};
    allCategories.forEach(function (category) {
      var name = normalizeCategoryName(category);
      if (!name || map[name]) return;
      map[name] = { name: name, count: 0 };
    });
    allProducts.forEach(function (product) {
      if (!isProductPublished(product)) return;
      var name = getProductCategory(product);
      if (!name) return;
      if (!map[name]) map[name] = { name: name, count: 0 };
      map[name].count += 1;
    });
    return Object.keys(map).map(function (key) { return map[key]; }).sort(function (a, b) {
      return b.count - a.count || a.name.localeCompare(b.name, "es");
    });
  }

  function buildDerivedStores() {
    var storeMap = {};
    allProducts.forEach(function (product) {
      if (!isProductPublished(product)) return;
      var name = deriveStoreName(product);
      if (!name) return;
      if (!storeMap[name]) {
        storeMap[name] = {
          name: name,
          count: 0,
          featured: false,
          description: "",
          logo: DEFAULT_LOGO,
          phone: "",
          email: "",
        };
      }
      storeMap[name].count += 1;
    });

    allStores.forEach(function (store) {
      var name = normalizeText(store.store_name);
      if (!name) return;
      if (!storeMap[name]) {
        storeMap[name] = {
          name: name,
          count: 0,
          featured: !!store.is_featured,
          description: normalizeText(store.description),
          logo: store.logo || DEFAULT_LOGO,
          phone: normalizeText(store.phone),
          email: "",
        };
      } else {
        storeMap[name].featured = storeMap[name].featured || !!store.is_featured;
        storeMap[name].description = storeMap[name].description || normalizeText(store.description);
        storeMap[name].logo = storeMap[name].logo === DEFAULT_LOGO && store.logo ? store.logo : storeMap[name].logo;
        storeMap[name].phone = storeMap[name].phone || normalizeText(store.phone);
      }
    });

    return Object.keys(storeMap).map(function (key) { return storeMap[key]; }).sort(function (a, b) {
      return (b.featured ? 1 : 0) - (a.featured ? 1 : 0) || b.count - a.count || a.name.localeCompare(b.name, "es");
    });
  }

  function updateHero() {
    var sidebarSettings = safeParse(localStorage.getItem("backend_template_sidebar_settings"), {});
    var storeName = normalizeText(localStorage.getItem("multitienda_store_name")) || "Calidad y precio a tu alcance";
    var storeEmail = normalizeText(localStorage.getItem("multitienda_store_email")) || "contacto@tunegocio.com";
    var storePhone = normalizeText(localStorage.getItem("multitienda_store_phone")) || "Sin telefono";
    var storeLogo = normalizeText(sidebarSettings.logo) || DEFAULT_LOGO;
    var storeDesc = "";
    var heroTitle = selectedCategory ? "Coleccion de " + selectedCategory : "Las mejores tiendas";
    var heroCopy = selectedCategory
      ? "Filtra productos publicados dentro de " + selectedCategory + " y descubre articulos listos para destacar en el marketplace."
      : "Todo al alcance de un CLIC";

    setText("sl-page-title", heroTitle);
    setText("sl-page-copy", heroCopy);
    setText("sl-store-name", storeName);
    setText("sl-store-email", storeEmail);
    setText("sl-store-phone", storePhone);
    setSrc("sl-store-logo", storeLogo);
    setText("sl-store-copy", storeDesc);
    // Actualizar nombre en la barra de navegación
    var navBrandEl = document.getElementById("sl-nav-brand-name");
    if (navBrandEl && storeName && storeName !== "Calidad y precio a tu alcance") {
      navBrandEl.textContent = storeName;
    }
  }

  function renderFeaturedCategories() {
    var container = document.getElementById("sl-featured-categories");
    container.innerHTML = "";
    featuredCategories = buildDerivedCategories().slice(0, 5).map(function (category) { return category.name; });

    var allButton = document.createElement("button");
    allButton.type = "button";
    allButton.className = "sl-chip" + (selectedCategory === "" ? " active" : "");
    allButton.textContent = "Todo";
    allButton.addEventListener("click", function () {
      selectedCategory = "";
      renderAll();
    });
    container.appendChild(allButton);

    featuredCategories.forEach(function (name) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "sl-chip" + (selectedCategory === name ? " active" : "");
      button.textContent = name;
      button.addEventListener("click", function () {
        selectedCategory = name;
        renderAll();
      });
      container.appendChild(button);
    });
  }

  function renderStoreList() {
    var list = document.getElementById("sl-store-list");
    var stores = buildDerivedStores();
    list.innerHTML = "";

    var allItem = document.createElement("li");
    var allButton = document.createElement("button");
    allButton.type = "button";
    allButton.className = selectedStore === "" ? "active" : "";
    allButton.innerHTML = '<span>Todas las tiendas</span><span class="sl-list-count">' + stores.length + '</span>';
    allButton.addEventListener("click", function () {
      selectedStore = "";
      renderAll();
    });
    allItem.appendChild(allButton);
    list.appendChild(allItem);

    stores.forEach(function (store) {
      var item = document.createElement("li");
      var button = document.createElement("button");
      button.type = "button";
      button.className = selectedStore === store.name ? "active" : "";
      button.innerHTML = '<span>' + escapeHtml(store.name) + '</span><span class="sl-list-count">' + store.count + '</span>';
      button.addEventListener("click", function () {
        selectedStore = store.name;
        renderAll();
      });
      item.appendChild(button);
      list.appendChild(item);
    });

    setText("sl-stat-stores", String(stores.length || 1));
  }

  function renderCategoryList() {
    var list = document.getElementById("sl-category-list");
    var categories = buildDerivedCategories();
    list.innerHTML = "";

    var allItem = document.createElement("li");
    var allButton = document.createElement("button");
    allButton.type = "button";
    allButton.className = selectedCategory === "" ? "active" : "";
    allButton.innerHTML = '<span>Todas</span><span class="sl-list-count">' + categories.length + '</span>';
    allButton.addEventListener("click", function () {
      selectedCategory = "";
      renderAll();
    });
    allItem.appendChild(allButton);
    list.appendChild(allItem);

    categories.forEach(function (category) {
      var item = document.createElement("li");
      var button = document.createElement("button");
      button.type = "button";
      button.className = selectedCategory === category.name ? "active" : "";
      button.innerHTML = '<span>' + escapeHtml(category.name) + '</span><span class="sl-list-count">' + category.count + '</span>';
      button.addEventListener("click", function () {
        selectedCategory = category.name;
        renderAll();
      });
      item.appendChild(button);
      list.appendChild(item);
    });

    setText("sl-stat-categories", String(categories.length));
  }

  function renderOfferList() {
    var list = document.getElementById("sl-offer-list");
    var items = [
      { key: "all", label: "Todo el catalogo", count: allProducts.filter(isProductPublished).length },
      { key: "offers", label: "Ofertas", count: allProducts.filter(function (product) { return isProductPublished(product) && hasOffer(product); }).length },
      { key: "new", label: "Nuevos", count: allProducts.filter(function (product) { return isProductPublished(product) && product.nuevo; }).length },
      { key: "ready", label: "Con imagen", count: allProducts.filter(function (product) { return isProductPublished(product) && hasImage(product); }).length },
    ];

    list.innerHTML = "";
    items.forEach(function (offer) {
      var item = document.createElement("li");
      var button = document.createElement("button");
      button.type = "button";
      button.className = selectedOffer === offer.key ? "active" : "";
      button.innerHTML = '<span>' + escapeHtml(offer.label) + '</span><span class="sl-list-count">' + offer.count + '</span>';
      button.addEventListener("click", function () {
        selectedOffer = offer.key;
        renderAll();
      });
      item.appendChild(button);
      list.appendChild(item);
    });
  }

  function renderActiveFilters() {
    var container = document.getElementById("sl-active-filters");
    container.innerHTML = "";
    var filters = [];
    if (selectedStore) filters.push({ key: "store", label: selectedStore });
    if (selectedCategory) filters.push({ key: "category", label: selectedCategory });
    if (selectedOffer !== "all") {
      var offerLabel = selectedOffer === "offers" ? "Ofertas" : (selectedOffer === "new" ? "Nuevos" : "Con imagen");
      filters.push({ key: "offer", label: offerLabel });
    }
    if (searchQ) filters.push({ key: "search", label: 'Busqueda: "' + searchQ + '"' });

    filters.forEach(function (filter) {
      var pill = document.createElement("span");
      pill.className = "sl-pill";
      pill.innerHTML = '<span>' + escapeHtml(filter.label) + '</span><button type="button" aria-label="Quitar filtro">x</button>';
      pill.querySelector("button").addEventListener("click", function () {
        if (filter.key === "store") selectedStore = "";
        if (filter.key === "category") selectedCategory = "";
        if (filter.key === "offer") selectedOffer = "all";
        if (filter.key === "search") {
          searchQ = "";
          document.getElementById("sl-search-input").value = "";
        }
        renderAll();
      });
      container.appendChild(pill);
    });
  }

  function makeBadgeMarkup(product) {
    var badges = [];
    if (product.nuevo) badges.push('<span class="sl-badge">Nuevo</span>');
    var category = getProductCategory(product);
    if (category) badges.push('<span class="sl-badge">' + escapeHtml(category) + '</span>');
    return badges.length ? '<div class="sl-card-badges">' + badges.join("") + "</div>" : "";
  }

  function makeMediaMarkup(product) {
    if (hasImage(product)) {
      return '<img class="sl-card-img" src="' + escapeHtml(product.imagen) + '" alt="' + escapeHtml(product.nombre || "Producto") + '" ' +
        'onerror="var m=this.parentElement;m.innerHTML=\'<div class=\\\"sl-card-img-placeholder\\\">□</div>\'" />';
    }
    return '<div class="sl-card-img-placeholder">□</div>';
  }

  function makeGridCard(product) {
    var card = document.createElement("article");
    card.className = "sl-card";
    var pid = String(product.id || product.nombre || "");
    var hidePrices = !!(currentStoreInfo && currentStoreInfo.hide_product_prices);
    card.dataset.productId = pid;
    card.innerHTML =
      '<div class="sl-card-media">' +
        makeMediaMarkup(product) +
        makeBadgeMarkup(product) +
        makeCartLink() +
        makeWishButton(product) +
      "</div>" +
      '<div class="sl-card-body">' +
        '<div class="sl-card-store">' + escapeHtml(deriveStoreName(product)) + "</div>" +
        '<h3 class="sl-card-name">' + escapeHtml(product.nombre || "Producto") + "</h3>" +
        '<p class="sl-card-desc">' + escapeHtml(product.descCorta || product.descLarga || "Sin descripcion disponible.") + "</p>" +
        '<div class="sl-card-footer">' +
          '<div class="sl-card-price">' + escapeHtml(hidePrices ? "Consultar" : formatPrice(product.precio)) + '<small>' + escapeHtml(getProductCategory(product) || "Categoria general") + "</small></div>" +
          '<button class="sl-card-cta" type="button">Ver detalle</button>' +
        "</div>" +
      "</div>";
    return card;
  }

  function makeListCard(product) {
    var card = document.createElement("article");
    card.className = "sl-card-list";
    var pid = String(product.id || product.nombre || "");
    var hidePrices = !!(currentStoreInfo && currentStoreInfo.hide_product_prices);
    card.dataset.productId = pid;
    card.innerHTML =
      '<div class="sl-card-media">' +
        makeMediaMarkup(product) +
        makeBadgeMarkup(product) +
        makeCartLink() +
        makeWishButton(product) +
      "</div>" +
      '<div class="sl-card-body">' +
        '<div class="sl-card-store">' + escapeHtml(deriveStoreName(product)) + "</div>" +
        '<h3 class="sl-card-name">' + escapeHtml(product.nombre || "Producto") + "</h3>" +
        '<p class="sl-card-desc">' + escapeHtml(product.descCorta || product.descLarga || "Sin descripcion disponible.") + "</p>" +
        '<div class="sl-card-footer">' +
          '<div class="sl-card-price">' + escapeHtml(hidePrices ? "Consultar" : formatPrice(product.precio)) + '<small>' + escapeHtml(getProductCategory(product) || "Categoria general") + "</small></div>" +
          '<button class="sl-card-cta" type="button">Ver detalle</button>' +
        "</div>" +
      "</div>";
    return card;
  }

  function renderProducts() {
    var container = document.getElementById("sl-products-container");
    var products = getDisplayProducts();
    container.className = viewMode === "grid" ? "sl-products-grid" : "sl-products-list";
    container.innerHTML = "";

    document.getElementById("sl-results-count").textContent = products.length + (products.length === 1 ? " resultado" : " resultados");
    document.getElementById("sl-summary-title").textContent = selectedCategory ? selectedCategory : "Todos los productos";
    setText("sl-stat-products", String(allProducts.filter(isProductPublished).length));

    if (!products.length) {
      container.innerHTML =
        '<div class="sl-empty">' +
          '<div class="sl-empty-icon">⌕</div>' +
          "<strong>No encontramos productos con esos filtros</strong>" +
          "<span>Ajusta la busqueda, cambia la categoria o limpia los filtros activos.</span>" +
        "</div>";
      return;
    }

    products.forEach(function (product) {
      container.appendChild(viewMode === "grid" ? makeGridCard(product) : makeListCard(product));
    });
  }

  function renderAll() {
    updateHero();
    renderFeaturedCategories();
    renderStoreList();
    renderCategoryList();
    renderOfferList();
    renderActiveFilters();
    renderProducts();
  }

  function clearFilters() {
    selectedCategory = "";
    selectedStore = "";
    selectedOffer = "all";
    searchQ = "";
    sortMode = "featured";
    document.getElementById("sl-search-input").value = "";
    document.getElementById("sl-sort-select").value = "featured";
    renderAll();
  }

  async function hydrateStores() {
    try {
      var response = await fetch("/multitienda/vendors/", { headers: { Accept: "application/json" } });
      if (!response.ok) return;
      var data = await response.json();
      if (Array.isArray(data)) allStores = data;
      renderStoreList();
    } catch (error) {}
  }

  function bindAccordion() {
    document.querySelectorAll(".sl-acc-toggle").forEach(function (button) {
      button.addEventListener("click", function () {
        var item = button.parentElement;
        var isOpen = item.getAttribute("data-open") !== "false";
        item.setAttribute("data-open", isOpen ? "false" : "true");
        var body = button.nextElementSibling;
        if (body) body.hidden = isOpen;
      });
    });
  }

  function bindEvents() {
    document.getElementById("sl-view-grid").addEventListener("click", function () {
      viewMode = "grid";
      document.getElementById("sl-view-grid").classList.add("active");
      document.getElementById("sl-view-list").classList.remove("active");
      renderProducts();
    });

    document.getElementById("sl-view-list").addEventListener("click", function () {
      viewMode = "list";
      document.getElementById("sl-view-list").classList.add("active");
      document.getElementById("sl-view-grid").classList.remove("active");
      renderProducts();
    });

    document.getElementById("sl-search-input").addEventListener("input", function (event) {
      searchQ = normalizeText(event.target.value);
      renderAll();
    });

    document.getElementById("sl-sort-select").addEventListener("change", function (event) {
      sortMode = event.target.value;
      renderProducts();
    });

    document.getElementById("sl-clear-filters").addEventListener("click", clearFilters);

    var contactBtn = document.getElementById("sl-contact-btn");
    if (contactBtn) {
      contactBtn.addEventListener("click", function () {
        var emailEl = document.getElementById("sl-store-email");
        var email = normalizeText(emailEl ? emailEl.textContent : "");
        var subject = encodeURIComponent("Consulta sobre productos");
        if (email && email.indexOf("@") !== -1) {
          window.location.href = "mailto:" + email + "?subject=" + subject;
          return;
        }
        alert("No hay correo configurado para esta tienda.");
      });
    }

    var viewStoreBtn = document.getElementById("sl-view-store-btn");
    if (viewStoreBtn) {
      viewStoreBtn.addEventListener("click", function () {
        document.getElementById("sl-search-input").focus();
      });
    }

    // Wishlist: event delegation on products container
    document.getElementById("sl-products-container").addEventListener("click", function (event) {
      var btn = event.target.closest("[data-wish-id]");
      if (!btn) return;
      event.stopPropagation();
      var productId = btn.dataset.wishId;
      var card = btn.closest("[data-product-id]");
      var product = allProducts.find(function (p) {
        return String(p.id || p.nombre || "") === productId;
      }) || {};
      toggleWishlist(productId, product, btn);
    });

    // Ver detalle: navega a /{store_slug}/{product_slug}
    document.getElementById("sl-products-container").addEventListener("click", function (event) {
      var cta = event.target.closest(".sl-card-cta");
      if (!cta) return;
      var card = cta.closest("[data-product-id]");
      if (!card) return;
      var productId = card.dataset.productId;
      var product = allProducts.find(function (p) {
        return String(p.id || p.nombre || "") === productId;
      });
      if (!product) return;
      var storeSlug = product.store_slug || detectStoreSlugFromPath();
      var productSlug = product.slug || encodeURIComponent((product.nombre || "").toLowerCase().replace(/\s+/g, "-"));
      if (storeSlug && productSlug) {
        window.location.href = "/" + storeSlug + "/" + productSlug;
      }
    });
  }

  function _cleanImagen(img) {
    if (!img) return "";
    if (img.startsWith("data:image/")) return img;             // data URL embebida
    if (img.startsWith("/") && !img.startsWith("//")) return img; // ruta relativa al servidor
    if (img.startsWith("https://")) return img;                // CDN / servidor externo HTTPS
    return "";  // descarta http:// localhost y otros artefactos del desarrollo
  }

  function loadInitialData() {
    allProducts = safeParse(localStorage.getItem("multitienda_productos"), []);
    allCategories = safeParse(localStorage.getItem("multitienda_categorias"), []);
    if (!Array.isArray(allProducts)) allProducts = [];
    if (!Array.isArray(allCategories)) allCategories = [];
    // Limpiar URLs absolutas corruptas de sesiones anteriores
    allProducts.forEach(function (p) { p.imagen = _cleanImagen(p.imagen); });
  }

  function hydrateProducts() {
    var slug = detectStoreSlugFromPath();
    var endpoint = "/multitienda/api/productos-publicos";
    if (slug) endpoint += "?store_slug=" + encodeURIComponent(slug);
    fetch(endpoint, { headers: { Accept: "application/json" } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (payload) {
        var items = payload && Array.isArray(payload.data) ? payload.data : [];
        if (!items.length) return;
        // Merge: API items primero; si la API trae imagen vacía pero localStorage tiene una, se preserva
        var seen = {};
        var merged = [];
        var localMap = {};
        allProducts.forEach(function (p) {
          var key = String(p.id || "") + "|" + String(p.slug || p.nombre || "").toLowerCase();
          localMap[key] = p;
        });
        (items.concat(allProducts)).forEach(function (p) {
          var key = String(p.id || "") + "|" + String(p.slug || p.nombre || "").toLowerCase();
          if (!seen[key]) {
            seen[key] = true;
            var local = localMap[key];
            var localImg = local && local.imagen || "";
            var isValidLocal = localImg && (localImg.startsWith("data:") || localImg.startsWith("/"));
            if (!p.imagen && isValidLocal) { p = Object.assign({}, p, { imagen: localImg }); }
            merged.push(p);
          }
        });
        allProducts = merged;
        // Limpiar URLs corruptas de la respuesta de API
        allProducts.forEach(function (p) { p.imagen = _cleanImagen(p.imagen); });
        // Actualizar localStorage para sesiones futuras
        try { localStorage.setItem("multitienda_productos", JSON.stringify(allProducts)); } catch (e) {}
        // Si estamos en detalle de producto, mostrar esa vista; si no, catálogo normal
        if (!maybeShowProductDetail()) {
          renderAll();
        }
      })
      .catch(function () {});
  }

  /* ── Vista detalle de producto ─────────────────────────── */
  function renderProductDetail(product) {
    // Ocultar catálogo, mostrar detalle
    var content = document.querySelector(".sl-content");
    var toolbar = document.querySelector(".sl-toolbar");
    if (content) content.style.display = "none";
    if (toolbar) toolbar.style.display = "none";

    var detail = document.getElementById("sl-product-detail");
    if (!detail) return;
    detail.hidden = false;

    var mainImage = product.imagen || "";
    var img = mainImage
      ? '<div class="sl-detail-zoom" id="sl-detail-zoom">' +
          '<img class="sl-detail-img" id="sl-detail-main-img" src="' + escapeHtml(mainImage) + '" alt="' + escapeHtml(product.nombre || "") + '" onerror="this.src=\'/static/imagenes/logo_vale.png\'" />' +
        '</div>'
      : '<div class="sl-detail-img-placeholder">□</div>';

    var galleryImages = [];
    var storeSlug = product.store_slug || detectStoreSlugFromPath();
    if (mainImage) galleryImages.push(mainImage);
    if (Array.isArray(product.galleryImages) && product.galleryImages.length) {
      product.galleryImages.forEach(function (src) {
        if (src && galleryImages.indexOf(src) === -1) galleryImages.push(src);
      });
    }
    var gallerySlots = galleryImages.slice(0, 5);
    while (gallerySlots.length < 4) gallerySlots.push("");
    var gallery = '<div class="sl-detail-gallery-wrap">' +
      '<div class="sl-detail-gallery-label">Mas fotos del producto</div>' +
      '<div class="sl-detail-gallery">' +
        gallerySlots.map(function (src, index) {
          if (!src) {
            return '<button class="sl-detail-gallery-thumb sl-detail-gallery-thumb--empty" type="button" aria-hidden="true" tabindex="-1"></button>';
          }
          return '<button class="sl-detail-gallery-thumb' + (index === 0 ? " is-active" : "") + '" type="button" data-detail-thumb="' + escapeHtml(src) + '">' +
            '<img src="' + escapeHtml(src) + '" alt="" onerror="this.parentElement.remove()" />' +
          '</button>';
        }).join("") +
      '</div>' +
    '</div>';

    var detailTabs = [];
    if (product.mostrarDetalles !== false && normalizeText(product.detallesHtml)) {
      detailTabs.push({
        key: "detalles",
        label: "Detalles del articulo",
        content:
          '<div class="sl-detail-richtext">' + String(product.detallesHtml) + '</div>',
      });
    }
    if (product.mostrarEspecificaciones !== false && normalizeText(product.especificacionesHtml)) {
      detailTabs.push({
        key: "especificaciones",
        label: "Especificacion",
        content:
          '<div class="sl-detail-richtext">' + String(product.especificacionesHtml) + '</div>',
      });
    }
    detailTabs.push({
      key: "valoraciones",
      label: "Valoraciones",
      content:
        '<div class="sl-detail-empty-state">Todavia no hay valoraciones para este producto.</div>',
    });
    detailTabs.push({
      key: "ofertas",
      label: "Mas ofertas",
      content:
        '<div class="sl-detail-empty-state">Aun no hay mas ofertas disponibles para este producto.</div>',
    });
    detailTabs.push({
      key: "consultas",
      label: "Consultas",
      content:
        '<div class="sl-detail-empty-state">Aun no hay consultas registradas.</div>',
    });
    if (product.mostrarCondiciones !== false && normalizeText(product.condicionesHtml)) {
      detailTabs.push({
        key: "condiciones",
        label: "Condiciones adicionales",
        content:
          '<div class="sl-detail-richtext">' + String(product.condicionesHtml) + '</div>',
      });
    }

    var tabsMarkup = "";
    if (detailTabs.length) {
      tabsMarkup =
        '<div class="sl-detail-tabs">' +
          '<div class="sl-detail-tablist" role="tablist" aria-label="Secciones del producto">' +
            detailTabs.map(function (tab, index) {
              return (
                '<button class="sl-detail-tab' + (index === 0 ? " is-active" : "") + '" ' +
                  'type="button" role="tab" data-detail-tab="' + escapeHtml(tab.key) + '" ' +
                  'aria-selected="' + (index === 0 ? "true" : "false") + '">' +
                  escapeHtml(tab.label) +
                '</button>'
              );
            }).join("") +
          '</div>' +
          '<div class="sl-detail-panels">' +
            detailTabs.map(function (tab, index) {
              return (
                '<section class="sl-detail-section' + (index === 0 ? " is-active" : "") + '" ' +
                  'role="tabpanel" data-detail-panel="' + escapeHtml(tab.key) + '"' +
                  (index === 0 ? "" : ' hidden') + ">" +
                  tab.content +
                "</section>"
              );
            }).join("") +
          "</div>" +
        "</div>";
    }

    detail.innerHTML =
      '<div class="sl-detail-back"><a href="javascript:history.back()" class="sl-detail-back-link">← Volver</a></div>' +
      '<div class="sl-detail-wrap">' +
        '<div class="sl-detail-media">' + img + gallery + '</div>' +
        '<div class="sl-detail-info">' +
          '<div class="sl-detail-store">' + escapeHtml(product.tienda || "") + '</div>' +
          '<h1 class="sl-detail-name">' + escapeHtml(product.nombre || "Producto") + '</h1>' +
          (storeSlug
            ? '<a class="sl-detail-store-link" href="/' + escapeHtml(storeSlug) + '">Ver todos los productos de la tienda</a>'
            : '') +
          (product.descCorta ? '<p class="sl-detail-desc-short">' + escapeHtml(product.descCorta) + '</p>' : '') +
          '<div class="sl-detail-price">' + escapeHtml(formatPrice(product.precio)) + '</div>' +
          (product.categoria ? '<div class="sl-detail-category">Categoría: ' + escapeHtml(product.categoria) + '</div>' : '') +
          (product.descLarga && product.descLarga !== product.descCorta
            ? '<div class="sl-detail-desc-long">' + escapeHtml(product.descLarga) + '</div>'
            : '') +
        '</div>' +
      '</div>' +
      tabsMarkup;

    bindProductDetailTabs(detail);
    bindProductDetailGallery(detail);
    bindProductDetailZoom(detail);
  }

  function bindProductDetailTabs(detailRoot) {
    if (!detailRoot) return;
    var tabs = Array.prototype.slice.call(detailRoot.querySelectorAll("[data-detail-tab]"));
    var panels = Array.prototype.slice.call(detailRoot.querySelectorAll("[data-detail-panel]"));
    if (!tabs.length || !panels.length) return;

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var key = tab.getAttribute("data-detail-tab");
        tabs.forEach(function (currentTab) {
          var isActive = currentTab === tab;
          currentTab.classList.toggle("is-active", isActive);
          currentTab.setAttribute("aria-selected", isActive ? "true" : "false");
        });
        panels.forEach(function (panel) {
          var isActive = panel.getAttribute("data-detail-panel") === key;
          panel.classList.toggle("is-active", isActive);
          panel.hidden = !isActive;
        });
      });
    });
  }

  function bindProductDetailGallery(detailRoot) {
    if (!detailRoot) return;
    var mainImg = detailRoot.querySelector("#sl-detail-main-img");
    var thumbs = Array.prototype.slice.call(detailRoot.querySelectorAll("[data-detail-thumb]"));
    if (!mainImg || !thumbs.length) return;

    thumbs.forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        var src = thumb.getAttribute("data-detail-thumb");
        if (!src) return;
        mainImg.src = src;
        thumbs.forEach(function (item) {
          item.classList.toggle("is-active", item === thumb);
        });
      });
    });
  }

  function bindProductDetailZoom(detailRoot) {
    if (!detailRoot) return;
    var zoom = detailRoot.querySelector("#sl-detail-zoom");
    var image = detailRoot.querySelector("#sl-detail-main-img");
    if (!zoom || !image) return;

    zoom.addEventListener("mousemove", function (event) {
      var rect = zoom.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      var x = ((event.clientX - rect.left) / rect.width) * 100;
      var y = ((event.clientY - rect.top) / rect.height) * 100;
      image.style.transformOrigin = x + "% " + y + "%";
      zoom.classList.add("is-zooming");
    });

    zoom.addEventListener("mouseenter", function () {
      zoom.classList.add("is-zooming");
    });

    zoom.addEventListener("mouseleave", function () {
      zoom.classList.remove("is-zooming");
      image.style.transformOrigin = "50% 50%";
    });
  }

  function maybeShowProductDetail() {
    var pathInfo = _parsePath();
    if (!pathInfo.productSlug) return false;
    // Buscar en allProducts por slug
    var product = allProducts.find(function (p) {
      return (p.slug || "").toLowerCase() === pathInfo.productSlug.toLowerCase();
    });
    if (product) {
      renderProductDetail(product);
      return true;
    }
    return false;
  }

  loadInitialData();
  bindAccordion();
  bindEvents();

  var pathInfo = _parsePath();
  if (pathInfo.productSlug) {
    // Estamos en /{store_slug}/{product_slug}: ocultar catálogo de inicio,
    // cargar productos de esa tienda y mostrar el detalle
    var content = document.querySelector(".sl-content");
    var toolbar = document.querySelector(".sl-toolbar");
    if (content) content.style.display = "none";
    if (toolbar) toolbar.style.display = "none";
  } else {
    renderAll();
  }

  hydrateStores();
  hydrateProducts();
  hydrateStoreInfo();
})();

/* ── Sticky mini header ─────────────────────────────────── */
(function () {
  const header = document.getElementById('stickyMiniHeader');
  const hero   = document.getElementById('heroMarketplace');
  if (!header) return;

  function updateSticky() {
    const threshold = hero
      ? hero.getBoundingClientRect().bottom
      : 120;
    if (threshold < 0) {
      header.classList.add('is-visible');
    } else {
      header.classList.remove('is-visible');
    }
  }

  window.addEventListener('scroll', updateSticky, { passive: true });
  updateSticky();
})();
