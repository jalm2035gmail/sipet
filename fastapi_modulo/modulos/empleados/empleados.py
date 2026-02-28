import os
import uuid
import json
from pathlib import Path
from typing import Dict, Any, List

from fastapi import APIRouter, Request, Body, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy.exc import IntegrityError
from fastapi_modulo.db import SessionLocal

router = APIRouter()
COLAB_UPLOAD_DIR = Path("fastapi_modulo/uploads/colaboradores")
_APP_ENV = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
_DEFAULT_SIPET_DATA_DIR = (os.environ.get("SIPET_DATA_DIR") or os.path.expanduser("~/.sipet/data")).strip()
_RUNTIME_STORE_DIR = (os.environ.get("RUNTIME_STORE_DIR") or os.path.join(_DEFAULT_SIPET_DATA_DIR, "runtime_store", _APP_ENV)).strip()
COLAB_META_PATH = Path(
    os.environ.get("COLAB_META_PATH") or os.path.join(_RUNTIME_STORE_DIR, "colaboradores_meta.json")
)


def _colab_sort_key(row: Dict[str, Any]) -> tuple[str, str]:
    name = (row.get("nombre") or "").strip().lower()
    user = (row.get("usuario") or "").strip().lower()
    return (name or user, user)


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


def _normalize_poa_access_level(value: Any) -> str:
    raw = str(value or "").strip().lower()
    return "todas_tareas" if raw == "todas_tareas" else "mis_tareas"


def _is_admin_role(role_name: str) -> bool:
    role = (role_name or "").strip().lower()
    if role == "admin":
        role = "administrador"
    if role == "super_admin":
        role = "superadministrador"
    if role == "superadministrdor":
        role = "superadministrador"
    return role in {"superadministrador", "administrador"}


def _allowed_role_assignments(viewer_role: str) -> set[str]:
    role = (viewer_role or "").strip().lower()
    if role == "admin":
        role = "administrador"
    if role == "super_admin":
        role = "superadministrador"
    if role == "superadministrdor":
        role = "superadministrador"
    if role == "superadministrador":
        return {"superadministrador", "usuario", "autoridades", "departamento"}
    if role == "administrador":
        return {"administrador", "usuario", "autoridades", "departamento"}
    return set()

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
    from fastapi_modulo.main import Usuario, Rol, _decrypt_sensitive, normalize_role_name

    db = SessionLocal()
    try:
        meta = _load_colab_meta()
        rows = db.query(Usuario).all()
        names_by_id = {u.id: (u.nombre or "").strip() for u in rows}
        roles_by_id = {role.id: normalize_role_name(role.nombre) for role in db.query(Rol).all()}
        viewer_role = normalize_role_name((getattr(request.state, "user_role", None) or "").strip().lower())
        assignable_roles = sorted(_allowed_role_assignments(viewer_role))
        data: List[Dict[str, Any]] = [
            {
                "id": u.id,
                "nombre": u.nombre or "",
                "usuario": (_decrypt_sensitive(u.usuario) or "").strip(),
                "correo": (_decrypt_sensitive(u.correo) or "").strip(),
                "departamento": u.departamento or "",
                "imagen": u.imagen or "",
                "jefe_inmediato_id": getattr(u, "jefe_inmediato_id", None),
                "jefe": (
                    names_by_id.get(getattr(u, "jefe_inmediato_id", None))
                    or u.jefe
                    or ""
                ),
                "puesto": u.puesto or "",
                "rol": (
                    roles_by_id.get(u.rol_id)
                    or normalize_role_name(getattr(u, "role", "") or "usuario")
                    or "usuario"
                ),
                "colaborador": bool(meta.get(str(u.id), {}).get("colaborador", False)),
                "menu_blocks": meta.get(str(u.id), {}).get("menu_blocks", []),
                "poa_access_level": _normalize_poa_access_level(meta.get(str(u.id), {}).get("poa_access_level", "mis_tareas")),
                "estado": "Activo" if getattr(u, "is_active", True) else "Inactivo",
            }
            for u in rows
        ]
        can_view_all = _is_admin_role(viewer_role)
        viewer_username = (getattr(request.state, "user_name", None) or "").strip().lower()
        if viewer_role == "superadministrador":
            pass
        elif viewer_role == "administrador":
            data = [row for row in data if (row.get("rol") or "").strip().lower() != "superadministrador"]
        else:
            data = [row for row in data if (row.get("usuario") or "").strip().lower() == viewer_username]
            for row in data:
                if (row.get("rol") or "").strip().lower() == "superadministrador":
                    row["rol"] = ""
        data = sorted(data, key=_colab_sort_key)
        return {
            "success": True,
            "data": data,
            "viewer_role": viewer_role,
            "can_view_all": can_view_all,
            "can_manage_access": can_view_all,
            "assignable_roles": assignable_roles,
        }
    finally:
        db.close()


