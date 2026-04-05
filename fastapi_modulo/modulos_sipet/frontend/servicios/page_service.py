"""
servicios/page_service.py
─────────────────────────────────────────────────────────────────────────────
Lógica de negocio sobre páginas del módulo frontend.

Responsabilidades:
  • Resolver qué página es la home pública activa.
  • Determinar si una ruta pertenece a una página pública del sitio.
  • Cargar el modelo FormDefinition de forma diferida y segura.

Uso típico:
    from fastapi_modulo.modulos_sipet.frontend.servicios.page_service import (
        resolve_public_home_slug,
        is_public_frontend_page_path,
        load_form_definition_model,
    )
"""

from __future__ import annotations

from importlib import import_module
from typing import Optional


def resolve_public_home_slug() -> str:
    """
    Devuelve el slug de la página marcada como home y publicada.
    Si no existe ninguna, retorna 'inicio' como fallback.
    """
    from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import list_pages

    pages = list_pages()
    home_page = next(
        (
            page for page in pages
            if bool(page.get("is_home"))
            and str(page.get("status") or "").strip() == "published"
            and str(page.get("slug") or "").strip()
        ),
        None,
    )
    if home_page:
        return str(home_page.get("slug") or "").strip() or "inicio"
    return "inicio"


def is_public_frontend_page_path(path: str) -> bool:
    """
    Determina si una ruta HTTP corresponde a una página pública del frontend.

    Reconoce:
      /web  →  True
      /web/<slug>  →  True si la página existe y está publicada
      /backend/<slug>  →  idem

    Excluye rutas reservadas del sistema.
    """
    from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import get_page_by_slug

    normalized = str(path or "").strip()

    if normalized in {"/web", "/web/"}:
        return True

    if normalized.startswith("/web/"):
        slug = (normalized[len("/web/"):] or "").strip().strip("/")
    elif normalized.startswith("/backend/"):
        slug = (normalized[len("/backend/"):] or "").strip().strip("/")
    else:
        return False

    if not slug or "/" in slug or slug in {"login", "404", "passkey"}:
        return False
    if slug in {"descripcion", "funcionalidades", "inicio"}:
        return True

    try:
        return bool(get_page_by_slug(slug, published_only=True))
    except Exception:
        return False


def load_form_definition_model() -> Optional[type]:
    """
    Carga el modelo FormDefinition del módulo de plantillas si está disponible.
    Prueba ambas rutas conocidas de instalación del módulo.
    Devuelve None si el módulo no está instalado.
    """
    for module_path in (
        "fastapi_modulo.modulos_sipet.plantillas.modelos.plantillas_db_models",
        "fastapi_modulo.modulos.plantillas.modelos.plantillas_db_models",
    ):
        try:
            module = import_module(module_path)
            return getattr(module, "FormDefinition", None)
        except Exception:
            continue
    return None
