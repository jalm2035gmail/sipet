from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers.models import StoreSupplier


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreSupplier]:
    return (
        db.query(StoreSupplier)
        .filter_by(vendor_id=vendor_id)
        .order_by(StoreSupplier.name)
        .all()
    )


def get_by_id(db: Session, supplier_id: int) -> StoreSupplier | None:
    return db.query(StoreSupplier).filter_by(id=supplier_id).first()


def get_by_vendor(db: Session, vendor_id: int, supplier_id: int) -> StoreSupplier | None:
    return db.query(StoreSupplier).filter_by(id=supplier_id, vendor_id=vendor_id).first()


def create_for_vendor(db: Session, vendor_id: int, **payload) -> StoreSupplier:
    supplier = StoreSupplier(vendor_id=vendor_id, **payload)
    db.add(supplier)
    db.flush()
    db.refresh(supplier)
    return supplier


def update_supplier(db: Session, supplier: StoreSupplier, **updates) -> StoreSupplier:
    for field, value in updates.items():
        setattr(supplier, field, value)
    db.flush()
    db.refresh(supplier)
    return supplier


def delete_supplier(db: Session, supplier: StoreSupplier) -> None:
    db.delete(supplier)
    db.flush()
