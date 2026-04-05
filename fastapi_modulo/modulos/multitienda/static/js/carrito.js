(function () {
  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatPrice(value) {
    var numeric = parseFloat(value);
    if (isNaN(numeric)) numeric = 0;
    return "$" + numeric.toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function renderEmpty(container) {
    container.innerHTML =
      '<div class="sl-empty sl-cart-empty">' +
        '<div class="sl-empty-icon">🛒</div>' +
        '<strong>Tu carrito está vacío</strong>' +
        '<span>Agrega productos desde la tienda para verlos aquí.</span>' +
      '</div>';
  }

  function renderItems(payload) {
    var container = document.getElementById("sl-cart-items");
    var countEl = document.getElementById("sl-cart-count");
    var totalEl = document.getElementById("sl-cart-total");
    if (!container || !countEl || !totalEl) return;

    var items = payload && Array.isArray(payload.items) ? payload.items : [];
    countEl.textContent = String(payload && payload.items_count || 0);
    totalEl.textContent = formatPrice(payload && payload.total || 0);

    if (!items.length) {
      renderEmpty(container);
      return;
    }

    container.innerHTML = items.map(function (item) {
      return (
        '<article class="sl-cart-item">' +
          '<div class="sl-cart-item__media">' +
            (item.product_image
              ? '<img class="sl-cart-item__img" src="' + escapeHtml(item.product_image) + '" alt="' + escapeHtml(item.product_name || "") + '" />'
              : '<div class="sl-cart-item__placeholder">□</div>') +
          '</div>' +
          '<div class="sl-cart-item__body">' +
            '<div class="sl-cart-item__store">' + escapeHtml(item.store_name || "Tienda") + '</div>' +
            '<h3 class="sl-cart-item__name">' + escapeHtml(item.product_name || "Producto") + '</h3>' +
            '<div class="sl-cart-item__meta">Cantidad: ' + escapeHtml(item.quantity) + "</div>" +
          '</div>' +
          '<div class="sl-cart-item__totals">' +
            '<strong>' + escapeHtml(formatPrice(item.subtotal)) + '</strong>' +
            '<span>' + escapeHtml(formatPrice(item.unit_price)) + ' c/u</span>' +
          '</div>' +
        '</article>'
      );
    }).join("");
  }

  fetch("/api/cart/", { headers: { Accept: "application/json" } })
    .then(function (response) { return response.ok ? response.json() : null; })
    .then(function (payload) { renderItems(payload || { items: [], items_count: 0, total: 0 }); })
    .catch(function () { renderEmpty(document.getElementById("sl-cart-items")); });
})();
