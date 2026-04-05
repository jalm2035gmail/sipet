"""
Capa de acceso a datos para las tablas del núcleo Multitienda.

Fuente de verdad: modelos ORM en marketplace/backend/apps/*/models.py
Esquema real en BD (creado por migrate_phase2.py):
  store_employees, store_coupons, store_referrals, store_reservations,
  store_layaways, store_followers, store_videos, store_suppliers,
  store_whatsapp_config, store_ai_config

El parámetro `store_id` en las funciones públicas corresponde a `vendor_id` en la BD.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from enum import Enum
import json
from sqlalchemy import text
from sqlalchemy.inspection import inspect as sa_inspect
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import SessionLocal


def _coerce(v):
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, Enum):
        return v.value
    return v


def _serialize(row: dict) -> dict:
    return {k: _coerce(v) for k, v in row.items()}


def _rows(db, sql: str, params=None) -> list:
    result = db.execute(text(sql), params or {})
    keys = result.keys()
    return [_serialize(dict(zip(keys, row))) for row in result.fetchall()]


def _row(db, sql: str, params=None):
    result = db.execute(text(sql), params or {})
    keys = result.keys()
    row = result.fetchone()
    return _serialize(dict(zip(keys, row))) if row else None


def _orm_to_dict(instance) -> dict:
    return _serialize({
        attr.key: getattr(instance, attr.key)
        for attr in sa_inspect(instance.__class__).mapper.column_attrs
    })


def _orm_list(query) -> list:
    return [_orm_to_dict(row) for row in query.all()]


def _apply_updates(instance, data: dict, col_map: dict) -> bool:
    updated = False
    seen = set()
    for src, field in col_map.items():
        if data.get(src) is not None and field not in seen:
            setattr(instance, field, data[src])
            seen.add(field)
            updated = True
    return updated


def _parse_datetime_value(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        normalized = normalized.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass
    return value


def _normalize_datetime_fields(data: dict, *fields: str) -> dict:
    normalized = dict(data)
    for field in fields:
        if field in normalized:
            normalized[field] = _parse_datetime_value(normalized[field])
    return normalized


def _build_update_params(data: dict, base_params: dict, col_map: dict) -> tuple[list[str], dict]:
    fields = []
    params = dict(base_params)
    seen = set()
    for src, col in col_map.items():
        if data.get(src) is not None and col not in seen:
            key = f"p_{col}"
            fields.append(f"{col} = :{key}")
            params[key] = data[src]
            seen.add(col)
    return fields, params


def _list_by_vendor(db, table: str, store_id: int, order_by: str) -> list:
    return _rows(
        db,
        f"SELECT * FROM {table} WHERE vendor_id = :vid ORDER BY {order_by}",
        {"vid": store_id},
    )


def _delete_by_vendor(db, table: str, id_column: str, record_id: int, store_id: int) -> bool:
    result = db.execute(
        text(f"DELETE FROM {table} WHERE {id_column} = :rid AND vendor_id = :vid"),
        {"rid": record_id, "vid": store_id},
    )
    return result.rowcount > 0


def _decode_theme(raw_value) -> dict:
    current = raw_value
    for _ in range(3):
        if isinstance(current, dict):
            return current
        if not isinstance(current, str):
            return {}
        try:
            current = json.loads(current)
        except Exception:
            return {}
    return {}


@contextmanager
def _managed_session(*, commit: bool = False):
    db = SessionLocal()
    try:
        yield db
        if commit:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def _optional_session(db=None, *, commit: bool = False):
    if db is not None:
        yield db
        return
    with _managed_session(commit=commit) as own_db:
        yield own_db


def ensure_store_tables(bind=None) -> None:
    """Garantiza las tablas de persistencia del núcleo Multitienda."""
    from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base, engine
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons.models import StoreCoupon  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals.models import StoreReferral  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations.models import StoreReservation  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways.models import StoreLayaway  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers.models import StoreFollower  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos.models import StoreVideo  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers.models import StoreSupplier  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.whatsapp_config.models import StoreWhatsappConfig  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.ai_config.models import StoreAiConfig  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.wishlist.models import WishlistItem  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.cart.models import Cart, CartItem  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.payments.models import IFWalletAccount, IFWalletTransaction, LoanRequest, CheckoutPayment, VendorPayout  # noqa: F401

    Base.metadata.create_all(
        bind=bind or engine,
        tables=[
            Base.metadata.tables[name]
            for name in [
                "store_employees",
                "store_coupons",
                "store_referrals",
                "store_reservations",
                "store_layaways",
                "store_followers",
                "store_videos",
                "store_suppliers",
                "store_whatsapp_config",
                "store_ai_config",
                "wishlist_items",
                "mt_cart",
                "mt_cart_items",
                "mt_if_wallet_accounts",
                "mt_if_wallet_transactions",
                "mt_loan_requests",
                "mt_checkout_payments",
                "vendor_payouts",
            ]
            if name in Base.metadata.tables
        ],
        checkfirst=True,
    )


# ─── EMPLOYEES ───────────────────────────────────────────────────────────────

def list_employees(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service

    with _managed_session() as db:
        return [_orm_to_dict(employee) for employee in employee_service.list_by_vendor(db, store_id)]


def create_employee(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service

    with _managed_session(commit=True) as db:
        employee = employee_service.create_for_vendor(
            db,
            store_id,
            user_id=int(data.get("user_id") or 0),
            role=str(data.get("role") or data.get("rol") or "seller"),
            position=str(data.get("position") or data.get("puesto") or ""),
            is_active=bool(data.get("is_active", True)),
        )
        return _orm_to_dict(employee)


def update_employee(store_id: int, employee_id: int, data: dict):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service

    with _managed_session(commit=True) as db:
        col_map = {"role": "role", "rol": "role",
                   "position": "position", "puesto": "position",
                   "is_active": "is_active"}
        employee = employee_service.get_by_vendor(db, store_id, employee_id)
        if not employee:
            return None
        if not _apply_updates(employee, data, col_map):
            return None
        employee = employee_service.update_employee(db, employee)
        return _orm_to_dict(employee)


def delete_employee(store_id: int, employee_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service

    with _managed_session(commit=True) as db:
        employee = employee_service.get_by_vendor(db, store_id, employee_id)
        if not employee:
            return False
        employee_service.delete_employee(db, employee)
        return True


def change_employee_password(store_id: int, employee_id: int, password: str) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service

    with _managed_session(commit=True) as db:
        return employee_service.set_password_for_vendor_employee(db, store_id, employee_id, password)


# ─── COUPONS ─────────────────────────────────────────────────────────────────

def list_coupons(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service

    with _managed_session() as db:
        return [_orm_to_dict(coupon) for coupon in coupon_service.list_by_vendor(db, store_id)]


def create_coupon(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service

    with _managed_session(commit=True) as db:
        normalized = _normalize_datetime_fields(data, "valid_from", "inicio", "valid_until", "expiracion")
        coupon = coupon_service.create_for_vendor(
            db,
            store_id,
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
        return _orm_to_dict(coupon)


def update_coupon(store_id: int, coupon_id: int, data: dict):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service

    with _managed_session(commit=True) as db:
        normalized = _normalize_datetime_fields(data, "valid_from", "inicio", "valid_until", "expiracion")
        col_map = {"code": "code", "codigo": "code",
                   "discount_type": "discount_type", "tipo": "discount_type",
                   "discount_value": "discount_value", "valor": "discount_value",
                   "min_order_amount": "min_order_amount", "min_compra": "min_order_amount",
                   "max_uses": "max_uses", "per_user_limit": "per_user_limit",
                   "valid_from": "valid_from", "inicio": "valid_from",
                   "valid_until": "valid_until", "expiracion": "valid_until",
                   "is_active": "is_active"}
        coupon = coupon_service.get_by_vendor(db, store_id, coupon_id)
        if not coupon:
            return None
        if not _apply_updates(coupon, normalized, col_map):
            return None
        coupon = coupon_service.update_coupon(db, coupon)
        return _orm_to_dict(coupon)


def delete_coupon(store_id: int, coupon_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service

    with _managed_session(commit=True) as db:
        coupon = coupon_service.get_by_vendor(db, store_id, coupon_id)
        if not coupon:
            return False
        coupon_service.delete_coupon(db, coupon)
        return True


# ─── REFERRALS ───────────────────────────────────────────────────────────────

def list_referrals(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals import service as referral_service

    with _managed_session() as db:
        return [_orm_to_dict(referral) for referral in referral_service.list_by_vendor(db, store_id)]


def create_referral(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals import service as referral_service

    with _managed_session(commit=True) as db:
        normalized = _normalize_datetime_fields(data, "reward_given_at")
        referral = referral_service.create_for_vendor(
            db,
            store_id,
            referrer_user_id=int(normalized.get("referrer_user_id") or 0),
            referral_code=str(normalized.get("referral_code") or normalized.get("codigo") or "").strip().upper(),
            reward_type=normalized.get("reward_type"),
            reward_value=float(normalized["reward_value"]) if normalized.get("reward_value") else None,
            status="pending",
        )
        return _orm_to_dict(referral)


def update_referral(store_id: int, referral_id: int, data: dict):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals import service as referral_service

    with _managed_session(commit=True) as db:
        normalized = _normalize_datetime_fields(data, "reward_given_at")
        col_map = {"status": "status", "estado": "status",
                   "referred_user_id": "referred_user_id",
                   "reward_type": "reward_type", "reward_value": "reward_value",
                   "reward_given_at": "reward_given_at"}
        referral = referral_service.get_by_vendor(db, store_id, referral_id)
        if not referral:
            return None
        if not _apply_updates(referral, normalized, col_map):
            return None
        referral = referral_service.update_referral(db, referral)
        return _orm_to_dict(referral)


def delete_referral(store_id: int, referral_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals import service as referral_service

    with _managed_session(commit=True) as db:
        referral = referral_service.get_by_vendor(db, store_id, referral_id)
        if not referral:
            return False
        referral_service.delete_referral(db, referral)
        return True


# ─── RESERVATIONS ────────────────────────────────────────────────────────────

def list_reservations(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations import service as reservation_service

    with _managed_session() as db:
        return [_orm_to_dict(reservation) for reservation in reservation_service.list_by_vendor(db, store_id)]


def create_reservation(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations import service as reservation_service

    with _managed_session(commit=True) as db:
        normalized = _normalize_datetime_fields(data, "reservation_date", "fecha")
        reservation = reservation_service.create_for_vendor(
            db,
            store_id,
            customer_user_id=int(normalized.get("customer_user_id") or 0),
            product_id=int(normalized["product_id"]) if normalized.get("product_id") else None,
            reservation_date=normalized.get("reservation_date") or normalized.get("fecha"),
            time_slot=normalized.get("time_slot") or normalized.get("hora"),
            duration_minutes=int(normalized.get("duration_minutes") or 60),
            notes=str(normalized.get("notes") or normalized.get("notas") or ""),
        )
        return _orm_to_dict(reservation)


def update_reservation(store_id: int, reservation_id: int, data: dict):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations import service as reservation_service

    with _managed_session(commit=True) as db:
        normalized = _normalize_datetime_fields(
            data,
            "reservation_date",
            "fecha",
            "confirmed_at",
            "cancelled_at",
        )
        col_map = {"status": "status", "estado": "status",
                   "reservation_date": "reservation_date", "fecha": "reservation_date",
                   "time_slot": "time_slot", "hora": "time_slot",
                   "duration_minutes": "duration_minutes",
                   "notes": "notes", "notas": "notes",
                   "confirmed_at": "confirmed_at", "cancelled_at": "cancelled_at"}
        reservation = reservation_service.get_by_vendor(db, store_id, reservation_id)
        if not reservation:
            return None
        if not _apply_updates(reservation, normalized, col_map):
            return None
        reservation = reservation_service.update_reservation(db, reservation)
        return _orm_to_dict(reservation)


def delete_reservation(store_id: int, reservation_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations import service as reservation_service

    with _managed_session(commit=True) as db:
        reservation = reservation_service.get_by_vendor(db, store_id, reservation_id)
        if not reservation:
            return False
        reservation_service.delete_reservation(db, reservation)
        return True


# ─── LAYAWAYS ────────────────────────────────────────────────────────────────

def list_layaways(store_id: int) -> list:
    with _managed_session() as db:
        return _list_by_vendor(db, "store_layaways", store_id, "created_at DESC")


def create_layaway(store_id: int, data: dict) -> dict:
    with _managed_session(commit=True) as db:
        total = float(data.get("total_amount") or data.get("precio_total") or 0)
        down = float(data.get("downpayment") or data.get("enganche") or 0)
        row = _row(db,
            "INSERT INTO store_layaways "
            "(vendor_id, customer_user_id, product_id, total_amount, downpayment, balance_due, due_date, notes, status) "
            "VALUES (:vid, :cuid, :pid, :total, :down, :balance, :due, :notes, 'active') RETURNING *",
            {"vid": store_id,
             "cuid": int(data.get("customer_user_id") or 0),
             "pid": int(data["product_id"]) if data.get("product_id") else 0,
             "total": total,
             "down": down,
             "balance": round(total - down, 2),
             "due": data.get("due_date") or data.get("fecha_limite"),
             "notes": str(data.get("notes") or data.get("notas") or "")})
        return row or {}


def update_layaway(store_id: int, layaway_id: int, data: dict):
    with _managed_session(commit=True) as db:
        col_map = {"status": "status", "estado": "status",
                   "balance_due": "balance_due", "saldo_pendiente": "balance_due",
                   "due_date": "due_date", "fecha_limite": "due_date",
                   "notes": "notes", "notas": "notes"}
        fields, params = _build_update_params(data, {"vid": store_id, "lid": layaway_id}, col_map)
        if not fields:
            return None
        row = _row(db,
            "UPDATE store_layaways SET " + ", ".join(fields) + ", updated_at = CURRENT_TIMESTAMP "
            "WHERE id = :lid AND vendor_id = :vid RETURNING *", params)
        return row


def delete_layaway(store_id: int, layaway_id: int) -> bool:
    with _managed_session(commit=True) as db:
        return _delete_by_vendor(db, "store_layaways", "id", layaway_id, store_id)


def _ensure_layaway_extras(db) -> None:
    """Add rich columns to store_layaways and create store_layaway_payments if needed."""
    extra_cols = [
        ("folio",          "TEXT DEFAULT ''"),
        ("customer_name",  "TEXT DEFAULT ''"),
        ("customer_phone", "TEXT DEFAULT ''"),
        ("customer_email", "TEXT DEFAULT ''"),
        ("product_name",   "TEXT DEFAULT ''"),
        ("product_sku",    "TEXT DEFAULT ''"),
        ("modalidad",      "TEXT DEFAULT 'libre'"),
        ("cuotas",         "INTEGER DEFAULT 0"),
        ("periodicidad",   "TEXT DEFAULT 'mensual'"),
        ("start_date",     "TEXT DEFAULT ''"),
    ]
    for col, typ in extra_cols:
        try:
            db.execute(text(f"ALTER TABLE store_layaways ADD COLUMN {col} {typ}"))
            db.commit()
        except Exception:
            pass  # column already exists

    db.execute(text("""
        CREATE TABLE IF NOT EXISTS store_layaway_payments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            layaway_id INTEGER NOT NULL,
            amount     REAL NOT NULL DEFAULT 0,
            paid_at    TEXT DEFAULT '',
            method     TEXT DEFAULT 'efectivo',
            reference  TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()


