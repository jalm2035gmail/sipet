from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from fastapi import HTTPException, Request

from fastapi_modulo.modulos_sipet.web.servicios.module_tools import require_app_access
from fastapi_modulo.modulos_sipet.web.servicios.access_service import has_permission_flag, is_admin_or_superadmin


class ModulePermissionAction(str, Enum):
    VER = "ver"
    CREAR = "crear"
    EDITAR = "editar"
    ELIMINAR = "eliminar"
    EXPORTAR = "exportar"
    APROBAR = "aprobar"
    CONFIGURAR = "configurar"
    ADMINISTRAR = "administrar"
    AUDITORIA = "auditoria"


@dataclass(slots=True, frozen=True)
class ModulePermission:
    code: str
    name: str
    description: str
    action: str = ""


STANDARD_MODULE_ACTIONS = tuple(action.value for action in ModulePermissionAction)


def _normalize_permission_code(value: str | None) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    normalized = unicodedata.normalize("NFKD", raw)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9._-]+", "", normalized)
    return normalized


def _parse_permission_values(value: object) -> set[str]:
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value]
    else:
        return set()
    return {_normalize_permission_code(item) for item in items if _normalize_permission_code(item)}


def build_standard_permissions(module_key: str, module_label: str) -> list[ModulePermission]:
    action_labels = {
        ModulePermissionAction.VER.value: "Ver",
        ModulePermissionAction.CREAR.value: "Crear",
        ModulePermissionAction.EDITAR.value: "Editar",
        ModulePermissionAction.ELIMINAR.value: "Eliminar",
        ModulePermissionAction.EXPORTAR.value: "Exportar",
        ModulePermissionAction.APROBAR.value: "Aprobar",
        ModulePermissionAction.CONFIGURAR.value: "Configurar",
        ModulePermissionAction.ADMINISTRAR.value: "Administrar",
        ModulePermissionAction.AUDITORIA.value: "Auditoria",
    }
    return [
        ModulePermission(
            code=f"{module_key}.{action}",
            name=f"{action_labels[action]} {module_label}",
            description=f"Permite {action} en el modulo {module_label}.",
            action=action,
        )
        for action in STANDARD_MODULE_ACTIONS
    ]


class ModulePermissionRegistry:
    def __init__(self, *, module_name: str, permissions_path: Path, detail: str) -> None:
        self.module_name = module_name
        self.permissions_path = permissions_path
        self.detail = detail

    def load(self) -> list[ModulePermission]:
        try:
            payload = json.loads(self.permissions_path.read_text(encoding="utf-8"))
        except OSError:
            return []
        return [
            ModulePermission(
                code=item.get("code", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                action=item.get("action", ""),
            )
            for item in payload.get("permissions", [])
        ]

    def require_access(self, request: Request) -> None:
        require_app_access(request, self.module_name, self.detail)

    def request_permissions(self, request: Request) -> set[str]:
        candidates = [
            getattr(request.state, "permissions", None),
            getattr(request.state, "user_permissions", None),
        ]
        permissions: set[str] = set()
        for candidate in candidates:
            permissions.update(_parse_permission_values(candidate))
        return permissions

    def require_permission(self, request: Request, permission_code: str, detail: str | None = None) -> None:
        self.require_access(request)
        required_permission = _normalize_permission_code(permission_code)
        if not required_permission:
            return
        if required_permission in self.request_permissions(request):
            return
        if has_permission_flag(request, required_permission):
            return
        if is_admin_or_superadmin(request):
            return
        raise HTTPException(status_code=403, detail=detail or self.detail)
