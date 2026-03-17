from __future__ import annotations

import os
import re
from dataclasses import dataclass

from fastapi_modulo.core.tenant_types import DatabaseEngine, MappingSource, TenantKeyStrategy

DATABASE_NAME_MAX_LENGTH = 63


def normalize_tenant_slug(value: str) -> str:
    raw = str(value or "").strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    normalized = re.sub(r"_+", "_", normalized)
    return normalized or "default"


def build_database_name(tenant_key: str, environment: str) -> str:
    tenant_slug = normalize_tenant_slug(tenant_key)
    env_slug = normalize_tenant_slug(environment)
    candidate = f"{tenant_slug}_{env_slug}".strip("_")
    return candidate[:DATABASE_NAME_MAX_LENGTH]


@dataclass(frozen=True)
class TenantArchitectureSettings:
    web_framework: str
    orm: str
    tenant_key_strategy: TenantKeyStrategy
    production_engine: DatabaseEngine
    development_engine: DatabaseEngine
    preferred_cache: str
    production_mapping_source: MappingSource
    development_mapping_source: MappingSource
    central_admin_database_enabled: bool

    @property
    def environment(self) -> str:
        return (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()

    @property
    def active_database_engine(self) -> DatabaseEngine:
        if self.environment in {"production", "prod", "staging"}:
            return self.production_engine
        return self.development_engine


ARCHITECTURE_SETTINGS = TenantArchitectureSettings(
    web_framework="fastapi",
    orm="sqlalchemy",
    tenant_key_strategy=TenantKeyStrategy.HOST,
    production_engine=DatabaseEngine.POSTGRESQL,
    development_engine=DatabaseEngine.SQLITE,
    preferred_cache="redis",
    production_mapping_source=MappingSource.CENTRAL_DB,
    development_mapping_source=MappingSource.CONVENTION,
    central_admin_database_enabled=True,
)
