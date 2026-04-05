from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import inspect, text

from fastapi_modulo.modulos.multitienda.servicios.data_utils import (
    managed_session as managed_session,
    normalize_datetime_fields as normalize_datetime_fields,
    orm_list as orm_list,
    orm_to_dict as orm_to_dict,
    serialize_mapping as serialize_mapping,
)
from fastapi_modulo.modulos.multitienda.servicios.theme_utils import decode_theme as decode_theme


def rows(db, sql: str, params=None) -> list:
    result = db.execute(text(sql), params or {})
    keys = result.keys()
    return [serialize_mapping(dict(zip(keys, row))) for row in result.fetchall()]


def row(db, sql: str, params=None):
    result = db.execute(text(sql), params or {})
    keys = result.keys()
    current_row = result.fetchone()
    return serialize_mapping(dict(zip(keys, current_row))) if current_row else None


def apply_updates(instance, data: dict, col_map: dict) -> bool:
    updated = False
    seen = set()
    for src, field in col_map.items():
        if data.get(src) is not None and field not in seen:
            setattr(instance, field, data[src])
            seen.add(field)
            updated = True
    return updated


def build_update_params(data: dict, base_params: dict, col_map: dict) -> tuple[list[str], dict]:
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


@contextmanager
def optional_session(db=None, *, commit: bool = False):
    if db is not None:
        yield db
        return
    with managed_session(commit=commit) as own_db:
        yield own_db


_STORE_EMPLOYEE_ALLOWED_COLUMNS = {
    "full_name": "VARCHAR(150) DEFAULT ''",
    "job_title": "VARCHAR(120) DEFAULT ''",
    "phone": "VARCHAR(30) DEFAULT ''",
    "department": "VARCHAR(80) DEFAULT ''",
}


def _add_allowed_columns(connection, table_name: str, existing_columns: set[str], allowed_columns: dict[str, str]) -> None:
    for column_name, column_sql in allowed_columns.items():
        if column_name in existing_columns:
            continue
        if column_name not in allowed_columns:
            raise ValueError(f"Columna no permitida para {table_name}: {column_name}")
        connection.execute(
            text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {allowed_columns[column_name]}")
        )


def ensure_store_tables(bind=None) -> None:
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

    target_bind = bind or engine
    Base.metadata.create_all(
        bind=target_bind,
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
    inspector = inspect(target_bind)
    existing_columns = {
        column["name"]
        for column in inspector.get_columns("store_employees")
    }
    with target_bind.begin() as connection:
        _add_allowed_columns(
            connection,
            "store_employees",
            existing_columns,
            _STORE_EMPLOYEE_ALLOWED_COLUMNS,
        )
