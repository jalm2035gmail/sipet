(function () {
  /* ════════════════════════════════
     ESTADO
  ════════════════════════════════ */
  var STORAGE_KEY   = "multitienda_productos";
  var CAT_KEY       = "multitienda_categorias";
  var PAGE_SIZE     = 15;
  var DEFAULT_PHOTO = "/static/imagenes/logo_vale.png";

  var allProducts      = [];
  var filteredProducts = [];
  var currentPage      = 1;
  var sortCol          = "nombre";
  var sortAsc          = true;
  var selectedIds      = new Set();
  var editIndex        = -1;   /* -1 = nuevo */
  var isPublicado      = false;
  var photoDataUrl     = null; /* foto pendiente (blob URL o data URL) */
  var galleryImages    = [];

  function activateNotebookTab(tabIndex) {
    document.querySelectorAll(".pf-nb-tab").forEach(function(t){ t.classList.remove("active"); t.setAttribute("aria-selected","false"); });
    document.querySelectorAll(".pf-nb-panel").forEach(function(p){ p.hidden=true; });
    var tab = document.getElementById("pf-tab-" + tabIndex);
    var panel = document.getElementById("pf-panel-" + tabIndex);
    if (tab) {
      tab.classList.add("active");
      tab.setAttribute("aria-selected", "true");
    }
    if (panel) panel.hidden = false;
  }

  function openNotebookDrawer(tabIndex) {
    activateNotebookTab(tabIndex || 1);
    var drawer = document.querySelector(".pf-notebook");
    var overlay = document.getElementById("pf-drawer-overlay");
    if (drawer) drawer.classList.add("is-open");
    if (overlay) overlay.hidden = false;
    document.body.classList.add("pf-drawer-open");
  }

  function closeNotebookDrawer() {
    var drawer = document.querySelector(".pf-notebook");
    var overlay = document.getElementById("pf-drawer-overlay");
    if (drawer) drawer.classList.remove("is-open");
    if (overlay) overlay.hidden = true;
    document.body.classList.remove("pf-drawer-open");
  }

  /* ── persistencia ── */
  async function load() {
    try {
      var response = await fetch("/multitienda/api/productos", {
        headers: { "Accept": "application/json" }
      });
      if (!response.ok) throw new Error("No se pudieron cargar los productos.");
      var result = await response.json().catch(function () { return {}; });
      allProducts = Array.isArray(result.data) ? result.data : [];
    } catch (e) {
      allProducts = [];
    }
    allProducts.forEach(function(p,i){ if (!p._id) p._id = "p" + Date.now() + i; });
  }
  async function saveAll() {
    var response = await fetch("/multitienda/api/productos", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ products: allProducts })
    });
    var result = await response.json().catch(function () { return {}; });
    if (!response.ok) {
      throw new Error(result.detail || "No se pudieron guardar los productos.");
    }
    allProducts = Array.isArray(result.data) ? result.data : allProducts;
    allProducts.forEach(function(p,i){ if (!p._id) p._id = "p" + Date.now() + i; });
  }

  function loadCategories() {
    try { return JSON.parse(localStorage.getItem(CAT_KEY) || "[]"); }
    catch(e) { return []; }
  }

  function readFileAsDataUrl(file) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function (event) {
        var result = event && event.target ? event.target.result : "";
        if (typeof result === "string") resolve(result);
        else reject(new Error("No se pudo leer la imagen."));
      };
      reader.onerror = function () {
        reject(new Error("No se pudo leer la imagen."));
      };
      reader.readAsDataURL(file);
    });
  }

  /* ── helpers ── */
  /* Devuelve la URL de imagen solo si es data URL o ruta relativa. Descarta URLs absolutas http(s) */
  function _safeImagen(raw) {
    if (!raw) return "";
    if (raw.startsWith("data:")) return raw;
    if (raw.startsWith("/")) return raw;
    return "";
  }

  function esc(s) { return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function fmtMoney(v) {
    var n = parseFloat(v);
    if (isNaN(n)) return "";
    return "$ " + n.toLocaleString("es-MX",{minimumFractionDigits:2,maximumFractionDigits:2});
  }

  function isScheduledPublished(mode, atValue) {
    if (mode !== "scheduled") return true;
    if (!atValue) return false;
    var scheduledDate = new Date(atValue);
    if (Number.isNaN(scheduledDate.getTime())) return false;
    return scheduledDate.getTime() <= Date.now();
  }

  function updatePublishHelp(mode, atValue) {
    var help = document.getElementById("pf-publish-help");
    if (!help) return;
    if (mode !== "scheduled") {
      help.textContent = "El producto se publica de inmediato al guardar.";
      return;
    }
    if (!atValue) {
      help.textContent = "Selecciona una fecha y hora para activar la publicación.";
      return;
    }
    help.textContent = "Se publicará automáticamente en la fecha y hora programadas.";
  }

  function renderGallery() {
    var list = document.getElementById("pf-gallery-list");
    var empty = document.getElementById("pf-gallery-empty");
    if (!list || !empty) return;
    list.innerHTML = "";
    if (!galleryImages.length) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    galleryImages.forEach(function (src, index) {
      var item = document.createElement("div");
      item.className = "pf-gallery-item";
      item.innerHTML =
        '<img src="' + esc(src) + '" alt="Foto adicional ' + (index + 1) + '" />' +
        '<div class="pf-gallery-tools">' +
        '<button class="pf-gallery-tool" data-gallery-main="' + index + '" type="button">Principal</button>' +
        '<button class="pf-gallery-tool" data-gallery-remove="' + index + '" type="button">Quitar</button>' +
        '</div>';
      list.appendChild(item);
    });
  }

  /* ════════════════════════════════
     VISTA LISTA
  ════════════════════════════════ */
  function applyFilterSort() {
    var q = (document.getElementById("pv-search").value || "").toLowerCase();
    filteredProducts = allProducts.filter(function(p) {
      if (!q) return true;
      return (p.nombre    ||"").toLowerCase().includes(q) ||
             (p.referencia||"").toLowerCase().includes(q) ||
             (p.etiquetas ||"").toLowerCase().includes(q);
    });
    filteredProducts.sort(function(a,b){
      var va = a[sortCol]||"", vb = b[sortCol]||"";
      if (sortCol==="precio"||sortCol==="costo") {
        va=parseFloat(va)||0; vb=parseFloat(vb)||0;
        return sortAsc ? va-vb : vb-va;
      }
      return sortAsc
        ? String(va).localeCompare(String(vb),"es")
        : String(vb).localeCompare(String(va),"es");
    });
    currentPage = 1;
    renderTable();
  }

  function renderTable() {
    var tbody   = document.getElementById("pv-tbody");
    var empty   = document.getElementById("pv-empty");
    var pagLbl  = document.getElementById("pv-pag-label");
    var prevBtn = document.getElementById("pv-prev-btn");
    var nextBtn = document.getElementById("pv-next-btn");
    tbody.innerHTML = "";

    if (filteredProducts.length === 0) {
      empty.hidden = false;
      pagLbl.textContent = "0 / 0";
      prevBtn.disabled = nextBtn.disabled = true;
      return;
    }
    empty.hidden = true;
    var totalPages = Math.ceil(filteredProducts.length / PAGE_SIZE);
    if (currentPage > totalPages) currentPage = totalPages;
    var start = (currentPage-1)*PAGE_SIZE;
    var end   = Math.min(start+PAGE_SIZE, filteredProducts.length);
    pagLbl.textContent = (start+1)+"-"+end+" / "+filteredProducts.length;
    prevBtn.disabled = currentPage<=1;
    nextBtn.disabled = currentPage>=totalPages;

    filteredProducts.slice(start,end).forEach(function(p){
      var tr = document.createElement("tr");
      if (selectedIds.has(p._id)) tr.classList.add("selected");
      var tags = (p.etiquetas||"").split(",").map(function(t){
        t=t.trim(); return t?'<span class="tag-badge">'+esc(t)+'</span>':"";
      }).join("");
      tr.innerHTML =
        '<td class="col-cb"><input class="cb-input" type="checkbox" data-id="'+esc(p._id)+'" '+(selectedIds.has(p._id)?"checked":"")+' /></td>'+
        '<td class="col-star"><button class="star-btn'+(p._star?" active":"")+'" data-star="'+esc(p._id)+'" type="button">★</button></td>'+
        '<td>'+esc(p.nombre||"—")+'</td>'+
        '<td style="color:var(--mp-muted);">'+esc(p.referencia||"")+'</td>'+
        '<td>'+(tags||"")+'</td>'+
        '<td class="col-num">'+fmtMoney(p.precio)+'</td>'+
        '<td class="col-num">'+fmtMoney(p.costo)+'</td>'+
        '<td></td>';
      tr.addEventListener("click", function(e){
        if (e.target.closest("[data-id]")||e.target.closest("[data-star]")) return;
        openForm(allProducts.indexOf(p));
      });
      document.getElementById("pv-tbody").appendChild(tr);
    });

    /* sort arrows */
    document.querySelectorAll(".pv-table th.sortable").forEach(function(th){
      var a = th.querySelector(".sort-arrow"); if (!a) return;
      if (th.dataset.col===sortCol){ a.textContent=sortAsc?"↑":"↓"; a.style.color="var(--mp-accent)"; }
      else { a.textContent="↕"; a.style.color="var(--mp-muted)"; }
    });
    var pageSlice = filteredProducts.slice(start,end);
    document.getElementById("pv-select-all").checked =
      pageSlice.length>0 && pageSlice.every(function(p){ return selectedIds.has(p._id); });
  }

  /* eventos lista */
  document.getElementById("pv-tbody").addEventListener("change", function(e){
    var cb = e.target.closest("[data-id]"); if (!cb) return;
    if (cb.checked) selectedIds.add(cb.dataset.id); else selectedIds.delete(cb.dataset.id);
    renderTable();
  });
  document.getElementById("pv-tbody").addEventListener("click", function(e){
    var s = e.target.closest("[data-star]"); if (!s) return;
    var p = allProducts.find(function(x){ return x._id===s.dataset.star; });
    if (p){
      p._star=!p._star;
      saveAll().then(function () {
        renderTable();
      }).catch(function (error) {
        alert(error && error.message ? error.message : "No se pudo guardar el cambio.");
      });
    }
  });
  document.getElementById("pv-select-all").addEventListener("change", function(){
    var start=(currentPage-1)*PAGE_SIZE;
    filteredProducts.slice(start,start+PAGE_SIZE).forEach(function(p){
      if (this.checked) selectedIds.add(p._id); else selectedIds.delete(p._id);
    },this);
    renderTable();
  });
  document.querySelectorAll(".pv-table th.sortable").forEach(function(th){
    th.addEventListener("click",function(){
      if (sortCol===th.dataset.col) sortAsc=!sortAsc; else { sortCol=th.dataset.col; sortAsc=true; }
      applyFilterSort();
    });
  });
  document.getElementById("pv-search").addEventListener("input", applyFilterSort);
  document.getElementById("pv-prev-btn").addEventListener("click",function(){
    if (currentPage>1){ currentPage--; renderTable(); }
  });
  document.getElementById("pv-next-btn").addEventListener("click",function(){
    if (currentPage<Math.ceil(filteredProducts.length/PAGE_SIZE)){ currentPage++; renderTable(); }
  });
  document.getElementById("pv-nuevo-btn").addEventListener("click",function(){ openForm(-1); });

  /* ════════════════════════════════
     VISTA FORM
  ════════════════════════════════ */
  function openForm(idx) {
    editIndex    = idx;
    isPublicado  = false;
    photoDataUrl = null;
    galleryImages = [];

    /* rellenar categorías */
    var catSel = document.getElementById("pf-categoria");
    catSel.innerHTML = '<option value="">Sin categoría</option>';
    loadCategories().forEach(function(c){
      var o=document.createElement("option"); o.value=c.nombre; o.textContent=c.nombre;
      catSel.appendChild(o);
    });

    var p = idx>=0 ? allProducts[idx] : {};
    isPublicado = !!p.publicado;

    /* campos */
    document.getElementById("pf-nombre").value              = p.nombre             || "";
    document.getElementById("pf-precio").value              = p.precio             || "";
    document.getElementById("pf-costo").value               = p.costo              || "";
    document.getElementById("pf-referencia").value          = p.referencia         || "";
    document.getElementById("pf-etiquetas").value           = p.etiquetas          || "";
    document.getElementById("pf-stock").value               = p.stock              || "";
    document.getElementById("pf-stock-min").value           = p.stockMin           || "";
    document.getElementById("pf-unidad").value              = p.unidad             || "pieza";
    document.getElementById("pf-codigo-barras").value       = p.codigoBarras       || "";
    document.getElementById("pf-notas-internas").value      = p.notasInternas      || "";
    document.getElementById("pf-politica-facturacion").value= p.politicaFacturacion|| "cantidad_ordenada";
    document.getElementById("pf-politica-hint").textContent = ({
      "cantidad_ordenada":  "Puede facturar los bienes antes de entregarlos.",
      "cantidad_entregada": "Solo puede facturar después de registrar la entrega.",
      "anticipo":           "Se factura un anticipo al confirmar el pedido."
    })[p.politicaFacturacion || "cantidad_ordenada"];
    catSel.value = p.categoria || "";

    /* tipo de producto */
    var tipo = p.tipoProducto || "bienes";
    document.querySelectorAll("[name='pf-tipo-producto']").forEach(function(r){ r.checked = r.value === tipo; });

    /* impuestos */
    taxVenta  = (p.taxVenta  || []).slice();
    taxCompra = (p.taxCompra || []).slice();
    renderTaxTags(document.getElementById("pf-tax-venta-tags"),  document.getElementById("pf-tax-venta-input"),  taxVenta,  document.getElementById("pf-tax-venta-calc"));
    renderTaxTags(document.getElementById("pf-tax-compra-tags"), document.getElementById("pf-tax-compra-input"), taxCompra, null);

    /* ventas */
    document.getElementById("pf-productos-opcionales").value = p.productosOpcionales || "";
    document.getElementById("pf-accesorios").value           = p.accesorios          || "";
    document.getElementById("pf-productos-alternos").value   = p.productosAlternos   || "";
    document.getElementById("pf-desc-cotizacion").value      = p.descCotizacion      || "";
    document.getElementById("pf-ecom-etiquetas").value       = p.ecomEtiquetas       || "";
    document.getElementById("pf-ecom-publicado").checked     = !!p.ecomPublicado;
    document.getElementById("pf-ecom-categorias").value      = p.ecomCategorias      || "";
    document.getElementById("pf-desc-ecom").value            = p.descEcom            || "";
    mediaFiles = (p.mediaFiles || []).slice();
    renderMedia();
    document.getElementById("pf-publish-mode").value         = p.publishMode || "immediate";
    document.getElementById("pf-publish-at").value           = p.publishAt || "";

    /* características */
    document.getElementById("pf-nuevo").checked     = !!p.nuevo;
    document.getElementById("pf-desc-corta").value = p.descCorta || "";
    document.getElementById("pf-desc-larga").value = p.descLarga || "";

    /* detalles del artículo */
    document.getElementById("pf-mostrar-detalles").checked       = p.mostrarDetalles !== false;
    document.getElementById("pf-detalles-editor").innerHTML      = p.detallesHtml || "";
    /* especificaciones */
    document.getElementById("pf-mostrar-especificaciones").checked    = p.mostrarEspecificaciones !== false;
    document.getElementById("pf-especificaciones-editor").innerHTML   = p.especificacionesHtml || "";
    /* condiciones especiales */
    document.getElementById("pf-mostrar-condiciones").checked    = p.mostrarCondiciones !== false;
    document.getElementById("pf-condiciones-editor").innerHTML   = p.condicionesHtml || "";

    /* foto */
    var cleanedImagen = _safeImagen(p.imagen || "");
    photoDataUrl = cleanedImagen;  // preserva la imagen válida; descarta URLs absolutas
    document.getElementById("pf-photo-preview").src = cleanedImagen || DEFAULT_PHOTO;
    galleryImages = Array.isArray(p.galleryImages) ? p.galleryImages.slice() : [];
    renderGallery();

    /* breadcrumb + publicar */
    document.getElementById("pf-breadcrumb-nombre").textContent = p.nombre || "Nuevo";
    isPublicado = isScheduledPublished(
      document.getElementById("pf-publish-mode").value,
      document.getElementById("pf-publish-at").value
    );
    updatePublishHelp(
      document.getElementById("pf-publish-mode").value,
      document.getElementById("pf-publish-at").value
    );
    syncPublicar();

    /* tabs (reset a primera pestaña) */
    activateNotebookTab(1);
    closeNotebookDrawer();

    /* mostrar/ocultar btn eliminar en form */
    document.getElementById("pf-eliminar-btn").style.display = idx >= 0 ? "" : "none";

    /* mostrar form en panel derecho */
    var placeholder = document.getElementById("pf-placeholder");
    if (placeholder) placeholder.hidden = true;
    document.getElementById("pf-view").hidden = false;
  }

  async function showList() {
    closeNotebookDrawer();
    var placeholder = document.getElementById("pf-placeholder");
    document.getElementById("pf-view").hidden = true;
    if (placeholder) placeholder.hidden = false;
    await load();
    applyFilterSort();
  }

  function syncPublicar() {
    document.querySelectorAll("#pf-publicar-btn, #pf-publicar-btn-card").forEach(function (btn) {
      if (isPublicado) {
        btn.textContent = "Publicado: sí";
        btn.classList.add("publicado");
      } else {
        btn.textContent = "Publicado: no";
        btn.classList.remove("publicado");
      }
    });
  }

  async function saveForm() {
    var nombre = document.getElementById("pf-nombre").value.trim();
    if (!nombre){ alert("El nombre del producto es obligatorio."); return; }

    var tipoChecked = document.querySelector("[name='pf-tipo-producto']:checked");
    var prod = {
      nombre:              nombre,
      precio:              document.getElementById("pf-precio").value,
      costo:               document.getElementById("pf-costo").value,
      referencia:          document.getElementById("pf-referencia").value.trim(),
      etiquetas:           document.getElementById("pf-etiquetas").value.trim(),
      stock:               document.getElementById("pf-stock").value,
      stockMin:            document.getElementById("pf-stock-min").value,
      unidad:              document.getElementById("pf-unidad").value,
      codigoBarras:        document.getElementById("pf-codigo-barras").value.trim(),
      notasInternas:       document.getElementById("pf-notas-internas").value.trim(),
      politicaFacturacion: document.getElementById("pf-politica-facturacion").value,
      tipoProducto:        tipoChecked ? tipoChecked.value : "bienes",
      taxVenta:            taxVenta.slice(),
      taxCompra:           taxCompra.slice(),
      /* ventas */
      productosOpcionales: document.getElementById("pf-productos-opcionales").value.trim(),
      accesorios:          document.getElementById("pf-accesorios").value.trim(),
      productosAlternos:   document.getElementById("pf-productos-alternos").value.trim(),
      descCotizacion:      document.getElementById("pf-desc-cotizacion").value.trim(),
      ecomEtiquetas:       document.getElementById("pf-ecom-etiquetas").value.trim(),
      ecomPublicado:       document.getElementById("pf-ecom-publicado").checked,
      ecomCategorias:      document.getElementById("pf-ecom-categorias").value.trim(),
      descEcom:            document.getElementById("pf-desc-ecom").value.trim(),
      publishMode:         document.getElementById("pf-publish-mode").value,
      publishAt:           document.getElementById("pf-publish-at").value,
      mediaFiles:          mediaFiles.slice(),
      /* características */
      nuevo:               document.getElementById("pf-nuevo").checked,
      descCorta:           document.getElementById("pf-desc-corta").value.trim(),
      descLarga:           document.getElementById("pf-desc-larga").value.trim(),
      /* detalles del artículo */
      mostrarDetalles:     document.getElementById("pf-mostrar-detalles").checked,
      detallesHtml:        document.getElementById("pf-detalles-editor").innerHTML,
      /* especificaciones */
      mostrarEspecificaciones: document.getElementById("pf-mostrar-especificaciones").checked,
      especificacionesHtml:    document.getElementById("pf-especificaciones-editor").innerHTML,
      /* condiciones especiales */
      mostrarCondiciones:  document.getElementById("pf-mostrar-condiciones").checked,
      condicionesHtml:     document.getElementById("pf-condiciones-editor").innerHTML,
      categoria:           document.getElementById("pf-categoria").value,
      publicado:           isScheduledPublished(
                              document.getElementById("pf-publish-mode").value,
                              document.getElementById("pf-publish-at").value
                            ),
      imagen:              photoDataUrl || _safeImagen(editIndex >= 0 ? (allProducts[editIndex].imagen || "") : ""),
      galleryImages:       galleryImages.filter(function(src) {
                             return src && (src.startsWith("data:") || src.startsWith("/") || src.startsWith("http"));
                           }),
    };

    if (editIndex>=0) {
      prod._id    = allProducts[editIndex]._id;
      prod._star  = allProducts[editIndex]._star;
      allProducts[editIndex] = prod;
    } else {
      prod._id = "p" + Date.now();
      allProducts.push(prod);
    }
    try {
      await saveAll();
      await showList();
    } catch (error) {
      alert(error && error.message ? error.message : "No se pudo guardar el producto.");
    }
  }

  /* eventos form */
  document.getElementById("pf-guardar-btn").addEventListener("click", saveForm);
  document.getElementById("pf-descartar-btn").addEventListener("click", function () { showList(); });
  document.getElementById("pf-breadcrumb-back").addEventListener("click", function () { showList(); });

  document.getElementById("pf-publish-mode").addEventListener("change", function () {
    isPublicado = isScheduledPublished(this.value, document.getElementById("pf-publish-at").value);
    updatePublishHelp(this.value, document.getElementById("pf-publish-at").value);
    syncPublicar();
  });
  document.getElementById("pf-publish-at").addEventListener("change", function () {
    var mode = document.getElementById("pf-publish-mode").value;
    isPublicado = isScheduledPublished(mode, this.value);
    updatePublishHelp(mode, this.value);
    syncPublicar();
  });

  /* actualiza breadcrumb dinámicamente con el nombre */
  document.getElementById("pf-nombre").addEventListener("input", function(){
    document.getElementById("pf-breadcrumb-nombre").textContent = this.value.trim() || "Nuevo";
  });

  /* foto */
  document.getElementById("pf-photo-box").addEventListener("click",function(){
    document.getElementById("pf-photo-input").click();
  });
  document.getElementById("pf-photo-change-btn").addEventListener("click",function(){
    document.getElementById("pf-photo-input").click();
  });
  document.getElementById("pf-photo-remove-btn").addEventListener("click",function(){
    photoDataUrl = DEFAULT_PHOTO;
    document.getElementById("pf-photo-preview").src = DEFAULT_PHOTO;
  });
  document.getElementById("pf-photo-input").addEventListener("change",async function(){
    var f = this.files[0]; if (!f) return;
    try {
      var url = await readFileAsDataUrl(f);
      photoDataUrl = url;
      document.getElementById("pf-photo-preview").src = url;
    } catch (error) {
      alert(error && error.message ? error.message : "No se pudo cargar la imagen.");
    } finally {
      this.value = "";
    }
  });
  document.getElementById("pf-gallery-add-btn").addEventListener("click", function () {
    document.getElementById("pf-gallery-input").click();
  });
  document.getElementById("pf-gallery-input").addEventListener("change", async function () {
    try {
      var files = Array.from(this.files || []);
      for (var i = 0; i < files.length; i += 1) {
        galleryImages.push(await readFileAsDataUrl(files[i]));
      }
      renderGallery();
    } catch (error) {
      alert(error && error.message ? error.message : "No se pudieron cargar las fotos.");
    } finally {
      this.value = "";
    }
  });
  document.getElementById("pf-gallery-list").addEventListener("click", function (event) {
    var removeBtn = event.target.closest("[data-gallery-remove]");
    if (removeBtn) {
      galleryImages.splice(Number(removeBtn.getAttribute("data-gallery-remove")), 1);
      renderGallery();
      return;
    }
    var mainBtn = event.target.closest("[data-gallery-main]");
    if (mainBtn) {
      var index = Number(mainBtn.getAttribute("data-gallery-main"));
      var selected = galleryImages[index];
      if (!selected) return;
      var currentMain = document.getElementById("pf-photo-preview").src || DEFAULT_PHOTO;
      photoDataUrl = selected;
      document.getElementById("pf-photo-preview").src = selected;
      galleryImages.splice(index, 1);
      if (currentMain && currentMain !== DEFAULT_PHOTO) {
        galleryImages.unshift(currentMain);
      }
      renderGallery();
    }
  });

  /* ── Impuestos (tag input) ── */
  var taxVenta  = [];
  var taxCompra = [];

  function renderTaxTags(tagsEl, inputEl, taxArr, calcEl) {
    tagsEl.innerHTML = "";
    taxArr.forEach(function(t, i) {
      var span = document.createElement("span");
      span.className = "pf-tax-tag";
      span.innerHTML = t + '% <button class="pf-tax-remove" data-ti="' + i + '" type="button">×</button>';
      tagsEl.appendChild(span);
    });
    if (calcEl) updateTaxCalc(calcEl, taxArr);
    tagsEl.querySelectorAll(".pf-tax-remove").forEach(function(btn) {
      btn.addEventListener("click", function() {
        taxArr.splice(Number(btn.dataset.ti), 1);
        renderTaxTags(tagsEl, inputEl, taxArr, calcEl);
      });
    });
  }

  function updateTaxCalc(calcEl, taxArr) {
    var precio = parseFloat(document.getElementById("pf-precio").value) || 0;
    if (!precio || !taxArr.length) { calcEl.textContent = ""; return; }
    var total = taxArr.reduce(function(acc, t) { return acc + precio * (parseFloat(t) / 100); }, 0);
    calcEl.textContent = "(= $ " + (precio + total).toLocaleString("es-MX", {minimumFractionDigits:2,maximumFractionDigits:2}) + " impuestos incluidos)";
  }

  function setupTaxInput(inputId, tagsId, taxArr, calcId) {
    var input  = document.getElementById(inputId);
    var tags   = document.getElementById(tagsId);
    var calcEl = calcId ? document.getElementById(calcId) : null;
    input.addEventListener("keydown", function(e) {
      if (e.key === "Enter" || e.key === "Tab" || e.key === ",") {
        e.preventDefault();
        var val = parseFloat(input.value.replace(/[^0-9.]/g,""));
        if (!isNaN(val) && val > 0 && val <= 100) {
          taxArr.push(val);
          input.value = "";
          renderTaxTags(tags, input, taxArr, calcEl);
        }
      }
    });
    /* click en el wrap enfoca el input */
    input.closest(".pf-tax-wrap").addEventListener("click", function() { input.focus(); });
  }

  setupTaxInput("pf-tax-venta-input",  "pf-tax-venta-tags",  taxVenta,  "pf-tax-venta-calc");
  setupTaxInput("pf-tax-compra-input", "pf-tax-compra-tags", taxCompra, null);

  /* recalcular cuando cambia el precio */
  document.getElementById("pf-precio").addEventListener("input", function() {
    updateTaxCalc(document.getElementById("pf-tax-venta-calc"), taxVenta);
  });

  /* ── Política de facturación — hint dinámico ── */
  var politicaHints = {
    "cantidad_ordenada":  "Puede facturar los bienes antes de entregarlos.",
    "cantidad_entregada": "Solo puede facturar después de registrar la entrega.",
    "anticipo":           "Se factura un anticipo al confirmar el pedido."
  };
  document.getElementById("pf-politica-facturacion").addEventListener("change", function() {
    document.getElementById("pf-politica-hint").textContent = politicaHints[this.value] || "";
  });

  /* ── Tipo de producto — ajusta opciones de política ── */
  document.querySelectorAll("[name='pf-tipo-producto']").forEach(function(radio) {
    radio.addEventListener("change", function() {
      var pol = document.getElementById("pf-politica-facturacion");
      if (this.value === "servicio") {
        pol.querySelector("[value='cantidad_ordenada']").textContent = "Cantidad ordenada";
        pol.querySelector("[value='cantidad_entregada']").textContent = "Cantidad manual";
      } else {
        pol.querySelector("[value='cantidad_ordenada']").textContent = "Cantidad ordenada";
        pol.querySelector("[value='cantidad_entregada']").textContent = "Cantidad entregada";
      }
      pol.dispatchEvent(new Event("change"));
    });
  });

  /* ── Multimedia (Ventas) ── */
  var mediaFiles = [];   /* { name, url } */

  function renderMedia() {
    var list = document.getElementById("pf-media-list");
    list.innerHTML = "";
    mediaFiles.forEach(function(f, i) {
      var div = document.createElement("div");
      div.className = "pf-media-thumb";
      div.innerHTML = '<img src="' + f.url + '" alt="' + f.name + '" />' +
        '<button class="pf-media-del" data-mi="' + i + '" type="button" title="Quitar">×</button>';
      list.appendChild(div);
    });
    list.querySelectorAll(".pf-media-del").forEach(function(btn) {
      btn.addEventListener("click", function() {
        mediaFiles.splice(Number(btn.dataset.mi), 1);
        renderMedia();
      });
    });
  }

  document.getElementById("pf-media-add-btn").addEventListener("click", function() {
    document.getElementById("pf-media-input").click();
  });
  document.getElementById("pf-media-input").addEventListener("change", async function() {
    try {
      var files = Array.from(this.files || []);
      for (var i = 0; i < files.length; i += 1) {
        mediaFiles.push({ name: files[i].name, url: await readFileAsDataUrl(files[i]) });
      }
      renderMedia();
    } catch (error) {
      alert(error && error.message ? error.message : "No se pudo cargar la multimedia.");
    } finally {
      this.value = "";
    }
  });

  /* ── RTE helpers (shared) ── */
  function setupRteToolbar(toolbarId) {
    var toolbar = document.getElementById(toolbarId);
    toolbar.querySelectorAll(".pf-rte-btn").forEach(function(btn){
      btn.addEventListener("mousedown", function(e){
        e.preventDefault();
        var cmd = btn.dataset.cmd;
        if (cmd === "createLink") {
          var url = prompt("URL del enlace:");
          if (url) document.execCommand("createLink", false, url);
        } else if (cmd === "insertTable") {
          document.execCommand("insertHTML", false,
            '<table style="border-collapse:collapse;width:100%;"><tr>' +
            '<td style="border:1px solid var(--mp-border);padding:6px;">&nbsp;</td>' +
            '<td style="border:1px solid var(--mp-border);padding:6px;">&nbsp;</td>' +
            '</tr></table><p></p>');
        } else if (cmd === "insertCheckbox") {
          document.execCommand("insertHTML", false,
            '<label style="display:flex;align-items:center;gap:6px;">' +
            '<input type="checkbox" /><span>Elemento</span></label>');
        } else {
          document.execCommand(cmd, false, null);
        }
      });
    });
  }
  setupRteToolbar("pf-detalles-toolbar");
  setupRteToolbar("pf-especificaciones-toolbar");
  setupRteToolbar("pf-condiciones-toolbar");

  /* notebook tabs */
  document.querySelectorAll(".pf-nb-tab").forEach(function(tab,i){
    tab.addEventListener("click",function(){
      activateNotebookTab(i + 1);
    });
  });

  document.querySelectorAll("[data-open-product-panel]").forEach(function(btn){
    btn.addEventListener("click", function(){
      openNotebookDrawer(Number(btn.getAttribute("data-open-product-panel")) || 1);
    });
  });
  document.getElementById("pf-notebook-close").addEventListener("click", closeNotebookDrawer);
  document.getElementById("pf-drawer-overlay").addEventListener("click", closeNotebookDrawer);
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeNotebookDrawer();
  });

  /* ════════════════════════════════
     ELIMINACIÓN
  ════════════════════════════════ */
  var pendingDeleteIds = [];   /* ids a eliminar al confirmar */

  function openConfirm(msg, ids) {
    pendingDeleteIds = ids;
    document.getElementById("pv-confirm-msg").textContent = msg;
    document.getElementById("pv-confirm-overlay").hidden = false;
  }

  function closeConfirm() {
    document.getElementById("pv-confirm-overlay").hidden = true;
    pendingDeleteIds = [];
  }

  document.getElementById("pv-confirm-cancel").addEventListener("click", closeConfirm);

  document.getElementById("pv-confirm-ok").addEventListener("click", async function() {
    pendingDeleteIds.forEach(function(id) {
      allProducts = allProducts.filter(function(p) { return p._id !== id; });
      selectedIds.delete(id);
    });
    try {
      await saveAll();
      closeConfirm();
      /* cerrar panel derecho si veníamos del form */
      if (!document.getElementById("pf-view").hidden) {
        closeNotebookDrawer();
        document.getElementById("pf-view").hidden = true;
        var placeholder = document.getElementById("pf-placeholder");
        if (placeholder) placeholder.hidden = false;
      }
      await load();
      applyFilterSort();
    } catch (error) {
      alert(error && error.message ? error.message : "No se pudo eliminar el producto.");
    }
  });

  /* Eliminar seleccionados desde lista */
  var pvEliminarBtn = document.getElementById("pv-eliminar-btn");
  pvEliminarBtn.addEventListener("click", function() {
    if (!selectedIds.size) return;
    var count = selectedIds.size;
    openConfirm(
      count === 1
        ? "¿Eliminar 1 producto? Esta acción no se puede deshacer."
        : "¿Eliminar " + count + " productos? Esta acción no se puede deshacer.",
      Array.from(selectedIds)
    );
  });

  /* Activar/desactivar btn eliminar lista según selección */
  function syncEliminarBtn() {
    pvEliminarBtn.disabled = selectedIds.size === 0;
  }

  /* Eliminar producto actual desde formulario */
  document.getElementById("pf-eliminar-btn").addEventListener("click", function() {
    if (editIndex < 0) return;
    var p = allProducts[editIndex];
    openConfirm(
      "¿Eliminar \"" + (p.nombre || "este producto") + "\"? Esta acción no se puede deshacer.",
      [p._id]
    );
  });

  /* Sobrescribir renderTable para sincronizar btn eliminar */
  var _origRenderTable = renderTable;
  renderTable = function() {
    _origRenderTable();
    syncEliminarBtn();
  };

  /* breadcrumb nombre tienda */
  (function(){
    var n = localStorage.getItem("multitienda_store_name");
    if (n) document.getElementById("pv-breadcrumb-tienda").textContent = n;
  })();

  /* ── init ── */
  (async function init() {
    await load();
    applyFilterSort();
  })();
})();
