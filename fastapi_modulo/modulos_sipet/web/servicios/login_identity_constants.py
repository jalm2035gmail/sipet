# -*- coding: utf-8 -*-
"""Constantes de identidad de login para evitar importaciones circulares."""

LEGACY_LOGIN_IDENTITY_CONFIG_PATH = (
    "fastapi_modulo/modulos_sipet/web/identidad_login.json"
)
LOGIN_IDENTITY_IMAGE_DIR = "fastapi_modulo/templates/imagenes"

DEFAULT_LOGIN_IDENTITY = {
    "favicon_filename": "icon.png",
    "logo_filename": "icon.png",
    "login_logo_filename": "icon.png",
    "desktop_bg_filename": "fondo.jpg",
    "mobile_bg_filename": "movil.jpg",
    "company_short_name": "AVAN",
    "login_message": "Incrementando el nivel de eficiencia",
    "menu_position": "arriba",
}
