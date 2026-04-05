from __future__ import annotations


def productos_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Productos</title>
  <link rel="stylesheet" href="/multitienda/static/css/productos.css" />
</head>
<body>
__BACKEND_SHARED_SIDEBAR_HTML__
<main class="page">
  <div class="productos-shell">
    <section class="productos-shell__list">

  <!-- ══════════ VISTA LISTA ══════════ -->
  <div id="pv-view">
    <div class="pv-toolbar">
      <div class="pv-toolbar-left">
        <button class="btn-nuevo" id="pv-nuevo-btn" type="button">Nuevo</button>
        <button class="btn-eliminar" id="pv-eliminar-btn" type="button" disabled>Eliminar</button>
        <div>
          <div class="pv-breadcrumb">
            <a id="pv-breadcrumb-tiendas">Tiendas</a>
            <span class="pv-breadcrumb-sep">/</span>
            <span id="pv-breadcrumb-tienda">Tu Negocio VALE</span>
          </div>
          <div class="pv-page-title">
            Productos de la tienda
            <button class="gear-btn" type="button" title="Configuración">⚙</button>
          </div>
        </div>
      </div>
      <div class="pv-toolbar-center">
        <div class="pv-search-wrap">
          <span class="pv-search-icon">🔍</span>
          <input class="pv-search-input" id="pv-search" type="text" placeholder="Buscar..." />
          <button class="pv-search-drop" type="button">▾</button>
        </div>
      </div>
      <div class="pv-toolbar-right">
        <span id="pv-pag-label">0 / 0</span>
        <button class="pv-pag-btn" id="pv-prev-btn" type="button" disabled>&#8249;</button>
        <button class="pv-pag-btn" id="pv-next-btn" type="button" disabled>&#8250;</button>
      </div>
    </div>

    <div class="pv-table-wrap">
      <table class="pv-table">
        <thead>
          <tr>
            <th class="col-cb"><input class="cb-input" type="checkbox" id="pv-select-all" title="Seleccionar todo" /></th>
            <th class="col-star"></th>
            <th class="sortable" data-col="nombre">Nombre del producto <span class="sort-arrow">↕</span></th>
            <th class="sortable" data-col="referencia">Referencia interna <span class="sort-arrow">↕</span></th>
            <th>Etiquetas</th>
            <th class="col-num sortable" data-col="precio">Precio de venta <span class="sort-arrow">↕</span></th>
            <th class="col-num sortable" data-col="costo">Costo <span class="sort-arrow">↕</span></th>
            <th class="col-cfg"><button class="col-settings-btn" type="button" title="Columnas">⇌</button></th>
          </tr>
        </thead>
        <tbody id="pv-tbody"></tbody>
      </table>
      <div id="pv-empty" class="pv-empty" hidden>
        No hay productos registrados. Haz clic en <strong>Nuevo</strong> para agregar el primero.
      </div>
    </div>
  </div>
    </section>

    <aside class="productos-shell__form">
      <div class="pf-placeholder" id="pf-placeholder">
        <div class="pf-placeholder__inner">
          <div class="pf-placeholder__icon">+</div>
          <h2 class="pf-placeholder__title">Selecciona o crea un producto</h2>
          <p class="pf-placeholder__copy">Haz clic en una fila de la lista o usa el botón <strong>Nuevo</strong> para abrir el formulario en este panel.</p>
        </div>
      </div>

  <!-- ══════════ VISTA FORM ══════════ -->
  <div id="pf-view" hidden>

    <!-- Toolbar form -->
    <div class="pv-toolbar">
      <div class="pv-toolbar-left">
        <button class="btn-guardar" id="pf-guardar-btn" type="button">Guardar</button>
        <button class="btn-descartar" id="pf-descartar-btn" type="button">Descartar</button>
        <button class="btn-eliminar" id="pf-eliminar-btn" type="button" style="display:none">Eliminar</button>
        <div>
          <div class="pv-breadcrumb">
            <a id="pf-breadcrumb-back">Productos</a>
            <span class="pv-breadcrumb-sep">/</span>
            <span id="pf-breadcrumb-nombre">Nuevo</span>
          </div>
          <div class="pv-page-title">Producto</div>
        </div>
      </div>
      <div class="pv-toolbar-right">
        <button class="btn-publicar" id="pf-publicar-btn" type="button">Sin publicar</button>
      </div>
    </div>

    <!-- Cuerpo del form -->
    <div class="pf-body">

      <!-- Columna principal -->
      <div class="pf-main-col">
        <!-- Nombre -->
        <div class="pf-nombre-wrap">
          <input class="pf-nombre-input" id="pf-nombre" type="text" placeholder="Nombre del producto" />
        </div>
        <div class="pf-publish-card">
          <div class="pf-publish-field">
            <p class="pf-publish-label">Programar publicación</p>
            <div class="pf-publish-inline">
              <select class="pf-input" id="pf-publish-mode">
                <option value="immediate">Inmediato</option>
                <option value="scheduled">Fecha y hora</option>
              </select>
              <input class="pf-input" id="pf-publish-at" type="datetime-local" />
            </div>
            <p class="pf-publish-help" id="pf-publish-help">El producto se publica de inmediato al guardar.</p>
          </div>
          <div class="pf-publish-field">
            <p class="pf-publish-label">Publicado</p>
            <button class="btn-publicar" id="pf-publicar-btn-card" type="button" disabled>Sin publicar</button>
          </div>
        </div>

        <div class="pf-photo-col">
          <div class="pf-photo-box" id="pf-photo-box" title="Haz clic para cambiar la foto">
            <img id="pf-photo-preview" src="/multitienda/static/imagenes/logo_vale.png" alt="Foto del producto" />
          </div>
          <div class="pf-photo-meta">
            <p class="pf-photo-hint">Fotografía principal del producto. Haz clic para subir, cambiar o quitar la imagen y agrega fotos adicionales para la galería.</p>
            <div class="pf-photo-actions">
              <button class="pf-photo-btn" id="pf-photo-change-btn" type="button">Cambiar</button>
              <button class="pf-photo-btn" id="pf-photo-remove-btn" type="button">Quitar</button>
            </div>
            <input type="file" id="pf-photo-input" accept="image/*" style="display:none" />
            <div class="pf-gallery">
              <div class="pf-gallery-head">
                <p class="pf-gallery-title">Fotos adicionales</p>
                <button class="pf-gallery-add-btn" id="pf-gallery-add-btn" type="button">Agregar fotos</button>
              </div>
              <div class="pf-gallery-list" id="pf-gallery-list"></div>
              <p class="pf-gallery-empty" id="pf-gallery-empty">Aún no hay fotos adicionales.</p>
            </div>
            <input type="file" id="pf-gallery-input" accept="image/*" multiple style="display:none" />
            <input type="hidden" id="pf-stock" value="" />
            <input type="hidden" id="pf-stock-min" value="" />
          </div>
        </div>

        <div class="pf-section-card">
          <div class="pf-section-card__head">
            <div>
              <p class="pf-section-card__eyebrow">Secciones del producto</p>
              <h3 class="pf-section-card__title">Configura cada bloque en panel lateral</h3>
            </div>
          </div>
          <div class="pf-section-launchers">
            <button class="pf-section-launcher" data-open-product-panel="1" type="button">
              <strong>Información general</strong>
              <span>Precio, categoría, impuestos y datos base.</span>
            </button>
            <button class="pf-section-launcher" data-open-product-panel="2" type="button">
              <strong>Ventas</strong>
              <span>Comercio electrónico, multimedia y descripción de venta.</span>
            </button>
            <button class="pf-section-launcher" data-open-product-panel="3" type="button">
              <strong>Características</strong>
              <span>Descripción corta, larga y atributos visibles.</span>
            </button>
            <button class="pf-section-launcher" data-open-product-panel="4" type="button">
              <strong>Detalles del artículo</strong>
              <span>Contenido enriquecido y visibilidad en la web.</span>
            </button>
            <button class="pf-section-launcher" data-open-product-panel="5" type="button">
              <strong>Especificaciones</strong>
              <span>Ficha técnica y datos complementarios del producto.</span>
            </button>
            <button class="pf-section-launcher" data-open-product-panel="6" type="button">
              <strong>Condiciones especiales</strong>
              <span>Garantías, restricciones y políticas del artículo.</span>
            </button>
          </div>
        </div>

        <div class="pf-drawer-overlay" id="pf-drawer-overlay" hidden></div>

        <!-- Notebook drawer -->
        <div class="pf-notebook">
          <div class="pf-notebook-head">
            <div>
              <p class="pf-notebook-eyebrow">Configuración</p>
              <h3 class="pf-notebook-title">Editor de secciones del producto</h3>
            </div>
            <button class="pf-notebook-close" id="pf-notebook-close" type="button" aria-label="Cerrar panel">✕</button>
          </div>
          <div class="pf-notebook-tabs" role="tablist">
            <button class="pf-nb-tab active" role="tab" aria-selected="true"
                    aria-controls="pf-panel-1" id="pf-tab-1" type="button">Información general</button>
            <button class="pf-nb-tab" role="tab" aria-selected="false"
                    aria-controls="pf-panel-2" id="pf-tab-2" type="button">Ventas</button>
            <button class="pf-nb-tab" role="tab" aria-selected="false"
                    aria-controls="pf-panel-3" id="pf-tab-3" type="button">Características del producto</button>
            <button class="pf-nb-tab" role="tab" aria-selected="false"
                    aria-controls="pf-panel-4" id="pf-tab-4" type="button">Detalles del artículo</button>
            <button class="pf-nb-tab" role="tab" aria-selected="false"
                    aria-controls="pf-panel-5" id="pf-tab-5" type="button">Especificaciones</button>
            <button class="pf-nb-tab" role="tab" aria-selected="false"
                    aria-controls="pf-panel-6" id="pf-tab-6" type="button">Condiciones especiales</button>
          </div>

          <!-- ── Información general ── -->
          <div class="pf-nb-panel" id="pf-panel-1" role="tabpanel" aria-labelledby="pf-tab-1">

            <!-- Grid dos columnas estilo Odoo -->
            <div class="pf-ig-grid">

              <!-- ── Columna izquierda ── -->
              <div class="pf-ig-col">

                <div class="pf-ig-row">
                  <label class="pf-ig-label">Tipo de producto <span class="pf-hint" title="Determina cómo se gestiona el inventario">?</span></label>
                  <div class="pf-ig-val pf-radio-group">
                    <label class="pf-radio-label">
                      <input type="radio" name="pf-tipo-producto" value="bienes" id="pf-tipo-bienes" checked class="pf-radio" />
                      Bienes
                    </label>
                    <label class="pf-radio-label">
                      <input type="radio" name="pf-tipo-producto" value="servicio" id="pf-tipo-servicio" class="pf-radio" />
                      Servicio
                    </label>
                    <label class="pf-radio-label">
                      <input type="radio" name="pf-tipo-producto" value="combo" id="pf-tipo-combo" class="pf-radio" />
                      Combo
                    </label>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-politica-facturacion">Política de facturación <span class="pf-hint" title="Define cuándo se factura este producto">?</span></label>
                  <div class="pf-ig-val">
                    <select class="pf-input" id="pf-politica-facturacion">
                      <option value="cantidad_ordenada">Cantidad ordenada</option>
                      <option value="cantidad_entregada">Cantidad entregada</option>
                      <option value="anticipo">Anticipo</option>
                    </select>
                    <p class="pf-ig-hint" id="pf-politica-hint">Puede facturar los bienes antes de entregarlos.</p>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-unidad">Unidad de medida</label>
                  <div class="pf-ig-val">
                    <select class="pf-input" id="pf-unidad">
                      <option value="pieza">Pieza</option>
                      <option value="kg">Kilogramo</option>
                      <option value="litro">Litro</option>
                      <option value="metro">Metro</option>
                      <option value="caja">Caja</option>
                      <option value="par">Par</option>
                    </select>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-etiquetas">Etiquetas</label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-etiquetas" type="text" placeholder="Ej. nuevo, oferta, temporada" />
                  </div>
                </div>

              </div><!-- /col izq -->

              <!-- ── Columna derecha ── -->
              <div class="pf-ig-col">

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-precio">Precio de venta <span class="pf-hint" title="Precio al público">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input pf-money-input" id="pf-precio" type="number" min="0" step="0.01" placeholder="0.00" />
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label">Impuesto de ventas <span class="pf-hint" title="Impuestos aplicados al precio de venta">?</span></label>
                  <div class="pf-ig-val">
                    <div class="pf-tax-wrap" id="pf-tax-venta-wrap" data-key="taxVenta">
                      <div class="pf-tax-tags" id="pf-tax-venta-tags"></div>
                      <input class="pf-tax-input" id="pf-tax-venta-input" type="text" placeholder="Agregar %" />
                    </div>
                    <p class="pf-tax-calc" id="pf-tax-venta-calc"></p>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-costo">Costo <span class="pf-hint" title="Costo de adquisición del producto">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input pf-money-input" id="pf-costo" type="number" min="0" step="0.01" placeholder="0.00" />
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label">Impuestos de compra <span class="pf-hint" title="Impuestos aplicados al costo de compra">?</span></label>
                  <div class="pf-ig-val">
                    <div class="pf-tax-wrap" id="pf-tax-compra-wrap" data-key="taxCompra">
                      <div class="pf-tax-tags" id="pf-tax-compra-tags"></div>
                      <input class="pf-tax-input" id="pf-tax-compra-input" type="text" placeholder="Agregar %" />
                    </div>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-categoria">Categoría</label>
                  <div class="pf-ig-val">
                    <select class="pf-input" id="pf-categoria">
                      <option value="">Sin categoría</option>
                    </select>
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-referencia">Referencia</label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-referencia" type="text" placeholder="" />
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-codigo-barras">Código de barras</label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-codigo-barras" type="text" placeholder="" />
                  </div>
                </div>

              </div><!-- /col der -->
            </div><!-- /pf-ig-grid -->

            <!-- NOTAS INTERNAS -->
            <div class="pf-notas-section">
              <p class="pf-notas-title">NOTAS INTERNAS</p>
              <textarea class="pf-notas-textarea" id="pf-notas-internas" placeholder="Esta nota es solo para fines internos."></textarea>
            </div>

          </div><!-- /pf-panel-1 -->

          <!-- ── Ventas ── -->
          <div class="pf-nb-panel" id="pf-panel-2" role="tabpanel" aria-labelledby="pf-tab-2" hidden>
            <div class="pf-ventas-grid">

              <!-- ── Columna izquierda ── -->
              <div>

                <p class="pf-ventas-section-title">VENTAS ADICIONALES Y VENTAS CRUZADAS</p>
                <div class="pf-ventas-divider"></div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-productos-opcionales">Productos opcionales <span class="pf-hint" title="Se recomiendan al hacer clic en 'Agregar al carrito' o al cotizar">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-productos-opcionales" type="text"
                           placeholder="Recomendar al "Agregar al carrito" o a la cotización…" />
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-accesorios">Accesorios <span class="pf-hint" title="Accesorios sugeridos en el carrito de comercio electrónico">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-accesorios" type="text"
                           placeholder="Accesorios sugeridos en el carrito de comercio electrónico…" />
                  </div>
                </div>

                <div class="pf-ig-row" style="border-bottom:none;">
                  <label class="pf-ig-label" for="pf-productos-alternos">Productos alternos <span class="pf-hint" title="Aparecen en la parte inferior de las páginas del producto">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-productos-alternos" type="text"
                           placeholder="Aparecen en la parte inferior de las páginas del producto…" />
                  </div>
                </div>

                <p class="pf-ventas-section-title" style="margin-top:28px;">MEDIOS DE COMERCIO ELECTRÓNICO</p>
                <div class="pf-ventas-divider"></div>

                <div class="pf-media-area">
                  <div class="pf-media-list" id="pf-media-list"></div>
                  <button class="pf-media-add-btn" id="pf-media-add-btn" type="button">Agregar archivo multimedia</button>
                  <input type="file" id="pf-media-input" accept="image/*,video/*,.pdf" multiple style="display:none" />
                </div>

                <p class="pf-ventas-section-title" style="margin-top:28px;">DESCRIPCIÓN DE LA COTIZACIÓN</p>
                <div class="pf-ventas-divider"></div>
                <textarea class="pf-input pf-ventas-desc" id="pf-desc-cotizacion"
                          placeholder="Esta nota se agrega a las órdenes de ventas y facturas."></textarea>

              </div>

              <!-- ── Columna derecha ── -->
              <div>

                <p class="pf-ventas-section-title">TIENDA DE COMERCIO ELECTRÓNICO</p>
                <div class="pf-ventas-divider"></div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-ecom-etiquetas">Etiquetas</label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-ecom-etiquetas" type="text" placeholder="" />
                  </div>
                </div>

                <div class="pf-ig-row">
                  <label class="pf-ig-label" for="pf-ecom-publicado">Está publicado</label>
                  <div class="pf-ig-val" style="padding-top:7px;">
                    <input type="checkbox" id="pf-ecom-publicado" class="cb-input" />
                  </div>
                </div>

                <div class="pf-ig-row" style="border-bottom:none;">
                  <label class="pf-ig-label" for="pf-ecom-categorias">Categorías <span class="pf-hint" title="Categorías visibles en la tienda en línea">?</span></label>
                  <div class="pf-ig-val">
                    <input class="pf-input" id="pf-ecom-categorias" type="text" placeholder="" />
                  </div>
                </div>

                <p class="pf-ventas-section-title" style="margin-top:28px;">DESCRIPCIÓN DE COMERCIO ELECTRÓNICO</p>
                <div class="pf-ventas-divider"></div>
                <textarea class="pf-input pf-ventas-desc" id="pf-desc-ecom"
                          placeholder="Una descripción detallada y con formato para promocionar su producto en la tienda en línea."></textarea>

              </div>

            </div>
          </div><!-- /pf-panel-2 -->

          <!-- ── Características del producto ── -->
          <div class="pf-nb-panel" id="pf-panel-3" role="tabpanel" aria-labelledby="pf-tab-3" hidden>

            <div class="pf-ig-row">
              <label class="pf-ig-label" for="pf-nuevo">Nuevo</label>
              <div class="pf-ig-val" style="padding-top:7px;">
                <input type="checkbox" id="pf-nuevo" class="cb-input" />
              </div>
            </div>

            <div class="pf-ig-row">
              <label class="pf-ig-label" for="pf-desc-corta">Descripción corta</label>
              <div class="pf-ig-val">
                <input class="pf-input" id="pf-desc-corta" type="text" placeholder="" />
              </div>
            </div>

            <div class="pf-ig-row" style="border-bottom:none;align-items:start;">
              <label class="pf-ig-label" for="pf-desc-larga" style="padding-top:7px;">Descripción larga</label>
              <div class="pf-ig-val">
                <textarea class="pf-input" id="pf-desc-larga" rows="5"
                          style="resize:vertical;font-family:inherit;" placeholder=""></textarea>
              </div>
            </div>

          </div><!-- /pf-panel-3 -->

          <!-- ── Detalles del artículo ── -->
          <div class="pf-nb-panel" id="pf-panel-4" role="tabpanel" aria-labelledby="pf-tab-4" hidden>

            <div class="pf-ig-row">
              <label class="pf-ig-label" for="pf-mostrar-detalles">
                Mostrar pestaña Detalles del artículo en la web
                <span class="pf-hint" title="Muestra u oculta esta sección en la página del producto en la tienda">?</span>
              </label>
              <div class="pf-ig-val" style="padding-top:6px;">
                <label class="pf-toggle">
                  <input type="checkbox" id="pf-mostrar-detalles" checked />
                  <span class="pf-toggle-track"><span class="pf-toggle-thumb"></span></span>
                </label>
              </div>
            </div>

            <div class="pf-ig-row" style="border-bottom:none;align-items:start;">
              <label class="pf-ig-label" style="padding-top:10px;">
                Detalles del producto (producto)
                <span class="pf-hint" title="Descripción enriquecida visible en la ficha del producto">?</span>
              </label>
              <div class="pf-ig-val" style="flex:1;">
                <div class="pf-rte-wrap" id="pf-detalles-rte-wrap">
                  <div class="pf-rte-toolbar" id="pf-detalles-toolbar">
                    <button type="button" class="pf-rte-btn" data-cmd="insertTable"   title="Tabla">⊞</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertUnorderedList" title="Lista">≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertOrderedList"   title="Lista numerada"><span style="font-size:.7rem;font-weight:700;">1.</span>≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertCheckbox" title="Casilla">☑</button>
                    <button type="button" class="pf-rte-btn" data-cmd="createLink"    title="Enlace">⛓</button>
                    <button type="button" class="pf-rte-btn" data-cmd="bold"          title="Negrita" style="font-weight:700;">B</button>
                    <button type="button" class="pf-rte-btn" data-cmd="italic"        title="Cursiva" style="font-style:italic;">I</button>
                    <button type="button" class="pf-rte-btn" data-cmd="removeFormat"  title="Limpiar formato" style="color:var(--mp-muted);">✕</button>
                  </div>
                  <div class="pf-rte-editor" id="pf-detalles-editor"
                       contenteditable="true"
                       data-placeholder='Escriba "/" para acceder a los comandos'></div>
                </div>
              </div>
            </div>

          </div><!-- /pf-panel-4 -->

          <!-- ── Especificaciones ── -->
          <div class="pf-nb-panel" id="pf-panel-5" role="tabpanel" aria-labelledby="pf-tab-5" hidden>

            <div class="pf-ig-row">
              <label class="pf-ig-label" for="pf-mostrar-especificaciones">
                Mostrar pestaña Especificaciones en la web
                <span class="pf-hint" title="Muestra u oculta esta sección en la página del producto en la tienda">?</span>
              </label>
              <div class="pf-ig-val" style="padding-top:6px;">
                <label class="pf-toggle">
                  <input type="checkbox" id="pf-mostrar-especificaciones" checked />
                  <span class="pf-toggle-track"><span class="pf-toggle-thumb"></span></span>
                </label>
              </div>
            </div>

            <div class="pf-ig-row" style="border-bottom:none;align-items:start;">
              <label class="pf-ig-label" style="padding-top:10px;">
                Especificaciones del producto (producto)
                <span class="pf-hint" title="Especificaciones técnicas visibles en la ficha del producto">?</span>
              </label>
              <div class="pf-ig-val" style="flex:1;">
                <div class="pf-rte-wrap" id="pf-especificaciones-rte-wrap">
                  <div class="pf-rte-toolbar" id="pf-especificaciones-toolbar">
                    <button type="button" class="pf-rte-btn" data-cmd="insertTable"   title="Tabla">⊞</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertUnorderedList" title="Lista">≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertOrderedList"   title="Lista numerada"><span style="font-size:.7rem;font-weight:700;">1.</span>≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertCheckbox" title="Casilla">☑</button>
                    <button type="button" class="pf-rte-btn" data-cmd="createLink"    title="Enlace">⛓</button>
                    <button type="button" class="pf-rte-btn" data-cmd="bold"          title="Negrita" style="font-weight:700;">B</button>
                    <button type="button" class="pf-rte-btn" data-cmd="italic"        title="Cursiva" style="font-style:italic;">I</button>
                    <button type="button" class="pf-rte-btn" data-cmd="removeFormat"  title="Limpiar formato" style="color:var(--mp-muted);">✕</button>
                  </div>
                  <div class="pf-rte-editor" id="pf-especificaciones-editor"
                       contenteditable="true"
                       data-placeholder='Escriba "/" para acceder a los comandos'></div>
                </div>
              </div>
            </div>

          </div><!-- /pf-panel-5 -->

          <!-- ── Condiciones especiales ── -->
          <div class="pf-nb-panel" id="pf-panel-6" role="tabpanel" aria-labelledby="pf-tab-6" hidden>

            <div class="pf-ig-row">
              <label class="pf-ig-label" for="pf-mostrar-condiciones">
                Mostrar pestaña Condiciones especiales en la web
                <span class="pf-hint" title="Muestra u oculta esta sección en la página del producto en la tienda">?</span>
              </label>
              <div class="pf-ig-val" style="padding-top:6px;">
                <label class="pf-toggle">
                  <input type="checkbox" id="pf-mostrar-condiciones" checked />
                  <span class="pf-toggle-track"><span class="pf-toggle-thumb"></span></span>
                </label>
              </div>
            </div>

            <div class="pf-ig-row" style="border-bottom:none;align-items:start;">
              <label class="pf-ig-label" style="padding-top:10px;">
                Condiciones especiales (producto)
                <span class="pf-hint" title="Garantías, restricciones o condiciones de venta visibles en la ficha del producto">?</span>
              </label>
              <div class="pf-ig-val" style="flex:1;">
                <div class="pf-rte-wrap" id="pf-condiciones-rte-wrap">
                  <div class="pf-rte-toolbar" id="pf-condiciones-toolbar">
                    <button type="button" class="pf-rte-btn" data-cmd="insertTable"   title="Tabla">⊞</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertUnorderedList" title="Lista">≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertOrderedList"   title="Lista numerada"><span style="font-size:.7rem;font-weight:700;">1.</span>≡</button>
                    <button type="button" class="pf-rte-btn" data-cmd="insertCheckbox" title="Casilla">☑</button>
                    <button type="button" class="pf-rte-btn" data-cmd="createLink"    title="Enlace">⛓</button>
                    <button type="button" class="pf-rte-btn" data-cmd="bold"          title="Negrita" style="font-weight:700;">B</button>
                    <button type="button" class="pf-rte-btn" data-cmd="italic"        title="Cursiva" style="font-style:italic;">I</button>
                    <button type="button" class="pf-rte-btn" data-cmd="removeFormat"  title="Limpiar formato" style="color:var(--mp-muted);">✕</button>
                  </div>
                  <div class="pf-rte-editor" id="pf-condiciones-editor"
                       contenteditable="true"
                       data-placeholder='Escriba "/" para acceder a los comandos'></div>
                </div>
              </div>
            </div>

          </div><!-- /pf-panel-6 -->

        </div><!-- /pf-notebook -->
      </div><!-- /columna principal -->

    </div><!-- /pf-body -->
  </div><!-- /pf-view -->
    </aside>
  </div>

  <!-- Diálogo de confirmación eliminación -->
  <div class="pv-confirm-overlay" id="pv-confirm-overlay" hidden>
    <div class="pv-confirm-card">
      <h3 class="pv-confirm-title">&#9888; Eliminar producto(s)</h3>
      <p class="pv-confirm-msg" id="pv-confirm-msg">¿Confirmar eliminación?</p>
      <div class="pv-confirm-actions">
        <button class="btn-descartar" id="pv-confirm-cancel" type="button">Cancelar</button>
        <button class="btn-eliminar" id="pv-confirm-ok" type="button">Eliminar</button>
      </div>
    </div>
  </div>

</main>
<script src="/multitienda/static/js/backend-sidebar-core.js"></script>
<script>
  (function () {
    if (window.initBackendSidebarCore) window.initBackendSidebarCore();
  })();
</script>
<script src="/multitienda/static/js/backend-navbar.js"></script>
<script src="/multitienda/static/js/multitienda-productos.js"></script>
</body>
</html>"""
