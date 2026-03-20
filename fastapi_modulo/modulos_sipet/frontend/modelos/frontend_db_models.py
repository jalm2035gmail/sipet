"""
modelos/frontend_db_models.py
─────────────────────────────────────────────────────────────────────────────
Modelos SQLAlchemy del módulo frontend.

Tablas:
  • frontend_pages          — páginas del builder GrapesJS (existente)
  • frontend_page_versions  — historial de versiones por página (existente)
  • frontend_contacts       — mensajes del formulario de contacto público (NUEVO)
  • frontend_brand          — configuración de marca clave-valor (NUEVO)
  • frontend_tasas          — tasas de interés editables desde el builder (NUEVO)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from fastapi_modulo.core.db import MAIN


class FrontendPage(MAIN):
    """Páginas creadas y editadas con el constructor GrapesJS."""

    __tablename__ = "frontend_pages"

    id         = Column(String,  primary_key=True, index=True)
    title      = Column(String,  nullable=False, default="")
    slug       = Column(String,  nullable=False, unique=True, index=True, default="")
    status     = Column(String,  nullable=False, default="draft", index=True)
    is_home    = Column(Boolean, default=False, nullable=False)
    gjs_html   = Column(Text,    default="", nullable=False)
    gjs_css    = Column(Text,    default="", nullable=False)
    blocks     = Column(JSON,    default=list, nullable=False)
    meta       = Column(JSON,    default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FrontendPageVersion(MAIN):
    """
    Snapshot de una versión anterior de una página.
    Se guardan hasta _MAX_VERSIONS (5) por página, eliminando las más antiguas.
    """

    __tablename__ = "frontend_page_versions"

    id       = Column(Integer, primary_key=True, index=True)
    page_id  = Column(String,  nullable=False, index=True)
    title    = Column(String,  nullable=False, default="")
    status   = Column(String,  nullable=False, default="draft")
    gjs_html = Column(Text,    default="", nullable=False)
    gjs_css  = Column(Text,    default="", nullable=False)
    meta     = Column(JSON,    default=dict, nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class FrontendContact(MAIN):
    """
    Mensajes recibidos a través del formulario de contacto del sitio público.
    Reemplaza contact_store.json.
    """

    __tablename__ = "frontend_contacts"

    id         = Column(String,  primary_key=True, index=True)
    name       = Column(String,  nullable=False)
    email      = Column(String,  nullable=False, index=True)
    message    = Column(Text,    nullable=False)
    read       = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class FrontendBrand(MAIN):
    """
    Configuración de marca del sitio (colores, logo URL, tipografía, etc.)
    almacenada como pares clave-valor.
    Reemplaza brand_store.json.

    Ejemplos de claves:
      'primary', 'secondary', 'logo_url', 'font_heading', 'sidebar-bottom'
    """

    __tablename__ = "frontend_brand"

    key   = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)


class FrontendTasa(MAIN):
    """
    Tasas de interés editables desde el panel del builder.
    Reemplaza tasas_store.json.

    Cada fila es una tasa identificada por un id único (slug).
    El campo 'position' controla el orden de visualización.
    """

    __tablename__ = "frontend_tasas"

    id       = Column(String,  primary_key=True, index=True)   # ej. "ahorro_vista"
    label    = Column(String,  nullable=False)                  # ej. "Ahorro a la vista"
    rate     = Column(String,  nullable=False)                  # ej. "3.50" (string para preservar decimales exactos)
    color    = Column(String,  nullable=False, default="#3b82f6")
    unit     = Column(String,  nullable=False, default="% anual")
    position = Column(Integer, nullable=False, default=0, index=True)  # orden en el listado

