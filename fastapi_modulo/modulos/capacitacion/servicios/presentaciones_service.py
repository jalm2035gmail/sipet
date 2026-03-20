from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.capacitacion.modelos.db_models import (
    CapAssetBiblioteca,
    CapDiapositiva,
    CapElemento,
    CapPresentacion,
    CapPresentacionVersion
)
from fastapi_modulo.modulos.capacitacion.repositorios import presentaciones_repository as repo
from fastapi_modulo.modulos.capacitacion.servicios.audit_service import registrar_evento

# Asegurar que el esquema existe
repo.ensure_schema()


# ============================================================================
# TEMPLATES PREDEFINIDOS
# ============================================================================

DEFAULT_TEMPLATES = [
    {
        "key": "corporativo",
        "nombre": "Corporativo limpio",
        "tema": "azul",
        "descripcion": "Portadas sobrias, bloques de indicadores y llamadas a la acción.",
        "slides": [
            {
                "titulo": "Portada",
                "layout_key": "hero-cover",
                "bg_color": "#f8fbff"
            },
            {
                "titulo": "Contenido",
                "layout_key": "two-columns",
                "bg_color": "#ffffff"
            }
        ],
    },
    {
        "key": "cumplimiento",
        "nombre": "Cumplimiento",
        "tema": "granate",
        "descripcion": "Ideal para políticas, normativa y seguimiento institucional.",
        "slides": [
            {
                "titulo": "Portada",
                "layout_key": "hero-centered",
                "bg_color": "#fff7f7"
            },
            {
                "titulo": "Checklist",
                "layout_key": "checklist",
                "bg_color": "#ffffff"
            }
        ],
    },
    {
        "key": "onboarding",
        "nombre": "Onboarding",
        "tema": "teal",
        "descripcion": "Ruta de bienvenida con hitos, hotspots y resúmenes.",
        "slides": [
            {
                "titulo": "Bienvenida",
                "layout_key": "hero-cover",
                "bg_color": "#f4fffb"
            },
            {
                "titulo": "Mapa",
                "layout_key": "spotlight",
                "bg_color": "#ffffff"
            }
        ],
    },
]


# ============================================================================
# FUNCIONES AUXILIARES DE SERIALIZACIÓN Y JSON
# ============================================================================

def _dt(value: Optional[datetime]) -> Optional[str]:
    """
    Convierte un datetime a formato ISO string.
    
    Args:
        value: Objeto datetime o None
        
    Returns:
        String ISO 8601 o None
    """
    if value is None:
        return None
    return value.isoformat() if isinstance(value, datetime) else str(value)


def _loads(value: Any, fallback: Any) -> Any:
    """
    Deserializa un JSON string de forma segura.
    
    Args:
        value: String JSON, dict, list o None
        fallback: Valor de respaldo si falla la deserialización
        
    Returns:
        Objeto deserializado o fallback
    """
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return fallback


def _dumps(value: Any) -> Optional[str]:
    """
    Serializa un objeto a JSON string.
    
    Args:
        value: Objeto a serializar
        
    Returns:
        String JSON o None
    """
    if value is None:
        return None
    return value if isinstance(value, str) else json.dumps(value)


# ============================================================================
# FUNCIONES DE SERIALIZACIÓN DE MODELOS
# ============================================================================

def _version_dict(obj: CapPresentacionVersion) -> Dict[str, Any]:
    """
    Convierte un objeto CapPresentacionVersion a diccionario.
    
    Args:
        obj: Objeto CapPresentacionVersion
        
    Returns:
        Diccionario con datos de la versión
    """
    return {
        "id": obj.id,
        "presentacion_id": obj.presentacion_id,
        "tipo": obj.tipo,
        "etiqueta": obj.etiqueta,
        "actor_key": obj.actor_key,
        "creado_en": _dt(obj.creado_en)
    }


