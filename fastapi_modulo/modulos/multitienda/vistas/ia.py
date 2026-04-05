from __future__ import annotations

from fastapi_modulo.modulos.multitienda.vistas.utils import load_multitienda_template


def ia_html() -> str:
    return load_multitienda_template("ia.html")