def _recalculate_layaway_balance(db, layaway_id: int, layaway_row: dict, *, paid_status: str = "completado") -> dict | None:
    total_paid_row = _row(
        db,
        "SELECT COALESCE(SUM(amount),0) AS s FROM store_layaway_payments WHERE layaway_id = :lid",
        {"lid": layaway_id},
    )
    total_paid = float((total_paid_row or {}).get("s", 0)) + float(layaway_row.get("downpayment") or 0)
    total_amt = float(layaway_row.get("total_amount") or 0)
    new_balance = max(0.0, round(total_amt - total_paid, 2))
    new_status = paid_status if new_balance <= 0 else "active"
    return _row(
        db,
        "UPDATE store_layaways SET balance_due = :bal, status = :st, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = :lid RETURNING *",
        {"bal": new_balance, "st": new_status, "lid": layaway_id},
    )


def create_layaway_rich(store_id: int, data: dict) -> dict:
    """Create layaway with all UI fields. Replaces create_layaway for the panel."""
    with _managed_session(commit=True) as db:
        _ensure_layaway_extras(db)
        total = float(data.get("total_amount") or data.get("precio") or 0)
        down  = float(data.get("downpayment") or data.get("enganche") or 0)

        # Auto-generate folio
        cnt = _row(db, "SELECT COUNT(*) AS n FROM store_layaways WHERE vendor_id = :vid",
                   {"vid": store_id})
        n = int((cnt or {}).get("n", 0)) + 1
        folio = data.get("folio") or f"AP-{__import__('datetime').date.today().year}-{n:04d}"

        row = _row(db,
            "INSERT INTO store_layaways "
            "(vendor_id, customer_user_id, product_id, total_amount, downpayment, balance_due, due_date, notes, status,"
            " folio, customer_name, customer_phone, customer_email, product_name, product_sku,"
            " modalidad, cuotas, periodicidad, start_date) "
            "VALUES (:vid, 0, 0, :total, :down, :balance, :due, :notes, 'active',"
            " :folio, :cname, :cphone, :cemail, :pname, :psku,"
            " :modalidad, :cuotas, :periodicidad, :sdate) RETURNING *",
            {
                "vid":        store_id,
                "total":      total,
                "down":       down,
                "balance":    round(total - down, 2),
                "due":        data.get("due_date") or data.get("fechaLimite") or "",
                "notes":      data.get("notes") or data.get("notas") or "",
                "folio":      folio,
                "cname":      data.get("customer_name") or data.get("nombre") or "",
                "cphone":     data.get("customer_phone") or data.get("telefono") or "",
                "cemail":     data.get("customer_email") or data.get("email") or "",
                "pname":      data.get("product_name") or data.get("producto") or "",
                "psku":       data.get("product_sku") or data.get("sku") or "",
                "modalidad":  data.get("modalidad") or "libre",
                "cuotas":     int(data.get("cuotas") or 0),
                "periodicidad": data.get("periodicidad") or "mensual",
                "sdate":      data.get("start_date") or data.get("fechaInicio") or "",
            })
        return row or {}


