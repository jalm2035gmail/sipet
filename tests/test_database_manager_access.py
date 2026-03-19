import types

from starlette.requests import Request

from fastapi_modulo.modulos_sipet.modulo_base.controladores import database_manager


def _request(path: str = "/base_datos/inicializar", cookies: dict[str, str] | None = None):
    headers = []
    if cookies:
        cookie_value = "; ".join(f"{key}={value}" for key, value in cookies.items())
        headers.append((b"cookie", cookie_value.encode("latin1")))

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "headers": headers,
        "app": types.SimpleNamespace(state=types.SimpleNamespace(database_setup_required=False)),
    }
    return Request(scope, receive=receive)


def test_database_setup_page_allows_setup_cookie_outside_initial_install(monkeypatch) -> None:
    monkeypatch.setattr(database_manager, "AUTH_COOKIE_SECRET", "test-secret")
    valid_cookie = database_manager._build_setup_auth_cookie("0konomiyaki")
    request = _request(cookies={database_manager.SETUP_AUTH_COOKIE_NAME: valid_cookie})

    monkeypatch.setattr(database_manager, "is_superadmin", lambda _request: False)

    response = database_manager.database_setup_page(request)

    assert response.status_code == 200
