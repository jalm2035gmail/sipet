from __future__ import annotations

from fastapi_modulo.modulos.multitienda.servicios.store_tables_shared import managed_session, orm_to_dict


def _ensure_loyalty_tables(db) -> None:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty.models import LoyaltyAccount, LoyaltyPlan, LoyaltyTransaction
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
    with managed_session() as db:
        _ensure_loyalty_tables(db)
        plan = loyalty_service.get_plan(db, store_id)
        return orm_to_dict(plan) if plan else {
            "id": None,
            "vendor_id": store_id,
            "name": "Programa de puntos",
            "points_per_peso": 1.0,
            "min_redeem_points": 100,
            "redeem_rate": 0.01,
            "is_active": True,
            "description": "",
        }


def upsert_loyalty_plan(store_id: int, data: dict) -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty import service as loyalty_service
    with managed_session(commit=True) as db:
        _ensure_loyalty_tables(db)
        plan = loyalty_service.upsert_plan(
            db, store_id,
            name=str(data.get("name") or "Programa de puntos"),
            points_per_peso=float(data.get("points_per_peso") or 1.0),
            min_redeem_points=int(data.get("min_redeem_points") or 100),
            redeem_rate=float(data.get("redeem_rate") or 0.01),
            is_active=bool(data.get("is_active", True)),
            description=str(data.get("description") or ""),
        )
        return orm_to_dict(plan)


def list_loyalty_customers(store_id: int) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty import service as loyalty_service
    with managed_session() as db:
        _ensure_loyalty_tables(db)
        return [orm_to_dict(account) for account in loyalty_service.list_customers(db, store_id)]


def adjust_loyalty_points(store_id: int, email: str, points: int, tx_type: str = "adjusted", notes: str = "", reference: str = "", name: str = "") -> dict:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty import service as loyalty_service
    with managed_session(commit=True) as db:
        _ensure_loyalty_tables(db)
        account = loyalty_service.adjust_points(
            db, store_id,
            email=email.lower().strip(),
            points=points,
            tx_type=tx_type,
            notes=notes,
            reference=reference,
            name=name,
        )
        return orm_to_dict(account)


def get_loyalty_history(store_id: int, email: str) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty import service as loyalty_service
    with managed_session() as db:
        _ensure_loyalty_tables(db)
        return [orm_to_dict(tx) for tx in loyalty_service.get_history(db, store_id, email.lower().strip())]
