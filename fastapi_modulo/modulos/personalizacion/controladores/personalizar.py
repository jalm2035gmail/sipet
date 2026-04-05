"""Controlador de personalización visual — personalizar.py"""
from __future__ import annotations

import io
import re
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos.personalizacion.modelos.theme_system import (
    MAIN_THEME_KEYS,
    build_institutional_theme,
    normalize_hex_color,
    DEFAULT_MAIN_THEME,
)
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Colores
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_superadmin
from fastapi_modulo.modulos_sipet.web.servicios.ui_shell_service import get_colores_context

try:
    from PIL import Image, UnidentifiedImageError
    _PILLOW_AVAILABLE = True
except Exception:  # pragma: no cover
    _PILLOW_AVAILABLE = False

router = APIRouter()
templates = Jinja2Templates(directory=["fastapi_modulo/templates", "fastapi_modulo"])

MODULE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = MODULE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ASSET_FIELDS = ["favicon", "logo_empresa", "logo_usuario", "svg_fondo", "svg_defecto"]

# Extensiones permitidas por tipo de asset
_ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    "favicon":       {".png", ".ico", ".svg"},
    "logo_empresa":  {".png", ".jpg", ".jpeg", ".svg", ".webp"},
    "logo_usuario":  {".png", ".jpg", ".jpeg", ".svg", ".webp"},
    "svg_fondo":     {".svg"},
    "svg_defecto":   {".svg"},
}

# Tamaño máximo por asset en bytes (5 MB)
_MAX_FILE_BYTES = 5 * 1024 * 1024

# Dimensiones máximas recomendadas por asset
_ASSET_MAX_SIZES: dict[str, tuple[int, int]] = {
    "favicon":      (64,   64),
    "logo_empresa": (800,  400),
    "logo_usuario": (400,  400),
}

# ── Cache de tema con Redis ───────────────────────────────────────────────────
_THEME_CACHE_KEY = "personalizacion:theme:institutional"
_THEME_CACHE_TTL = 60  # segundos


def _get_redis():
    """Devuelve el cliente Redis del módulo web si está disponible."""
    try:
        from fastapi_modulo.modulos_sipet.web.servicios.redis_security_service import get_redis_client
        return get_redis_client()
    except Exception:
        return None


def _cache_theme(theme: dict) -> None:
    try:
        import json
        client = _get_redis()
        if client:
            client.setex(_THEME_CACHE_KEY, _THEME_CACHE_TTL, json.dumps(theme))
    except Exception:
        pass


def _get_cached_theme() -> dict | None:
    try:
        import json
        client = _get_redis()
        if not client:
            return None
        raw = client.get(_THEME_CACHE_KEY)
        if not raw:
            return None
        return json.loads(raw)
    except Exception:
        return None


def _invalidate_theme_cache() -> None:
    try:
        client = _get_redis()
        if client:
            client.delete(_THEME_CACHE_KEY)
    except Exception:
        pass


def _load_theme_from_db() -> dict:
    """Carga colores de la DB, con caché Redis. Usa colores.json como fallback."""
    cached = _get_cached_theme()
    if cached:
        return cached

    db = SessionLocal()
    try:
        colores = db.query(Colores).all()
        stored = {str(c.key or "").strip(): str(c.value or "").strip() for c in colores}
    finally:
        db.close()

    # Si la BD está vacía, intentar leer data/colores.json como fallback
    if not stored:
        stored = _load_json_fallback()

    theme = build_institutional_theme(stored)
    _cache_theme(theme)
    return theme


def _load_json_fallback() -> dict:
    """Lee data/colores.json como configuración inicial si la BD está vacía."""
    json_path = MODULE_DIR / "data" / "colores.json"
    if not json_path.exists():
        return {}
    try:
        import json
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        # Solo usar las claves MAIN del tema
        return {k: v for k, v in raw.items() if k in set(MAIN_THEME_KEYS)}
    except Exception:
        return {}


# ── Schemas Pydantic ──────────────────────────────────────────────────────────

