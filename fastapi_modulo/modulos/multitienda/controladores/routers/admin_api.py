from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers import service as follower_service
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty import service as loyalty_service
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers import service as supplier_service
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos import service as video_service
from fastapi_modulo.modulos.multitienda.servicios.data_utils import (
    managed_session as _managed_session,
    normalize_datetime_fields as _normalize_datetime_fields,
    orm_list as _orm_list,
    orm_to_dict as _orm_to_dict,
)


JsonBodyReader = Callable[[Request], Awaitable[dict]]
StoreIdResolver = Callable[[Request], int]


def create_admin_api_router(require_store_id: StoreIdResolver, json_body: JsonBodyReader) -> APIRouter:
    router = APIRouter()

    @router.get("/multitienda/api/cupones", response_class=JSONResponse)
    def api_list_coupons(request: Request):
        store_id = require_store_id(request)
        with _managed_session() as db:
            return {"success": True, "data": _orm_list(coupon_service.list_by_vendor(db, store_id))}

    @router.post("/multitienda/api/cupones", response_class=JSONResponse)
    async def api_create_coupon(request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        normalized = _normalize_datetime_fields(data, "valid_from", "inicio", "valid_until", "expiracion")
        with _managed_session(commit=True) as db:
            coupon = coupon_service.create_for_vendor(
                db,
                store_id,
                code=str(normalized.get("code") or normalized.get("codigo") or "").strip().upper(),
                discount_type=str(normalized.get("discount_type") or normalized.get("tipo") or "percent"),
                discount_value=float(normalized.get("discount_value") or normalized.get("valor") or 0),
                min_order_amount=float(normalized.get("min_order_amount") or normalized.get("min_compra") or 0),
                max_uses=int(normalized["max_uses"]) if normalized.get("max_uses") else None,
                per_user_limit=int(normalized.get("per_user_limit") or 1),
                valid_from=normalized.get("valid_from") or normalized.get("inicio"),
                valid_until=normalized.get("valid_until") or normalized.get("expiracion"),
                is_active=bool(normalized.get("is_active", True)),
            )
            return {"success": True, "data": _orm_to_dict(coupon)}

    @router.put("/multitienda/api/cupones/{coupon_id}", response_class=JSONResponse)
    async def api_update_coupon(coupon_id: int, request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        normalized = _normalize_datetime_fields(data, "valid_from", "inicio", "valid_until", "expiracion")
        updates = {}
        field_map = {
            "code": "code",
            "codigo": "code",
            "discount_type": "discount_type",
            "tipo": "discount_type",
            "discount_value": "discount_value",
            "valor": "discount_value",
            "min_order_amount": "min_order_amount",
            "min_compra": "min_order_amount",
            "max_uses": "max_uses",
            "per_user_limit": "per_user_limit",
            "valid_from": "valid_from",
            "inicio": "valid_from",
            "valid_until": "valid_until",
            "expiracion": "valid_until",
            "is_active": "is_active",
        }
        seen = set()
        for src, dest in field_map.items():
            if normalized.get(src) is not None and dest not in seen:
                value = normalized[src]
                if dest == "code":
                    value = str(value).strip().upper()
                updates[dest] = value
                seen.add(dest)
        with _managed_session(commit=True) as db:
            coupon = coupon_service.get_by_vendor(db, store_id, coupon_id)
            if not coupon:
                raise HTTPException(status_code=404, detail="Cupón no encontrado.")
            coupon = coupon_service.update_coupon(db, coupon, **updates)
            return {"success": True, "data": _orm_to_dict(coupon)}

    @router.delete("/multitienda/api/cupones/{coupon_id}", response_class=JSONResponse)
    def api_delete_coupon(coupon_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            coupon = coupon_service.get_by_vendor(db, store_id, coupon_id)
            if not coupon:
                raise HTTPException(status_code=404, detail="Cupón no encontrado.")
            coupon_service.delete_coupon(db, coupon)
            return {"success": True}

    @router.post("/multitienda/api/cupones/validar", response_class=JSONResponse)
    async def api_validate_coupon(request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        code = str(data.get("code") or data.get("codigo") or "").strip()
        cart_total = float(data.get("cart_total") or data.get("total_carrito") or 0)
        if not code:
            raise HTTPException(status_code=400, detail="Se requiere el código del cupón.")
        with _managed_session() as db:
            return coupon_service.validate_coupon_for_vendor(db, store_id, code, cart_total=cart_total)

    @router.post("/multitienda/api/cupones/{coupon_id}/redimir", response_class=JSONResponse)
    def api_redeem_coupon(coupon_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            ok = coupon_service.redeem_for_vendor(db, store_id, coupon_id)
            if not ok:
                raise HTTPException(status_code=404, detail="Cupón no encontrado.")
            return {"success": True}

    @router.get("/multitienda/api/fidelizacion/plan", response_class=JSONResponse)
    def api_get_loyalty_plan(request: Request):
        store_id = require_store_id(request)
        with _managed_session() as db:
            plan = loyalty_service.get_plan(db, store_id)
            data = _orm_to_dict(plan) if plan else {
                "vendor_id": store_id,
                "name": "Programa de Lealtad",
                "points_per_peso": 1.0,
                "min_redeem_points": 100,
                "redeem_rate": 1.0,
                "is_active": False,
                "description": "",
            }
            return {"success": True, "data": data}

    @router.put("/multitienda/api/fidelizacion/plan", response_class=JSONResponse)
    async def api_update_loyalty_plan(request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        with _managed_session(commit=True) as db:
            plan = loyalty_service.upsert_plan(
                db,
                store_id,
                name=str(data.get("name") or data.get("nombre") or "Programa de Lealtad"),
                points_per_peso=float(data.get("points_per_peso") or data.get("puntos_por_peso") or 1),
                min_redeem_points=int(data.get("min_redeem_points") or data.get("minimo_canje") or 100),
                redeem_rate=float(data.get("redeem_rate") or data.get("valor_punto") or 1),
                is_active=bool(data.get("is_active", True)),
                description=str(data.get("description") or data.get("descripcion") or ""),
            )
            return {"success": True, "data": _orm_to_dict(plan)}

    @router.get("/multitienda/api/fidelizacion/clientes", response_class=JSONResponse)
    def api_list_loyalty_customers(request: Request):
        store_id = require_store_id(request)
        with _managed_session() as db:
            return {"success": True, "data": _orm_list(loyalty_service.list_customers(db, store_id))}

    @router.get("/multitienda/api/fidelizacion/clientes/{email}/historial", response_class=JSONResponse)
    def api_loyalty_history(email: str, request: Request):
        store_id = require_store_id(request)
        with _managed_session() as db:
            return {"success": True, "data": _orm_list(loyalty_service.get_history(db, store_id, email))}

    @router.post("/multitienda/api/fidelizacion/clientes/{email}/ajustar", response_class=JSONResponse)
    async def api_adjust_loyalty(email: str, request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        points = int(data.get("points") or data.get("puntos") or 0)
        if points == 0:
            raise HTTPException(status_code=400, detail="Se requiere una cantidad de puntos distinta de 0.")
        tx_type = str(data.get("type") or ("adjusted" if points > 0 else "adjusted"))
        with _managed_session(commit=True) as db:
            result = loyalty_service.adjust_points(
                db,
                store_id,
                email=email,
                points=points,
                tx_type=tx_type,
                notes=str(data.get("notes") or data.get("notas") or ""),
                reference=str(data.get("reference") or ""),
                name=str(data.get("name") or data.get("nombre") or ""),
            )
            return {"success": True, "data": _orm_to_dict(result)}

    @router.get("/multitienda/api/apartados", response_class=JSONResponse)
    def api_list_layaways(request: Request):
        store_id = require_store_id(request)
        with _managed_session() as db:
            return {"success": True, "data": layaway_service.list_by_vendor(db, store_id)}

    @router.post("/multitienda/api/apartados", response_class=JSONResponse)
    async def api_create_layaway(request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        with _managed_session(commit=True) as db:
            return {"success": True, "data": layaway_service.create_basic(db, store_id, data)}

    @router.put("/multitienda/api/apartados/{layaway_id}", response_class=JSONResponse)
    async def api_update_layaway(layaway_id: int, request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        with _managed_session(commit=True) as db:
            result = layaway_service.update_basic(db, store_id, layaway_id, data)
            if result is None:
                raise HTTPException(status_code=404, detail="Apartado no encontrado.")
            return {"success": True, "data": result}

    @router.delete("/multitienda/api/apartados/{layaway_id}", response_class=JSONResponse)
    def api_delete_layaway(layaway_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            ok = layaway_service.delete_basic(db, store_id, layaway_id)
            if not ok:
                raise HTTPException(status_code=404, detail="Apartado no encontrado.")
            return {"success": True}

    @router.post("/multitienda/api/apartados/crear", response_class=JSONResponse)
    async def api_create_layaway_rich(request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        with _managed_session(commit=True) as db:
            return {"success": True, "data": layaway_service.create_rich(db, store_id, data)}

    @router.put("/multitienda/api/apartados/{layaway_id}/editar", response_class=JSONResponse)
    async def api_update_layaway_rich(layaway_id: int, request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        with _managed_session(commit=True) as db:
            result = layaway_service.update_rich(db, store_id, layaway_id, data)
            if result is None:
                raise HTTPException(status_code=404, detail="Apartado no encontrado.")
            return {"success": True, "data": result}

    @router.get("/multitienda/api/apartados/{layaway_id}/pagos", response_class=JSONResponse)
    def api_list_layaway_payments(layaway_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session() as db:
            return {"success": True, "data": layaway_service.list_payments(db, store_id, layaway_id)}

    @router.post("/multitienda/api/apartados/{layaway_id}/pagos", response_class=JSONResponse)
    async def api_add_layaway_payment(layaway_id: int, request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        with _managed_session(commit=True) as db:
            result = layaway_service.add_payment(db, store_id, layaway_id, data)
            if result.get("error"):
                raise HTTPException(status_code=400, detail=result["error"])
            return {"success": True, "data": result}

    @router.delete("/multitienda/api/apartados/{layaway_id}/pagos/{payment_id}", response_class=JSONResponse)
    def api_delete_layaway_payment(layaway_id: int, payment_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            ok = layaway_service.delete_payment(db, store_id, layaway_id, payment_id)
            if not ok:
                raise HTTPException(status_code=404, detail="Pago no encontrado.")
            return {"success": True}

    @router.post("/multitienda/api/apartados/{layaway_id}/cancelar", response_class=JSONResponse)
    def api_cancel_layaway(layaway_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            result = layaway_service.set_status(db, store_id, layaway_id, "cancelado")
            if not result:
                raise HTTPException(status_code=404, detail="Apartado no encontrado.")
            return {"success": True, "data": result}

    @router.post("/multitienda/api/apartados/{layaway_id}/reactivar", response_class=JSONResponse)
    def api_reactivate_layaway(layaway_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            result = layaway_service.set_status(db, store_id, layaway_id, "active")
            if not result:
                raise HTTPException(status_code=404, detail="Apartado no encontrado.")
            return {"success": True, "data": result}

    @router.post("/multitienda/api/apartados/{layaway_id}/entregar", response_class=JSONResponse)
    def api_deliver_layaway(layaway_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            result = layaway_service.set_status(db, store_id, layaway_id, "entregado")
            if not result:
                raise HTTPException(status_code=404, detail="Apartado no encontrado.")
            return {"success": True, "data": result}

    @router.post("/multitienda/api/apartados/vencer", response_class=JSONResponse)
    def api_mark_overdue_layaways(request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            count = layaway_service.mark_overdue(db, store_id)
            return {"success": True, "updated": count}

    @router.get("/multitienda/api/seguidores", response_class=JSONResponse)
    def api_list_followers(request: Request):
        store_id = require_store_id(request)
        with _managed_session() as db:
            return {"success": True, "data": _orm_list(follower_service.list_by_vendor(db, store_id))}

    @router.post("/multitienda/api/seguidores", response_class=JSONResponse)
    async def api_create_follower(request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        with _managed_session(commit=True) as db:
            follower = follower_service.create_for_vendor(db, store_id, user_id=int(data.get("user_id") or 0))
            return {"success": True, "data": _orm_to_dict(follower)}

    @router.delete("/multitienda/api/seguidores/{follower_id}", response_class=JSONResponse)
    def api_delete_follower(follower_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            follower = follower_service.get_by_vendor(db, store_id, follower_id)
            if not follower:
                raise HTTPException(status_code=404, detail="Seguidor no encontrado.")
            follower_service.delete_follower(db, follower)
            return {"success": True}

    @router.get("/multitienda/api/videos", response_class=JSONResponse)
    def api_list_videos(request: Request):
        store_id = require_store_id(request)
        with _managed_session() as db:
            return {"success": True, "data": _orm_list(video_service.list_by_vendor(db, store_id))}

    @router.post("/multitienda/api/videos", response_class=JSONResponse)
    async def api_create_video(request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        with _managed_session(commit=True) as db:
            video = video_service.create_for_vendor(
                db,
                store_id,
                product_id=int(data["product_id"]) if data.get("product_id") else None,
                title=str(data.get("title") or data.get("nombre") or ""),
                url=str(data.get("url") or ""),
                thumbnail=data.get("thumbnail"),
                description=str(data.get("description") or data.get("notas") or ""),
                is_active=bool(data.get("is_active", True)),
                order=int(data.get("order") or 0),
            )
            return {"success": True, "data": _orm_to_dict(video)}

    @router.delete("/multitienda/api/videos/{video_id}", response_class=JSONResponse)
    def api_delete_video(video_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            video = video_service.get_by_vendor(db, store_id, video_id)
            if not video:
                raise HTTPException(status_code=404, detail="Video no encontrado.")
            video_service.delete_video(db, video)
            return {"success": True}

    @router.get("/multitienda/api/proveedores", response_class=JSONResponse)
    def api_list_suppliers(request: Request):
        store_id = require_store_id(request)
        with _managed_session() as db:
            return {"success": True, "data": _orm_list(supplier_service.list_by_vendor(db, store_id))}

    @router.post("/multitienda/api/proveedores", response_class=JSONResponse)
    async def api_create_supplier(request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        with _managed_session(commit=True) as db:
            supplier = supplier_service.create_for_vendor(
                db,
                store_id,
                name=str(data.get("name") or data.get("nombre") or "").strip(),
                contact_name=str(data.get("contact_name") or ""),
                email=str(data.get("email") or ""),
                phone=str(data.get("phone") or data.get("telefono") or ""),
                address=str(data.get("address") or data.get("direccion") or ""),
                country=str(data.get("country") or ""),
                website=data.get("website"),
                notes=str(data.get("notes") or data.get("notas") or ""),
                is_active=bool(data.get("is_active", True)),
            )
            return {"success": True, "data": _orm_to_dict(supplier)}

    @router.put("/multitienda/api/proveedores/{supplier_id}", response_class=JSONResponse)
    async def api_update_supplier(supplier_id: int, request: Request):
        store_id = require_store_id(request)
        data = await json_body(request)
        updates = {}
        field_map = {
            "name": "name",
            "nombre": "name",
            "contact_name": "contact_name",
            "email": "email",
            "phone": "phone",
            "telefono": "phone",
            "address": "address",
            "direccion": "address",
            "country": "country",
            "website": "website",
            "notes": "notes",
            "notas": "notes",
            "is_active": "is_active",
        }
        seen = set()
        for src, dest in field_map.items():
            if data.get(src) is not None and dest not in seen:
                updates[dest] = data[src]
                seen.add(dest)
        with _managed_session(commit=True) as db:
            supplier = supplier_service.get_by_vendor(db, store_id, supplier_id)
            if not supplier:
                raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
            supplier = supplier_service.update_supplier(db, supplier, **updates)
            return {"success": True, "data": _orm_to_dict(supplier)}

    @router.delete("/multitienda/api/proveedores/{supplier_id}", response_class=JSONResponse)
    def api_delete_supplier(supplier_id: int, request: Request):
        store_id = require_store_id(request)
        with _managed_session(commit=True) as db:
            supplier = supplier_service.get_by_vendor(db, store_id, supplier_id)
            if not supplier:
                raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
            supplier_service.delete_supplier(db, supplier)
            return {"success": True}

    return router
