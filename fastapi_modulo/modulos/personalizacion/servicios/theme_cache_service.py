"""
Servicio de caché del tema institucional con Redis.

Centraliza toda la lógica de caché para build_institutional_theme(),
evitando que cada request a /guardar-colores o al render del backend
ejecute consultas SQL + 20+ operaciones de color.

Estrategia:
  - SET al guardar colores (invalida y recalcula inmediatamente)
  - GET con TTL de 60s (configurable via WEB_THEME_CACHE_TTL)
  - Fallback transparente a DB si Redis no está disponible
  - Invalidación explícita disponible para forzar recálculo

Variables de entorno:
  WEB_THEME_CACHE_TTL       TTL en segundos (default: 60)
  WEB_THEME_CACHE_KEY       Clave Redis (default: personalizacion:theme:institutional)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

from fastapi_modulo.modulos.personalizacion.modelos.theme_system import build_institutional_theme

logger = logging.getLogger(__name__)

_CACHE_KEY = (
    os.environ.get("WEB_THEME_CACHE_KEY") or "personalizacion:theme:institutional"
).strip()

_CACHE_TTL = int(
    (os.environ.get("WEB_THEME_CACHE_TTL") or "60").strip() or "60"
)


# ── Redis client ──────────────────────────────────────────────────────────────

def _get_redis():
    """
    Reutiliza el cliente Redis del módulo web (redis_security_service)
    para no abrir conexiones adicionales.
    Devuelve None si Redis no está disponible — todo el servicio
    funciona en modo degradado sin caché.
    """
    try:
        from fastapi_modulo.modulos_sipet.web.servicios.redis_security_service import get_redis_client
        return get_redis_client()
    except Exception:
        return None


# ── Operaciones de caché ──────────────────────────────────────────────────────

def get_cached_theme() -> Optional[dict[str, str]]:
    """
    Lee el tema institucional desde Redis.
    Devuelve None si no hay caché o Redis no está disponible.
    """
    try:
        client = _get_redis()
        if not client:
            return None
        raw = client.get(_CACHE_KEY)
        if not raw:
            return None
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return None
        return payload
    except Exception as exc:
        logger.debug("theme_cache_service: error leyendo caché — %s", exc)
        return None


def set_cached_theme(theme: dict[str, str]) -> bool:
    """
    Guarda el tema institucional en Redis con TTL.
    Devuelve True si se guardó correctamente, False en cualquier otro caso.
    """
    if not isinstance(theme, dict) or not theme:
        return False
    try:
        client = _get_redis()
        if not client:
            return False
        client.setex(_CACHE_KEY, max(1, _CACHE_TTL), json.dumps(theme))
        return True
    except Exception as exc:
        logger.debug("theme_cache_service: error escribiendo caché — %s", exc)
        return False


def invalidate_theme_cache() -> bool:
    """
    Elimina el tema del caché para forzar recálculo en el próximo request.
    Llámala después de guardar colores o assets.
    Devuelve True si se eliminó, False si no había caché o hubo error.
    """
    try:
        client = _get_redis()
        if not client:
            return False
        deleted = client.delete(_CACHE_KEY)
        return bool(deleted)
    except Exception as exc:
        logger.debug("theme_cache_service: error invalidando caché — %s", exc)
        return False


# ── Carga del tema con caché ──────────────────────────────────────────────────

def load_theme(stored_colors: Optional[dict[str, str]] = None) -> dict[str, str]:
    """
    Devuelve el tema institucional completo.

    Si stored_colors es None, intenta leer desde caché Redis.
    Si el caché está vacío o Redis no está disponible, consulta la DB.
    Si stored_colors se provee explícitamente, recalcula y actualiza el caché.

    Args:
        stored_colors: dict con los colores MAIN de la DB, o None para
                       intentar leer desde caché antes de ir a la DB.

    Returns:
        dict completo con todas las claves del tema institucional.
    """
    if stored_colors is not None:
        theme = build_institutional_theme(stored_colors)
        set_cached_theme(theme)
        return theme

    cached = get_cached_theme()
    if cached:
        return cached

    theme = _load_from_db()
    set_cached_theme(theme)
    return theme


def _load_from_db() -> dict[str, str]:
    """
    Carga los colores desde la DB y construye el tema.
    Usa data/colores.json como fallback si la DB está vacía
    (lógica manejada por build_institutional_theme vía theme_system.py).
    """
    try:
        from fastapi_modulo.core.db import SessionLocal
        from fastapi_modulo.modulos_sipet.web.modelos.core_models import Colores

        db = SessionLocal()
        try:
            colores = db.query(Colores).all()
            stored = {
                str(c.key or "").strip(): str(c.value or "").strip()
                for c in colores
            }
        finally:
            db.close()

        return build_institutional_theme(stored)
    except Exception as exc:
        logger.warning(
            "theme_cache_service: error cargando colores de DB — %s. "
            "Usando tema por defecto.",
            exc,
        )
        return build_institutional_theme(None)


# ── Utilidades ────────────────────────────────────────────────────────────────

def refresh_theme_cache() -> dict[str, str]:
    """
    Fuerza la recarga del tema desde DB, actualiza el caché y lo devuelve.
    Útil para llamar después de un deploy o cuando se sospecha
    inconsistencia entre DB y caché.
    """
    invalidate_theme_cache()
    theme = _load_from_db()
    set_cached_theme(theme)
    logger.info("theme_cache_service: caché refrescado")
    return theme


def cache_status() -> dict[str, object]:
    """
    Devuelve el estado actual del caché para diagnóstico.
    Incluye si Redis está disponible, si hay un tema cacheado y su TTL.
    """
    client = _get_redis()
    if not client:
        return {
            "redis_available": False,
            "cached": False,
            "ttl_seconds": None,
            "cache_key": _CACHE_KEY,
            "configured_ttl": _CACHE_TTL,
        }
    try:
        ttl = client.ttl(_CACHE_KEY)
        cached = ttl > 0
        return {
            "redis_available": True,
            "cached": cached,
            "ttl_seconds": ttl if ttl > 0 else None,
            "cache_key": _CACHE_KEY,
            "configured_ttl": _CACHE_TTL,
        }
    except Exception as exc:
        return {
            "redis_available": True,
            "cached": False,
            "ttl_seconds": None,
            "cache_key": _CACHE_KEY,
            "configured_ttl": _CACHE_TTL,
            "error": str(exc),
        }
    