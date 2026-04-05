from __future__ import annotations

from fastapi_modulo.modulos.multitienda.servicios.store_tables_shared import (
    apply_updates,
    managed_session,
    normalize_datetime_fields,
    optional_session,
    orm_to_dict,
)


def _serialize_rows(rows) -> list[dict]:
    return [orm_to_dict(row) for row in rows]


def _list_by_vendor_compat(service_module, store_id: int, *, db=None) -> list[dict]:
    with optional_session(db) as current_db:
        return _serialize_rows(service_module.list_by_vendor(current_db, store_id))


def _update_by_vendor_compat(
    service_module,
    store_id: int,
    record_id: int,
    data: dict,
    col_map: dict,
    *,
    update_fn_name: str,
    normalizer=None,
    db=None,
):
    with optional_session(db, commit=True) as current_db:
        normalized = normalizer(data) if normalizer else data
        record = service_module.get_by_vendor(current_db, store_id, record_id)
        if not record or not apply_updates(record, normalized, col_map):
            return None
        return orm_to_dict(getattr(service_module, update_fn_name)(current_db, record))


def _delete_by_vendor_compat(
    service_module,
    store_id: int,
    record_id: int,
    *,
    delete_fn_name: str,
    db=None,
) -> bool:
    with optional_session(db, commit=True) as current_db:
        record = service_module.get_by_vendor(current_db, store_id, record_id)
        if not record:
            return False
        getattr(service_module, delete_fn_name)(current_db, record)
        return True


