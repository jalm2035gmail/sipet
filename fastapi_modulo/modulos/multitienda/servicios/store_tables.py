"""
Fachada de compatibilidad para el acceso a datos de Multitienda.

La implementación se distribuye por área para evitar que este módulo siga
creciendo como una capa paralela monolítica.
"""
from __future__ import annotations

from fastapi_modulo.modulos.multitienda.servicios.store_tables_catalog import (
    get_public_products,
    get_store_stats,
)
from fastapi_modulo.modulos.multitienda.servicios.store_tables_crud import (
    change_employee_password,
    create_coupon,
    create_employee,
    create_follower,
    create_referral,
    create_reservation,
    create_supplier,
    create_video,
    delete_coupon,
    delete_employee,
    delete_follower,
    delete_referral,
    delete_reservation,
    delete_supplier,
    delete_video,
    list_coupons,
    list_employees,
    list_followers,
    list_referrals,
    list_reservations,
    list_suppliers,
    list_videos,
    redeem_coupon,
    update_coupon,
    update_employee,
    update_follower,
    update_referral,
    update_reservation,
    update_supplier,
    validate_coupon,
)
from fastapi_modulo.modulos.multitienda.servicios.store_tables_layaways import (
    add_layaway_payment,
    create_layaway,
    create_layaway_rich,
    delete_layaway,
    delete_layaway_payment,
    list_layaway_payments,
    list_layaways,
    mark_overdue_layaways,
    set_layaway_status,
    update_layaway,
    update_layaway_rich,
)
from fastapi_modulo.modulos.multitienda.servicios.store_tables_loyalty import (
    adjust_loyalty_points,
    get_loyalty_history,
    get_loyalty_plan,
    list_loyalty_customers,
    upsert_loyalty_plan,
)
from fastapi_modulo.modulos.multitienda.servicios.store_tables_shared import ensure_store_tables

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
