from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from fastapi_modulo.modulos.modulo_base.modelos.enums import ModuloBaseEstado


class APIResponse(BaseModel):
    ok: bool
    message: str = ""
    data: dict[str, Any] | list[Any] | None = None


class ModuloBaseCreate(BaseModel):
    nombre: str = Field(min_length=3, max_length=150)
    descripcion: str = Field(default="", max_length=5000)
    estado: ModuloBaseEstado = ModuloBaseEstado.ACTIVO


class ModuloBaseUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=150)
    descripcion: str | None = Field(default=None, max_length=5000)
    estado: ModuloBaseEstado | None = None


class ModuloBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    nombre: str
    descripcion: str | None = None
    estado: str


class ModuloBaseHealthResponse(BaseModel):
    status: str
    module: str
    purpose: str
    route: str


class ModuloBaseResumenResponse(BaseModel):
    tenant_id: str
    total_registros: int
    health: str
    module: str
    sections: list[str]


class APIHealthResponse(APIResponse):
    data: ModuloBaseHealthResponse | None = None


class APIResumenResponse(APIResponse):
    data: ModuloBaseResumenResponse | None = None
