from __future__ import annotations

import os

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _secret_key() -> str:
    return os.getenv("DASHBOARD_JWT_SECRET") or os.getenv("SECRET_KEY") or "dashboard-dev-secret"


def _decode_bearer_token(token: str) -> dict:
    try:
        return jwt.decode(token, _secret_key(), algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid dashboard token") from exc


def _extract_bearer_token(request: Request) -> str:
    authorization = str(request.headers.get("authorization") or "").strip()
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return token


def _normalize_user(request: Request) -> dict:
    state_user = getattr(getattr(request, "state", None), "user", None)
    if isinstance(state_user, dict):
        return {
            "id": state_user.get("id") or state_user.get("sub") or "anonymous",
            "allowed_apps": list(state_user.get("allowed_apps") or []),
            "allowed_screens": list(state_user.get("allowed_screens") or []),
            "is_superadmin": bool(state_user.get("is_superadmin")),
        }
    if state_user is not None:
        return {
            "id": getattr(state_user, "id", None) or getattr(state_user, "sub", None) or "anonymous",
            "allowed_apps": list(getattr(state_user, "allowed_apps", []) or []),
            "allowed_screens": list(getattr(state_user, "allowed_screens", []) or []),
            "is_superadmin": bool(getattr(state_user, "is_superadmin", False)),
        }
    return {"id": "anonymous", "allowed_apps": [], "allowed_screens": [], "is_superadmin": False}


def verify_dashboard_password(password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(password, hashed_password)
    except Exception:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False


def build_dashboard_security_context(request) -> dict:
    user = _normalize_user(request)
    if "authorization" in request.headers:
        token_payload = _decode_bearer_token(_extract_bearer_token(request))
        user["id"] = token_payload.get("sub") or user["id"]
        user["allowed_apps"] = list(token_payload.get("allowed_apps") or user["allowed_apps"])
        user["allowed_screens"] = list(token_payload.get("allowed_screens") or user["allowed_screens"])
        user["is_superadmin"] = bool(token_payload.get("is_superadmin", user["is_superadmin"]))

    return {
        "user_id": str(user["id"]),
        "is_superadmin": bool(user["is_superadmin"]),
        "user_app_access": list(user["allowed_apps"]),
        "user_screen_access": list(user["allowed_screens"]),
    }


def require_dashboard_user(request: Request) -> dict:
    context = build_dashboard_security_context(request)
    if context["user_id"] == "anonymous" and "authorization" in request.headers:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized dashboard user")
    return context


def require_dashboard_page_access(request, module: dict | None) -> dict:
    security = require_dashboard_user(request)
    if not module or not bool(module.get("enabled")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard page not found")
    if security["is_superadmin"]:
        return security
    app_access_name = str(module.get("app_access_name") or module.get("label") or "").strip()
    screen_access_name = str(module.get("screen_access_name") or module.get("key") or module.get("route") or "").strip()
    if app_access_name and not user_has_app_access(security, app_access_name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard page not found")
    if screen_access_name and not user_has_screen_access(security, screen_access_name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard page not found")
    return security


def user_has_app_access(user: dict, app_key: str) -> bool:
    return bool(user.get("is_superadmin")) or app_key in set(user.get("user_app_access") or [])


def user_has_screen_access(user: dict, screen_key: str) -> bool:
    return bool(user.get("is_superadmin")) or screen_key in set(user.get("user_screen_access") or [])


def validate_catalog_item(item_key: str, catalog: list[dict]) -> dict:
    for item in catalog:
        key = str(item.get("key") or item.get("route") or "").strip()
        if key == item_key:
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard catalog item not found")


def can_view_module(request, module: dict) -> bool:
    route = str(module.get("route") or "").strip()
    if not route or route == "/mi-tablero" or not bool(module.get("enabled")):
        return False
    security = build_dashboard_security_context(request)
    app_access_name = str(module.get("app_access_name") or module.get("label") or "").strip()
    screen_access_name = str(module.get("screen_access_name") or module.get("key") or route).strip()
    if security["is_superadmin"]:
        return True
    if app_access_name and not user_has_app_access(security, app_access_name):
        return False
    return user_has_screen_access(security, screen_access_name)
