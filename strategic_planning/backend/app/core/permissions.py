from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Set

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import InsufficientPermissionsException


class Permission(str, Enum):
    """Enumeración de permisos del sistema."""

    SYSTEM_MANAGE_USERS = "system:manage_users"
    SYSTEM_MANAGE_ROLES = "system:manage_roles"
    SYSTEM_MANAGE_PERMISSIONS = "system:manage_permissions"
    SYSTEM_MANAGE_DEPARTMENTS = "system:manage_departments"
    SYSTEM_VIEW_AUDIT_LOGS = "system:view_audit_logs"
    SYSTEM_MANAGE_SETTINGS = "system:manage_settings"
    SYSTEM_MANAGE_INTEGRATIONS = "system:manage_integrations"

    STRATEGIC_VIEW_PLANS = "strategic:view_plans"
    STRATEGIC_CREATE_PLANS = "strategic:create_plans"
    STRATEGIC_EDIT_PLANS = "strategic:edit_plans"
    STRATEGIC_DELETE_PLANS = "strategic:delete_plans"
    STRATEGIC_APPROVE_PLANS = "strategic:approve_plans"
    STRATEGIC_ARCHIVE_PLANS = "strategic:archive_plans"
    STRATEGIC_VIEW_AXES = "strategic:view_axes"
    STRATEGIC_CREATE_AXES = "strategic:create_axes"
    STRATEGIC_EDIT_AXES = "strategic:edit_axes"
    STRATEGIC_DELETE_AXES = "strategic:delete_axes"
    STRATEGIC_VIEW_DIAGNOSTICS = "strategic:view_diagnostics"
    STRATEGIC_CREATE_DIAGNOSTICS = "strategic:create_diagnostics"
    STRATEGIC_EDIT_DIAGNOSTICS = "strategic:edit_diagnostics"

    POA_VIEW = "poa:view"
    POA_CREATE = "poa:create"
    POA_EDIT = "poa:edit"
    POA_DELETE = "poa:delete"
    POA_APPROVE = "poa:approve"
    POA_EXPORT = "poa:export"
    POA_VIEW_ACTIVITIES = "poa:view_activities"
    POA_CREATE_ACTIVITIES = "poa:create_activities"
    POA_EDIT_ACTIVITIES = "poa:edit_activities"
    POA_DELETE_ACTIVITIES = "poa:delete_activities"
    POA_VIEW_RESOURCES = "poa:view_resources"
    POA_MANAGE_RESOURCES = "poa:manage_resources"
    POA_VIEW_BUDGET = "poa:view_budget"
    POA_MANAGE_BUDGET = "poa:manage_budget"

    KPI_VIEW = "kpi:view"
    KPI_CREATE = "kpi:create"
    KPI_EDIT = "kpi:edit"
    KPI_DELETE = "kpi:delete"
    KPI_RECORD_MEASUREMENTS = "kpi:record_measurements"
    KPI_VIEW_DASHBOARDS = "kpi:view_dashboards"
    KPI_MANAGE_ALERTS = "kpi:manage_alerts"

    REPORTS_VIEW = "reports:view"
    REPORTS_CREATE = "reports:create"
    REPORTS_EDIT = "reports:edit"
    REPORTS_DELETE = "reports:delete"
    REPORTS_EXPORT = "reports:export"
    REPORTS_SCHEDULE = "reports:schedule"

    FILES_UPLOAD = "files:upload"
    FILES_DOWNLOAD = "files:download"
    FILES_DELETE = "files:delete"
    FILES_SHARE = "files:share"

    COLLABORATION_VIEW = "collaboration:view"
    COLLABORATION_COMMENT = "collaboration:comment"
    COLLABORATION_EDIT_COMMENTS = "collaboration:edit_comments"
    COLLABORATION_DELETE_COMMENTS = "collaboration:delete_comments"

    NOTIFICATIONS_VIEW = "notifications:view"
    NOTIFICATIONS_MANAGE = "notifications:manage"

    PROFILE_VIEW = "profile:view"
    PROFILE_EDIT = "profile:edit"
    PROFILE_CHANGE_PASSWORD = "profile:change_password"
    PROFILE_VIEW_ACTIVITY = "profile:view_activity"


