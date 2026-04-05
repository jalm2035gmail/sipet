from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import render_backend_page_html
from fastapi_modulo.modulos.tortas.modelos.db_models import ensure_tortas_schema
from fastapi_modulo.modulos.tortas.modelos.schemas import (
    CategoriaCreate, AlergenoCreate, BaseProductoCreate, BaseProductoUpdate,
    ToppingCreate, TortaCreate, TortaUpdate,
    ZonaEntregaCreate, ZonaEntregaUpdate, FormaPagoCreate,
    CanalVentaCreate, ConceptoCreate,
    CuponCreate, CuponValidarRequest,
    PedidoCreate, PagoCreate,
    CorteCajaCreate, CorteCajaCerrarRequest,
    PreordenCreate,
    # Fase 3
    ClienteCreate, ClienteUpdate, DireccionClienteCreate,
    # Fase 4
    PlantillaMensajeCreate, MensajePedidoCreate, OrigenPedidoCreate, RenderPlantillaRequest,
    # Fase 5
    EstacionCocinaCreate, TiempoProduccionCreate, TicketCocinaCreate,
    ActualizarEstadoTicketRequest, ActualizarEstadoLineaTicketRequest,
    # Fase 6
    AjustePuntosRequest, RecompensaCreate, CanjearRecompensaRequest,
    PreferenciaClienteCreate, PromocionClienteCreate,
    # Fase 7
    RepartidorCreate, EntregaCreate, AsignarRepartidorRequest,
    ActualizarEstadoEntregaRequest, RegistrarEvidenciaRequest,
    # Fase 8
    CajaCreate, TurnoCreate, CerrarTurnoRequest, CerrarCorteRequest,
    AnulacionCreate, DevolucionCreate,
    # Fase 9
    PromocionCreate, EvaluarPromocionesRequest,
    ComboCreate,
    # Fase 10
    InsumoCreate, MovimientoInsumoCreate, AjusteStockRequest,
    RecetaCreate, OpcionModificadorInsumoCreate, DescontarStockPedidoRequest,
    # Fase 11
    ReportePeriodoRequest,
    # Fase 12
    AutomatizacionCreate, WebhookSalidaCreate, DisparadorEventoRequest,
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
        title="Restaurante",
        description="Sistema de gestión de restaurante y comida",
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
            "canal_venta_id": p.canal_venta_id,
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
        "canal_venta_id": obj.canal_venta_id,
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
                "base_id": l.base_id,
                "precio_base": l.precio_base,
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
    estados_validos = ["borrador", "confirmado", "enviado_cocina", "en_preparacion",
                       "en_empaque", "listo", "en_reparto", "entregado",
                       "no_entregado", "cancelado"]
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


# ── API: Canales de venta ─────────────────────────────────────────────────────

@router.get("/api/tortas/canales-venta")
async def api_list_canales_venta(request: Request, db=Depends(SessionLocal)):
    items = store.list_canales_venta(db)
    return JSONResponse({"success": True, "data": [
        {
            "id": c.id, "name": c.name, "codigo": c.codigo,
            "icono": c.icono, "requiere_confirmacion": c.requiere_confirmacion,
        }
        for c in items
    ]})


@router.post("/api/tortas/canales-venta")
async def api_create_canal_venta(data: CanalVentaCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_canal_venta(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name, "codigo": obj.codigo}})


# ── API: Concepto de restaurante ──────────────────────────────────────────────

@router.get("/api/tortas/concepto")
async def api_get_concepto(request: Request, db=Depends(SessionLocal)):
    obj = store.get_concepto(db)
    if not obj:
        return JSONResponse({"success": True, "data": None})
    return JSONResponse({"success": True, "data": {
        "id": obj.id,
        "name": obj.name,
        "tipo_cocina": obj.tipo_cocina,
        "icono": obj.icono,
        "color_primario": obj.color_primario,
        "label_producto": obj.label_producto,
        "label_base": obj.label_base,
        "label_modificador": obj.label_modificador,
    }})


@router.post("/api/tortas/concepto")
async def api_create_concepto(data: ConceptoCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_concepto(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})



# ── API: Clientes ─────────────────────────────────────────────────────────────

@router.get("/api/tortas/clientes")
async def api_list_clientes(request: Request, q: str = "", db=Depends(SessionLocal)):
    items = store.list_clientes(db, q=q)
    return JSONResponse({"success": True, "data": [
        {
            "id": c.id, "nombre": c.nombre, "telefono": c.telefono,
            "email": c.email, "activo": c.activo,
            "num_pedidos": len(c.pedidos),
        }
        for c in items
    ]})


@router.get("/api/tortas/clientes/buscar")
async def api_buscar_cliente(request: Request, telefono: str = "", q: str = "", db=Depends(SessionLocal)):
    if telefono:
        obj = store.get_cliente_by_telefono(db, telefono)
        if not obj:
            return JSONResponse({"success": True, "data": None})
        return JSONResponse({"success": True, "data": {
            "id": obj.id, "nombre": obj.nombre, "telefono": obj.telefono,
            "email": obj.email, "activo": obj.activo,
            "direcciones": [
                {
                    "id": d.id, "alias": d.alias, "calle": d.calle,
                    "numero_exterior": d.numero_exterior,
                    "colonia": d.colonia, "ciudad": d.ciudad,
                    "codigo_postal": d.codigo_postal,
                    "referencias": d.referencias, "predeterminada": d.predeterminada,
                }
                for d in obj.direcciones if d.activa
            ],
        }})
    items = store.list_clientes(db, q=q)
    return JSONResponse({"success": True, "data": [
        {"id": c.id, "nombre": c.nombre, "telefono": c.telefono, "email": c.email}
        for c in items
    ]})


@router.get("/api/tortas/clientes/{cliente_id}")
async def api_get_cliente(cliente_id: int, request: Request, db=Depends(SessionLocal)):
    obj = store.get_cliente(db, cliente_id)
    if not obj:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True, "data": {
        "id": obj.id, "nombre": obj.nombre, "telefono": obj.telefono,
        "email": obj.email, "notas": obj.notas, "activo": obj.activo,
        "direcciones": [
            {
                "id": d.id, "alias": d.alias, "calle": d.calle,
                "numero_exterior": d.numero_exterior,
                "colonia": d.colonia, "ciudad": d.ciudad,
                "codigo_postal": d.codigo_postal,
                "referencias": d.referencias,
                "predeterminada": d.predeterminada, "activa": d.activa,
            }
            for d in obj.direcciones
        ],
        "pedidos_recientes": [
            {"id": p.id, "numero_pedido": p.numero_pedido, "estado": p.estado,
             "total": p.total}
            for p in sorted(obj.pedidos, key=lambda x: x.id, reverse=True)[:10]
        ],
    }})


