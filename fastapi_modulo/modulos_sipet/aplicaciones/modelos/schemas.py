from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ModuleToggleSchema(BaseModel):
    enabled: bool


class ProtocolSyncSchema(BaseModel):
    mode: str = "repair_missing_only"
    overwrite_manifest: bool = False
    overwrite_init: bool = False
    challenge_token: str = ""


class ModuleUploadResponse(BaseModel):
    module_key: str
    target_root: str
    dry_run: bool = False
    status: str = "success"
    task_id: str = ""
    task_name: str = ""
    checksum: str
    file_size: int
    content_type: str = ""
    updated_files: int = 0
    total_files: int = 0
    total_uncompressed_size: int = 0
    new_files: int = 0
    changed_files: int = 0
    unchanged_files: int = 0
    preview_files: list[dict[str, str | int]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    architecture_ok: bool = True
    architecture_errors: list[dict[str, str]] = Field(default_factory=list)
    architecture_warnings: list[dict[str, str]] = Field(default_factory=list)


class SensitiveActionChallengeSchema(BaseModel):
    action: str
    password: str
    module_key: str = ""


class SensitiveActionChallengeResponse(BaseModel):
    token: str
    expires_at: str
    action: str
    module_key: str = ""


class ModuleCatalogItem(BaseModel):
    key: str
    label: str
    route: str | None = None
    enabled: bool
    protocol_ok: bool
    protocol_missing: list[str] = Field(default_factory=list)
    package_upload_enabled: bool = False
    description: str = ""
    icon: str = ""
    image_url: str | None = None
    router_count: int = 0
    module_dir: str = ""
    package_target_label: str = ""
    protocol_has_init: bool = False
    protocol_has_manifest: bool = False
    architecture_ok: bool = True
    architecture_errors: list[dict[str, str]] = Field(default_factory=list)
    architecture_warnings: list[dict[str, str]] = Field(default_factory=list)


class ModuleUninstallResponse(BaseModel):
    module_key: str
    status: str = "success"
    removed_path: str = ""
    removed_files: int = 0


class ProtocolAuditItem(BaseModel):
    module_key: str = ""
    module_dir: str
    has_init: bool
    has_manifest: bool
    has_readme: bool = False
    has_controladores_dir: bool = False
    has_tests_dir: bool = False
    route_valid: bool = False
    icon_declared: bool = False
    depends_valid: bool = False
    routers_importable: bool = False
    assets_declared_exist: bool = False
    missing: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    ok: bool


class ProtocolSyncResponse(BaseModel):
    status: str = "success"
    task_id: str = ""
    task_name: str = ""
    created_init: list[str] = Field(default_factory=list)
    created_manifest: list[str] = Field(default_factory=list)
    updated_init: list[str] = Field(default_factory=list)
    updated_manifest: list[str] = Field(default_factory=list)
    before: dict[str, ProtocolAuditItem] = Field(default_factory=dict)
    after: dict[str, ProtocolAuditItem] = Field(default_factory=dict)


class AsyncTaskStateResponse(BaseModel):
    task_id: str
    task_name: str
    status: str
    updated_at: str = ""
    error: str = ""
    result: dict[str, Any] = Field(default_factory=dict)


class ModuleRollbackResponse(BaseModel):
    module_key: str
    status: str = "success"
    task_id: str = ""
    task_name: str = ""
    restored_files: int = 0
    snapshot_path: str = ""


ModuleStateIn = ModuleToggleSchema

__all__ = [
    "ModuleCatalogItem",
    "ModuleRollbackResponse",
    "ModuleUninstallResponse",
    "ModuleStateIn",
    "ModuleToggleSchema",
    "ModuleUploadResponse",
    "ProtocolAuditItem",
    "AsyncTaskStateResponse",
    "ProtocolSyncResponse",
    "ProtocolSyncSchema",
    "SensitiveActionChallengeResponse",
    "SensitiveActionChallengeSchema",
]
