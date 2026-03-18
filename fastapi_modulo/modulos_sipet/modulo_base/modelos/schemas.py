from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fastapi_modulo.modulos_sipet.modulo_base.modelos.enums import ModuloBaseEstado

ResponseDataT = TypeVar("ResponseDataT")


# ── Funciones de validación reutilizables ─────────────────────────────────────

def _normalize_nombre(value: str | None, *, required: bool = True) -> str | None:
    if value is None:
        return None if not required else value
    normalized = " ".join(value.split())
    if len(normalized) < 3:
        raise ValueError("El nombre debe tener al menos 3 caracteres.")
    return normalized


def _normalize_slug(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower().replace(" ", "-").replace("_", "-")
    if not normalized.replace("-", "").isalnum():
        raise ValueError("El slug solo puede contener letras, numeros y guiones.")
    return normalized


def _normalize_descripcion(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip()


# ── Modelos base ──────────────────────────────────────────────────────────────

class APIErrorDetail(BaseModel):
    type: str
    message: str
    field: str | None = None


class APIResponse(BaseModel, Generic[ResponseDataT]):
    ok: bool
    message: str = ""
    data: ResponseDataT | None = None
    errors: list[APIErrorDetail] = Field(default_factory=list)


class ModuloBaseSchemaModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


# ── Categoría ─────────────────────────────────────────────────────────────────

class ModuloBaseCategoriaBase(ModuloBaseSchemaModel):
    nombre: str = Field(min_length=3, max_length=120)
    slug: str = Field(min_length=3, max_length=120)
    descripcion: str = Field(default="", max_length=1000)

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str) -> str:
        return _normalize_nombre(value)  # type: ignore[return-value]

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        return _normalize_slug(value)  # type: ignore[return-value]

    @field_validator("descripcion")
    @classmethod
    def validate_descripcion(cls, value: str) -> str:
        return _normalize_descripcion(value) or ""


class ModuloBaseCategoriaCreate(ModuloBaseCategoriaBase):
    pass


class ModuloBaseCategoriaUpdate(ModuloBaseSchemaModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    slug: str | None = Field(default=None, min_length=3, max_length=120)
    descripcion: str | None = Field(default=None, max_length=1000)

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str | None) -> str | None:
        return _normalize_nombre(value)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        return _normalize_slug(value)

    @field_validator("descripcion")
    @classmethod
    def validate_descripcion(cls, value: str | None) -> str | None:
        return _normalize_descripcion(value)

    @model_validator(mode="after")
    def validate_non_empty_update(self) -> "ModuloBaseCategoriaUpdate":
        if not self.model_dump(exclude_none=True):
            raise ValueError("Debes enviar al menos un campo para actualizar.")
        return self


class ModuloBaseCategoriaResponse(ModuloBaseSchemaModel):
    id: int
    tenant_id: str
    nombre: str
    slug: str
    descripcion: str = ""


# ── Registro ──────────────────────────────────────────────────────────────────

class ModuloBaseBase(ModuloBaseSchemaModel):
    nombre: str = Field(min_length=3, max_length=150)
    descripcion: str = Field(default="", max_length=5000)
    estado: ModuloBaseEstado = ModuloBaseEstado.ACTIVO
    categoria_id: int = Field(gt=0)

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str) -> str:
        return _normalize_nombre(value)  # type: ignore[return-value]

    @field_validator("descripcion")
    @classmethod
    def validate_descripcion(cls, value: str) -> str:
        return _normalize_descripcion(value) or ""

    @field_validator("categoria_id")
    @classmethod
    def validate_categoria_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("La categoria es obligatoria.")
        return value


class ModuloBaseCreate(ModuloBaseBase):
    pass


class ModuloBaseUpdate(ModuloBaseSchemaModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=150)
    descripcion: str | None = Field(default=None, max_length=5000)
    estado: ModuloBaseEstado | None = None
    categoria_id: int | None = Field(default=None, gt=0)

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str | None) -> str | None:
        return _normalize_nombre(value)

    @field_validator("descripcion")
    @classmethod
    def validate_descripcion(cls, value: str | None) -> str | None:
        return _normalize_descripcion(value)

    @model_validator(mode="after")
    def validate_non_empty_update(self) -> "ModuloBaseUpdate":
        if not self.model_dump(exclude_none=True):
            raise ValueError("Debes enviar al menos un campo para actualizar.")
        return self