class ResourceScope(str, Enum):
    GLOBAL = "global"
    DEPARTMENT = "department"
    OWN = "own"
    TEAM = "team"


class PermissionManager:
    ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
        "super_admin": set(Permission),
        "admin": {
            Permission.SYSTEM_MANAGE_USERS,
            Permission.SYSTEM_MANAGE_DEPARTMENTS,
            Permission.SYSTEM_VIEW_AUDIT_LOGS,
            Permission.STRATEGIC_VIEW_PLANS,
            Permission.STRATEGIC_CREATE_PLANS,
            Permission.STRATEGIC_EDIT_PLANS,
            Permission.STRATEGIC_DELETE_PLANS,
            Permission.STRATEGIC_APPROVE_PLANS,
            Permission.STRATEGIC_ARCHIVE_PLANS,
            Permission.STRATEGIC_VIEW_AXES,
            Permission.STRATEGIC_CREATE_AXES,
            Permission.STRATEGIC_EDIT_AXES,
            Permission.STRATEGIC_DELETE_AXES,
            Permission.STRATEGIC_VIEW_DIAGNOSTICS,
            Permission.STRATEGIC_CREATE_DIAGNOSTICS,
            Permission.STRATEGIC_EDIT_DIAGNOSTICS,
            Permission.POA_VIEW,
            Permission.POA_CREATE,
            Permission.POA_EDIT,
            Permission.POA_DELETE,
            Permission.POA_APPROVE,
            Permission.POA_EXPORT,
            Permission.KPI_VIEW,
            Permission.KPI_CREATE,
            Permission.KPI_EDIT,
            Permission.KPI_MANAGE_ALERTS,
            Permission.REPORTS_VIEW,
            Permission.REPORTS_CREATE,
            Permission.REPORTS_EDIT,
            Permission.REPORTS_DELETE,
            Permission.REPORTS_EXPORT,
            Permission.REPORTS_SCHEDULE,
            Permission.FILES_UPLOAD,
            Permission.FILES_DOWNLOAD,
            Permission.FILES_DELETE,
            Permission.FILES_SHARE,
            Permission.COLLABORATION_VIEW,
            Permission.COLLABORATION_COMMENT,
            Permission.COLLABORATION_EDIT_COMMENTS,
            Permission.COLLABORATION_DELETE_COMMENTS,
            Permission.NOTIFICATIONS_VIEW,
            Permission.NOTIFICATIONS_MANAGE,
            Permission.PROFILE_VIEW,
            Permission.PROFILE_EDIT,
            Permission.PROFILE_CHANGE_PASSWORD,
            Permission.PROFILE_VIEW_ACTIVITY,
        },
        "strategic_manager": {
            Permission.STRATEGIC_VIEW_PLANS,
            Permission.STRATEGIC_CREATE_PLANS,
            Permission.STRATEGIC_EDIT_PLANS,
            Permission.STRATEGIC_DELETE_PLANS,
            Permission.STRATEGIC_APPROVE_PLANS,
            Permission.STRATEGIC_ARCHIVE_PLANS,
            Permission.STRATEGIC_VIEW_AXES,
            Permission.STRATEGIC_CREATE_AXES,
            Permission.STRATEGIC_EDIT_AXES,
            Permission.STRATEGIC_DELETE_AXES,
            Permission.STRATEGIC_VIEW_DIAGNOSTICS,
            Permission.STRATEGIC_CREATE_DIAGNOSTICS,
            Permission.STRATEGIC_EDIT_DIAGNOSTICS,
            Permission.POA_VIEW,
            Permission.POA_APPROVE,
            Permission.POA_EXPORT,
            Permission.KPI_VIEW,
            Permission.KPI_CREATE,
            Permission.KPI_EDIT,
            Permission.KPI_VIEW_DASHBOARDS,
            Permission.KPI_MANAGE_ALERTS,
            Permission.REPORTS_VIEW,
            Permission.REPORTS_CREATE,
            Permission.REPORTS_EDIT,
            Permission.REPORTS_DELETE,
            Permission.REPORTS_EXPORT,
            Permission.REPORTS_SCHEDULE,
            Permission.FILES_UPLOAD,
            Permission.FILES_DOWNLOAD,
            Permission.FILES_SHARE,
            Permission.COLLABORATION_VIEW,
            Permission.COLLABORATION_COMMENT,
            Permission.NOTIFICATIONS_VIEW,
            Permission.PROFILE_VIEW,
            Permission.PROFILE_EDIT,
            Permission.PROFILE_CHANGE_PASSWORD,
            Permission.PROFILE_VIEW_ACTIVITY,
        },
        "department_manager": {
            Permission.STRATEGIC_VIEW_PLANS,
            Permission.STRATEGIC_CREATE_PLANS,
            Permission.STRATEGIC_EDIT_PLANS,
            Permission.STRATEGIC_ARCHIVE_PLANS,
            Permission.STRATEGIC_VIEW_AXES,
            Permission.STRATEGIC_CREATE_AXES,
            Permission.STRATEGIC_EDIT_AXES,
            Permission.STRATEGIC_VIEW_DIAGNOSTICS,
            Permission.STRATEGIC_CREATE_DIAGNOSTICS,
            Permission.STRATEGIC_EDIT_DIAGNOSTICS,
            Permission.POA_VIEW,
            Permission.POA_CREATE,
            Permission.POA_EDIT,
            Permission.POA_EXPORT,
            Permission.POA_VIEW_ACTIVITIES,
            Permission.POA_CREATE_ACTIVITIES,
            Permission.POA_EDIT_ACTIVITIES,
            Permission.POA_DELETE_ACTIVITIES,
            Permission.POA_VIEW_RESOURCES,
            Permission.POA_MANAGE_RESOURCES,
            Permission.POA_VIEW_BUDGET,
            Permission.POA_MANAGE_BUDGET,
            Permission.KPI_VIEW,
            Permission.KPI_CREATE,
            Permission.KPI_EDIT,
            Permission.KPI_RECORD_MEASUREMENTS,
            Permission.KPI_VIEW_DASHBOARDS,
            Permission.KPI_MANAGE_ALERTS,
            Permission.REPORTS_VIEW,
            Permission.REPORTS_CREATE,
            Permission.REPORTS_EDIT,
            Permission.REPORTS_EXPORT,
            Permission.FILES_UPLOAD,
            Permission.FILES_DOWNLOAD,
            Permission.FILES_SHARE,
            Permission.COLLABORATION_VIEW,
            Permission.COLLABORATION_COMMENT,
            Permission.COLLABORATION_EDIT_COMMENTS,
            Permission.NOTIFICATIONS_VIEW,
            Permission.PROFILE_VIEW,
            Permission.PROFILE_EDIT,
            Permission.PROFILE_CHANGE_PASSWORD,
            Permission.PROFILE_VIEW_ACTIVITY,
        },
        "team_leader": {
            Permission.STRATEGIC_VIEW_PLANS,
            Permission.STRATEGIC_VIEW_AXES,
            Permission.STRATEGIC_VIEW_DIAGNOSTICS,
            Permission.POA_VIEW,
            Permission.POA_VIEW_ACTIVITIES,
            Permission.POA_EDIT_ACTIVITIES,
            Permission.POA_VIEW_RESOURCES,
            Permission.POA_VIEW_BUDGET,
            Permission.KPI_VIEW,
            Permission.KPI_RECORD_MEASUREMENTS,
            Permission.KPI_VIEW_DASHBOARDS,
            Permission.REPORTS_VIEW,
            Permission.FILES_UPLOAD,
            Permission.FILES_DOWNLOAD,
            Permission.COLLABORATION_VIEW,
            Permission.COLLABORATION_COMMENT,
            Permission.NOTIFICATIONS_VIEW,
            Permission.PROFILE_VIEW,
            Permission.PROFILE_EDIT,
            Permission.PROFILE_CHANGE_PASSWORD,
        },
        "collaborator": {
            Permission.STRATEGIC_VIEW_PLANS,
            Permission.STRATEGIC_VIEW_AXES,
            Permission.POA_VIEW,
            Permission.POA_VIEW_ACTIVITIES,
            Permission.KPI_VIEW,
            Permission.KPI_RECORD_MEASUREMENTS,
            Permission.REPORTS_VIEW,
            Permission.FILES_UPLOAD,
            Permission.FILES_DOWNLOAD,
            Permission.COLLABORATION_VIEW,
            Permission.COLLABORATION_COMMENT,
            Permission.NOTIFICATIONS_VIEW,
            Permission.PROFILE_VIEW,
            Permission.PROFILE_EDIT,
            Permission.PROFILE_CHANGE_PASSWORD,
        },
        "viewer": {
            Permission.STRATEGIC_VIEW_PLANS,
            Permission.STRATEGIC_VIEW_AXES,
            Permission.POA_VIEW,
            Permission.POA_VIEW_ACTIVITIES,
            Permission.KPI_VIEW,
            Permission.REPORTS_VIEW,
            Permission.FILES_DOWNLOAD,
            Permission.COLLABORATION_VIEW,
            Permission.NOTIFICATIONS_VIEW,
            Permission.PROFILE_VIEW,
            Permission.PROFILE_EDIT,
            Permission.PROFILE_CHANGE_PASSWORD,
        },
    }

    ROLE_HIERARCHY: Dict[str, Set[str]] = {
        "super_admin": {"admin", "strategic_manager", "department_manager", "team_leader", "collaborator", "viewer"},
        "admin": {"strategic_manager", "department_manager", "team_leader", "collaborator", "viewer"},
        "strategic_manager": {"department_manager", "team_leader", "collaborator", "viewer"},
        "department_manager": {"team_leader", "collaborator", "viewer"},
        "team_leader": {"collaborator"},
        "collaborator": set(),
        "viewer": set(),
    }

    @classmethod
    def get_role_permissions(cls, role_name: str) -> Set[Permission]:
        return cls.ROLE_PERMISSIONS.get(role_name, set())

    @classmethod
    def can_assign_role(cls, assigner_role: str, target_role: str) -> bool:
        return target_role in cls.ROLE_HIERARCHY.get(assigner_role, set())

    @classmethod
    def has_permission(cls, role_name: str, permission: Permission) -> bool:
        return permission in cls.get_role_permissions(role_name)

    @classmethod
    def check_permission(cls, role_name: str, permission: Permission) -> bool:
        if not cls.has_permission(role_name, permission):
            raise InsufficientPermissionsException(f"Se requiere permiso: {permission.value}")
        return True

    @classmethod
    def get_permission_categories(cls) -> Dict[str, List[Dict[str, str]]]:
        categories: Dict[str, List[Dict[str, str]]] = {}
        for permission in Permission:
            category = permission.value.split(":")[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(
                {
                    "value": permission.value,
                    "name": permission.name,
                    "description": cls.get_permission_description(permission),
                }
            )
        return categories

    @classmethod
    def get_permission_description(cls, permission: Permission) -> str:
        descriptions = {
            Permission.SYSTEM_MANAGE_USERS: "Gestionar usuarios del sistema",
            Permission.SYSTEM_MANAGE_ROLES: "Gestionar roles y permisos",
            Permission.SYSTEM_MANAGE_DEPARTMENTS: "Gestionar departamentos",
            Permission.SYSTEM_VIEW_AUDIT_LOGS: "Ver registros de auditoría",
            Permission.STRATEGIC_VIEW_PLANS: "Ver planes estratégicos",
            Permission.STRATEGIC_CREATE_PLANS: "Crear planes estratégicos",
            Permission.STRATEGIC_EDIT_PLANS: "Editar planes estratégicos",
            Permission.STRATEGIC_DELETE_PLANS: "Eliminar planes estratégicos",
            Permission.STRATEGIC_APPROVE_PLANS: "Aprobar planes estratégicos",
            Permission.STRATEGIC_ARCHIVE_PLANS: "Archivar planes estratégicos",
            Permission.POA_VIEW: "Ver POAs",
            Permission.POA_CREATE: "Crear POAs",
            Permission.POA_EDIT: "Editar POAs",
            Permission.POA_DELETE: "Eliminar POAs",
            Permission.POA_APPROVE: "Aprobar POAs",
            Permission.KPI_VIEW: "Ver KPIs",
            Permission.KPI_CREATE: "Crear KPIs",
            Permission.KPI_EDIT: "Editar KPIs",
            Permission.KPI_DELETE: "Eliminar KPIs",
            Permission.KPI_RECORD_MEASUREMENTS: "Registrar mediciones de KPI",
            Permission.KPI_VIEW_DASHBOARDS: "Ver dashboards de KPIs",
            Permission.REPORTS_VIEW: "Ver reportes",
            Permission.REPORTS_CREATE: "Crear reportes",
            Permission.REPORTS_EXPORT: "Exportar reportes",
            Permission.FILES_UPLOAD: "Subir archivos",
            Permission.FILES_DOWNLOAD: "Descargar archivos",
            Permission.FILES_SHARE: "Compartir archivos",
            Permission.COLLABORATION_VIEW: "Ver comentarios",
            Permission.COLLABORATION_COMMENT: "Agregar comentarios",
            Permission.PROFILE_VIEW: "Ver perfil",
            Permission.PROFILE_EDIT: "Editar perfil",
            Permission.PROFILE_CHANGE_PASSWORD: "Cambiar contraseña",
            Permission.PROFILE_VIEW_ACTIVITY: "Ver actividad del perfil",
        }
        return descriptions.get(permission, "Sin descripción")


class PermissionDependency:
    def __init__(self, permission: Permission, scope: ResourceScope = ResourceScope.GLOBAL):
        self.permission = permission
        self.scope = scope

    async def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        PermissionManager.check_permission(current_user["role"], self.permission)
        current_user["resource_scope"] = self.scope
        return current_user


def require_role(name: str):
    hierarchy = {
        "super_admin": 100,
        "admin": 90,
        "strategic_manager": 80,
        "department_manager": 70,
        "team_leader": 60,
        "collaborator": 50,
        "viewer": 40,
    }

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict = Depends(get_current_user), **kwargs):
            user_level = hierarchy.get(current_user["role"], 0)
            if user_level < hierarchy.get(name, 0):
                raise InsufficientPermissionsException(f"Se requiere rol {name} o superior")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper

    return decorator


