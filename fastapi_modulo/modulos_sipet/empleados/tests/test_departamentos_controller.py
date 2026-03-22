from __future__ import annotations

import asyncio
import json
import types
from pathlib import Path

from fastapi.responses import HTMLResponse
from starlette.requests import Request

from fastapi_modulo.modulos_sipet.empleados.controladores import departamentos


def _request(path: str, method: str = "GET") -> Request:
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": method,
        "scheme": "http",
        "path": path,
        "headers": [],
        "app": types.SimpleNamespace(state=types.SimpleNamespace()),
    }
    return Request(scope, receive=receive)


def test_departamentos_routes_redirect_to_canonical_backend_page() -> None:
    legacy_response = departamentos.departamentos_page(_request("/departamentos"))
    areas_response = departamentos.areas_organizacionales_page(_request("/areas-organizacionales"))

    assert legacy_response.status_code == 307
    assert legacy_response.headers["location"] == "/inicio/departamentos"
    assert areas_response.status_code == 307
    assert areas_response.headers["location"] == "/inicio/departamentos"


def test_guardar_departamentos_enforces_permission_and_forwards_payload(monkeypatch) -> None:
    calls: list[object] = []

    monkeypatch.setattr(departamentos, "DEPARTAMENTOS_PUBLIC_ACCESS", False)
    monkeypatch.setattr(departamentos, "require_admin_or_superadmin", lambda request: calls.append("permission"))
    monkeypatch.setattr(
        departamentos,
        "save_departamentos_payload",
        lambda payload: calls.append(payload) or {"success": True, "data": payload},
    )

    request = _request("/api/inicio/departamentos", method="POST")
    response = asyncio.run(
        departamentos.guardar_departamentos(request, {"data": [{"code": "DIR", "name": "Direccion"}]})
    )

    assert response["success"] is True
    assert calls == ["permission", [{"code": "DIR", "name": "Direccion"}]]


def test_puestos_laborales_page_injects_initial_areas_into_template(tmp_path: Path, monkeypatch) -> None:
    template_path = tmp_path / "puestos_laborales.html"
    template_path.write_text("<div id='areas'>__INITIAL_AREAS__</div>", encoding="utf-8")

    monkeypatch.setattr(departamentos, "PUESTOS_LABORALES_TEMPLATE_PATH", str(template_path))
    monkeypatch.setattr(departamentos, "get_departamentos_catalog", lambda: ["Direccion", "Talento"])
    monkeypatch.setattr(
        departamentos,
        "render_backend_page",
        lambda request, **kwargs: HTMLResponse(kwargs["content"]),
    )

    response = departamentos.puestos_laborales_page(_request("/inicio/departamentos/puestos-laborales"))

    assert response.status_code == 200
    body = response.body.decode("utf-8")
    assert json.dumps(["Direccion", "Talento"], ensure_ascii=False) in body