def update_layaway_rich(store_id: int, layaway_id: int, data: dict) -> dict | None:
    """Update layaway with all UI fields."""
    with _managed_session(commit=True) as db:
        _ensure_layaway_extras(db)
        col_map = {
            "status": "status", "estado": "status",
            "balance_due": "balance_due", "saldo_pendiente": "balance_due",
            "due_date": "due_date", "fechaLimite": "due_date",
            "notes": "notes", "notas": "notes",
            "folio": "folio",
            "customer_name": "customer_name", "nombre": "customer_name",
            "customer_phone": "customer_phone", "telefono": "customer_phone",
            "customer_email": "customer_email", "email": "customer_email",
            "product_name": "product_name", "producto": "product_name",
            "product_sku": "product_sku", "sku": "product_sku",
            "total_amount": "total_amount", "precio": "total_amount",
            "downpayment": "downpayment", "enganche": "downpayment",
            "modalidad": "modalidad",
            "cuotas": "cuotas",
            "periodicidad": "periodicidad",
            "start_date": "start_date", "fechaInicio": "start_date",
        }
        fields, params = _build_update_params(data, {"vid": store_id, "lid": layaway_id}, col_map)
        if not fields:
            return None
        row = _row(db,
            "UPDATE store_layaways SET " + ", ".join(fields) + ", updated_at = CURRENT_TIMESTAMP "
            "WHERE id = :lid AND vendor_id = :vid RETURNING *", params)
        return row