def list_employees(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service
    return _list_by_vendor_compat(employee_service, store_id)


def create_employee(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service
    with managed_session(commit=True) as db:
        employee = employee_service.create_for_vendor(
            db,
            store_id,
            user_id=int(data.get("user_id") or 0),
            role=str(data.get("role") or data.get("rol") or "seller"),
            position=str(data.get("position") or data.get("puesto") or ""),
            full_name=str(data.get("full_name") or data.get("nombre") or ""),
            job_title=str(data.get("job_title") or data.get("puesto") or ""),
            phone=str(data.get("phone") or data.get("celular") or ""),
            department=str(data.get("department") or data.get("departamento") or ""),
            is_active=bool(data.get("is_active", True)),
        )
        return orm_to_dict(employee)


def update_employee(store_id: int, employee_id: int, data: dict):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service
    return _update_by_vendor_compat(
        employee_service,
        store_id,
        employee_id,
        data,
        {
            "role": "role", "rol": "role",
            "position": "position",
            "full_name": "full_name", "nombre": "full_name",
            "job_title": "job_title", "puesto": "job_title",
            "phone": "phone", "celular": "phone",
            "department": "department", "departamento": "department",
            "is_active": "is_active",
        },
        update_fn_name="update_employee",
    )


def delete_employee(store_id: int, employee_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service
    return _delete_by_vendor_compat(
        employee_service,
        store_id,
        employee_id,
        delete_fn_name="delete_employee",
    )


def change_employee_password(store_id: int, employee_id: int, password: str) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service
    with managed_session(commit=True) as db:
        return employee_service.set_password_for_vendor_employee(db, store_id, employee_id, password)


def list_coupons(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service
    return _list_by_vendor_compat(coupon_service, store_id)


def create_coupon(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service
    with managed_session(commit=True) as db:
        normalized = normalize_datetime_fields(data, "valid_from", "inicio", "valid_until", "expiracion")
        coupon = coupon_service.create_for_vendor(
            db, store_id,
            code=str(normalized.get("code") or normalized.get("codigo") or "").strip().upper(),
            discount_type=str(normalized.get("discount_type") or normalized.get("tipo") or "percent"),
            discount_value=float(normalized.get("discount_value") or normalized.get("valor") or 0),
            min_order_amount=float(normalized.get("min_order_amount") or normalized.get("min_compra") or 0),
            max_uses=int(normalized["max_uses"]) if normalized.get("max_uses") else None,
            per_user_limit=int(normalized.get("per_user_limit") or 1),
            valid_from=normalized.get("valid_from") or normalized.get("inicio"),
            valid_until=normalized.get("valid_until") or normalized.get("expiracion"),
            is_active=bool(normalized.get("is_active", True)),
        )
        return orm_to_dict(coupon)


def update_coupon(store_id: int, coupon_id: int, data: dict):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service
    return _update_by_vendor_compat(
        coupon_service,
        store_id,
        coupon_id,
        data,
        {
            "code": "code", "codigo": "code",
            "discount_type": "discount_type", "tipo": "discount_type",
            "discount_value": "discount_value", "valor": "discount_value",
            "min_order_amount": "min_order_amount", "min_compra": "min_order_amount",
            "max_uses": "max_uses", "per_user_limit": "per_user_limit",
            "valid_from": "valid_from", "inicio": "valid_from",
            "valid_until": "valid_until", "expiracion": "valid_until",
            "is_active": "is_active",
        },
        update_fn_name="update_coupon",
        normalizer=lambda payload: normalize_datetime_fields(payload, "valid_from", "inicio", "valid_until", "expiracion"),
    )


def delete_coupon(store_id: int, coupon_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service
    return _delete_by_vendor_compat(
        coupon_service,
        store_id,
        coupon_id,
        delete_fn_name="delete_coupon",
    )


def validate_coupon(store_id: int, code: str, cart_total: float = 0.0) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service
    with managed_session() as db:
        return coupon_service.validate_coupon_for_vendor(db, store_id, code, cart_total=cart_total)


def redeem_coupon(store_id: int, coupon_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service
    with managed_session(commit=True) as db:
        return coupon_service.redeem_for_vendor(db, store_id, coupon_id)


def list_referrals(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals import service as referral_service
    return _list_by_vendor_compat(referral_service, store_id)


def create_referral(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals import service as referral_service
    with managed_session(commit=True) as db:
        normalized = normalize_datetime_fields(data, "reward_given_at")
        referral = referral_service.create_for_vendor(
            db, store_id,
            referrer_user_id=int(normalized.get("referrer_user_id") or 0),
            referral_code=str(normalized.get("referral_code") or normalized.get("codigo") or "").strip().upper(),
            reward_type=normalized.get("reward_type"),
            reward_value=float(normalized["reward_value"]) if normalized.get("reward_value") else None,
            status="pending",
        )
        return orm_to_dict(referral)


def update_referral(store_id: int, referral_id: int, data: dict):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals import service as referral_service
    return _update_by_vendor_compat(
        referral_service,
        store_id,
        referral_id,
        data,
        {
            "status": "status", "estado": "status",
            "referred_user_id": "referred_user_id",
            "reward_type": "reward_type",
            "reward_value": "reward_value",
            "reward_given_at": "reward_given_at",
        },
        update_fn_name="update_referral",
        normalizer=lambda payload: normalize_datetime_fields(payload, "reward_given_at"),
    )


def delete_referral(store_id: int, referral_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals import service as referral_service
    return _delete_by_vendor_compat(
        referral_service,
        store_id,
        referral_id,
        delete_fn_name="delete_referral",
    )


def list_reservations(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations import service as reservation_service
    return _list_by_vendor_compat(reservation_service, store_id)


def create_reservation(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations import service as reservation_service
    with managed_session(commit=True) as db:
        normalized = normalize_datetime_fields(data, "reservation_date", "fecha")
        reservation = reservation_service.create_for_vendor(
            db, store_id,
            customer_user_id=int(normalized.get("customer_user_id") or 0),
            product_id=int(normalized["product_id"]) if normalized.get("product_id") else None,
            reservation_date=normalized.get("reservation_date") or normalized.get("fecha"),
            time_slot=normalized.get("time_slot") or normalized.get("hora"),
            duration_minutes=int(normalized.get("duration_minutes") or 60),
            notes=str(normalized.get("notes") or normalized.get("notas") or ""),
        )
        return orm_to_dict(reservation)


def update_reservation(store_id: int, reservation_id: int, data: dict):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations import service as reservation_service
    return _update_by_vendor_compat(
        reservation_service,
        store_id,
        reservation_id,
        data,
        {
            "status": "status", "estado": "status",
            "reservation_date": "reservation_date", "fecha": "reservation_date",
            "time_slot": "time_slot", "hora": "time_slot",
            "duration_minutes": "duration_minutes",
            "notes": "notes", "notas": "notes",
            "confirmed_at": "confirmed_at", "cancelled_at": "cancelled_at",
        },
        update_fn_name="update_reservation",
        normalizer=lambda payload: normalize_datetime_fields(payload, "reservation_date", "fecha", "confirmed_at", "cancelled_at"),
    )


def delete_reservation(store_id: int, reservation_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations import service as reservation_service
    return _delete_by_vendor_compat(
        reservation_service,
        store_id,
        reservation_id,
        delete_fn_name="delete_reservation",
    )


def list_followers(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers import service as follower_service
    return _list_by_vendor_compat(follower_service, store_id)


def create_follower(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers import service as follower_service
    with managed_session(commit=True) as db:
        return orm_to_dict(follower_service.create_for_vendor(db, store_id, user_id=int(data.get("user_id") or 0)))


def update_follower(store_id: int, follower_id: int, data: dict):
    return None


def delete_follower(store_id: int, follower_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers import service as follower_service
    return _delete_by_vendor_compat(
        follower_service,
        store_id,
        follower_id,
        delete_fn_name="delete_follower",
    )


def list_videos(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos import service as video_service
    return _list_by_vendor_compat(video_service, store_id)


def create_video(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos import service as video_service
    with managed_session(commit=True) as db:
        video = video_service.create_for_vendor(
            db, store_id,
            product_id=int(data["product_id"]) if data.get("product_id") else None,
            title=str(data.get("title") or data.get("nombre") or ""),
            url=str(data.get("url") or ""),
            thumbnail=data.get("thumbnail"),
            description=str(data.get("description") or data.get("notas") or ""),
            is_active=bool(data.get("is_active", True)),
            order=int(data.get("order") or 0),
        )
        return orm_to_dict(video)


def delete_video(store_id: int, video_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos import service as video_service
    return _delete_by_vendor_compat(
        video_service,
        store_id,
        video_id,
        delete_fn_name="delete_video",
    )


def list_suppliers(store_id: int, db=None) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers import service as supplier_service
    return _list_by_vendor_compat(supplier_service, store_id, db=db)


def create_supplier(store_id: int, data: dict, db=None) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers import service as supplier_service
    with optional_session(db, commit=True) as current_db:
        supplier = supplier_service.create_for_vendor(
            current_db, store_id,
            name=str(data.get("name") or data.get("nombre") or "").strip(),
            contact_name=str(data.get("contact_name") or ""),
            email=str(data.get("email") or ""),
            phone=str(data.get("phone") or data.get("telefono") or ""),
            address=str(data.get("address") or data.get("direccion") or ""),
            country=str(data.get("country") or ""),
            website=data.get("website"),
            notes=str(data.get("notes") or data.get("notas") or ""),
            is_active=bool(data.get("is_active", True)),
        )
        return orm_to_dict(supplier)


def update_supplier(store_id: int, supplier_id: int, data: dict, db=None):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers import service as supplier_service
    return _update_by_vendor_compat(
        supplier_service,
        store_id,
        supplier_id,
        data,
        {
            "name": "name", "nombre": "name",
            "contact_name": "contact_name", "email": "email",
            "phone": "phone", "telefono": "phone",
            "address": "address", "direccion": "address",
            "country": "country", "website": "website",
            "notes": "notes", "notas": "notes",
            "is_active": "is_active",
        },
        update_fn_name="update_supplier",
        db=db,
    )


def delete_supplier(store_id: int, supplier_id: int, db=None) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers import service as supplier_service
    return _delete_by_vendor_compat(
        supplier_service,
        store_id,
        supplier_id,
        delete_fn_name="delete_supplier",
        db=db,
    )
