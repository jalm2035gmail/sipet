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
import json
from sqlalchemy import text
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import SessionLocal


def _coerce(v):
    if isinstance(v, datetime):
        return v.isoformat()
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
    with _managed_session() as db:
        return _rows(db,
            "SELECT * FROM store_employees WHERE vendor_id = :vid ORDER BY id",
            {"vid": store_id})


def create_employee(store_id: int, data: dict) -> dict:
    with _managed_session(commit=True) as db:
        row = _row(db,
            "INSERT INTO store_employees (vendor_id, user_id, role, position, is_active) "
            "VALUES (:vid, :uid, :role, :pos, :active) RETURNING *",
            {"vid": store_id,
             "uid": int(data.get("user_id") or 0),
             "role": str(data.get("role") or data.get("rol") or "seller"),
             "pos": str(data.get("position") or data.get("puesto") or ""),
             "active": bool(data.get("is_active", True))})
        return row or {}


def update_employee(store_id: int, employee_id: int, data: dict):
    with _managed_session(commit=True) as db:
        fields, params = [], {"vid": store_id, "eid": employee_id}
        col_map = {"role": "role", "rol": "role",
                   "position": "position", "puesto": "position",
                   "is_active": "is_active"}
        seen = set()
        for src, col in col_map.items():
            if data.get(src) is not None and col not in seen:
                key = f"p_{col}"
                fields.append(f"{col} = :{key}")
                params[key] = data[src]
                seen.add(col)
        if not fields:
            return None
        row = _row(db,
            "UPDATE store_employees SET " + ", ".join(fields) + ", updated_at = CURRENT_TIMESTAMP "
            "WHERE id = :eid AND vendor_id = :vid RETURNING *", params)
        return row


def delete_employee(store_id: int, employee_id: int) -> bool:
    with _managed_session(commit=True) as db:
        r = db.execute(text("DELETE FROM store_employees WHERE id = :eid AND vendor_id = :vid"),
                       {"eid": employee_id, "vid": store_id})
        return r.rowcount > 0


def change_employee_password(store_id: int, employee_id: int, password: str) -> bool:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import get_password_hash

    with _managed_session(commit=True) as db:
        employee = _row(
            db,
            "SELECT user_id FROM store_employees WHERE id = :eid AND vendor_id = :vid",
            {"eid": employee_id, "vid": store_id},
        )
        if not employee or not employee.get("user_id"):
            return False
        hashed_password = get_password_hash(password)
        result = db.execute(
            text(
                "UPDATE users SET hashed_password = :pwd WHERE id = :uid"
            ),
            {"pwd": hashed_password, "uid": int(employee["user_id"])},
        )
        return result.rowcount > 0


# ─── COUPONS ─────────────────────────────────────────────────────────────────

def list_coupons(store_id: int) -> list:
    with _managed_session() as db:
        return _rows(db,
            "SELECT * FROM store_coupons WHERE vendor_id = :vid ORDER BY created_at DESC",
            {"vid": store_id})


def create_coupon(store_id: int, data: dict) -> dict:
    with _managed_session(commit=True) as db:
        row = _row(db,
            "INSERT INTO store_coupons "
            "(vendor_id, code, discount_type, discount_value, min_order_amount, "
            "max_uses, uses_count, per_user_limit, valid_from, valid_until, is_active) "
            "VALUES (:vid, :code, :dtype, :dval, :minamt, :maxuses, 0, :perlimit, :vfrom, :vuntil, :active) "
            "RETURNING *",
            {"vid": store_id,
             "code": str(data.get("code") or data.get("codigo") or "").strip().upper(),
             "dtype": str(data.get("discount_type") or data.get("tipo") or "percent"),
             "dval": float(data.get("discount_value") or data.get("valor") or 0),
             "minamt": float(data.get("min_order_amount") or data.get("min_compra") or 0),
             "maxuses": int(data["max_uses"]) if data.get("max_uses") else None,
             "perlimit": int(data.get("per_user_limit") or 1),
             "vfrom": data.get("valid_from") or data.get("inicio"),
             "vuntil": data.get("valid_until") or data.get("expiracion"),
             "active": bool(data.get("is_active", True))})
        return row or {}


