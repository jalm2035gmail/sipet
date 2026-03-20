from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace


DEPENDENCIES_PATH = Path(__file__).resolve().parents[1] / "controladores" / "dependencies.py"
SPEC = spec_from_file_location("capacitacion_dependencies_test", DEPENDENCIES_PATH)
MODULE = module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

PermisoCapacitacion = MODULE.PermisoCapacitacion
get_capacitacion_permissions = MODULE.get_capacitacion_permissions
get_capacitacion_access_payload = MODULE.get_capacitacion_access_payload
require_access = MODULE.require_access


def _request() -> SimpleNamespace:
    return SimpleNamespace(
        state=SimpleNamespace(user_name="tester", username="tester", user_role="usuario", tenant_id="default"),
        cookies={},
        headers={},
    )


def test_permissions_allow_explicit_screen_grants_without_app_access(monkeypatch) -> None:
    request = _request()
    monkeypatch.setattr(MODULE, "web_is_admin_or_superadmin", lambda req: False)
    monkeypatch.setattr(MODULE, "get_user_app_access", lambda req: [])
    monkeypatch.setattr(MODULE, "get_user_screen_access_levels", lambda req: {
        "capacitacion.presentaciones.gestionar": {"special_permissions": True},
    })

    permissions = get_capacitacion_permissions(request)

    assert permissions[PermisoCapacitacion.PRESENTACIONES_GESTIONAR.value] is True
    assert permissions[PermisoCapacitacion.PRESENTACIONES_VER.value] is True
    assert permissions[PermisoCapacitacion.VER.value] is True
    require_access(request)


def test_permissions_map_user_only_base_access(monkeypatch) -> None:
    request = _request()
    monkeypatch.setattr(MODULE, "web_is_admin_or_superadmin", lambda req: False)
    monkeypatch.setattr(MODULE, "get_user_app_access", lambda req: [])
    monkeypatch.setattr(MODULE, "get_user_screen_access_levels", lambda req: {
        "capacitacion": {"user_only": True},
    })

    permissions = get_capacitacion_permissions(request)

    assert permissions[PermisoCapacitacion.CATALOGO_VER.value] is True
    assert permissions[PermisoCapacitacion.AUTOGESTION_PROGRESO.value] is True
    assert permissions[PermisoCapacitacion.CERTIFICADOS_VER.value] is True
    assert permissions[PermisoCapacitacion.CATALOGO_EDITAR.value] is False
    assert permissions[PermisoCapacitacion.INSCRIPCIONES_GESTIONAR.value] is False


def test_access_payload_exposes_resolved_role(monkeypatch) -> None:
    request = _request()
    monkeypatch.setattr(MODULE, "web_is_admin_or_superadmin", lambda req: False)
    monkeypatch.setattr(MODULE, "get_user_app_access", lambda req: [])
    monkeypatch.setattr(MODULE, "get_user_screen_access_levels", lambda req: {
        "capacitacion": {"special_permissions": True},
    })

    payload = get_capacitacion_access_payload(request)

    assert payload["role"] == "coordinador"
    assert payload["has_access"] is True
    assert payload["permissions"][PermisoCapacitacion.EVALUACIONES_GESTIONAR.value] is True
