from __future__ import annotations


def gestion_html() -> str:
    return _HTML


_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" type="image/png" href="/static/imagenes/tu-negocio.png" />
  <title>Administrar tiendas</title>
  <style>
    html, body {
      margin: 0;
      padding: 0;
      background: #f5f6f8;
      font-family: Arial, sans-serif;
      color: #1f2937;
    }

    * {
      box-sizing: border-box;
    }

__BACKEND_SHARED_SIDEBAR_CSS__

__BACKEND_SHARED_FORM_BASE_CSS__

    .business-type-tools {
      margin-top: 8px;
      display: grid;
      gap: 6px;
    }

    .business-type-btn {
      width: fit-content;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      background: #fff;
      color: #1f2937;
      font-size: 0.82rem;
      font-weight: 700;
      padding: 6px 10px;
      cursor: pointer;
    }

    .business-type-description {
      font-size: 0.83rem;
      color: #475569;
    }

    .business-type-panel {
      margin-top: 10px;
      border: 1px solid #dbe2ea;
      border-radius: 10px;
      background: #f8fafc;
      padding: 10px;
      display: grid;
      gap: 8px;
    }

    .business-type-panel[hidden] {
      display: none;
    }

    .business-type-grid {
      display: grid;
      grid-template-columns: 1fr 160px;
      gap: 8px;
    }

    .business-type-textarea {
      width: 100%;
      min-height: 76px;
      border: 1px solid #eadfe2;
      border-radius: 10px;
      padding: 8px 10px;
      font-size: 0.95rem;
      outline: none;
      background: #fff;
      color: #1f2937;
      resize: vertical;
    }

    .business-type-actions {
      display: flex;
      gap: 8px;
    }

    .business-type-message {
      margin: 0;
      font-size: 0.8rem;
      font-weight: 700;
      min-height: 1.2em;
    }

    .store-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }

    .store-table-note {
      margin: 0 0 16px;
      color: #6b7280;
      font-size: 0.88rem;
    }

    .admin-user-tools {
      margin-top: 8px;
      display: grid;
      gap: 6px;
    }

    .admin-user-note {
      margin: 0;
      font-size: 0.82rem;
      color: #475569;
    }

    .admin-user-btn {
      width: fit-content;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      background: #fff;
      color: #1f2937;
      font-size: 0.82rem;
      font-weight: 700;
      padding: 6px 10px;
      cursor: pointer;
    }

    .logo-box {
      border: 1px solid #e7ecef;
      border-radius: 10px;
      min-height: 260px;
      background: #f8fbfd;
      padding: 14px;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      align-items: center;
      text-align: center;
      gap: 14px;
    }

    .logo-preview {
      width: 146px;
      height: 146px;
      border-radius: 2px;
      border: 1px solid #e5e7eb;
      background: #ffffff;
      color: #fff;
      font-size: 2rem;
      display: grid;
      place-items: center;
      margin-top: 4px;
      overflow: hidden;
    }

    .logo-preview-wrap {
      position: relative;
      width: 146px;
      height: 182px;
      display: flex;
      align-items: flex-start;
      justify-content: center;
    }

    .logo-preview img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .logo-actions {
      position: absolute;
      left: 50%;
      bottom: 0;
      transform: translateX(-50%);
      display: flex;
      gap: 8px;
      z-index: 3;
    }

    .logo-action-btn {
      width: 34px;
      height: 34px;
      border: 1px solid #d9dee3;
      border-radius: 999px;
      background: #fff;
      color: #4b5563;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
      line-height: 1;
    }

    .logo-action-btn:hover {
      background: #f3f4f6;
    }

    .logo-input {
      display: none;
    }

    .logo-urls {
      width: 100%;
      margin-top: 6px;
      text-align: left;
      display: grid;
      gap: 10px;
    }

    .url-item {
      display: grid;
      gap: 4px;
    }

    .url-label {
      font-size: 0.86rem;
      font-weight: 700;
      color: #4b5563;
      text-transform: lowercase;
    }

    .url-value {
      font-size: 0.9rem;
      color: #2563eb;
      text-decoration: none;
      word-break: break-all;
    }

    .url-value:hover {
      text-decoration: underline;
    }

    .placeholder {
      color: #6b7280;
      font-size: 0.92rem;
      margin: 0;
    }

    .avan-grid {
      display: grid;
      gap: 14px;
      max-width: 760px;
    }

    .avan-row {
      display: grid;
      grid-template-columns: 320px 1fr;
      align-items: center;
      gap: 10px;
    }

    .avan-label {
      font-size: 1rem;
      font-weight: 700;
      color: #2f343b;
      margin: 0;
    }

    .avan-label .hint {
      color: #1f9bb8;
      font-size: 1rem;
      margin-left: 6px;
    }

    .avan-check {
      width: 28px;
      height: 28px;
      accent-color: #5b8fab;
      cursor: pointer;
    }

    .avan-input {
      width: 100%;
      height: 52px;
      border: 1px solid #eadfe2;
      border-radius: 18px;
      background: #f2e9eb;
      padding: 0 14px;
      font-size: 1.05rem;
      color: #374151;
      outline: none;
    }

    @media (max-width: 920px) {
      .section-grid {
        grid-template-columns: 1fr;
      }

      .avan-row {
        grid-template-columns: 1fr;
      }
    }

    /* Publicidad */
    .pub-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      padding: 4px 0;
    }

    .pub-card {
      border: 1px solid #e6e8ee;
      border-radius: 10px;
      overflow: hidden;
      background: #fff;
    }

    .pub-card-header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 16px;
      background: #f7f8fa;
      border-bottom: 1px solid #e6e8ee;
    }

    .pub-card-icon {
      font-size: 1.2rem;
    }

    .pub-card-title {
      margin: 0;
      font-size: 0.95rem;
      font-weight: 600;
      color: #1f2937;
    }

    .pub-card-body {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .pub-dates {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    @media (max-width: 720px) {
      .pub-grid {
        grid-template-columns: 1fr;
      }
      .pub-dates {
        grid-template-columns: 1fr;
      }
    }

    /* Categorías */
    .panel-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 10px;
    }
    .panel-header-row h2 {
      margin: 0;
    }
    .action-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      background: #1a6b3c;
      color: #fff;
      border: none;
      border-radius: 7px;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }
    .action-btn:hover { background: #155c32; }
    .action-btn--secondary {
      background: #f3f4f6;
      color: #374151;
    }
    .action-btn--secondary:hover { background: #e5e7eb; }
    .action-btn--danger {
      background: #fee2e2;
      color: #b91c1c;
    }
    .action-btn--danger:hover { background: #fecaca; }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
    }
    .data-table th {
      text-align: left;
      padding: 10px 12px;
      background: #f7f8fa;
      border-bottom: 2px solid #e6e8ee;
      font-weight: 600;
      color: #374151;
    }
    .data-table td {
      padding: 10px 12px;
      border-bottom: 1px solid #f0f1f3;
      vertical-align: middle;
      color: #1f2937;
    }
    .data-table tbody tr:last-child td { border-bottom: none; }
    .data-table tbody tr:hover td { background: #f9fafb; }
    .empty-row td { border-bottom: none !important; }

    /* Atributos */
    .attr-form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 28px;
      align-items: start;
    }
    @media (max-width: 800px) {
      .attr-form-grid { grid-template-columns: 1fr; }
    }
    .attr-values-col {
      background: #f7f8fa;
      border: 1px solid #e6e8ee;
      border-radius: 10px;
      padding: 16px;
    }
    .attr-values-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }
    .attr-values-header label {
      font-weight: 600;
      color: #374151;
      font-size: 0.875rem;
    }
    .attr-values-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 320px;
      overflow-y: auto;
    }
    .attr-value-row {
      display: flex;
      align-items: center;
      gap: 8px;
      background: #fff;
      border: 1px solid #e6e8ee;
      border-radius: 7px;
      padding: 6px 10px;
    }
    .attr-value-row .attr-color-swatch {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      border: 1px solid #d1d5db;
      flex-shrink: 0;
      cursor: pointer;
    }
    .attr-value-row .attr-val-name {
      flex: 1;
      font-size: 0.875rem;
      color: #1f2937;
    }
    .attr-value-row .attr-val-del {
      background: none;
      border: none;
      cursor: pointer;
      color: #9ca3af;
      font-size: 1rem;
      line-height: 1;
      padding: 2px 4px;
      border-radius: 4px;
      transition: color 0.15s;
    }
    .attr-value-row .attr-val-del:hover { color: #b91c1c; }
    .attr-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 0.78rem;
      font-weight: 500;
      background: #e5e7eb;
      color: #374151;
      margin: 1px 2px;
    }
    .attr-badge-color {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 1px solid rgba(0,0,0,.15);
      flex-shrink: 0;
    }
  </style>
