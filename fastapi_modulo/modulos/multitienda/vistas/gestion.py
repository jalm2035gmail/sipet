from __future__ import annotations


def gestion_html() -> str:
    return _HTML


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" type="image/png" href="/multitienda/static/imagenes/tu-negocio.png" />
  <link rel="stylesheet" href="/multitienda/static/css/backend-master-detail.css" />
  <title>Administrar tiendas</title>
  <link rel="stylesheet" href="/multitienda/static/css/gestion.css" />
</head>
<body>
__BACKEND_SHARED_SIDEBAR_HTML__

  <main class="page">
    <h1 class="title">Administrar tiendas</h1>
    <p class="subtitle">Dar de alta tiendas con sus permisos y roles</p>

    <div class="notebook config-workspace backend-master-detail js-backend-master-detail">
      <aside class="config-nav backend-master-detail__nav">
        <p class="config-nav-title backend-master-detail__nav-title">Configuración</p>
        <div class="notebook-tabs backend-master-detail__tabs" role="tablist" aria-orientation="vertical">
          <button class="notebook-tab backend-master-detail__tab active" role="tab" aria-selected="true" aria-controls="tab-panel-1" id="tab-1" type="button">
            <span class="config-tab-title backend-master-detail__tab-title">Tiendas</span>
            <span class="config-tab-copy backend-master-detail__tab-copy">Alta, edición y asignación del administrador.</span>
          </button>
          <button class="notebook-tab backend-master-detail__tab" role="tab" aria-selected="false" aria-controls="tab-panel-2" id="tab-2" type="button">
            <span class="config-tab-title backend-master-detail__tab-title">Acceso a AVAN</span>
            <span class="config-tab-copy backend-master-detail__tab-copy">Permisos y capacidades habilitadas para la tienda.</span>
          </button>
          <button class="notebook-tab backend-master-detail__tab" role="tab" aria-selected="false" aria-controls="tab-panel-3" id="tab-3" type="button">
            <span class="config-tab-title backend-master-detail__tab-title">Publicidad</span>
            <span class="config-tab-copy backend-master-detail__tab-copy">Campañas visuales, ventanas emergentes y destacados.</span>
          </button>
          <button class="notebook-tab backend-master-detail__tab" role="tab" aria-selected="false" aria-controls="tab-panel-4" id="tab-4" type="button">
            <span class="config-tab-title backend-master-detail__tab-title">Institución financiera</span>
            <span class="config-tab-copy backend-master-detail__tab-copy">Datos bancarios o cooperativos ligados a la tienda.</span>
          </button>
          <button class="notebook-tab backend-master-detail__tab" role="tab" aria-selected="false" aria-controls="tab-panel-5" id="tab-5" type="button">
            <span class="config-tab-title backend-master-detail__tab-title">Categorías</span>
            <span class="config-tab-copy backend-master-detail__tab-copy">Estructura del catálogo y su imagen representativa.</span>
          </button>
          <button class="notebook-tab backend-master-detail__tab" role="tab" aria-selected="false" aria-controls="tab-panel-6" id="tab-6" type="button">
            <span class="config-tab-title backend-master-detail__tab-title">Atributos</span>
            <span class="config-tab-copy backend-master-detail__tab-copy">Variantes como color, talla, material o imagen.</span>
          </button>
        </div>
      </aside>

      <div class="config-content backend-master-detail__content">
      <div class="notebook-panel backend-master-detail__panel" id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1">
        <div id="store-list-view">
          <div class="store-toolbar">
            <h2 style="margin:0;">Tiendas registradas</h2>
            <button class="action-btn" id="store-new-btn" type="button" onclick="if(window.multitiendaShowStoreForm){window.multitiendaShowStoreForm(-1);}else{var list=document.getElementById('store-list-view');var form=document.getElementById('store-form-view');var title=document.getElementById('store-form-title');if(list){list.hidden=true;}if(form){form.hidden=false;}if(title){title.textContent='Nueva tienda';}}">+ Nueva tienda</button>
          </div>
          <p class="store-table-note">Consulta todas las tiendas registradas y abre cualquiera para editarla.</p>
          <table class="data-table" id="store-table">
            <thead>
              <tr>
                <th>Tienda</th>
                <th>Giro</th>
                <th>Administrador</th>
                <th>Membresía</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody id="store-tbody">
              <tr id="store-empty-row" class="empty-row">
                <td colspan="5" style="text-align:center;color:var(--mt-muted);padding:32px;">
                  No hay tiendas registradas. Haz clic en <strong>+ Nueva tienda</strong> para agregar la primera.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div id="store-form-view" hidden>
          <div class="panel-header-row">
            <h2 id="store-form-title">Nueva tienda</h2>
            <button class="action-btn action-btn--secondary" id="store-cancel-btn" type="button" onclick="if(window.multitiendaShowStoreList){window.multitiendaShowStoreList();}else{var list=document.getElementById('store-list-view');var form=document.getElementById('store-form-view');if(list){list.hidden=false;}if(form){form.hidden=true;}}">← Volver a lista</button>
          </div>
          <section class="section">
            <h2>Datos generales</h2>
            <div class="section-grid">
              <div>
                <div class="field">
                  <label for="store-name">Nombre de la tienda</label>
                  <input class="field-input" id="store-name" type="text" placeholder="Ej. Tu Negocio" />
                </div>
                <div class="field">
                  <label for="store-type">Giro o tipo de negocio</label>
                  <select class="field-input field-select" id="store-type">
                    <option value="">Selecciona un giro</option>
                  </select>
                  <div class="business-type-tools">
                    <button class="business-type-btn" id="openBusinessTypePanelBtn" type="button">Agregar giro</button>
                    <span class="business-type-description" id="storeTypeDescription"></span>
                  </div>
                  <div class="business-type-panel" id="businessTypePanel" hidden>
                    <div class="business-type-grid">
                      <input class="field-input" id="business-type-name" type="text" placeholder="Giro de negocio" />
                      <input class="field-input" id="business-type-code" type="text" placeholder="Código" />
                    </div>
                    <textarea class="business-type-textarea" id="business-type-description" placeholder="Descripción"></textarea>
                    <div class="business-type-actions">
                      <button class="business-type-btn" id="saveBusinessTypeBtn" type="button">Guardar giro</button>
                      <button class="business-type-btn" id="cancelBusinessTypeBtn" type="button">Cancelar</button>
                    </div>
                    <p class="business-type-message" id="businessTypeMessage"></p>
                  </div>
                </div>
                <div class="field">
                  <label for="store-admin">Administrador de la tienda</label>
                  <select class="field-input field-select" id="store-admin">
                    <option value="">Cargando usuarios...</option>
                  </select>
                  <div class="admin-user-tools">
                    <p class="admin-user-note" id="storeAdminNote"></p>
                    <button class="admin-user-btn" id="createAdminUserBtn" type="button" hidden>Crear administrador de tienda</button>
                  </div>
                </div>
                <div class="field">
                  <label for="store-membership">Membresía</label>
                  <select class="field-input field-select" id="store-membership">
                    <option value="">Cargando membresías...</option>
                  </select>
                </div>
                <div style="display:flex;gap:12px;margin-top:20px;">
                  <button class="action-btn" id="store-save-btn" data-store-save-trigger="1" type="button">Guardar tienda</button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>

      <div class="notebook-panel backend-master-detail__panel" id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" hidden>
        <section class="section">
          <h2>Acceso a AVAN</h2>
          <div class="avan-grid">
            <div class="avan-row">
              <p class="avan-label">Activa Tienda</p>
              <input class="avan-check" id="store-is-active" type="checkbox" checked />
            </div>
            <div class="avan-row">
              <p class="avan-label">Tienda destacada<span class="hint">?</span></p>
              <input class="avan-check" id="store-is-featured" type="checkbox" checked />
            </div>
            <div class="avan-row">
              <p class="avan-label">Sistema de inventario</p>
              <input class="avan-check" id="store-inventory-enabled" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Vigencia<span class="hint">?</span></p>
              <input class="avan-input" id="store-validity" type="text" placeholder="Ej. 12 meses" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Acceso a Referidos</p>
              <input class="avan-check" id="store-referrals" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Acceso a Fidelización</p>
              <input class="avan-check" id="store-fidelizacion" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Notificaciones PWA</p>
              <input class="avan-check" id="store-pwa-notifications" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Sistema de cita</p>
              <input class="avan-check" id="store-appointments" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Sistema de cupones</p>
              <input class="avan-check" id="store-coupons" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">WhatsApp</p>
              <input class="avan-check" id="store-whatsapp" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Usuarios internos</p>
              <input class="avan-input" id="max-internal-users" type="number" min="0" step="1" placeholder="Máximo de empleados" oninput="localStorage.setItem('multitienda_max_internal_users', this.value)" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Usuarios de portal</p>
              <input class="avan-input" id="max-portal-users" type="number" min="0" step="1" placeholder="Máximo de clientes" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Puede subir videos</p>
              <input class="avan-check" id="store-can-upload-videos" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Red de proveedores</p>
              <input class="avan-check" id="store-can-use-providers" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Inteligencia Artificial</p>
              <input class="avan-check" id="store-can-use-ai" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Institución financiera</p>
              <input class="avan-check" id="store-can-use-financial" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Apartados</p>
              <input class="avan-check" id="store-can-use-layaway" type="checkbox" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Subastas</p>
              <input class="avan-check" id="store-can-use-auctions" type="checkbox" />
            </div>
          </div>
          <div style="display:flex;justify-content:flex-end;gap:12px;margin-top:20px;">
            <button class="action-btn" data-store-save-trigger="1" type="button">Guardar tienda</button>
          </div>
        </section>
      </div>

      <div class="notebook-panel backend-master-detail__panel" id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" hidden>
        <div class="pub-grid">

          <div class="pub-card">
            <div class="pub-card-header">
              <span class="pub-card-icon">🖼️</span>
              <h3 class="pub-card-title">Header principal</h3>
            </div>
            <div class="pub-card-body">
              <div class="field">
                <label>Nombre</label>
                <input class="field-input" type="text" placeholder="Nombre del header" />
              </div>
              <div class="pub-dates">
                <div class="field">
                  <label>Fecha inicial</label>
                  <input class="field-input" type="date" />
                </div>
                <div class="field">
                  <label>Fecha final</label>
                  <input class="field-input" type="date" />
                </div>
              </div>
            </div>
          </div>

          <div class="pub-card">
            <div class="pub-card-header">
              <span class="pub-card-icon">💬</span>
              <h3 class="pub-card-title">Ventana emergente</h3>
            </div>
            <div class="pub-card-body">
              <div class="field">
                <label>Nombre</label>
                <input class="field-input" type="text" placeholder="Nombre del popup" />
              </div>
              <div class="pub-dates">
                <div class="field">
                  <label>Fecha inicial</label>
                  <input class="field-input" type="date" />
                </div>
                <div class="field">
                  <label>Fecha final</label>
                  <input class="field-input" type="date" />
                </div>
              </div>
            </div>
          </div>

          <div class="pub-card">
            <div class="pub-card-header">
              <span class="pub-card-icon">⭐</span>
              <h3 class="pub-card-title">Tienda destacada</h3>
            </div>
            <div class="pub-card-body">
              <div class="field">
                <label>Nombre</label>
                <input class="field-input" type="text" placeholder="Nombre de la campaña" />
              </div>
              <div class="pub-dates">
                <div class="field">
                  <label>Fecha inicial</label>
                  <input class="field-input" type="date" />
                </div>
                <div class="field">
                  <label>Fecha final</label>
                  <input class="field-input" type="date" />
                </div>
              </div>
            </div>
          </div>

          <div class="pub-card">
            <div class="pub-card-header">
              <span class="pub-card-icon">🏷️</span>
              <h3 class="pub-card-title">Ofertas</h3>
            </div>
            <div class="pub-card-body">
              <div class="field">
                <label>Nombre</label>
                <input class="field-input" type="text" placeholder="Nombre de la oferta" />
              </div>
              <div class="pub-dates">
                <div class="field">
                  <label>Fecha inicial</label>
                  <input class="field-input" type="date" />
                </div>
                <div class="field">
                  <label>Fecha final</label>
                  <input class="field-input" type="date" />
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

      <div class="notebook-panel backend-master-detail__panel" id="tab-panel-4" role="tabpanel" aria-labelledby="tab-4" hidden>
        <section class="section">
          <h2>Institución financiera</h2>
          <p class="section-description">Datos de la institución financiera asociada a esta tienda.</p>
          <div class="field">
            <label for="fi-tipo">Tipo</label>
            <select class="field-input field-select" id="fi-tipo">
              <option value="">Selecciona un tipo</option>
              <option value="banco">Banco</option>
              <option value="cooperativa">Cooperativa de ahorro y crédito</option>
              <option value="caja_popular">Caja popular</option>
              <option value="union_credito">Unión de crédito</option>
              <option value="financiera">Financiera</option>
              <option value="otro">Otro</option>
            </select>
          </div>
          <div class="field">
            <label for="fi-nombre">Nombre</label>
            <input class="field-input" id="fi-nombre" type="text" placeholder="Nombre de la institución financiera" />
          </div>
        </section>
      </div>

      <!-- ===================== TAB 5: Categorías ===================== -->
      <div class="notebook-panel backend-master-detail__panel" id="tab-panel-5" role="tabpanel" aria-labelledby="tab-5" hidden>

        <!-- Vista lista -->
        <div id="cat-list-view">
          <div class="panel-header-row">
            <h2>Categorías de productos</h2>
            <button class="action-btn" id="cat-new-btn" type="button">+ Nueva categoría</button>
          </div>
          <table class="data-table" id="cat-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Descripción</th>
                <th>Categoría padre</th>
                <th>Imagen</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody id="cat-tbody">
              <tr class="empty-row" id="cat-empty-row">
                <td colspan="5" style="text-align:center;color:var(--mt-muted);padding:32px;">
                  No hay categorías registradas. Haz clic en <strong>+ Nueva categoría</strong> para agregar la primera.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Vista form -->
        <div id="cat-form-view" hidden>
          <div class="panel-header-row">
            <h2 id="cat-form-title">Nueva categoría</h2>
            <button class="action-btn action-btn--secondary" id="cat-cancel-btn" type="button">← Volver a lista</button>
          </div>

          <div class="field">
            <label for="cat-nombre">Nombre <span style="color:var(--mt-danger-text)">*</span></label>
            <input class="field-input" id="cat-nombre" type="text" placeholder="Nombre de la categoría" />
          </div>

          <div class="field">
            <label for="cat-descripcion">Descripción</label>
            <textarea class="field-input" id="cat-descripcion" rows="3" placeholder="Describe brevemente esta categoría"></textarea>
          </div>

          <div class="field">
            <label for="cat-padre">Categoría padre</label>
            <select class="field-input field-select" id="cat-padre">
              <option value="">— Sin categoría padre (categoría raíz) —</option>
            </select>
          </div>

          <div class="field">
            <label>Imagen de categoría</label>
            <div class="cat-image-box" id="cat-img-box" onclick="document.getElementById('cat-img-input').click()">
              <img id="cat-img-preview" src="" alt="Imagen categoría" />
              <div class="cat-image-placeholder">
                <div class="cat-image-icon">+</div>
                <div>Haz clic para cargar<br>la imagen de la categoría</div>
              </div>
            </div>
            <input type="file" id="cat-img-input" accept="image/*" style="display:none" />
            <p style="font-size:0.8rem;color:var(--mt-muted);margin-top:4px;">Haz clic en la imagen para cambiarla.</p>
          </div>

          <div class="field" style="display:flex;align-items:center;gap:10px;">
            <input type="checkbox" id="cat-activa" checked style="width:18px;height:18px;" />
            <label for="cat-activa" style="margin:0;cursor:pointer;">Categoría activa (visible en la tienda)</label>
          </div>

          <div style="display:flex;gap:12px;margin-top:20px;">
            <button class="action-btn" id="cat-save-btn" type="button">Guardar categoría</button>
            <button class="action-btn action-btn--secondary" id="cat-cancel-btn2" type="button">Cancelar</button>
          </div>
        </div>

      </div>

      <!-- ===================== TAB 6: Atributos ===================== -->
      <div class="notebook-panel backend-master-detail__panel" id="tab-panel-6" role="tabpanel" aria-labelledby="tab-6" hidden>

        <!-- Vista: lista de atributos -->
        <div id="attr-list-view">
          <div class="panel-header-row">
            <h2>Atributos de productos</h2>
            <button class="action-btn" id="attr-new-btn" type="button">+ Nuevo atributo</button>
          </div>
          <p style="color:var(--mt-muted);font-size:0.875rem;margin:-8px 0 16px;">
            Define los atributos que pueden tener tus productos (Color, Talla, Material, etc.) y sus valores posibles.
          </p>
          <table class="data-table" id="attr-table">
            <thead>
              <tr>
                <th>Nombre del atributo</th>
                <th>Tipo de control</th>
                <th>Valores</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody id="attr-tbody">
              <tr class="empty-row" id="attr-empty-row">
                <td colspan="4" style="text-align:center;color:var(--mt-muted);padding:32px;">
                  No hay atributos registrados. Haz clic en <strong>+ Nuevo atributo</strong> para agregar el primero.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Vista: form de atributo -->
        <div id="attr-form-view" hidden>
          <div class="panel-header-row">
            <h2 id="attr-form-title">Nuevo atributo</h2>
            <button class="action-btn action-btn--secondary" id="attr-cancel-btn" type="button">← Volver a lista</button>
          </div>

          <div class="attr-form-grid">
            <div>
              <div class="field">
                <label for="attr-nombre">Nombre del atributo <span style="color:var(--mt-danger-text)">*</span></label>
                <input class="field-input" id="attr-nombre" type="text" placeholder="Ej. Color, Talla, Material…" />
              </div>
              <div class="field">
                <label for="attr-tipo">Tipo de control</label>
                <select class="field-input field-select" id="attr-tipo">
                  <option value="color">Color (selector de color)</option>
                  <option value="texto">Texto (etiquetas)</option>
                  <option value="imagen">Imagen (swatch)</option>
                </select>
              </div>
              <div class="field" style="display:flex;align-items:center;gap:10px;">
                <input type="checkbox" id="attr-requerido" style="width:18px;height:18px;" />
                <label for="attr-requerido" style="margin:0;cursor:pointer;">Atributo requerido en productos</label>
              </div>
            </div>

            <div class="attr-values-col">
              <div class="attr-values-header">
                <label>Valores del atributo</label>
                <button class="action-btn" id="attr-add-value-btn" type="button" style="padding:5px 12px;font-size:0.8rem;">+ Agregar valor</button>
              </div>
              <div id="attr-values-list" class="attr-values-list">
                <p id="attr-values-empty" style="color:var(--mt-muted);font-size:0.85rem;padding:12px 0;">
                  Aún no hay valores. Haz clic en <strong>+ Agregar valor</strong>.
                </p>
              </div>
            </div>
          </div>

          <div style="display:flex;gap:12px;margin-top:24px;">
            <button class="action-btn" id="attr-save-btn" type="button">Guardar atributo</button>
            <button class="action-btn action-btn--secondary" id="attr-cancel-btn2" type="button">Cancelar</button>
          </div>
        </div>

      </div>
      </div>
    </div>
  </main>
  <div class="store-error-dialog" id="store-error-dialog" hidden>
    <div class="store-error-card" role="dialog" aria-modal="true" aria-labelledby="store-error-title">
      <h3 class="store-error-title" id="store-error-title">Error al guardar la tienda</h3>
      <textarea class="store-error-copy" id="store-error-text" readonly></textarea>
      <p class="store-error-copy-status" id="store-error-copy-status"></p>
      <div class="store-error-actions">
        <button class="action-btn action-btn--secondary" id="store-error-close-btn" type="button">Cerrar</button>
        <button class="action-btn" id="store-error-copy-btn" type="button">Copiar</button>
      </div>
    </div>
  </div>
  <script src="/multitienda/static/js/backend-sidebar-core.js"></script>
  <script>
    (function () {
      if (window.initBackendSidebarCore) {
        window.initBackendSidebarCore();
      }
    })();

    (function () {
      try {
        const STORAGE_KEY = "multitienda_stores";
        const listView = document.getElementById("store-list-view");
        const formView = document.getElementById("store-form-view");
        const tbody = document.getElementById("store-tbody");
        const emptyRow = document.getElementById("store-empty-row");
        const newBtn = document.getElementById("store-new-btn");
        const cancelBtn = document.getElementById("store-cancel-btn");
        const saveButtons = Array.from(document.querySelectorAll('[data-store-save-trigger="1"]'));
        const formTitle = document.getElementById("store-form-title");
        const nameInput = document.getElementById("store-name");
        const typeSelect = document.getElementById("store-type");
        const adminSelect = document.getElementById("store-admin");
        const membershipInput = document.getElementById("store-membership");
        const activeCheckbox = document.getElementById("store-is-active");
        const featuredCheckbox = document.getElementById("store-is-featured");
        const inventoryCheckbox = document.getElementById("store-inventory-enabled");
        const validityInput = document.getElementById("store-validity");
        const referralsCheckbox = document.getElementById("store-referrals");
        const fidelizacionCheckbox = document.getElementById("store-fidelizacion");
        const pwaNotificationsCheckbox = document.getElementById("store-pwa-notifications");
        const appointmentsCheckbox = document.getElementById("store-appointments");
        const couponsCheckbox = document.getElementById("store-coupons");
        const whatsappCheckbox = document.getElementById("store-whatsapp");
        const maxInternalUsersInput = document.getElementById("max-internal-users");
        const maxPortalUsersInput = document.getElementById("max-portal-users");
        const canUploadVideosCheckbox = document.getElementById("store-can-upload-videos");
        const canUseProvidersCheckbox = document.getElementById("store-can-use-providers");
        const canUseAiCheckbox = document.getElementById("store-can-use-ai");
        const canUseFinancialCheckbox = document.getElementById("store-can-use-financial");
        const canUseLayawayCheckbox = document.getElementById("store-can-use-layaway");
        const canUseAuctionsCheckbox = document.getElementById("store-can-use-auctions");
        const errorDialog = document.getElementById("store-error-dialog");
        const errorText = document.getElementById("store-error-text");
        const errorCopyBtn = document.getElementById("store-error-copy-btn");
        const errorCloseBtn = document.getElementById("store-error-close-btn");
        const errorCopyStatus = document.getElementById("store-error-copy-status");
        let stores = [];
        let editIndex = -1;
        let currentStoreId = "";

      function closeStoreErrorDialog() {
        if (errorDialog) errorDialog.hidden = true;
        if (errorCopyStatus) errorCopyStatus.textContent = "";
      }

      function showStoreErrorDialog(message) {
        const text = String(message || "No se pudo guardar la tienda.");
        if (!errorDialog || !errorText) {
          window.alert(text);
          return;
        }
        errorText.value = text;
        errorDialog.hidden = false;
        if (errorCopyStatus) errorCopyStatus.textContent = "Puedes copiar este error para soporte.";
        window.setTimeout(function () {
          errorText.focus();
          errorText.select();
        }, 0);
      }

      async function copyStoreErrorText() {
        if (!errorText) return;
        const text = errorText.value || "";
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
          } else {
            errorText.focus();
            errorText.select();
            document.execCommand("copy");
          }
          if (errorCopyStatus) errorCopyStatus.textContent = "Error copiado.";
        } catch (error) {
          if (errorCopyStatus) errorCopyStatus.textContent = "No se pudo copiar automáticamente. Selecciona el texto y copia manualmente.";
        }
      }

      async function loadStores() {
        try {
          const response = await fetch("/multitienda/api/stores", { headers: { "Accept": "application/json" } });
          if (!response.ok) {
            throw new Error("No se pudieron cargar las tiendas.");
          }
          const payload = await response.json();
          stores = Array.isArray(payload && payload.data) ? payload.data : [];
          saveStores();
        } catch (error) {
          try { stores = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch (e) { stores = []; }
        }
      }

      function saveStores() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(stores));
      }

      function escHtml(value) {
        return String(value == null ? "" : value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      }

      function adminLabel() {
        if (!adminSelect) return "";
        const option = adminSelect.options[adminSelect.selectedIndex];
        return option ? String(option.textContent || "").replace(/\s+\(Administrador de tienda\)\s*$/, "") : "";
      }

      function giroLabel() {
        if (!typeSelect) return "";
        const option = typeSelect.options[typeSelect.selectedIndex];
        return option ? String(option.textContent || "") : "";
      }

      function showList() {
        if (listView) listView.hidden = false;
        if (formView) formView.hidden = true;
        editIndex = -1;
        currentStoreId = "";
      }

      function showForm(index) {
        editIndex = typeof index === "number" ? index : -1;
        if (listView) listView.hidden = true;
        if (formView) formView.hidden = false;
        if (editIndex >= 0 && stores[editIndex]) {
          const item = stores[editIndex];
          currentStoreId = String(item.id || "");
          if (formTitle) formTitle.textContent = "Editar tienda";
          if (nameInput) nameInput.value = item.name || "";
          if (typeSelect) typeSelect.value = item.typeCode || "";
          if (adminSelect) adminSelect.value = item.adminId || "";
          if (adminSelect) adminSelect.disabled = false;
          if (membershipInput) membershipInput.value = item.membership || "";
          if (activeCheckbox) activeCheckbox.checked = item.isActive !== false;
          if (featuredCheckbox) featuredCheckbox.checked = !!item.isFeatured;
          if (inventoryCheckbox) inventoryCheckbox.checked = !!item.inventoryEnabled;
          if (validityInput) validityInput.value = item.validity || "";
          if (referralsCheckbox) referralsCheckbox.checked = !!item.referrals;
          if (fidelizacionCheckbox) fidelizacionCheckbox.checked = !!item.fidelizacion;
          if (pwaNotificationsCheckbox) pwaNotificationsCheckbox.checked = !!item.pwaNotifications;
          if (appointmentsCheckbox) appointmentsCheckbox.checked = !!item.appointments;
          if (couponsCheckbox) couponsCheckbox.checked = !!item.coupons;
          if (whatsappCheckbox) whatsappCheckbox.checked = !!item.whatsapp;
          if (maxInternalUsersInput) maxInternalUsersInput.value = item.maxInternalUsers || "";
          if (maxPortalUsersInput) maxPortalUsersInput.value = item.maxPortalUsers || "";
          if (canUploadVideosCheckbox) canUploadVideosCheckbox.checked = !!item.canUploadVideos;
          if (canUseProvidersCheckbox) canUseProvidersCheckbox.checked = !!item.canUseProviders;
          if (canUseAiCheckbox) canUseAiCheckbox.checked = !!item.canUseAi;
          if (canUseFinancialCheckbox) canUseFinancialCheckbox.checked = !!item.canUseFinancial;
          if (canUseLayawayCheckbox) canUseLayawayCheckbox.checked = !!item.canUseLayaway;
          if (canUseAuctionsCheckbox) canUseAuctionsCheckbox.checked = !!item.canUseAuctions;
        } else {
          currentStoreId = "";
          if (formTitle) formTitle.textContent = "Nueva tienda";
          if (nameInput) nameInput.value = "";
          if (typeSelect) typeSelect.value = "";
          if (adminSelect) adminSelect.value = "";
          if (adminSelect) adminSelect.disabled = false;
          if (membershipInput) membershipInput.value = "";
          if (activeCheckbox) activeCheckbox.checked = true;
          if (featuredCheckbox) featuredCheckbox.checked = true;
          if (inventoryCheckbox) inventoryCheckbox.checked = false;
          if (validityInput) validityInput.value = "";
          if (referralsCheckbox) referralsCheckbox.checked = false;
          if (fidelizacionCheckbox) fidelizacionCheckbox.checked = false;
          if (pwaNotificationsCheckbox) pwaNotificationsCheckbox.checked = false;
          if (appointmentsCheckbox) appointmentsCheckbox.checked = false;
          if (couponsCheckbox) couponsCheckbox.checked = false;
          if (whatsappCheckbox) whatsappCheckbox.checked = false;
          if (maxInternalUsersInput) maxInternalUsersInput.value = "";
          if (maxPortalUsersInput) maxPortalUsersInput.value = "";
          if (canUploadVideosCheckbox) canUploadVideosCheckbox.checked = false;
          if (canUseProvidersCheckbox) canUseProvidersCheckbox.checked = false;
          if (canUseAiCheckbox) canUseAiCheckbox.checked = false;
          if (canUseFinancialCheckbox) canUseFinancialCheckbox.checked = false;
          if (canUseLayawayCheckbox) canUseLayawayCheckbox.checked = false;
          if (canUseAuctionsCheckbox) canUseAuctionsCheckbox.checked = false;
        }
        if (typeSelect && typeof typeSelect.dispatchEvent === "function") {
          typeSelect.dispatchEvent(new Event("change"));
        }
      }

      function renderStores() {
        if (!tbody || !emptyRow) return;
        tbody.innerHTML = "";
        if (!stores.length) {
          tbody.appendChild(emptyRow);
          return;
        }
        stores.forEach(function (item, index) {
          const tr = document.createElement("tr");
          tr.style.cursor = "pointer";
          tr.innerHTML =
            "<td>" + escHtml(item.name || "Sin nombre") + "</td>" +
            "<td>" + escHtml(item.typeLabel || "—") + "</td>" +
            "<td>" + escHtml(item.adminLabel || "—") + "</td>" +
            "<td>" + escHtml(item.membership || "—") + "</td>" +
            "<td>" + escHtml(item.isActive === false ? "Inactiva" : "Activa") + "</td>";
          tr.setAttribute("data-store-index", String(index));
          tbody.appendChild(tr);
        });
      }

      window.multitiendaShowStoreForm = function (index) {
        showForm(Number(index));
      };

      window.multitiendaShowStoreList = function () {
        showList();
        renderStores();
      };

      if (newBtn) newBtn.addEventListener("click", function () { showForm(-1); });
      if (cancelBtn) cancelBtn.addEventListener("click", function () { showList(); renderStores(); });
      async function persistStore() {
          const payload = {
            name: String(nameInput && nameInput.value || "").trim(),
            typeCode: String(typeSelect && typeSelect.value || "").trim(),
            typeLabel: giroLabel(),
            adminId: String(adminSelect && adminSelect.value || "").trim(),
            adminLabel: adminLabel(),
            membership: String(membershipInput && membershipInput.value || "").trim(),
            isActive: !!(activeCheckbox && activeCheckbox.checked),
            isFeatured: !!(featuredCheckbox && featuredCheckbox.checked),
            inventoryEnabled: !!(inventoryCheckbox && inventoryCheckbox.checked),
            validity: String(validityInput && validityInput.value || "").trim(),
            referrals: !!(referralsCheckbox && referralsCheckbox.checked),
            fidelizacion: !!(fidelizacionCheckbox && fidelizacionCheckbox.checked),
            pwaNotifications: !!(pwaNotificationsCheckbox && pwaNotificationsCheckbox.checked),
            appointments: !!(appointmentsCheckbox && appointmentsCheckbox.checked),
            coupons: !!(couponsCheckbox && couponsCheckbox.checked),
            whatsapp: !!(whatsappCheckbox && whatsappCheckbox.checked),
            maxInternalUsers: String(maxInternalUsersInput && maxInternalUsersInput.value || "").trim(),
            maxPortalUsers: String(maxPortalUsersInput && maxPortalUsersInput.value || "").trim(),
            canUploadVideos: !!(canUploadVideosCheckbox && canUploadVideosCheckbox.checked),
            canUseProviders: !!(canUseProvidersCheckbox && canUseProvidersCheckbox.checked),
            canUseAi: !!(canUseAiCheckbox && canUseAiCheckbox.checked),
            canUseFinancial: !!(canUseFinancialCheckbox && canUseFinancialCheckbox.checked),
            canUseLayaway: !!(canUseLayawayCheckbox && canUseLayawayCheckbox.checked),
            canUseAuctions: !!(canUseAuctionsCheckbox && canUseAuctionsCheckbox.checked),
          };
          const isEditingStore = currentStoreId !== "";
          if (!payload.name) {
            window.alert("Nombre de la tienda es obligatorio.");
            return;
          }
          if (!payload.adminId) {
            window.alert("Selecciona un administrador de tienda.");
            return;
          }
          const response = await fetch("/multitienda/api/stores", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Accept": "application/json"
            },
            body: JSON.stringify({
              is_edit: isEditingStore,
              store_id: currentStoreId,
              store_name: payload.name,
              store_type: payload.typeCode,
              store_type_name: payload.typeLabel,
              admin_user_id: payload.adminId,
              membership: payload.membership,
              is_active: payload.isActive,
              is_featured: payload.isFeatured,
              inventory_enabled: payload.inventoryEnabled,
              validity: payload.validity,
              referrals: payload.referrals,
              pwa_notifications: payload.pwaNotifications,
              appointments: payload.appointments,
              coupons: payload.coupons,
              whatsapp: payload.whatsapp,
              max_internal_users: payload.maxInternalUsers,
              max_portal_users: payload.maxPortalUsers,
              can_upload_videos: payload.canUploadVideos,
              can_use_providers: payload.canUseProviders,
              can_use_ai: payload.canUseAi,
              can_use_financial: payload.canUseFinancial,
              can_use_layaway: payload.canUseLayaway,
              can_use_auctions: payload.canUseAuctions,
            })
          });
          const responseText = await response.text().catch(function () { return ""; });
          let responsePayload = {};
          try {
            responsePayload = responseText ? JSON.parse(responseText) : {};
          } catch (error) {
            responsePayload = { detail: responseText };
          }
          if (!response.ok) {
            throw new Error(responsePayload.detail || "No se pudo guardar la tienda.");
          }
          await loadStores();
          renderStores();
          showList();
      }

      saveButtons.forEach(function (button) {
        button.addEventListener("click", async function () {
          try {
            await persistStore();
          } catch (error) {
            showStoreErrorDialog(error && error.message ? error.message : "No se pudo guardar la tienda.");
          }
        });
      });

      if (errorCloseBtn) {
        errorCloseBtn.addEventListener("click", function () {
          closeStoreErrorDialog();
        });
      }

      if (errorCopyBtn) {
        errorCopyBtn.addEventListener("click", function () {
          copyStoreErrorText();
        });
      }

      if (errorDialog) {
        errorDialog.addEventListener("click", function (event) {
          if (event.target === errorDialog) closeStoreErrorDialog();
        });
      }

      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && errorDialog && !errorDialog.hidden) {
          closeStoreErrorDialog();
        }
      });

      document.addEventListener("click", function (event) {
        var newButton = event.target && event.target.closest && event.target.closest("#store-new-btn");
        if (newButton) {
          event.preventDefault();
          showForm(-1);
          return;
        }
        var cancelButton = event.target && event.target.closest && event.target.closest("#store-cancel-btn");
        if (cancelButton) {
          event.preventDefault();
          showList();
          renderStores();
          return;
        }
        var row = event.target && event.target.closest && event.target.closest("#store-tbody tr[data-store-index]");
        if (row) {
          event.preventDefault();
          showForm(Number(row.getAttribute("data-store-index")));
        }
      });

        loadStores().then(function () {
          renderStores();
        });
      } catch (error) {
        console.error("multitienda stores init failed", error);
      }
    })();

    (function () {
      try {
        const BUSINESS_TYPES_PATHS = ["/multitienda/api/business-types"];
        const select = document.getElementById("store-type");
        const description = document.getElementById("storeTypeDescription");
        const openPanelBtn = document.getElementById("openBusinessTypePanelBtn");
        const panel = document.getElementById("businessTypePanel");
        const nameInput = document.getElementById("business-type-name");
        const codeInput = document.getElementById("business-type-code");
        const detailInput = document.getElementById("business-type-description");
        const saveBtn = document.getElementById("saveBusinessTypeBtn");
        const cancelBtn = document.getElementById("cancelBusinessTypeBtn");
        const message = document.getElementById("businessTypeMessage");
        if (!select) {
          return;
        }

      function clearPanelMessage() {
        if (!message) return;
        message.textContent = "";
        message.style.color = "var(--mt-danger-text)";
      }

      function renderOptions(catalog, selectedCode) {
        const currentValue = selectedCode || select.value || "";
        select.innerHTML = '<option value="">Selecciona un giro</option>';
        catalog.forEach(function (item) {
          const option = document.createElement("option");
          option.value = item.code;
          option.textContent = item.name + " (" + item.code + ")";
          option.dataset.description = item.description || "";
          select.appendChild(option);
        });
        select.value = currentValue;
      }

      function updateDescription() {
        const option = select.options[select.selectedIndex];
        if (!option || !description) return;
        description.textContent = option.dataset.description || "";
      }

      function openPanel() {
        if (!panel) return;
        panel.hidden = false;
        clearPanelMessage();
      }

      function closePanel() {
        if (!panel) return;
        panel.hidden = true;
        clearPanelMessage();
        if (nameInput) nameInput.value = "";
        if (codeInput) codeInput.value = "";
        if (detailInput) detailInput.value = "";
      }

      let catalog = [];

      async function fetchBusinessTypes(path, options) {
        const response = await fetch(path, Object.assign({ headers: { "Accept": "application/json" } }, options || {}));
        return response;
      }

      async function fetchBusinessTypesWithFallback(options) {
        let lastError = null;
        for (const path of BUSINESS_TYPES_PATHS) {
          try {
            const response = await fetchBusinessTypes(path, options);
            if (response.ok) {
              return { response: response, path: path };
            }
            lastError = new Error("HTTP " + response.status);
          } catch (error) {
            lastError = error;
          }
        }
        throw lastError || new Error("No se pudo conectar con el catálogo de giros");
      }

      async function loadCatalog() {
        try {
          const result = await fetchBusinessTypesWithFallback();
          const response = result.response;
          const data = await response.json();
          catalog = Array.isArray(data) ? data : [];
          renderOptions(catalog);
          updateDescription();
        } catch (error) {
          catalog = [];
          renderOptions(catalog);
          updateDescription();
          if (message) {
            message.textContent = "No se pudo cargar el catálogo de giros.";
          }
        }
      }

      select.addEventListener("change", updateDescription);

      if (openPanelBtn) {
        openPanelBtn.addEventListener("click", openPanel);
      }
      if (cancelBtn) {
        cancelBtn.addEventListener("click", closePanel);
      }

      if (saveBtn) {
        saveBtn.addEventListener("click", async function () {
          const name = (nameInput && nameInput.value || "").trim();
          const code = (codeInput && codeInput.value || "").trim().toUpperCase();
          const detail = (detailInput && detailInput.value || "").trim();
          if (!name || !code || !detail) {
            if (message) {
              message.textContent = "Completa Giro de negocio, Código y Descripción.";
            }
            return;
          }
          try {
            const result = await fetchBusinessTypesWithFallback({
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
              },
              body: JSON.stringify({ name: name, code: code, description: detail })
            });
            const response = result.response;
            const payload = await response.json().catch(function () { return {}; });
            if (!response.ok) {
              throw new Error(payload.detail || "No se pudo guardar el giro.");
            }
            catalog = catalog.concat([payload]);
            renderOptions(catalog, code);
            updateDescription();
            if (message) {
              message.style.color = "var(--mt-accent)";
              message.textContent = "Giro agregado correctamente.";
            }
            setTimeout(closePanel, 600);
          } catch (error) {
            if (message) {
              message.style.color = "var(--mt-danger-text)";
              message.textContent = error && error.message ? error.message : "No se pudo guardar el giro.";
            }
          }
        });
      }

        loadCatalog();
      } catch (error) {
        console.error("multitienda business types init failed", error);
      }
    })();

    (function () {
      try {
        const adminSelect = document.getElementById("store-admin");
        const adminNote = document.getElementById("storeAdminNote");
        const createUserBtn = document.getElementById("createAdminUserBtn");
        if (!adminSelect) {
          return;
        }

      function normalizeRole(value) {
        return String(value || "")
          .trim()
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .replace(/\s+/g, "_");
      }

        async function loadUsers() {
          try {
            const response = await fetch("/api/usuarios", { headers: { "Accept": "application/json" } });
          if (!response.ok) {
            throw new Error("No se pudieron cargar usuarios");
          }
          const payload = await response.json();
          const rawUsers = Array.isArray(payload) ? payload : (Array.isArray(payload && payload.data) ? payload.data : []);
          const users = rawUsers.filter(function (user) {
            return normalizeRole(user && user.rol) === "administrador_tienda";
          });
          adminSelect.innerHTML = "";

          const placeholder = document.createElement("option");
          placeholder.value = "";
          placeholder.textContent = "Selecciona un administrador de tienda";
          adminSelect.appendChild(placeholder);

          if (!users.length) {
            const emptyOption = document.createElement("option");
            emptyOption.value = "";
            emptyOption.textContent = "Sin administradores de tienda";
            adminSelect.appendChild(emptyOption);
            if (adminNote) {
              adminNote.textContent = "Primero crea un usuario con rol Administrador de tienda en Usuarios.";
            }
            if (createUserBtn) {
              createUserBtn.hidden = false;
            }
            return;
          }

          users.forEach(function (user) {
            const option = document.createElement("option");
            option.value = String(user.id || "");
            option.textContent = (user.usuario || user.username || "Usuario") + " (Administrador de tienda)";
            adminSelect.appendChild(option);
          });

          if (adminNote) {
            adminNote.textContent = "Solo se muestran usuarios con rol Administrador de tienda.";
          }
          if (createUserBtn) {
            createUserBtn.hidden = true;
          }
        } catch (error) {
          adminSelect.innerHTML = '<option value="">No disponible</option>';
          if (adminNote) {
            adminNote.textContent = "No se pudo cargar el listado. Intenta nuevamente.";
          }
          if (createUserBtn) {
            createUserBtn.hidden = false;
          }
        }
      }

        if (createUserBtn) {
          createUserBtn.addEventListener("click", function () {
            window.location.href = "/empresa/usuarios";
          });
        }

        loadUsers();
      } catch (error) {
        console.error("multitienda admin users init failed", error);
      }
    })();

    (function () {
      try {
        const membershipSelect = document.getElementById("store-membership");
        if (!membershipSelect) return;

        fetch("/multitienda/api/memberships", { headers: { "Accept": "application/json" } })
          .then(function (response) {
            if (!response.ok) throw new Error("No se pudieron cargar las membresías");
            return response.json();
          })
          .then(function (payload) {
            const rows = Array.isArray(payload && payload.data) ? payload.data : [];
            membershipSelect.innerHTML = '<option value="">Selecciona una membresía</option>';
            rows.forEach(function (item) {
              const option = document.createElement("option");
              option.value = String(item.nombre || "");
              option.textContent = String(item.nombre || item.tipo || "Membresía");
              membershipSelect.appendChild(option);
            });
          })
          .catch(function () {
            membershipSelect.innerHTML = '<option value="">No disponible</option>';
          });
      } catch (error) {
        console.error("multitienda memberships init failed", error);
      }
    })();

  </script>
  <script src="/multitienda/static/js/backend-master-detail.js"></script>
  <script src="/multitienda/static/js/sidebar-theme-editor.js"></script>
  <script src="/multitienda/static/js/backend-navbar.js"></script>
  <script>
    (function () {
      var panelToTab = {
        tiendas: "tab-1",
        acceso: "tab-2",
        publicidad: "tab-3",
        institucion_financiera: "tab-4",
        categorias: "tab-5",
        atributos: "tab-6"
      };

      function syncGestionPanelFromUrl() {
        var params = new URLSearchParams(window.location.search || "");
        var panelKey = String(params.get("panel") || "tiendas").trim().toLowerCase();
        var tabId = panelToTab[panelKey] || panelToTab.tiendas;
        var tab = document.getElementById(tabId);
        if (tab) {
          tab.click();
        }
        document.querySelectorAll(".sb-subitem[data-gestion-panel]").forEach(function (link) {
          link.classList.toggle("is-active", link.getAttribute("data-gestion-panel") === panelKey);
        });
      }

      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", syncGestionPanelFromUrl);
      } else {
        syncGestionPanelFromUrl();
      }
    })();
  </script>
  <script>
    /* ---- Categorías ---- */
    (function () {
      var STORAGE_KEY = "multitienda_categorias";
      var categories  = [];
      var editIndex   = -1;

      var listView    = document.getElementById("cat-list-view");
      var formView    = document.getElementById("cat-form-view");
      var tbody       = document.getElementById("cat-tbody");
      var emptyRow    = document.getElementById("cat-empty-row");
      var formTitle   = document.getElementById("cat-form-title");
      var padreSelect = document.getElementById("cat-padre");
      var imgBox      = document.getElementById("cat-img-box");
      var imgInput    = document.getElementById("cat-img-input");
      var imgPreview  = document.getElementById("cat-img-preview");
      var DEFAULT_IMG = "";

      function syncCategoryImagePreview(src) {
        var resolved = String(src || "").trim();
        imgPreview.src = resolved;
        imgBox.classList.toggle("has-image", resolved !== "");
      }

      /* ---------- persistencia ---------- */
      function load() {
        try { categories = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch(e) { categories = []; }
      }
      function save() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(categories));
      }

      /* ---------- poblar select padre ---------- */
      function refreshPadreOptions(excludeIndex) {
        padreSelect.innerHTML = '<option value="">— Sin categoría padre (categoría raíz) —</option>';
        categories.forEach(function (c, i) {
          if (i === excludeIndex) return;
          var opt = document.createElement("option");
          opt.value = String(i);
          opt.textContent = c.nombre;
          padreSelect.appendChild(opt);
        });
      }

      /* ---------- render tabla ---------- */
      function renderList() {
        while (tbody.rows.length > 0) tbody.deleteRow(0);
        if (categories.length === 0) {
          tbody.appendChild(emptyRow);
          return;
        }
        categories.forEach(function (c, i) {
          var tr = tbody.insertRow();
          var padreNombre = c.padreIdx !== "" && c.padreIdx !== undefined
            ? (categories[Number(c.padreIdx)] ? categories[Number(c.padreIdx)].nombre : "—") : "—";
          tr.innerHTML =
            '<td>' + escHtml(c.nombre) + '</td>' +
            '<td style="color:var(--mt-muted);font-size:0.85rem;">' + escHtml(c.descripcion || "") + '</td>' +
            '<td>' + escHtml(padreNombre) + '</td>' +
            '<td>' + (c.imagen
              ? '<img src="' + escHtml(c.imagen) + '" style="width:40px;height:40px;object-fit:cover;border-radius:6px;" alt="Imagen de categoría" />'
              : '<div style="width:40px;height:40px;border:1px dashed var(--mt-border);border-radius:6px;display:grid;place-items:center;color:var(--mt-muted);font-size:0.8rem;">+</div>')
            + '</td>' +
            '<td style="display:flex;gap:8px;">' +
              '<button class="action-btn" style="padding:4px 10px;font-size:0.8rem;" data-edit="' + i + '" type="button">Editar</button>' +
              '<button class="action-btn action-btn--danger" style="padding:4px 10px;font-size:0.8rem;" data-del="' + i + '" type="button">Eliminar</button>' +
            '</td>';
        });
      }

      function escHtml(s) {
        return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
      }

      /* ---------- mostrar / ocultar vistas ---------- */
      function showList() {
        listView.hidden = false;
        formView.hidden = true;
        editIndex = -1;
        syncCategoryImagePreview(DEFAULT_IMG);
      }
      function showForm(idx) {
        editIndex = idx;
        refreshPadreOptions(idx);
        if (idx >= 0) {
          var c = categories[idx];
          formTitle.textContent = "Editar categoría";
          document.getElementById("cat-nombre").value      = c.nombre || "";
          document.getElementById("cat-descripcion").value = c.descripcion || "";
          padreSelect.value = c.padreIdx !== undefined ? String(c.padreIdx) : "";
          document.getElementById("cat-activa").checked    = c.activa !== false;
          syncCategoryImagePreview(c.imagen || DEFAULT_IMG);
        } else {
          formTitle.textContent = "Nueva categoría";
          document.getElementById("cat-nombre").value      = "";
          document.getElementById("cat-descripcion").value = "";
          padreSelect.value = "";
          document.getElementById("cat-activa").checked    = true;
          syncCategoryImagePreview(DEFAULT_IMG);
        }
        listView.hidden = true;
        formView.hidden = false;
      }

      /* ---------- guardar ---------- */
      function saveCategory() {
        var nombre = document.getElementById("cat-nombre").value.trim();
        if (!nombre) { alert("El nombre de la categoría es obligatorio."); return; }
        var cat = {
          nombre:      nombre,
          descripcion: document.getElementById("cat-descripcion").value.trim(),
          padreIdx:    padreSelect.value,
          activa:      document.getElementById("cat-activa").checked,
          imagen:      imgPreview.src || DEFAULT_IMG
        };
        if (editIndex >= 0) {
          categories[editIndex] = cat;
        } else {
          categories.push(cat);
        }
        save();
        renderList();
        showList();
      }

      /* ---------- imagen preview ---------- */
      imgInput.addEventListener("change", function () {
        var file = imgInput.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function (event) {
          syncCategoryImagePreview(event && event.target ? event.target.result : "");
        };
        reader.readAsDataURL(file);
      });

      /* ---------- eventos ---------- */
      document.getElementById("cat-new-btn").addEventListener("click", function () { showForm(-1); });
      document.getElementById("cat-cancel-btn").addEventListener("click", showList);
      document.getElementById("cat-cancel-btn2").addEventListener("click", showList);
      document.getElementById("cat-save-btn").addEventListener("click", saveCategory);

      tbody.addEventListener("click", function (e) {
        var editBtn = e.target.closest("[data-edit]");
        var delBtn  = e.target.closest("[data-del]");
        if (editBtn) { showForm(Number(editBtn.dataset.edit)); }
        if (delBtn) {
          var i = Number(delBtn.dataset.del);
          if (confirm('¿Eliminar la categoría "' + categories[i].nombre + '"?')) {
            categories.splice(i, 1);
            save();
            renderList();
          }
        }
      });

      /* ---------- init ---------- */
      load();
      renderList();
      syncCategoryImagePreview(DEFAULT_IMG);
    })();

    /* ---- Atributos ---- */
    (function () {
      var STORAGE_KEY  = "multitienda_atributos";
      var attributes   = [];
      var editIndex    = -1;
      var pendingValues = [];   // valores en edición antes de guardar

      var listView   = document.getElementById("attr-list-view");
      var formView   = document.getElementById("attr-form-view");
      var tbody      = document.getElementById("attr-tbody");
      var emptyRow   = document.getElementById("attr-empty-row");
      var formTitle  = document.getElementById("attr-form-title");
      var valuesList = document.getElementById("attr-values-list");
      var valEmpty   = document.getElementById("attr-values-empty");

      /* ---------- persistencia ---------- */
      function load() {
        try { attributes = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch(e) { attributes = []; }
      }
      function save() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(attributes));
      }

      /* ---------- render valores en form ---------- */
      function renderValueRows() {
        while (valuesList.firstChild) valuesList.removeChild(valuesList.firstChild);
        if (pendingValues.length === 0) {
          valuesList.appendChild(valEmpty);
          return;
        }
        var tipo = document.getElementById("attr-tipo").value;
        pendingValues.forEach(function (v, i) {
          var row = document.createElement("div");
          row.className = "attr-value-row";
          if (tipo === "color") {
            row.innerHTML =
              '<input type="color" class="attr-color-swatch" value="' + escAttr(v.color || "#cccccc") + '" data-color-idx="' + i + '" title="Cambiar color" />' +
              '<span class="attr-val-name">' + escHtml(v.nombre) + '</span>' +
              '<button class="attr-val-del" data-val-del="' + i + '" type="button" title="Eliminar">✕</button>';
          } else {
            row.innerHTML =
              '<span class="attr-val-name">' + escHtml(v.nombre) + '</span>' +
              '<button class="attr-val-del" data-val-del="' + i + '" type="button" title="Eliminar">✕</button>';
          }
          valuesList.appendChild(row);
        });
        // color change listener
        valuesList.querySelectorAll("[data-color-idx]").forEach(function (input) {
          input.addEventListener("input", function () {
            pendingValues[Number(input.dataset.colorIdx)].color = input.value;
          });
        });
      }

      /* ---------- render tabla lista ---------- */
      function renderList() {
        while (tbody.rows.length > 0) tbody.deleteRow(0);
        if (attributes.length === 0) {
          tbody.appendChild(emptyRow);
          return;
        }
        attributes.forEach(function (a, i) {
          var tr = tbody.insertRow();
          var tipoLabel = { color: "Color", texto: "Texto", imagen: "Imagen" }[a.tipo] || a.tipo;
          var badges = (a.valores || []).slice(0, 8).map(function (v) {
            var dot = a.tipo === "color"
              ? '<span class="attr-badge-color" style="background:' + escAttr(v.color || "#ccc") + '"></span>'
              : "";
            return '<span class="attr-badge">' + dot + escHtml(v.nombre) + '</span>';
          }).join("");
          if ((a.valores || []).length > 8) {
            badges += '<span class="attr-badge" style="color:var(--mt-muted);">+' + ((a.valores.length - 8)) + ' más</span>';
          }
          tr.innerHTML =
            '<td style="font-weight:600;">' + escHtml(a.nombre) + (a.requerido ? ' <span style="color:var(--mt-danger-text);font-size:0.8rem;" title="Requerido">●</span>' : "") + '</td>' +
            '<td style="color:var(--mt-muted);font-size:0.85rem;">' + tipoLabel + '</td>' +
            '<td>' + (badges || '<span style="color:var(--mt-muted);font-size:0.82rem;">Sin valores</span>') + '</td>' +
            '<td style="display:flex;gap:8px;">' +
              '<button class="action-btn" style="padding:4px 10px;font-size:0.8rem;" data-attr-edit="' + i + '" type="button">Editar</button>' +
              '<button class="action-btn action-btn--danger" style="padding:4px 10px;font-size:0.8rem;" data-attr-del="' + i + '" type="button">Eliminar</button>' +
            '</td>';
        });
      }

      /* ---------- vistas ---------- */
      function showList() {
        listView.hidden = false;
        formView.hidden = true;
        editIndex = -1;
        pendingValues = [];
      }
      function showForm(idx) {
        editIndex = idx;
        if (idx >= 0) {
          var a = attributes[idx];
          formTitle.textContent = "Editar atributo";
          document.getElementById("attr-nombre").value    = a.nombre || "";
          document.getElementById("attr-tipo").value      = a.tipo   || "texto";
          document.getElementById("attr-requerido").checked = a.requerido || false;
          pendingValues = (a.valores || []).map(function (v) { return Object.assign({}, v); });
        } else {
          formTitle.textContent = "Nuevo atributo";
          document.getElementById("attr-nombre").value    = "";
          document.getElementById("attr-tipo").value      = "texto";
          document.getElementById("attr-requerido").checked = false;
          pendingValues = [];
        }
        renderValueRows();
        listView.hidden = true;
        formView.hidden = false;
      }

      /* ---------- agregar valor con prompt ---------- */
      function promptAddValue() {
        var tipo = document.getElementById("attr-tipo").value;
        var nombre = prompt("Nombre del valor (ej. Rojo, S, Algodón…):");
        if (!nombre || !nombre.trim()) return;
        var v = { nombre: nombre.trim() };
        if (tipo === "color") { v.color = "#cccccc"; }
        pendingValues.push(v);
        renderValueRows();
      }

      /* ---------- guardar atributo ---------- */
      function saveAttribute() {
        var nombre = document.getElementById("attr-nombre").value.trim();
        if (!nombre) { alert("El nombre del atributo es obligatorio."); return; }
        var attr = {
          nombre:    nombre,
          tipo:      document.getElementById("attr-tipo").value,
          requerido: document.getElementById("attr-requerido").checked,
          valores:   pendingValues.slice()
        };
        if (editIndex >= 0) {
          attributes[editIndex] = attr;
        } else {
          attributes.push(attr);
        }
        save();
        renderList();
        showList();
      }

      /* ---------- helpers ---------- */
      function escHtml(s) {
        return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
      }
      function escAttr(s) {
        return String(s).replace(/"/g,"&quot;");
      }

      /* ---------- eventos ---------- */
      document.getElementById("attr-new-btn").addEventListener("click", function () { showForm(-1); });
      document.getElementById("attr-cancel-btn").addEventListener("click", showList);
      document.getElementById("attr-cancel-btn2").addEventListener("click", showList);
      document.getElementById("attr-save-btn").addEventListener("click", saveAttribute);
      document.getElementById("attr-add-value-btn").addEventListener("click", promptAddValue);

      // re-render al cambiar tipo (para mostrar/ocultar color swatch)
      document.getElementById("attr-tipo").addEventListener("change", renderValueRows);

      // eliminar valor desde la lista
      valuesList.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-val-del]");
        if (btn) {
          pendingValues.splice(Number(btn.dataset.valDel), 1);
          renderValueRows();
        }
      });

      // editar / eliminar atributo desde tabla
      tbody.addEventListener("click", function (e) {
        var editBtn = e.target.closest("[data-attr-edit]");
        var delBtn  = e.target.closest("[data-attr-del]");
        if (editBtn) { showForm(Number(editBtn.dataset.attrEdit)); }
        if (delBtn) {
          var i = Number(delBtn.dataset.attrDel);
          if (confirm('¿Eliminar el atributo "' + attributes[i].nombre + '" y todos sus valores?')) {
            attributes.splice(i, 1);
            save();
            renderList();
          }
        }
      });

      /* ---------- init ---------- */
      load();
      renderList();
    })();
  </script>
</body>
</html>
"""
