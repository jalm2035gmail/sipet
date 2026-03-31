from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi_modulo.core.module_registry import list_enabled_module_manifests


APP_ENV = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
RUNTIME_STORE_DIR = Path((os.environ.get("RUNTIME_STORE_DIR") or f"fastapi_modulo/runtime_store/{APP_ENV}").strip())
PWA_STORE_DIR = RUNTIME_STORE_DIR / "pwa"
PWA_SETTINGS_PATH = PWA_STORE_DIR / "settings.json"
PWA_ASSETS_DIR = PWA_STORE_DIR / "assets"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "enabled": True,
    "app_name": "SIPET",
    "short_name": "SIPET",
    "description": "Que bueno verte aqui",
    "start_url": "/web/inicio",
    "scope": "/",
    "display": "standalone",
    "theme_color": "#9a3412",
    "background_color": "#9a3412",
    "background_color_start": "#9a3412",
    "background_color_end": "#c2410c",
    "splash_logo_filename": "",
    "offline_url": "/offline",
    "updated_at": "",
}

DEFAULT_PWA_LOGO_URL = "/modulos_sipet/pwa/static/imagenes/cc.png"


def _clean_route(value: Any) -> str:
    route = str(value or "").strip()
    if not route.startswith("/"):
        return ""
    return route


def _normalize_hex_color(value: Any, fallback: str) -> str:
    color = str(value or "").strip()
    if len(color) == 7 and color.startswith("#"):
        return color
    return fallback