def update_coupon(store_id: int, coupon_id: int, data: dict):
    with _managed_session(commit=True) as db:
        fields, params = [], {"vid": store_id, "cid": coupon_id}
        col_map = {"code": "code", "codigo": "code",
                   "discount_type": "discount_type", "tipo": "discount_type",
                   "discount_value": "discount_value", "valor": "discount_value",
                   "min_order_amount": "min_order_amount", "min_compra": "min_order_amount",
                   "max_uses": "max_uses", "per_user_limit": "per_user_limit",
                   "valid_from": "valid_from", "inicio": "valid_from",
                   "valid_until": "valid_until", "expiracion": "valid_until",
                   "is_active": "is_active"}
        seen = set()
        for src, col in col_map.items():
            if data.get(src) is not None and col not in seen:
                key = f"p_{col}"
                fields.append(f"{col} = :{key}")
                params[key] = data[src]
                seen.add(col)
        if not fields:
            return None
        row = _row(db,
            "UPDATE store_coupons SET " + ", ".join(fields) +
            " WHERE id = :cid AND vendor_id = :vid RETURNING *", params)
        return row


def delete_coupon(store_id: int, coupon_id: int) -> bool:
    with _managed_session(commit=True) as db:
        r = db.execute(text("DELETE FROM store_coupons WHERE id = :cid AND vendor_id = :vid"),
                       {"cid": coupon_id, "vid": store_id})
        return r.rowcount > 0


# ─── REFERRALS ───────────────────────────────────────────────────────────────

def list_referrals(store_id: int) -> list:
    with _managed_session() as db:
        return _rows(db,
            "SELECT * FROM store_referrals WHERE vendor_id = :vid ORDER BY created_at DESC",
            {"vid": store_id})


def create_referral(store_id: int, data: dict) -> dict:
    with _managed_session(commit=True) as db:
        row = _row(db,
            "INSERT INTO store_referrals "
            "(vendor_id, referrer_user_id, referral_code, reward_type, reward_value, status) "
            "VALUES (:vid, :ruid, :code, :rtype, :rval, 'pending') RETURNING *",
            {"vid": store_id,
             "ruid": int(data.get("referrer_user_id") or 0),
             "code": str(data.get("referral_code") or data.get("codigo") or "").strip().upper(),
             "rtype": data.get("reward_type"),
             "rval": float(data["reward_value"]) if data.get("reward_value") else None})
        return row or {}


def update_referral(store_id: int, referral_id: int, data: dict):
    with _managed_session(commit=True) as db:
        fields, params = [], {"vid": store_id, "rid": referral_id}
        col_map = {"status": "status", "estado": "status",
                   "referred_user_id": "referred_user_id",
                   "reward_type": "reward_type", "reward_value": "reward_value",
                   "reward_given_at": "reward_given_at"}
        seen = set()
        for src, col in col_map.items():
            if data.get(src) is not None and col not in seen:
                key = f"p_{col}"
                fields.append(f"{col} = :{key}")
                params[key] = data[src]
                seen.add(col)
        if not fields:
            return None
        row = _row(db,
            "UPDATE store_referrals SET " + ", ".join(fields) +
            " WHERE id = :rid AND vendor_id = :vid RETURNING *", params)
        return row


def delete_referral(store_id: int, referral_id: int) -> bool:
    with _managed_session(commit=True) as db:
        r = db.execute(text("DELETE FROM store_referrals WHERE id = :rid AND vendor_id = :vid"),
                       {"rid": referral_id, "vid": store_id})
        return r.rowcount > 0


# ─── RESERVATIONS ────────────────────────────────────────────────────────────

def list_reservations(store_id: int) -> list:
    with _managed_session() as db:
        return _rows(db,
            "SELECT * FROM store_reservations WHERE vendor_id = :vid ORDER BY reservation_date DESC",
            {"vid": store_id})


