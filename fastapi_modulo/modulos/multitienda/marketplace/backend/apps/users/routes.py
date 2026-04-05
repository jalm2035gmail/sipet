from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text, func, or_, select, text
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users import models, schemas
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import SessionLocal
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional
from threading import Lock
from types import SimpleNamespace
import bcrypt
import os

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
security = HTTPBearer()

router = APIRouter()
_NOTIFICATIONS_METADATA = MetaData()
_USER_NOTIFICATIONS_TABLE = Table(
    "user_notifications",
    _NOTIFICATIONS_METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("title", String(120), nullable=False),
    Column("message", Text, nullable=False),
    Column("is_read", Integer, nullable=False, server_default=text("0")),
    Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
)

MAX_FREE_ATTEMPTS = 3
INITIAL_LOCK_SECONDS = 5 * 60
_LOGIN_ATTEMPTS: dict[str, dict] = {}
_LOGIN_ATTEMPTS_LOCK = Lock()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False

def get_password_hash(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _get_attempt_state(key: str) -> dict:
    with _LOGIN_ATTEMPTS_LOCK:
        state = _LOGIN_ATTEMPTS.get(key)
        if not state:
            state = {
                "failed_count": 0,
                "lock_until": None,
                "backoff_seconds": INITIAL_LOCK_SECONDS,
            }
            _LOGIN_ATTEMPTS[key] = state
        return state


def _is_locked(key: str) -> int:
    state = _get_attempt_state(key)
    lock_until = state.get("lock_until")
    if not lock_until:
        return 0
    remaining = int((lock_until - datetime.utcnow()).total_seconds())
    return remaining if remaining > 0 else 0


def _register_failed_attempt(key: str) -> int:
    with _LOGIN_ATTEMPTS_LOCK:
        state = _LOGIN_ATTEMPTS.get(key) or {
            "failed_count": 0,
            "lock_until": None,
            "backoff_seconds": INITIAL_LOCK_SECONDS,
        }
        state["failed_count"] += 1
        lock_seconds = 0
        if state["failed_count"] > MAX_FREE_ATTEMPTS:
            lock_seconds = int(state.get("backoff_seconds", INITIAL_LOCK_SECONDS))
            state["lock_until"] = datetime.utcnow() + timedelta(seconds=lock_seconds)
            state["backoff_seconds"] = lock_seconds * 2
        _LOGIN_ATTEMPTS[key] = state
        return lock_seconds


def _reset_attempts(*keys: str) -> None:
    with _LOGIN_ATTEMPTS_LOCK:
        for key in keys:
            if key in _LOGIN_ATTEMPTS:
                del _LOGIN_ATTEMPTS[key]

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _find_user_by_identifier(db: Session, identifier: str):
    stmt = select(models.User.__table__).where(
        or_(
            models.User.__table__.c.username == identifier,
            models.User.__table__.c.email == identifier,
        )
    )
    return db.execute(stmt).mappings().first()


def _as_user_namespace(user_row) -> SimpleNamespace:
    raw_user_type = user_row["user_type"]
    normalized_user_type = raw_user_type.value if hasattr(raw_user_type, "value") else str(raw_user_type)
    return SimpleNamespace(
        id=user_row["id"],
        username=user_row["username"],
        email=user_row["email"],
        user_type=normalized_user_type,
        vendor_profile_id=user_row.get("vendor_profile_id"),
        two_factor_enabled=bool(user_row.get("two_factor_enabled", False)),
    )


def _ensure_notifications_table(db: Session) -> None:
    bind = db.get_bind()
    if bind is None:
        raise RuntimeError("No hay engine asociado a la sesión actual.")
    _USER_NOTIFICATIONS_TABLE.create(bind=bind, checkfirst=True)
    db.commit()


def _coerce_limit(value) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _extract_store_limits(store: VendorStore) -> tuple[int, int]:
    theme = store.store_theme if isinstance(store.store_theme, dict) else {}
    return (
        _coerce_limit(theme.get("max_internal_users")),
        _coerce_limit(theme.get("max_portal_users")),
    )


def _enforce_store_user_limit(db: Session, user: schemas.UserCreate) -> None:
    if not user.vendor_profile_id:
        return
    store = db.query(VendorStore).filter(VendorStore.id == int(user.vendor_profile_id)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    max_internal_users, max_portal_users = _extract_store_limits(store)
    if user.user_type == schemas.UserType.vendor and max_internal_users > 0:
        internal_count = db.query(models.User).filter(
            models.User.vendor_profile_id == int(store.id),
            models.User.user_type == models.UserType.vendor,
        ).count()
        if internal_count >= max_internal_users:
            raise HTTPException(status_code=422, detail="La tienda alcanzo el limite de usuarios internos.")
    if user.user_type == schemas.UserType.customer and max_portal_users > 0:
        portal_count = db.query(models.User).filter(
            models.User.vendor_profile_id == int(store.id),
            models.User.user_type == models.UserType.customer,
        ).count()
        if portal_count >= max_portal_users:
            raise HTTPException(status_code=422, detail="La tienda alcanzo el limite de usuarios de portal.")

@router.post("/register", response_model=schemas.UserRead)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter((models.User.username == user.username) | (models.User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    _enforce_store_user_limit(db, user)
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        user_type=user.user_type,
        vendor_profile_id=user.vendor_profile_id,
        two_factor_enabled=user.two_factor_enabled,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    identifier = form_data.username.strip()
    user_row = _find_user_by_identifier(db, identifier)
    identifier_key = f"id:{identifier.lower()}"
    user_key = f"user:{user_row['id']}" if user_row else identifier_key

    remaining_lock_seconds = _is_locked(user_key)
    if remaining_lock_seconds > 0:
        wait_minutes = max(1, int((remaining_lock_seconds + 59) / 60))
        raise HTTPException(
            status_code=429,
            detail=f"Datos incorrectos, intente nuevamente. Debe esperar {wait_minutes} minutos antes de intentar de nuevo.",
        )

    if not user_row or not verify_password(form_data.password, user_row["hashed_password"]):
        applied_lock_seconds = _register_failed_attempt(user_key)
        if applied_lock_seconds > 0:
            wait_minutes = max(1, int((applied_lock_seconds + 59) / 60))
            raise HTTPException(
                status_code=429,
                detail=f"Datos incorrectos, intente nuevamente. Debe esperar {wait_minutes} minutos antes de intentar de nuevo.",
            )
        raise HTTPException(status_code=401, detail="Datos incorrectos, intente nuevamente.")

    if user_row:
        _reset_attempts(
            user_key,
            f"id:{user_row['username'].lower()}",
            f"id:{user_row['email'].lower()}",
            identifier_key,
        )
    raw_user_type = user_row["user_type"]
    user_type = raw_user_type.value if hasattr(raw_user_type, "value") else str(raw_user_type)
    access_token = create_access_token(
        data={"sub": user_row["username"], "user_type": user_type}
    )
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    stmt = select(models.User.__table__).where(models.User.__table__.c.username == username)
    user_row = db.execute(stmt).mappings().first()
    if user_row is None:
        raise credentials_exception
    return _as_user_namespace(user_row)

def require_role(required_role: str):
    def role_checker(user: models.User = Depends(get_current_user)):
        user_type = user.user_type.value if hasattr(user.user_type, "value") else str(user.user_type)
        if user_type != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker


def require_any_role(*required_roles: str):
    """Accepts users whose user_type is any of the given roles."""
    roles_set = set(required_roles)

    def role_checker(user: models.User = Depends(get_current_user)):
        user_type = user.user_type.value if hasattr(user.user_type, "value") else str(user.user_type)
        if user_type not in roles_set:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return role_checker


@router.get("/system-users")
def list_system_users(db: Session = Depends(get_db)):
    rows = db.execute(
        select(
            models.User.__table__.c.id,
            models.User.__table__.c.username,
            models.User.__table__.c.email,
            models.User.__table__.c.user_type,
        ).order_by(models.User.__table__.c.username.asc())
    ).mappings().all()
    items = []
    for row in rows:
        raw_type = row["user_type"]
        user_type = raw_type.value if hasattr(raw_type, "value") else str(raw_type)
        items.append(
            {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "user_type": user_type,
            }
        )
    return items


@router.get("/notifications/unread-count")
def notifications_unread_count(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_notifications_table(db)
    unread = db.execute(
        text(
            """
            SELECT COUNT(*) AS unread_count
            FROM user_notifications
            WHERE user_id = :user_id AND is_read = 0
            """
        ),
        {"user_id": current_user.id},
    ).scalar_one()
    return {"unread_count": int(unread or 0)}


@router.get("/notifications")
def list_notifications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_notifications_table(db)
    rows = db.execute(
        text(
            """
            SELECT id, title, message, is_read, created_at
            FROM user_notifications
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 50
            """
        ),
        {"user_id": current_user.id},
    ).mappings().all()
    return {"items": [dict(row) for row in rows]}


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_notifications_table(db)
    result = db.execute(
        text(
            """
            UPDATE user_notifications
            SET is_read = 1
            WHERE id = :notification_id AND user_id = :user_id
            """
        ),
        {"notification_id": notification_id, "user_id": current_user.id},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}


@router.post("/notifications")
def create_notification(
    payload: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_notifications_table(db)
    title = str(payload.get("title") or "").strip()
    message = str(payload.get("message") or "").strip()
    if not title or not message:
        raise HTTPException(status_code=400, detail="title and message are required")

    db.execute(
        text(
            """
            INSERT INTO user_notifications (user_id, title, message, is_read)
            VALUES (:user_id, :title, :message, 0)
            """
        ),
        {"user_id": current_user.id, "title": title, "message": message},
    )
    db.commit()
    return {"ok": True}

@router.get("/me", response_model=schemas.UserRead)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.get("/admin-only")
def admin_only(user: models.User = Depends(require_role("superadmin"))):
    return {"msg": f"Hello, {user.username}. You are a superadmin."}

@router.get("/vendor-only")
def vendor_only(user: models.User = Depends(require_role("vendor"))):
    return {"msg": f"Hello, {user.username}. You are a vendor."}

@router.get("/customer-only")
def customer_only(user: models.User = Depends(require_role("customer"))):
    return {"msg": f"Hello, {user.username}. You are a customer."}
