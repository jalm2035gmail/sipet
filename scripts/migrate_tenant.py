#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from fastapi_modulo.core.tenant_migrations import run_migrations_for_tenants


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecutar migraciones administrativas y por tenant en SIPET.")
    parser.add_argument("--tenant-key", default="", help="Tenant específico a migrar. Vacío = todos los activos.")
    args = parser.parse_args()

    results = run_migrations_for_tenants(tenant_key=args.tenant_key)
    print(
        json.dumps(
            [
                {
                    "tenant_key": item.tenant_key,
                    "target_scope": item.target_scope,
                    "migration_key": item.migration_key,
                    "status": item.status,
                    "detail": item.detail,
                }
                for item in results
            ],
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
