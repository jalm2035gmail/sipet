"""Schemas Pydantic para validación del módulo personalizacion."""
from __future__ import annotations

import re
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator

from fastapi_modulo.modulos_sipet.personalizacion.modelos.theme_system import (
    MAIN_THEME_KEYS,
    normalize_hex_color,
)

# ── Tipo anotado reutilizable ─────────────────────────────────────────────────
HexColor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]

ALLOWED_EXTENSIONS: dict[str, frozenset[str]] = {
    "favicon":      frozenset({".png", ".ico", ".svg"}),
    "logo_empresa": frozenset({".png", ".jpg", ".jpeg", ".svg", ".webp"}),
    "logo_usuario": frozenset({".png", ".jpg", ".jpeg", ".svg", ".webp"}),
    "svg_fondo":    frozenset({".svg"}),
    "svg_defecto":  frozenset({".svg"}),
}

MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB


# ── Schemas de colores ────────────────────────────────────────────────────────

class ColorPayloadSchema(BaseModel):
    """
    Valida los 5 colores MAIN del tema institucional para el form multipart.
    Acepta #RGB (shorthand) y lo expande a #RRGGBB.
    Los campos None se ignoran — no sobreescriben el valor guardado en DB.
    """
    navbar_bg:      Optional[str] = None
    sidebar_top:    Optional[str] = None
    sidebar_bottom: Optional[str] = None
    field_color:    Optional[str] = None
    button_bg:      Optional[str] = None

    @field_validator(
        "navbar_bg", "sidebar_top", "sidebar_bottom",
        "field_color", "button_bg",
        mode="before",
    )
    @classmethod
    def validate_hex(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        raw = str(v or "").strip()
        if not raw:
            return None
        normalized = normalize_hex_color(raw, "")
        if not normalized:
            raise ValueError(
                f"Color inválido: '{raw}'. "
                "Usa formato hexadecimal #RRGGBB o #RGB."
            )
        return normalized

    def to_theme_dict(self) -> dict[str, str]:
        """Devuelve solo los colores no-None con las claves CSS del tema."""
        mapping: dict[str, Optional[str]] = {
            "navbar-bg":      self.navbar_bg,
            "sidebar-top":    self.sidebar_top,
            "sidebar-bottom": self.sidebar_bottom,
            "field-color":    self.field_color,
            "button-bg":      self.button_bg,
        }
        return {k: v for k, v in mapping.items() if v is not None}

    def has_any(self) -> bool:
        """True si al menos un color fue enviado."""
        return any(
            v is not None
            for v in (
                self.navbar_bg, self.sidebar_top, self.sidebar_bottom,
                self.field_color, self.button_bg,
            )
        )


class FullColorPayloadSchema(BaseModel):
    """
    Valida un payload JSON con los 5 colores MAIN completos (todos requeridos).
    Usado en el endpoint POST /guardar-colores que recibe JSON directo.
    """
    navbar_bg:      str
    sidebar_top:    str
    sidebar_bottom: str
    field_color:    str
    button_bg:      str

    @field_validator(
        "navbar_bg", "sidebar_top", "sidebar_bottom",
        "field_color", "button_bg",
        mode="before",
    )
    @classmethod
    def validate_hex(cls, v: object) -> str:
        raw = str(v or "").strip()
        if not raw:
            raise ValueError("El campo de color no puede estar vacío.")
        normalized = normalize_hex_color(raw, "")
        if not normalized:
            raise ValueError(
                f"Color inválido: '{raw}'. "
                "Usa formato hexadecimal #RRGGBB o #RGB."
            )
        return normalized

    def to_theme_dict(self) -> dict[str, str]:
        return {
            "navbar-bg":      self.navbar_bg,
            "sidebar-top":    self.sidebar_top,
            "sidebar-bottom": self.sidebar_bottom,
            "field-color":    self.field_color,
            "button-bg":      self.button_bg,
        }

    @classmethod
    def from_raw_dict(cls, data: dict) -> "FullColorPayloadSchema":
        """
        Construye el schema desde un dict con claves en formato CSS
        (ej. 'navbar-bg') en lugar de snake_case del modelo.
        """
        return cls(
            navbar_bg=data.get("navbar-bg", ""),
            sidebar_top=data.get("sidebar-top", ""),
            sidebar_bottom=data.get("sidebar-bottom", ""),
            field_color=data.get("field-color", ""),
            button_bg=data.get("button-bg", ""),
        )


# ── Schemas de assets ─────────────────────────────────────────────────────────

class RemoveAssetsSchema(BaseModel):
    """
    Valida los flags de remoción de assets del formulario multipart.
    Acepta '1'/'0' (strings de form data) además de bool.
    """
    remove_favicon:      bool = False
    remove_logo_empresa: bool = False
    remove_logo_usuario: bool = False
    remove_svg_fondo:    bool = False
    remove_svg_defecto:  bool = False

    @field_validator(
        "remove_favicon", "remove_logo_empresa", "remove_logo_usuario",
        "remove_svg_fondo", "remove_svg_defecto",
        mode="before",
    )
    @classmethod
    def parse_flag(cls, v: object) -> bool:
        if isinstance(v, str):
            return v.strip() == "1"
        return bool(v)

    def to_dict(self) -> dict[str, bool]:
        """Devuelve dict con las claves de asset (sin prefijo 'remove_')."""
        return {
            "favicon":      self.remove_favicon,
            "logo_empresa": self.remove_logo_empresa,
            "logo_usuario": self.remove_logo_usuario,
            "svg_fondo":    self.remove_svg_fondo,
            "svg_defecto":  self.remove_svg_defecto,
        }

    def any_flagged(self) -> bool:
        """True si al menos un asset fue marcado para eliminar."""
        return any(self.to_dict().values())


class AssetUploadMetaSchema(BaseModel):
    """
    Metadatos de un asset procesado y guardado.
    Se incluye en asset_details de la respuesta de guardar_personalizacion.
    """
    field:      str
    filename:   str
    ext:        str
    size_bytes: int
    width:      Optional[int] = None
    height:     Optional[int] = None
    url:        str = ""

    @field_validator("ext")
    @classmethod
    def validate_ext(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not cleaned.startswith("."):
            cleaned = f".{cleaned}"
        return cleaned

    @field_validator("size_bytes")
    @classmethod
    def validate_size(cls, v: int) -> int:
        if v < 0:
            raise ValueError("size_bytes no puede ser negativo.")
        if v > MAX_FILE_BYTES:
            raise ValueError(
                f"El archivo supera el tamaño máximo de "
                f"{MAX_FILE_BYTES // (1024 * 1024)} MB."
            )
        return v


class AssetStateSchema(BaseModel):
    """Estado de un asset individual en el sistema de uploads."""
    filename:         str  = ""
    url:              str  = ""
    exists:           bool = False
    default_filename: str  = ""
    has_default:      bool = False


# ── Schemas de respuesta ──────────────────────────────────────────────────────

class ColoresResponseSchema(BaseModel):
    """Respuesta estándar del endpoint GET/POST /guardar-colores."""
    success: bool
    data:    Optional[dict[str, str]] = None
    error:   Optional[str] = None


class GuardarPersonalizacionResponseSchema(BaseModel):
    """Respuesta del endpoint POST /personalizar/guardar."""
    ok:            bool
    updated:       list[str]           = Field(default_factory=list)
    removed:       list[str]           = Field(default_factory=list)
    asset_details: dict[str, dict]     = Field(default_factory=dict)
    assets:        dict[str, dict]     = Field(default_factory=dict)
    colors:        dict[str, str]      = Field(default_factory=dict)
    error:         Optional[str]       = None


class PersonalizarEstadoResponseSchema(BaseModel):
    """Respuesta del endpoint GET /personalizar/estado."""
    ok:     bool
    assets: dict[str, AssetStateSchema] = Field(default_factory=dict)


class RestablecerAssetsResponseSchema(BaseModel):
    """Respuesta del endpoint POST /personalizar/restablecer-assets."""
    ok:       bool
    restored: list[str]      = Field(default_factory=list)
    assets:   dict[str, dict] = Field(default_factory=dict)


# ── Schema de rol ─────────────────────────────────────────────────────────────

class RolCreateSchema(BaseModel):
    """Valida los datos al crear o editar un rol."""
    nombre:      str = Field(..., min_length=1, max_length=80, strip_whitespace=True)
    descripcion: str = Field(default="", max_length=255, strip_whitespace=True)

    @field_validator("nombre")
    @classmethod
    def sanitize_nombre(cls, v: str) -> str:
        """
        Normaliza el nombre del rol a snake_case lowercase.
        Ej: 'Super Admin' → 'super_admin'
        """
        cleaned = re.sub(r"\s+", "_", v.strip().lower())
        cleaned = re.sub(r"[^a-z0-9_]", "", cleaned).strip("_")
        if not cleaned:
            raise ValueError("El nombre del rol no puede estar vacío tras sanitizar.")
        return cleaned


class RolResponseSchema(BaseModel):
    """Representación de un rol para responses JSON."""
    id:          int
    nombre:      str
    descripcion: str = ""

    model_config = {"from_attributes": True}
    