# ── Responses ─────────────────────────────────────────────────────────────────

class ModuloBaseResponse(ModuloBaseSchemaModel):
    id: int
    tenant_id: str
    nombre: str
    descripcion: str = ""
    estado: ModuloBaseEstado
    categoria_id: int
    categoria: ModuloBaseCategoriaResponse | None = None
    eliminado: bool = False


class ModuloBaseListResponse(ModuloBaseSchemaModel):
    items: list[ModuloBaseResponse] = Field(default_factory=list)
    total: int = Field(ge=0, default=0)

    @model_validator(mode="after")
    def validate_total(self) -> "ModuloBaseListResponse":
        if self.total < len(self.items):
            raise ValueError("El total no puede ser menor que la cantidad de elementos.")
        return self


class ModuloBaseHealthResponse(ModuloBaseSchemaModel):
    status: str
    module: str
    purpose: str
    route: str


class ModuloBaseResumenResponse(ModuloBaseSchemaModel):
    tenant_id: str
    total_registros: int = Field(ge=0)
    health: str
    module: str
    sections: list[str]

    @field_validator("sections")
    @classmethod
    def validate_sections(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item and item.strip()]
        if not normalized:
            raise ValueError("Debe existir al menos una seccion.")
        return normalized


class ModuloBaseRequestContext(ModuloBaseSchemaModel):
    tenant_id: str = "default"
    user_role: str = "usuario"


# ── Paginación genérica ───────────────────────────────────────────────────────

class PaginatedResponse(ModuloBaseSchemaModel, Generic[ResponseDataT]):
    items: list[ResponseDataT] = Field(default_factory=list)
    total: int = Field(ge=0, default=0)
    skip: int = Field(ge=0, default=0)
    limit: int = Field(ge=1, default=50)

    @model_validator(mode="after")
    def validate_total(self) -> "PaginatedResponse[ResponseDataT]":
        if self.total < len(self.items):
            raise ValueError("El total no puede ser menor que la cantidad de elementos.")
        return self


# ── API envelope responses ────────────────────────────────────────────────────

class APIHealthResponse(APIResponse[ModuloBaseHealthResponse]):
    data: ModuloBaseHealthResponse | None = None


class APIResumenResponse(APIResponse[ModuloBaseResumenResponse]):
    data: ModuloBaseResumenResponse | None = None


class APIModuloBaseItemResponse(APIResponse[ModuloBaseResponse]):
    data: ModuloBaseResponse | None = None


class APIModuloBaseListResponse(APIResponse[ModuloBaseListResponse]):
    data: ModuloBaseListResponse | None = None


class APICategoriaItemResponse(APIResponse[ModuloBaseCategoriaResponse]):
    data: ModuloBaseCategoriaResponse | None = None


class APIErrorResponse(APIResponse[dict[str, Any] | list[Any] | None]):
    data: dict[str, Any] | list[Any] | None = None


__all__ = [
    "APIErrorDetail",
    "APIErrorResponse",
    "APIHealthResponse",
    "APIModuloBaseItemResponse",
    "APIModuloBaseListResponse",
    "APIResumenResponse",
    "APICategoriaItemResponse",
    "APIResponse",
    "ModuloBaseCategoriaBase",
    "ModuloBaseCategoriaCreate",
    "ModuloBaseCategoriaResponse",
    "ModuloBaseCategoriaUpdate",
    "ModuloBaseBase",
    "ModuloBaseCreate",
    "ModuloBaseHealthResponse",
    "ModuloBaseListResponse",
    "ModuloBaseRequestContext",
    "ModuloBaseResumenResponse",
    "ModuloBaseResponse",
    "ModuloBaseSchemaModel",
    "ModuloBaseUpdate",
    "PaginatedResponse",
]
