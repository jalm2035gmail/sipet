from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


StoreProductsListHandler = Callable[[Request], dict]
StoreProductsReplaceHandler = Callable[[Request], Awaitable[dict]]


def create_products_router(
    *,
    list_store_products: StoreProductsListHandler,
    replace_store_products: StoreProductsReplaceHandler,
) -> APIRouter:
    router = APIRouter()

    @router.get("/multitienda/api/productos", response_class=JSONResponse)
    def api_list_store_products(request: Request):
        return list_store_products(request)

    @router.put("/multitienda/api/productos", response_class=JSONResponse)
    async def api_replace_store_products(request: Request):
        return await replace_store_products(request)

    return router
