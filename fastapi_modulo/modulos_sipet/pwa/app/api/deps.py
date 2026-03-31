from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import TokenError, decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── DB shorthand ──────────────────────────────────────────────────────────────
DBSession = Depends(get_db)


# ── Token extraction ──────────────────────────────────────────────────────────
def _get_token_payload(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return decode_token(token, expected_type="access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Current user ──────────────────────────────────────────────────────────────
def get_current_user(
    payload: dict = Depends(_get_token_payload),
    db: Session = Depends(get_db),
):
    """
    Inyecta el usuario autenticado en el endpoint.
    Descomenta la importación del modelo cuando exista app/models/user.py
    """
    from app.repositories.user_repo import UserRepository  # lazy import
    from app.models.user import User                        # lazy import

    user_id: str = payload.get("sub")
    user: User | None = UserRepository(db).get_by_id(int(user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def get_current_superuser(current_user=Depends(get_current_active_user)):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


# ── Pagination ────────────────────────────────────────────────────────────────
class PaginationParams:
    def __init__(self, skip: int = 0, limit: int = 20):
        if limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit cannot exceed 100",
            )
        self.skip = skip
        self.limit = limit


Pagination = Depends(PaginationParams)