class ColorPayloadSchema(BaseModel):
    """Valida que los colores enviados sean hex #RRGGBB válidos."""
    navbar_bg: Optional[str] = None
    sidebar_top: Optional[str] = None
    sidebar_bottom: Optional[str] = None
    field_color: Optional[str] = None
    button_bg: Optional[str] = None
    screen_bg: Optional[str] = None
    panel_1_bg: Optional[str] = None
    panel_2_bg: Optional[str] = None

    @field_validator(
        "navbar_bg",
        "sidebar_top",
        "sidebar_bottom",
        "field_color",
        "button_bg",
        "screen_bg",
        "panel_1_bg",
        "panel_2_bg",
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
            raise ValueError(f"Color inválido: '{raw}'. Debe ser formato #RRGGBB.")
        return normalized

    def to_theme_dict(self) -> dict[str, str]:
        mapping = {
            "navbar-bg":      self.navbar_bg,
            "sidebar-top":    self.sidebar_top,
            "sidebar-bottom": self.sidebar_bottom,
            "field-color":    self.field_color,
            "button-bg":      self.button_bg,
            "screen-bg":      self.screen_bg,
            "panel-1-bg":     self.panel_1_bg,
            "panel-2-bg":     self.panel_2_bg,
        }
        return {k: v for k, v in mapping.items() if v is not None}


class RemoveAssetsSchema(BaseModel):
    """Valida los flags de remoción de assets."""
    remove_favicon:      bool = False
    remove_logo_empresa: bool = False
    remove_logo_usuario: bool = False
    remove_svg_fondo:    bool = False
    remove_svg_defecto:  bool = False

    @field_validator(
        "remove_favicon", "remove_logo_empresa", "remove_logo_usuario",
        "remove_svg_fondo", "remove_svg_defecto", mode="before"
    )
    @classmethod
    def parse_flag(cls, v: object) -> bool:
        if isinstance(v, str):
            return v.strip() == "1"
        return bool(v)

    def to_dict(self) -> dict[str, bool]:
        return {
            "favicon":      self.remove_favicon,
            "logo_empresa": self.remove_logo_empresa,
            "logo_usuario": self.remove_logo_usuario,
            "svg_fondo":    self.remove_svg_fondo,
            "svg_defecto":  self.remove_svg_defecto,
        }


# ── Helpers de assets ─────────────────────────────────────────────────────────

def _safe_ext(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    if not suffix:
        return ".bin"
    cleaned = re.sub(r"[^a-z0-9.]", "", suffix)
    if not cleaned.startswith("."):
        cleaned = f".{cleaned}"
    return cleaned or ".bin"


def _asset_candidates(field: str) -> list[Path]:
    return sorted(UPLOAD_DIR.glob(f"{field}.*"), key=lambda p: p.stat().st_mtime, reverse=True)


def _asset_default_candidates(field: str) -> list[Path]:
    return sorted(UPLOAD_DIR.glob(f"default_{field}.*"), key=lambda p: p.stat().st_mtime, reverse=True)


def _asset_path(field: str) -> Optional[Path]:
    candidates = _asset_candidates(field)
    return candidates[0] if candidates else None


def _asset_default_path(field: str) -> Optional[Path]:
    candidates = _asset_default_candidates(field)
    return candidates[0] if candidates else None


def _clear_asset(field: str) -> bool:
    removed = False
    for path in _asset_candidates(field):
        path.unlink(missing_ok=True)
        removed = True
    return removed


def _clear_asset_default(field: str) -> bool:
    removed = False
    for path in _asset_default_candidates(field):
        path.unlink(missing_ok=True)
        removed = True
    return removed


def _save_default_from_path(field: str, source_path: Path) -> Optional[str]:
    if not source_path.exists():
        return None
    _clear_asset_default(field)
    filename = f"default_{field}{source_path.suffix.lower()}"
    target = UPLOAD_DIR / filename
    shutil.copy2(source_path, target)
    return filename


def _restore_active_from_default(field: str) -> Optional[str]:
    default_path = _asset_default_path(field)
    if not default_path:
        return None
    _clear_asset(field)
    filename = f"{field}{default_path.suffix.lower()}"
    target = UPLOAD_DIR / filename
    shutil.copy2(default_path, target)
    return filename


def _bootstrap_defaults_from_active() -> None:
    for field in ASSET_FIELDS:
        if _asset_default_path(field):
            continue
        active = _asset_path(field)
        if active:
            _save_default_from_path(field, active)


def _validate_and_process_image(
    raw: bytes, ext: str, field: str
) -> tuple[bytes, str]:
    """
    Valida con Pillow que sea una imagen real, aplica resize si supera
    el máximo recomendado para el asset, y convierte a WebP si aplica.
    SVGs pasan sin procesar.
    Lanza HTTPException 400 si el archivo no es imagen válida.
    """
    if ext == ".svg":
        return raw, ext

    if not _PILLOW_AVAILABLE:
        return raw, ext

    # Verificar que sea imagen real
    try:
        probe = Image.open(io.BytesIO(raw))
        probe.verify()
        img = Image.open(io.BytesIO(raw))
    except (UnidentifiedImageError, Exception):
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida.")

    # Normalizar modo de color
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGBA" if "A" in img.mode else "RGB")

    # Redimensionar si supera el máximo del asset
    max_w, max_h = _ASSET_MAX_SIZES.get(field, (1920, 1920))
    if img.width > max_w or img.height > max_h:
        img.thumbnail((max_w, max_h), Image.LANCZOS)

    # Convertir a WebP (excepto favicon que mantiene PNG/ICO)
    if field == "favicon":
        out_format = "PNG"
        out_ext = ".png"
        save_kwargs: dict = {"optimize": True}
    else:
        out_format = "WEBP"
        out_ext = ".webp"
        save_kwargs = {"quality": 85, "method": 4}

    if out_format == "PNG" and img.mode == "RGBA":
        pass  # PNG soporta alpha
    elif out_format != "PNG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")

    buf = io.BytesIO()
    img.save(buf, format=out_format, **save_kwargs)
    buf.seek(0)
    return buf.read(), out_ext


async def _store_asset(field: str, file_obj: UploadFile) -> tuple[Optional[str], dict]:
    """
    Valida, procesa con Pillow y guarda el asset.
    Devuelve (filename, info_dict).
    """
    if not file_obj or not (file_obj.filename or "").strip():
        return None, {}

    ext = _safe_ext(file_obj.filename)

    # Validar extensión permitida para este field
    allowed = _ALLOWED_EXTENSIONS.get(field, set())
    if allowed and ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión '{ext}' no permitida para '{field}'. "
                   f"Usa: {', '.join(sorted(allowed))}.",
        )

    contents = await file_obj.read()

    # Validar tamaño máximo
    if len(contents) > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo demasiado grande. Máximo {_MAX_FILE_BYTES // (1024 * 1024)} MB.",
        )

    # Procesar imagen con Pillow
    contents, ext = _validate_and_process_image(contents, ext, field)

    _clear_asset(field)
    filename = f"{field}{ext}"
    target = UPLOAD_DIR / filename
    target.write_bytes(contents)
    _save_default_from_path(field, target)

    info: dict = {"size_bytes": len(contents), "ext": ext}
    if _PILLOW_AVAILABLE and ext != ".svg":
        try:
            img = Image.open(io.BytesIO(contents))
            info["width"] = img.width
            info["height"] = img.height
        except Exception:
            pass

    return filename, info


