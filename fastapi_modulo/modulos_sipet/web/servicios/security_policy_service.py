from __future__ import annotations

import json
import os
from typing import Any

from fastapi_modulo.modulos_sipet.web.servicios.access_service import normalize_role_name
from fastapi_modulo.modulos_sipet.web.servicios.session_service import normalize_tenant_id

DEFAULT_MFA_POLICY = {
    "roles": {
        "autoridades": True,
    },
    "tenants": {},
    "users": {},
}
DEFAULT_SESSION_POLICY = {
    "mode": "allow_multiple",
    "max_sessions": 5,
}


def _load_json_env(env_name: str, default: dict[str, Any]) -> dict[str, Any]:
    raw = (os.environ.get(env_name) or "").strip()
    if not raw:
        return default.copy()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return default.copy()
    if not isinstance(payload, dict):
        return default.copy()
    merged = default.copy()
    merged.update(payload)
    return merged


def mfa_policy() -> dict[str, Any]:
    return _load_json_env("WEB_MFA_POLICY_JSON", DEFAULT_MFA_POLICY)


def session_policy() -> dict[str, Any]:
    policy = _load_json_env("WEB_SESSION_POLICY_JSON", DEFAULT_SESSION_POLICY)
    policy["mode"] = str(policy.get("mode") or DEFAULT_SESSION_POLICY["mode"]).strip().lower()
    try:
        policy["max_sessions"] = max(1, int(policy.get("max_sessions") or DEFAULT_SESSION_POLICY["max_sessions"]))
    except (TypeError, ValueError):
        policy["max_sessions"] = DEFAULT_SESSION_POLICY["max_sessions"]
    return policy


def is_mfa_required(*, role_name: str, tenant_id: str = "", user_id: int | None = None, username: str = "") -> bool:
    policy = mfa_policy()
    normalized_role = normalize_role_name(role_name)
    normalized_tenant = normalize_tenant_id(tenant_id)
    resolved_username = str(username or "").strip().lower()
    if user_id is not None and bool((policy.get("users") or {}).get(str(int(user_id)))):
        return True
    if resolved_username and bool((policy.get("users") or {}).get(resolved_username)):
        return True
    if bool((policy.get("tenants") or {}).get(normalized_tenant)):
        return True
    return bool((policy.get("roles") or {}).get(normalized_role))


def should_revoke_other_sessions(*, role_name: str = "", tenant_id: str = "", user_id: int | None = None) -> bool:
    policy = session_policy()
    mode = str(policy.get("mode") or "").strip().lower()
    if mode == "single_session":
        return True
    forced_by_tenant = bool((policy.get("tenant_single_session") or {}).get(normalize_tenant_id(tenant_id)))
    forced_by_user = bool((policy.get("user_single_session") or {}).get(str(int(user_id)) if user_id is not None else ""))
    forced_by_role = bool((policy.get("role_single_session") or {}).get(normalize_role_name(role_name)))
    return forced_by_tenant or forced_by_user or forced_by_role


def max_concurrent_sessions(*, role_name: str = "", tenant_id: str = "", user_id: int | None = None) -> int:
    policy = session_policy()
    role_limits = policy.get("role_max_sessions") or {}
    tenant_limits = policy.get("tenant_max_sessions") or {}
    user_limits = policy.get("user_max_sessions") or {}
    resolved = user_limits.get(str(int(user_id)) if user_id is not None else "")
    if resolved is None:
        resolved = tenant_limits.get(normalize_tenant_id(tenant_id))
    if resolved is None:
        resolved = role_limits.get(normalize_role_name(role_name))
    if resolved is None:
        resolved = policy.get("max_sessions")
    try:
        return max(1, int(resolved or DEFAULT_SESSION_POLICY["max_sessions"]))
    except (TypeError, ValueError):
        return DEFAULT_SESSION_POLICY["max_sessions"]
