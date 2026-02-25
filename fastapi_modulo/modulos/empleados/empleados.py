import os
import uuid
import json
from pathlib import Path
from typing import Dict, Any, List

from fastapi import APIRouter, Request, Body, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi_modulo.db import SessionLocal

router = APIRouter()
COLAB_UPLOAD_DIR = Path("fastapi_modulo/uploads/colaboradores")
COLAB_META_PATH = Path("fastapi_modulo/runtime_store/development/colaboradores_meta.json")


def _load_colab_meta() -> Dict[str, Dict[str, Any]]:
    try:
        if not COLAB_META_PATH.exists():
            return {}
        raw = json.loads(COLAB_META_PATH.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _save_colab_meta(meta: Dict[str, Dict[str, Any]]) -> None:
    COLAB_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    COLAB_META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_admin_role(role_name: str) -> bool:
    role = (role_name or "").strip().lower()
    return role in {"superadministrador", "administrador"}

EMPLEADOS_TEMPLATE_PATH = os.path.join(
    "fastapi_modulo",
    "templates",
    "modulos",
    "empleados",
    "empleados.html",
)


@router.get("/api/colaboradores", response_class=JSONResponse)
def api_listar_colaboradores(request: Request):
    # Import diferido para evitar importación circular con fastapi_modulo.main.
    from fastapi_modulo.main import Usuario, _decrypt_sensitive

    db = SessionLocal()
    try:
        meta = _load_colab_meta()
        rows = db.query(Usuario).all()
        data: List[Dict[str, Any]] = [
            {
                "id": u.id,
                "nombre": u.nombre or "",
                "usuario": (_decrypt_sensitive(u.usuario) or "").strip(),
                "correo": (_decrypt_sensitive(u.correo) or "").strip(),
                "departamento": u.departamento or "",
                "imagen": u.imagen or "",
                "jefe": u.jefe or "",
                "puesto": u.puesto or "",
                "colaborador": bool(meta.get(str(u.id), {}).get("colaborador", False)),
                "estado": "Activo" if getattr(u, "is_active", True) else "Inactivo",
            }
            for u in rows
        ]
        viewer_username = (getattr(request.state, "user_name", None) or "").strip().lower()
        viewer_role = (getattr(request.state, "user_role", None) or "").strip().lower()
        can_view_all = _is_admin_role(viewer_role)
        if not can_view_all:
            data = [row for row in data if (row.get("usuario") or "").strip().lower() == viewer_username]
        return {"success": True, "data": data, "viewer_role": viewer_role, "can_view_all": can_view_all}
    finally:
        db.close()


@router.get("/api/colaboradores/organigrama", response_class=JSONResponse)
def api_organigrama_colaboradores(request: Request):
    # Import diferido para evitar importación circular con fastapi_modulo.main.
    from fastapi_modulo.main import Usuario, _decrypt_sensitive

    db = SessionLocal()
    try:
        meta = _load_colab_meta()
        rows = db.query(Usuario).all()
        all_rows: List[Dict[str, Any]] = [
            {
                "id": u.id,
                "nombre": u.nombre or "",
                "usuario": (_decrypt_sensitive(u.usuario) or "").strip(),
                "correo": (_decrypt_sensitive(u.correo) or "").strip(),
                "departamento": u.departamento or "",
                "imagen": u.imagen or "",
                "jefe": u.jefe or "",
                "puesto": u.puesto or "",
                "colaborador": bool(meta.get(str(u.id), {}).get("colaborador", False)),
                "estado": "Activo" if getattr(u, "is_active", True) else "Inactivo",
            }
            for u in rows
        ]
        # Solo nodos marcados como colaborador entran al organigrama.
        all_rows = [row for row in all_rows if bool(row.get("colaborador"))]

        viewer_username = (getattr(request.state, "user_name", None) or "").strip().lower()
        viewer_role = (getattr(request.state, "user_role", None) or "").strip().lower()
        can_view_all = _is_admin_role(viewer_role)
        if can_view_all:
            return {"success": True, "data": all_rows, "viewer_role": viewer_role, "can_view_all": True}

        # Usuario regular: solo él + subordinados hacia abajo (sin jefes hacia arriba).
        me = None
        for row in all_rows:
            if (row.get("usuario") or "").strip().lower() == viewer_username:
                me = row
                break
        if not me:
            return {"success": True, "data": [], "viewer_role": viewer_role, "can_view_all": False}

        visible_ids = {int(me["id"])}
        queue = [me]
        while queue:
            current = queue.pop(0)
            current_name = (current.get("nombre") or "").strip().lower()
            current_user = (current.get("usuario") or "").strip().lower()
            for row in all_rows:
                if int(row["id"]) in visible_ids:
                    continue
                boss = (row.get("jefe") or "").strip().lower()
                if boss and boss in {current_name, current_user}:
                    visible_ids.add(int(row["id"]))
                    queue.append(row)

        filtered = [row for row in all_rows if int(row["id"]) in visible_ids]
        return {"success": True, "data": filtered, "viewer_role": viewer_role, "can_view_all": False}
    finally:
        db.close()


@router.post("/api/colaboradores", response_class=JSONResponse)
def api_guardar_colaborador(request: Request, data: dict = Body(...)):
    # Import diferido para evitar importación circular con fastapi_modulo.main.
    from fastapi_modulo.main import (
        Usuario,
        Rol,
        _decrypt_sensitive,
        _encrypt_sensitive,
        _sensitive_lookup_hash,
        hash_password,
        require_admin_or_superadmin,
    )
    require_admin_or_superadmin(request)
    nombre = (data.get("nombre") or "").strip()
    usuario_login = (data.get("usuario") or "").strip()
    correo = (data.get("correo") or "").strip()
    departamento = (data.get("departamento") or "").strip()
    puesto = (data.get("puesto") or "").strip()
    celular = (data.get("celular") or "").strip()
    nivel_organizacional = (data.get("nivel_organizacional") or "").strip()
    imagen = (data.get("imagen") or "").strip()
    colaborador = bool(data.get("colaborador"))

    if not nombre or not usuario_login or not correo:
        return JSONResponse(
            {"success": False, "error": "Nombre, usuario y correo son obligatorios"},
            status_code=400,
        )

    db = SessionLocal()
    try:
        role_usuario = db.query(Rol).filter(Rol.nombre == "usuario").first()
        rol_id = role_usuario.id if role_usuario else None
        user_hash = _sensitive_lookup_hash(usuario_login)
        email_hash = _sensitive_lookup_hash(correo)

        existing = (
            db.query(Usuario)
            .filter((Usuario.usuario_hash == user_hash) | (Usuario.correo_hash == email_hash))
            .first()
        )
        if not existing:
            existing = (
                db.query(Usuario)
                .filter((Usuario.usuario == usuario_login) | (Usuario.correo == correo))
                .first()
            )

        if existing:
            existing.nombre = nombre
            existing.usuario = _encrypt_sensitive(usuario_login)
            existing.usuario_hash = user_hash
            existing.correo = _encrypt_sensitive(correo)
            existing.correo_hash = email_hash
            existing.departamento = departamento
            existing.puesto = puesto
            existing.celular = celular
            existing.coach = nivel_organizacional
            existing.imagen = imagen or None
            existing.role = existing.role or "usuario"
            existing.rol_id = existing.rol_id or rol_id
            existing.is_active = True
            db.add(existing)
            db.commit()
            db.refresh(existing)
            meta = _load_colab_meta()
            meta[str(existing.id)] = {"colaborador": colaborador}
            _save_colab_meta(meta)
            return {
                "success": True,
                "data": {
                    "id": existing.id,
                    "nombre": existing.nombre or "",
                    "usuario": _decrypt_sensitive(existing.usuario) or "",
                    "correo": _decrypt_sensitive(existing.correo) or "",
                    "departamento": existing.departamento or "",
                    "puesto": existing.puesto or "",
                    "celular": existing.celular or "",
                    "nivel_organizacional": existing.coach or "",
                    "imagen": existing.imagen or "",
                    "colaborador": colaborador,
                    "estado": "Activo" if bool(getattr(existing, "is_active", True)) else "Inactivo",
                },
            }

        nuevo = Usuario(
            nombre=nombre,
            usuario=_encrypt_sensitive(usuario_login),
            usuario_hash=user_hash,
            correo=_encrypt_sensitive(correo),
            correo_hash=email_hash,
            contrasena=hash_password("Temp1234!"),
            departamento=departamento,
            puesto=puesto,
            celular=celular,
            coach=nivel_organizacional,
            imagen=imagen or None,
            role="usuario",
            rol_id=rol_id,
            is_active=True,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        meta = _load_colab_meta()
        meta[str(nuevo.id)] = {"colaborador": colaborador}
        _save_colab_meta(meta)
        return {
            "success": True,
            "data": {
                "id": nuevo.id,
                "nombre": nuevo.nombre or "",
                "usuario": _decrypt_sensitive(nuevo.usuario) or "",
                "correo": _decrypt_sensitive(nuevo.correo) or "",
                "departamento": nuevo.departamento or "",
                "puesto": nuevo.puesto or "",
                "celular": nuevo.celular or "",
                "nivel_organizacional": nuevo.coach or "",
                "imagen": nuevo.imagen or "",
                "colaborador": colaborador,
                "estado": "Activo",
            },
        }
    finally:
        db.close()


@router.post("/api/colaboradores/foto", response_class=JSONResponse)
async def api_subir_foto_colaborador(request: Request, file: UploadFile = File(...)):
    from fastapi_modulo.main import require_admin_or_superadmin

    require_admin_or_superadmin(request)
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo se permiten imágenes")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        ext = ".png"
    COLAB_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"colab_{uuid.uuid4().hex}{ext}"
    target = COLAB_UPLOAD_DIR / filename
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Archivo vacío")
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="La imagen supera 5MB")
    target.write_bytes(content)
    return {"success": True, "url": f"/colaboradores/uploads/{filename}"}


@router.get("/colaboradores/uploads/{filename}")
def api_ver_foto_colaborador(filename: str):
    safe_name = Path(filename).name
    target = COLAB_UPLOAD_DIR / safe_name
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(target)


def _load_empleados_template() -> str:
    try:
        with open(EMPLEADOS_TEMPLATE_PATH, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return """
        <section id="usuario-panel" class="usuario-panel">
            <div id="usuario-view"></div>
        </section>
        """


def _render_empleados_page(
    request: Request,
    title: str = "Usuarios",
    description: str = "Gestiona usuarios, roles y permisos desde la misma pantalla",
) -> HTMLResponse:
    from fastapi_modulo.main import render_backend_page

    return render_backend_page(
        request,
        title=title,
        description=description,
        content=_load_empleados_template(),
        hide_floating_actions=True,
        view_buttons=[
            {"label": "Form", "icon": "/templates/icon/formulario.svg", "view": "form"},
            {"label": "Lista", "icon": "/templates/icon/list.svg", "view": "list", "active": True},
            {"label": "Kanban", "icon": "/templates/icon/kanban.svg", "view": "kanban"},
            {"label": "Organigrama", "icon": "/icon/organigrama.svg", "view": "organigrama"},
        ],
        floating_actions_screen="none",
    )


@router.get("/usuarios", response_class=HTMLResponse)
@router.get("/usuarios-sistema", response_class=HTMLResponse)
def usuarios_page(request: Request):
    return _render_empleados_page(request)


@router.get("/inicio/colaboradores", response_class=HTMLResponse)
def inicio_colaboradores_page(request: Request):
    return _render_empleados_page(
        request,
        title="Colaboradores",
        description="Gestiona colaboradores, roles y permisos desde la misma pantalla",
    )
