from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from fastapi_modulo.core.db import MAIN


class Colores(MAIN):
    __tablename__ = "colores"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)


class Rol(MAIN):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    descripcion = Column(String)


class Usuario(MAIN):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column("full_name", String)
    usuario = Column("username", String, unique=True, index=True)
    usuario_hash = Column(String, index=True)
    correo = Column("email", String, unique=True, index=True)
    correo_hash = Column(String, index=True)
    celular = Column(String)
    contrasena = Column("password", String)
    departamento = Column(String)
    puesto = Column(String)
    jefe = Column(String)
    jefe_inmediato_id = Column(Integer, ForeignKey("users.id"), index=True)
    coach = Column(String)
    rol_id = Column(Integer)
    imagen = Column(String)
    role = Column(String)
    nivel_acceso = Column(String)
    identidad_institucional = Column(String)
    app_access = Column(String)
    menu_blocks = Column(String)
    conversation_access = Column(String)
    is_employee = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True)
    backendauthn_credential_id = Column(String, unique=True, index=True)
    backendauthn_public_key = Column(String)
    backendauthn_sign_count = Column(Integer, default=0)
    totp_secret = Column(String)
    totp_enabled = Column(Boolean, default=False)
    jefe_inmediato = relationship("Usuario", remote_side=[id], backref="subordinados")


__all__ = ["Colores", "Rol", "Usuario"]
