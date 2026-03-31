from __future__ import annotations

import json
from html import escape

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

from fastapi_modulo.modulos_sipet.pwa.servicios.pwa_runtime_service import (
    build_manifest_payload,
    build_offline_page,
    build_service_worker_script,
    collect_module_pwa_capabilities,
    get_pwa_logo_url,
    load_pwa_settings,
    PWA_ASSETS_DIR,
    resolve_pwa_logo_path,
    save_pwa_settings,
)
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_admin_or_superadmin
from fastapi_modulo.modulos_sipet.web.servicios.branding_upload_service import save_branding_upload

router = APIRouter()


def _build_status_cards(settings: dict) -> str:
    rows = [
        ("Manifest", "/manifest.webmanifest"),
        ("Service worker", "/sw.js"),
        ("Pantalla offline", settings["offline_url"]),
        ("Inicio", settings["start_url"]),
        ("Scope", settings["scope"]),
        ("Modo", settings["display"]),
    ]
    return "".join(
        f'<article style="border:1px solid #e2e8f0;border-radius:12px;padding:12px;background:#fff;color:#0f172a;">'
        f'<strong style="display:block;margin-bottom:4px;">{escape(label)}</strong>'
        f'<span style="color:#475569;word-break:break-all;">{escape(value)}</span>'
        f"</article>"
        for label, value in rows
    )