def _asset_url(filename: str) -> str:
    return f"/personalizar/uploads/{filename}"


def resolve_logo_empresa_url() -> str:
    path = _asset_path("logo_empresa")
    if not path:
        return ""
    version = int(path.stat().st_mtime) if path.exists() else 0
    return f"/personalizar/uploads/{path.name}?v={version}"


def _assets_state() -> dict:
    _bootstrap_defaults_from_active()
    state = {}
    for field in ASSET_FIELDS:
        path = _asset_path(field)
        filename = path.name if path else ""
        default_path = _asset_default_path(field)
        default_filename = default_path.name if default_path else ""
        state[field] = {
            "filename": filename,
            "url": _asset_url(filename) if filename else "",
            "exists": bool(filename),
            "default_filename": default_filename,
            "has_default": bool(default_filename),
        }
    return state


# ── Rutas ─────────────────────────────────────────────────────────────────────

@router.post("/guardar-colores")
async def guardar_colores(request: Request, data: dict):
    """Guarda colores desde el payload JSON y devuelve el tema completo."""
    db = SessionLocal()
    try:
        # Validar colores con Pydantic
        try:
            schema = ColorPayloadSchema(
                navbar_bg=data.get("navbar-bg"),
                sidebar_top=data.get("sidebar-top"),
                sidebar_bottom=data.get("sidebar-bottom"),
                field_color=data.get("field-color"),
                button_bg=data.get("button-bg"),
                screen_bg=data.get("screen-bg"),
                panel_1_bg=data.get("panel-1-bg"),
                panel_2_bg=data.get("panel-2-bg"),
            )
        except Exception as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=422)

        validated = schema.to_theme_dict()
        allowed = set(MAIN_THEME_KEYS)

        for key, value in validated.items():
            color = db.query(Colores).filter(Colores.key == key).first()
            if color:
                color.value = value
            else:
                db.add(Colores(key=key, value=value))

        # Eliminar claves no permitidas enviadas en el payload
        for key in (data or {}):
            if key not in allowed:
                db.query(Colores).filter(Colores.key == key).delete()

        db.commit()
        stored = {str(c.key or "").strip(): str(c.value or "").strip() for c in db.query(Colores).all()}
        _invalidate_theme_cache()
        theme = build_institutional_theme(stored)
        _cache_theme(theme)
        return JSONResponse({"success": True, "data": theme})
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)
    finally:
        db.close()


@router.get("/guardar-colores")
async def obtener_colores():
    """Devuelve el tema institucional completo (con caché Redis)."""
    try:
        return JSONResponse({"success": True, "data": _load_theme_from_db()})
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@router.get("/personalizar/estado")
def personalizar_estado() -> JSONResponse:
    return JSONResponse({"ok": True, "assets": _assets_state()})


@router.get("/personalizar/uploads/{filename}")
def personalizar_upload(filename: str):
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")
    file_path = UPLOAD_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(file_path)


