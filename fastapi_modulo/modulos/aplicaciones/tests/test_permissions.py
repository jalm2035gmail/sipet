from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace


DEPENDENCIES_PATH = Path(__file__).resolve().parents[1] / "controladores" / "dependencies.py"
SPEC = spec_from_file_location("aplicaciones_dependencies_test", DEPENDENCIES_PATH)
MODULE = module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
get_applications_permissions = MODULE.get_applications_permissions


def _request() -> SimpleNamespace:
    return SimpleNamespace(
        state=SimpleNamespace(user_name="tester", username="tester", user_role="usuario"),
        cookies={},
    )


def test_permissions_allow_explicit_screen_grants(monkeypatch) -> None:
    request = _request()
    monkeypatch.setattr(
        "fastapi_modulo.modulos.web.servicios.access_service.is_admin_or_superadmin",
        lambda req: False,
    )
    monkeypatch.setattr(
        "fastapi_modulo.modulos.web.servicios.access_service.get_user_app_access",
        lambda req: [],
    )
    monkeypatch.setattr(
        "fastapi_modulo.modulos.web.servicios.access_service.get_user_screen_access_levels",
        lambda req: {
            "aplicaciones.ver": {"read_only": True},
            "aplicaciones.protocolo.sincronizar": {"special_permissions": True},
        },
    )

    permissions = get_applications_permissions(request)

    assert permissions["aplicaciones.ver"] is True
    assert permissions["aplicaciones.protocolo.sincronizar"] is True
    assert permissions["aplicaciones.estado.editar"] is False


def test_permissions_allow_full_access_from_app_access(monkeypatch) -> None:
    request = _request()
    monkeypatch.setattr(
        "fastapi_modulo.modulos.web.servicios.access_service.is_admin_or_superadmin",
        lambda req: False,
    )
    monkeypatch.setattr(
        "fastapi_modulo.modulos.web.servicios.access_service.get_user_app_access",
        lambda req: ["Aplicaciones"],
    )
    monkeypatch.setattr(
        "fastapi_modulo.modulos.web.servicios.access_service.get_user_screen_access_levels",
        lambda req: {},
    )

    permissions = get_applications_permissions(request)

    assert all(permissions.values())
