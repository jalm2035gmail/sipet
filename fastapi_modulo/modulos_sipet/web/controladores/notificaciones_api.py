from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.servicios.notification_service import (
    list_notificaciones,
    marcar_leida,
    marcar_todas_leidas,
)

router = APIRouter()

_TIPO_LABEL: dict[str, str] = {
    "actividad_atrasada": "Actividad atrasada",
    "actividad_por_vencer": "Actividad por vencer",
    "lead_nuevo": "Nuevo lead asignado",
    "oportunidad_sin_movimiento": "Oportunidad sin movimiento",
    "cambio_etapa": "Cambio de etapa",
    "propuesta_pendiente": "Propuesta pendiente",
    "campana_por_iniciar": "Campaña por iniciar",
    "campana_finalizada": "Campaña finalizada",
    "oportunidad_perdida": "Oportunidad perdida",
    "cierre_ganado": "Cierre ganado",
}

_HREF_MAP: dict[str, str] = {
    "oportunidad": "/crm/oportunidades/{}",
    "lead": "/crm/leads/{}",
    "campana": "/crm/campanas/{}",
    "contacto": "/crm/contactos/{}",
}


def _item_href(ref_tipo: str | None, ref_id: int | None) -> str:
    if ref_tipo and ref_id and ref_tipo in _HREF_MAP:
        return _HREF_MAP[ref_tipo].format(ref_id)
    return "/crm"


def _build_resumen(raw: dict) -> dict:
    items = raw.get("items", [])
    mapped = [
        {
            "id": str(it["id"]),
            "href": _item_href(it.get("referencia_tipo"), it.get("referencia_id")),
            "title": _TIPO_LABEL.get(it.get("tipo", ""), it.get("tipo", "Notificación")),
            "message": it.get("mensaje", ""),
            "created_at": it.get("fecha_creacion", ""),
            "read": bool(it.get("leida", False)),
        }
        for it in items
    ]
    unread = sum(1 for m in mapped if not m["read"])
    counts: dict[str, int] = {}
    for it in items:
        tipo = it.get("tipo", "")
        if tipo:
            counts[tipo] = counts.get(tipo, 0) + (0 if it.get("leida") else 1)
    return {
        "success": True,
        "total": raw.get("total", len(mapped)),
        "unread": unread,
        "counts": counts,
        "items": mapped,
    }


_EMPTY_OK = {"success": True, "total": 0, "unread": 0, "counts": {}, "items": []}


@router.get("/api/notificaciones/resumen")
def api_resumen(request: Request):
    try:
        usuario = getattr(request.state, "user_name", "") or ""
        if not usuario:
            return JSONResponse(_EMPTY_OK)
        tenant_id = getattr(request.state, "tenant_id", None)
        raw = list_notificaciones(tenant_id, usuario, limit=50)
        return JSONResponse(_build_resumen(raw))
    except Exception:
        return JSONResponse(_EMPTY_OK)


@router.post("/api/notificaciones/marcar-leida")
async def api_marcar_leida(request: Request):
    try:
        body = await request.json()
        notif_id = int(body.get("id", 0))
        usuario = getattr(request.state, "user_name", "") or ""
        tenant_id = getattr(request.state, "tenant_id", None)
        result = marcar_leida(tenant_id, notif_id, usuario)
        return JSONResponse({"ok": bool(result)})
    except Exception:
        return JSONResponse({"ok": False})


@router.post("/api/notificaciones/marcar-todas-leidas")
async def api_marcar_todas_leidas(request: Request):
    try:
        usuario = getattr(request.state, "user_name", "") or ""
        tenant_id = getattr(request.state, "tenant_id", None)
        count = marcar_todas_leidas(tenant_id, usuario)
        return JSONResponse({"ok": True, "marcadas": count})
    except Exception:
        return JSONResponse({"ok": False, "marcadas": 0})