def list_layaway_payments(store_id: int, layaway_id: int) -> list:
    with _managed_session() as db:
        _ensure_layaway_extras(db)
        # verify ownership
        ap = _row(db, "SELECT id FROM store_layaways WHERE id = :lid AND vendor_id = :vid",
                  {"lid": layaway_id, "vid": store_id})
        if not ap:
            return []
        return _rows(db,
            "SELECT * FROM store_layaway_payments WHERE layaway_id = :lid ORDER BY paid_at ASC, id ASC",
            {"lid": layaway_id})


def add_layaway_payment(store_id: int, layaway_id: int, data: dict) -> dict:
    with _managed_session(commit=True) as db:
        _ensure_layaway_extras(db)
        ap = _row(db, "SELECT * FROM store_layaways WHERE id = :lid AND vendor_id = :vid",
                  {"lid": layaway_id, "vid": store_id})
        if not ap:
            return {"error": "Apartado no encontrado"}

        amount = float(data.get("amount") or data.get("monto") or 0)
        if amount <= 0:
            return {"error": "Monto inválido"}

        payment = _row(db,
            "INSERT INTO store_layaway_payments (layaway_id, amount, paid_at, method, reference) "
            "VALUES (:lid, :amt, :paid_at, :method, :ref) RETURNING *",
            {
                "lid":     layaway_id,
                "amt":     amount,
                "paid_at": data.get("paid_at") or data.get("fecha") or "",
                "method":  data.get("method") or data.get("metodo") or "efectivo",
                "ref":     data.get("reference") or data.get("referencia") or "",
            })
        _recalculate_layaway_balance(db, layaway_id, ap)
        return payment or {}


