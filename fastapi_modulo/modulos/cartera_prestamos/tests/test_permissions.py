from __future__ import annotations

from fastapi_modulo.modulos.cartera_prestamos.controladores import dependencies as cartera_dependencies


def test_role_from_request_state_is_rendered(client):
    response = client.get(
        "/resumen_ejecutivo",
        headers={"x-user-name": "analista.cp", "x-user-role": "jefe_cobranza"},
    )
    assert response.status_code == 200
    assert "analista.cp" in response.text
    assert "Jefe Cobranza" in response.text


def test_role_from_cookie_is_used_when_request_state_is_empty(client):
    response = client.get(
        "/resumen_ejecutivo",
        headers={"x-user-name": "", "x-user-role": ""},
        cookies={"user_name": "cookie.user", "user_role": "auditor_interno"},
    )
    assert response.status_code == 200
    assert "cookie.user" in response.text
    assert "Auditor Interno" in response.text


def test_menu_is_filtered_by_role_permissions(client):
    response = client.get(
        "/resumen_ejecutivo",
        headers={"x-user-name": "gestor", "x-user-role": "gestor_cobranza"},
    )
    assert response.status_code == 200
    assert "Cobranza" in response.text
    assert "Cartera de cobranza" in response.text
    assert "Cartera operativa" not in response.text
    assert "Configuración" not in response.text


def test_page_access_is_blocked_by_role(client):
    response = client.get(
        "/cartera-prestamos/gestion",
        headers={"x-user-name": "gestor", "x-user-role": "gestor_cobranza"},
    )
    assert response.status_code == 200
    assert "Sin permisos para acceder a esta sección." in response.text


def test_module_access_allows_page_without_cartera_role(client, monkeypatch):
    monkeypatch.setattr(cartera_dependencies, "get_user_app_access_level", lambda request, app_name: "read_only")

    response = client.get(
        "/resumen_ejecutivo",
        headers={"x-user-name": "usuario.app", "x-user-role": "usuario"},
    )

    assert response.status_code == 200
    assert "Cartera ejecutiva" in response.text


def test_legacy_mesa_control_access_alias_still_allows_page(client, monkeypatch):
    monkeypatch.setattr(
        cartera_dependencies,
        "get_user_app_access_level",
        lambda request, app_name: "read_only" if app_name == "Mesa de control" else "no_access",
    )

    response = client.get(
        "/resumen_ejecutivo",
        headers={"x-user-name": "usuario.legacy", "x-user-role": "usuario"},
    )

    assert response.status_code == 200
    assert "Cartera ejecutiva" in response.text
