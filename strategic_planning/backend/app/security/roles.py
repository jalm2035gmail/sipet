class Role:
    ADMIN = "admin"
    STRATEGIC_MANAGER = "strategic_manager"
    DEPARTMENT_MANAGER = "department_manager"
    EMPLOYEE = "employee"

class Permission:
    CREATE_USER = "create_user"
    EDIT_USER = "edit_user"
    DELETE_USER = "delete_user"
    VIEW_USER = "view_user"
    MANAGE_POA = "manage_poa"
    MANAGE_KPI = "manage_kpi"
    VIEW_REPORTS = "view_reports"

role_permissions = {
    Role.ADMIN: [Permission.CREATE_USER, Permission.EDIT_USER, Permission.DELETE_USER, Permission.VIEW_USER, Permission.MANAGE_POA, Permission.MANAGE_KPI, Permission.VIEW_REPORTS],
    Role.STRATEGIC_MANAGER: [Permission.MANAGE_POA, Permission.MANAGE_KPI, Permission.VIEW_REPORTS],
    Role.DEPARTMENT_MANAGER: [Permission.MANAGE_POA, Permission.VIEW_REPORTS],
    Role.EMPLOYEE: [Permission.VIEW_REPORTS],
}

def has_permission(role, permission):
    return permission in role_permissions.get(role, [])