def require_permission(permission: Permission, scope: ResourceScope = ResourceScope.GLOBAL):
    return PermissionDependency(permission, scope)


require_manage_users = require_permission(Permission.SYSTEM_MANAGE_USERS)
require_manage_roles = require_permission(Permission.SYSTEM_MANAGE_ROLES)
require_view_strategic_plans = require_permission(Permission.STRATEGIC_VIEW_PLANS)
require_create_strategic_plans = require_permission(Permission.STRATEGIC_CREATE_PLANS)
require_edit_strategic_plans = require_permission(Permission.STRATEGIC_EDIT_PLANS)
require_approve_strategic_plans = require_permission(Permission.STRATEGIC_APPROVE_PLANS)
require_view_poa = require_permission(Permission.POA_VIEW)
require_create_poa = require_permission(Permission.POA_CREATE)
require_manage_kpis = require_permission(Permission.KPI_CREATE)
require_view_reports = require_permission(Permission.REPORTS_VIEW)
require_upload_files = require_permission(Permission.FILES_UPLOAD)


class ResourcePermissionChecker:
    @staticmethod
    def check_resource_access(
        user: dict,
        resource: Any,
        required_permission: Permission,
        resource_owner_id: Optional[int] = None,
        resource_department_id: Optional[int] = None,
    ) -> bool:
        from app.core.permissions import PermissionManager

        if not PermissionManager.has_permission(user["role"], required_permission):
            return False

        scope = user.get("resource_scope", ResourceScope.GLOBAL)
        if scope == ResourceScope.GLOBAL:
            return True
        if scope == ResourceScope.DEPARTMENT:
            return user.get("department_id") == resource_department_id
        if scope == ResourceScope.OWN:
            return user["id"] == resource_owner_id
        if scope == ResourceScope.TEAM:
            return True
        return False

    @staticmethod
    def filter_resources_by_permission(
        user: dict,
        resources: List[Any],
        required_permission: Permission,
        owner_field: str = "created_by",
        department_field: str = "department_id",
    ) -> List[Any]:
        scope = user.get("resource_scope", ResourceScope.GLOBAL)
        if scope == ResourceScope.GLOBAL:
            return resources
        if scope == ResourceScope.DEPARTMENT:
            return [
                r for r in resources if getattr(r, department_field, None) == user.get("department_id")
            ]
        if scope == ResourceScope.OWN:
            return [r for r in resources if getattr(r, owner_field, None) == user["id"]]
        if scope == ResourceScope.TEAM:
            return resources
        return []