def _asset_dict(obj: CapAssetBiblioteca) -> Dict[str, Any]:
    """
    Convierte un objeto CapAssetBiblioteca a diccionario.
    
    Args:
        obj: Objeto CapAssetBiblioteca
        
    Returns:
        Diccionario con datos del asset
    """
    return {
        "id": obj.id,
        "presentacion_id": obj.presentacion_id,
        "nombre": obj.nombre,
        "tipo": obj.tipo,
        "url": obj.url,
        "thumb_url": obj.thumb_url,
        "tags": _loads(obj.tags_json, []),
        "metadata": _loads(obj.metadata_json, {}),
        "creado_por": obj.creado_por,
        "creado_en": _dt(obj.creado_en),
    }


def _el_dict(obj: CapElemento) -> Dict[str, Any]:
    """
    Convierte un objeto CapElemento a diccionario.
    
    Args:
        obj: Objeto CapElemento
        
    Returns:
        Diccionario con datos del elemento
    """
    contenido = _loads(obj.contenido_json, {})
    
    return {
        "id": obj.id,
        "diapositiva_id": obj.diapositiva_id,
        "tipo": obj.tipo,
        "contenido_json": contenido or {},
        "asset_id": obj.asset_id,
        "animation_json": _loads(obj.animation_json, {}),
        "hotspot_key": obj.hotspot_key,
        "pos_x": obj.pos_x,
        "pos_y": obj.pos_y,
        "width": obj.width,
        "height": obj.height,
        "z_index": obj.z_index,
    }


def _diap_dict(obj: CapDiapositiva, include_elementos: bool = False) -> Dict[str, Any]:
    """
    Convierte un objeto CapDiapositiva a diccionario.
    
    Args:
        obj: Objeto CapDiapositiva
        include_elementos: Si debe incluir los elementos de la diapositiva
        
    Returns:
        Diccionario con datos de la diapositiva
    """
    data = {
        "id": obj.id,
        "presentacion_id": obj.presentacion_id,
        "orden": obj.orden,
        "titulo": obj.titulo,
        "layout_key": obj.layout_key,
        "transition_key": obj.transition_key,
        "animation_json": _loads(obj.animation_json, {}),
        "responsive_json": _loads(obj.responsive_json, {}),
        "bg_color": obj.bg_color or "#ffffff",
        "bg_image_url": obj.bg_image_url,
        "notas": obj.notas,
        "creado_en": _dt(obj.creado_en),
    }
    
    if include_elementos and obj.elementos:
        data["elementos"] = [
            _el_dict(item) 
            for item in sorted(obj.elementos, key=lambda x: x.z_index)
        ]
    
    return data


def _pres_dict(obj: CapPresentacion, include_diapositivas: bool = False) -> Dict[str, Any]:
    """
    Convierte un objeto CapPresentacion a diccionario.
    
    Args:
        obj: Objeto CapPresentacion
        include_diapositivas: Si debe incluir las diapositivas
        
    Returns:
        Diccionario con datos de la presentación
    """
    data = {
        "id": obj.id,
        "titulo": obj.titulo,
        "descripcion": obj.descripcion,
        "autor_key": obj.autor_key,
        "template_key": obj.template_key,
        "theme_key": obj.theme_key,
        "responsive_mode": obj.responsive_mode,
        "autosave": _loads(obj.autosave_json, {}),
        "estado": obj.estado,
        "curso_id": obj.curso_id,
        "miniatura_url": obj.miniatura_url,
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "publicado_por": obj.publicado_por,
        "publicado_en": _dt(obj.publicado_en),
        "num_diapositivas": len(obj.diapositivas) if obj.diapositivas else 0,
        "creado_en": _dt(obj.creado_en),
        "actualizado_en": _dt(obj.actualizado_en),
    }
    
    if include_diapositivas and obj.diapositivas:
        data["diapositivas"] = [
            _diap_dict(item, True) 
            for item in sorted(obj.diapositivas, key=lambda x: x.orden)
        ]
    
    return data


# ============================================================================
# FUNCIONES AUXILIARES DE LÓGICA DE NEGOCIO
# ============================================================================