def _normalize_bool(value: Any, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return fallback


def _normalize_path(value: Any, fallback: str) -> str:
    candidate = str(value or "").strip()
    if not candidate.startswith("/"):
        return fallback
    return candidate


def _sanitize_settings(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    raw = payload or {}
    settings = dict(DEFAULT_SETTINGS)
    settings["enabled"] = _normalize_bool(raw.get("enabled"), settings["enabled"])
    settings["app_name"] = str(raw.get("app_name") or settings["app_name"]).strip() or settings["app_name"]
    settings["short_name"] = str(raw.get("short_name") or settings["short_name"]).strip() or settings["short_name"]
    settings["description"] = str(raw.get("description") or settings["description"]).strip() or settings["description"]
    settings["start_url"] = _normalize_path(raw.get("start_url"), settings["start_url"])
    settings["scope"] = _normalize_path(raw.get("scope"), settings["scope"])
    settings["offline_url"] = _normalize_path(raw.get("offline_url"), settings["offline_url"])
    display = str(raw.get("display") or settings["display"]).strip().lower()
    settings["display"] = display if display in {"standalone", "fullscreen", "minimal-ui", "browser"} else settings["display"]
    settings["theme_color"] = _normalize_hex_color(raw.get("theme_color"), settings["theme_color"])
    settings["background_color"] = _normalize_hex_color(raw.get("background_color"), settings["background_color"])
    settings["background_color_start"] = _normalize_hex_color(raw.get("background_color_start"), settings["background_color_start"])
    settings["background_color_end"] = _normalize_hex_color(raw.get("background_color_end"), settings["background_color_end"])
    settings["splash_logo_filename"] = str(raw.get("splash_logo_filename") or settings["splash_logo_filename"]).strip()
    settings["updated_at"] = str(raw.get("updated_at") or settings["updated_at"]).strip()
    return settings


def load_pwa_settings() -> Dict[str, Any]:
    if not PWA_SETTINGS_PATH.exists():
        return dict(DEFAULT_SETTINGS)
    try:
        payload = json.loads(PWA_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)
    return _sanitize_settings(payload if isinstance(payload, dict) else None)


def save_pwa_settings(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    current = load_pwa_settings()
    merged = dict(current)
    merged.update(payload or {})
    settings = _sanitize_settings(merged)
    settings["updated_at"] = datetime.utcnow().isoformat()
    PWA_STORE_DIR.mkdir(parents=True, exist_ok=True)
    PWA_SETTINGS_PATH.write_text(json.dumps(settings, ensure_ascii=True, indent=2), encoding="utf-8")
    return settings


def resolve_pwa_logo_path(filename: str) -> Path:
    return PWA_ASSETS_DIR / filename


def get_pwa_logo_url(settings: Dict[str, Any] | None = None) -> str:
    current = _sanitize_settings(settings or load_pwa_settings())
    filename = str(current.get("splash_logo_filename") or "").strip()
    if not filename:
        return DEFAULT_PWA_LOGO_URL
    path = resolve_pwa_logo_path(filename)
    if not path.exists():
        return DEFAULT_PWA_LOGO_URL
    return "/api/ajustes/pwa/logo"


def _normalize_pwa_shortcut(raw: Any, module_key: str, module_label: str) -> Dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    url = _clean_route(raw.get("url"))
    name = str(raw.get("name") or "").strip()
    if not url or not name:
        return None
    short_name = str(raw.get("short_name") or name).strip() or name
    return {
        "module_key": module_key,
        "module_label": module_label,
        "name": name,
        "short_name": short_name,
        "description": str(raw.get("description") or "").strip(),
        "url": url,
        "icon": str(raw.get("icon") or "").strip(),
        "offline_capable": _normalize_bool(raw.get("offline_capable"), False),
    }


def _normalize_pwa_feature(raw: Any, module_key: str, module_label: str) -> Dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    route = _clean_route(raw.get("route") or raw.get("url"))
    label = str(raw.get("label") or raw.get("name") or "").strip()
    if not route or not label:
        return None
    return {
        "module_key": module_key,
        "module_label": module_label,
        "key": str(raw.get("key") or f"{module_key}:{label.lower().replace(' ', '_')}").strip(),
        "label": label,
        "description": str(raw.get("description") or "").strip(),
        "route": route,
        "icon": str(raw.get("icon") or "").strip(),
        "offline_capable": _normalize_bool(raw.get("offline_capable"), False),
        "priority": int(raw.get("priority") or 100),
    }


def _normalize_precache_url(raw: Any) -> str:
    return _clean_route(raw)


def collect_module_pwa_capabilities() -> Dict[str, Any]:
    modules: list[Dict[str, Any]] = []
    shortcuts: list[Dict[str, Any]] = []
    features: list[Dict[str, Any]] = []
    precache_urls: list[str] = []
    for item in list_enabled_module_manifests():
        module_key = str(item.get("key") or "").strip()
        manifest = item.get("manifest") if isinstance(item.get("manifest"), dict) else {}
        pwa_contract = manifest.get("pwa") if isinstance(manifest.get("pwa"), dict) else {}
        module_label = str(manifest.get("label") or item.get("label") or module_key).strip() or module_key
        module_features = []
        module_shortcuts = []
        for raw_feature in pwa_contract.get("features") or []:
            feature = _normalize_pwa_feature(raw_feature, module_key, module_label)
            if feature is not None:
                module_features.append(feature)
                features.append(feature)
        for raw_shortcut in pwa_contract.get("shortcuts") or []:
            shortcut = _normalize_pwa_shortcut(raw_shortcut, module_key, module_label)
            if shortcut is not None:
                module_shortcuts.append(shortcut)
                shortcuts.append(shortcut)
        for raw_url in pwa_contract.get("precache_urls") or []:
            normalized = _normalize_precache_url(raw_url)
            if normalized:
                precache_urls.append(normalized)
        if module_features or module_shortcuts or precache_urls:
            modules.append(
                {
                    "module_key": module_key,
                    "module_label": module_label,
                    "route": str(item.get("route") or manifest.get("route") or "").strip(),
                    "features": sorted(module_features, key=lambda entry: (entry["priority"], entry["label"].lower())),
                    "shortcuts": sorted(module_shortcuts, key=lambda entry: entry["name"].lower()),
                }
            )
    deduped_precache = list(dict.fromkeys(url for url in precache_urls if url))
    shortcuts.sort(key=lambda entry: (entry["module_label"].lower(), entry["name"].lower()))
    features.sort(key=lambda entry: (entry["priority"], entry["module_label"].lower(), entry["label"].lower()))
    modules.sort(key=lambda entry: entry["module_label"].lower())
    return {
        "modules": modules,
        "features": features,
        "shortcuts": shortcuts,
        "precache_urls": deduped_precache,
    }


def build_manifest_payload(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    current = _sanitize_settings(settings or load_pwa_settings())
    capabilities = collect_module_pwa_capabilities()
    shortcuts = [
        {
            "name": shortcut["name"],
            "short_name": shortcut["short_name"],
            "url": shortcut["url"],
            **({"description": shortcut["description"]} if shortcut["description"] else {}),
        }
        for shortcut in capabilities["shortcuts"]
    ]
    return {
        "id": current["scope"],
        "name": current["app_name"],
        "short_name": current["short_name"],
        "description": current["description"],
        "lang": "es",
        "start_url": current["start_url"],
        "scope": current["scope"],
        "display": current["display"],
        "display_override": [current["display"], "window-controls-overlay"],
        "background_color": current["background_color"],
        "theme_color": current["theme_color"],
        "orientation": "portrait-primary",
        "categories": ["business", "productivity", "utilities"],
        "shortcuts": shortcuts,
        "icons": [
            {"src": "/modulos_sipet/pwa/static/icons/icon-72x72.png", "sizes": "72x72", "type": "image/png"},
            {"src": "/modulos_sipet/pwa/static/icons/icon-96x96.png", "sizes": "96x96", "type": "image/png"},
            {"src": "/modulos_sipet/pwa/static/icons/icon-128x128.png", "sizes": "128x128", "type": "image/png"},
            {"src": "/modulos_sipet/pwa/static/icons/icon-144x144.png", "sizes": "144x144", "type": "image/png"},
            {"src": "/modulos_sipet/pwa/static/icons/icon-152x152.png", "sizes": "152x152", "type": "image/png"},
            {"src": "/modulos_sipet/pwa/static/icons/icon-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/modulos_sipet/pwa/static/icons/icon-384x384.png", "sizes": "384x384", "type": "image/png"},
            {"src": "/modulos_sipet/pwa/static/icons/icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }


def build_service_worker_script(settings: Dict[str, Any] | None = None) -> str:
    current = _sanitize_settings(settings or load_pwa_settings())
    capabilities = collect_module_pwa_capabilities()
    version = (current.get("updated_at") or "v1").replace(":", "-")
    precache_urls = list(
        dict.fromkeys(
            [
        current["start_url"],
        current["offline_url"],
        "/manifest.webmanifest",
        "/static/vendor/fontawesome/css/all.min.css",
        "/static/dist/output.css",
        "/static/css/global.css",
        "/static/css/components.css",
        "/modulos_sipet/pwa/static/icons/icon-192x192.png",
        "/modulos_sipet/pwa/static/icons/icon-512x512.png",
            ]
            + capabilities["precache_urls"]
        )
    )
    cache_json = json.dumps(precache_urls, ensure_ascii=True)
    return f"""const VERSION = {json.dumps(version, ensure_ascii=True)};
const STATIC_CACHE = `sipet-static-${{VERSION}}`;
const RUNTIME_CACHE = `sipet-runtime-${{VERSION}}`;
const OFFLINE_URL = {json.dumps(current["offline_url"], ensure_ascii=True)};
const PRECACHE_URLS = {cache_json};

self.addEventListener('install', (event) => {{
  event.waitUntil(caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS)));
  self.skipWaiting();
}});

self.addEventListener('activate', (event) => {{
  event.waitUntil((async () => {{
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => ![STATIC_CACHE, RUNTIME_CACHE].includes(key)).map((key) => caches.delete(key)));
    await self.clients.claim();
  }})());
}});

async function staleWhileRevalidate(request) {{
  const cache = await caches.open(RUNTIME_CACHE);
  const cached = await cache.match(request);
  const networkFetch = fetch(request)
    .then((response) => {{
      if (response && response.ok) {{
        cache.put(request, response.clone());
      }}
      return response;
    }})
    .catch(() => cached);
  return cached || networkFetch;
}}

self.addEventListener('fetch', (event) => {{
  const request = event.request;
  if (request.method !== 'GET' || !request.url.startsWith(self.location.origin)) {{
    return;
  }}
  if (request.url.includes('/api/')) {{
    return;
  }}
  if (request.mode === 'navigate') {{
    event.respondWith(
      fetch(request)
        .then((response) => {{
          const clone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, clone));
          return response;
        }})
        .catch(async () => {{
          const cached = await caches.match(request);
          return cached || caches.match(OFFLINE_URL);
        }})
    );
    return;
  }}
  event.respondWith(staleWhileRevalidate(request));
}});
"""


def build_offline_page(settings: Dict[str, Any] | None = None) -> str:
    current = _sanitize_settings(settings or load_pwa_settings())
    logo_url = get_pwa_logo_url(current)
    logo_html = (
        f'<img src="{logo_url}" alt="{current["app_name"]}" style="width:min(132px,40vw);height:auto;display:block;margin:0 auto 18px;">'
        if logo_url
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="{current["theme_color"]}">
  <title>Sin conexion | {current["app_name"]}</title>
  <style>
    :root {{
      color-scheme: light;
      --pwa-bg-start: {current["background_color_start"]};
      --pwa-bg-end: {current["background_color_end"]};
      --pwa-accent: {current["theme_color"]};
      --pwa-card: #ffffff;
      --pwa-text: #0f172a;
      --pwa-muted: #475569;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
      font-family: Inter, system-ui, sans-serif;
      background:
        radial-gradient(circle at top, rgba(255,255,255,.18), transparent 34%),
        linear-gradient(180deg, var(--pwa-bg-start), var(--pwa-bg-end));
      color: var(--pwa-text);
    }}
    .card {{
      width: min(100%, 520px);
      background: var(--pwa-card);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 24px 80px rgba(15, 23, 42, .22);
    }}
    h1 {{ margin: 0 0 12px; font-size: clamp(1.7rem, 4vw, 2.4rem); }}
    p {{ margin: 0 0 18px; line-height: 1.55; color: var(--pwa-muted); }}
    a {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      padding: 0 16px;
      border-radius: 999px;
      background: var(--pwa-accent);
      color: #fff;
      text-decoration: none;
      font-weight: 700;
    }}
    .actions {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 8px;
    }}
    .actions a {{
      flex: 1 1 180px;
    }}
    .actions .secondary {{
      background: #ffffff;
      color: var(--pwa-accent);
      border: 1px solid color-mix(in srgb, var(--pwa-accent) 22%, #cbd5e1);
    }}
  </style>
</head>
<body>
  <main class="card">
    {logo_html}
    <h1>{current["app_name"]} te acompana</h1>
    <p>Que gusto tenerte aqui. En este momento no encontramos conexion, pero {current["app_name"]} sigue contigo.</p>
    <p>En cuanto regrese internet, intenta de nuevo y continuaremos contigo.</p>
    <div class="actions">
      <a href="{current["start_url"]}">Reintentar</a>
      <a class="secondary" href="/web/inicio">Ir a inicio</a>
    </div>
  </main>
</body>
</html>
"""
