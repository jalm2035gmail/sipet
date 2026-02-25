import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()
NOTIFICACIONES_TEMPLATE_PATH = os.path.join(
    'fastapi_modulo', 'templates', 'modulos', 'notificaciones', 'notificaciones.html'
)


def _load_notificaciones_template() -> str:
    try:
        with open(NOTIFICACIONES_TEMPLATE_PATH, 'r', encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return '<p>No se pudo cargar la vista de notificaciones.</p>'


@router.get('/notificaciones', response_class=HTMLResponse)
def notificaciones_page(request: Request):
    from fastapi_modulo.main import render_backend_page

    return render_backend_page(
        request,
        title='Notificaciones',
        description='Consulta notificaciones del sistema y de flujo de aprobación.',
        content=_load_notificaciones_template(),
        hide_floating_actions=True,
        show_page_header=True,
    )
