"""
servicios/layout_service.py
─────────────────────────────────────────────────────────────────────────────
Utilidades para extraer y recomponer segmentos de layout global (nav/footer)
del HTML de páginas construidas con GrapesJS.

Responsabilidades:
  • Separar el HTML de página en cuerpo, nav global y footer global.
  • Reensamblar los tres segmentos respetando el orden correcto.

Uso típico:
    from fastapi_modulo.modulos_sipet.frontend.servicios.layout_service import (
        extract_global_layout_segments,
        merge_global_layout,
    )

    body, nav, footer = extract_global_layout_segments(page_html)
    full_html = merge_global_layout(body, nav, footer)
"""

from __future__ import annotations

import re

_NAV_RE    = re.compile(r"<nav\b[^>]*>.*?</nav>",       re.IGNORECASE | re.DOTALL)
_FOOTER_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.IGNORECASE | re.DOTALL)


def extract_global_layout_segments(gjs_html: str) -> tuple[str, str, str]:
    """
    Separa el HTML completo en tres partes: cuerpo, nav global y footer global.

    Devuelve:
        (body_html, global_nav, global_footer)
        donde body_html es el HTML sin el nav ni el último footer.
    """
    html = str(gjs_html or "")

    nav_match      = _NAV_RE.search(html)
    footer_matches = list(_FOOTER_RE.finditer(html))
    footer_match   = footer_matches[-1] if footer_matches else None

    global_nav    = nav_match.group(0)    if nav_match    else ""
    global_footer = footer_match.group(0) if footer_match else ""

    body_html = html
    if global_nav:
        body_html = body_html.replace(global_nav, "", 1)
    if global_footer:
        body_html = body_html[:footer_match.start()] + body_html[footer_match.end():]

    return body_html.strip(), global_nav.strip(), global_footer.strip()


def merge_global_layout(body_html: str, global_nav: str, global_footer: str) -> str:
    """
    Reensambla nav + cuerpo (sin nav/footer) + footer en el orden correcto.
    Elimina nav/footer redundantes del body antes de ensamblar.
    """
    clean_body, _, _ = extract_global_layout_segments(body_html)
    return f"{global_nav or ''}{clean_body or ''}{global_footer or ''}"
