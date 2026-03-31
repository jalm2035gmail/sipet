from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import DBSession, Pagination, PaginationParams, get_current_active_user, get_current_superuser
from app.core.security import hash_password, verify_password
from app.repositories.user_repo import UserRepository
from app.schemas.user import PasswordChange, UserRead, UserUpdate
from app.services import media_service

router = APIRouter()


@router.get("/", response_model=list[UserRead])
def list_users(
    params: PaginationParams = Pagination,
    db: Session = DBSession,
    current_user=Depends(get_current_superuser),
):
    return UserRepository(db).list(skip=params.skip, limit=params.limit)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.email and data.email.lower() != user.email and repo.exists_email(data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    return repo.update(user, data)


@router.post("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    user_id: int,
    data: PasswordChange,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(data.new_password)
    db.add(current_user)
    db.commit()
    return None


@router.post("/{user_id}/avatar", response_model=dict)
async def upload_avatar(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid image type")

    data = await file.read()
    thumb = media_service.thumbnail(data, size=200)
    media_service.save_upload(thumb, f"avatar_{user_id}.webp", subfolder="avatars")

    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.avatar_url = f"/media/avatars/avatar_{user_id}.webp"
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"avatar_url": user.avatar_url}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = DBSession,
    current_user=Depends(get_current_superuser),
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    repo.delete(user)
    return None
