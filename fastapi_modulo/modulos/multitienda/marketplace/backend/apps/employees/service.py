from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import get_password_hash


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreEmployee]:
    return (
        db.query(StoreEmployee)
        .filter_by(vendor_id=vendor_id)
        .order_by(StoreEmployee.id)
        .all()
    )


def get_by_id(db: Session, employee_id: int) -> StoreEmployee | None:
    return db.query(StoreEmployee).filter_by(id=employee_id).first()


def get_by_vendor(db: Session, vendor_id: int, employee_id: int) -> StoreEmployee | None:
    return db.query(StoreEmployee).filter_by(id=employee_id, vendor_id=vendor_id).first()


def get_by_vendor_user(db: Session, vendor_id: int, user_id: int) -> StoreEmployee | None:
    return db.query(StoreEmployee).filter_by(vendor_id=vendor_id, user_id=user_id).first()


def create_for_vendor(
    db: Session,
    vendor_id: int,
    *,
    user_id: int,
    role,
    position: str = "",
    is_active: bool = True,
) -> StoreEmployee:
    employee = StoreEmployee(
        vendor_id=vendor_id,
        user_id=user_id,
        role=role,
        position=position,
        is_active=is_active,
    )
    db.add(employee)
    db.flush()
    db.refresh(employee)
    return employee


def update_employee(
    db: Session,
    employee: StoreEmployee,
    **updates,
) -> StoreEmployee:
    for field, value in updates.items():
        setattr(employee, field, value)
    db.flush()
    db.refresh(employee)
    return employee


def delete_employee(db: Session, employee: StoreEmployee) -> None:
    db.delete(employee)
    db.flush()


def set_password_for_vendor_employee(
    db: Session,
    vendor_id: int,
    employee_id: int,
    password: str,
) -> bool:
    employee = get_by_vendor(db, vendor_id, employee_id)
    if not employee or not employee.user_id:
        return False
    user = db.query(User).filter_by(id=int(employee.user_id)).first()
    if not user:
        return False
    user.hashed_password = get_password_hash(password)
    db.flush()
    return True
