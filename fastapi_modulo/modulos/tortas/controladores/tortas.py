from __future__ import annotations
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import render_backend_page_html
from fastapi_modulo.modulos.tortas.modelos.db_models import ensure_tortas_schema
from fastapi_modulo.modulos.tortas.modelos.schemas import (
    CategoriaCreate, AlergenoCreate, TipoPanCreate, TipoPanUpdate,
    ToppingCreate, TortaCreate, TortaUpdate,
    ZonaEntregaCreate, ZonaEntregaUpdate, FormaPagoCreate,
    CuponCreate, CuponValidarRequest,
    PedidoCreate, PagoCreate,
    CorteCajaCreate, CorteCajaCerrarRequest,
    PreordenCreate,
)
from fastapi_modulo.modulos.tortas.modelos import store

MODULE_DIR = Path(__file__).resolve().parents[1]
VIEWS_DIR = MODULE_DIR / "vistas"

try:
    ensure_tortas_schema()
except Exception as _e:
    print(f"[tortas] schema init warning: {_e}")

router = APIRouter()


# ── Página principal ──────────────────────────────────────────────────────────

@router.get("/tortas", response_class=HTMLResponse)
async def tortas_page(request: Request):
    content = (VIEWS_DIR / "tortas.html").read_text(encoding="utf-8")
    return render_backend_page_html(
        request,
        title="Tortas",
        description="Sistema de gestión de negocio de tortas",
        content=content,
        hide_floating_actions=True,
        show_page_header=False,
    )


# ── API: Categorías ───────────────────────────────────────────────────────────

@router.get("/api/tortas/categorias")
async def api_list_categorias(request: Request, db=Depends(SessionLocal)):
    items = store.list_categorias(db)
    return JSONResponse({"success": True, "data": [
        {"id": c.id, "name": c.name, "descripcion": c.descripcion} for c in items
    ]})


