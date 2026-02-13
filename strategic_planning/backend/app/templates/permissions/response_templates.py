from typing import Dict, Any, List
from app.templates.components.buttons import ButtonTemplate
from app.templates.components.cards import CardTemplate
from app.templates.components.tables import TableTemplate
from app.templates.api import ApiResponseTemplate
from app.core.permissions import PermissionManager

class PermissionResponseTemplates:
    """Templates para respuestas del sistema de permisos"""
    
    @staticmethod
    def role_card(role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Template para tarjeta de rol"""
        return CardTemplate.basic(
            title=role_data.get("display_name", role_data.get("name")),
            subtitle=f"{role_data.get('user_count', 0)} usuarios",
            content={
                "name": role_data.get("name"),
                "description": role_data.get("description", "Sin descripción"),
                "hierarchy_level": role_data.get("hierarchy_level", 0),
                "is_system": role_data.get("is_system", False),
                "permissions_count": len(role_data.get("permissions", [])),
                "created_at": role_data.get("created_at")
            },
            actions=[
                ButtonTemplate.primary("Ver Detalles", url=f"/roles/{role_data.get('id')}"),
                ButtonTemplate.secondary("Editar", url=f"/roles/{role_data.get('id')}/edit"),
                ButtonTemplate.info("Asignar Usuarios", action="assign_users")
            ],
            badges=[
                {"text": "Sistema" if role_data.get("is_system") else "Personalizado", 
                 "color": "primary" if role_data.get("is_system") else "secondary"},
                {"text": f"Nivel {role_data.get('hierarchy_level', 0)}", "color": "info"}
            ]
        )
    
    @staticmethod
    def permission_card(permission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Template para tarjeta de permiso"""
        return CardTemplate.basic(
            title=permission_data.get("name"),
            subtitle=permission_data.get("code"),
            content={
                "category": permission_data.get("category"),
                "description": permission_data.get("description", "Sin descripción"),
                "is_system": permission_data.get("is_system", False),
                "display_order": permission_data.get("display_order", 0)
            },
            actions=[
                ButtonTemplate.info("Ver Roles", action="view_roles"),
                ButtonTemplate.secondary("Editar", url=f"/permissions/{permission_data.get('id')}/edit")
            ],
            badges=[
                {"text": permission_data.get("category", "").upper(), "color": "primary"},
                {"text": "Sistema" if permission_data.get("is_system") else "Personalizado", 
                 "color": "success" if permission_data.get("is_system") else "warning"}
            ]
        )
    
    @staticmethod
    def user_permissions_response(user_data: Dict[str, Any], permissions_data: Dict[str, Any]) -> Dict[str, Any]:
        """Template para respuesta de permisos de usuario"""
        permission_tables = []
        for category, permissions in permissions_data.get("categories", {}).items():
            permission_tables.append({
                "category": category.replace("_", " ").title(),
                "permissions": permissions,
                "count": len(permissions)
            })
        
        return ApiResponseTemplate.success(
            data={
                "user": {
                    "id": user_data.get("id"),
                    "name": user_data.get("full_name"),
                    "email": user_data.get("email"),
                    "role": user_data.get("role")
                },
                "permissions": permissions_data.get("permissions", []),
                "categories": permissions_data.get("categories", {}),
                "summary": {
                    "total_permissions": len(permissions_data.get("permissions", [])),
                    "total_categories": len(permissions_data.get("categories", {})),
                    "role_permissions": len(PermissionManager.get_role_permissions(user_data.get("role")))
                }
            },
            message=f"Permisos obtenidos para {user_data.get('full_name')}",
            metadata={
                "tables": permission_tables,
                "actions": [
                    ButtonTemplate.primary("Cambiar Rol", action="change_role"),
                    ButtonTemplate.secondary("Exportar Permisos", action="export_permissions")
                ]
            }
        )
    
    @staticmethod
    def role_hierarchy_response(hierarchy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Template para jerarquía de roles"""
        hierarchy_tree = []
        
        for role, info in hierarchy_data.items():
            hierarchy_tree.append({
                "role": role,
                "display_name": role.replace("_", " ").title(),
                "level": len(info.get("level", [])),
                "can_assign_to": info.get("can_assign", []),
                "can_be_assigned_by": [
                    r for r, assignable in hierarchy_data.items()
                    if role in assignable.get("can_assign", [])
                ]
            })
        
        hierarchy_tree.sort(key=lambda x: len(x.get("can_be_assigned_by", [])), reverse=True)
        
        return ApiResponseTemplate.success(
            data={
                "hierarchy": hierarchy_tree,
                "tree_structure": hierarchy_data
            },
            message="Jerarquía de roles obtenida exitosamente",
            metadata={
                "visualization": "tree",
                "actions": [
                    ButtonTemplate.primary("Ver Gráfico", action="show_chart"),
                    ButtonTemplate.secondary("Exportar Jerarquía", action="export_hierarchy")
                ]
            }
        )


class RoleResponseTemplates:
    """Templates específicos para respuestas de roles"""
    
    @staticmethod
    def role_detail_response(role: Dict[str, Any], users: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Template para detalle de rol con usuarios"""
        user_table = None
        if users:
            user_table = TableTemplate.create(
                headers=["ID", "Nombre", "Email", "Departamento", "Acciones"],
                rows=[
                    {
                        "id": user.get("id"),
                        "name": user.get("full_name"),
                        "email": user.get("email"),
                        "department": user.get("department_name", "Sin departamento"),
                        "actions": [
                            {"label": "Ver", "url": f"/users/{user.get('id')}"},
                            {"label": "Remover Rol", "action": "remove_role", "confirmation": True}
                        ]
                    }
                    for user in users
                ]
            )
        
        permission_table = TableTemplate.create(
            headers=["Código", "Nombre", "Categoría", "Descripción"],
            rows=[
                {
                    "code": perm.get("code"),
                    "name": perm.get("name"),
                    "category": perm.get("category"),
                    "description": perm.get("description", "")
                }
                for perm in role.get("permissions", [])
            ]
        )
        
        return ApiResponseTemplate.success(
            data=role,
            message=f"Detalles del rol {role.get('display_name')}",
            metadata={
                "tables": {
                    "permissions": permission_table,
                    "users": user_table
                },
                "stats": {
                    "total_users": len(users) if users else 0,
                    "total_permissions": len(role.get("permissions", [])),
                    "system_role": role.get("is_system", False)
                },
                "actions": [
                    ButtonTemplate.primary("Editar Rol", url=f"/roles/{role.get('id')}/edit"),
                    ButtonTemplate.success("Agregar Permisos", action="add_permissions"),
                    ButtonTemplate.warning("Asignar a Usuarios", action="assign_users"),
                    ButtonTemplate.danger("Eliminar Rol", action="delete_role", confirmation=True)
                ]
            }
        )