@router.post("/api/tortas/clientes")
async def api_create_cliente(data: ClienteCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_cliente(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "nombre": obj.nombre}}, status_code=201)


@router.put("/api/tortas/clientes/{cliente_id}")
async def api_update_cliente(cliente_id: int, data: ClienteUpdate, request: Request, db=Depends(SessionLocal)):
    obj = store.update_cliente(db, cliente_id, data)
    if not obj:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True, "data": {"id": obj.id, "nombre": obj.nombre}})


# ── API: Direcciones del cliente ──────────────────────────────────────────────

@router.get("/api/tortas/clientes/{cliente_id}/direcciones")
async def api_list_direcciones(cliente_id: int, request: Request, db=Depends(SessionLocal)):
    items = store.list_direcciones_cliente(db, cliente_id)
    return JSONResponse({"success": True, "data": [
        {
            "id": d.id, "alias": d.alias, "calle": d.calle,
            "numero_exterior": d.numero_exterior, "numero_interior": d.numero_interior,
            "colonia": d.colonia, "ciudad": d.ciudad,
            "codigo_postal": d.codigo_postal, "referencias": d.referencias,
            "lat": d.lat, "lng": d.lng,
            "predeterminada": d.predeterminada, "activa": d.activa,
        }
        for d in items
    ]})


@router.post("/api/tortas/clientes/{cliente_id}/direcciones")
async def api_create_direccion(cliente_id: int, data: DireccionClienteCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_direccion_cliente(db, cliente_id, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "alias": obj.alias}}, status_code=201)


@router.put("/api/tortas/clientes/direcciones/{dir_id}")
async def api_update_direccion(dir_id: int, data: DireccionClienteCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.update_direccion_cliente(db, dir_id, data)
    if not obj:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True, "data": {"id": obj.id, "alias": obj.alias}})


@router.delete("/api/tortas/clientes/direcciones/{dir_id}")
async def api_delete_direccion(dir_id: int, request: Request, db=Depends(SessionLocal)):
    ok = store.delete_direccion_cliente(db, dir_id)
    if not ok:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True})



# ── API: Plantillas de mensaje ────────────────────────────────────────────────

@router.get("/api/tortas/plantillas-mensaje")
async def api_list_plantillas(
    request: Request,
    canal: str = "",
    tipo: str = "",
    db=Depends(SessionLocal),
):
    items = store.list_plantillas_mensaje(db, canal=canal or None, tipo=tipo or None)
    return JSONResponse({"success": True, "data": [
        {
            "id": p.id, "name": p.name, "tipo": p.tipo,
            "canal": p.canal, "cuerpo": p.cuerpo, "activo": p.activo,
        }
        for p in items
    ]})


@router.post("/api/tortas/plantillas-mensaje")
async def api_create_plantilla(data: PlantillaMensajeCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_plantilla_mensaje(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}}, status_code=201)


@router.put("/api/tortas/plantillas-mensaje/{plantilla_id}")
async def api_update_plantilla(plantilla_id: int, data: PlantillaMensajeCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.update_plantilla_mensaje(db, plantilla_id, data)
    if not obj:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.delete("/api/tortas/plantillas-mensaje/{plantilla_id}")
async def api_delete_plantilla(plantilla_id: int, request: Request, db=Depends(SessionLocal)):
    ok = store.delete_plantilla_mensaje(db, plantilla_id)
    if not ok:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True})


@router.post("/api/tortas/plantillas-mensaje/render")
async def api_render_plantilla(data: RenderPlantillaRequest, request: Request, db=Depends(SessionLocal)):
    texto = store.render_plantilla(db, data.plantilla_id, data.pedido_id)
    return JSONResponse({"success": True, "data": {"texto": texto}})


# ── API: Mensajes del pedido ──────────────────────────────────────────────────

@router.get("/api/tortas/pedidos/{pedido_id}/mensajes")
async def api_list_mensajes_pedido(pedido_id: int, request: Request, db=Depends(SessionLocal)):
    items = store.list_mensajes_pedido(db, pedido_id)
    return JSONResponse({"success": True, "data": [
        {
            "id": m.id, "pedido_id": m.pedido_id, "direccion": m.direccion,
            "canal": m.canal, "plantilla_id": m.plantilla_id,
            "cuerpo": m.cuerpo, "estado": m.estado,
            "referencia_externa": m.referencia_externa,
            "enviado_por": m.enviado_por,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in items
    ]})


@router.post("/api/tortas/pedidos/{pedido_id}/mensajes")
async def api_create_mensaje_pedido(pedido_id: int, data: MensajePedidoCreate, request: Request, db=Depends(SessionLocal)):
    data.pedido_id = pedido_id
    obj = store.create_mensaje_pedido(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "estado": obj.estado}}, status_code=201)


@router.put("/api/tortas/mensajes/{mensaje_id}/enviado")
async def api_marcar_mensaje_enviado(mensaje_id: int, request: Request, db=Depends(SessionLocal)):
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    ref = body.get("referencia_externa", "") if isinstance(body, dict) else ""
    ok = store.marcar_mensaje_enviado(db, mensaje_id, ref)
    if not ok:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True})


# ── API: Origen del pedido ────────────────────────────────────────────────────

@router.get("/api/tortas/pedidos/{pedido_id}/origen")
async def api_get_origen_pedido(pedido_id: int, request: Request, db=Depends(SessionLocal)):
    obj = store.get_origen_pedido(db, pedido_id)
    if not obj:
        return JSONResponse({"success": True, "data": None})
    return JSONResponse({"success": True, "data": {
        "id": obj.id, "pedido_id": obj.pedido_id,
        "operador_nombre": obj.operador_nombre,
        "telefono_origen": obj.telefono_origen,
        "referencia_chat": obj.referencia_chat,
        "plataforma": obj.plataforma,
        "script_usado": obj.script_usado,
        "notas_operador": obj.notas_operador,
        "duracion_llamada_seg": obj.duracion_llamada_seg,
    }})


