from __future__ import annotations

import json

from sqlalchemy.orm import Session, joinedload

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.service_utils import (
    delete_entity,
    get_by_id as get_record_by_id,
    get_by_vendor as get_vendor_record,
    list_by_vendor as list_vendor_records,
    update_entity,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import get_password_hash


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreEmployee]:
    return list_vendor_records(db, StoreEmployee, vendor_id, order_by=(StoreEmployee.id,))


def get_by_id(db: Session, employee_id: int) -> StoreEmployee | None:
    return get_record_by_id(db, StoreEmployee, employee_id)


def get_by_vendor(db: Session, vendor_id: int, employee_id: int) -> StoreEmployee | None:
    return get_vendor_record(db, StoreEmployee, vendor_id, employee_id)


def get_by_vendor_user(db: Session, vendor_id: int, user_id: int) -> StoreEmployee | None:
    return db.query(StoreEmployee).filter_by(vendor_id=vendor_id, user_id=user_id).first()


def create_for_vendor(
    db: Session,
    vendor_id: int,
    *,
    user_id: int,
    role,
    position: str = "",
    full_name: str = "",
    job_title: str = "",
    phone: str = "",
    department: str = "",
    is_active: bool = True,
) -> StoreEmployee:
    position, full_name, job_title, phone, department = _resolve_profile_fields(
        position=position,
        full_name=full_name,
        job_title=job_title,
        phone=phone,
        department=department,
    )
    employee = StoreEmployee(
        vendor_id=vendor_id,
        user_id=user_id,
        role=role,
        position=position,
        full_name=full_name,
        job_title=job_title,
        phone=phone,
        department=department,
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
    profile_related = {"position", "full_name", "job_title", "phone", "department"}
    if profile_related.intersection(updates):
        position, full_name, job_title, phone, department = _resolve_profile_fields(
            position=str(updates.get("position", employee.position) or ""),
            full_name=str(updates.get("full_name", employee.full_name) or ""),
            job_title=str(updates.get("job_title", employee.job_title) or ""),
            phone=str(updates.get("phone", employee.phone) or ""),
            department=str(updates.get("department", employee.department) or ""),
        )
        updates["position"] = position
        updates["full_name"] = full_name
        updates["job_title"] = job_title
        updates["phone"] = phone
        updates["department"] = department
    return update_entity(db, employee, **updates)


def delete_employee(db: Session, employee: StoreEmployee) -> None:
    delete_entity(db, employee)


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


def _decode_position_meta(raw_value) -> dict:
    try:
        decoded = json.loads(str(raw_value or ""))
        return decoded if isinstance(decoded, dict) else {}
    except json.JSONDecodeError:
        return {"p": str(raw_value or "")}


def _encode_position_meta(*, name: str, position: str, phone: str, department: str) -> str:
    return json.dumps(
        {"n": name, "p": position, "t": phone, "d": department},
        ensure_ascii=False,
    )[:400]


def _role_from_form(role_name: str | None) -> str:
    return "manager" if str(role_name or "").lower() == "administrador" else "seller"


def _resolve_profile_fields(
    *,
    position: str = "",
    full_name: str = "",
    job_title: str = "",
    phone: str = "",
    department: str = "",
) -> tuple[str, str, str, str, str]:
    meta = _decode_position_meta(position)
    resolved_full_name = str(full_name or meta.get("n") or "").strip()
    resolved_job_title = str(job_title or meta.get("p") or "").strip()
    resolved_phone = str(phone or meta.get("t") or "").strip()
    resolved_department = str(department or meta.get("d") or "").strip()
    encoded_position = _encode_position_meta(
        name=resolved_full_name,
        position=resolved_job_title,
        phone=resolved_phone,
        department=resolved_department,
    )
    return encoded_position, resolved_full_name, resolved_job_title, resolved_phone, resolved_department


def list_admin_rows(db: Session, vendor_id: int) -> list[dict]:
    employees = (
        db.query(StoreEmployee)
        .options(joinedload(StoreEmployee.user))
        .filter_by(vendor_id=vendor_id)
        .order_by(StoreEmployee.id)
        .all()
    )
    rows = []
    for employee in employees:
        user = employee.user
        meta = _decode_position_meta(employee.position)
        full_name = str(employee.full_name or meta.get("n") or getattr(user, "username", "") or "")
        job_title = str(employee.job_title or meta.get("p") or "")
        phone = str(employee.phone or meta.get("t") or "")
        department = str(employee.department or meta.get("d") or "")
        rows.append({
            "id": employee.id,
            "rol": getattr(employee.role, "value", employee.role),
            "usuario": str(getattr(user, "username", "") or ""),
            "correo": str(getattr(user, "email", "") or ""),
            "full_name": full_name,
            "nombre": full_name,
            "puesto": job_title,
            "celular": phone,
            "departamento": department,
            "estado": "Activo" if bool(employee.is_active) else "Inactivo",
            "created_at": str(employee.created_at) if employee.created_at else "",
        })
    return rows


def create_admin_employee(db: Session, vendor_id: int, data: dict, *, max_users: int = 0) -> dict:
    if max_users > 0 and len(list_by_vendor(db, vendor_id)) >= max_users:
        raise ValueError("LIMIT_REACHED")

    username = str(data.get("usuario") or "").strip()
    email = str(data.get("correo") or "").strip()
    password = str(data.get("contrasena") or "").strip()
    if not username:
        raise ValueError("USERNAME_REQUIRED")
    if not password:
        raise ValueError("PASSWORD_REQUIRED")
    if db.query(User).filter_by(username=username).first():
        raise ValueError("USERNAME_TAKEN")

    user = User(
        username=username,
        email=email or f"{username}@tienda.local",
        hashed_password=get_password_hash(password),
        user_type="store_employee",
    )
    db.add(user)
    db.flush()

    full_name = str(data.get("nombre") or username).strip()
    position = str(data.get("puesto") or "").strip()
    phone = str(data.get("celular") or "").strip()
    department = str(data.get("departamento") or "").strip()
    employee = create_for_vendor(
        db,
        vendor_id,
        user_id=int(user.id),
        role=_role_from_form(data.get("rol")),
        position=_encode_position_meta(
            name=full_name,
            position=position,
            phone=phone,
            department=department,
        ),
        full_name=full_name,
        job_title=position,
        phone=phone,
        department=department,
        is_active=True,
    )
    return {
        "id": employee.id,
        "usuario": username,
        "correo": email,
        "nombre": full_name,
        "puesto": position,
    }


def update_admin_employee(db: Session, vendor_id: int, employee_id: int, data: dict) -> bool:
    employee = get_by_vendor(db, vendor_id, employee_id)
    if not employee:
        return False

    meta = _decode_position_meta(employee.position)
    if "nombre" in data:
        meta["n"] = data["nombre"]
    if "puesto" in data:
        meta["p"] = data["puesto"]
    if "celular" in data:
        meta["t"] = data["celular"]
    if "departamento" in data:
        meta["d"] = data["departamento"]

    updates = {
        "position": json.dumps(meta, ensure_ascii=False)[:400],
        "full_name": str(meta.get("n") or ""),
        "job_title": str(meta.get("p") or ""),
        "phone": str(meta.get("t") or ""),
        "department": str(meta.get("d") or ""),
    }
    role_name = str(data.get("rol") or "").lower()
    if role_name == "administrador":
        updates["role"] = "manager"
    elif role_name == "usuario":
        updates["role"] = "seller"

    is_active = data.get("is_active")
    if is_active is None and "estado" in data:
        is_active = str(data["estado"]).lower() != "inactivo"
    if is_active is not None:
        updates["is_active"] = bool(is_active)

    update_employee(db, employee, **updates)
    if data.get("correo"):
        user = db.query(User).filter_by(id=int(employee.user_id or 0)).first()
        if user:
            user.email = data["correo"]
            db.flush()
    return True


def delete_admin_employee(db: Session, vendor_id: int, employee_id: int) -> bool:
    employee = get_by_vendor(db, vendor_id, employee_id)
    if not employee:
        return False
    user_id = int(employee.user_id or 0)
    delete_employee(db, employee)
    other_refs = db.query(StoreEmployee).filter_by(user_id=user_id).count()
    if user_id and other_refs == 0:
        db.query(User).filter_by(id=user_id, user_type="store_employee").delete()
        db.flush()
    return True