@router.post("/api/tortas/categorias")
async def api_create_categoria(data: CategoriaCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_categoria(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


# ── API: Alérgenos ────────────────────────────────────────────────────────────

@router.get("/api/tortas/alergenos")
async def api_list_alergenos(request: Request, db=Depends(SessionLocal)):
    items = store.list_alergenos(db)
    return JSONResponse({"success": True, "data": [
        {"id": a.id, "name": a.name, "icono": a.icono, "color": a.color} for a in items
    ]})


@router.post("/api/tortas/alergenos")
async def api_create_alergeno(data: AlergenoCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_alergeno(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


# ── API: Tipos de pan ─────────────────────────────────────────────────────────

@router.get("/api/tortas/tipos-pan")
async def api_list_tipos_pan(request: Request, db=Depends(SessionLocal)):
    items = store.list_tipos_pan(db)
    return JSONResponse({"success": True, "data": [
        {"id": t.id, "nombre": t.nombre, "precio_extra": t.precio_extra, "disponible": t.disponible}
        for t in items
    ]})


@router.post("/api/tortas/tipos-pan")
async def api_create_tipo_pan(data: TipoPanCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_tipo_pan(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "nombre": obj.nombre}})


@router.put("/api/tortas/tipos-pan/{tipo_pan_id}")
async def api_update_tipo_pan(tipo_pan_id: int, data: TipoPanUpdate, request: Request, db=Depends(SessionLocal)):
    obj = store.update_tipo_pan(db, tipo_pan_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Tipo de pan no encontrado")
    return JSONResponse({"success": True, "data": {"id": obj.id, "disponible": obj.disponible}})


# ── API: Toppings ─────────────────────────────────────────────────────────────

@router.get("/api/tortas/toppings")
async def api_list_toppings(request: Request, db=Depends(SessionLocal)):
    items = store.list_toppings(db)
    return JSONResponse({"success": True, "data": [
        {
            "id": t.id, "name": t.name, "tipo": t.tipo,
            "precio": t.precio, "unidad": t.unidad, "maximo": t.maximo,
            "sort_order": t.sort_order,
        }
        for t in items
    ]})


@router.post("/api/tortas/toppings")
async def api_create_topping(data: ToppingCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_topping(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


# ── API: Tortas (menú) ────────────────────────────────────────────────────────

@router.get("/api/tortas/menu")
async def api_list_tortas(
    request: Request,
    db=Depends(SessionLocal),
    categoria_id: Optional[int] = None,
):
    items = store.list_tortas(db, categoria_id=categoria_id)
    return JSONResponse({"success": True, "data": [
        {
            "id": t.id, "name": t.name, "descripcion": t.descripcion,
            "precio": t.precio, "categoria_id": t.categoria_id,
            "min_toppings": t.min_toppings, "max_toppings": t.max_toppings,
            "requiere_tipo_pan": t.requiere_tipo_pan,
        }
        for t in items
    ]})


@router.post("/api/tortas/menu")
async def api_create_torta(data: TortaCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_torta(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.put("/api/tortas/menu/{torta_id}")
async def api_update_torta(torta_id: int, data: TortaUpdate, request: Request, db=Depends(SessionLocal)):
    obj = store.update_torta(db, torta_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Torta no encontrada")
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


# ── API: Zonas de entrega ─────────────────────────────────────────────────────

@router.get("/api/tortas/zonas")
async def api_list_zonas(request: Request, db=Depends(SessionLocal)):
    items = store.list_zonas(db)
    return JSONResponse({"success": True, "data": [
        {
            "id": z.id, "name": z.name, "costo_envio": z.costo_envio,
            "monto_minimo_pedido": z.monto_minimo_pedido,
            "tiempo_entrega_minutos": z.tiempo_entrega_minutos,
            "acepta_pedidos": z.acepta_pedidos,
        }
        for z in items
    ]})


@router.post("/api/tortas/zonas")
async def api_create_zona(data: ZonaEntregaCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_zona(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.put("/api/tortas/zonas/{zona_id}")
async def api_update_zona(zona_id: int, data: ZonaEntregaUpdate, request: Request, db=Depends(SessionLocal)):
    obj = store.update_zona(db, zona_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    return JSONResponse({"success": True, "data": {"id": obj.id, "acepta_pedidos": obj.acepta_pedidos}})


@router.get("/api/tortas/zonas/{zona_id}/costo-envio")
async def api_costo_envio(zona_id: int, subtotal: float, request: Request, db=Depends(SessionLocal)):
    acepta, mensaje, costo = store.calcular_costo_envio(db, zona_id, subtotal)
    return JSONResponse({"success": True, "data": {"acepta": acepta, "mensaje": mensaje, "costo": costo}})


# ── API: Formas de pago ───────────────────────────────────────────────────────

@router.get("/api/tortas/formas-pago")
async def api_list_formas_pago(request: Request, db=Depends(SessionLocal)):
    items = store.list_formas_pago(db)
    return JSONResponse({"success": True, "data": [
        {"id": f.id, "name": f.name, "codigo": f.codigo, "icono": f.icono,
         "requiere_referencia": f.requiere_referencia}
        for f in items
    ]})


@router.post("/api/tortas/formas-pago")
async def api_create_forma_pago(data: FormaPagoCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_forma_pago(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


# ── API: Cupones ──────────────────────────────────────────────────────────────

@router.get("/api/tortas/cupones")
async def api_list_cupones(request: Request, db=Depends(SessionLocal)):
    items = store.list_cupones(db)
    return JSONResponse({"success": True, "data": [
        {
            "id": c.id, "name": c.name, "codigo": c.codigo,
            "tipo_descuento": c.tipo_descuento, "valor_descuento": c.valor_descuento,
            "fecha_inicio": c.fecha_inicio.isoformat(), "fecha_fin": c.fecha_fin.isoformat(),
        }
        for c in items
    ]})


@router.post("/api/tortas/cupones")
async def api_create_cupon(data: CuponCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_cupon(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "codigo": obj.codigo}})


@router.post("/api/tortas/cupones/validar")
async def api_validar_cupon(data: CuponValidarRequest, request: Request, db=Depends(SessionLocal)):
    valido, mensaje, monto = store.validar_cupon(db, data.codigo, data.subtotal)
    return JSONResponse({"success": True, "data": {
        "valido": valido, "mensaje": mensaje, "monto_descuento": monto,
    }})


# ── API: Pedidos ──────────────────────────────────────────────────────────────

@router.get("/api/tortas/pedidos")
async def api_list_pedidos(
    request: Request,
    db=Depends(SessionLocal),
    estado: Optional[str] = None,
    limit: int = 100,
):
    items = store.list_pedidos(db, estado=estado, limit=limit)
    return JSONResponse({"success": True, "data": [
        {
            "id": p.id,
            "numero_pedido": p.numero_pedido,
            "fecha_pedido": p.fecha_pedido.isoformat() if p.fecha_pedido else None,
            "nombre_cliente": p.nombre_cliente,
            "telefono": p.telefono,
            "tipo_pedido": p.tipo_pedido,
            "estado": p.estado,
            "prioridad": p.prioridad,
            "costo_envio": p.costo_envio,
            "descuento": p.descuento,
            "impuesto": p.impuesto,
            "ticket_impreso": p.ticket_impreso,
            "notas_cocina": p.notas_cocina,
        }
        for p in items
    ]})


@router.post("/api/tortas/pedidos")
async def api_create_pedido(data: PedidoCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_pedido(db, data)
    totales = store._calcular_totales_pedido(obj)
    return JSONResponse({"success": True, "data": {
        "id": obj.id,
        "numero_pedido": obj.numero_pedido,
        **totales,
    }})


@router.get("/api/tortas/pedidos/{pedido_id}")
async def api_get_pedido(pedido_id: int, request: Request, db=Depends(SessionLocal)):
    obj = store.get_pedido(db, pedido_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    totales = store._calcular_totales_pedido(obj)
    return JSONResponse({"success": True, "data": {
        "id": obj.id,
        "numero_pedido": obj.numero_pedido,
        "fecha_pedido": obj.fecha_pedido.isoformat() if obj.fecha_pedido else None,
        "nombre_cliente": obj.nombre_cliente,
        "telefono": obj.telefono,
        "tipo_pedido": obj.tipo_pedido,
        "estado": obj.estado,
        "prioridad": obj.prioridad,
        "notas": obj.notas,
        "notas_cocina": obj.notas_cocina,
        "lineas": [
            {
                "id": l.id,
                "torta_id": l.torta_id,
                "cantidad": l.cantidad,
                "precio_unitario": l.precio_unitario,
                "precio_pan": l.precio_pan,
                "notas": l.notas,
                "toppings": [
                    {"topping_id": t.topping_id, "cantidad": t.cantidad, "precio_unitario": t.precio_unitario}
                    for t in l.toppings
                ],
            }
            for l in obj.lineas
        ],
        **totales,
    }})


@router.put("/api/tortas/pedidos/{pedido_id}/estado")
async def api_update_estado_pedido(pedido_id: int, request: Request, db=Depends(SessionLocal)):
    body = await request.json()
    estado = body.get("estado", "")
    estados_validos = ["borrador", "confirmado", "en_preparacion", "listo", "entregado", "cancelado"]
    if estado not in estados_validos:
        raise HTTPException(status_code=400, detail="Estado inválido")
    obj = store.update_estado_pedido(db, pedido_id, estado)
    if not obj:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return JSONResponse({"success": True, "data": {"id": obj.id, "estado": obj.estado}})


# ── API: Pagos de pedido ──────────────────────────────────────────────────────

@router.get("/api/tortas/pedidos/{pedido_id}/pagos")
async def api_list_pagos(pedido_id: int, request: Request, db=Depends(SessionLocal)):
    items = store.list_pagos_pedido(db, pedido_id)
    return JSONResponse({"success": True, "data": [
        {
            "id": p.id, "monto": p.monto, "fecha": p.fecha.isoformat() if p.fecha else None,
            "forma_pago_id": p.forma_pago_id, "cancelado": p.cancelado, "referencia": p.referencia,
        }
        for p in items
    ]})


@router.post("/api/tortas/pedidos/{pedido_id}/pagos")
async def api_create_pago(pedido_id: int, data: PagoCreate, request: Request, db=Depends(SessionLocal)):
    pedido = store.get_pedido(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    obj = store.create_pago(db, pedido_id, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "monto": obj.monto}})


# ── API: Cortes de caja ───────────────────────────────────────────────────────

@router.get("/api/tortas/cortes")
async def api_list_cortes(request: Request, db=Depends(SessionLocal)):
    items = store.list_cortes(db)
    return JSONResponse({"success": True, "data": [
        {
            "id": c.id, "name": c.name,
            "fecha_inicio": c.fecha_inicio.isoformat() if c.fecha_inicio else None,
            "fecha_cierre": c.fecha_cierre.isoformat() if c.fecha_cierre else None,
            "estado": c.estado, "monto_inicial": c.monto_inicial,
        }
        for c in items
    ]})


@router.post("/api/tortas/cortes")
async def api_create_corte(data: CorteCajaCreate, request: Request, db=Depends(SessionLocal)):
    abierto = store.get_corte_abierto(db)
    if abierto:
        raise HTTPException(status_code=400, detail=f"Ya hay un corte abierto: {abierto.name}")
    obj = store.create_corte(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.put("/api/tortas/cortes/{corte_id}/cerrar")
async def api_cerrar_corte(corte_id: int, data: CorteCajaCerrarRequest, request: Request, db=Depends(SessionLocal)):
    obj = store.cerrar_corte(db, corte_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Corte no encontrado o ya cerrado")
    return JSONResponse({"success": True, "data": {
        "id": obj.id, "name": obj.name, "estado": obj.estado,
        "fecha_cierre": obj.fecha_cierre.isoformat() if obj.fecha_cierre else None,
    }})


# ── API: Preordenes ───────────────────────────────────────────────────────────

@router.get("/api/tortas/preordenes")
async def api_list_preordenes(
    request: Request,
    db=Depends(SessionLocal),
    state: Optional[str] = None,
    limit: int = 100,
):
    items = store.list_preordenes(db, state=state, limit=limit)
    return JSONResponse({"success": True, "data": [
        {
            "id": p.id, "name": p.name, "nombre_cliente": p.nombre_cliente,
            "fecha_entrega": p.fecha_entrega.isoformat() if p.fecha_entrega else None,
            "hora_entrega": p.hora_entrega, "tipo_pedido": p.tipo_pedido,
            "state": p.state, "pedido_id": p.pedido_id,
        }
        for p in items
    ]})


@router.post("/api/tortas/preordenes")
async def api_create_preorden(data: PreordenCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_preorden(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.put("/api/tortas/preordenes/{preorden_id}/estado")
async def api_update_estado_preorden(preorden_id: int, request: Request, db=Depends(SessionLocal)):
    body = await request.json()
    state = body.get("state", "")
    estados_validos = ["borrador", "confirmado", "recordatorio_enviado", "pedido_generado", "cancelado"]
    if state not in estados_validos:
        raise HTTPException(status_code=400, detail="Estado inválido")
    obj = store.update_estado_preorden(db, preorden_id, state)
    if not obj:
        raise HTTPException(status_code=404, detail="Preorden no encontrada")
    return JSONResponse({"success": True, "data": {"id": obj.id, "state": obj.state}})


@router.post("/api/tortas/preordenes/{preorden_id}/generar-pedido")
async def api_generar_pedido_preorden(preorden_id: int, request: Request, db=Depends(SessionLocal)):
    pedido = store.generar_pedido_desde_preorden(db, preorden_id)
    if not pedido:
        raise HTTPException(status_code=400, detail="No se puede generar el pedido. Verifique que la preorden esté confirmada.")
    return JSONResponse({"success": True, "data": {
        "pedido_id": pedido.id, "numero_pedido": pedido.numero_pedido,
    }})


# ── API: Stats ────────────────────────────────────────────────────────────────

@router.get("/api/tortas/stats")
async def api_stats(request: Request, db=Depends(SessionLocal)):
    stats = store.get_dashboard_stats(db)
    return JSONResponse({"success": True, "data": stats})


__all__ = ["router"]
