from __future__ import annotations

from fastapi_modulo.modulos.multitienda.vistas.utils import load_multitienda_template


def cupones_html() -> str:
    return load_multitienda_template("cupones.html")