def _touch_presentacion(
    db: Session,
    pres_id: int,
    actor_key: Optional[str] = None
) -> Optional[CapPresentacion]:
    """
    Actualiza el timestamp de modificación de una presentación.
    
    Args:
        db: Sesión de base de datos
        pres_id: ID de la presentación
        actor_key: Identificador del actor
        
    Returns:
        Objeto CapPresentacion actualizado o None
    """
    presentacion = repo.get_presentacion(db, pres_id)
    if not presentacion:
        return None
    
    presentacion.actualizado_en = datetime.utcnow()
    if actor_key:
        presentacion.actualizado_por = actor_key
    
    db.flush()
    return presentacion


def _snapshot_payload(presentacion: CapPresentacion) -> Dict[str, Any]:
    """
    Genera el payload para un snapshot de presentación.
    
    Args:
        presentacion: Objeto CapPresentacion
        
    Returns:
        Diccionario con datos del snapshot
    """
    return {
        "presentacion": _pres_dict(presentacion),
        "diapositivas": [
            _diap_dict(item, True) 
            for item in sorted(presentacion.diapositivas, key=lambda x: x.orden)
        ],
    }


def _create_snapshot(
    db: Session,
    presentacion: CapPresentacion,
    actor_key: Optional[str] = None,
    tipo: str = "snapshot",
    etiqueta: Optional[str] = None
) -> CapPresentacionVersion:
    """
    Crea un snapshot (versión) de una presentación.
    
    Args:
        db: Sesión de base de datos
        presentacion: Objeto CapPresentacion
        actor_key: Identificador del actor
        tipo: Tipo de snapshot
        etiqueta: Etiqueta descriptiva
        
    Returns:
        Objeto CapPresentacionVersion creado
    """
    payload = _snapshot_payload(presentacion)
    
    return repo.create_version(
        db,
        {
            "tenant_id": presentacion.tenant_id,
            "presentacion_id": presentacion.id,
            "tipo": tipo,
            "etiqueta": etiqueta or tipo,
            "contenido_json": json.dumps(payload),
            "actor_key": actor_key,
            "creado_en": datetime.utcnow(),
        },
    )


# ============================================================================
# SERVICIOS DE TEMPLATES
# ============================================================================

def get_templates() -> List[Dict[str, Any]]:
    """
    Obtiene la lista de templates disponibles.
    
    Returns:
        Lista de templates predefinidos
    """
    return DEFAULT_TEMPLATES


# ============================================================================
# SERVICIOS DE PRESENTACIONES
# ============================================================================

