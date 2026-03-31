from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Token helpers ─────────────────────────────────────────────────────────────
def _build_token(subject: Any, extra: dict, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        **extra,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: Any, extra: dict | None = None) -> str:
    return _build_token(
        subject=subject,
        extra={"type": "access", **(extra or {})},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: Any) -> str:
    return _build_token(
        subject=subject,
        extra={"type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


# ── Token decoding ────────────────────────────────────────────────────────────
class TokenError(Exception):
    """Raised when a token is invalid or expired."""


def decode_token(token: str, expected_type: str = "access") -> dict:
    """
    Decode and validate a JWT.

    Returns the full payload dict on success.
    Raises TokenError on any validation failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise TokenError(f"Invalid token: {exc}") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected token type '{expected_type}', got '{payload.get('type')}'")

    sub = payload.get("sub")
    if sub is None:
        raise TokenError("Token missing 'sub' claim")

    return payload


def get_subject(token: str, expected_type: str = "access") -> str:
    """Shortcut — returns only the subject (user id) from a valid token."""
    return decode_token(token, expected_type)["sub"]
