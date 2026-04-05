from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.servicios.data_utils import serialize_mapping


def _rows(db: Session, sql: str, params=None) -> list:
    result = db.execute(text(sql), params or {})
    keys = result.keys()
    return [serialize_mapping(dict(zip(keys, row))) for row in result.fetchall()]


def _row(db: Session, sql: str, params=None):
    result = db.execute(text(sql), params or {})
    keys = result.keys()
    row = result.fetchone()
    return serialize_mapping(dict(zip(keys, row))) if row else None


def _delete_by_vendor(db: Session, table: str, id_column: str, record_id: int, vendor_id: int) -> bool:
    result = db.execute(
        text(f"DELETE FROM {table} WHERE {id_column} = :rid AND vendor_id = :vid"),
        {"rid": record_id, "vid": vendor_id},
    )
    return result.rowcount > 0


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


def ensure_extras(db: Session) -> None:
    extra_cols = [
        ("folio", "TEXT DEFAULT ''"),
        ("customer_name", "TEXT DEFAULT ''"),
        ("customer_phone", "TEXT DEFAULT ''"),
        ("customer_email", "TEXT DEFAULT ''"),
        ("product_name", "TEXT DEFAULT ''"),
        ("product_sku", "TEXT DEFAULT ''"),
        ("modalidad", "TEXT DEFAULT 'libre'"),
        ("cuotas", "INTEGER DEFAULT 0"),
        ("periodicidad", "TEXT DEFAULT 'mensual'"),
        ("start_date", "TEXT DEFAULT ''"),
    ]
    for col, typ in extra_cols:
        try:
            db.execute(text(f"ALTER TABLE store_layaways ADD COLUMN {col} {typ}"))
            db.commit()
        except Exception:
            pass

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


def list_by_vendor(db: Session, vendor_id: int) -> list:
    return _rows(
        db,
        "SELECT * FROM store_layaways WHERE vendor_id = :vid ORDER BY created_at DESC",
        {"vid": vendor_id},
    )


def create_basic(db: Session, vendor_id: int, data: dict) -> dict:
    total = float(data.get("total_amount") or data.get("precio_total") or 0)
    down = float(data.get("downpayment") or data.get("enganche") or 0)
    return _row(
        db,
        "INSERT INTO store_layaways "
        "(vendor_id, customer_user_id, product_id, total_amount, downpayment, balance_due, due_date, notes, status) "
        "VALUES (:vid, :cuid, :pid, :total, :down, :balance, :due, :notes, 'active') RETURNING *",
        {
            "vid": vendor_id,
            "cuid": int(data.get("customer_user_id") or 0),
            "pid": int(data["product_id"]) if data.get("product_id") else 0,
            "total": total,
            "down": down,
            "balance": round(total - down, 2),
            "due": data.get("due_date") or data.get("fecha_limite"),
            "notes": str(data.get("notes") or data.get("notas") or ""),
        },
    ) or {}


def update_basic(db: Session, vendor_id: int, layaway_id: int, data: dict):
    col_map = {
        "status": "status", "estado": "status",
        "balance_due": "balance_due", "saldo_pendiente": "balance_due",
        "due_date": "due_date", "fecha_limite": "due_date",
        "notes": "notes", "notas": "notes",
    }
    fields, params = _build_update_params(data, {"vid": vendor_id, "lid": layaway_id}, col_map)
    if not fields:
        return None
    return _row(
        db,
        "UPDATE store_layaways SET " + ", ".join(fields) + ", updated_at = CURRENT_TIMESTAMP "
        "WHERE id = :lid AND vendor_id = :vid RETURNING *",
        params,
    )


def delete_basic(db: Session, vendor_id: int, layaway_id: int) -> bool:
    return _delete_by_vendor(db, "store_layaways", "id", layaway_id, vendor_id)


def _recalculate_balance(db: Session, layaway_id: int, layaway_row: dict, *, paid_status: str = "completado") -> dict | None:
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