def create_reservation(store_id: int, data: dict) -> dict:
    with _managed_session(commit=True) as db:
        row = _row(db,
            "INSERT INTO store_reservations "
            "(vendor_id, customer_user_id, product_id, reservation_date, time_slot, duration_minutes, notes, status) "
            "VALUES (:vid, :cuid, :pid, :rdate, :slot, :dur, :notes, 'pending') RETURNING *",
            {"vid": store_id,
             "cuid": int(data.get("customer_user_id") or 0),
             "pid": int(data["product_id"]) if data.get("product_id") else None,
             "rdate": data.get("reservation_date") or data.get("fecha"),
             "slot": data.get("time_slot") or data.get("hora"),
             "dur": int(data.get("duration_minutes") or 60),
             "notes": str(data.get("notes") or data.get("notas") or "")})
        return row or {}


def update_reservation(store_id: int, reservation_id: int, data: dict):
    with _managed_session(commit=True) as db:
        fields, params = [], {"vid": store_id, "rid": reservation_id}
        col_map = {"status": "status", "estado": "status",
                   "reservation_date": "reservation_date", "fecha": "reservation_date",
                   "time_slot": "time_slot", "hora": "time_slot",
                   "duration_minutes": "duration_minutes",
                   "notes": "notes", "notas": "notes",
                   "confirmed_at": "confirmed_at", "cancelled_at": "cancelled_at"}
        seen = set()
        for src, col in col_map.items():
            if data.get(src) is not None and col not in seen:
                key = f"p_{col}"
                fields.append(f"{col} = :{key}")
                params[key] = data[src]
                seen.add(col)
        if not fields:
            return None
        row = _row(db,
            "UPDATE store_reservations SET " + ", ".join(fields) + ", updated_at = CURRENT_TIMESTAMP "
            "WHERE id = :rid AND vendor_id = :vid RETURNING *", params)
        return row


def delete_reservation(store_id: int, reservation_id: int) -> bool:
    with _managed_session(commit=True) as db:
        r = db.execute(text("DELETE FROM store_reservations WHERE id = :rid AND vendor_id = :vid"),
                       {"rid": reservation_id, "vid": store_id})
        return r.rowcount > 0


# ─── LAYAWAYS ────────────────────────────────────────────────────────────────

def list_layaways(store_id: int) -> list:
    with _managed_session() as db:
        return _rows(db,
            "SELECT * FROM store_layaways WHERE vendor_id = :vid ORDER BY created_at DESC",
            {"vid": store_id})


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
        fields, params = [], {"vid": store_id, "lid": layaway_id}
        col_map = {"status": "status", "estado": "status",
                   "balance_due": "balance_due", "saldo_pendiente": "balance_due",
                   "due_date": "due_date", "fecha_limite": "due_date",
                   "notes": "notes", "notas": "notes"}
        seen = set()
        for src, col in col_map.items():
            if data.get(src) is not None and col not in seen:
                key = f"p_{col}"
                fields.append(f"{col} = :{key}")
                params[key] = data[src]
                seen.add(col)
        if not fields:
            return None
        row = _row(db,
            "UPDATE store_layaways SET " + ", ".join(fields) + ", updated_at = CURRENT_TIMESTAMP "
            "WHERE id = :lid AND vendor_id = :vid RETURNING *", params)
        return row