@router.post("/personalizar/restablecer-assets")
def restablecer_assets(request: Request) -> JSONResponse:
    require_superadmin(request)
    restored = []
    for field in ASSET_FIELDS:
        if _restore_active_from_default(field):
            restored.append(field)
    return JSONResponse({"ok": True, "restored": restored, "assets": _assets_state()})


@router.post("/personalizar/guardar")
async def guardar_personalizacion(
    request: Request,
    navbar_bg: Optional[str] = Form(None),
    sidebar_top: Optional[str] = Form(None),
    sidebar_bottom: Optional[str] = Form(None),
    field_color: Optional[str] = Form(None),
    button_bg: Optional[str] = Form(None),
    screen_bg: Optional[str] = Form(None),
    panel_1_bg: Optional[str] = Form(None),
    panel_2_bg: Optional[str] = Form(None),
    favicon: Optional[UploadFile] = File(None),
    logo_empresa: Optional[UploadFile] = File(None),
    logo_usuario: Optional[UploadFile] = File(None),
    svg_fondo: Optional[UploadFile] = File(None),
    svg_defecto: Optional[UploadFile] = File(None),
    remove_favicon: str = Form("0"),
    remove_logo_empresa: str = Form("0"),
    remove_logo_usuario: str = Form("0"),
    remove_svg_fondo: str = Form("0"),
    remove_svg_defecto: str = Form("0"),
):
    require_superadmin(request)

    # ── Validar colores con Pydantic ──────────────────────────────────────────
    try:
        color_schema = ColorPayloadSchema(
            navbar_bg=navbar_bg,
            sidebar_top=sidebar_top,
            sidebar_bottom=sidebar_bottom,
            field_color=field_color,
            button_bg=button_bg,
            screen_bg=screen_bg,
            panel_1_bg=panel_1_bg,
            panel_2_bg=panel_2_bg,
        )
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=422)

    # ── Validar flags de remoción ─────────────────────────────────────────────
    remove_schema = RemoveAssetsSchema(
        remove_favicon=remove_favicon,
        remove_logo_empresa=remove_logo_empresa,
        remove_logo_usuario=remove_logo_usuario,
        remove_svg_fondo=remove_svg_fondo,
        remove_svg_defecto=remove_svg_defecto,
    )
    remove_flags = remove_schema.to_dict()

    file_map: dict[str, Optional[UploadFile]] = {
        "favicon":      favicon,
        "logo_empresa": logo_empresa,
        "logo_usuario": logo_usuario,
        "svg_fondo":    svg_fondo,
        "svg_defecto":  svg_defecto,
    }

    updated: list[str] = []
    removed: list[str] = []
    asset_details: dict = {}

    # ── Guardar colores en DB ─────────────────────────────────────────────────
    color_db = SessionLocal()
    try:
        validated_colors = color_schema.to_theme_dict()
        for key, value in validated_colors.items():
            current = color_db.query(Colores).filter(Colores.key == key).first()
            if current:
                current.value = value
            else:
                color_db.add(Colores(key=key, value=value))
        color_db.commit()
        stored_colors = {
            str(item.key or "").strip(): str(item.value or "").strip()
            for item in color_db.query(Colores).all()
        }
    finally:
        color_db.close()

    # ── Procesar eliminaciones de assets ──────────────────────────────────────
    for field in ASSET_FIELDS:
        if remove_flags.get(field):
            if _clear_asset(field):
                removed.append(field)

    # ── Procesar uploads con validación Pillow ────────────────────────────────
    for field, upload in file_map.items():
        if upload and (upload.filename or "").strip():
            saved, info = await _store_asset(field, upload)
            if saved:
                updated.append(field)
                if info:
                    asset_details[field] = info

    # Invalidar y recalcular tema
    _invalidate_theme_cache()
    theme = build_institutional_theme(stored_colors)
    _cache_theme(theme)

    return JSONResponse(
        {
            "ok": True,
            "updated": updated,
            "removed": removed,
            "asset_details": asset_details,
            "assets": _assets_state(),
            "colors": theme,
        }
    )


@router.get("/personalizar", response_class=HTMLResponse)
def personalizar_page(request: Request):
    require_superadmin(request)
    with open(MODULE_DIR / "vistas" / "personalizar.html", encoding="utf-8") as f:
        panel_html = f.read()
    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "title": "Personalización visual",
            "description": "Ajusta la paleta visual del sistema.",
            "page_title": "Personalización visual",
            "page_description": "Ajusta la paleta visual del sistema.",
            "section_label": "",
            "section_title": "",
            "content": panel_html,
            "floating_actions_html": "",
            "floating_actions_screen": "personalization",
            "hide_floating_actions": True,
            "show_page_header": True,
            "colores": get_colores_context(),
        },
    )
    