def delete_layaway_payment(store_id: int, layaway_id: int, payment_id: int) -> bool:
    with _managed_session(commit=True) as db:
        _ensure_layaway_extras(db)
        ap = _row(db, "SELECT * FROM store_layaways WHERE id = :lid AND vendor_id = :vid",
                  {"lid": layaway_id, "vid": store_id})
        if not ap:
            return False
        r = db.execute(text("DELETE FROM store_layaway_payments WHERE id = :pid AND layaway_id = :lid"),
                       {"pid": payment_id, "lid": layaway_id})
        _recalculate_layaway_balance(db, layaway_id, ap)
        return r.rowcount > 0


def set_layaway_status(store_id: int, layaway_id: int, new_status: str) -> dict | None:
    """Set apartado status to: cancelado, active (reactivar), entregado."""
    allowed = {"cancelado", "active", "entregado"}
    if new_status not in allowed:
        return None
    with _managed_session(commit=True) as db:
        _ensure_layaway_extras(db)
        row = _row(db,
            "UPDATE store_layaways SET status = :st, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = :lid AND vendor_id = :vid RETURNING *",
            {"st": new_status, "lid": layaway_id, "vid": store_id})
        return row


def mark_overdue_layaways(store_id: int) -> int:
    """Mark active layaways whose due_date < today as 'vencido'. Returns count updated."""
    with _managed_session(commit=True) as db:
        _ensure_layaway_extras(db)
        r = db.execute(text(
            "UPDATE store_layaways SET status = 'vencido', updated_at = CURRENT_TIMESTAMP "
            "WHERE vendor_id = :vid AND status = 'active' AND due_date != '' AND due_date < date('now')"
        ), {"vid": store_id})
        return r.rowcount


# ─── FOLLOWERS ───────────────────────────────────────────────────────────────

