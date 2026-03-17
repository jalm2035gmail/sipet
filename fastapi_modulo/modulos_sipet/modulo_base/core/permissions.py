from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from fastapi import Request

from fastapi_modulo.modulos_sipet.web.servicios.module_tools import require_app_access


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
