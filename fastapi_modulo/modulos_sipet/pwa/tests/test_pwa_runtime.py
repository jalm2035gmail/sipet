from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_modulo.core.module_registry import MODULES_BY_KEY
from fastapi_modulo.modulos_sipet.pwa.controladores import pwa as pwa_controller
from fastapi_modulo.modulos_sipet.pwa.servicios import pwa_runtime_service


def test_pwa_module_is_mounted_in_runtime_catalog() -> None:
    module = MODULES_BY_KEY["pwa"]

    assert module.route == "/ajustes/pwa"
    assert module.router_specs
    assert module.router_specs[0].module_path == "fastapi_modulo.modulos_sipet.pwa.controladores.pwa"


def test_pwa_manifest_and_settings_api(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pwa_runtime_service, "PWA_STORE_DIR", tmp_path)
    monkeypatch.setattr(pwa_runtime_service, "PWA_SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(pwa_runtime_service, "PWA_ASSETS_DIR", tmp_path / "assets")
    monkeypatch.setattr(pwa_controller, "require_admin_or_superadmin", lambda request: None)

    app = FastAPI()
    app.include_router(pwa_controller.router)
    client = TestClient(app)

    response = client.get("/manifest.webmanifest")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/manifest+json")
    assert response.json()["start_url"] == "/web/inicio"

    save_response = client.post(
        "/api/ajustes/pwa",
        json={
            "app_name": "SIPET Movil",
            "short_name": "Movil",
            "start_url": "/backend/inicio",
            "scope": "/",
            "theme_color": "#112233",
        },
    )
    assert save_response.status_code == 200
    payload = save_response.json()
    assert payload["success"] is True
    assert payload["settings"]["app_name"] == "SIPET Movil"

    persisted = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert persisted["theme_color"] == "#112233"


def test_pwa_settings_support_splash_logo_and_background_gradient(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pwa_runtime_service, "PWA_STORE_DIR", tmp_path)
    monkeypatch.setattr(pwa_runtime_service, "PWA_SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(pwa_runtime_service, "PWA_ASSETS_DIR", tmp_path / "assets")

    settings = pwa_runtime_service.save_pwa_settings(
        {
            "splash_logo_filename": "logo.png",
            "background_color_start": "#112233",
            "background_color_end": "#445566",
        }
    )
    (tmp_path / "assets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "assets" / "logo.png").write_bytes(b"fake")

    html = pwa_runtime_service.build_offline_page(settings)

    assert "/api/ajustes/pwa/logo" in html
    assert "#112233" in html
    assert "#445566" in html


def test_backend_configuration_menu_lists_pwa_after_general() -> None:
    content = (
        (pwa_runtime_service.Path(__file__).resolve().parents[2] / "web" / "vistas" / "backend_nav_catalog.html")
        .read_text(encoding="utf-8")
    )

    general_index = content.index('{ href: "/ajustes/configuracion", label: "General" }')
    pwa_index = content.index('{ href: "/ajustes/pwa", label: "PWA" }')

    assert general_index < pwa_index


def test_manifest_and_service_worker_include_module_capabilities(monkeypatch) -> None:
    monkeypatch.setattr(
        pwa_runtime_service,
        "list_enabled_module_manifests",
        lambda tenant_key=None: [
            {
                "key": "empleados",
                "label": "Organización",
                "route": "/inicio/departamentos",
                "manifest": {
                    "pwa": {
                        "features": [
                            {
                                "key": "departamentos",
                                "label": "Departamentos",
                                "route": "/inicio/departamentos",
                            }
                        ],
                        "shortcuts": [
                            {
                                "name": "Departamentos",
                                "short_name": "Areas",
                                "url": "/inicio/departamentos",
                            }
                        ],
                        "precache_urls": ["/inicio/departamentos"],
                    }
                },
            }
        ],
    )

    manifest = pwa_runtime_service.build_manifest_payload()
    script = pwa_runtime_service.build_service_worker_script()
    capabilities = pwa_runtime_service.collect_module_pwa_capabilities()

    assert manifest["shortcuts"][0]["url"] == "/inicio/departamentos"
    assert "/inicio/departamentos" in script
    assert capabilities["modules"][0]["module_key"] == "empleados"