@router.post("/api/tortas/pedidos/{pedido_id}/origen")
async def api_create_or_update_origen(pedido_id: int, data: OrigenPedidoCreate, request: Request, db=Depends(SessionLocal)):
    data.pedido_id = pedido_id
    obj = store.create_or_update_origen_pedido(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id}})



# ── API: Estaciones de cocina ─────────────────────────────────────────────────

@router.get("/api/tortas/estaciones-cocina")
async def api_list_estaciones(request: Request, db=Depends(SessionLocal)):
    items = store.list_estaciones_cocina(db)
    return JSONResponse({"success": True, "data": [
        {
            "id": e.id, "name": e.name, "codigo": e.codigo,
            "descripcion": e.descripcion, "activa": e.activa,
            "sequence": e.sequence, "color": e.color, "icono": e.icono,
        }
        for e in items
    ]})


@router.post("/api/tortas/estaciones-cocina")
async def api_create_estacion(data: EstacionCocinaCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_estacion_cocina(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}}, status_code=201)


@router.put("/api/tortas/estaciones-cocina/{estacion_id}")
async def api_update_estacion(estacion_id: int, data: EstacionCocinaCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.update_estacion_cocina(db, estacion_id, data)
    if not obj:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


# ── API: Tiempos de producción ────────────────────────────────────────────────

@router.get("/api/tortas/tiempos-produccion")
async def api_list_tiempos(request: Request, torta_id: int = 0, db=Depends(SessionLocal)):
    items = store.list_tiempos_produccion(db, torta_id=torta_id or None)
    return JSONResponse({"success": True, "data": [
        {
            "id": t.id, "torta_id": t.torta_id, "estacion_id": t.estacion_id,
            "variante_id": t.variante_id, "minutos": t.minutos,
        }
        for t in items
    ]})


@router.post("/api/tortas/tiempos-produccion")
async def api_create_tiempo(data: TiempoProduccionCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_tiempo_produccion(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "minutos": obj.minutos}}, status_code=201)


@router.get("/api/tortas/pedidos/{pedido_id}/tiempo-estimado")
async def api_calcular_tiempo(pedido_id: int, request: Request, db=Depends(SessionLocal)):
    minutos = store.calcular_tiempo_pedido(db, pedido_id)
    return JSONResponse({"success": True, "data": {"minutos": minutos}})


# ── API: Cola de cocina (tablero operativo) ───────────────────────────────────

@router.get("/api/tortas/cola-cocina")
async def api_cola_cocina(
    request: Request,
    estacion_id: int = 0,
    estados: str = "pendiente,en_preparacion",
    db=Depends(SessionLocal),
):
    estados_lista = [s.strip() for s in estados.split(",") if s.strip()]
    items = store.get_cola_cocina(db, estacion_id=estacion_id or None, estados=estados_lista)
    return JSONResponse({"success": True, "data": [
        {
            "id": t.id,
            "numero_ticket": t.numero_ticket,
            "pedido_id": t.pedido_id,
            "numero_pedido": t.pedido.numero_pedido if t.pedido else "",
            "estacion_id": t.estacion_id,
            "estado": t.estado,
            "prioridad": t.prioridad,
            "notas": t.notas,
            "impreso": t.impreso,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "lineas": [
                {
                    "id": l.id,
                    "descripcion": l.descripcion,
                    "cantidad": l.cantidad,
                    "variante": l.variante,
                    "modificadores_texto": l.modificadores_texto,
                    "notas": l.notas,
                    "estado": l.estado,
                }
                for l in t.lineas
            ],
        }
        for t in items
    ]})


# ── API: Tickets de cocina ────────────────────────────────────────────────────

@router.get("/api/tortas/pedidos/{pedido_id}/tickets-cocina")
async def api_tickets_por_pedido(pedido_id: int, request: Request, db=Depends(SessionLocal)):
    items = store.get_ticket_por_pedido(db, pedido_id)
    return JSONResponse({"success": True, "data": [
        {
            "id": t.id, "numero_ticket": t.numero_ticket,
            "estacion_id": t.estacion_id, "estado": t.estado,
            "prioridad": t.prioridad, "notas": t.notas, "impreso": t.impreso,
            "lineas": [
                {
                    "id": l.id, "descripcion": l.descripcion,
                    "cantidad": l.cantidad, "variante": l.variante,
                    "modificadores_texto": l.modificadores_texto,
                    "notas": l.notas, "estado": l.estado,
                }
                for l in t.lineas
            ],
        }
        for t in items
    ]})


@router.post("/api/tortas/tickets-cocina")
async def api_generar_ticket(data: TicketCocinaCreate, request: Request, db=Depends(SessionLocal)):
    try:
        ticket = store.generar_ticket_cocina(db, data)
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=404)
    return JSONResponse({"success": True, "data": {
        "id": ticket.id, "numero_ticket": ticket.numero_ticket, "estado": ticket.estado,
    }}, status_code=201)


@router.put("/api/tortas/tickets-cocina/{ticket_id}/estado")
async def api_actualizar_estado_ticket(ticket_id: int, data: ActualizarEstadoTicketRequest, request: Request, db=Depends(SessionLocal)):
    obj = store.actualizar_estado_ticket(db, ticket_id, data)
    if not obj:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True, "data": {"id": obj.id, "estado": obj.estado}})


@router.put("/api/tortas/tickets-cocina/{ticket_id}/impreso")
async def api_marcar_impreso(ticket_id: int, request: Request, db=Depends(SessionLocal)):
    ok = store.marcar_ticket_impreso(db, ticket_id)
    if not ok:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True})


@router.put("/api/tortas/tickets-cocina/lineas/{linea_id}/estado")
async def api_actualizar_estado_linea(linea_id: int, data: ActualizarEstadoLineaTicketRequest, request: Request, db=Depends(SessionLocal)):
    obj = store.actualizar_estado_linea_ticket(db, linea_id, data)
    if not obj:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return JSONResponse({"success": True, "data": {"id": obj.id, "estado": obj.estado}})



# ── Fase 6: Clientes y fidelización ──────────────────────────────────────────

# ---- Stats y puntos ---------------------------------------------------------

