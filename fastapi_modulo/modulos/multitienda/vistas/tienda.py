from __future__ import annotations


def tienda_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tienda</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { font-family: system-ui, -apple-system, sans-serif; background: #f3f4f6; color: #1f2937; font-size: 15px; }

    /* ══════════════════════
       HERO BANNER
    ══════════════════════ */
    .sl-hero {
      position: relative;
      width: 100%;
      height: 220px;
      overflow: hidden;
      background: linear-gradient(135deg, #0d3320 0%, #1a5c30 40%, #2d8a50 70%, #1a5c30 100%);
    }

    /* sparkle dots */
    .sl-hero::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        radial-gradient(circle 2px at 12% 30%, rgba(255,255,200,.85) 0%, transparent 60%),
        radial-gradient(circle 3px at 22% 55%, rgba(255,255,150,.7)  0%, transparent 60%),
        radial-gradient(circle 2px at 38% 20%, rgba(200,255,200,.8)  0%, transparent 60%),
        radial-gradient(circle 4px at 52% 45%, rgba(255,255,180,.9)  0%, transparent 60%),
        radial-gradient(circle 2px at 65% 25%, rgba(255,255,200,.75) 0%, transparent 60%),
        radial-gradient(circle 3px at 78% 60%, rgba(200,255,150,.7)  0%, transparent 60%),
        radial-gradient(circle 2px at 88% 35%, rgba(255,255,200,.8)  0%, transparent 60%),
        radial-gradient(circle 2px at 8%  70%, rgba(255,240,150,.6)  0%, transparent 60%),
        radial-gradient(circle 3px at 45% 75%, rgba(255,255,180,.65) 0%, transparent 60%);
      pointer-events: none;
    }

    /* glow center */
    .sl-hero::after {
      content: "";
      position: absolute;
      top: 50%;
      left: 55%;
      transform: translate(-50%, -50%);
      width: 320px;
      height: 320px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(100,230,130,.18) 0%, transparent 70%);
      pointer-events: none;
    }

    .sl-hero-logo {
      position: absolute;
      right: 60px;
      top: 50%;
      transform: translateY(-50%);
      width: 160px;
      height: 160px;
      border-radius: 50%;
      object-fit: cover;
      border: 4px solid rgba(255,255,255,.25);
      box-shadow: 0 0 40px rgba(80,200,100,.4), 0 0 80px rgba(60,180,80,.2);
      background: #fff;
    }

    /* ══════════════════════
       INFO BAR
    ══════════════════════ */
    .sl-info-bar {
      background: #111827;
      padding: 14px 32px;
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .sl-info-logo {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      object-fit: cover;
      border: 3px solid rgba(255,255,255,.2);
      background: #fff;
      flex-shrink: 0;
    }

    .sl-info-details {
      flex: 1;
      min-width: 0;
    }

    .sl-info-name {
      font-size: 1.25rem;
      font-weight: 700;
      color: #fff;
      line-height: 1.2;
    }

    .sl-info-stars {
      display: flex;
      gap: 2px;
      margin: 4px 0 6px;
    }

    .sl-star {
      font-size: 1rem;
      color: #fbbf24;
    }

    .sl-info-contact {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }

    .sl-info-contact span {
      font-size: .85rem;
      color: #d1d5db;
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .sl-info-contact .ic {
      font-size: .9rem;
    }

    .sl-consulta-btn {
      flex-shrink: 0;
      padding: 10px 22px;
      background: #fff;
      color: #111827;
      border: none;
      border-radius: 24px;
      font-size: .9rem;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 7px;
      white-space: nowrap;
      transition: background .15s;
    }

    .sl-consulta-btn:hover { background: #f3f4f6; }

    /* ══════════════════════
       BODY LAYOUT
    ══════════════════════ */
    .sl-body {
      display: grid;
      grid-template-columns: 240px 1fr;
      gap: 0;
      max-width: 1400px;
      margin: 0 auto;
      padding: 20px 16px 40px;
      align-items: start;
    }

    /* ── SIDEBAR ── */
    .sl-sidebar {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: 10px;
      padding: 18px 16px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      position: sticky;
      top: 16px;
    }

    .sl-all-stores-link {
      color: #15803d;
      font-size: .9rem;
      font-weight: 600;
      text-decoration: none;
      border-bottom: 2px solid #bbf7d0;
      padding-bottom: 12px;
    }

    .sl-all-stores-link:hover { color: #166534; text-decoration: underline; }

    .sl-sidebar-section h3 {
      font-size: 1rem;
      font-weight: 700;
      color: #1f2937;
      margin-bottom: 10px;
    }

    .sl-search-row {
      display: flex;
      gap: 6px;
    }

    .sl-search-input {
      flex: 1;
      padding: 8px 12px;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      font-size: .875rem;
      outline: none;
      background: #fff;
    }

    .sl-search-input:focus { border-color: #16a34a; box-shadow: 0 0 0 3px rgba(22,163,74,.1); }

    .sl-search-btn {
      padding: 8px 12px;
      background: #fff;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      cursor: pointer;
      font-size: .9rem;
      color: #374151;
      transition: background .15s;
    }

    .sl-search-btn:hover { background: #f9fafb; }

    .sl-cat-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .sl-cat-item {
      font-size: .875rem;
      color: #374151;
      cursor: pointer;
      padding: 5px 8px;
      border-radius: 6px;
      transition: background .12s;
    }

    .sl-cat-item:hover, .sl-cat-item.active { background: #dcfce7; color: #15803d; font-weight: 600; }

    /* ── MAIN ── */
    .sl-main {
      padding-left: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    /* nav tabs */
    .sl-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
    }

    .sl-nav-tab {
      padding: 9px 18px;
      border-radius: 6px;
      font-size: .88rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      background: #f3f4f6;
      color: #374151;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: background .15s, color .15s;
    }

    .sl-nav-tab:hover { background: #e5e7eb; }

    .sl-nav-tab.active {
      background: #16a34a;
      color: #fff;
    }

    /* view toggle */
    .sl-panel-header {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 8px;
    }

    .sl-view-btn {
      padding: 6px 14px;
      border-radius: 6px;
      font-size: .82rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid #16a34a;
      background: #fff;
      color: #16a34a;
      transition: background .15s, color .15s;
    }

    .sl-view-btn.active {
      background: #16a34a;
      color: #fff;
    }

    /* ── PRODUCT GRID ── */
    .sl-products-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
    }

    .sl-products-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    /* card grid */
    .sl-card {
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      overflow: hidden;
      cursor: pointer;
      transition: box-shadow .15s, transform .15s;
    }

    .sl-card:hover {
      box-shadow: 0 4px 20px rgba(0,0,0,.1);
      transform: translateY(-2px);
    }

    .sl-card-img {
      width: 100%;
      aspect-ratio: 1 / 1;
      object-fit: cover;
      background: #f9fafb;
      display: block;
    }

    .sl-card-img-placeholder {
      width: 100%;
      aspect-ratio: 1 / 1;
      background: linear-gradient(135deg, #f0fdf4, #dcfce7);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 2.5rem;
      color: #86efac;
    }

    .sl-card-body {
      padding: 12px 14px 14px;
    }

    .sl-card-name {
      font-size: .95rem;
      font-weight: 600;
      color: #1f2937;
      margin-bottom: 4px;
      line-height: 1.3;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .sl-card-price {
      font-size: 1rem;
      font-weight: 700;
      color: #16a34a;
      margin-bottom: 6px;
    }

    .sl-card-desc {
      font-size: .8rem;
      color: #6b7280;
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    /* card list mode */
    .sl-card-list {
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      overflow: hidden;
      cursor: pointer;
      display: flex;
      gap: 0;
      transition: box-shadow .15s;
    }

    .sl-card-list:hover { box-shadow: 0 2px 12px rgba(0,0,0,.08); }

    .sl-card-list .sl-card-img,
    .sl-card-list .sl-card-img-placeholder {
      width: 100px;
      flex-shrink: 0;
      aspect-ratio: 1 / 1;
    }

    .sl-card-list .sl-card-body {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    /* empty state */
    .sl-empty {
      grid-column: 1 / -1;
      text-align: center;
      padding: 60px 20px;
      color: #9ca3af;
    }

    .sl-empty-icon { font-size: 2.5rem; margin-bottom: 12px; }
    .sl-empty-msg  { font-size: 1rem; }

    /* ── PANELS ── */
    .sl-panel { display: none; }
    .sl-panel.active { display: block; }

    /* panel simple content */
    .sl-content-panel {
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 28px 32px;
      min-height: 200px;
    }

    .sl-content-panel p {
      color: #6b7280;
      font-size: .95rem;
      line-height: 1.6;
    }

    /* responsive */
    @media (max-width: 900px) {
      .sl-body { grid-template-columns: 1fr; }
      .sl-main { padding-left: 0; }
      .sl-products-grid { grid-template-columns: repeat(2, 1fr); }
      .sl-hero-logo { width: 110px; height: 110px; right: 20px; }
    }

    @media (max-width: 560px) {
      .sl-products-grid { grid-template-columns: 1fr; }
      .sl-info-bar { flex-wrap: wrap; }
    }
  </style>
</head>
<body>
<div class="page">

  <!-- ── Hero banner ── -->
  <div class="sl-hero">
    <img id="sl-hero-logo"
         src="/static/imagenes/logo_vale.png"
         alt="Logo de la tienda"
         class="sl-hero-logo" />
  </div>

  <!-- ── Info bar ── -->
  <div class="sl-info-bar">
    <img id="sl-info-logo"
         src="/static/imagenes/logo_vale.png"
         alt="Logo"
         class="sl-info-logo" />
    <div class="sl-info-details">
      <div class="sl-info-name" id="sl-store-name">Tu Negocio VALE</div>
      <div class="sl-info-stars">
        <span class="sl-star">★</span>
        <span class="sl-star">★</span>
        <span class="sl-star">★</span>
        <span class="sl-star">★</span>
        <span class="sl-star">★</span>
      </div>
      <div class="sl-info-contact">
        <span><span class="ic">✉</span> <span id="sl-store-email">contacto@tunegocio.com</span></span>
        <span><span class="ic">✆</span> <span id="sl-store-phone"></span></span>
      </div>
    </div>
    <button class="sl-consulta-btn" id="sl-consulta-btn" type="button">
      💬 Consulta
    </button>
  </div>

  <!-- ── Body ── -->
  <div class="sl-body">

    <!-- Sidebar -->
    <aside class="sl-sidebar">
      <a href="#" class="sl-all-stores-link" id="sl-all-stores-link">Ver todas las tiendas</a>

      <div class="sl-sidebar-section">
        <h3>Buscar</h3>
        <div class="sl-search-row">
          <input type="text" class="sl-search-input" id="sl-search-input" placeholder="Buscar productos…" />
          <button class="sl-search-btn" id="sl-search-btn" type="button">🔍</button>
        </div>
      </div>

      <div class="sl-sidebar-section">
        <h3>Categorías</h3>
        <ul class="sl-cat-list" id="sl-cat-list">
          <li class="sl-cat-item active" data-cat="">Todas</li>
        </ul>
      </div>
    </aside>

    <!-- Main -->
    <main class="sl-main">

      <!-- nav tabs -->
      <nav class="sl-nav">
        <button class="sl-nav-tab active" type="button" data-panel="productos">
          🏪 Productos
        </button>
        <button class="sl-nav-tab" type="button" data-panel="ofertas">
          🎁 Ofertas y beneficios
        </button>
        <button class="sl-nav-tab" type="button" data-panel="acerca">
          ℹ Acerca de
        </button>
        <button class="sl-nav-tab" type="button" data-panel="politicas">
          🤝 Políticas
        </button>
        <button class="sl-nav-tab" type="button" data-panel="resenas">
          ★ Reseñas (<span id="sl-review-count">0</span>)
        </button>
      </nav>

      <!-- ── Panel: Productos ── -->
      <div class="sl-panel active" id="sl-panel-productos">
        <div class="sl-panel-header">
          <button class="sl-view-btn active" id="sl-view-grid" type="button">⊞ Grilla</button>
          <button class="sl-view-btn" id="sl-view-list" type="button">☰ Listado</button>
        </div>
        <div id="sl-products-container" class="sl-products-grid" style="margin-top:12px;"></div>
      </div>

      <!-- ── Panel: Ofertas ── -->
      <div class="sl-panel" id="sl-panel-ofertas">
        <div class="sl-content-panel">
          <p>No hay ofertas disponibles en este momento.</p>
        </div>
      </div>

      <!-- ── Panel: Acerca de ── -->
      <div class="sl-panel" id="sl-panel-acerca">
        <div class="sl-content-panel">
          <p id="sl-acerca-text">Información sobre la tienda.</p>
        </div>
      </div>

      <!-- ── Panel: Políticas ── -->
      <div class="sl-panel" id="sl-panel-politicas">
        <div class="sl-content-panel">
          <p>Las políticas de la tienda serán publicadas próximamente.</p>
        </div>
      </div>

      <!-- ── Panel: Reseñas ── -->
      <div class="sl-panel" id="sl-panel-resenas">
        <div class="sl-content-panel">
          <p>Aún no hay reseñas para esta tienda.</p>
        </div>
      </div>

    </main>
  </div><!-- /sl-body -->

</div><!-- /page -->

<script>
(function () {
  var DEFAULT_LOGO = "/static/imagenes/logo_vale.png";

  /* ── Load store data from localStorage ── */
  var allProducts = [];
  var allCategories = [];
  var filterCat = "";
  var searchQ   = "";
  var viewMode  = "grid"; /* grid | list */

  function loadData() {
    try { allProducts   = JSON.parse(localStorage.getItem("multitienda_productos") || "[]"); } catch(e) { allProducts = []; }
    try { allCategories = JSON.parse(localStorage.getItem("multitienda_categorias") || "[]"); } catch(e) { allCategories = []; }

    var storeName = localStorage.getItem("multitienda_store_name") || "Tu Negocio VALE";
    var storeEmail = localStorage.getItem("multitienda_store_email") || "";
    var storePhone = localStorage.getItem("multitienda_store_phone") || "";
    var storeLogoRaw = localStorage.getItem("backend_template_sidebar_settings");
    var storeLogo = DEFAULT_LOGO;
    if (storeLogoRaw) {
      try {
        var ss = JSON.parse(storeLogoRaw);
        if (ss.logo) storeLogo = ss.logo;
      } catch(e) {}
    }

    document.getElementById("sl-store-name").textContent  = storeName;
    document.getElementById("sl-store-email").textContent = storeEmail;
    document.getElementById("sl-store-phone").textContent = storePhone;
    document.getElementById("sl-hero-logo").src = storeLogo;
    document.getElementById("sl-info-logo").src = storeLogo;

    if (storeEmail) {
      document.getElementById("sl-consulta-btn").setAttribute("data-email", storeEmail);
    }
  }

  /* ── Sidebar categories ── */
  function renderCategories() {
    var list = document.getElementById("sl-cat-list");
    list.innerHTML = '<li class="sl-cat-item' + (filterCat === "" ? " active" : "") + '" data-cat="">Todas</li>';
    allCategories.forEach(function(c) {
      var name = (typeof c === "string") ? c : (c.nombre || c.name || String(c));
      if (!name) return;
      var li = document.createElement("li");
      li.className = "sl-cat-item" + (filterCat === name ? " active" : "");
      li.dataset.cat = name;
      li.textContent = name;
      list.appendChild(li);
    });
    /* also build from product categories */
    var prodCats = {};
    allProducts.forEach(function(p) { if (p.categoria) prodCats[p.categoria] = true; });
    Object.keys(prodCats).forEach(function(cat) {
      if (!allCategories.find(function(c){ return (typeof c === "string" ? c : (c.nombre||c.name||"")) === cat; })) {
        var li = document.createElement("li");
        li.className = "sl-cat-item" + (filterCat === cat ? " active" : "");
        li.dataset.cat = cat;
        li.textContent = cat;
        list.appendChild(li);
      }
    });
    list.querySelectorAll(".sl-cat-item").forEach(function(li) {
      li.addEventListener("click", function() {
        filterCat = li.dataset.cat;
        list.querySelectorAll(".sl-cat-item").forEach(function(el){ el.classList.remove("active"); });
        li.classList.add("active");
        renderProducts();
      });
    });
  }

  /* ── Product rendering ── */
  function getFilteredProducts() {
    return allProducts.filter(function(p) {
      if (!p.publicado) return false;
      if (filterCat && p.categoria !== filterCat) return false;
      if (searchQ) {
        var q = searchQ.toLowerCase();
        return (p.nombre || "").toLowerCase().includes(q) ||
               (p.descCorta || "").toLowerCase().includes(q);
      }
      return true;
    });
  }

  function fmtPrice(val) {
    var n = parseFloat(val);
    if (isNaN(n)) return "";
    return "$" + n.toLocaleString("es-MX", {minimumFractionDigits:2, maximumFractionDigits:2});
  }

  function makeCardGrid(p) {
    var div = document.createElement("div");
    div.className = "sl-card";
    var imgHtml;
    if (p.imagen && p.imagen !== "" && !p.imagen.includes("undefined")) {
      imgHtml = '<img src="' + p.imagen + '" alt="' + (p.nombre || "") + '" class="sl-card-img" />';
    } else {
      imgHtml = '<div class="sl-card-img-placeholder">📦</div>';
    }
    div.innerHTML = imgHtml +
      '<div class="sl-card-body">' +
        '<div class="sl-card-name">' + (p.nombre || "") + '</div>' +
        (p.precio ? '<div class="sl-card-price">' + fmtPrice(p.precio) + '</div>' : '') +
        '<div class="sl-card-desc">' + (p.descCorta || "") + '</div>' +
      '</div>';
    return div;
  }

  function makeCardList(p) {
    var div = document.createElement("div");
    div.className = "sl-card-list";
    var imgHtml;
    if (p.imagen && p.imagen !== "" && !p.imagen.includes("undefined")) {
      imgHtml = '<img src="' + p.imagen + '" alt="' + (p.nombre || "") + '" class="sl-card-img" />';
    } else {
      imgHtml = '<div class="sl-card-img-placeholder">📦</div>';
    }
    div.innerHTML = imgHtml +
      '<div class="sl-card-body">' +
        '<div class="sl-card-name">' + (p.nombre || "") + '</div>' +
        (p.precio ? '<div class="sl-card-price">' + fmtPrice(p.precio) + '</div>' : '') +
        '<div class="sl-card-desc">' + (p.descCorta || "") + '</div>' +
      '</div>';
    return div;
  }

  function renderProducts() {
    var container = document.getElementById("sl-products-container");
    container.innerHTML = "";
    if (viewMode === "grid") {
      container.className = "sl-products-grid";
    } else {
      container.className = "sl-products-list";
    }
    var filtered = getFilteredProducts();
    if (!filtered.length) {
      var empty = document.createElement("div");
      empty.className = "sl-empty";
      empty.innerHTML = '<div class="sl-empty-icon">📦</div><div class="sl-empty-msg">No hay productos disponibles</div>';
      container.appendChild(empty);
      return;
    }
    filtered.forEach(function(p) {
      container.appendChild(viewMode === "grid" ? makeCardGrid(p) : makeCardList(p));
    });
  }

  /* ── Nav tabs ── */
  document.querySelectorAll(".sl-nav-tab").forEach(function(tab) {
    tab.addEventListener("click", function() {
      document.querySelectorAll(".sl-nav-tab").forEach(function(t){ t.classList.remove("active"); });
      document.querySelectorAll(".sl-panel").forEach(function(p){ p.classList.remove("active"); });
      tab.classList.add("active");
      var panel = document.getElementById("sl-panel-" + tab.dataset.panel);
      if (panel) panel.classList.add("active");
    });
  });

  /* ── View toggle ── */
  document.getElementById("sl-view-grid").addEventListener("click", function() {
    viewMode = "grid";
    document.getElementById("sl-view-grid").classList.add("active");
    document.getElementById("sl-view-list").classList.remove("active");
    renderProducts();
  });
  document.getElementById("sl-view-list").addEventListener("click", function() {
    viewMode = "list";
    document.getElementById("sl-view-list").classList.add("active");
    document.getElementById("sl-view-grid").classList.remove("active");
    renderProducts();
  });

  /* ── Search ── */
  document.getElementById("sl-search-input").addEventListener("input", function() {
    searchQ = this.value.trim();
    renderProducts();
  });
  document.getElementById("sl-search-btn").addEventListener("click", function() {
    searchQ = document.getElementById("sl-search-input").value.trim();
    renderProducts();
  });
  document.getElementById("sl-search-input").addEventListener("keydown", function(e) {
    if (e.key === "Enter") { searchQ = this.value.trim(); renderProducts(); }
  });

  /* ── Consulta button ── */
  document.getElementById("sl-consulta-btn").addEventListener("click", function() {
    var email = this.dataset.email || "";
    var name  = document.getElementById("sl-store-name").textContent;
    if (email) {
      window.location.href = "mailto:" + email + "?subject=Consulta sobre " + encodeURIComponent(name);
    } else {
      alert("Contacto no disponible.");
    }
  });

  /* ── Init ── */
  loadData();
  renderCategories();
  renderProducts();
})();
</script>
</body>
</html>"""