@router.get("/api/colaboradores/organigrama", response_class=JSONResponse)
def api_organigrama_colaboradores(request: Request):
    # Import diferido para evitar importación circular con fastapi_modulo.main.
    from fastapi_modulo.main import Usuario, Rol, _decrypt_sensitive, normalize_role_name

    db = SessionLocal()
    try:
        meta = _load_colab_meta()
        rows = db.query(Usuario).all()
        names_by_id = {u.id: (u.nombre or "").strip() for u in rows}
        roles_by_id = {role.id: normalize_role_name(role.nombre) for role in db.query(Rol).all()}
        all_rows: List[Dict[str, Any]] = [
            {
                "id": u.id,
                "nombre": u.nombre or "",
                "usuario": (_decrypt_sensitive(u.usuario) or "").strip(),
                "correo": (_decrypt_sensitive(u.correo) or "").strip(),
                "departamento": u.departamento or "",
                "imagen": u.imagen or "",
                "jefe_inmediato_id": getattr(u, "jefe_inmediato_id", None),
                "jefe": (
                    names_by_id.get(getattr(u, "jefe_inmediato_id", None))
                    or u.jefe
                    or ""
                ),
                "puesto": u.puesto or "",
                "rol": (
                    roles_by_id.get(u.rol_id)
                    or normalize_role_name(getattr(u, "role", "") or "usuario")
                    or "usuario"
                ),
                "colaborador": bool(meta.get(str(u.id), {}).get("colaborador", False)),
                "estado": "Activo" if getattr(u, "is_active", True) else "Inactivo",
            }
            for u in rows
        ]
        # Solo nodos marcados como colaborador entran al organigrama.
        all_rows = [row for row in all_rows if bool(row.get("colaborador"))]

        viewer_username = (getattr(request.state, "user_name", None) or "").strip().lower()
        viewer_role = normalize_role_name((getattr(request.state, "user_role", None) or "").strip().lower())
        can_view_all = _is_admin_role(viewer_role)
        if viewer_role == "administrador":
            all_rows = [row for row in all_rows if (row.get("rol") or "").strip().lower() != "superadministrador"]
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
                boss_id = row.get("jefe_inmediato_id")
                boss = (row.get("jefe") or "").strip().lower()
                if (boss_id and int(boss_id) == int(current["id"])) or (boss and boss in {current_name, current_user}):
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
        normalize_role_name,
        require_admin_or_superadmin,
    )
    require_admin_or_superadmin(request)
    viewer_role = normalize_role_name((getattr(request.state, "user_role", None) or "").strip().lower())
    allowed_assignments = _allowed_role_assignments(viewer_role)
    nombre = (data.get("nombre") or "").strip()
    incoming_id = data.get("id")
    try:
        incoming_id = int(incoming_id) if incoming_id not in (None, "") else None
    except Exception:
        incoming_id = None
    usuario_login = (data.get("usuario") or "").strip()
    correo = (data.get("correo") or "").strip()
    departamento = (data.get("departamento") or "").strip()
    puesto = (data.get("puesto") or "").strip()
    jefe_inmediato_id = data.get("jefe_inmediato_id")
    try:
        jefe_inmediato_id = int(jefe_inmediato_id) if jefe_inmediato_id not in (None, "") else None
    except Exception:
        jefe_inmediato_id = None
    celular = (data.get("celular") or "").strip()
    nivel_organizacional = (data.get("nivel_organizacional") or "").strip()
    imagen = (data.get("imagen") or "").strip()
    colaborador = bool(data.get("colaborador"))
    requested_role = normalize_role_name((data.get("rol") or "").strip() or "usuario")
    if requested_role not in allowed_assignments:
        requested_role = "usuario"
    raw_menu_blocks = data.get("menu_blocks")
    menu_blocks: List[str] = []
    if isinstance(raw_menu_blocks, list):
        menu_blocks = [str(item).strip() for item in raw_menu_blocks if str(item).strip()]
    elif isinstance(raw_menu_blocks, str) and raw_menu_blocks.strip():
        menu_blocks = [raw_menu_blocks.strip()]
    menu_blocks = sorted(set(menu_blocks))
    poa_access_level = _normalize_poa_access_level(data.get("poa_access_level"))

    if not nombre or not usuario_login:
        return JSONResponse(
            {"success": False, "error": "Nombre y usuario son obligatorios"},
            status_code=400,
        )

    db = SessionLocal()
    try:
        from sqlalchemy import func
        from fastapi_modulo.main import ensure_default_roles
        ensure_default_roles()
        target_role = db.query(Rol).filter(Rol.nombre == requested_role).first()
        if not target_role:
            target_role = (
                db.query(Rol)
                .filter(func.lower(Rol.nombre) == requested_role.lower())
                .first()
            )
        if not target_role:
            target_role = (
                db.query(Rol)
                .filter(func.lower(Rol.nombre) == "usuario")
                .first()
            )
        if not target_role:
            return JSONResponse({"success": False, "error": "Rol no encontrado"}, status_code=404)
        rol_id = target_role.id
        user_hash = _sensitive_lookup_hash(usuario_login)
        email_hash = _sensitive_lookup_hash(correo) if correo else None
        jefe_inmediato_nombre = ""
        if jefe_inmediato_id and incoming_id and int(jefe_inmediato_id) == int(incoming_id):
            return JSONResponse(
                {"success": False, "error": "El jefe inmediato no puede ser el mismo colaborador"},
                status_code=400,
            )
        if jefe_inmediato_id:
            jefe_exists = db.query(Usuario).filter(Usuario.id == jefe_inmediato_id).first()
            if not jefe_exists:
                return JSONResponse(
                    {"success": False, "error": "El jefe inmediato seleccionado no existe"},
                    status_code=400,
                )
            jefe_inmediato_nombre = (jefe_exists.nombre or "").strip()

        existing = None
        if incoming_id:
            existing = db.query(Usuario).filter(Usuario.id == incoming_id).first()
        if not incoming_id:
            duplicate_by_username = db.query(Usuario).filter(Usuario.usuario_hash == user_hash).first()
            if duplicate_by_username:
                return JSONResponse(
                    {"success": False, "error": "No se pudo guardar: el usuario ya existe."},
                    status_code=409,
                )
            if email_hash:
                duplicate_by_email = db.query(Usuario).filter(Usuario.correo_hash == email_hash).first()
                if duplicate_by_email:
                    return JSONResponse(
                        {"success": False, "error": "No se pudo guardar: el correo ya existe."},
                        status_code=409,
                    )

        if existing:
            existing.nombre = nombre
            existing.usuario = _encrypt_sensitive(usuario_login)
            existing.usuario_hash = user_hash
            existing.correo = _encrypt_sensitive(correo) if correo else None
            existing.correo_hash = email_hash
            existing.departamento = departamento
            existing.puesto = puesto
            existing.jefe_inmediato_id = jefe_inmediato_id
            existing.jefe = jefe_inmediato_nombre
            existing.celular = celular
            existing.coach = nivel_organizacional
            existing.imagen = imagen or None
            existing.role = requested_role
            existing.rol_id = rol_id
            existing.is_active = True
            db.add(existing)
            db.commit()
            db.refresh(existing)
            meta = _load_colab_meta()
            meta[str(existing.id)] = {
                "colaborador": colaborador,
                "menu_blocks": menu_blocks,
                "poa_access_level": poa_access_level,
            }
            _save_colab_meta(meta)
            return {
                "success": True,
                "message": "Colaborador actualizado correctamente",
                "data": {
                    "id": existing.id,
                    "nombre": existing.nombre or "",
                    "usuario": _decrypt_sensitive(existing.usuario) or "",
                    "correo": _decrypt_sensitive(existing.correo) or "",
                    "departamento": existing.departamento or "",
                    "puesto": existing.puesto or "",
                    "jefe_inmediato_id": existing.jefe_inmediato_id,
                    "celular": existing.celular or "",
                    "nivel_organizacional": existing.coach or "",
                    "imagen": existing.imagen or "",
                    "rol": requested_role,
                    "colaborador": colaborador,
                    "menu_blocks": menu_blocks,
                    "poa_access_level": poa_access_level,
                    "estado": "Activo" if bool(getattr(existing, "is_active", True)) else "Inactivo",
                },
            }

        nuevo = Usuario(
            nombre=nombre,
            usuario=_encrypt_sensitive(usuario_login),
            usuario_hash=user_hash,
            correo=_encrypt_sensitive(correo) if correo else None,
            correo_hash=email_hash,
            contrasena=hash_password("Temp1234!"),
            departamento=departamento,
            puesto=puesto,
            jefe=jefe_inmediato_nombre,
            jefe_inmediato_id=jefe_inmediato_id,
            celular=celular,
            coach=nivel_organizacional,
            imagen=imagen or None,
            role=requested_role,
            rol_id=rol_id,
            is_active=True,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        meta = _load_colab_meta()
        meta[str(nuevo.id)] = {
            "colaborador": colaborador,
            "menu_blocks": menu_blocks,
            "poa_access_level": poa_access_level,
        }
        _save_colab_meta(meta)
        return {
            "success": True,
            "message": "Colaborador creado correctamente",
            "data": {
                "id": nuevo.id,
                "nombre": nuevo.nombre or "",
                "usuario": _decrypt_sensitive(nuevo.usuario) or "",
                "correo": _decrypt_sensitive(nuevo.correo) or "",
                "departamento": nuevo.departamento or "",
                "puesto": nuevo.puesto or "",
                "jefe_inmediato_id": nuevo.jefe_inmediato_id,
                "celular": nuevo.celular or "",
                "nivel_organizacional": nuevo.coach or "",
                "imagen": nuevo.imagen or "",
                "rol": requested_role,
                "colaborador": colaborador,
                "menu_blocks": menu_blocks,
                "poa_access_level": poa_access_level,
                "estado": "Activo",
            },
        }
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            {
                "success": False,
                "error": "No se pudo guardar: el usuario o correo ya existe.",
            },
            status_code=409,
        )
    except Exception as exc:
        db.rollback()
        return JSONResponse(
            {
                "success": False,
                "error": f"No se pudo guardar: {exc}",
            },
            status_code=500,
        )
    finally:
        db.close()


@router.delete("/api/colaboradores/{colaborador_id}", response_class=JSONResponse)
def api_eliminar_colaborador(request: Request, colaborador_id: int):
    from fastapi_modulo.main import (
        Usuario,
        Rol,
        normalize_role_name,
        require_admin_or_superadmin,
        is_superadmin,
    )

    require_admin_or_superadmin(request)
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.id == colaborador_id).first()
        if not user:
            return JSONResponse({"success": False, "error": "Colaborador no encontrado"}, status_code=404)
        roles_by_id = {role.id: normalize_role_name(role.nombre) for role in db.query(Rol).all()}
        target_role = (
            roles_by_id.get(getattr(user, "rol_id", None))
            or normalize_role_name(getattr(user, "role", "") or "usuario")
            or "usuario"
        )
        if target_role == "superadministrador" and not is_superadmin(request):
            return JSONResponse(
                {"success": False, "error": "Solo superadministrador puede eliminar superadministradores"},
                status_code=403,
            )
        db.delete(user)
        db.commit()
        meta = _load_colab_meta()
        key = str(colaborador_id)
        if key in meta:
            del meta[key]
            _save_colab_meta(meta)
        return {"success": True}
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
