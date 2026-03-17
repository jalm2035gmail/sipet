#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from fastapi_modulo.core.tenant_provisioning import create_tenant_with_default_session


def main() -> int:
    parser = argparse.ArgumentParser(description="Crear o actualizar un tenant en SIPET.")
    parser.add_argument("--host", required=True, help="Dominio principal del tenant.")
    parser.add_argument("--tenant-key", default="", help="Identificador lógico opcional del tenant.")
    parser.add_argument("--plan", default="base", help="Plan o perfil inicial del tenant.")
    args = parser.parse_args()

    result = create_tenant_with_default_session(
        primary_host=args.host,
        tenant_key=args.tenant_key,
        plan=args.plan,
    )
    print(
        json.dumps(
            {
                "tenant_key": result.tenant_key,
                "primary_host": result.primary_host,
                "db_name": result.db_name,
                "db_url": result.db_url,
                "created": result.created,
                "installed_apps": list(result.installed_apps),
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