def list_followers(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers import service as follower_service

    with _managed_session() as db:
        return [_orm_to_dict(follower) for follower in follower_service.list_by_vendor(db, store_id)]


def create_follower(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers import service as follower_service

    with _managed_session(commit=True) as db:
        follower = follower_service.create_for_vendor(db, store_id, user_id=int(data.get("user_id") or 0))
        return _orm_to_dict(follower)


def update_follower(store_id: int, follower_id: int, data: dict):
    return None  # no hay campos actualizables en store_followers


def delete_follower(store_id: int, follower_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers import service as follower_service

    with _managed_session(commit=True) as db:
        follower = follower_service.get_by_vendor(db, store_id, follower_id)
        if not follower:
            return False
        follower_service.delete_follower(db, follower)
        return True


# ─── VIDEOS ──────────────────────────────────────────────────────────────────

def list_videos(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos import service as video_service

    with _managed_session() as db:
        return [_orm_to_dict(video) for video in video_service.list_by_vendor(db, store_id)]


def create_video(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos import service as video_service

    with _managed_session(commit=True) as db:
        video = video_service.create_for_vendor(
            db,
            store_id,
            product_id=int(data["product_id"]) if data.get("product_id") else None,
            title=str(data.get("title") or data.get("nombre") or ""),
            url=str(data.get("url") or ""),
            thumbnail=data.get("thumbnail"),
            description=str(data.get("description") or data.get("notas") or ""),
            is_active=bool(data.get("is_active", True)),
            order=int(data.get("order") or 0),
        )
        return _orm_to_dict(video)


def delete_video(store_id: int, video_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos import service as video_service

    with _managed_session(commit=True) as db:
        video = video_service.get_by_vendor(db, store_id, video_id)
        if not video:
            return False
        video_service.delete_video(db, video)
        return True


# ─── SUPPLIERS ───────────────────────────────────────────────────────────────

def list_suppliers(store_id: int, db=None) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers import service as supplier_service

    with _optional_session(db) as db:
        return [_orm_to_dict(supplier) for supplier in supplier_service.list_by_vendor(db, store_id)]


def create_supplier(store_id: int, data: dict, db=None) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers import service as supplier_service

    with _optional_session(db, commit=True) as db:
        supplier = supplier_service.create_for_vendor(
            db,
            store_id,
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
        return _orm_to_dict(supplier)


def update_supplier(store_id: int, supplier_id: int, data: dict, db=None):
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers import service as supplier_service

    with _optional_session(db, commit=True) as db:
        col_map = {"name": "name", "nombre": "name",
                   "contact_name": "contact_name",
                   "email": "email",
                   "phone": "phone", "telefono": "phone",
                   "address": "address", "direccion": "address",
                   "country": "country", "website": "website",
                   "notes": "notes", "notas": "notes",
                   "is_active": "is_active"}
        supplier = supplier_service.get_by_vendor(db, store_id, supplier_id)
        if not supplier:
            return None
        if not _apply_updates(supplier, data, col_map):
            return None
        supplier = supplier_service.update_supplier(db, supplier)
        return _orm_to_dict(supplier)


def delete_supplier(store_id: int, supplier_id: int, db=None) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers import service as supplier_service

    with _optional_session(db, commit=True) as db:
        supplier = supplier_service.get_by_vendor(db, store_id, supplier_id)
        if not supplier:
            return False
        supplier_service.delete_supplier(db, supplier)
        return True


# ─── STATS ───────────────────────────────────────────────────────────────────

def get_store_stats(store_id: int) -> dict:
    """Retorna conteos reales y datos de analítica de los últimos 7 días."""
    from datetime import date, timedelta
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.analytics.models import VendorAnalytics
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons.models import StoreCoupon
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product

    with _managed_session() as db:
        def _safe_count(sql, params):
            try:
                row = _row(db, sql, params)
                return int(row["cnt"]) if row else 0
            except Exception:
                return 0

        products = db.query(Product).filter_by(vendor_id=store_id).count()
        employees = db.query(StoreEmployee).filter_by(vendor_id=store_id).count()
        coupons = db.query(StoreCoupon).filter_by(vendor_id=store_id, is_active=True).count()
        orders = _safe_count("SELECT COUNT(*) AS cnt FROM orders WHERE vendor_id = :vid", {"vid": store_id})

        today = date.today()
        chart_labels, chart_values = [], []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            chart_labels.append(d.strftime("%d/%m"))
            try:
                row = (
                    db.query(VendorAnalytics)
                    .filter_by(vendor_id=store_id, date=d)
                    .first()
                )
                chart_values.append(int(row.store_views or 0) if row else 0)
            except Exception:
                chart_values.append(0)

        return {
            "products":     products,
            "employees":    employees,
            "coupons":      coupons,
            "orders":       orders,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
        }


# ─── PUBLIC PRODUCTS (tienda pública) ────────────────────────────────────────

def get_public_products(store_id: int = None, featured_only: bool = False) -> list:
    """
    Retorna todos los productos publicados y activos.
    Si store_id es None, retorna de todas las tiendas.
    Campos adaptados al formato que usa vistas/tienda.py.
    """
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import ProductImage
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore

    try:
        with _managed_session() as db:
                vendor_query = db.query(VendorStore).filter_by(is_active=True)
                if store_id is not None:
                    vendor_query = vendor_query.filter(VendorStore.id == store_id)
                elif featured_only:
                    vendor_query = vendor_query.filter(VendorStore.is_featured.is_(True))
                vendor_rows = _orm_list(vendor_query.order_by(VendorStore.id.desc()))
                themed_products = []
                themed_seen: set[tuple] = set()
                for vendor in vendor_rows:
                    theme = _decode_theme(vendor.get("store_theme"))
                    catalog_products = theme.get("catalog_products")
                    if not isinstance(catalog_products, list):
                        continue
                    for item in catalog_products:
                        if not isinstance(item, dict):
                            continue
                        is_public = bool(item.get("publicado")) or bool(item.get("ecomPublicado"))
                        if not is_public:
                            continue
                        nombre = str(item.get("nombre") or "").strip()
                        if not nombre:
                            continue
                        # Deduplicar por (vendor_id, nombre) — evita dobles si el mismo producto
                        # fue guardado dos veces con slugs distintos (ej: "sandwindh" y "sandwindh-2")
                        themed_dedup_key = (vendor["id"], nombre.lower())
                        if themed_dedup_key in themed_seen:
                            continue
                        themed_seen.add(themed_dedup_key)
                        raw_img = str(item.get("imagen") or "").strip()
                        if raw_img.startswith(("http://localhost", "http://127.", "http://0.0.0.0")):
                            raw_img = ""
                        themed_products.append({
                            "id":           item.get("db_product_id") or item.get("_id") or item.get("id"),
                            "vendor_id":    vendor["id"],
                            "nombre":       nombre,
                            "precio":       float(item.get("precio") or 0),
                            "imagen":       raw_img,
                            "galleryImages": [img for img in (item.get("galleryImages") or []) if isinstance(img, str) and img],
                            "categoria":    item.get("categoria") or "",
                            "slug":         item.get("slug") or "",
                            "store_slug":   str(vendor.get("store_slug") or "").strip().lower(),
                            "descCorta":    item.get("descCorta") or "",
                            "descLarga":    item.get("descLarga") or item.get("descripcion") or "",
                            "mostrarDetalles": item.get("mostrarDetalles") is not False,
                            "detallesHtml": item.get("detallesHtml") or "",
                            "mostrarEspecificaciones": item.get("mostrarEspecificaciones") is not False,
                            "especificacionesHtml": item.get("especificacionesHtml") or "",
                            "mostrarCondiciones": item.get("mostrarCondiciones") is not False,
                            "condicionesHtml": item.get("condicionesHtml") or "",
                            "tienda":       vendor.get("store_name") or "",
                            "publicado":    True,
                            "nuevo":        bool(item.get("nuevo")),
                        })

                # Rellenar imagen faltante desde product_images para themed_products sin imagen
                ids_sin_imagen = [
                    int(item["id"]) for item in themed_products
                    if not item["imagen"] and isinstance(item["id"], int)
                ]
                if ids_sin_imagen:
                    img_rows = _orm_list(
                        db.query(ProductImage)
                        .filter(
                            ProductImage.is_primary.is_(True),
                            ProductImage.product_id.in_(ids_sin_imagen),
                        )
                    )
                    img_map = {int(r["product_id"]): str(r["image"] or "") for r in img_rows}
                    for item in themed_products:
                        if not item["imagen"] and isinstance(item["id"], int) and item["id"] in img_map:
                            item["imagen"] = img_map[item["id"]]

                # Consulta DB: intenta con product_category; si falla, usa versión simple
                db_params: dict = {}
                try:
                    sql = (
                        "SELECT p.id, p.vendor_id, p.name, p.description, p.price, "
                        "p.stock_quantity, p.slug, p.is_active, p.status, p.created_at, "
                        "c.name AS category_name, "
                        "pi.image AS primary_image, "
                        "v.store_name AS store_name, "
                        "v.store_slug AS store_slug "
                        "FROM products p "
                        "LEFT JOIN categories c ON c.id = ("
                        "  SELECT id FROM categories WHERE id IN ("
                        "    SELECT category_id FROM product_category WHERE product_id = p.id LIMIT 1"
                        "  ) LIMIT 1"
                        ") "
                        "LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1 "
                        "LEFT JOIN vendors v ON v.id = p.vendor_id "
                        "WHERE p.status = 'published' AND p.is_active = 1"
                    )
                    if store_id is not None:
                        sql += " AND p.vendor_id = :vid"
                        db_params["vid"] = store_id
                    elif featured_only:
                        sql += " AND v.is_featured = 1"
                    sql += " ORDER BY p.id DESC"
                    rows = _rows(db, sql, db_params)
                    use_category = True
                except Exception:
                    # Fallback: sin product_category
                    sql = (
                        "SELECT p.id, p.vendor_id, p.name, p.description, p.price, "
                        "p.stock_quantity, p.slug, p.is_active, p.status, "
                        "pi.image AS primary_image, "
                        "v.store_name AS store_name, "
                        "v.store_slug AS store_slug "
                        "FROM products p "
                        "LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1 "
                        "LEFT JOIN vendors v ON v.id = p.vendor_id "
                        "WHERE p.status = 'published' AND p.is_active = 1"
                    )
                    if store_id is not None:
                        sql += " AND p.vendor_id = :vid"
                        db_params["vid"] = store_id
                    elif featured_only:
                        sql += " AND v.is_featured = 1"
                    sql += " ORDER BY p.id DESC"
                    rows = _rows(db, sql, db_params)
                    use_category = False

                result = []
                for r in rows:
                    result.append({
                        "id":           r["id"],
                        "vendor_id":    r["vendor_id"],
                        "nombre":       r["name"] or "",
                        "precio":       float(r["price"] or 0),
                        "imagen":       r["primary_image"] or "",
                        "galleryImages": [],
                        "categoria":    (r.get("category_name") or "") if use_category else "",
                        "slug":         r["slug"] or "",
                        "store_slug":   str(r.get("store_slug") or "").strip().lower(),
                        "descCorta":    r["description"] or "",
                        "descLarga":    r["description"] or "",
                        "mostrarDetalles": False,
                        "detallesHtml": "",
                        "mostrarEspecificaciones": False,
                        "especificacionesHtml": "",
                        "mostrarCondiciones": False,
                        "condicionesHtml": "",
                        "tienda":       r["store_name"] or "",
                        "publicado":    True,
                        "nuevo":        False,
                    })

                # Merge con dedup por nombre Y por slug — siempre se ejecuta
                merged = []
                seen_slug: set = set()
                seen_nombre: set = set()
                for item in themed_products + result:
                    item_vendor = str(item.get("vendor_id") or "").strip()
                    item_nombre = str(item.get("nombre") or "").strip().lower()
                    item_slug = str(item.get("slug") or "").strip().lower()
                    slug_key = (item_vendor, item_slug) if item_slug else None
                    nombre_key = (item_vendor, item_nombre) if item_nombre else None
                    if (slug_key and slug_key in seen_slug) or (nombre_key and nombre_key in seen_nombre):
                        continue
                    if slug_key:
                        seen_slug.add(slug_key)
                    if nombre_key:
                        seen_nombre.add(nombre_key)
                    merged.append(item)
                return merged
    except Exception:
        return []


# ─── COUPON VALIDATION ───────────────────────────────────────────────────────

def validate_coupon(store_id: int, code: str, cart_total: float = 0.0) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service

    with _managed_session() as db:
        return coupon_service.validate_coupon_for_vendor(db, store_id, code, cart_total=cart_total)


def redeem_coupon(store_id: int, coupon_id: int) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import service as coupon_service

    with _managed_session(commit=True) as db:
        return coupon_service.redeem_for_vendor(db, store_id, coupon_id)


# ─── LOYALTY ─────────────────────────────────────────────────────────────────

def _ensure_loyalty_tables(db) -> None:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty.models import (
        LoyaltyAccount,
        LoyaltyPlan,
        LoyaltyTransaction,
    )
    from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base

    Base.metadata.create_all(
        bind=db.get_bind(),
        tables=[
            Base.metadata.tables[LoyaltyPlan.__tablename__],
            Base.metadata.tables[LoyaltyAccount.__tablename__],
            Base.metadata.tables[LoyaltyTransaction.__tablename__],
        ],
        checkfirst=True,
    )


def get_loyalty_plan(store_id: int) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty import service as loyalty_service

    with _managed_session() as db:
        _ensure_loyalty_tables(db)
        plan = loyalty_service.get_plan(db, store_id)
        return _orm_to_dict(plan) if plan else {
            "id": None, "vendor_id": store_id,
            "name": "Programa de puntos", "points_per_peso": 1.0,
            "min_redeem_points": 100, "redeem_rate": 0.01,
            "is_active": True, "description": "",
        }


def upsert_loyalty_plan(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty import service as loyalty_service

    with _managed_session(commit=True) as db:
        _ensure_loyalty_tables(db)
        plan = loyalty_service.upsert_plan(
            db,
            store_id,
            name=str(data.get("name") or "Programa de puntos"),
            points_per_peso=float(data.get("points_per_peso") or 1.0),
            min_redeem_points=int(data.get("min_redeem_points") or 100),
            redeem_rate=float(data.get("redeem_rate") or 0.01),
            is_active=bool(data.get("is_active", True)),
            description=str(data.get("description") or ""),
        )
        return _orm_to_dict(plan)


def list_loyalty_customers(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty import service as loyalty_service

    with _managed_session() as db:
        _ensure_loyalty_tables(db)
        return [_orm_to_dict(account) for account in loyalty_service.list_customers(db, store_id)]


def adjust_loyalty_points(store_id: int, email: str, points: int,
                          tx_type: str = "adjusted", notes: str = "",
                          reference: str = "", name: str = "") -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty import service as loyalty_service

    with _managed_session(commit=True) as db:
        _ensure_loyalty_tables(db)
        email = email.lower().strip()
        account = loyalty_service.adjust_points(
            db,
            store_id,
            email=email,
            points=points,
            tx_type=tx_type,
            notes=notes,
            reference=reference,
            name=name,
        )
        return _orm_to_dict(account)


def get_loyalty_history(store_id: int, email: str) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty import service as loyalty_service

    with _managed_session() as db:
        _ensure_loyalty_tables(db)
        email = email.lower().strip()
        return [_orm_to_dict(tx) for tx in loyalty_service.get_history(db, store_id, email)]


__all__ = [
    "ensure_store_tables",
    "list_employees", "create_employee", "update_employee", "delete_employee", "change_employee_password",
    "list_coupons", "create_coupon", "update_coupon", "delete_coupon",
    "validate_coupon", "redeem_coupon",
    "list_referrals", "create_referral", "update_referral", "delete_referral",
    "list_reservations", "create_reservation", "update_reservation", "delete_reservation",
    "list_layaways", "create_layaway", "update_layaway", "delete_layaway",
    "create_layaway_rich", "update_layaway_rich",
    "list_layaway_payments", "add_layaway_payment", "delete_layaway_payment",
    "set_layaway_status", "mark_overdue_layaways",
    "list_followers", "create_follower", "update_follower", "delete_follower",
    "list_videos", "create_video", "delete_video",
    "list_suppliers", "create_supplier", "update_supplier", "delete_supplier",
    "get_store_stats", "get_public_products",
    "get_loyalty_plan", "upsert_loyalty_plan",
    "list_loyalty_customers", "adjust_loyalty_points", "get_loyalty_history",
]
