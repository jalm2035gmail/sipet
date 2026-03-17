from __future__ import annotations

from enum import Enum


class TenantKeyStrategy(str, Enum):
    HOST = "host"
    SUBDOMAIN = "subdomain"
    HOST_ENV = "host_env"


class DatabaseEngine(str, Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class MappingSource(str, Enum):
    CONVENTION = "convention"
    FILE = "file"
    CENTRAL_DB = "central_db"
    REDIS_CACHE = "redis_cache"
