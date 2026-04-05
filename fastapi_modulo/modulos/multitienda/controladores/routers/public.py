from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse


HtmlRenderer = Callable[[str], HTMLResponse]
StoreExistsChecker = Callable[[Request, str], bool]
StoreProductExistsChecker = Callable[[Request, str, str], bool]
NotFoundRenderer = Callable[..., HTMLResponse]
PublicStoreInfoLoader = Callable[[Request, str], dict]
PublicProductsLoader = Callable[[Request, str, str], list]
StoreIdResolver = Callable[[Request], int]


def create_public_router(
    *,
    render_public_document: HtmlRenderer,
    public_store_exists: StoreExistsChecker,
    public_store_product_exists: StoreProductExistsChecker,
    render_not_found_template: NotFoundRenderer,
    tienda_html: Callable[[], str],
    carrito_html: Callable[[], str],
    public_landing_reserved: set[str],
    load_public_store_info: PublicStoreInfoLoader,
    load_public_products: PublicProductsLoader,
    require_store_id: StoreIdResolver,
) -> APIRouter:
    router = APIRouter()

    @router.get("/tiendas", include_in_schema=False, response_class=HTMLResponse)
    def public_tiendas_entrypoint():
        return render_public_document(tienda_html())

    @router.get("/tiendas/", include_in_schema=False, response_class=HTMLResponse)
    def public_tiendas_entrypoint_slash():
        return render_public_document(tienda_html())

    @router.get("/multitienda/public/tiendas", include_in_schema=False, response_class=HTMLResponse)
    def public_multitienda_tiendas_entrypoint():
        return render_public_document(tienda_html())

    @router.get("/destacados", include_in_schema=False, response_class=HTMLResponse)
    def public_destacados_entrypoint():
        return render_public_document(tienda_html())

    @router.get("/destacados/", include_in_schema=False, response_class=HTMLResponse)
    def public_destacados_entrypoint_slash():
        return render_public_document(tienda_html())

    @router.get("/carrito", include_in_schema=False, response_class=HTMLResponse)
    def public_cart_entrypoint():
        return render_public_document(carrito_html())

    @router.get("/carrito/", include_in_schema=False, response_class=HTMLResponse)
    def public_cart_entrypoint_slash():
        return render_public_document(carrito_html())

    @router.get("/destaacados", include_in_schema=False, response_class=HTMLResponse)
    def public_destacados_typo_entrypoint():
        return RedirectResponse(url="/destacados", status_code=307)

    @router.get("/destaacados/", include_in_schema=False, response_class=HTMLResponse)
    def public_destacados_typo_entrypoint_slash():
        return RedirectResponse(url="/destacados", status_code=307)

    @router.get("/multitienda/api/store-info", response_class=JSONResponse)
    def api_public_store_info(request: Request):
        store_slug = str(request.query_params.get("store_slug") or "").strip().lower()
        if not store_slug:
            return {"success": False, "data": {}}
        return load_public_store_info(request, store_slug)

    @router.get("/multitienda/api/productos-publicos", response_class=JSONResponse)
    def api_public_products(request: Request):
        mode = str(request.query_params.get("mode") or "all").strip().lower()
        store_slug = str(request.query_params.get("store_slug") or "").strip().lower()
        store_id = None

        if store_slug:
            store_info = load_public_store_info(request, store_slug)
            data = store_info.get("data") or {}
            store_id = data.get("id")
        elif mode == "store":
            try:
                store_id = require_store_id(request)
            except HTTPException:
                store_id = None

        return {
            "success": True,
            "data": load_public_products(request, mode, str(store_id or "")),
        }

    return router


def create_public_catchall_router(
    *,
    render_public_document: HtmlRenderer,
    public_store_exists: StoreExistsChecker,
    public_store_product_exists: StoreProductExistsChecker,
    render_not_found_template: NotFoundRenderer,
    tienda_html: Callable[[], str],
    public_landing_reserved: set[str],
) -> APIRouter:
    """Catch-all router for public store URLs.

    MUST be registered in the 'late' phase so it does not intercept explicit
    routes from other modules (e.g. /web/{slug} from the frontend module).
    """
    router = APIRouter()

    @router.get("/{store_slug}", include_in_schema=False, response_class=HTMLResponse)
    def public_store_landing_entrypoint(request: Request, store_slug: str):
        normalized = str(store_slug or "").strip().lower()
        if not normalized or normalized in public_landing_reserved:
            return render_not_found_template(request, title="Pagina no encontrada", status_code=404)
        if not public_store_exists(request, normalized):
            return render_not_found_template(request, title="Tienda no encontrada", status_code=404)
        return render_public_document(tienda_html())

    @router.get("/{store_slug}/{product_slug}", include_in_schema=False, response_class=HTMLResponse)
    def public_store_product_landing_entrypoint(request: Request, store_slug: str, product_slug: str):
        normalized_store = str(store_slug or "").strip().lower()
        normalized_product = str(product_slug or "").strip().lower()
        if (
            not normalized_store
            or not normalized_product
            or normalized_store in public_landing_reserved
            or normalized_product in public_landing_reserved
        ):
            return render_not_found_template(request, title="Pagina no encontrada", status_code=404)
        if not public_store_product_exists(request, normalized_store, normalized_product):
            return render_not_found_template(request, title="Producto no encontrado", status_code=404)
        return render_public_document(tienda_html())

    return router
