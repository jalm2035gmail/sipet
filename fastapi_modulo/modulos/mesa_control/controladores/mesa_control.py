from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter()


@router.get("/mesa-de-control", response_class=HTMLResponse)
def mesa_control_home(_: Request) -> HTMLResponse:
    return HTMLResponse(
        "<html><head><title>Mesa de control</title></head>"
        "<body><section id='mesa-control-root'><h1>Mesa de control</h1>"
        "<p>Modulo base disponible.</p></section></body></html>"
    )


@router.get("/api/mesa-de-control/status")
def mesa_control_status() -> JSONResponse:
    return JSONResponse({"ok": True, "module": "mesa_control"})
