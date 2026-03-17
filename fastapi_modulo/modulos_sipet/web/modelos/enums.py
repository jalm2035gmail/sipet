from __future__ import annotations

from enum import Enum


class AuthEventType(str, Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    SESSION_CREATED = "session_created"
    PASSKEY_REGISTERED = "passkey_registered"
    PASSKEY_REVOKED = "passkey_revoked"
    PASSKEY_AUTH_SUCCESS = "passkey_auth_success"
    SCREEN_VIEW = "screen_view"


class MfaChallengeType(str, Enum):
    MFA_GATE = "mfa_gate"
    REGISTER = "register"
    AUTH = "auth"


class PreferenceTheme(str, Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class SidebarMode(str, Enum):
    EXPANDED = "expanded"
    COLLAPSED = "collapsed"
