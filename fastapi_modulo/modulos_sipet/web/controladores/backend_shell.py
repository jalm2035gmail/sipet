from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import Request
from fastapi.responses import HTMLResponse

from fastapi_modulo.modulos_sipet.web.controladores.backend_middleware import enforce_backend_login
from fastapi_modulo.modulos_sipet.web.servicios.template_service import render_backend_main


def _render_backend_MAIN(
    request: Request,
    title: str,
    subtitle: Optional[str] = None,
    description: Optional[str] = None,
    content: str = "",
    view_buttons: Optional[List[Dict]] = None,
    view_buttons_html: str = "",
    hide_floating_actions: bool = True,
    show_page_header: bool = True,
    page_title: Optional[str] = None,
    page_description: Optional[str] = None,
    section_title: Optional[str] = None,
    section_label: Optional[str] = None,
    floating_buttons: Optional[List[Dict]] = None,
    floating_actions_html: str = "",
    floating_actions_screen: str = "personalization",
    **extra: object,
) -> HTMLResponse:
    return render_backend_main(
        request=request,
        title=title,
        subtitle=subtitle,
        description=description,
        content=content,
        view_buttons=view_buttons,
        view_buttons_html=view_buttons_html,
        hide_floating_actions=hide_floating_actions,
        show_page_header=show_page_header,
        page_title=page_title,
        page_description=page_description,
        section_title=section_title,
        section_label=section_label,
        floating_buttons=floating_buttons,
        floating_actions_html=floating_actions_html,
        floating_actions_screen=floating_actions_screen,
        **extra,
    )


def backend_screen(
    request: Request,
    title: str,
    subtitle: Optional[str] = None,
    description: Optional[str] = None,
    content: str = "",
    view_buttons: Optional[List[Dict]] = None,
    view_buttons_html: str = "",
    floating_buttons: Optional[List[Dict]] = None,
    hide_floating_actions: bool = False,
    show_page_header: bool = True,
    page_title: Optional[str] = None,
    page_description: Optional[str] = None,
    section_title: Optional[str] = None,
    section_label: Optional[str] = None,
    **extra: object,
):
    return _render_backend_MAIN(
        request=request,
        title=title,
        subtitle=subtitle,
        description=description,
        content=content,
        view_buttons=view_buttons,
        view_buttons_html=view_buttons_html,
        hide_floating_actions=hide_floating_actions,
        show_page_header=show_page_header,
        page_title=page_title,
        page_description=page_description,
        section_title=section_title,
        section_label=section_label,
        floating_buttons=floating_buttons,
        **extra,
    )


def render_backend_page(
    request: Request,
    title: str,
    description: str = "",
    content: str = "",
    subtitle: Optional[str] = None,
    hide_floating_actions: bool = True,
    view_buttons: Optional[List[Dict]] = None,
    view_buttons_html: str = "",
    floating_actions_html: str = "",
    floating_actions_screen: str = "personalization",
    show_page_header: bool = True,
    section_title: Optional[str] = None,
    section_label: Optional[str] = None,
    **extra: object,
) -> HTMLResponse:
    return _render_backend_MAIN(
        request=request,
        title=title,
        subtitle=subtitle,
        description=description,
        content=content,
        view_buttons=view_buttons,
        view_buttons_html=view_buttons_html,
        hide_floating_actions=hide_floating_actions,
        show_page_header=show_page_header,
        page_title=title,
        page_description=description,
        section_title=section_title,
        section_label=section_label,
        floating_actions_html=floating_actions_html,
        floating_actions_screen=floating_actions_screen,
        **extra,
    )
