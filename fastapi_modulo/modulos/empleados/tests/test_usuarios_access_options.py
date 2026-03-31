from __future__ import annotations

from types import SimpleNamespace

from fastapi_modulo.modulos.empleados.controladores import empleados


def test_resolve_access_app_options_uses_installed_modules(monkeypatch) -> None:
    monkeypatch.setattr(
        empleados,
        "get_active_app_access_names",
        lambda tenant_key=None: ["Mi tablero", "CRM", "Modulo inexistente"],
    )
    request = SimpleNamespace(state=SimpleNamespace(tenant_key="oaxaca"))

    installed = empleados._resolve_access_app_options(request)

    assert installed == ["Mi tablero", "CRM"]


def test_normalize_app_access_levels_filters_uninstalled_modules() -> None:
    normalized = empleados._normalize_app_access_levels(
        {
            "Mi tablero": {"full_access": True},
            "CRM": {"read_only": True},
            "PLD": {"full_access": True},
        },
        ["Mi tablero", "PLD"],
        allowed_app_options=["Mi tablero", "CRM"],
    )

    assert set(normalized.keys()) == {"Mi tablero", "CRM"}
    assert normalized["Mi tablero"]["full_access"] is True
    assert normalized["CRM"]["read_only"] is True


def test_apply_conversation_access_skips_module_when_not_installed() -> None:
    normalized = empleados._apply_conversation_module_access(
        {"Mi tablero": {"full_access": True}},
        {"role": "administrador"},
        allowed_app_options=["Mi tablero"],
    )

    assert set(normalized.keys()) == {"Mi tablero"}
