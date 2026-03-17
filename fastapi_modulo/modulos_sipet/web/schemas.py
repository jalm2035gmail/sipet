from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class LoginFormSchema(BaseModel):
    usuario: str = Field(default="")
    contrasena: str = Field(default="")
    codigo_autenticador: Optional[str] = None


class PasskeyRegisterOptionsSchema(BaseModel):
    usuario: str = Field(default="")
    contrasena: str = Field(default="")


class PasskeyCredentialResponseSchema(BaseModel):
    clientDataJSON: str = Field(default="")
    publicKey: str = Field(default="")
    signCount: int = Field(default=0)


class PasskeyRegisterVerifySchema(BaseModel):
    id: str = Field(default="")
    response: PasskeyCredentialResponseSchema = Field(default_factory=PasskeyCredentialResponseSchema)


class PasskeyAuthOptionsSchema(BaseModel):
    usuario: str = Field(default="")


class PasskeyAuthResponseSchema(BaseModel):
    clientDataJSON: str = Field(default="")
    signCount: int = Field(default=0)


class PasskeyAuthVerifySchema(BaseModel):
    id: str = Field(default="")
    response: PasskeyAuthResponseSchema = Field(default_factory=PasskeyAuthResponseSchema)


class PasskeyRevokeSchema(BaseModel):
    credential_id: str = Field(default="")


class BackendSettingsSchema(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


def schema_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
