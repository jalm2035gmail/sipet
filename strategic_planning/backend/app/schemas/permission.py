from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class PermissionCategory(str, Enum):
    """Categorías de permisos"""
    SYSTEM = "system"
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    KPI = "kpi"
    REPORTS = "reports"
    FILES = "files"
    COLLABORATION = "collaboration"
    NOTIFICATIONS = "notifications"
    PROFILE = "profile"

# ========== BASE SCHEMAS ==========
class PermissionBase(BaseModel):
    """Schema base para permiso"""
    code: str = Field(..., min_length=3, max_length=100, description="Código único del permiso")
    name: str = Field(..., min_length=3, max_length=200, description="Nombre del permiso")
    description: Optional[str] = Field(None, description="Descripción del permiso")
    category: PermissionCategory = Field(..., description="Categoría del permiso")
    display_order: int = Field(0, ge=0, description="Orden de visualización")

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    """Schema base para rol"""
    name: str = Field(..., min_length=2, max_length=50, description="Nombre único del rol")
    display_name: str = Field(..., min_length=2, max_length=100, description="Nombre para mostrar")
    description: Optional[str] = Field(None, description="Descripción del rol")
    hierarchy_level: int = Field(0, ge=0, le=100, description="Nivel en jerarquía")

    class Config:
        from_attributes = True

# ========== CREATE SCHEMAS ==========
class PermissionCreate(PermissionBase):
    """Schema para crear permiso"""
    is_system: bool = Field(False, description="Es permiso del sistema")

    @validator('code')
    def validate_code_format(cls, v):
        # Validar formato: categoria:accion_recurso
        if ':' not in v:
            raise ValueError('El código debe tener formato: categoria:accion_recurso')
        return v

class RoleCreate(RoleBase):
    """Schema para crear rol"""
    is_system: bool = Field(False, description="Es rol del sistema")
    permission_codes: Optional[List[str]] = Field([], description="Códigos de permisos a asignar")

class RoleUpdate(BaseModel):
    """Schema para actualizar rol"""
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    hierarchy_level: Optional[int] = Field(None, ge=0, le=100)
    permission_codes: Optional[List[str]] = None

class RolePermissionUpdate(BaseModel):
    """Schema para actualizar permisos de un rol"""
    permission_codes: List[str] = Field(..., description="Lista de códigos de permisos")
    action: str = Field(..., description="add o remove")

# ========== RESPONSE SCHEMAS ==========
class PermissionResponse(PermissionBase):
    """Schema para respuesta de permiso"""
    id: int
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "code": "strategic:view_plans",
                "name": "Ver Planes Estratégicos",
                "description": "Permite visualizar planes estratégicos",
                "category": "strategic",
                "is_system": True,
                "display_order": 10,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

class RoleResponse(RoleBase):
    """Schema para respuesta de rol"""
    id: int
    is_system: bool
    permissions: List[PermissionResponse]
    user_count: Optional[int] = 0
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "department_manager",
                "display_name": "Gerente de Departamento",
                "description": "Gestiona planes y recursos de su departamento",
                "hierarchy_level": 70,
                "is_system": True,
                "user_count": 5,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

class RoleSimpleResponse(RoleBase):
    """Schema simple para respuesta de rol"""
    id: int
    is_system: bool
    user_count: Optional[int] = 0

class UserPermissionResponse(BaseModel):
    """Schema para respuesta de permisos de usuario"""
    user_id: int
    role: str
    permissions: List[str]
    categories: Dict[str, List[str]]

class PermissionCategoryResponse(BaseModel):
    """Schema para respuesta de categorías de permisos"""
    category: str
    permissions: List[PermissionResponse]
    count: int

# ========== FILTER SCHEMAS ==========
class PermissionFilter(BaseModel):
    """Schema para filtrar permisos"""
    category: Optional[PermissionCategory] = None
    is_system: Optional[bool] = None
    search: Optional[str] = None

class RoleFilter(BaseModel):
    """Schema para filtrar roles"""
    is_system: Optional[bool] = None
    search: Optional[str] = None
    min_hierarchy: Optional[int] = None
    max_hierarchy: Optional[int] = None

# ========== ASSIGNMENT SCHEMAS ==========
class UserRoleAssignment(BaseModel):
    """Schema para asignar rol a usuario"""
    user_id: int = Field(..., description="ID del usuario")
    role_id: int = Field(..., description="ID del rol a asignar")
    reason: Optional[str] = Field(None, description="Razón del cambio")

class BulkRoleAssignment(BaseModel):
    """Schema para asignar rol a múltiples usuarios"""
    user_ids: List[int] = Field(..., description="IDs de usuarios")
    role_id: int = Field(..., description="ID del rol a asignar")
    reason: Optional[str] = Field(None, description="Razón del cambio")

# ========== AUDIT SCHEMAS ==========
class PermissionAuditResponse(BaseModel):
    """Schema para auditoría de permisos"""
    id: int
    permission_id: int
    action: str
    details: Optional[str]
    previous_value: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[int]
    created_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True

class RoleAuditResponse(BaseModel):
    """Schema para auditoría de roles"""
    id: int
    role_id: int
    action: str
    details: Optional[str]
    affected_user_id: Optional[int]
    created_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True