</head>
<body>
__BACKEND_SHARED_SIDEBAR_HTML__

  <main class="page">
    <h1 class="title">Administrar tiendas</h1>
    <p class="subtitle">Dar de alta tiendas con sus permisos y roles</p>

    <div class="notebook">
      <div class="notebook-tabs" role="tablist">
        <button class="notebook-tab active" role="tab" aria-selected="true"  aria-controls="tab-panel-1" id="tab-1" type="button">Tiendas</button>
        <button class="notebook-tab"        role="tab" aria-selected="false" aria-controls="tab-panel-2" id="tab-2" type="button">Acceso a AVAN</button>
        <button class="notebook-tab"        role="tab" aria-selected="false" aria-controls="tab-panel-3" id="tab-3" type="button">Publicidad</button>
        <button class="notebook-tab"        role="tab" aria-selected="false" aria-controls="tab-panel-4" id="tab-4" type="button">Institución financiera</button>
        <button class="notebook-tab"        role="tab" aria-selected="false" aria-controls="tab-panel-5" id="tab-5" type="button">Categorías</button>
        <button class="notebook-tab"        role="tab" aria-selected="false" aria-controls="tab-panel-6" id="tab-6" type="button">Atributos</button>
      </div>

      <div class="notebook-panel" id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1">
        <div id="store-list-view">
          <div class="store-toolbar">
            <h2 style="margin:0;">Tiendas registradas</h2>
            <button class="action-btn" id="store-new-btn" type="button">+ Nueva tienda</button>
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
                <td colspan="5" style="text-align:center;color:#9ca3af;padding:32px;">
                  No hay tiendas registradas. Haz clic en <strong>+ Nueva tienda</strong> para agregar la primera.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div id="store-form-view" hidden>
          <div class="panel-header-row">
            <h2 id="store-form-title">Nueva tienda</h2>
            <button class="action-btn action-btn--secondary" id="store-cancel-btn" type="button">← Volver a lista</button>
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
                  <button class="action-btn" id="store-save-btn" type="button">Guardar tienda</button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>

      <div class="notebook-panel" id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" hidden>
        <section class="section">
          <h2>Acceso a AVAN</h2>
          <div class="avan-grid">
            <div class="avan-row">
              <p class="avan-label">Active</p>
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
              <p class="avan-label">Sistema de referidos</p>
              <input class="avan-input" id="store-referrals" type="text" placeholder="Configuración de referidos" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Sistema de cita</p>
              <input class="avan-input" id="store-appointments" type="text" placeholder="Configuración de citas" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Sistema de cupones</p>
              <input class="avan-input" id="store-coupons" type="text" placeholder="Configuración de cupones" />
            </div>
            <div class="avan-row">
              <p class="avan-label">WhatsApp</p>
              <input class="avan-input" id="store-whatsapp" type="text" placeholder="Número o integración" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Usuarios internos</p>
              <input class="avan-input" id="max-internal-users" type="number" min="0" step="1" placeholder="Máximo de empleados" oninput="localStorage.setItem('multitienda_max_internal_users', this.value)" />
            </div>
            <div class="avan-row">
              <p class="avan-label">Usuarios de portal</p>
              <input class="avan-input" id="max-portal-users" type="number" min="0" step="1" placeholder="Máximo de clientes" />
            </div>
          </div>
        </section>
      </div>

      <div class="notebook-panel" id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" hidden>
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

      <div class="notebook-panel" id="tab-panel-4" role="tabpanel" aria-labelledby="tab-4" hidden>
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
      <div class="notebook-panel" id="tab-panel-5" role="tabpanel" aria-labelledby="tab-5" hidden>

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
                <td colspan="5" style="text-align:center;color:#9ca3af;padding:32px;">
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
            <label for="cat-nombre">Nombre <span style="color:#e53e3e">*</span></label>
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
            <div class="photo-box" id="cat-img-box" style="width:140px;height:140px;cursor:pointer;" onclick="document.getElementById('cat-img-input').click()">
              <img id="cat-img-preview" src="/static/imagenes/banner.png"
                   style="width:100%;height:100%;object-fit:cover;border-radius:8px;" alt="Imagen categoría" />
            </div>
            <input type="file" id="cat-img-input" accept="image/*" style="display:none" />
            <p style="font-size:0.8rem;color:#6b7280;margin-top:4px;">Haz clic en la imagen para cambiarla.</p>
          </div>

          <div class="field" style="display:flex;align-items:center;gap:10px;">
            <input type="checkbox" id="cat-activa" checked style="width:18px;height:18px;accent-color:#1a6b3c;" />
            <label for="cat-activa" style="margin:0;cursor:pointer;">Categoría activa (visible en la tienda)</label>
          </div>

          <div style="display:flex;gap:12px;margin-top:20px;">
            <button class="action-btn" id="cat-save-btn" type="button">Guardar categoría</button>
            <button class="action-btn action-btn--secondary" id="cat-cancel-btn2" type="button">Cancelar</button>
          </div>
        </div>

      </div>

      <!-- ===================== TAB 6: Atributos ===================== -->
      <div class="notebook-panel" id="tab-panel-6" role="tabpanel" aria-labelledby="tab-6" hidden>

        <!-- Vista: lista de atributos -->
        <div id="attr-list-view">
          <div class="panel-header-row">
            <h2>Atributos de productos</h2>
            <button class="action-btn" id="attr-new-btn" type="button">+ Nuevo atributo</button>
          </div>
          <p style="color:#6b7280;font-size:0.875rem;margin:-8px 0 16px;">
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
                <td colspan="4" style="text-align:center;color:#9ca3af;padding:32px;">
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
                <label for="attr-nombre">Nombre del atributo <span style="color:#e53e3e">*</span></label>
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
                <input type="checkbox" id="attr-requerido" style="width:18px;height:18px;accent-color:#1a6b3c;" />
                <label for="attr-requerido" style="margin:0;cursor:pointer;">Atributo requerido en productos</label>
              </div>
            </div>

            <div class="attr-values-col">
              <div class="attr-values-header">
                <label>Valores del atributo</label>
                <button class="action-btn" id="attr-add-value-btn" type="button" style="padding:5px 12px;font-size:0.8rem;">+ Agregar valor</button>
              </div>
              <div id="attr-values-list" class="attr-values-list">
                <p id="attr-values-empty" style="color:#9ca3af;font-size:0.85rem;padding:12px 0;">
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
  </main>
  <script src="/static/js/backend-sidebar-core.js"></script>
  <script>
    (function () {
      if (window.initBackendSidebarCore) {
        window.initBackendSidebarCore();
      }
    })();

    (function () {
      const STORAGE_KEY = "multitienda_stores";
      const listView = document.getElementById("store-list-view");
      const formView = document.getElementById("store-form-view");
      const tbody = document.getElementById("store-tbody");
      const emptyRow = document.getElementById("store-empty-row");
      const newBtn = document.getElementById("store-new-btn");
      const cancelBtn = document.getElementById("store-cancel-btn");
      const saveBtn = document.getElementById("store-save-btn");
      const formTitle = document.getElementById("store-form-title");
      const nameInput = document.getElementById("store-name");
      const typeSelect = document.getElementById("store-type");
      const adminSelect = document.getElementById("store-admin");
      const membershipInput = document.getElementById("store-membership");
      const activeCheckbox = document.getElementById("store-is-active");
      const featuredCheckbox = document.getElementById("store-is-featured");
      const inventoryCheckbox = document.getElementById("store-inventory-enabled");
      const validityInput = document.getElementById("store-validity");
      const referralsInput = document.getElementById("store-referrals");
      const appointmentsInput = document.getElementById("store-appointments");
      const couponsInput = document.getElementById("store-coupons");
      const whatsappInput = document.getElementById("store-whatsapp");
      const maxInternalUsersInput = document.getElementById("max-internal-users");
      const maxPortalUsersInput = document.getElementById("max-portal-users");
      let stores = [];
      let editIndex = -1;

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
      }

      function showForm(index) {
        editIndex = typeof index === "number" ? index : -1;
        if (listView) listView.hidden = true;
        if (formView) formView.hidden = false;
        if (editIndex >= 0 && stores[editIndex]) {
          const item = stores[editIndex];
          if (formTitle) formTitle.textContent = "Editar tienda";
          if (nameInput) nameInput.value = item.name || "";
          if (typeSelect) typeSelect.value = item.typeCode || "";
          if (adminSelect) adminSelect.value = item.adminId || "";
          if (membershipInput) membershipInput.value = item.membership || "";
          if (activeCheckbox) activeCheckbox.checked = item.isActive !== false;
          if (featuredCheckbox) featuredCheckbox.checked = !!item.isFeatured;
          if (inventoryCheckbox) inventoryCheckbox.checked = !!item.inventoryEnabled;
          if (validityInput) validityInput.value = item.validity || "";
          if (referralsInput) referralsInput.value = item.referrals || "";
          if (appointmentsInput) appointmentsInput.value = item.appointments || "";
          if (couponsInput) couponsInput.value = item.coupons || "";
          if (whatsappInput) whatsappInput.value = item.whatsapp || "";
          if (maxInternalUsersInput) maxInternalUsersInput.value = item.maxInternalUsers || "";
          if (maxPortalUsersInput) maxPortalUsersInput.value = item.maxPortalUsers || "";
        } else {
          if (formTitle) formTitle.textContent = "Nueva tienda";
          if (nameInput) nameInput.value = "";
          if (typeSelect) typeSelect.value = "";
          if (adminSelect) adminSelect.value = "";
          if (membershipInput) membershipInput.value = "";
          if (activeCheckbox) activeCheckbox.checked = true;
          if (featuredCheckbox) featuredCheckbox.checked = true;
          if (inventoryCheckbox) inventoryCheckbox.checked = false;
          if (validityInput) validityInput.value = "";
          if (referralsInput) referralsInput.value = "";
          if (appointmentsInput) appointmentsInput.value = "";
          if (couponsInput) couponsInput.value = "";
          if (whatsappInput) whatsappInput.value = "";
          if (maxInternalUsersInput) maxInternalUsersInput.value = "";
          if (maxPortalUsersInput) maxPortalUsersInput.value = "";
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
            referrals: String(referralsInput && referralsInput.value || "").trim(),
            appointments: String(appointmentsInput && appointmentsInput.value || "").trim(),
            coupons: String(couponsInput && couponsInput.value || "").trim(),
            whatsapp: String(whatsappInput && whatsappInput.value || "").trim(),
            maxInternalUsers: String(maxInternalUsersInput && maxInternalUsersInput.value || "").trim(),
            maxPortalUsers: String(maxPortalUsersInput && maxPortalUsersInput.value || "").trim(),
          };
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
              store_name: payload.name,
              store_type: payload.typeCode,
              admin_user_id: payload.adminId,
              membership: payload.membership,
              is_active: payload.isActive,
              is_featured: payload.isFeatured,
              inventory_enabled: payload.inventoryEnabled,
              validity: payload.validity,
              referrals: payload.referrals,
              appointments: payload.appointments,
              coupons: payload.coupons,
              whatsapp: payload.whatsapp,
              max_internal_users: payload.maxInternalUsers,
              max_portal_users: payload.maxPortalUsers,
            })
          });
          const responsePayload = await response.json().catch(function () { return {}; });
          if (!response.ok) {
            throw new Error(responsePayload.detail || "No se pudo guardar la tienda.");
          }
          await loadStores();
          renderStores();
          showList();
      }

      if (saveBtn) {
        saveBtn.addEventListener("click", async function () {
          try {
            await persistStore();
          } catch (error) {
            window.alert(error && error.message ? error.message : "No se pudo guardar la tienda.");
          }
        });
      }

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
        showList();
      });
    })();

    (function () {
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
        message.style.color = "#b91c1c";
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
              message.style.color = "#166534";
              message.textContent = "Giro agregado correctamente.";
            }
            setTimeout(closePanel, 600);
          } catch (error) {
            if (message) {
              message.style.color = "#b91c1c";
              message.textContent = error && error.message ? error.message : "No se pudo guardar el giro.";
            }
          }
        });
      }

      loadCatalog();
    })();

    (function () {
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
          const response = await fetch("/multitienda/api/store-admin-users", { headers: { "Accept": "application/json" } });
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
    })();

    (function () {
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
    })();

  </script>
  <script src="/static/js/sidebar-theme-editor.js"></script>
  <script src="/static/js/backend-navbar.js"></script>
  <script>
    (function () {
      document.querySelectorAll(".notebook").forEach(function (notebook) {
        var tabs = notebook.querySelectorAll(".notebook-tab");
        var panels = notebook.querySelectorAll(".notebook-panel");

        function openTab(tab) {
          var panelId = tab.getAttribute("aria-controls");
          tabs.forEach(function (t) {
            t.classList.remove("active");
            t.setAttribute("aria-selected", "false");
          });
          panels.forEach(function (p) {
            p.hidden = true;
          });
          tab.classList.add("active");
          tab.setAttribute("aria-selected", "true");
          if (panelId) {
            var targetPanel = notebook.querySelector("#" + panelId);
            if (targetPanel) {
              targetPanel.hidden = false;
            }
          }
        }

        tabs.forEach(function (tab) {
          tab.addEventListener("click", function (event) {
            event.preventDefault();
            openTab(tab);
          });
        });

        var activeTab = notebook.querySelector(".notebook-tab.active") || tabs[0];
        if (activeTab) {
          openTab(activeTab);
        }
      });
    })();

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
      var imgInput    = document.getElementById("cat-img-input");
      var imgPreview  = document.getElementById("cat-img-preview");
      var DEFAULT_IMG = "/static/imagenes/banner.png";

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
            '<td><img src="' + (c.imagen || DEFAULT_IMG) + '" style="width:40px;height:40px;object-fit:cover;border-radius:6px;" /></td>' +
            '<td>' + escHtml(c.nombre) + '</td>' +
            '<td style="color:#6b7280;font-size:0.85rem;">' + escHtml(c.descripcion || "") + '</td>' +
            '<td>' + escHtml(padreNombre) + '</td>' +
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
        imgPreview.src = DEFAULT_IMG;
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
          imgPreview.src = c.imagen || DEFAULT_IMG;
        } else {
          formTitle.textContent = "Nueva categoría";
          document.getElementById("cat-nombre").value      = "";
          document.getElementById("cat-descripcion").value = "";
          padreSelect.value = "";
          document.getElementById("cat-activa").checked    = true;
          imgPreview.src = DEFAULT_IMG;
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
          imagen:      imgPreview.src !== window.location.href ? imgPreview.src : DEFAULT_IMG
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
        imgPreview.src = URL.createObjectURL(file);
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
            badges += '<span class="attr-badge" style="color:#6b7280;">+' + ((a.valores.length - 8)) + ' más</span>';
          }
          tr.innerHTML =
            '<td style="font-weight:600;">' + escHtml(a.nombre) + (a.requerido ? ' <span style="color:#e53e3e;font-size:0.8rem;" title="Requerido">●</span>' : "") + '</td>' +
            '<td style="color:#6b7280;font-size:0.85rem;">' + tipoLabel + '</td>' +
            '<td>' + (badges || '<span style="color:#9ca3af;font-size:0.82rem;">Sin valores</span>') + '</td>' +
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
