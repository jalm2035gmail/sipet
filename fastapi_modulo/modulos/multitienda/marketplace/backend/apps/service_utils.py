from __future__ import annotations

from sqlalchemy.orm import Session


def list_by_vendor(
    db: Session,
    model,
    vendor_id: int,
    *,
    order_by=None,
    extra_filters: tuple = (),
):
    query = db.query(model).filter_by(vendor_id=vendor_id)
    if extra_filters:
        query = query.filter(*extra_filters)
    if order_by:
        query = query.order_by(*order_by)
    return query.all()


def get_by_id(db: Session, model, record_id: int):
    return db.query(model).filter_by(id=record_id).first()


def get_by_vendor(db: Session, model, vendor_id: int, record_id: int):
    return db.query(model).filter_by(id=record_id, vendor_id=vendor_id).first()


def create_for_vendor(db: Session, model, vendor_id: int, **payload):
    record = model(vendor_id=vendor_id, **payload)
    db.add(record)
    db.flush()
    db.refresh(record)
    return record


def update_entity(db: Session, record, **updates):
    for field, value in updates.items():
        setattr(record, field, value)
    db.flush()
    db.refresh(record)
    return record


def delete_entity(db: Session, record) -> None:
    db.delete(record)
    db.flush()
