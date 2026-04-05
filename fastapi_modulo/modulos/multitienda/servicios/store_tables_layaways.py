from __future__ import annotations

from fastapi_modulo.modulos.multitienda.servicios.store_tables_shared import managed_session


def list_layaways(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session() as db:
        return layaway_service.list_by_vendor(db, store_id)


def create_layaway(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session(commit=True) as db:
        return layaway_service.create_basic(db, store_id, data)


def update_layaway(store_id: int, layaway_id: int, data: dict):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session(commit=True) as db:
        return layaway_service.update_basic(db, store_id, layaway_id, data)


def delete_layaway(store_id: int, layaway_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session(commit=True) as db:
        return layaway_service.delete_basic(db, store_id, layaway_id)


def create_layaway_rich(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session(commit=True) as db:
        return layaway_service.create_rich(db, store_id, data)


def update_layaway_rich(store_id: int, layaway_id: int, data: dict) -> dict | None:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session(commit=True) as db:
        return layaway_service.update_rich(db, store_id, layaway_id, data)


def list_layaway_payments(store_id: int, layaway_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session() as db:
        return layaway_service.list_payments(db, store_id, layaway_id)


def add_layaway_payment(store_id: int, layaway_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session(commit=True) as db:
        return layaway_service.add_payment(db, store_id, layaway_id, data)


def delete_layaway_payment(store_id: int, layaway_id: int, payment_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session(commit=True) as db:
        return layaway_service.delete_payment(db, store_id, layaway_id, payment_id)


def set_layaway_status(store_id: int, layaway_id: int, new_status: str) -> dict | None:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session(commit=True) as db:
        return layaway_service.set_status(db, store_id, layaway_id, new_status)


def mark_overdue_layaways(store_id: int) -> int:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
    with managed_session(commit=True) as db:
        return layaway_service.mark_overdue(db, store_id)
