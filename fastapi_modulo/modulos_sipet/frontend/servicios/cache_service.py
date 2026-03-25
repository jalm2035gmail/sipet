"""
servicios/cache_service.py
─────────────────────────────────────────────────────────────────────────────
Servicio de caché Redis para el módulo frontend.

Responsabilidades:
  • Conectar a Redis una sola vez por proceso (singleton con lru_cache).
  • Exponer get / set / delete / clear_all con degradación silenciosa:
    si Redis no está disponible la app sigue funcionando sin caché.
  • Centralizar el prefijo de claves y el TTL configurable por env var.

Variables de entorno:
  REDIS_URL          URL de conexión, ej. redis://localhost:6379/0
                     Si no está definida, el caché queda desactivado.
  PAGE_CACHE_TTL     TTL en segundos (default: 300 = 5 min).
  PAGE_CACHE_PREFIX  Prefijo de claves (default: "frontend:page:").

Uso típico en controladores:
    from fastapi_modulo.modulos_sipet.frontend.servicios.cache_service import page_cache

    html = page_cache.get("inicio")
    if html is None:
        html = render_page(...)
        page_cache.set("inicio", html)

    page_cache.delete("inicio", "backend:inicio")
    page_cache.clear_all()
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# ── Configuración desde variables de entorno ──────────────────────────────────
_REDIS_URL    = os.environ.get("REDIS_URL", "")
_CACHE_TTL    = int(os.environ.get("PAGE_CACHE_TTL", "300"))
_CACHE_PREFIX = os.environ.get("PAGE_CACHE_PREFIX", "frontend:page:")


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — CONEXIÓN (singleton)
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def _get_client():
    """
    Crea y devuelve el cliente Redis reutilizable.
    Se llama como máximo una vez por proceso gracias a lru_cache.

    Devuelve None si:
      - REDIS_URL no está definido.
      - La librería redis no está instalada.
      - Redis no responde al ping de conexión.

    En todos los casos de fallo se emite un warning y la app continúa
    sin caché (degradación silenciosa).
    """
    if not _REDIS_URL:
        logger.warning(
            "cache_service: REDIS_URL no configurado — "
            "caché de páginas desactivado."
        )
        return None

    try:
        import redis  # importación diferida: no falla si redis no está instalado
        client = redis.from_url(
            _REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=False,
        )
        client.ping()
        logger.info("cache_service: conexión a Redis establecida (%s).", _REDIS_URL)
        return client
    except ImportError:
        logger.warning(
            "cache_service: paquete 'redis' no instalado — "
            "caché desactivado. Instala con: pip install redis"
        )
    except Exception as exc:
        logger.warning(
            "cache_service: no se pudo conectar a Redis (%s) — "
            "caché desactivado. Error: %s",
            _REDIS_URL, exc,
        )
    return None


def _full_key(key: str) -> str:
    """Devuelve la clave completa con prefijo: 'frontend:page:inicio'."""
    return f"{_CACHE_PREFIX}{key}"


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — OPERACIONES BÁSICAS
# ══════════════════════════════════════════════════════════════════════════════

def get(key: str) -> Optional[str]:
    """
    Lee el HTML cacheado para la clave dada.
    Devuelve None si la clave no existe, expiró o Redis no está disponible.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        return client.get(_full_key(key))
    except Exception as exc:
        logger.debug("cache_service.get('%s') falló: %s", key, exc)
        return None


def set(key: str, value: str, ttl: Optional[int] = None) -> None:
    """
    Almacena value bajo key con el TTL configurado (o el TTL explícito).
    No hace nada si Redis no está disponible.
    """
    client = _get_client()
    if client is None:
        return
    try:
        client.setex(_full_key(key), ttl if ttl is not None else _CACHE_TTL, value)
    except Exception as exc:
        logger.debug("cache_service.set('%s') falló: %s", key, exc)


def delete(*keys: str) -> None:
    """
    Invalida una o varias claves.
    Acepta cualquier número de argumentos: delete("inicio", "backend:inicio").
    No hace nada si Redis no está disponible o las claves no existen.
    """
    if not keys:
        return
    client = _get_client()
    if client is None:
        return
    try:
        client.delete(*[_full_key(k) for k in keys])
    except Exception as exc:
        logger.debug("cache_service.delete(%s) falló: %s", keys, exc)


def delete_for_slug(slug: str) -> None:
    """
    Atajo para invalidar las dos claves que genera una página:
      • '<slug>'          → sirve /p/<slug>
      • 'backend:<slug>'  → sirve /backend/<slug>
    """
    delete(slug, f"backend:{slug}")


def clear_all() -> None:
    """
    Elimina TODAS las claves del módulo frontend del caché.
    Usa SCAN en lugar de KEYS * para no bloquear Redis en producción.
    """
    client = _get_client()
    if client is None:
        return
    try:
        pattern = f"{_CACHE_PREFIX}*"
        cursor   = 0
        deleted  = 0
        while True:
            cursor, keys = client.scan(cursor, match=pattern, count=200)
            if keys:
                client.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        logger.debug("cache_service.clear_all(): %d claves eliminadas.", deleted)
    except Exception as exc:
        logger.debug("cache_service.clear_all() falló: %s", exc)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — UTILIDADES DE DIAGNÓSTICO
# ══════════════════════════════════════════════════════════════════════════════

def is_available() -> bool:
    """
    Devuelve True si Redis está configurado y responde.
    Útil para endpoints de healthcheck.
    """
    return _get_client() is not None


def ttl(key: str) -> int:
    """
    Devuelve el TTL restante en segundos para una clave.
    Devuelve -2 si la clave no existe, -1 si no tiene TTL, 0 si Redis no está disponible.
    """
    client = _get_client()
    if client is None:
        return 0
    try:
        return client.ttl(_full_key(key))
    except Exception as exc:
        logger.debug("cache_service.ttl('%s') falló: %s", key, exc)
        return 0


def info() -> dict:
    """
    Devuelve información básica del estado del caché.
    Útil para endpoints de administración o logging de startup.
    """
    available = is_available()
    return {
        "available":    available,
        "redis_url":    _REDIS_URL if _REDIS_URL else "(no configurado)",
        "ttl_seconds":  _CACHE_TTL,
        "key_prefix":   _CACHE_PREFIX,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — INSTANCIA SINGLETON (interfaz orientada a objetos, opcional)
# ══════════════════════════════════════════════════════════════════════════════

class PageCache:
    """
    Wrapper orientado a objetos sobre las funciones del módulo.
    Permite usar page_cache.get(...) en lugar de cache_service.get(...)
    y facilita el mocking en tests.

    Ejemplo:
        from fastapi_modulo.modulos_sipet.frontend.servicios.cache_service import page_cache

        html = page_cache.get("inicio")
        page_cache.set("inicio", html)
        page_cache.delete_for_slug("inicio")
        page_cache.clear_all()
    """

    def get(self, key: str) -> Optional[str]:
        return get(key)

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        set(key, value, ttl=ttl)

    def delete(self, *keys: str) -> None:
        delete(*keys)

    def delete_for_slug(self, slug: str) -> None:
        delete_for_slug(slug)

    def clear_all(self) -> None:
        clear_all()

    def is_available(self) -> bool:
        return is_available()

    def ttl(self, key: str) -> int:
        return ttl(key)

    def info(self) -> dict:
        return info()


# Instancia lista para importar directamente en los controladores
page_cache = PageCache()
