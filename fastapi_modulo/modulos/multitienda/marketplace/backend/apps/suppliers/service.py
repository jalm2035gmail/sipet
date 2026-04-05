from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers.models import StoreSupplier
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.service_utils import (
    create_for_vendor as create_vendor_record,
    delete_entity,
    get_by_id as get_record_by_id,
    get_by_vendor as get_vendor_record,
    list_by_vendor as list_vendor_records,
    update_entity,
)


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreSupplier]:
    return list_vendor_records(db, StoreSupplier, vendor_id, order_by=(StoreSupplier.name,))


def get_by_id(db: Session, supplier_id: int) -> StoreSupplier | None:
    return get_record_by_id(db, StoreSupplier, supplier_id)


def get_by_vendor(db: Session, vendor_id: int, supplier_id: int) -> StoreSupplier | None:
    return get_vendor_record(db, StoreSupplier, vendor_id, supplier_id)


def create_for_vendor(db: Session, vendor_id: int, **payload) -> StoreSupplier:
    return create_vendor_record(db, StoreSupplier, vendor_id, **payload)


def update_supplier(db: Session, supplier: StoreSupplier, **updates) -> StoreSupplier:
    return update_entity(db, supplier, **updates)


def delete_supplier(db: Session, supplier: StoreSupplier) -> None:
    delete_entity(db, supplier)