def create_rich(db: Session, vendor_id: int, data: dict) -> dict:
    ensure_extras(db)
    total = float(data.get("total_amount") or data.get("precio") or 0)
    down = float(data.get("downpayment") or data.get("enganche") or 0)
    cnt = _row(db, "SELECT COUNT(*) AS n FROM store_layaways WHERE vendor_id = :vid", {"vid": vendor_id})
    sequence = int((cnt or {}).get("n", 0)) + 1
    folio = data.get("folio") or f"AP-{date.today().year}-{sequence:04d}"
    return _row(
        db,
        "INSERT INTO store_layaways "
        "(vendor_id, customer_user_id, product_id, total_amount, downpayment, balance_due, due_date, notes, status,"
        " folio, customer_name, customer_phone, customer_email, product_name, product_sku,"
        " modalidad, cuotas, periodicidad, start_date) "
        "VALUES (:vid, 0, 0, :total, :down, :balance, :due, :notes, 'active',"
        " :folio, :cname, :cphone, :cemail, :pname, :psku,"
        " :modalidad, :cuotas, :periodicidad, :sdate) RETURNING *",
        {
            "vid": vendor_id,
            "total": total,
            "down": down,
            "balance": round(total - down, 2),
            "due": data.get("due_date") or data.get("fechaLimite") or "",
            "notes": data.get("notes") or data.get("notas") or "",
            "folio": folio,
            "cname": data.get("customer_name") or data.get("nombre") or "",
            "cphone": data.get("customer_phone") or data.get("telefono") or "",
            "cemail": data.get("customer_email") or data.get("email") or "",
            "pname": data.get("product_name") or data.get("producto") or "",
            "psku": data.get("product_sku") or data.get("sku") or "",
            "modalidad": data.get("modalidad") or "libre",
            "cuotas": int(data.get("cuotas") or 0),
            "periodicidad": data.get("periodicidad") or "mensual",
            "sdate": data.get("start_date") or data.get("fechaInicio") or "",
        },
    ) or {}


def update_rich(db: Session, vendor_id: int, layaway_id: int, data: dict) -> dict | None:
    ensure_extras(db)
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
    fields, params = _build_update_params(data, {"vid": vendor_id, "lid": layaway_id}, col_map)
    if not fields:
        return None
    return _row(
        db,
        "UPDATE store_layaways SET " + ", ".join(fields) + ", updated_at = CURRENT_TIMESTAMP "
        "WHERE id = :lid AND vendor_id = :vid RETURNING *",
        params,
    )


def list_payments(db: Session, vendor_id: int, layaway_id: int) -> list:
    ensure_extras(db)
    layaway = _row(
        db,
        "SELECT id FROM store_layaways WHERE id = :lid AND vendor_id = :vid",
        {"lid": layaway_id, "vid": vendor_id},
    )
    if not layaway:
        return []
    return _rows(
        db,
        "SELECT * FROM store_layaway_payments WHERE layaway_id = :lid ORDER BY paid_at ASC, id ASC",
        {"lid": layaway_id},
    )


def add_payment(db: Session, vendor_id: int, layaway_id: int, data: dict) -> dict:
    ensure_extras(db)
    layaway = _row(
        db,
        "SELECT * FROM store_layaways WHERE id = :lid AND vendor_id = :vid",
        {"lid": layaway_id, "vid": vendor_id},
    )
    if not layaway:
        return {"error": "Apartado no encontrado"}
    amount = float(data.get("amount") or data.get("monto") or 0)
    if amount <= 0:
        return {"error": "Monto inválido"}
    payment = _row(
        db,
        "INSERT INTO store_layaway_payments (layaway_id, amount, paid_at, method, reference) "
        "VALUES (:lid, :amt, :paid_at, :method, :ref) RETURNING *",
        {
            "lid": layaway_id,
            "amt": amount,
            "paid_at": data.get("paid_at") or data.get("fecha") or "",
            "method": data.get("method") or data.get("metodo") or "efectivo",
            "ref": data.get("reference") or data.get("referencia") or "",
        },
    )
    _recalculate_balance(db, layaway_id, layaway)
    return payment or {}


def delete_payment(db: Session, vendor_id: int, layaway_id: int, payment_id: int) -> bool:
    ensure_extras(db)
    layaway = _row(
        db,
        "SELECT * FROM store_layaways WHERE id = :lid AND vendor_id = :vid",
        {"lid": layaway_id, "vid": vendor_id},
    )
    if not layaway:
        return False
    result = db.execute(
        text("DELETE FROM store_layaway_payments WHERE id = :pid AND layaway_id = :lid"),
        {"pid": payment_id, "lid": layaway_id},
    )
    _recalculate_balance(db, layaway_id, layaway)
    return result.rowcount > 0


def set_status(db: Session, vendor_id: int, layaway_id: int, new_status: str) -> dict | None:
    allowed = {"cancelado", "active", "entregado"}
    if new_status not in allowed:
        return None
    ensure_extras(db)
    return _row(
        db,
        "UPDATE store_layaways SET status = :st, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = :lid AND vendor_id = :vid RETURNING *",
        {"st": new_status, "lid": layaway_id, "vid": vendor_id},
    )


def mark_overdue(db: Session, vendor_id: int) -> int:
    ensure_extras(db)
    result = db.execute(text(
        "UPDATE store_layaways SET status = 'vencido', updated_at = CURRENT_TIMESTAMP "
        "WHERE vendor_id = :vid AND status = 'active' AND due_date != '' AND due_date < date('now')"
    ), {"vid": vendor_id})
    return result.rowcount
