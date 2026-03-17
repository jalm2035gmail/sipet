from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from fastapi_modulo.core.db import MAIN


class AppRegistryState(MAIN):
    __tablename__ = "app_registry_state"

    id = Column(Integer, primary_key=True)
    module_key = Column(String(120), nullable=False, index=True)
    tenant_id = Column(String(120), nullable=True, index=True)
    enabled = Column(Boolean, nullable=False, default=False)
    installed_version = Column(String(64), nullable=True)
    uploaded_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(255), nullable=True)


class AppRegistryAudit(MAIN):
    __tablename__ = "app_registry_audit"

    id = Column(Integer, primary_key=True)
    module_key = Column(String(120), nullable=False, index=True)
    action = Column(String(80), nullable=False, index=True)
    payload_json = Column(Text, nullable=False, default="{}")
    result = Column(String(80), nullable=False, default="pending", index=True)
    user_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    ip = Column(String(64), nullable=True)


class AppProtocolAudit(MAIN):
    __tablename__ = "app_protocol_audit"

    id = Column(Integer, primary_key=True)
    module_key = Column(String(120), nullable=False, index=True)
    has_init = Column(Boolean, nullable=False, default=False)
    has_manifest = Column(Boolean, nullable=False, default=False)
    missing_json = Column(Text, nullable=False, default="[]")
    ok = Column(Boolean, nullable=False, default=False, index=True)
    scanned_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class AppPackageUpload(MAIN):
    __tablename__ = "app_package_upload"

    id = Column(Integer, primary_key=True)
    module_key = Column(String(120), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    checksum = Column(String(128), nullable=False, index=True)
    file_size = Column(Integer, nullable=False, default=0)
    uploaded_by = Column(String(255), nullable=True, index=True)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    applied = Column(Boolean, nullable=False, default=False, index=True)


__all__ = [
    "AppPackageUpload",
    "AppProtocolAudit",
    "AppRegistryAudit",
    "AppRegistryState",
]
