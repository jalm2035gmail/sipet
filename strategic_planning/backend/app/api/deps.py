from typing import Optional, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    AccountLockedException,
    CredentialsException,
    InsufficientPermissionsException,
    TokenExpiredException,
    TokenInvalidException,
)
from app.core.permissions import (
    Permission,
    ResourceScope,
    require_permission,
)
from app.crud.role import role as role_crud
from app.crud.token import token_crud
from app.crud.user import user as user_crud
from app.db.session import SessionLocal
from app.models.user import UserStatus


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)

http_bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> dict:
    auth_token = token
    if not auth_token and credentials:
        auth_token = credentials.credentials

    if not auth_token:
        raise CredentialsException("Token no proporcionado")

    try:
        payload = jwt.decode(
            auth_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        if user_id is None:
            raise CredentialsException("Token inválido: sub claim faltante")
        if token_type != "access":
            raise CredentialsException("Token no es de tipo access")
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()
    except JWTError:
        raise TokenInvalidException()

    token_obj = token_crud.get_by_token(db, token=auth_token)
    if token_obj and (token_obj.revoked or not token_obj.is_valid()):
        raise CredentialsException("Token revocado o inválido")

    user = user_crud.get(db, id=int(user_id))
    if user is None:
        raise CredentialsException("Usuario no encontrado")

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Usuario {user.status}. Contacta al administrador.",
        )

    if token_obj:
        token_obj.record_usage()
        db.add(token_obj)
        db.commit()

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "department_id": user.department_id,
        "is_verified": user.is_verified,
        "full_name": user.full_name,
    }


async def get_current_user_with_permissions(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> dict:
    user = await get_current_user(db=db, token=token, credentials=credentials)

    try:
        permissions = role_crud.get_user_permissions(db, user_id=user["id"])
        user["permissions"] = permissions.get("permissions", [])
        user["permissions_by_category"] = permissions.get("categories", {})
    except Exception:
        user["permissions"] = []
        user["permissions_by_category"] = {}

    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user_with_permissions),
) -> dict:
    if not current_user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no verificado",
        )
    return current_user


def require_permissions(*permissions: Permission):
    async def permissions_dependency(
        current_user: dict = Depends(get_current_user_with_permissions),
    ) -> dict:
        for permission in permissions:
            if permission.value not in current_user.get("permissions", []):
                raise InsufficientPermissionsException(
                    f"Se requiere permiso: {permission.value}"
                )
        return current_user

    return permissions_dependency


def require_strategic_view():
    return require_permission(Permission.STRATEGIC_VIEW_PLANS)


def require_strategic_edit():
    return require_permission(Permission.STRATEGIC_EDIT_PLANS)


def require_strategic_approve():
    return require_permission(Permission.STRATEGIC_APPROVE_PLANS)


def require_poa_manage():
    return require_permissions(
        Permission.POA_VIEW,
        Permission.POA_CREATE,
        Permission.POA_EDIT,
    )


def check_resource_scope(
    resource_department_id: Optional[int] = None,
    resource_owner_id: Optional[int] = None,
):
    async def scope_checker(
        current_user: dict = Depends(get_current_user_with_permissions),
    ) -> dict:
        scope = current_user.get("resource_scope", ResourceScope.GLOBAL)

        if scope == ResourceScope.GLOBAL:
            return current_user

        if scope == ResourceScope.DEPARTMENT:
            user_dept = current_user.get("department_id")
            if user_dept is None or user_dept != resource_department_id:
                raise InsufficientPermissionsException(
                    "No tienes acceso a recursos de este departamento"
                )

        if scope == ResourceScope.OWN:
            if current_user["id"] != resource_owner_id:
                raise InsufficientPermissionsException(
                    "Solo puedes acceder a tus propios recursos"
                )

        return current_user

    return scope_checker
