"""
modelos/frontend_schemas.py
─────────────────────────────────────────────────────────────────────────────
Schemas Pydantic para validación de entrada/salida del módulo frontend.

Uso en controladores:
    from fastapi_modulo.modulos.frontend.modelos.frontend_schemas import (
        PagePayload, ContactPayload, TasaItem, TasaListPayload,
        BrandPayload, GalleryDeleteResponse, PageActionEnum,
    )
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — ENUMS
# ══════════════════════════════════════════════════════════════════════════════

class PageStatusEnum(str, Enum):
    draft     = "draft"
    published = "published"


class PageActionEnum(str, Enum):
    upsert = "upsert"
    delete = "delete"


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — PÁGINAS
# ══════════════════════════════════════════════════════════════════════════════

class PageMetaSchema(BaseModel):
    """SEO y Open Graph de una página."""
    title:       Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=300)
    og_image:    Optional[str] = Field(default=None, max_length=500)

    model_config = {"extra": "allow"}   # permite claves futuras sin romper


class PagePayload(BaseModel):
    """
    Payload para crear o actualizar una página desde el builder.
    También acepta action='delete' para eliminar por id.
    """
    id:       Optional[str]       = None
    action:   PageActionEnum      = PageActionEnum.upsert
    title:    str                 = Field(default="Sin título", min_length=1, max_length=255)
    slug:     Optional[str]       = Field(default=None, max_length=120)
    status:   PageStatusEnum      = PageStatusEnum.draft
    is_home:  bool                = False
    gjs_html: str                 = ""
    gjs_css:  str                 = ""
    blocks:   List[Any]           = []
    meta:     PageMetaSchema      = Field(default_factory=PageMetaSchema)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: Any) -> str:
        return str(v or "Sin título").strip()

    @field_validator("slug", mode="before")
    @classmethod
    def build_slug(cls, v: Any, info: Any) -> str:
        # Toma el slug proporcionado o deriva del título
        raw = str(v or "").strip().lower()
        if not raw:
            title = str((info.data or {}).get("title") or "pagina").strip().lower()
            raw = title
        # Reemplaza cualquier caracter no alfanumérico/guion por guion
        slug = re.sub(r"[^a-z0-9\-]+", "-", raw).strip("-")
        return slug or "pagina"

    @field_validator("gjs_html", "gjs_css", mode="before")
    @classmethod
    def coerce_str(cls, v: Any) -> str:
        return str(v or "")

    @field_validator("blocks", mode="before")
    @classmethod
    def coerce_blocks(cls, v: Any) -> list:
        return v if isinstance(v, list) else []

    @field_validator("meta", mode="before")
    @classmethod
    def coerce_meta(cls, v: Any) -> dict:
        return v if isinstance(v, dict) else {}

    @model_validator(mode="after")
    def check_delete_has_id(self) -> "PagePayload":
        if self.action == PageActionEnum.delete and not self.id:
            raise ValueError("Se requiere 'id' cuando action es 'delete'.")
        return self


class PageResponse(BaseModel):
    """Respuesta de un endpoint que devuelve una sola página."""
    success: bool
    page:    Dict[str, Any]


class PagesListResponse(BaseModel):
    """Respuesta de un endpoint que devuelve la lista completa de páginas."""
    success: bool
    data:    List[Dict[str, Any]]


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — CONTACTO
# ══════════════════════════════════════════════════════════════════════════════

class ContactPayload(BaseModel):
    """
    Payload del formulario de contacto público.
    Valida el formato del email sin depender de paquetes opcionales.
    """
    name:    str = Field(..., min_length=1, max_length=200,
                         description="Nombre completo del remitente")
    email:   str = Field(..., min_length=3, max_length=320, description="Correo electrónico válido")
    message: str = Field(..., min_length=1, max_length=5000,
                         description="Cuerpo del mensaje")

    @field_validator("name", "message", mode="before")
    @classmethod
    def strip_fields(cls, v: Any) -> str:
        return str(v or "").strip()

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: Any) -> str:
        email = str(v or "").strip()
        if not _EMAIL_PATTERN.match(email):
            raise ValueError("Correo electrónico inválido.")
        return email


class ContactMarkReadPayload(BaseModel):
    """Payload para marcar mensajes como leídos en lote."""
    ids: List[str] = Field(..., min_length=1,
                           description="Lista de IDs de contactos a marcar como leídos")


class ContactResponse(BaseModel):
    success: bool
    data:    Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class ContactListResponse(BaseModel):
    success: bool
    data:    List[Dict[str, Any]]


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — TASAS DE INTERÉS
# ══════════════════════════════════════════════════════════════════════════════

class TasaItem(BaseModel):
    """
    Un ítem de tasa de interés.
    'rate' se almacena como str para preservar decimales exactos (ej. '3.50').
    """
    id:    str = Field(..., min_length=1, max_length=60,
                       description="Identificador único tipo slug, ej. 'ahorro_vista'")
    label: str = Field(..., min_length=1, max_length=120,
                       description="Etiqueta visible, ej. 'Ahorro a la vista'")
    rate:  str = Field(..., min_length=1, max_length=20,
                       description="Valor de la tasa como string, ej. '3.50'")
    color: str = Field(default="#3b82f6", max_length=30,
                       description="Color hex para el widget, ej. '#3b82f6'")
    unit:  str = Field(default="% anual", max_length=40,
                       description="Unidad de la tasa, ej. '% anual'")

    @field_validator("id", mode="before")
    @classmethod
    def slugify_id(cls, v: Any) -> str:
        raw = re.sub(r"[^a-z0-9_\-]+", "_", str(v or "").strip().lower()).strip("_")
        if not raw:
            raise ValueError("El id de la tasa no puede estar vacío.")
        return raw

    @field_validator("rate", mode="before")
    @classmethod
    def validate_rate(cls, v: Any) -> str:
        raw = str(v or "").strip()
        try:
            float(raw)   # valida que sea número
        except ValueError:
            raise ValueError(f"'rate' debe ser un número válido, recibido: '{raw}'")
        return raw

    @field_validator("color", mode="before")
    @classmethod
    def validate_color(cls, v: Any) -> str:
        raw = str(v or "#3b82f6").strip()
        if not re.match(r"^#[0-9a-fA-F]{3,8}$", raw):
            raise ValueError(f"'color' debe ser un color hex válido, recibido: '{raw}'")
        return raw


class TasaListPayload(BaseModel):
    """Payload para guardar la lista completa de tasas."""
    tasas: List[TasaItem] = Field(..., min_length=0)


class TasaListResponse(BaseModel):
    success: bool
    data:    List[Dict[str, Any]]


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — BRAND (configuración de marca)
# ══════════════════════════════════════════════════════════════════════════════

class BrandPayload(BaseModel):
    """
    Payload para actualizar la configuración de marca.
    Solo se aceptan valores de tipo str (colores hex, URLs, nombres de fuente).
    Claves no declaradas también son permitidas para extensibilidad.
    """
    logo_url:     Optional[str] = Field(default=None, max_length=500)
    primary:      Optional[str] = Field(default=None, max_length=30)
    secondary:    Optional[str] = Field(default=None, max_length=30)
    accent:       Optional[str] = Field(default=None, max_length=30)
    font_heading: Optional[str] = Field(default=None, max_length=80)
    font_body:    Optional[str] = Field(default=None, max_length=80)

    model_config = {"extra": "allow"}   # acepta claves adicionales como sidebar-bottom, etc.

    @field_validator("primary", "secondary", "accent", mode="before")
    @classmethod
    def validate_color_or_none(cls, v: Any) -> Optional[str]:
        if v is None or str(v).strip() == "":
            return None
        raw = str(v).strip()
        if not re.match(r"^#[0-9a-fA-F]{3,8}$", raw):
            raise ValueError(f"El color debe ser un valor hex válido, recibido: '{raw}'")
        return raw

    def to_store_dict(self) -> Dict[str, str]:
        """
        Devuelve un dict plano {clave: valor} con solo los campos str no nulos,
        incluyendo campos extra (model_config extra='allow').
        Listo para pasar a store.save_brand().
        """
        result: Dict[str, str] = {}
        # Campos declarados
        for field_name, value in self.model_dump(exclude_none=True).items():
            if isinstance(value, str) and value.strip():
                result[field_name] = value.strip()
        # Campos extra capturados por extra='allow'
        for key, value in self.__pydantic_extra__.items():  # type: ignore[union-attr]
            if isinstance(value, str) and value.strip():
                result[key] = value.strip()
        return result


class BrandResponse(BaseModel):
    success: bool
    data:    Dict[str, str]


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — GALERÍA
# ══════════════════════════════════════════════════════════════════════════════

class GalleryItem(BaseModel):
    filename: str
    url:      str


class GalleryListResponse(BaseModel):
    success: bool
    data:    List[GalleryItem]


class GalleryUploadResponse(BaseModel):
    success:  bool
    filename: Optional[str] = None
    url:      Optional[str] = None
    error:    Optional[str] = None


class GalleryDeleteResponse(BaseModel):
    success: bool
    error:   Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — VERSIONES
# ══════════════════════════════════════════════════════════════════════════════

class VersionItem(BaseModel):
    saved_at: str
    title:    str
    status:   str
    gjs_html: str
    gjs_css:  str
    meta:     Dict[str, Any] = {}


class VersionListResponse(BaseModel):
    success: bool
    data:    List[VersionItem]


class VersionRestoreResponse(BaseModel):
    success: bool
    page:    Optional[Dict[str, Any]] = None
    error:   Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — RESPUESTAS GENÉRICAS
# ══════════════════════════════════════════════════════════════════════════════

class SuccessResponse(BaseModel):
    """Respuesta mínima para endpoints que solo confirman éxito."""
    success: bool
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Respuesta de error estándar para todos los endpoints."""
    success: bool = False
    error:   str
    
