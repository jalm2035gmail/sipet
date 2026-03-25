from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from fastapi_modulo.modulos_sipet.web.servicios.template_context_service import (
    build_backend_context,
    build_login_context,
    build_not_found_context,
    get_login_identity_context,
    resolve_sidebar_logo_url,
)
from fastapi_modulo.modulos_sipet.web.servicios.ui_shell_service import build_view_buttons_html

BACKEND_BASE_TEMPLATE = "modulos_sipet/web/vistas/base_backend.html"
LOGIN_TEMPLATE = "web_login.html"
NOT_FOUND_TEMPLATE = "not_found.html"
NO_ACCESS_TEMPLATE = "modulos_sipet/web/vistas/no_access.html"


def get_templates(request: Optional[Request] = None) -> Jinja2Templates:
    if request is not None:
        app_templates = getattr(getattr(request, "app", None), "state", None)
        if app_templates is not None:
            templates = getattr(app_templates, "templates", None)
            if templates is not None:
                return templates
    return Jinja2Templates(directory=["fastapi_modulo/templates", "fastapi_modulo"])


def not_found_context(request: Request, title: str = "Pagina no existe") -> Dict[str, str]:
    return build_not_found_context(request, title=title)


def render_login_template(
    request: Request,
    *,
    title: str = "Login",
    login_error: str = "",
    status_code: int = 200,
    **extra: object,
) -> HTMLResponse:
    return get_templates(request).TemplateResponse(
        LOGIN_TEMPLATE,
        build_login_context(request, title=title, login_error=login_error, **extra),
        status_code=status_code,
    )


def render_not_found_template(
    request: Request,
    *,
    title: str = "Pagina no existe",
    status_code: int = 200,
    **extra: object,
) -> HTMLResponse:
    context = build_not_found_context(request, title=title)
    context.update(extra)
    return get_templates(request).TemplateResponse(
        NOT_FOUND_TEMPLATE,
        context,
        status_code=status_code,
    )

def render_backend_main(
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
    rendered_view_buttons = view_buttons_html or build_view_buttons_html(view_buttons)
    return get_templates(request).TemplateResponse(
        BACKEND_BASE_TEMPLATE,
        build_backend_context(
            request,
            title=title,
            subtitle=subtitle,
            description=description,
            content=content,
            view_buttons_html=rendered_view_buttons,
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
        ),
    )


def render_no_access_module_page(
    request: Request,
    title: str,
    description: str,
    message: str = "Sin acceso, consulte con el administrador",
) -> HTMLResponse:
    return get_templates(request).TemplateResponse(
        NO_ACCESS_TEMPLATE,
        build_backend_context(
            request,
            title=title,
            description=description,
            content="",
            hide_floating_actions=True,
            show_page_header=True,
            no_access_message=message,
            no_access_logo_url=resolve_sidebar_logo_url(get_login_identity_context(request)),
        ),
    )
