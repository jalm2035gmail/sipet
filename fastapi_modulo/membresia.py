from html import escape

from sqlalchemy import Column, Integer, String, Text
from fastapi_modulo.db import Base, SessionLocal, engine
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

membresia_router = APIRouter()
templates = Jinja2Templates(directory="fastapi_modulo/templates")


def _get_colores_context() -> dict:
    from fastapi_modulo.main import get_colores_context
    return get_colores_context()


class Membresia(Base):
    __tablename__ = "membresias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    caracteristicas = Column(Text, nullable=True)
    tipo = Column(String(50), nullable=False)

    def __repr__(self):
        return f"<Membresia(nombre={self.nombre}, tipo={self.tipo})>"


def _ensure_membresia_table() -> None:
    Membresia.__table__.create(bind=engine, checkfirst=True)


def _render_base(request: Request, title: str, description: str, content: str):
    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "title": title,
            "description": description,
            "page_title": title,
            "page_description": description,
            "section_label": "",
            "section_title": "",
            "content": content,
            "floating_actions_html": "",
            "floating_actions_screen": "personalization",
            "hide_floating_actions": True,
            "show_page_header": True,
            "colores": _get_colores_context(),
        },
    )


@membresia_router.get("/membresia")
def listar_membresias(request: Request):
    _ensure_membresia_table()
    db = SessionLocal()
    try:
        membresias = db.query(Membresia).order_by(Membresia.id.asc()).all()
    finally:
        db.close()

    rows_html = "".join(
        [
            (
                "<tr>"
                f"<td>{escape(membresia.nombre or '')}</td>"
                f"<td>{escape(membresia.tipo or '')}</td>"
                f"<td>{escape(membresia.caracteristicas or '')}</td>"
                f"<td>{escape(membresia.descripcion or '')}</td>"
                "</tr>"
            )
            for membresia in membresias
        ]
    )
    content = f"""
<section class="form-section">
    <div class="section-title">
        <h2>Membresías</h2>
    </div>
    <div class="color-actions">
        <a href="/membresia/nueva" class="color-btn color-btn--primary">Agregar Membresía</a>
    </div>
    <table>
        <thead>
            <tr>
                <th>Nombre</th>
                <th>Tipo</th>
                <th>Características</th>
                <th>Descripción</th>
            </tr>
        </thead>
        <tbody>
            {rows_html if rows_html else '<tr><td colspan="4">Sin membresías registradas.</td></tr>'}
        </tbody>
    </table>
</section>
"""
    return _render_base(request, "Membresías", "Administra tipos de membresía.", content)


@membresia_router.get("/membresia/nueva")
def nueva_membresia(request: Request):
    content = """
<section class="form-section">
    <div class="section-title">
        <h2>Nueva Membresía</h2>
    </div>
    <form method="post" action="/membresia/nueva" class="usuarios-form-layout">
        <div class="section-grid">
            <label class="form-field">
                <span>Nombre</span>
                <input type="text" id="nombre" name="nombre" required class="campo-personalizado">
            </label>
            <label class="form-field">
                <span>Tipo</span>
                <input type="text" id="tipo" name="tipo" required class="campo-personalizado">
            </label>
            <label class="form-field">
                <span>Características</span>
                <textarea id="caracteristicas" name="caracteristicas" class="campo-personalizado"></textarea>
            </label>
            <label class="form-field">
                <span>Descripción</span>
                <textarea id="descripcion" name="descripcion" class="campo-personalizado"></textarea>
            </label>
        </div>
        <div class="color-actions">
            <button type="submit" class="color-btn color-btn--primary">Guardar</button>
            <a href="/membresia" class="color-btn color-btn--ghost">Cancelar</a>
        </div>
    </form>
</section>
"""
    return _render_base(request, "Nueva Membresía", "Registrar una nueva membresía.", content)


@membresia_router.post("/membresia/nueva")
def crear_membresia(
    request: Request,
    nombre: str = Form(...),
    tipo: str = Form(...),
    caracteristicas: str = Form(None),
    descripcion: str = Form(None),
):
    del request
    _ensure_membresia_table()
    db = SessionLocal()
    try:
        membresia = Membresia(
            nombre=(nombre or "").strip(),
            tipo=(tipo or "").strip(),
            caracteristicas=(caracteristicas or "").strip(),
            descripcion=(descripcion or "").strip(),
        )
        db.add(membresia)
        db.commit()
    finally:
        db.close()
    return RedirectResponse(url="/membresia", status_code=303)
