from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, field_validator

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ESTADOS_VALIDOS = {"activa", "inactiva"}


def _validate_color(v: Optional[str]) -> Optional[str]:
    if v is not None and not _HEX_RE.match(v.strip()):
        raise ValueError("color_primario debe ser un valor HEX válido (ej. #0f172a o #fff)")
    return v.strip() if v else v


def _validate_email(v: Optional[str]) -> Optional[str]:
    if v is not None and v.strip() and not _EMAIL_RE.match(v.strip()):
        raise ValueError("email_contacto no tiene un formato válido")
    return v.strip() if v else v


def _validate_estado(v: Optional[str]) -> Optional[str]:
    if v is not None and v not in _ESTADOS_VALIDOS:
        raise ValueError("estado debe ser 'activa' o 'inactiva'")
    return v


class EmpresaCreate(BaseModel):
    codigo: str
    nombre: str
    tenant_id: str
    descripcion: Optional[str] = None
    email_contacto: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    rfc: Optional[str] = None
    color_primario: Optional[str] = "#0f172a"
    estado: Optional[str] = "activa"

    @field_validator("codigo")
    @classmethod
    def codigo_slug(cls, v: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9_-]", "", v.strip().upper())
        if not clean:
            raise ValueError("El código solo puede contener letras, números, guiones y guiones bajos")
        return clean

    @field_validator("tenant_id")
    @classmethod
    def tenant_slug(cls, v: str) -> str:
        clean = re.sub(r"[^a-z0-9._-]", "-", v.strip().lower()).strip("-._")
        if not clean:
            raise ValueError("tenant_id inválido")
        return clean

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, v: Optional[str]) -> Optional[str]:
        return _validate_estado(v)

    @field_validator("color_primario")
    @classmethod
    def color_hex_valido(cls, v: Optional[str]) -> Optional[str]:
        return _validate_color(v)

    @field_validator("email_contacto")
    @classmethod
    def email_valido(cls, v: Optional[str]) -> Optional[str]:
        return _validate_email(v)


class EmpresaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    email_contacto: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    rfc: Optional[str] = None
    color_primario: Optional[str] = None
    estado: Optional[str] = None

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, v: Optional[str]) -> Optional[str]:
        return _validate_estado(v)

    @field_validator("color_primario")
    @classmethod
    def color_hex_valido(cls, v: Optional[str]) -> Optional[str]:
        return _validate_color(v)

    @field_validator("email_contacto")
    @classmethod
    def email_valido(cls, v: Optional[str]) -> Optional[str]:
        return _validate_email(v)
