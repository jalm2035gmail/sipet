"""
Servicio de generación de avatares con Pillow.

Genera avatares en memoria (bytes PNG o WebP) a partir de:
- Iniciales del nombre de usuario
- Color de fondo derivado del username (determinístico)
- Rol del usuario (afecta la paleta de color)

No escribe nada en disco — devuelve bytes listos para:
- Servir como HTTP response (image/png o image/webp)
- Guardar en base de datos como BLOB
- Cachear en Redis con TTL

Configuración via variables de entorno:
  WEB_AVATAR_SIZE          Tamaño en px del avatar cuadrado (default: 128)
  WEB_AVATAR_FORMAT        "PNG" o "WEBP" (default: WEBP)
  WEB_AVATAR_QUALITY       Calidad WebP 1-95 (default: 85)
"""
from __future__ import annotations

import hashlib
import io
import os
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
    _PILLOW_AVAILABLE = True
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    _PILLOW_AVAILABLE = False

# ── Configuración ─────────────────────────────────────────────────────────────
_AVATAR_SIZE = int((os.environ.get("WEB_AVATAR_SIZE") or "128").strip() or "128")
_AVATAR_FORMAT = (os.environ.get("WEB_AVATAR_FORMAT") or "WEBP").strip().upper()
_AVATAR_QUALITY = int((os.environ.get("WEB_AVATAR_QUALITY") or "85").strip() or "85")

# Paletas por rol — (fondo, texto)
# Cada rol tiene 6 variantes para distribuir usuarios del mismo rol
_ROLE_PALETTES: dict[str, list[tuple[str, str]]] = {
    "superadministrador": [
        ("#1e1b4b", "#e0e7ff"), ("#312e81", "#eef2ff"), ("#3730a3", "#e0e7ff"),
        ("#4338ca", "#eef2ff"), ("#4f46e5", "#eef2ff"), ("#6366f1", "#1e1b4b"),
    ],
    "administrador": [
        ("#0c4a6e", "#e0f2fe"), ("#075985", "#f0f9ff"), ("#0369a1", "#e0f2fe"),
        ("#0284c7", "#f0f9ff"), ("#0ea5e9", "#082f49"), ("#38bdf8", "#0c4a6e"),
    ],
    "autoridades": [
        ("#134e4a", "#ccfbf1"), ("#115e59", "#f0fdfa"), ("#0f766e", "#ccfbf1"),
        ("#0d9488", "#f0fdfa"), ("#14b8a6", "#042f2e"), ("#2dd4bf", "#134e4a"),
    ],
    "usuario": [
        ("#1e3a5f", "#dbeafe"), ("#1e40af", "#eff6ff"), ("#1d4ed8", "#dbeafe"),
        ("#2563eb", "#eff6ff"), ("#3b82f6", "#1e3a5f"), ("#60a5fa", "#1e3a5f"),
    ],
}
_DEFAULT_PALETTE: list[tuple[str, str]] = [
    ("#374151", "#f9fafb"), ("#4b5563", "#f9fafb"), ("#6b7280", "#f9fafb"),
    ("#9ca3af", "#111827"), ("#d1d5db", "#111827"), ("#e5e7eb", "#374151"),
]


def pillow_available() -> bool:
    return _PILLOW_AVAILABLE


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _palette_index(username: str) -> int:
    """Índice determinístico 0-5 basado en el hash del username."""
    digest = hashlib.md5(username.lower().encode("utf-8")).hexdigest()
    return int(digest[:2], 16) % 6


def _pick_palette(username: str, role: str) -> tuple[str, str]:
    """Devuelve (color_fondo, color_texto) para el username y rol dados."""
    palettes = _ROLE_PALETTES.get(role.lower().strip(), _DEFAULT_PALETTE)
    idx = _palette_index(username)
    return palettes[idx % len(palettes)]


def _extract_initials(username: str, max_chars: int = 2) -> str:
    """
    Extrae las iniciales del username:
    - 'juan perez'  → 'JP'
    - 'jperez'      → 'JP'  (primera letra + primera consonante/vocal)
    - 'j'           → 'J'
    """
    clean = username.strip()
    if not clean:
        return "?"
    parts = clean.split()
    if len(parts) >= 2:
        initials = "".join(p[0].upper() for p in parts if p)[:max_chars]
        return initials if initials else clean[0].upper()
    # Nombre único: primera letra + segunda letra diferente
    letters = [c for c in clean.upper() if c.isalpha()]
    if not letters:
        return clean[0].upper()
    if len(letters) == 1:
        return letters[0]
    return letters[0] + letters[1]