def delete_layaway(store_id: int, layaway_id: int) -> bool:
    with _managed_session(commit=True) as db:
        r = db.execute(text("DELETE FROM store_layaways WHERE id = :lid AND vendor_id = :vid"),
                       {"lid": layaway_id, "vid": store_id})
        return r.rowcount > 0


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
        fields, params, seen = [], {"vid": store_id, "lid": layaway_id}, set()
        for src, col in col_map.items():
            if data.get(src) is not None and col not in seen:
                key = f"p_{col}"
                fields.append(f"{col} = :{key}")
                params[key] = data[src]
                seen.add(col)
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

        # recalculate balance_due
        total_paid_row = _row(db,
            "SELECT COALESCE(SUM(amount),0) AS s FROM store_layaway_payments WHERE layaway_id = :lid",
            {"lid": layaway_id})
        total_paid = float((total_paid_row or {}).get("s", 0)) + float(ap.get("downpayment") or 0)
        total_amt  = float(ap.get("total_amount") or 0)
        new_balance = max(0.0, round(total_amt - total_paid, 2))
        new_status  = ap.get("status") or "active"
        if new_balance <= 0:
            new_status = "completado"
        _row(db,
            "UPDATE store_layaways SET balance_due = :bal, status = :st, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = :lid",
            {"bal": new_balance, "st": new_status, "lid": layaway_id})
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

        # recalculate balance_due
        total_paid_row = _row(db,
            "SELECT COALESCE(SUM(amount),0) AS s FROM store_layaway_payments WHERE layaway_id = :lid",
            {"lid": layaway_id})
        total_paid = float((total_paid_row or {}).get("s", 0)) + float(ap.get("downpayment") or 0)
        total_amt  = float(ap.get("total_amount") or 0)
        new_balance = max(0.0, round(total_amt - total_paid, 2))
        new_status  = "completado" if new_balance <= 0 else "active"
        _row(db,
            "UPDATE store_layaways SET balance_due = :bal, status = :st, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = :lid",
            {"bal": new_balance, "st": new_status, "lid": layaway_id})
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
    with _managed_session() as db:
        return _rows(db,
            "SELECT * FROM store_followers WHERE vendor_id = :vid ORDER BY created_at DESC",
            {"vid": store_id})


def create_follower(store_id: int, data: dict) -> dict:
    with _managed_session(commit=True) as db:
        row = _row(db,
            "INSERT INTO store_followers (vendor_id, user_id) VALUES (:vid, :uid) RETURNING *",
            {"vid": store_id, "uid": int(data.get("user_id") or 0)})
        return row or {}


def update_follower(store_id: int, follower_id: int, data: dict):
    return None  # no hay campos actualizables en store_followers


def delete_follower(store_id: int, follower_id: int) -> bool:
    with _managed_session(commit=True) as db:
        r = db.execute(text("DELETE FROM store_followers WHERE id = :fid AND vendor_id = :vid"),
                       {"fid": follower_id, "vid": store_id})
        return r.rowcount > 0


# ─── VIDEOS ──────────────────────────────────────────────────────────────────

def list_videos(store_id: int) -> list:
    with _managed_session() as db:
        return _rows(db,
            'SELECT * FROM store_videos WHERE vendor_id = :vid ORDER BY "order" ASC, created_at DESC',
            {"vid": store_id})


def create_video(store_id: int, data: dict) -> dict:
    with _managed_session(commit=True) as db:
        row = _row(db,
            'INSERT INTO store_videos (vendor_id, product_id, title, url, thumbnail, description, is_active, "order") '
            "VALUES (:vid, :pid, :title, :url, :thumb, :desc, :active, :ord) RETURNING *",
            {"vid": store_id,
             "pid": int(data["product_id"]) if data.get("product_id") else None,
             "title": str(data.get("title") or data.get("nombre") or ""),
             "url": str(data.get("url") or ""),
             "thumb": data.get("thumbnail"),
             "desc": str(data.get("description") or data.get("notas") or ""),
             "active": bool(data.get("is_active", True)),
             "ord": int(data.get("order") or 0)})
        return row or {}


def delete_video(store_id: int, video_id: int) -> bool:
    with _managed_session(commit=True) as db:
        r = db.execute(text("DELETE FROM store_videos WHERE id = :vid2 AND vendor_id = :vid"),
                       {"vid2": video_id, "vid": store_id})
        return r.rowcount > 0


# ─── SUPPLIERS ───────────────────────────────────────────────────────────────