@router.get("/api/tortas/clientes/{cliente_id}/stats")
def ep_stats_cliente(cliente_id: int, db=Depends(get_db)):
    stats = get_stats_cliente(db, cliente_id)
    if not stats:
        return JSONResponse({"error": "no encontrado"}, 404)
    return JSONResponse(stats)

@router.get("/api/tortas/clientes/{cliente_id}/puntos")
def ep_historial_puntos(cliente_id: int, limit: int = 30, db=Depends(get_db)):
    movs = get_historial_puntos(db, cliente_id, limit=limit)
    from ..modelos.schemas import PuntosHistorialRead
    return JSONResponse([PuntosHistorialRead.model_validate(m).model_dump() for m in movs])

@router.post("/api/tortas/clientes/{cliente_id}/puntos/ajuste")
def ep_ajustar_puntos(cliente_id: int, data: AjustePuntosRequest, db=Depends(get_db)):
    return JSONResponse(ajustar_puntos(db, cliente_id, data))

# ---- Recompensas ------------------------------------------------------------

@router.get("/api/tortas/recompensas")
def ep_list_recompensas(todas: bool = False, db=Depends(get_db)):
    items = list_recompensas(db, solo_activas=not todas)
    from ..modelos.schemas import RecompensaRead
    return JSONResponse([RecompensaRead.model_validate(r).model_dump() for r in items])

@router.post("/api/tortas/recompensas")
def ep_create_recompensa(data: RecompensaCreate, db=Depends(get_db)):
    obj = create_recompensa(db, data)
    from ..modelos.schemas import RecompensaRead
    return JSONResponse(RecompensaRead.model_validate(obj).model_dump(), status_code=201)

@router.post("/api/tortas/clientes/{cliente_id}/canjear")
def ep_canjear_recompensa(cliente_id: int, data: CanjearRecompensaRequest, db=Depends(get_db)):
    result = canjear_recompensa(db, cliente_id, data)
    status = 200 if result.get("ok") else 400
    return JSONResponse(result, status_code=status)

# ---- Preferencias -----------------------------------------------------------

@router.get("/api/tortas/clientes/{cliente_id}/preferencias")
def ep_list_preferencias(cliente_id: int, db=Depends(get_db)):
    items = list_preferencias_cliente(db, cliente_id)
    from ..modelos.schemas import PreferenciaClienteRead
    return JSONResponse([PreferenciaClienteRead.model_validate(p).model_dump() for p in items])

@router.post("/api/tortas/clientes/{cliente_id}/preferencias")
def ep_create_preferencia(cliente_id: int, data: PreferenciaClienteCreate, db=Depends(get_db)):
    obj = create_preferencia_cliente(db, cliente_id, data)
    from ..modelos.schemas import PreferenciaClienteRead
    return JSONResponse(PreferenciaClienteRead.model_validate(obj).model_dump(), status_code=201)

@router.delete("/api/tortas/clientes/{cliente_id}/preferencias/{pref_id}")
def ep_delete_preferencia(cliente_id: int, pref_id: int, db=Depends(get_db)):
    return JSONResponse(delete_preferencia_cliente(db, pref_id, cliente_id))

# ---- Promociones personales -------------------------------------------------

@router.get("/api/tortas/clientes/{cliente_id}/promociones")
def ep_list_promociones(cliente_id: int, todas: bool = False, db=Depends(get_db)):
    items = list_promociones_cliente(db, cliente_id, solo_activas=not todas)
    from ..modelos.schemas import PromocionClienteRead
    return JSONResponse([PromocionClienteRead.model_validate(p).model_dump() for p in items])

@router.post("/api/tortas/clientes/{cliente_id}/promociones")
def ep_create_promocion(cliente_id: int, data: PromocionClienteCreate, db=Depends(get_db)):
    obj = create_promocion_cliente(db, cliente_id, data)
    from ..modelos.schemas import PromocionClienteRead
    return JSONResponse(PromocionClienteRead.model_validate(obj).model_dump(), status_code=201)


# ── Fase 7: Entrega y logística ───────────────────────────────────────────────

# ---- Repartidores -----------------------------------------------------------

@router.get("/api/tortas/repartidores")
def ep_list_repartidores(todos: bool = False, db=Depends(get_db)):
    items = list_repartidores(db, solo_activos=not todos)
    from ..modelos.schemas import RepartidorRead
    return JSONResponse([RepartidorRead.model_validate(r).model_dump() for r in items])

@router.post("/api/tortas/repartidores")
def ep_create_repartidor(data: RepartidorCreate, db=Depends(get_db)):
    obj = create_repartidor(db, data)
    from ..modelos.schemas import RepartidorRead
    return JSONResponse(RepartidorRead.model_validate(obj).model_dump(), status_code=201)

