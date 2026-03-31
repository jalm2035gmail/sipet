from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from fastapi_modulo.modulos_sipet.aplicaciones.controladores.aplicaciones import router
from fastapi_modulo.modulos_sipet.aplicaciones.controladores import api_packages, api_protocol, api_state


def _module_item(**overrides):
    base = {
        "key": "crm",
        "label": "CRM",
        "route": "/crm",
        "enabled": True,
        "protocol_ok": True,
        "protocol_missing": [],
        "package_upload_enabled": True,
        "description": "demo",
        "icon": "",
        "image_url": None,
        "router_count": 1,
        "module_dir": "/tmp/crm",
        "package_target_label": "fastapi_modulo/modulos/crm",
        "is_core_module": False,
        "package_management_note": "",
        "protocol_has_init": True,
        "protocol_has_manifest": True,
    }
    base.update(overrides)
    return base


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_api_list_modules_returns_catalog(monkeypatch) -> None:
    monkeypatch.setattr(api_state, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(api_state, "decorate_modules_payload", lambda tenant_key=None, refresh=False, include_legacy=False: [_module_item()])
    monkeypatch.setattr(api_state, "request_actor_context", lambda request: {"user_id": "tester", "tenant_id": "default", "tenant_key": "default", "ip": "127.0.0.1"})

    response = _client().get("/api/aplicaciones/modulos")

    assert response.status_code == 200
    assert response.json()[0]["key"] == "crm"


def test_api_update_module_state(monkeypatch) -> None:
    monkeypatch.setattr(api_state, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(api_state, "request_actor_context", lambda request: {"user_id": "tester", "tenant_id": "default", "tenant_key": "default", "ip": "127.0.0.1"})
    monkeypatch.setattr(api_state, "update_module_state", lambda module_key, enabled, **kwargs: _module_item(enabled=enabled))

    response = _client().put("/api/aplicaciones/modulos/crm", json={"enabled": False})

    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_api_update_module_state_returns_architecture_report(monkeypatch) -> None:
    monkeypatch.setattr(api_state, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(api_state, "request_actor_context", lambda request: {"user_id": "tester", "tenant_id": "default", "tenant_key": "default", "ip": "127.0.0.1"})

    def _raise(*args, **kwargs):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Arquitectura inválida.",
                "architecture_ok": False,
                "architecture_errors": [{"code": "db.raw_engine", "message": "bad", "path": "/tmp/crm/a.py"}],
                "architecture_warnings": [],
            },
        )

    monkeypatch.setattr(api_state, "update_module_state", _raise)

    response = _client().put("/api/aplicaciones/modulos/crm", json={"enabled": True})

    assert response.status_code == 400
    assert response.json()["detail"]["architecture_ok"] is False


def test_api_sync_protocol_inline(monkeypatch) -> None:
    monkeypatch.setattr(api_protocol, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(api_protocol, "request_actor_context", lambda request: {"user_id": "tester", "tenant_id": "default", "tenant_key": "default", "ip": "127.0.0.1"})
    monkeypatch.setattr(api_protocol, "verify_sensitive_action_token", lambda **kwargs: None)
    monkeypatch.setattr(api_protocol, "queue_task", lambda task_name, kwargs: {"status": "inline", "task_id": "t1"})
    monkeypatch.setattr(api_protocol, "sync_protocol_files", lambda **kwargs: {"created_init": ["crm"], "created_manifest": [], "updated_init": [], "updated_manifest": [], "before": {}, "after": {}})

    response = _client().post("/api/aplicaciones/protocolo/sync", json={"challenge_token": "ok"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["created_init"] == ["crm"]


def test_api_upload_valid_zip(monkeypatch) -> None:
    async def _import_module_package(module_key, package, **kwargs):
        return {
            "module_key": module_key,
            "target_root": "/tmp/crm",
            "dry_run": True,
            "status": "success",
            "task_id": "",
            "task_name": "",
            "checksum": "abc",
            "file_size": 3,
            "content_type": "application/zip",
            "updated_files": 0,
            "total_files": 1,
            "total_uncompressed_size": 3,
            "new_files": 1,
            "changed_files": 0,
            "unchanged_files": 0,
            "preview_files": [],
            "warnings": [],
            "architecture_ok": True,
            "architecture_errors": [],
            "architecture_warnings": [],
        }

    monkeypatch.setattr(api_packages, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(api_packages, "require_superadmin", lambda request: None)
    monkeypatch.setattr(api_packages, "_require_package_manageable_module", lambda module_key: module_key)
    monkeypatch.setattr(api_packages, "request_actor_context", lambda request: {"user_id": "tester", "tenant_id": "default", "tenant_key": "default", "ip": "127.0.0.1"})
    monkeypatch.setattr(api_packages, "import_module_package", _import_module_package)

    response = _client().post(
        "/api/aplicaciones/modulos/crm/upload",
        files={"package": ("crm.zip", b"PK\x03\x04", "application/zip")},
        data={"dry_run": "true"},
    )

    assert response.status_code == 200
    assert response.json()["module_key"] == "crm"


def test_api_upload_rejects_non_zip_extension(monkeypatch) -> None:
    monkeypatch.setattr(api_packages, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(api_packages, "require_superadmin", lambda request: None)
    monkeypatch.setattr(api_packages, "_require_package_manageable_module", lambda module_key: module_key)
    monkeypatch.setattr(api_packages, "request_actor_context", lambda request: {"user_id": "tester", "tenant_id": "default", "tenant_key": "default", "ip": "127.0.0.1"})

    response = _client().post(
        "/api/aplicaciones/modulos/crm/upload",
        files={"package": ("crm.txt", b"hello", "text/plain")},
        data={"dry_run": "true"},
    )

    assert response.status_code == 400
    assert "archivo .zip" in response.json()["detail"]


def test_api_upload_propagates_invalid_module(monkeypatch) -> None:
    async def _import_module_package(module_key, package, **kwargs):
        raise HTTPException(status_code=400, detail="Este modulo todavia no admite actualizacion por ZIP.")

    monkeypatch.setattr(api_packages, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(api_packages, "require_superadmin", lambda request: None)
    monkeypatch.setattr(api_packages, "_require_package_manageable_module", lambda module_key: module_key)
    monkeypatch.setattr(api_packages, "request_actor_context", lambda request: {"user_id": "tester", "tenant_id": "default", "tenant_key": "default", "ip": "127.0.0.1"})
    monkeypatch.setattr(api_packages, "import_module_package", _import_module_package)

    response = _client().post(
        "/api/aplicaciones/modulos/crm/upload",
        files={"package": ("crm.zip", b"PK\x03\x04", "application/zip")},
        data={"dry_run": "true"},
    )

    assert response.status_code == 400
    assert "no admite" in response.json()["detail"]


def test_api_upload_allows_manageable_alias_module(monkeypatch) -> None:
    monkeypatch.setattr(api_packages, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(api_packages, "require_superadmin", lambda request: None)
    monkeypatch.setattr(api_packages, "request_actor_context", lambda request: {"user_id": "tester", "tenant_id": "default", "tenant_key": "default", "ip": "127.0.0.1"})
    monkeypatch.setitem(api_packages.MODULES_BY_KEY, "empresa", SimpleNamespace(manageable=True))
    monkeypatch.setattr(
        api_packages,
        "_require_package_manageable_module",
        lambda module_key: (_ for _ in ()).throw(
            HTTPException(status_code=400, detail="Este módulo no admite instalación o actualización por importación.")
        ),
    )

    response = _client().post(
        "/api/aplicaciones/modulos/empresa/upload",
        files={"package": ("empresa.zip", b"PK\x03\x04", "application/zip")},
        data={"dry_run": "true"},
    )

    assert response.status_code == 400
    assert "no admite instalación" in response.json()["detail"]


def test_api_upload_requires_superadmin(monkeypatch) -> None:
    monkeypatch.setattr(api_packages, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(
        api_packages,
        "require_superadmin",
        lambda request: (_ for _ in ()).throw(HTTPException(status_code=403, detail="Acceso restringido a superadministrador")),
    )

    response = _client().post(
        "/api/aplicaciones/modulos/crm/upload",
        files={"package": ("crm.zip", b"PK\x03\x04", "application/zip")},
        data={"dry_run": "true"},
    )

    assert response.status_code == 403
    assert "superadministrador" in response.json()["detail"]


def test_api_uninstall_module(monkeypatch) -> None:
    monkeypatch.setattr(api_packages, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(api_packages, "_require_package_manageable_module", lambda module_key: module_key)
    monkeypatch.setattr(api_packages, "request_actor_context", lambda request: {"user_id": "tester", "tenant_id": "default", "tenant_key": "default", "ip": "127.0.0.1"})
    monkeypatch.setattr(api_packages, "verify_sensitive_action_token", lambda **kwargs: None)
    monkeypatch.setattr(
        api_packages,
        "uninstall_module_package_job",
        lambda **kwargs: {"module_key": "crm", "status": "success", "removed_path": "/tmp/crm", "removed_files": 12},
    )

    response = _client().delete("/api/aplicaciones/modulos/crm?challenge_token=ok")

    assert response.status_code == 200
    assert response.json()["removed_files"] == 12


def test_api_rejects_user_without_permission(monkeypatch) -> None:
    monkeypatch.setattr(
        api_state,
        "require_applications_permission",
        lambda request, permission: (_ for _ in ()).throw(HTTPException(status_code=403, detail="forbidden")),
    )

    response = _client().get("/api/aplicaciones/modulos")

    assert response.status_code == 403


def test_api_asset_nonexistent(monkeypatch) -> None:
    monkeypatch.setattr(api_packages, "require_applications_permission", lambda request, permission: None)
    monkeypatch.setattr(api_packages, "get_module_image_path", lambda module_key: None)
    monkeypatch.setitem(api_packages.MODULES_BY_KEY, "crm", type("Def", (), {"label": "CRM", "name": "CRM"})())
    monkeypatch.setattr(
        api_packages,
        "build_module_image_response",
        lambda module_key, filename, **kwargs: (_ for _ in ()).throw(HTTPException(status_code=404, detail="Recurso no encontrado")),
    )

    response = _client().get("/api/aplicaciones/assets/crm/inexistente.png")

    assert response.status_code == 404