def _build_settings_form(settings: dict) -> str:
    settings_json = json.dumps(settings, ensure_ascii=True)
    checked = "checked" if settings.get("enabled") else ""
    capabilities = collect_module_pwa_capabilities()
    logo_url = get_pwa_logo_url(settings)
    logo_preview = (
        f'<img src="{logo_url}" alt="Logo de inicio PWA" style="max-width:160px;max-height:96px;object-fit:contain;">'
        if logo_url
        else '<div style="width:160px;height:96px;border:1px dashed #cbd5e1;border-radius:12px;display:grid;place-items:center;color:#94a3b8;">Sin logo</div>'
    )
    def _feature_card(feature: dict) -> str:
        description_html = (
            f'<p style="margin:6px 0 0;color:#64748b;">{escape(feature["description"])}</p>'
            if feature["description"]
            else ""
        )
        return (
            f'<div style="padding:10px 12px;border-radius:10px;background:#f8fafc;border:1px solid #e2e8f0;">'
            f'<strong style="display:block;color:#0f172a;">{escape(feature["label"])}</strong>'
            f'<span style="display:block;color:#475569;">{escape(feature["route"])}</span>'
            f"{description_html}"
            "</div>"
        )
    module_cards = "".join(
        (
            '<article style="border:1px solid #e2e8f0;border-radius:14px;padding:14px;background:#fff;display:grid;gap:10px;">'
            f'<div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">'
            f'<div><strong style="display:block;color:#0f172a;">{escape(module["module_label"])}</strong>'
            f'<span style="display:block;color:#64748b;font-size:.92rem;">{escape(module["module_key"])}</span></div>'
            f'<span style="color:#475569;font-size:.92rem;">{len(module["features"])} funciones · {len(module["shortcuts"])} accesos</span>'
            '</div>'
            + (
                '<div style="display:grid;gap:8px;">'
                + "".join(_feature_card(feature) for feature in module["features"])
                + '</div>'
            if module["features"] else '<p style="margin:0;color:#64748b;">Este módulo no declaró funciones visuales para la PWA.</p>')
            + '</article>'
        )
        for module in capabilities["modules"]
    ) or '<article style="border:1px dashed #cbd5e1;border-radius:14px;padding:18px;background:#fff;color:#64748b;">Ningún módulo habilitado ha declarado extensiones PWA todavía.</article>'
    shortcut_preview = "".join(
        f'<li><strong>{escape(item["module_label"])}</strong>: {escape(item["name"])} <span style="color:#64748b;">{escape(item["url"])}</span></li>'
        for item in capabilities["shortcuts"]
    ) or "<li>Sin accesos rápidos declarados.</li>"
    contract_example = escape(
        json.dumps(
            {
                "pwa": {
                    "features": [
                        {
                            "key": "dashboard",
                            "label": "Dashboard",
                            "description": "Vista optimizada para uso móvil",
                            "route": "/mi-modulo/dashboard",
                            "offline_capable": False,
                        }
                    ],
                    "shortcuts": [
                        {
                            "name": "Abrir dashboard",
                            "short_name": "Dashboard",
                            "url": "/mi-modulo/dashboard",
                        }
                    ],
                    "precache_urls": ["/mi-modulo/dashboard"],
                }
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return f"""
    <section style="display:grid;gap:16px;max-width:980px;">
      <section style="background:#fff;border:1px solid #dbe3ef;border-radius:16px;padding:18px;display:grid;gap:14px;">
        <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;">
          <div>
            <h3 style="margin:0;color:#0f172a;font-size:1.12rem;">Progressive Web App</h3>
            <p style="margin:6px 0 0;color:#475569;">Configuración independiente del módulo PWA para manifest, service worker y experiencia instalable.</p>
          </div>
          <span style="display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border-radius:999px;background:#ecfdf3;color:#166534;font-weight:700;">
            <span style="width:8px;height:8px;border-radius:999px;background:#16a34a;"></span>
            Activo en runtime
          </span>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;">
          {_build_status_cards(settings)}
        </div>
      </section>
      <section style="background:#fff;border:1px solid #dbe3ef;border-radius:16px;padding:18px;display:grid;gap:16px;">
        <div>
          <h3 style="margin:0;color:#0f172a;font-size:1.05rem;">Extensiones aportadas por módulos</h3>
          <p style="margin:6px 0 0;color:#475569;">Cada módulo declara en su propio <code>__manifest__.py</code> qué rutas y accesos rápidos quiere aportar a la experiencia PWA.</p>
        </div>
        <div style="display:grid;gap:12px;">{module_cards}</div>
        <div style="border:1px solid #e2e8f0;border-radius:14px;padding:14px;background:#f8fafc;">
          <strong style="display:block;color:#0f172a;margin-bottom:8px;">Accesos rápidos actuales del manifest</strong>
          <ul style="margin:0 0 0 18px;padding:0;display:grid;gap:6px;color:#0f172a;">{shortcut_preview}</ul>
        </div>
        <div style="border:1px solid #e2e8f0;border-radius:14px;padding:14px;background:#0f172a;color:#e2e8f0;">
          <strong style="display:block;margin-bottom:8px;">Contrato por módulo</strong>
          <p style="margin:0 0 10px;color:#cbd5e1;">Ejemplo para declarar funcionalidad PWA directamente desde el manifest del módulo.</p>
          <pre style="margin:0;overflow:auto;white-space:pre-wrap;font-size:.88rem;line-height:1.5;">{contract_example}</pre>
        </div>
      </section>
      <section style="background:#fff;border:1px solid #dbe3ef;border-radius:16px;padding:18px;display:grid;gap:16px;">
        <div>
          <h3 style="margin:0;color:#0f172a;font-size:1.05rem;">Ajustes</h3>
          <p style="margin:6px 0 0;color:#475569;">Estos valores alimentan el manifest publicado en <code>/manifest.webmanifest</code> y el service worker en <code>/sw.js</code>.</p>
        </div>
        <section style="display:grid;grid-template-columns:240px minmax(0,1fr);gap:16px;align-items:start;padding:16px;border:1px solid #e2e8f0;border-radius:14px;background:#f8fafc;">
          <div style="display:grid;gap:10px;justify-items:start;">
            <strong style="color:#0f172a;">Logo de inicio</strong>
            <div id="pwa-logo-preview">{logo_preview}</div>
          </div>
          <div style="display:grid;gap:10px;">
            <p style="margin:0;color:#475569;">Se usa para la pantalla de inicio/offline de la PWA. El archivo queda almacenado dentro del módulo <code>pwa</code>.</p>
            <div style="display:flex;gap:10px;flex-wrap:wrap;">
              <input id="pwa-logo-input" type="file" accept="image/png,image/jpeg,image/webp,image/x-icon" style="max-width:100%;">
              <button id="pwa-logo-upload" type="button" style="display:inline-flex;align-items:center;justify-content:center;padding:10px 14px;border-radius:10px;border:1px solid #0f172a;background:#fff;color:#0f172a;font-weight:700;cursor:pointer;">Subir logo</button>
            </div>
            <span id="pwa-logo-status" style="color:#64748b;">{escape(logo_url or "Sin logo configurado")}</span>
          </div>
        </section>
        <form id="pwa-settings-form" style="display:grid;gap:14px;">
          <label style="display:flex;align-items:center;gap:10px;font-weight:600;color:#0f172a;">
            <input type="checkbox" name="enabled" {checked}>
            Habilitar PWA en la shell principal
          </label>
          <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;">
            <label style="display:grid;gap:6px;color:#0f172a;">
              <span>Nombre</span>
              <input name="app_name" value="{escape(settings["app_name"])}" style="height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px;">
            </label>
            <label style="display:grid;gap:6px;color:#0f172a;">
              <span>Nombre corto</span>
              <input name="short_name" value="{escape(settings["short_name"])}" style="height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px;">
            </label>
          </div>
          <label style="display:grid;gap:6px;color:#0f172a;">
            <span>Descripción</span>
            <textarea name="description" rows="3" style="border:1px solid #cbd5e1;border-radius:10px;padding:10px 12px;resize:vertical;">{escape(settings["description"])}</textarea>
          </label>
          <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;">
            <label style="display:grid;gap:6px;color:#0f172a;">
              <span>Start URL</span>
              <input name="start_url" value="{escape(settings["start_url"])}" style="height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px;">
            </label>
            <label style="display:grid;gap:6px;color:#0f172a;">
              <span>Scope</span>
              <input name="scope" value="{escape(settings["scope"])}" style="height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px;">
            </label>
            <label style="display:grid;gap:6px;color:#0f172a;">
              <span>Offline URL</span>
              <input name="offline_url" value="{escape(settings["offline_url"])}" style="height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px;">
            </label>
          </div>
          <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;">
            <label style="display:grid;gap:6px;color:#0f172a;">
              <span>Display</span>
              <select name="display" style="height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px;background:#fff;">
                <option value="standalone" {"selected" if settings["display"] == "standalone" else ""}>standalone</option>
                <option value="minimal-ui" {"selected" if settings["display"] == "minimal-ui" else ""}>minimal-ui</option>
                <option value="fullscreen" {"selected" if settings["display"] == "fullscreen" else ""}>fullscreen</option>
                <option value="browser" {"selected" if settings["display"] == "browser" else ""}>browser</option>
              </select>
            </label>
            <label style="display:grid;gap:6px;color:#0f172a;">
              <span>Theme color</span>
              <input name="theme_color" value="{escape(settings["theme_color"])}" style="height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px;">
            </label>
            <label style="display:grid;gap:6px;color:#0f172a;">
              <span>Background color</span>
              <input name="background_color" value="{escape(settings["background_color"])}" style="height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px;">
            </label>
          </div>
          <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;">
            <label style="display:grid;gap:6px;color:#0f172a;">
              <span>Color de fondo inicial</span>
              <input name="background_color_start" value="{escape(settings["background_color_start"])}" style="height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px;">
            </label>
            <label style="display:grid;gap:6px;color:#0f172a;">
              <span>Color de fondo final</span>
              <input name="background_color_end" value="{escape(settings["background_color_end"])}" style="height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px;">
            </label>
          </div>
          <div style="height:120px;border-radius:16px;border:1px solid #cbd5e1;background:linear-gradient(180deg, {escape(settings["background_color_start"])}, {escape(settings["background_color_end"])});display:grid;place-items:center;color:#fff;font-weight:700;">
            Vista previa de fondo
          </div>
          <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap;">
            <span id="pwa-settings-status" style="color:#475569;">Ultima actualización: {escape(settings.get("updated_at") or "sin cambios guardados")}</span>
            <div style="display:flex;gap:10px;flex-wrap:wrap;">
              <a href="/manifest.webmanifest" target="_blank" rel="noreferrer" style="display:inline-flex;align-items:center;justify-content:center;padding:10px 14px;border-radius:10px;border:1px solid #cbd5e1;background:#fff;color:#0f172a;font-weight:700;text-decoration:none;">Ver manifest</a>
              <button type="submit" style="display:inline-flex;align-items:center;justify-content:center;padding:10px 16px;border-radius:10px;border:1px solid #0f172a;background:#0f172a;color:#fff;font-weight:700;cursor:pointer;">Guardar</button>
            </div>
          </div>
        </form>
      </section>
      <script>
      (function() {{
        const form = document.getElementById('pwa-settings-form');
        const status = document.getElementById('pwa-settings-status');
        const logoInput = document.getElementById('pwa-logo-input');
        const logoUpload = document.getElementById('pwa-logo-upload');
        const logoStatus = document.getElementById('pwa-logo-status');
        const logoPreview = document.getElementById('pwa-logo-preview');
        const initialSettings = {settings_json};
        if (!form) return;
        if (logoUpload && logoInput) {{
          logoUpload.addEventListener('click', async function () {{
            if (!logoInput.files || !logoInput.files[0]) {{
              logoStatus.textContent = 'Selecciona un archivo antes de subirlo.';
              return;
            }}
            const formData = new FormData();
            formData.append('file', logoInput.files[0]);
            logoStatus.textContent = 'Subiendo logo...';
            try {{
              const response = await fetch('/api/ajustes/pwa/logo', {{
                method: 'POST',
                credentials: 'same-origin',
                body: formData
              }});
              const data = await response.json();
              if (!response.ok || data.success === false) {{
                throw new Error(data.error || 'No se pudo subir el logo');
              }}
              const bust = data.logo_url + '?v=' + Date.now();
              logoPreview.innerHTML = '<img src="' + bust + '" alt="Logo de inicio PWA" style="max-width:160px;max-height:96px;object-fit:contain;">';
              logoStatus.textContent = 'Logo actualizado.';
            }} catch (error) {{
              logoStatus.textContent = error.message || 'No se pudo subir el logo';
            }}
          }});
        }}
        form.addEventListener('submit', async function (event) {{
          event.preventDefault();
          const formData = new FormData(form);
          const payload = Object.assign({{}}, initialSettings, {{
            enabled: formData.get('enabled') === 'on',
            app_name: String(formData.get('app_name') || '').trim(),
            short_name: String(formData.get('short_name') || '').trim(),
            description: String(formData.get('description') || '').trim(),
            start_url: String(formData.get('start_url') || '').trim(),
            scope: String(formData.get('scope') || '').trim(),
            offline_url: String(formData.get('offline_url') || '').trim(),
            display: String(formData.get('display') || '').trim(),
            theme_color: String(formData.get('theme_color') || '').trim(),
            background_color: String(formData.get('background_color') || '').trim(),
            background_color_start: String(formData.get('background_color_start') || '').trim(),
            background_color_end: String(formData.get('background_color_end') || '').trim()
          }});
          status.textContent = 'Guardando configuración PWA...';
          try {{
            const response = await fetch('/api/ajustes/pwa', {{
              method: 'POST',
              credentials: 'same-origin',
              headers: {{
                'Accept': 'application/json',
                'Content-Type': 'application/json'
              }},
              body: JSON.stringify(payload)
            }});
            const data = await response.json();
            if (!response.ok || data.success === false) {{
              throw new Error(data.error || 'No se pudo guardar la configuración PWA');
            }}
            status.textContent = 'Guardado correctamente. Recarga la página si quieres refrescar el meta theme-color actual.';
          }} catch (error) {{
            status.textContent = error.message || 'No se pudo guardar la configuración PWA';
            status.style.color = '#b91c1c';
          }}
        }});
      }})();
      </script>
    </section>
    """


@router.get("/ajustes/pwa", response_class=HTMLResponse)
def pwa_settings_page(request: Request) -> HTMLResponse:
    require_admin_or_superadmin(request)
    settings = load_pwa_settings()
    return render_backend_page(
        request,
        title="PWA",
        description="Configuración independiente del módulo Progressive Web App.",
        content=_build_settings_form(settings),
        hide_floating_actions=True,
        show_page_header=True,
    )


@router.get("/api/ajustes/pwa")
def pwa_settings_state(request: Request) -> JSONResponse:
    require_admin_or_superadmin(request)
    settings = load_pwa_settings()
    return JSONResponse({"success": True, "settings": settings, "capabilities": collect_module_pwa_capabilities(), "logo_url": get_pwa_logo_url(settings)})


@router.post("/api/ajustes/pwa")
async def pwa_settings_update(request: Request) -> JSONResponse:
    require_admin_or_superadmin(request)
    payload = await request.json()
    settings = save_pwa_settings(payload if isinstance(payload, dict) else {})
    return JSONResponse({"success": True, "settings": settings})


@router.get("/api/ajustes/pwa/logo", include_in_schema=False)
def pwa_logo_file() -> Response:
    settings = load_pwa_settings()
    filename = str(settings.get("splash_logo_filename") or "").strip()
    if not filename:
        raise HTTPException(status_code=404, detail="Logo no configurado")
    path = resolve_pwa_logo_path(filename)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Logo no encontrado")
    return FileResponse(path)


@router.post("/api/ajustes/pwa/logo")
async def pwa_logo_upload(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    require_admin_or_superadmin(request)
    settings = load_pwa_settings()
    previous_filename = str(settings.get("splash_logo_filename") or "").strip()
    payload = await save_branding_upload(
        file,
        slot="logo",
        image_dir=str(PWA_ASSETS_DIR),
        previous_filename=previous_filename,
    )
    settings = save_pwa_settings({"splash_logo_filename": payload["filename"]})
    return JSONResponse({"success": True, "settings": settings, "logo_url": get_pwa_logo_url(settings)})


@router.get("/manifest.webmanifest", include_in_schema=False)
def pwa_manifest() -> Response:
    payload = build_manifest_payload()
    return Response(json.dumps(payload, ensure_ascii=False), media_type="application/manifest+json")


@router.get("/sw.js", include_in_schema=False)
def pwa_service_worker() -> Response:
    return Response(
        build_service_worker_script(),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@router.get("/offline", include_in_schema=False, response_class=HTMLResponse)
def pwa_offline() -> HTMLResponse:
    return HTMLResponse(build_offline_page(), headers={"Cache-Control": "no-cache"})
