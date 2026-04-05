"""
Migración Fase 2: Crear tablas de persistencia para dominios del núcleo Multitienda.

Tablas:
  store_employees · store_coupons · store_referrals · store_reservations
  store_layaways  · store_followers · store_videos  · store_suppliers
  store_whatsapp_config · store_ai_config

Uso:
  python -m fastapi_modulo.modulos.multitienda.marketplace.scripts.migrate_phase2
"""

from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base, engine

# Importar modelos existentes para que SQLAlchemy resuelva las foreign keys
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore, VendorDocument  # noqa: F401
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User  # noqa: F401
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product  # noqa: F401

# Modelos Fase 2
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons.models import StoreCoupon
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals.models import StoreReferral
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations.models import StoreReservation
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways.models import StoreLayaway
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers.models import StoreFollower
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos.models import StoreVideo
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers.models import StoreSupplier
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.whatsapp_config.models import StoreWhatsappConfig
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.ai_config.models import StoreAiConfig


PHASE2_TABLES = [
    StoreEmployee.__tablename__,
    StoreCoupon.__tablename__,
    StoreReferral.__tablename__,
    StoreReservation.__tablename__,
    StoreLayaway.__tablename__,
    StoreFollower.__tablename__,
    StoreVideo.__tablename__,
    StoreSupplier.__tablename__,
    StoreWhatsappConfig.__tablename__,
    StoreAiConfig.__tablename__,
]


def run():
    tables_to_create = [
        Base.metadata.tables[name]
        for name in PHASE2_TABLES
        if name in Base.metadata.tables
    ]
    Base.metadata.create_all(bind=engine, tables=tables_to_create, checkfirst=True)
    print("Fase 2 — Tablas creadas:")
    for name in PHASE2_TABLES:
        print(f"  ✓ {name}")


if __name__ == "__main__":
    run()