def _font_size_for(avatar_size: int) -> int:
    """Tamaño de fuente proporcional al avatar."""
    return max(12, int(avatar_size * 0.38))


def _load_font(font_size: int) -> "ImageFont.FreeTypeFont | ImageFont.ImageFont":
    """
    Intenta cargar una fuente del sistema. Cae a la fuente bitmap de Pillow
    si no hay ninguna disponible — siempre funciona.
    """
    system_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for path in system_fonts:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue
    # Fallback: fuente bitmap incluida en Pillow (siempre disponible)
    return ImageFont.load_default()


def generate_avatar_bytes(
    username: str,
    role: str = "usuario",
    size: Optional[int] = None,
    fmt: Optional[str] = None,
    quality: Optional[int] = None,
) -> bytes:
    """
    Genera un avatar cuadrado con las iniciales del usuario.

    Args:
        username:  Nombre de usuario o nombre completo.
        role:      Rol del usuario — afecta la paleta de colores.
        size:      Tamaño en px (default: WEB_AVATAR_SIZE o 128).
        fmt:       "PNG" o "WEBP" (default: WEB_AVATAR_FORMAT o "WEBP").
        quality:   Calidad para WebP (default: WEB_AVATAR_QUALITY o 85).

    Returns:
        bytes del imagen. Devuelve b"" si Pillow no está disponible.
    """
    if not _PILLOW_AVAILABLE:
        return b""

    resolved_size = int(size or _AVATAR_SIZE)
    resolved_fmt = (fmt or _AVATAR_FORMAT).upper()
    resolved_quality = int(quality or _AVATAR_QUALITY)

    bg_hex, fg_hex = _pick_palette(username, role)
    bg_rgb = _hex_to_rgb(bg_hex)
    fg_rgb = _hex_to_rgb(fg_hex)
    initials = _extract_initials(username)

    # ── Crear imagen base ─────────────────────────────────────────────────────
    img = Image.new("RGB", (resolved_size, resolved_size), color=bg_rgb)
    draw = ImageDraw.Draw(img)

    # ── Círculo de fondo ligeramente más claro ────────────────────────────────
    margin = int(resolved_size * 0.04)
    draw.ellipse(
        [margin, margin, resolved_size - margin, resolved_size - margin],
        fill=bg_rgb,
    )

    # ── Texto centrado ────────────────────────────────────────────────────────
    font = _load_font(_font_size_for(resolved_size))
    try:
        # Pillow >= 9.2.0
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        # Ajustar por descender (bbox[1] puede ser negativo en algunas fuentes)
        text_x = (resolved_size - text_w) / 2 - bbox[0]
        text_y = (resolved_size - text_h) / 2 - bbox[1]
    except AttributeError:
        # Pillow < 9.2.0 — fallback a getsize
        try:
            text_w, text_h = draw.textsize(initials, font=font)  # type: ignore[attr-defined]
        except Exception:
            text_w, text_h = resolved_size // 3, resolved_size // 3
        text_x = (resolved_size - text_w) / 2
        text_y = (resolved_size - text_h) / 2

    draw.text((text_x, text_y), initials, fill=fg_rgb, font=font)

    # ── Serializar ────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    save_kwargs: dict = {}
    if resolved_fmt == "WEBP":
        save_kwargs = {"quality": resolved_quality, "method": 4}
    elif resolved_fmt == "JPEG":
        resolved_fmt = "JPEG"
        save_kwargs = {"quality": resolved_quality, "optimize": True}

    img.save(buf, format=resolved_fmt, **save_kwargs)
    buf.seek(0)
    return buf.read()


def generate_avatar_for_user(user: object, size: Optional[int] = None) -> bytes:
    """
    Genera un avatar a partir de un objeto de usuario SQLAlchemy.
    Extrae `usuario` (o `nombre`) y `role` del objeto automáticamente.
    """
    username = (
        getattr(user, "usuario", None)
        or getattr(user, "nombre", None)
        or getattr(user, "username", None)
        or "?"
    )
    role = getattr(user, "role", None) or "usuario"
    return generate_avatar_bytes(str(username), role=str(role), size=size)


def avatar_content_type(fmt: Optional[str] = None) -> str:
    """Devuelve el Content-Type correspondiente al formato configurado."""
    resolved = (fmt or _AVATAR_FORMAT).upper()
    mapping = {
        "PNG": "image/png",
        "WEBP": "image/webp",
        "JPEG": "image/jpeg",
        "JPG": "image/jpeg",
    }
    return mapping.get(resolved, "image/png")
