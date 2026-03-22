from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios import package_repository
from fastapi_modulo.modulos_sipet.aplicaciones.servicios import state_service


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_valid_module(module_dir: Path) -> None:
    _write(
        module_dir / "__manifest__.py",
        """MANIFEST = {
    "name": "modulo_nuevo",
    "label": "Modulo nuevo",
    "summary": "Resumen",
    "version": "1.0.0",
    "depends": ["web"],
    "route": "/modulo-nuevo",
    "installable": True,
    "application": True,
    "assets": {"css": ["static/css/modulo.css"], "js": ["static/js/modulo.js"]},
    "structure": {"router": ["controladores/router.py"], "views": ["vistas/modulo.html"]},
}
""",
    )
    _write(
        module_dir / "controladores/router.py",
        "from fastapi_modulo.core import db as core_db\n\n"
        "def get_db():\n"
        "    return core_db.SessionLocal()\n",
    )
    _write(module_dir / "vistas/modulo.html", '<section class="text-slate-900 bg-white">OK</section>\n')
    _write(module_dir / "static/css/modulo.css", ".modulo { color: #111827; }\n")
    _write(module_dir / "static/js/modulo.js", "console.log('ok');\n")
    _write(module_dir / "tests/test_modulo.py", "def test_smoke():\n    assert True\n")


def _build_invalid_module(module_dir: Path) -> None:
    _build_valid_module(module_dir)
    _write(
        module_dir / "controladores/router.py",
        "from sqlalchemy import create_engine\n\n"
        "def get_db():\n"
        "    return create_engine('sqlite:///:memory:')\n",
    )


def _stub_side_effects(monkeypatch) -> None:
    monkeypatch.setattr(
        state_service,
        "set_catalog_module_enabled",
        lambda module_key, enabled, tenant_key=None: {
            "key": module_key,
            "enabled": enabled,
            "version": "1.0.0",
        },
    )
    monkeypatch.setattr(state_service, "upsert_registry_state", lambda **kwargs: None)
    monkeypatch.setattr(state_service, "create_registry_audit", lambda **kwargs: None)
    monkeypatch.setattr(state_service, "invalidate_catalog_cache", lambda: None)
    monkeypatch.setattr(state_service, "decorate_modules_payload", lambda items, tenant_key=None: items)


def test_activate_new_valid_module_passes_architecture_validation(tmp_path: Path, monkeypatch) -> None:
    module_dir = tmp_path / "modulo_nuevo_ok"
    _build_valid_module(module_dir)
    _stub_side_effects(monkeypatch)
    monkeypatch.setattr(
        state_service,
        "get_module_architecture_report",
        lambda module_key: package_repository.get_module_architecture_report(module_key, str(module_dir)),
    )

    payload = state_service.update_module_state("modulo_nuevo_ok", True, user_id="tester", tenant_key="default")

    assert payload["enabled"] is True


def test_activate_new_invalid_module_is_blocked_by_architecture_validation(tmp_path: Path, monkeypatch) -> None:
    module_dir = tmp_path / "modulo_nuevo_bad"
    _build_invalid_module(module_dir)
    _stub_side_effects(monkeypatch)
    monkeypatch.setattr(
        state_service,
        "get_module_architecture_report",
        lambda module_key: package_repository.get_module_architecture_report(module_key, str(module_dir)),
    )

    with pytest.raises(HTTPException) as exc_info:
        state_service.update_module_state("modulo_nuevo_bad", True, user_id="tester", tenant_key="default")

    assert exc_info.value.status_code == 400
    detail = exc_info.value.detail
    assert detail["architecture_ok"] is False
    assert any(item["code"] == "db.raw_engine" for item in detail["architecture_errors"])
