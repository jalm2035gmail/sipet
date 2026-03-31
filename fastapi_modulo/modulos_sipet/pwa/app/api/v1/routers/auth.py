from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import DBSession, get_current_active_user
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.repositories.user_repo import UserRepository
from app.schemas.token import LoginRequest, RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


def _issue_tokens(user) -> Token:
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = DBSession):
    repo = UserRepository(db)

    if repo.exists_email(data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if repo.exists_username(data.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    return repo.create(data)


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = DBSession):
    repo = UserRepository(db)
    user = repo.get_by_email(form.username) or repo.get_by_username(form.username)

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    return _issue_tokens(user)


@router.post("/login/json", response_model=Token)
def login_json(body: LoginRequest, db: Session = DBSession):
    repo = UserRepository(db)
    user = repo.get_by_email(body.username) or repo.get_by_username(body.username)

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    return _issue_tokens(user)


@router.post("/refresh", response_model=Token)
def refresh(body: RefreshTokenRequest, db: Session = DBSession):
    try:
        payload = decode_token(body.refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    repo = UserRepository(db)
    user = repo.get_by_id(int(payload["sub"]))

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return _issue_tokens(user)


@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_active_user)):
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user=Depends(get_current_active_user)):
    return None