def list_suppliers(store_id: int, db=None) -> list:
    with _optional_session(db) as db:
        return _rows(db,
            "SELECT * FROM store_suppliers WHERE vendor_id = :vid ORDER BY name",
            {"vid": store_id})


def create_supplier(store_id: int, data: dict, db=None) -> dict:
    with _optional_session(db, commit=True) as db:
        row = _row(db,
            "INSERT INTO store_suppliers "
            "(vendor_id, name, contact_name, email, phone, address, country, website, notes, is_active) "
            "VALUES (:vid, :name, :cname, :email, :phone, :addr, :country, :web, :notes, :active) RETURNING *",
            {"vid": store_id,
             "name": str(data.get("name") or data.get("nombre") or "").strip(),
             "cname": str(data.get("contact_name") or ""),
             "email": str(data.get("email") or ""),
             "phone": str(data.get("phone") or data.get("telefono") or ""),
             "addr": str(data.get("address") or data.get("direccion") or ""),
             "country": str(data.get("country") or ""),
             "web": data.get("website"),
             "notes": str(data.get("notes") or data.get("notas") or ""),
             "active": bool(data.get("is_active", True))})
        return row or {}


def update_supplier(store_id: int, supplier_id: int, data: dict, db=None):
    with _optional_session(db, commit=True) as db:
        fields, params = [], {"vid": store_id, "sid": supplier_id}
        col_map = {"name": "name", "nombre": "name",
                   "contact_name": "contact_name",
                   "email": "email",
                   "phone": "phone", "telefono": "phone",
                   "address": "address", "direccion": "address",
                   "country": "country", "website": "website",
                   "notes": "notes", "notas": "notes",
                   "is_active": "is_active"}
        seen = set()
        for src, col in col_map.items():
            if data.get(src) is not None and col not in seen:
                key = f"p_{col}"
                fields.append(f"{col} = :{key}")
                params[key] = data[src]
                seen.add(col)
        if not fields:
            return None
        row = _row(db,
            "UPDATE store_suppliers SET " + ", ".join(fields) + ", updated_at = CURRENT_TIMESTAMP "
            "WHERE id = :sid AND vendor_id = :vid RETURNING *", params)
        return row


def delete_supplier(store_id: int, supplier_id: int, db=None) -> bool:
    with _optional_session(db, commit=True) as db:
        r = db.execute(text("DELETE FROM store_suppliers WHERE id = :sid AND vendor_id = :vid"),
                       {"sid": supplier_id, "vid": store_id})
        return r.rowcount > 0


# ─── STATS ───────────────────────────────────────────────────────────────────