def list_presentaciones(
    autor_key: Optional[str] = None,
    estado: Optional[str] = None,
    curso_id: Optional[int] = None,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista presentaciones con filtros opcionales.
    
    Args:
        autor_key: Clave del autor
        estado: Estado de la presentación
        curso_id: ID del curso
        tenant_id: ID del tenant
        
    Returns:
        Lista de presentaciones como diccionarios
    """
    db = repo.get_db()
    try:
        presentaciones = repo.list_presentaciones(db, autor_key, estado, curso_id)
        return [_pres_dict(item) for item in presentaciones]
    finally:
        db.close()


def get_presentacion(
    pres_id: int,
    tenant_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Obtiene una presentación por ID.
    
    Args:
        pres_id: ID de la presentación
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con datos de la presentación o None
    """
    db = repo.get_db()
    try:
        obj = repo.get_presentacion(db, pres_id)
        return _pres_dict(obj) if obj else None
    finally:
        db.close()


def create_presentacion(
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una nueva presentación con diapositivas iniciales.
    
    Args:
        data: Datos de la presentación
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la presentación creada
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        actor = actor_key or data.get("autor_key")
        template_key = data.get("template_key")
        
        # Buscar template
        template = next(
            (item for item in DEFAULT_TEMPLATES if item["key"] == template_key),
            None
        )
        
        # Preparar payload
        payload = {
            "titulo": data.get("titulo", "Nueva presentación"),
            "descripcion": data.get("descripcion"),
            "autor_key": data.get("autor_key"),
            "template_key": template_key,
            "theme_key": data.get("theme_key") or (
                template.get("tema") if template else None
            ),
            "responsive_mode": data.get("responsive_mode", "desktop"),
            "estado": data.get("estado", "borrador"),
            "curso_id": data.get("curso_id") or None,
            "creado_por": actor,
            "actualizado_por": actor,
            "creado_en": datetime.utcnow(),
            "actualizado_en": datetime.utcnow(),
        }
        
        if tenant_id:
            payload["tenant_id"] = tenant_id
        
        # Si se publica inmediatamente
        if str(payload["estado"]) == "publicado":
            payload["publicado_por"] = actor
            payload["publicado_en"] = datetime.utcnow()
        
        # Crear presentación
        obj = repo.create_presentacion(db, payload)
        
        # Crear diapositivas iniciales desde template
        slides_seed = (
            template.get("slides") if template 
            else [{"titulo": "Diapositiva 1", "layout_key": "blank", "bg_color": "#ffffff"}]
        )
        
        for idx, slide in enumerate(slides_seed):
            repo.create_diapositiva(
                db,
                {
                    "presentacion_id": obj.id,
                    "orden": idx,
                    "titulo": slide.get("titulo", f"Diapositiva {idx + 1}"),
                    "layout_key": slide.get("layout_key", "blank"),
                    "transition_key": slide.get("transition_key", "fade"),
                    "responsive_json": json.dumps({
                        "desktop": {"scale": 1},
                        "tablet": {"scale": 0.9},
                        "mobile": {"scale": 0.75}
                    }),
                    "bg_color": slide.get("bg_color", "#ffffff"),
                    "creado_en": datetime.utcnow(),
                    "tenant_id": obj.tenant_id,
                },
            )
        
        # Crear snapshot inicial
        _create_snapshot(
            db,
            obj,
            actor_key=actor,
            tipo="created",
            etiqueta="Creación inicial"
        )
        
        # Registrar evento de creación
        registrar_evento(
            db,
            "presentacion",
            obj.id,
            "created",
            actor_key=actor,
            actor_nombre=actor_name,
            tenant_id=obj.tenant_id,
            detalle={
                "titulo": obj.titulo,
                "estado": str(obj.estado),
                "template_key": template_key
            }
        )
        
        # Registrar evento de publicación si aplica
        if str(obj.estado) == "publicado":
            registrar_evento(
                db,
                "presentacion",
                obj.id,
                "published",
                actor_key=actor,
                actor_nombre=actor_name,
                tenant_id=obj.tenant_id,
                detalle={"estado": str(obj.estado)}
            )
        
        db.commit()
        db.refresh(obj)
        
        return _pres_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_presentacion(
    pres_id: int,
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Actualiza una presentación existente.
    
    Args:
        pres_id: ID de la presentación
        data: Datos a actualizar
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la presentación actualizada o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        current = repo.get_presentacion(db, pres_id)
        if not current:
            return None
        
        prev_estado = str(current.estado)
        
        # Campos permitidos para actualizar
        allowed_fields = {
            "titulo", "descripcion", "estado", "curso_id",
            "miniatura_url", "template_key", "theme_key", "responsive_mode"
        }
        
        allowed = {
            key: value 
            for key, value in data.items() 
            if key in allowed_fields
        }
        
        # Manejar autosave
        if "autosave" in data:
            allowed["autosave_json"] = _dumps(data.get("autosave", {}))
        
        # Actualizar timestamps
        allowed["actualizado_en"] = datetime.utcnow()
        if actor_key:
            allowed["actualizado_por"] = actor_key
        
        # Si se está publicando
        next_estado = str(allowed.get("estado", prev_estado))
        if next_estado == "publicado" and prev_estado != "publicado":
            allowed["publicado_por"] = actor_key
            allowed["publicado_en"] = datetime.utcnow()
        
        # Actualizar presentación
        obj = repo.update_presentacion(db, pres_id, allowed)
        if not obj:
            return None
        
        # Registrar evento de actualización
        registrar_evento(
            db,
            "presentacion",
            obj.id,
            "updated",
            actor_key=actor_key,
            actor_nombre=actor_name,
            tenant_id=obj.tenant_id,
            detalle={
                "estado_anterior": prev_estado,
                "estado_nuevo": str(obj.estado)
            }
        )
        
        # Registrar evento de publicación si cambió
        if prev_estado != "publicado" and str(obj.estado) == "publicado":
            registrar_evento(
                db,
                "presentacion",
                obj.id,
                "published",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=obj.tenant_id,
                detalle={
                    "estado_anterior": prev_estado,
                    "estado_nuevo": str(obj.estado)
                }
            )
        
        db.commit()
        db.refresh(obj)
        
        return _pres_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_presentacion(
    pres_id: int,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> bool:
    """
    Elimina una presentación.
    
    Args:
        pres_id: ID de la presentación
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        True si se eliminó, False si no existía
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        # Registrar evento antes de eliminar
        obj = repo.get_presentacion(db, pres_id)
        if obj:
            registrar_evento(
                db,
                "presentacion",
                obj.id,
                "deleted",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=obj.tenant_id,
                detalle={"titulo": obj.titulo}
            )
        
        ok = repo.delete_presentacion(db, pres_id)
        if not ok:
            return False
        
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE DIAPOSITIVAS
# ============================================================================

def list_diapositivas(
    pres_id: int,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista todas las diapositivas de una presentación.
    
    Args:
        pres_id: ID de la presentación
        tenant_id: ID del tenant
        
    Returns:
        Lista de diapositivas como diccionarios
    """
    db = repo.get_db()
    try:
        diapositivas = repo.list_diapositivas(db, pres_id)
        return [_diap_dict(item, True) for item in diapositivas]
    finally:
        db.close()


def create_diapositiva(
    pres_id: int,
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una nueva diapositiva en una presentación.
    
    Args:
        pres_id: ID de la presentación
        data: Datos de la diapositiva
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la diapositiva creada
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        # Calcular orden
        orden = len(repo.list_diapositivas(db, pres_id))
        presentacion = repo.get_presentacion(db, pres_id)
        
        # Crear diapositiva
        obj = repo.create_diapositiva(
            db,
            {
                "presentacion_id": pres_id,
                "orden": orden,
                "titulo": data.get("titulo", f"Diapositiva {orden + 1}"),
                "layout_key": data.get("layout_key", "blank"),
                "transition_key": data.get("transition_key", "fade"),
                "animation_json": _dumps(data.get("animation_json", {})),
                "responsive_json": _dumps(data.get("responsive_json", {
                    "desktop": {},
                    "tablet": {},
                    "mobile": {}
                })),
                "bg_color": data.get("bg_color", "#ffffff"),
                "bg_image_url": data.get("bg_image_url"),
                "notas": data.get("notas"),
                "creado_en": datetime.utcnow(),
                "tenant_id": tenant_id or (
                    presentacion.tenant_id if presentacion else "default"
                ),
            },
        )
        
        # Actualizar presentación
        touched = _touch_presentacion(db, pres_id, actor_key)
        if touched:
            registrar_evento(
                db,
                "presentacion",
                touched.id,
                "slide_created",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=touched.tenant_id,
                detalle={
                    "diapositiva_id": obj.id,
                    "titulo": obj.titulo,
                    "layout_key": obj.layout_key
                }
            )
        
        db.commit()
        db.refresh(obj)
        
        return _diap_dict(obj, True)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_diapositiva(
    diap_id: int,
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Actualiza una diapositiva existente.
    
    Args:
        diap_id: ID de la diapositiva
        data: Datos a actualizar
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la diapositiva actualizada o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        obj = repo.get_diapositiva(db, diap_id)
        if not obj:
            return None
        
        # Actualizar campos simples
        updates = {
            "titulo": data.get("titulo", obj.titulo),
            "layout_key": data.get("layout_key", obj.layout_key),
            "transition_key": data.get("transition_key", obj.transition_key),
            "bg_color": data.get("bg_color", obj.bg_color),
            "bg_image_url": data.get("bg_image_url", obj.bg_image_url),
            "notas": data.get("notas", obj.notas),
        }
        
        for key, value in updates.items():
            setattr(obj, key, value)
        
        # Actualizar campos JSON
        if "animation_json" in data:
            obj.animation_json = _dumps(data.get("animation_json", {}))
        if "responsive_json" in data:
            obj.responsive_json = _dumps(data.get("responsive_json", {}))
        
        # Actualizar presentación
        touched = _touch_presentacion(db, obj.presentacion_id, actor_key)
        if touched:
            registrar_evento(
                db,
                "presentacion",
                touched.id,
                "slide_updated",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=touched.tenant_id,
                detalle={
                    "diapositiva_id": obj.id,
                    "titulo": obj.titulo
                }
            )
        
        db.commit()
        db.refresh(obj)
        
        return _diap_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_diapositiva(
    diap_id: int,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> bool:
    """
    Elimina una diapositiva y reordena las restantes.
    
    Args:
        diap_id: ID de la diapositiva
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        True si se eliminó, False si no existía
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        obj = repo.get_diapositiva(db, diap_id)
        if not obj:
            return False
        
        pres_id = obj.presentacion_id
        pres = repo.get_presentacion(db, pres_id)
        
        # Registrar evento
        if pres:
            registrar_evento(
                db,
                "presentacion",
                pres.id,
                "slide_deleted",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=pres.tenant_id,
                detalle={
                    "diapositiva_id": obj.id,
                    "titulo": obj.titulo
                }
            )
        
        # Eliminar diapositiva
        repo.delete_diapositiva(db, diap_id)
        db.flush()
        
        # Reordenar diapositivas restantes
        for index, slide in enumerate(repo.list_diapositivas(db, pres_id)):
            slide.orden = index
        
        # Actualizar presentación
        _touch_presentacion(db, pres_id, actor_key)
        
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def reordenar_diapositivas(
    pres_id: int,
    orden_ids: List[int],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> bool:
    """
    Reordena las diapositivas de una presentación.
    
    Args:
        pres_id: ID de la presentación
        orden_ids: Lista de IDs en el nuevo orden
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        True si se reordenó exitosamente
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        # Actualizar orden
        for index, diap_id in enumerate(orden_ids):
            slide = repo.get_diapositiva(db, diap_id)
            if slide and slide.presentacion_id == pres_id:
                slide.orden = index
        
        # Actualizar presentación
        touched = _touch_presentacion(db, pres_id, actor_key)
        if touched:
            registrar_evento(
                db,
                "presentacion",
                touched.id,
                "slides_reordered",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=touched.tenant_id,
                detalle={"orden_ids": orden_ids}
            )
        
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def duplicate_diapositiva(
    diap_id: int,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Duplica una diapositiva con todos sus elementos.
    
    Args:
        diap_id: ID de la diapositiva a duplicar
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la diapositiva duplicada o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        orig = repo.get_diapositiva(db, diap_id)
        if not orig:
            return None
        
        # Calcular nuevo orden
        new_orden = orig.orden + 1
        
        # Desplazar diapositivas posteriores
        for slide in repo.list_diapositivas(db, orig.presentacion_id):
            if slide.orden >= new_orden:
                slide.orden += 1
        
        # Crear diapositiva duplicada
        new_diap = repo.create_diapositiva(
            db,
            {
                "presentacion_id": orig.presentacion_id,
                "orden": new_orden,
                "titulo": (orig.titulo or "Diapositiva") + " (copia)",
                "layout_key": orig.layout_key,
                "transition_key": orig.transition_key,
                "animation_json": orig.animation_json,
                "responsive_json": orig.responsive_json,
                "bg_color": orig.bg_color,
                "bg_image_url": orig.bg_image_url,
                "notas": orig.notas,
                "creado_en": datetime.utcnow(),
                "tenant_id": orig.tenant_id,
            },
        )
        
        # Duplicar elementos
        for element in orig.elementos:
            repo.create_elemento(
                db,
                {
                    "diapositiva_id": new_diap.id,
                    "tipo": element.tipo,
                    "contenido_json": element.contenido_json,
                    "asset_id": element.asset_id,
                    "animation_json": element.animation_json,
                    "hotspot_key": element.hotspot_key,
                    "pos_x": element.pos_x,
                    "pos_y": element.pos_y,
                    "width": element.width,
                    "height": element.height,
                    "z_index": element.z_index,
                    "creado_en": datetime.utcnow(),
                    "tenant_id": orig.tenant_id,
                },
            )
        
        # Actualizar presentación
        touched = _touch_presentacion(db, orig.presentacion_id, actor_key)
        if touched:
            registrar_evento(
                db,
                "presentacion",
                touched.id,
                "slide_duplicated",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=touched.tenant_id,
                detalle={
                    "origen_id": orig.id,
                    "copia_id": new_diap.id
                }
            )
        
        db.commit()
        db.refresh(new_diap)
        
        return _diap_dict(new_diap, True)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE ELEMENTOS
# ============================================================================

def list_elementos(
    diap_id: int,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista todos los elementos de una diapositiva.
    
    Args:
        diap_id: ID de la diapositiva
        tenant_id: ID del tenant
        
    Returns:
        Lista de elementos como diccionarios
    """
    db = repo.get_db()
    try:
        elementos = repo.list_elementos(db, diap_id)
        return [_el_dict(item) for item in elementos]
    finally:
        db.close()


def save_elementos(
    diap_id: int,
    elementos: List[Dict[str, Any]],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None,
    autosave: bool = False
) -> List[Dict[str, Any]]:
    """
    Guarda los elementos de una diapositiva (reemplaza todos).
    
    Args:
        diap_id: ID de la diapositiva
        elementos: Lista de elementos a guardar
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        autosave: Si es un guardado automático
        
    Returns:
        Lista de elementos guardados como diccionarios
        
    Raises:
        ValueError: Si la diapositiva no existe
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        diap = repo.get_diapositiva(db, diap_id)
        if not diap:
            raise ValueError("La diapositiva no existe")
        
        # Eliminar elementos existentes
        repo.delete_elementos(db, diap_id)
        
        # Crear nuevos elementos
        nuevos = []
        for data in elementos:
            nuevo = repo.create_elemento(
                db,
                {
                    "diapositiva_id": diap_id,
                    "tipo": data.get("tipo", "texto"),
                    "contenido_json": _dumps(data.get("contenido_json", {})),
                    "asset_id": data.get("asset_id"),
                    "animation_json": _dumps(data.get("animation_json", {})),
                    "hotspot_key": data.get("hotspot_key"),
                    "pos_x": float(data.get("pos_x", 10)),
                    "pos_y": float(data.get("pos_y", 10)),
                    "width": float(data.get("width", 30)),
                    "height": float(data.get("height", 20)),
                    "z_index": int(data.get("z_index", 1)),
                    "creado_en": datetime.utcnow(),
                    "tenant_id": diap.tenant_id,
                },
            )
            nuevos.append(nuevo)
        
        # Actualizar presentación
        touched = _touch_presentacion(db, diap.presentacion_id, actor_key)
        
        if touched:
            # Manejar autosave
            if autosave:
                touched.autosave_json = json.dumps({
                    "diapositiva_id": diap.id,
                    "at": _dt(datetime.utcnow())
                })
                _create_snapshot(
                    db,
                    touched,
                    actor_key=actor_key,
                    tipo="autosave",
                    etiqueta="Auto guardado"
                )
            
            # Registrar evento
            registrar_evento(
                db,
                "presentacion",
                touched.id,
                "elements_saved",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=touched.tenant_id,
                detalle={
                    "diapositiva_id": diap.id,
                    "total_elementos": len(nuevos),
                    "autosave": autosave
                }
            )
        
        db.commit()
        
        # Refrescar elementos
        for item in nuevos:
            db.refresh(item)
        
        return [_el_dict(item) for item in nuevos]
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def duplicate_elemento(
    diap_id: int,
    element_id: int,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Duplica un elemento dentro de una diapositiva.
    
    Args:
        diap_id: ID de la diapositiva
        element_id: ID del elemento a duplicar
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con el elemento duplicado o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        diap = repo.get_diapositiva(db, diap_id)
        if not diap:
            return None
        
        # Buscar elemento original
        origen = next(
            (item for item in diap.elementos if item.id == element_id),
            None
        )
        if not origen:
            return None
        
        # Calcular nuevo z_index
        max_z = max([item.z_index for item in diap.elementos] + [0])
        
        # Crear elemento duplicado con offset
        nuevo = repo.create_elemento(
            db,
            {
                "diapositiva_id": diap_id,
                "tipo": origen.tipo,
                "contenido_json": origen.contenido_json,
                "asset_id": origen.asset_id,
                "animation_json": origen.animation_json,
                "hotspot_key": (origen.hotspot_key or "hotspot") + "-" + uuid.uuid4().hex[:6],
                "pos_x": origen.pos_x + 4,
                "pos_y": origen.pos_y + 4,
                "width": origen.width,
                "height": origen.height,
                "z_index": max_z + 1,
                "creado_en": datetime.utcnow(),
                "tenant_id": diap.tenant_id,
            },
        )
        
        # Actualizar presentación
        touched = _touch_presentacion(db, diap.presentacion_id, actor_key)
        if touched:
            registrar_evento(
                db,
                "presentacion",
                touched.id,
                "block_duplicated",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=touched.tenant_id,
                detalle={
                    "diapositiva_id": diap.id,
                    "elemento_id": element_id,
                    "copia_id": nuevo.id
                }
            )
        
        db.commit()
        db.refresh(nuevo)
        
        return _el_dict(nuevo)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE VERSIONES
# ============================================================================

def create_version_snapshot(
    pres_id: int,
    actor_key: Optional[str] = None,
    etiqueta: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Crea un snapshot manual de la presentación.
    
    Args:
        pres_id: ID de la presentación
        actor_key: Identificador del actor
        etiqueta: Etiqueta descriptiva del snapshot
        
    Returns:
        Diccionario con la versión creada o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        pres = repo.get_presentacion(db, pres_id)
        if not pres:
            return None
        
        # Crear snapshot
        obj = _create_snapshot(
            db,
            pres,
            actor_key=actor_key,
            tipo="manual",
            etiqueta=etiqueta or "Versión manual"
        )
        
        # Registrar evento
        registrar_evento(
            db,
            "presentacion",
            pres.id,
            "version_created",
            actor_key=actor_key,
            tenant_id=pres.tenant_id,
            detalle={"version_id": obj.id}
        )
        
        db.commit()
        db.refresh(obj)
        
        return _version_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def list_versiones(pres_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Lista las versiones de una presentación.
    
    Args:
        pres_id: ID de la presentación
        limit: Número máximo de versiones a retornar
        
    Returns:
        Lista de versiones como diccionarios
    """
    db = repo.get_db()
    try:
        versiones = repo.list_versions(db, pres_id, limit=limit)
        return [_version_dict(item) for item in versiones]
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE ASSETS
# ============================================================================

def list_assets(
    pres_id: Optional[int] = None,
    asset_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista assets de la biblioteca.
    
    Args:
        pres_id: ID de la presentación (opcional, para filtrar)
        asset_type: Tipo de asset (opcional, para filtrar)
        
    Returns:
        Lista de assets como diccionarios
    """
    db = repo.get_db()
    try:
        assets = repo.list_assets(db, pres_id, asset_type)
        return [_asset_dict(item) for item in assets]
    finally:
        db.close()


def create_asset(
    data: Dict[str, Any],
    pres_id: Optional[int] = None,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea un nuevo asset en la biblioteca.
    
    Args:
        data: Datos del asset
        pres_id: ID de la presentación (opcional)
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        
    Returns:
        Diccionario con el asset creado
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        obj = repo.create_asset(
            db,
            {
                "tenant_id": tenant_id or "default",
                "presentacion_id": pres_id,
                "nombre": data.get("nombre", "Asset"),
                "tipo": data.get("tipo", "imagen"),
                "url": data.get("url"),
                "thumb_url": data.get("thumb_url"),
                "tags_json": _dumps(data.get("tags", [])),
                "metadata_json": _dumps(data.get("metadata", {})),
                "creado_por": actor_key,
                "creado_en": datetime.utcnow(),
            },
        )
        
        db.commit()
        db.refresh(obj)
        
        return _asset_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
        