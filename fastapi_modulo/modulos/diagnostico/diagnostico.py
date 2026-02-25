import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()
BASE_TEMPLATE_PATH = os.path.join("fastapi_modulo", "templates", "modulos", "diagnostico")


def _bind_core_symbols() -> None:
    if globals().get('_CORE_BOUND'):
        return
    from fastapi_modulo import main as core

    names = [
        'render_backend_page',
        '_render_blank_management_screen',
    ]
    for name in names:
        globals()[name] = getattr(core, name)
    globals()['_CORE_BOUND'] = True


def _load_template(filename: str) -> str:
    path = os.path.join(BASE_TEMPLATE_PATH, filename)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return "<p>No se pudo cargar la vista de diagnóstico.</p>"


@router.get('/diagnostico', response_class=HTMLResponse)
def diagnostico_page(request: Request):
    _bind_core_symbols()
    return _render_blank_management_screen(request, 'Diagnóstico')


@router.get('/diagnostico/foda', response_class=HTMLResponse)
def diagnostico_foda_page(request: Request):
    _bind_core_symbols()
    return render_backend_page(
        request,
        title='FODA',
        description='Identifica factores internos y externos para el diagnóstico estratégico.',
        content=_load_template("foda.html"),
        hide_floating_actions=True,
        show_page_header=True,
    )


@router.get('/diagnostico/pestel', response_class=HTMLResponse)
def diagnostico_pestel_page(request: Request):
    _bind_core_symbols()
    return render_backend_page(
        request,
        title='PESTEL',
        description='Analiza factores externos que impactan la estrategia institucional.',
        content=_load_template("pestel.html"),
        hide_floating_actions=True,
        show_page_header=True,
    )


@router.get('/diagnostico/porter', response_class=HTMLResponse)
def diagnostico_porter_page(request: Request):
    _bind_core_symbols()
    return render_backend_page(
        request,
        title='PORTER',
        description='Evalúa las cinco fuerzas competitivas para priorizar decisiones estratégicas.',
        content=_load_template("porter.html"),
        hide_floating_actions=True,
        show_page_header=True,
    )


@router.get('/diagnostico/percepcion-cliente', response_class=HTMLResponse)
def diagnostico_percepcion_cliente_page(request: Request):
    _bind_core_symbols()
    return render_backend_page(
        request,
        title='Percepción del cliente',
        description='Monitorea feedback para detectar fortalezas y brechas del servicio.',
        content=_load_template("percepcion_cliente.html"),
        hide_floating_actions=True,
        show_page_header=True,
    )
