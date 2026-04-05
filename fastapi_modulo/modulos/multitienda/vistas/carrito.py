from __future__ import annotations

import pathlib

_HTML_PATH = pathlib.Path(__file__).resolve().parent.parent / "marketplace" / "backend" / "templates" / "carrito-public.html"


def carrito_html() -> str:
    return _HTML_PATH.read_text(encoding="utf-8")
