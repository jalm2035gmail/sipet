from __future__ import annotations

from fastapi_modulo.modulos.web.schemas import (
    BackendSettingsSchema,
    LoginFormSchema,
    PasskeyAuthOptionsSchema,
    PasskeyAuthResponseSchema,
    PasskeyAuthVerifySchema,
    PasskeyCredentialResponseSchema,
    PasskeyRegisterOptionsSchema,
    PasskeyRegisterVerifySchema,
    PasskeyRevokeSchema,
    schema_to_dict,
)

__all__ = [
    "BackendSettingsSchema",
    "LoginFormSchema",
    "PasskeyAuthOptionsSchema",
    "PasskeyAuthResponseSchema",
    "PasskeyAuthVerifySchema",
    "PasskeyCredentialResponseSchema",
    "PasskeyRegisterOptionsSchema",
    "PasskeyRegisterVerifySchema",
    "PasskeyRevokeSchema",
    "schema_to_dict",
]
