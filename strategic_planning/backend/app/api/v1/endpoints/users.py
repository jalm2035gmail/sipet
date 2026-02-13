from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_db,
    require_permission,
    require_role,
)
from app.crud.user import user as user_crud
from app.schemas.user import (
    UserCreateAdmin,
    UserDetailResponse,
    UserFilter,
    UserResponse,
    UserStats,
    UserUpdate,
)
from app.templates.api import ApiResponseTemplate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
async def read_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("can_manage_users")),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None),
    department_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    try:
        filter_obj = UserFilter(
            role=role,
            department_id=department_id,
            status=status,
            search=search,
        )
        users, total = user_crud.get_multi_with_filters(
            db,
            filter_obj=filter_obj,
            skip=skip,
            limit=limit,
        )
        response = [
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "role": user.role,
                "status": user.status,
                "department_id": user.department_id,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
            for user in users
        ]
        return ApiResponseTemplate.paginated(
            data=response,
            total=total,
            skip=skip,
            limit=limit,
            metadata={"filters": filter_obj.model_dump(exclude_none=True)},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar usuarios: {exc}",
        )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("can_manage_users")),
):
    try:
        user = user_crud.create_with_admin(
            db,
            obj_in=user_in,
            admin_id=current_user["id"],
        )
        return ApiResponseTemplate.success(
            data={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "role": user.role,
                "status": user.status,
                "department_id": user.department_id,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
            },
            message="Usuario creado exitosamente",
            status_code=status.HTTP_201_CREATED,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario: {exc}",
        )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("can_manage_users")),
):
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return ApiResponseTemplate.success(
        data={
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "status": user.status,
            "department_id": user.department_id,
            "is_verified": user.is_verified,
            "phone": user.phone,
            "last_login_at": user.last_login_at,
            "timezone": user.timezone,
            "language": user.language,
            "email_notifications": user.email_notifications,
            "push_notifications": user.push_notifications,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "department_name": user.department.name if user.department else None,
        },
        message="Usuario obtenido exitosamente",
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("can_manage_users")),
):
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if user.role == "super_admin" and current_user["role"] != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes modificar un super administrador",
        )
    user = user_crud.update(db, db_obj=user, obj_in=user_in)
    return ApiResponseTemplate.success(
        data={
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "status": user.status,
            "department_id": user.department_id,
            "is_verified": user.is_verified,
            "updated_at": user.updated_at,
        },
        message="Usuario actualizado exitosamente",
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("super_admin")),
):
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if user.id == current_user["id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes eliminarte a ti mismo")
    if user.role == "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes eliminar un super administrador")
    user.is_active = False
    db.commit()
    return ApiResponseTemplate.success(message="Usuario eliminado exitosamente")


@router.get("/stats/overview", response_model=UserStats)
async def get_users_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("can_manage_users")),
):
    stats = user_crud.get_statistics(db)
    return ApiResponseTemplate.success(data=stats, message="Estadísticas obtenidas exitosamente")


@router.post("/{user_id}/verify")
async def verify_user_email(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("can_manage_users")),
):
    user_crud.verify_email(db, user_id=user_id)
    return ApiResponseTemplate.success(message="Email verificado exitosamente")


@router.post("/{user_id}/status")
async def update_user_status(
    user_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("can_manage_users")),
):
    user_crud.update_status(db, user_id=user_id, status=status, updated_by=current_user["id"])
    return ApiResponseTemplate.success(message=f"Estado del usuario actualizado a {status}")