def get_store_stats(store_id: int) -> dict:
    """Retorna conteos reales y datos de analítica de los últimos 7 días."""
    from datetime import date, timedelta
    with _managed_session() as db:
        def _safe_count(sql, params):
            try:
                row = _row(db, sql, params)
                return int(row["cnt"]) if row else 0
            except Exception:
                return 0

        products = _safe_count("SELECT COUNT(*) AS cnt FROM products WHERE vendor_id = :vid", {"vid": store_id})
        employees = _safe_count("SELECT COUNT(*) AS cnt FROM store_employees WHERE vendor_id = :vid", {"vid": store_id})
        coupons = _safe_count("SELECT COUNT(*) AS cnt FROM store_coupons WHERE vendor_id = :vid AND is_active = 1", {"vid": store_id})
        orders = _safe_count("SELECT COUNT(*) AS cnt FROM orders WHERE vendor_id = :vid", {"vid": store_id})

        today = date.today()
        chart_labels, chart_values = [], []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            chart_labels.append(d.strftime("%d/%m"))
            try:
                row = _row(db,
                    "SELECT COALESCE(store_views, 0) AS views FROM vendor_analytics "
                    "WHERE vendor_id = :vid AND date = :d LIMIT 1",
                    {"vid": store_id, "d": d.isoformat()})
                chart_values.append(int(row["views"]) if row else 0)
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
    try:
        with _managed_session() as db:
                theme_sql = (
                    "SELECT id, store_name, store_slug, store_theme "
                    "FROM vendors "
                    "WHERE is_active = 1"
                )
                theme_params: dict = {}
                if store_id is not None:
                    theme_sql += " AND id = :vid"
                    theme_params["vid"] = store_id
                elif featured_only:
                    theme_sql += " AND is_featured = 1"
                theme_sql += " ORDER BY id DESC"
                vendor_rows = _rows(db, theme_sql, theme_params)
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
                    placeholders = ",".join(str(i) for i in ids_sin_imagen)
                    img_rows = _rows(
                        db,
                        f"SELECT product_id, image FROM product_images WHERE is_primary = 1 AND product_id IN ({placeholders})",
                        {},
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
    from datetime import datetime as _dt
    with _managed_session() as db:
        now = _dt.utcnow().isoformat()
        coupon = _row(db,
            "SELECT * FROM store_coupons WHERE vendor_id=:vid AND code=:code AND is_active=1",
            {"vid": store_id, "code": code.strip().upper()})
        if not coupon:
            return {"valid": False, "error": "Cupón inválido o inactivo."}
        if coupon.get("valid_from") and str(coupon["valid_from"]) > now:
            return {"valid": False, "error": "El cupón aún no es válido."}
        if coupon.get("valid_until") and str(coupon["valid_until"]) < now:
            return {"valid": False, "error": "El cupón ha expirado."}
        max_uses = coupon.get("max_uses")
        if max_uses is not None and int(coupon.get("uses_count", 0)) >= int(max_uses):
            return {"valid": False, "error": "El cupón ha alcanzado su límite de usos."}
        min_order = float(coupon.get("min_order_amount") or 0)
        if cart_total < min_order:
            return {"valid": False, "error": f"Compra mínima requerida: ${min_order:.2f}."}
        dtype = str(coupon.get("discount_type") or "percent")
        dval = float(coupon.get("discount_value") or 0)
        if dtype in ("percent", "porcentaje", "percentage"):
            discount = round(cart_total * dval / 100, 2)
        elif dtype in ("fixed", "monto"):
            discount = round(min(dval, cart_total), 2)
        else:
            discount = 0.0
        return {
            "valid":           True,
            "coupon_id":       coupon["id"],
            "code":            coupon["code"],
            "discount_type":   dtype,
            "discount_value":  dval,
            "discount_amount": discount,
            "free_shipping":   dtype in ("free_shipping", "envio"),
        }


def redeem_coupon(store_id: int, coupon_id: int) -> bool:
    with _managed_session(commit=True) as db:
        r = db.execute(text(
            "UPDATE store_coupons SET uses_count = uses_count + 1 WHERE id=:cid AND vendor_id=:vid"),
            {"cid": coupon_id, "vid": store_id})
        return r.rowcount > 0


# ─── LOYALTY ─────────────────────────────────────────────────────────────────

def _ensure_loyalty_tables(db) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS loyalty_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL UNIQUE,
            name TEXT NOT NULL DEFAULT 'Programa de puntos',
            points_per_peso REAL NOT NULL DEFAULT 1.0,
            min_redeem_points INTEGER NOT NULL DEFAULT 100,
            redeem_rate REAL NOT NULL DEFAULT 0.01,
            is_active INTEGER NOT NULL DEFAULT 1,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS loyalty_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            customer_email TEXT NOT NULL,
            customer_name TEXT DEFAULT '',
            current_points INTEGER NOT NULL DEFAULT 0,
            lifetime_points INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(vendor_id, customer_email)
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS loyalty_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            points INTEGER NOT NULL,
            transaction_type TEXT NOT NULL DEFAULT 'earned',
            reference TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """))
    db.commit()


def get_loyalty_plan(store_id: int) -> dict:
    with _managed_session() as db:
        _ensure_loyalty_tables(db)
        row = _row(db, "SELECT * FROM loyalty_plans WHERE vendor_id=:vid", {"vid": store_id})
        return row or {
            "id": None, "vendor_id": store_id,
            "name": "Programa de puntos", "points_per_peso": 1.0,
            "min_redeem_points": 100, "redeem_rate": 0.01,
            "is_active": True, "description": "",
        }


def upsert_loyalty_plan(store_id: int, data: dict) -> dict:
    with _managed_session(commit=True) as db:
        _ensure_loyalty_tables(db)
        existing = _row(db, "SELECT id FROM loyalty_plans WHERE vendor_id=:vid", {"vid": store_id})
        params = {
            "vid":  store_id,
            "name": str(data.get("name") or "Programa de puntos"),
            "ppp":  float(data.get("points_per_peso") or 1.0),
            "mrp":  int(data.get("min_redeem_points") or 100),
            "rr":   float(data.get("redeem_rate") or 0.01),
            "act":  1 if data.get("is_active", True) else 0,
            "desc": str(data.get("description") or ""),
        }
        if existing:
            row = _row(db,
                "UPDATE loyalty_plans SET name=:name, points_per_peso=:ppp, "
                "min_redeem_points=:mrp, redeem_rate=:rr, is_active=:act, "
                "description=:desc, updated_at=datetime('now') "
                "WHERE vendor_id=:vid RETURNING *", params)
        else:
            row = _row(db,
                "INSERT INTO loyalty_plans "
                "(vendor_id,name,points_per_peso,min_redeem_points,redeem_rate,is_active,description) "
                "VALUES (:vid,:name,:ppp,:mrp,:rr,:act,:desc) RETURNING *", params)
        return row or {}


def list_loyalty_customers(store_id: int) -> list:
    with _managed_session() as db:
        _ensure_loyalty_tables(db)
        return _rows(db,
            "SELECT * FROM loyalty_accounts WHERE vendor_id=:vid ORDER BY current_points DESC",
            {"vid": store_id})


def adjust_loyalty_points(store_id: int, email: str, points: int,
                          tx_type: str = "adjusted", notes: str = "",
                          reference: str = "", name: str = "") -> dict:
    with _managed_session(commit=True) as db:
        _ensure_loyalty_tables(db)
        email = email.lower().strip()
        existing = _row(db,
            "SELECT * FROM loyalty_accounts WHERE vendor_id=:vid AND customer_email=:e",
            {"vid": store_id, "e": email})
        if existing:
            new_pts = max(0, int(existing["current_points"]) + points)
            new_life = int(existing["lifetime_points"]) + max(0, points)
            account = _row(db,
                "UPDATE loyalty_accounts SET current_points=:cp, lifetime_points=:lp, "
                "updated_at=datetime('now') WHERE vendor_id=:vid AND customer_email=:e RETURNING *",
                {"cp": new_pts, "lp": new_life, "vid": store_id, "e": email})
        else:
            init = max(0, points)
            account = _row(db,
                "INSERT INTO loyalty_accounts "
                "(vendor_id,customer_email,customer_name,current_points,lifetime_points) "
                "VALUES (:vid,:e,:name,:cp,:lp) RETURNING *",
                {"vid": store_id, "e": email, "name": name or "", "cp": init, "lp": init})
        db.execute(text(
            "INSERT INTO loyalty_transactions "
            "(account_id,points,transaction_type,reference,notes) "
            "VALUES (:aid,:pts,:tt,:ref,:notes)"),
            {"aid": account["id"], "pts": points, "tt": tx_type,
             "ref": reference, "notes": notes})
        return account or {}


def get_loyalty_history(store_id: int, email: str) -> list:
    with _managed_session() as db:
        _ensure_loyalty_tables(db)
        email = email.lower().strip()
        acc = _row(db,
            "SELECT id FROM loyalty_accounts WHERE vendor_id=:vid AND customer_email=:e",
            {"vid": store_id, "e": email})
        if not acc:
            return []
        return _rows(db,
            "SELECT * FROM loyalty_transactions WHERE account_id=:aid ORDER BY id DESC LIMIT 100",
            {"aid": acc["id"]})


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
