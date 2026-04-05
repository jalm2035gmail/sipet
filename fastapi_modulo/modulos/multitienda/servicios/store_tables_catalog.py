from __future__ import annotations

import logging

from fastapi_modulo.modulos.multitienda.servicios.store_tables_shared import managed_session

_log = logging.getLogger("multitienda.store_tables_catalog")


def get_store_stats(store_id: int) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.analytics import service as analytics_service

    with managed_session() as db:
        return analytics_service.get_cached_store_stats(db, store_id)


def get_public_products(store_id: int = None, featured_only: bool = False) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products import service as product_service

    try:
        with managed_session() as db:
            return product_service.list_public_catalog(
                db,
                store_id,
                featured_only=featured_only,
            )
    except Exception:
        _log.exception(
            "Error obteniendo productos publicos store_id=%s featured_only=%s",
            store_id,
            featured_only,
        )
        return []