@router.put("/api/tortas/repartidores/{repartidor_id}")
def ep_update_repartidor(repartidor_id: int, data: RepartidorCreate, db=Depends(get_db)):
    result = update_repartidor(db, repartidor_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

@router.patch("/api/tortas/repartidores/{repartidor_id}/disponibilidad")
def ep_disponibilidad_repartidor(repartidor_id: int, disponible: bool, db=Depends(get_db)):
    return JSONResponse(set_disponibilidad_repartidor(db, repartidor_id, disponible))

@router.get("/api/tortas/repartidores/{repartidor_id}/entregas")
def ep_entregas_repartidor(repartidor_id: int, activas: bool = True, db=Depends(get_db)):
    items = get_entregas_repartidor(db, repartidor_id, activas=activas)
    from ..modelos.schemas import EntregaRead
    return JSONResponse([EntregaRead.model_validate(e).model_dump() for e in items])

# ---- Entregas ---------------------------------------------------------------

@router.get("/api/tortas/entregas/pendientes")
def ep_entregas_pendientes(db=Depends(get_db)):
    items = get_entregas_pendientes(db)
    from ..modelos.schemas import EntregaRead
    return JSONResponse([EntregaRead.model_validate(e).model_dump() for e in items])

@router.post("/api/tortas/pedidos/{pedido_id}/entrega")
def ep_create_entrega(pedido_id: int, data: EntregaCreate, db=Depends(get_db)):
    data.pedido_id = pedido_id
    result = create_entrega(db, data)
    status = 201 if result.get("ok") else 400
    return JSONResponse(result, status_code=status)

@router.get("/api/tortas/pedidos/{pedido_id}/entrega")
def ep_get_entrega_pedido(pedido_id: int, db=Depends(get_db)):
    obj = get_entrega_pedido(db, pedido_id)
    if not obj:
        return JSONResponse({"error": "no encontrada"}, 404)
    from ..modelos.schemas import EntregaRead
    return JSONResponse(EntregaRead.model_validate(obj).model_dump())

@router.put("/api/tortas/entregas/{entrega_id}/asignar-repartidor")
def ep_asignar_repartidor(entrega_id: int, data: AsignarRepartidorRequest, db=Depends(get_db)):
    result = asignar_repartidor(db, entrega_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

@router.put("/api/tortas/entregas/{entrega_id}/estado")
def ep_estado_entrega(entrega_id: int, data: ActualizarEstadoEntregaRequest, db=Depends(get_db)):
    result = actualizar_estado_entrega(db, entrega_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

@router.put("/api/tortas/entregas/{entrega_id}/evidencia")
def ep_evidencia_entrega(entrega_id: int, data: RegistrarEvidenciaRequest, db=Depends(get_db)):
    result = registrar_evidencia_entrega(db, entrega_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)


# ── Fase 8: Caja y administración ─────────────────────────────────────────────

# ---- Cajas ------------------------------------------------------------------

@router.get("/api/tortas/cajas")
def ep_list_cajas(todas: bool = False, db=Depends(get_db)):
    items = list_cajas(db, solo_activas=not todas)
    from ..modelos.schemas import CajaRead
    return JSONResponse([CajaRead.model_validate(c).model_dump() for c in items])

@router.post("/api/tortas/cajas")
def ep_create_caja(data: CajaCreate, db=Depends(get_db)):
    obj = create_caja(db, data)
    from ..modelos.schemas import CajaRead
    return JSONResponse(CajaRead.model_validate(obj).model_dump(), status_code=201)

@router.put("/api/tortas/cajas/{caja_id}")
def ep_update_caja(caja_id: int, data: CajaCreate, db=Depends(get_db)):
    result = update_caja(db, caja_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

# ---- Turnos -----------------------------------------------------------------

@router.get("/api/tortas/turnos")
def ep_list_turnos(caja_id: int = None, solo_abiertos: bool = False, db=Depends(get_db)):
    items = list_turnos(db, caja_id=caja_id, solo_abiertos=solo_abiertos)
    from ..modelos.schemas import TurnoRead
    return JSONResponse([TurnoRead.model_validate(t).model_dump() for t in items])

@router.get("/api/tortas/turnos/activo")
def ep_turno_activo(caja_id: int = None, db=Depends(get_db)):
    obj = get_turno_activo(db, caja_id=caja_id)
    if not obj:
        return JSONResponse({"error": "no hay turno abierto"}, 404)
    from ..modelos.schemas import TurnoRead
    return JSONResponse(TurnoRead.model_validate(obj).model_dump())

@router.post("/api/tortas/turnos/abrir")
def ep_abrir_turno(data: TurnoCreate, db=Depends(get_db)):
    result = abrir_turno(db, data)
    status = 201 if result.get("ok") else 400
    return JSONResponse(result, status_code=status)

@router.post("/api/tortas/turnos/{turno_id}/cerrar")
def ep_cerrar_turno(turno_id: int, data: CerrarTurnoRequest, db=Depends(get_db)):
    result = cerrar_turno(db, turno_id, data)
    status = 200 if result.get("ok") else 400
    return JSONResponse(result, status_code=status)

# ---- Cortes de caja ---------------------------------------------------------

@router.post("/api/tortas/cortes/{corte_id}/cerrar")
def ep_cerrar_corte(corte_id: int, data: CerrarCorteRequest, db=Depends(get_db)):
    result = cerrar_corte(db, corte_id, data)
    status = 200 if result.get("ok") else 400
    return JSONResponse(result, status_code=status)

@router.get("/api/tortas/cortes/{corte_id}/kpis")
def ep_kpis_corte(corte_id: int, db=Depends(get_db)):
    result = get_kpis_corte(db, corte_id)
    if not result:
        return JSONResponse({"error": "no encontrado"}, 404)
    return JSONResponse(result)

# ---- Anulaciones ------------------------------------------------------------

@router.get("/api/tortas/anulaciones")
def ep_list_anulaciones(corte_id: int = None, pedido_id: int = None, db=Depends(get_db)):
    items = list_anulaciones(db, corte_id=corte_id, pedido_id=pedido_id)
    from ..modelos.schemas import AnulacionRead
    return JSONResponse([AnulacionRead.model_validate(a).model_dump() for a in items])

@router.post("/api/tortas/anulaciones")
def ep_create_anulacion(data: AnulacionCreate, db=Depends(get_db)):
    result = create_anulacion(db, data)
    status = 201 if result.get("ok") else 400
    return JSONResponse(result, status_code=status)

# ---- Devoluciones -----------------------------------------------------------

@router.get("/api/tortas/devoluciones")
def ep_list_devoluciones(corte_id: int = None, pedido_id: int = None, db=Depends(get_db)):
    items = list_devoluciones(db, corte_id=corte_id, pedido_id=pedido_id)
    from ..modelos.schemas import DevolucionRead
    return JSONResponse([DevolucionRead.model_validate(d).model_dump() for d in items])

@router.post("/api/tortas/devoluciones")
def ep_create_devolucion(data: DevolucionCreate, db=Depends(get_db)):
    result = create_devolucion(db, data)
    status = 201 if result.get("ok") else 400
    return JSONResponse(result, status_code=status)


# ── Fase 9: Promociones y combos ─────────────────────────────────────────────

# ---- Promociones ------------------------------------------------------------

@router.get("/api/tortas/promociones")
def ep_list_promociones(todas: bool = False, canal_venta_id: int = None,
                        concepto_id: int = None, db=Depends(get_db)):
    items = list_promociones(db, solo_activas=not todas,
                             canal_venta_id=canal_venta_id, concepto_id=concepto_id)
    from ..modelos.schemas import PromocionRead
    return JSONResponse([PromocionRead.model_validate(p).model_dump() for p in items])

@router.post("/api/tortas/promociones")
def ep_create_promocion(data: PromocionCreate, db=Depends(get_db)):
    obj = create_promocion(db, data)
    from ..modelos.schemas import PromocionRead
    return JSONResponse(PromocionRead.model_validate(obj).model_dump(), status_code=201)

@router.put("/api/tortas/promociones/{promocion_id}")
def ep_update_promocion(promocion_id: int, data: PromocionCreate, db=Depends(get_db)):
    result = update_promocion(db, promocion_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

@router.post("/api/tortas/promociones/evaluar")
def ep_evaluar_promociones(data: EvaluarPromocionesRequest, db=Depends(get_db)):
    result = evaluar_promociones(db, data)
    from ..modelos.schemas import PromocionRead
    return JSONResponse({
        "descuento_total": result["descuento_total"],
        "detalle": result["detalle"],
        "promociones_aplicables": [
            PromocionRead.model_validate(p).model_dump()
            for p in result["promociones_aplicables"]
        ],
    })

@router.get("/api/tortas/promociones/{promocion_id}/usos")
def ep_usos_promocion(promocion_id: int, limit: int = 50, db=Depends(get_db)):
    items = list_usos_promocion(db, promocion_id, limit=limit)
    from ..modelos.schemas import PromocionUsoRead
    return JSONResponse([PromocionUsoRead.model_validate(u).model_dump() for u in items])

@router.post("/api/tortas/promociones/{promocion_id}/registrar-uso")
def ep_registrar_uso_promocion(promocion_id: int, pedido_id: int = None,
                                cliente_id: int = None, monto_descuento: float = 0.0,
                                descripcion: str = "", db=Depends(get_db)):
    registrar_promocion_uso(db, promocion_id, pedido_id=pedido_id,
                            cliente_id=cliente_id, monto_descuento=monto_descuento,
                            descripcion=descripcion)
    return JSONResponse({"ok": True})

# ---- Combos -----------------------------------------------------------------

@router.get("/api/tortas/combos")
def ep_list_combos(todos: bool = False, concepto_id: int = None, db=Depends(get_db)):
    items = list_combos(db, solo_activos=not todos, concepto_id=concepto_id)
    from ..modelos.schemas import ComboRead
    return JSONResponse([ComboRead.model_validate(c).model_dump() for c in items])

@router.get("/api/tortas/combos/{combo_id}")
def ep_get_combo(combo_id: int, db=Depends(get_db)):
    obj = get_combo(db, combo_id)
    if not obj:
        return JSONResponse({"error": "no encontrado"}, 404)
    from ..modelos.schemas import ComboRead
    return JSONResponse(ComboRead.model_validate(obj).model_dump())

@router.post("/api/tortas/combos")
def ep_create_combo(data: ComboCreate, db=Depends(get_db)):
    obj = create_combo(db, data)
    from ..modelos.schemas import ComboRead
    return JSONResponse(ComboRead.model_validate(obj).model_dump(), status_code=201)

@router.put("/api/tortas/combos/{combo_id}")
def ep_update_combo(combo_id: int, data: ComboCreate, db=Depends(get_db)):
    result = update_combo(db, combo_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

@router.patch("/api/tortas/combos/{combo_id}/disponibilidad")
def ep_disponibilidad_combo(combo_id: int, disponible: bool, db=Depends(get_db)):
    result = set_disponibilidad_combo(db, combo_id, disponible)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)


# ── Fase 9: Promociones y combos ─────────────────────────────────────────────

# ---- Promociones ------------------------------------------------------------

@router.get("/api/tortas/promociones")
def ep_list_promociones(todas: bool = False, canal_venta_id: int = None,
                        concepto_id: int = None, db=Depends(get_db)):
    items = list_promociones(db, solo_activas=not todas,
                             canal_venta_id=canal_venta_id, concepto_id=concepto_id)
    from ..modelos.schemas import PromocionRead
    return JSONResponse([PromocionRead.model_validate(p).model_dump() for p in items])

@router.post("/api/tortas/promociones")
def ep_create_promocion(data: PromocionCreate, db=Depends(get_db)):
    obj = create_promocion(db, data)
    from ..modelos.schemas import PromocionRead
    return JSONResponse(PromocionRead.model_validate(obj).model_dump(), status_code=201)

@router.put("/api/tortas/promociones/{promocion_id}")
def ep_update_promocion(promocion_id: int, data: PromocionCreate, db=Depends(get_db)):
    result = update_promocion(db, promocion_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

@router.post("/api/tortas/promociones/evaluar")
def ep_evaluar_promociones(data: EvaluarPromocionesRequest, db=Depends(get_db)):
    result = evaluar_promociones(db, data)
    from ..modelos.schemas import PromocionRead
    return JSONResponse({
        "descuento_total": result["descuento_total"],
        "detalle": result["detalle"],
        "promociones_aplicables": [
            PromocionRead.model_validate(p).model_dump()
            for p in result["promociones_aplicables"]
        ],
    })

@router.get("/api/tortas/promociones/{promocion_id}/usos")
def ep_usos_promocion(promocion_id: int, limit: int = 50, db=Depends(get_db)):
    items = list_usos_promocion(db, promocion_id, limit=limit)
    from ..modelos.schemas import PromocionUsoRead
    return JSONResponse([PromocionUsoRead.model_validate(u).model_dump() for u in items])

@router.post("/api/tortas/promociones/{promocion_id}/registrar-uso")
def ep_registrar_uso_promocion(promocion_id: int, pedido_id: int = None,
                                cliente_id: int = None, monto_descuento: float = 0.0,
                                descripcion: str = "", db=Depends(get_db)):
    registrar_promocion_uso(db, promocion_id, pedido_id=pedido_id,
                            cliente_id=cliente_id, monto_descuento=monto_descuento,
                            descripcion=descripcion)
    return JSONResponse({"ok": True})

# ---- Combos -----------------------------------------------------------------

@router.get("/api/tortas/combos")
def ep_list_combos(todos: bool = False, concepto_id: int = None, db=Depends(get_db)):
    items = list_combos(db, solo_activos=not todos, concepto_id=concepto_id)
    from ..modelos.schemas import ComboRead
    return JSONResponse([ComboRead.model_validate(c).model_dump() for c in items])

@router.get("/api/tortas/combos/{combo_id}")
def ep_get_combo(combo_id: int, db=Depends(get_db)):
    obj = get_combo(db, combo_id)
    if not obj:
        return JSONResponse({"error": "no encontrado"}, 404)
    from ..modelos.schemas import ComboRead
    return JSONResponse(ComboRead.model_validate(obj).model_dump())

@router.post("/api/tortas/combos")
def ep_create_combo(data: ComboCreate, db=Depends(get_db)):
    obj = create_combo(db, data)
    from ..modelos.schemas import ComboRead
    return JSONResponse(ComboRead.model_validate(obj).model_dump(), status_code=201)

@router.put("/api/tortas/combos/{combo_id}")
def ep_update_combo(combo_id: int, data: ComboCreate, db=Depends(get_db)):
    result = update_combo(db, combo_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

@router.patch("/api/tortas/combos/{combo_id}/disponibilidad")
def ep_disponibilidad_combo(combo_id: int, disponible: bool, db=Depends(get_db)):
    result = set_disponibilidad_combo(db, combo_id, disponible)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)


# ── Fase 10: Inventario y recetas ─────────────────────────────────────────────

# ---- Insumos ----------------------------------------------------------------

@router.get("/api/tortas/insumos")
def ep_list_insumos(todos: bool = False, db=Depends(get_db)):
    items = list_insumos(db, solo_activos=not todos)
    from ..modelos.schemas import InsumoRead
    return JSONResponse([InsumoRead.model_validate(i).model_dump() for i in items])

@router.post("/api/tortas/insumos")
def ep_create_insumo(data: InsumoCreate, db=Depends(get_db)):
    obj = create_insumo(db, data)
    from ..modelos.schemas import InsumoRead
    return JSONResponse(InsumoRead.model_validate(obj).model_dump(), status_code=201)

@router.put("/api/tortas/insumos/{insumo_id}")
def ep_update_insumo(insumo_id: int, data: InsumoCreate, db=Depends(get_db)):
    result = update_insumo(db, insumo_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

@router.get("/api/tortas/insumos/alertas-stock")
def ep_alertas_stock(db=Depends(get_db)):
    items = get_alertas_stock(db)
    from ..modelos.schemas import InsumoStockAlerta
    return JSONResponse([
        InsumoStockAlerta(
            id=i.id, name=i.name, unidad=i.unidad,
            stock_actual=i.stock_actual, stock_minimo=i.stock_minimo,
            diferencia=round(i.stock_actual - i.stock_minimo, 4),
        ).model_dump()
        for i in items
    ])

@router.get("/api/tortas/insumos/{insumo_id}/movimientos")
def ep_movimientos_insumo(insumo_id: int, limit: int = 50, db=Depends(get_db)):
    items = get_movimientos_insumo(db, insumo_id, limit=limit)
    from ..modelos.schemas import MovimientoInsumoRead
    return JSONResponse([MovimientoInsumoRead.model_validate(m).model_dump() for m in items])

@router.post("/api/tortas/insumos/movimiento")
def ep_registrar_movimiento(data: MovimientoInsumoCreate, db=Depends(get_db)):
    result = registrar_movimiento_insumo(db, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

@router.post("/api/tortas/insumos/ajuste-stock")
def ep_ajustar_stock(data: AjusteStockRequest, db=Depends(get_db)):
    result = ajustar_stock_insumo(db, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

# ---- Recetas ---------------------------------------------------------------

@router.get("/api/tortas/recetas")
def ep_list_recetas(producto_id: int = None, db=Depends(get_db)):
    items = list_recetas(db, producto_id=producto_id)
    from ..modelos.schemas import RecetaRead
    return JSONResponse([RecetaRead.model_validate(r).model_dump() for r in items])

@router.get("/api/tortas/recetas/{receta_id}")
def ep_get_receta(receta_id: int, db=Depends(get_db)):
    obj = get_receta(db, receta_id)
    if not obj:
        return JSONResponse({"error": "no encontrada"}, 404)
    from ..modelos.schemas import RecetaRead
    return JSONResponse(RecetaRead.model_validate(obj).model_dump())

@router.post("/api/tortas/recetas")
def ep_create_receta(data: RecetaCreate, db=Depends(get_db)):
    obj = create_receta(db, data)
    from ..modelos.schemas import RecetaRead
    return JSONResponse(RecetaRead.model_validate(obj).model_dump(), status_code=201)

@router.put("/api/tortas/recetas/{receta_id}")
def ep_update_receta(receta_id: int, data: RecetaCreate, db=Depends(get_db)):
    result = update_receta(db, receta_id, data)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)

# ---- Insumos por opción de modificador --------------------------------------

@router.get("/api/tortas/opciones-modificador/{opcion_id}/insumos")
def ep_insumos_opcion(opcion_id: int, db=Depends(get_db)):
    items = list_insumos_opcion(db, opcion_id)
    from ..modelos.schemas import OpcionModificadorInsumoRead
    return JSONResponse([OpcionModificadorInsumoRead.model_validate(o).model_dump() for o in items])

@router.post("/api/tortas/opciones-modificador/insumos")
def ep_create_insumo_opcion(data: OpcionModificadorInsumoCreate, db=Depends(get_db)):
    obj = create_insumo_opcion(db, data)
    from ..modelos.schemas import OpcionModificadorInsumoRead
    return JSONResponse(OpcionModificadorInsumoRead.model_validate(obj).model_dump(), status_code=201)

@router.delete("/api/tortas/opciones-modificador/insumos/{insumo_opcion_id}")
def ep_delete_insumo_opcion(insumo_opcion_id: int, db=Depends(get_db)):
    return JSONResponse(delete_insumo_opcion(db, insumo_opcion_id))

# ---- Descuento automático de stock ------------------------------------------

@router.post("/api/tortas/inventario/descontar-pedido")
def ep_descontar_stock_pedido(data: DescontarStockPedidoRequest, db=Depends(get_db)):
    result = descontar_stock_pedido(db, data)
    status = 200 if result.get("ok") else 400
    return JSONResponse(result, status_code=status)


# ── Fase 11: Reportes y analítica ─────────────────────────────────────────────

@router.get("/api/tortas/reportes/ventas-dia")
def ep_ventas_dia(fecha_inicio: date, fecha_fin: date, db=Depends(get_db)):
    return JSONResponse(store.get_reporte_ventas_dia(db, fecha_inicio, fecha_fin))


@router.get("/api/tortas/reportes/ventas-canal")
def ep_ventas_canal(fecha_inicio: date, fecha_fin: date, db=Depends(get_db)):
    return JSONResponse(store.get_reporte_ventas_canal(db, fecha_inicio, fecha_fin))


@router.get("/api/tortas/reportes/productos-top")
def ep_productos_top(fecha_inicio: date, fecha_fin: date, limit: int = 20, db=Depends(get_db)):
    return JSONResponse(store.get_reporte_productos_top(db, fecha_inicio, fecha_fin, limit))


@router.get("/api/tortas/reportes/modificadores-top")
def ep_modificadores_top(fecha_inicio: date, fecha_fin: date, limit: int = 20, db=Depends(get_db)):
    return JSONResponse(store.get_reporte_modificadores_top(db, fecha_inicio, fecha_fin, limit))


@router.get("/api/tortas/reportes/clientes-recurrentes")
def ep_clientes_recurrentes(fecha_inicio: date, fecha_fin: date, limit: int = 20, db=Depends(get_db)):
    return JSONResponse(store.get_reporte_clientes_recurrentes(db, fecha_inicio, fecha_fin, limit))


@router.get("/api/tortas/reportes/promociones-efectivas")
def ep_promociones_efectivas(fecha_inicio: date, fecha_fin: date, db=Depends(get_db)):
    return JSONResponse(store.get_reporte_promociones_efectivas(db, fecha_inicio, fecha_fin))


@router.get("/api/tortas/reportes/tiempo-preparacion")
def ep_tiempo_preparacion(fecha_inicio: date, fecha_fin: date, db=Depends(get_db)):
    return JSONResponse(store.get_reporte_tiempo_preparacion(db, fecha_inicio, fecha_fin))


@router.get("/api/tortas/reportes/tiempo-entrega")
def ep_tiempo_entrega(fecha_inicio: date, fecha_fin: date, db=Depends(get_db)):
    return JSONResponse(store.get_reporte_tiempo_entrega(db, fecha_inicio, fecha_fin))


@router.get("/api/tortas/dashboard/gerencial")
def ep_dashboard_gerencial(db=Depends(get_db)):
    return JSONResponse(store.get_dashboard_gerencial(db))


@router.get("/api/tortas/dashboard/operativo")
def ep_dashboard_operativo(db=Depends(get_db)):
    return JSONResponse(store.get_dashboard_operativo(db))



# ── Fase 12: Automatización e integración ─────────────────────────────────────

# ---- Eventos del sistema -----------------------------------------------------

@router.get("/api/tortas/eventos")
def ep_list_eventos(entidad: str = None, entidad_id: int = None,
                    tipo_evento: str = None, limit: int = 50,
                    db=Depends(get_db)):
    evs = store.list_eventos(db, entidad=entidad, entidad_id=entidad_id,
                             tipo_evento=tipo_evento, limit=limit)
    return JSONResponse([{
        "id": e.id, "tipo_evento": e.tipo_evento, "entidad": e.entidad,
        "entidad_id": e.entidad_id, "actor": e.actor, "resultado": e.resultado,
        "detalle": e.detalle,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    } for e in evs])


# ---- Automatizaciones -------------------------------------------------------

@router.get("/api/tortas/automatizaciones")
def ep_list_automatizaciones(solo_activas: bool = True, db=Depends(get_db)):
    items = store.list_automatizaciones(db, solo_activas=solo_activas)
    return JSONResponse([{
        "id": a.id, "name": a.name, "activa": a.activa,
        "evento_disparador": a.evento_disparador,
        "condicion_estado": a.condicion_estado,
        "accion_tipo": a.accion_tipo, "canal_mensaje": a.canal_mensaje,
        "plantilla_id": a.plantilla_id, "estado_destino": a.estado_destino,
        "prioridad": a.prioridad, "delay_seg": a.delay_seg,
    } for a in items])


@router.post("/api/tortas/automatizaciones")
def ep_create_automatizacion(data: AutomatizacionCreate, db=Depends(get_db)):
    obj = store.create_automatizacion(db, data)
    return JSONResponse({"id": obj.id, "name": obj.name}, status_code=201)


@router.put("/api/tortas/automatizaciones/{automatizacion_id}")
def ep_update_automatizacion(automatizacion_id: int,
                             data: AutomatizacionCreate, db=Depends(get_db)):
    return JSONResponse(store.update_automatizacion(db, automatizacion_id, data))


@router.post("/api/tortas/automatizaciones/disparar")
def ep_disparar_automatizacion(data: DisparadorEventoRequest, db=Depends(get_db)):
    result = store.evaluar_automatizaciones(
        db,
        pedido_id=data.pedido_id,
        evento=data.evento,
        actor=data.actor,
        estado_actual=data.payload.get("estado", ""),
        payload=data.payload,
    )
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)


# ---- Webhooks de salida -----------------------------------------------------

@router.get("/api/tortas/webhooks-salida")
def ep_list_webhooks(solo_activos: bool = True, db=Depends(get_db)):
    items = store.list_webhooks_salida(db, solo_activos=solo_activos)
    return JSONResponse([{
        "id": w.id, "name": w.name, "url": w.url,
        "eventos": w.eventos, "activo": w.activo,
        "ultimo_estado": w.ultimo_estado, "ultimo_error": w.ultimo_error,
        "ultimo_envio_at": w.ultimo_envio_at.isoformat() if w.ultimo_envio_at else None,
    } for w in items])


@router.post("/api/tortas/webhooks-salida")
def ep_create_webhook(data: WebhookSalidaCreate, db=Depends(get_db)):
    obj = store.create_webhook_salida(db, data)
    return JSONResponse({"id": obj.id, "name": obj.name}, status_code=201)


@router.put("/api/tortas/webhooks-salida/{webhook_id}")
def ep_update_webhook(webhook_id: int, data: WebhookSalidaCreate,
                      db=Depends(get_db)):
    return JSONResponse(store.update_webhook_salida(db, webhook_id, data))


@router.post("/api/tortas/webhooks-salida/{webhook_id}/disparar")
def ep_disparar_webhook(webhook_id: int, payload: dict = {},
                        db=Depends(get_db)):
    result = store.disparar_webhook(db, webhook_id, payload)
    status = 200 if result.get("ok") else 404
    return JSONResponse(result, status_code=status)


__all__ = ["router"]

