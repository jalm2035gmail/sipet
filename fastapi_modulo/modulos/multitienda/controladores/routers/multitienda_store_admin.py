from __future__ import annotations

from collections.abc import Awaitable, Callable

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

_log = logging.getLogger("multitienda.store_admin")

StoreSaveHandler = Callable[[Request], Awaitable[object]]
StoreListHandler = Callable[[Request], dict]
StoreAdminUsersHandler = Callable[[Request], dict]
MembershipsHandler = Callable[[], dict]
BusinessTypesHandler = Callable[[], object]
BusinessTypeCreateHandler = Callable[[Request], Awaitable[object]]
InicioStatsHandler = Callable[[Request], dict]
StoreConfigGetHandler = Callable[[Request], dict]
StoreConfigUpdateHandler = Callable[[Request], Awaitable[dict]]


def create_store_admin_router(
    *,
    list_business_types: BusinessTypesHandler,
    create_business_type: BusinessTypeCreateHandler,
    store_admin_users: StoreAdminUsersHandler,
    memberships: MembershipsHandler,
    list_stores: StoreListHandler,
    save_store: StoreSaveHandler,
    inicio_stats: InicioStatsHandler,
    get_store_configuration: StoreConfigGetHandler,
    update_store_configuration: StoreConfigUpdateHandler,
) -> APIRouter:
    router = APIRouter()

    @router.get("/multitienda/api/business-types", response_class=JSONResponse)
    def multitienda_business_types_proxy():
        return list_business_types()

    @router.post("/multitienda/api/business-types", response_class=JSONResponse)
    async def multitienda_create_business_type_proxy(request: Request):
        return await create_business_type(request)

    @router.get("/multitienda/api/store-admin-users", response_class=JSONResponse)
    def multitienda_store_admin_users(request: Request):
        return store_admin_users(request)

    @router.get("/multitienda/api/memberships", response_class=JSONResponse)
    def multitienda_memberships():
        return memberships()

    @router.get("/multitienda/api/stores", response_class=JSONResponse)
    def multitienda_list_stores(request: Request):
        return list_stores(request)

    @router.post("/multitienda/api/stores", response_class=JSONResponse)
    async def multitienda_save_store(request: Request):
        try:
            return await save_store(request)
        except HTTPException:
            raise
        except Exception as exc:
            _log.exception("No se pudo guardar la tienda desde el router administrativo.")
            raise HTTPException(status_code=500, detail="No se pudo guardar la tienda.") from exc

    @router.get("/multitienda/api/inicio-stats", response_class=JSONResponse)
    def api_inicio_stats(request: Request):
        return inicio_stats(request)

    @router.put("/multitienda/api/configuracion", response_class=JSONResponse)
    async def api_update_store_configuration(request: Request):
        return await update_store_configuration(request)

    @router.get("/multitienda/api/configuracion", response_class=JSONResponse)
    def api_get_store_configuration(request: Request):
        return get_store_configuration(request)

    return router
