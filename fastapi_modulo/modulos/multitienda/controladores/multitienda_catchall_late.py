"""Late-phase catch-all router for public multitienda store URLs.

Registered in the 'late' phase (after all other modules) so that explicit
routes like /web/{slug} (frontend) are matched before the store catch-alls
/{store_slug} and /{store_slug}/{product_slug}.
"""
from __future__ import annotations

from fastapi_modulo.modulos.multitienda.controladores.multitienda import (
    _PUBLIC_LANDING_RESERVED,
    _load_public_products,
    _load_public_store_info,
    _public_store_exists,
    _public_store_product_exists,
    _render_public_document,
    _require_store_id,
)
from fastapi_modulo.modulos.multitienda.controladores.routers.public import (
    create_public_catchall_router,
)
from fastapi_modulo.modulos.multitienda.vistas.carrito import carrito_html
from fastapi_modulo.modulos.multitienda.vistas.tienda import tienda_html
from fastapi_modulo.modulos_sipet.web.servicios.template_service import (
    render_not_found_template,
)

router = create_public_catchall_router(
    render_public_document=_render_public_document,
    public_store_exists=_public_store_exists,
    public_store_product_exists=_public_store_product_exists,
    render_not_found_template=render_not_found_template,
    tienda_html=tienda_html,
    public_landing_reserved=_PUBLIC_LANDING_RESERVED,
)
