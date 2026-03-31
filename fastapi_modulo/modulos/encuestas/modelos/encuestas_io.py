"""
Export / Import portátil de la estructura de encuestas (plantillas e instancias).

No incluye respuestas ni asignaciones — solo la estructura de secciones,
preguntas y opciones, junto con los metadatos de configuración.
"""
from __future__ import annotations

import re
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.encuestas.modelos.encuestas_models import (
    SurveyInstance,
    SurveyOption,
    SurveyQuestion,
    SurveySection,
    SurveyTemplate,
)
from fastapi_modulo.modulos.encuestas.modelos.encuestas_question_catalog import (
    normalize_question_payload,
)
from fastapi_modulo.modulos.encuestas.modelos.encuestas_store import (
    _dt,
    _instance_dict,
    _template_dict,
    _upsert_question_options,
    get_db,
)

_IO_SCHEMA_VERSION = "1.0"

_VALID_EXPORT_TYPES = {"survey_template", "survey_instance"}


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text or secrets.token_hex(4)


def _unique_slug(db: Session, tenant_id: str, base_slug: str) -> str:
    """Devuelve un slug único agregando sufijo numérico si ya existe en el tenant."""
    candidate = base_slug
    suffix = 1
    while db.query(SurveyTemplate.id).filter(
        SurveyTemplate.tenant_id == tenant_id,
        SurveyTemplate.slug == candidate,
    ).first():
        candidate = f"{base_slug}-{suffix}"
        suffix += 1
    return candidate


def _unique_codigo(db: Session, tenant_id: str, base_codigo: str) -> str:
    """Devuelve un codigo único para SurveyInstance."""
    candidate = base_codigo[:60]
    suffix = 1
    while db.query(SurveyInstance.id).filter(
        SurveyInstance.tenant_id == tenant_id,
        SurveyInstance.codigo == candidate,
    ).first():
        candidate = f"{base_codigo[:57]}-{suffix}"
        suffix += 1
    return candidate


# ---------------------------------------------------------------------------
# Serialización para exportar
# ---------------------------------------------------------------------------


def _export_option(option: SurveyOption) -> Dict[str, Any]:
    return {
        "label": option.label,
        "value": option.value,
        "orden": option.orden,
        "score_value": option.score_value,
        "is_correct": option.is_correct,
        "config_json": option.config_json or {},
    }


def _export_question(question: SurveyQuestion) -> Dict[str, Any]:
    return {
        "question_key": question.question_key,
        "titulo": question.titulo,
        "descripcion": question.descripcion,
        "question_type": question.question_type,
        "orden": question.orden,
        "is_required": question.is_required,
        "is_scored": question.is_scored,
        "max_score": question.max_score,
        "min_score": question.min_score,
        "config_json": question.config_json or {},
        "validation_json": question.validation_json or {},
        "logic_json": question.logic_json or {},
        "options": [_export_option(opt) for opt in (question.options or [])],
    }


def _export_section(section: SurveySection) -> Dict[str, Any]:
    return {
        "titulo": section.titulo,
        "descripcion": section.descripcion,
        "orden": section.orden,
        "is_required": section.is_required,
        "settings_json": section.settings_json or {},
        "questions": [_export_question(q) for q in (section.questions or [])],
    }


# ---------------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------------


def export_template_structure(template_id: int, tenant_id: str) -> Optional[Dict[str, Any]]:
    """
    Exporta una plantilla con toda su estructura (secciones → preguntas → opciones).
    Retorna None si no se encuentra.
    """
    db = get_db()
    try:
        obj = (
            db.query(SurveyTemplate)
            .filter(
                SurveyTemplate.id == template_id,
                SurveyTemplate.tenant_id == tenant_id,
            )
            .first()
        )
        if not obj:
            return None
        return {
            "schema_version": _IO_SCHEMA_VERSION,
            "type": "survey_template",
            "exported_at": datetime.utcnow().isoformat(),
            "template": {
                "nombre": obj.nombre,
                "slug": obj.slug,
                "descripcion": obj.descripcion,
                "categoria": obj.categoria,
                "survey_type": obj.survey_type,
                "scoring_mode": obj.scoring_mode,
                "settings_json": obj.settings_json or {},
                "validation_rules_json": obj.validation_rules_json or {},
                "sections": [_export_section(s) for s in (obj.sections or [])],
            },
        }
    finally:
        db.close()


def export_instance_structure(instance_id: int, tenant_id: str) -> Optional[Dict[str, Any]]:
    """
    Exporta la estructura de una instancia (configuración + secciones → preguntas → opciones).
    No incluye respuestas, asignaciones ni tokens de acceso.
    """
    db = get_db()
    try:
        obj = (
            db.query(SurveyInstance)
            .filter(
                SurveyInstance.id == instance_id,
                SurveyInstance.tenant_id == tenant_id,
            )
            .first()
        )
        if not obj:
            return None
        return {
            "schema_version": _IO_SCHEMA_VERSION,
            "type": "survey_instance",
            "exported_at": datetime.utcnow().isoformat(),
            "instance": {
                "nombre": obj.nombre,
                "descripcion": obj.descripcion,
                "publication_mode": obj.publication_mode,
                "audience_mode": obj.audience_mode,
                "anonymity_mode": obj.anonymity_mode,
                "is_public_link_enabled": False,
                "source_app": obj.source_app,
                "external_entity_type": obj.external_entity_type,
                "external_entity_id": obj.external_entity_id,
                "settings_json": obj.settings_json or {},
                "publication_rules_json": obj.publication_rules_json or {},
                "sections": [_export_section(s) for s in (obj.sections or [])],
            },
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Creación de secciones/preguntas/opciones desde payload importado
# ---------------------------------------------------------------------------


def _import_sections(
    db: Session,
    template_id: int,
    instance_id: Optional[int],
    tenant_id: str,
    sections: List[Dict[str, Any]],
) -> None:
    for idx, section_data in enumerate(sections, start=1):
        section = SurveySection(
            tenant_id=tenant_id,
            template_id=template_id,
            instance_id=instance_id,
            titulo=str(section_data.get("titulo") or f"Sección {idx}"),
            descripcion=section_data.get("descripcion"),
            orden=int(section_data.get("orden") or idx),
            is_required=bool(section_data.get("is_required", False)),
            settings_json=section_data.get("settings_json") or {},
        )
        db.add(section)
        db.flush()
        for q_idx, q_data in enumerate(section_data.get("questions") or [], start=1):
            normalized = normalize_question_payload(q_data)
            question = SurveyQuestion(
                tenant_id=tenant_id,
                template_id=template_id,
                section_id=section.id,
                question_key=normalized.get("question_key"),
                titulo=str(normalized.get("titulo") or f"Pregunta {q_idx}"),
                descripcion=normalized.get("descripcion"),
                question_type=str(normalized.get("question_type") or "short_text"),
                orden=int(normalized.get("orden") or q_idx),
                is_required=bool(normalized.get("is_required", False)),
                is_scored=bool(normalized.get("is_scored", False)),
                max_score=normalized.get("max_score"),
                min_score=normalized.get("min_score"),
                config_json=normalized.get("config_json") or {},
                validation_json=normalized.get("validation_json") or {},
                logic_json=normalized.get("logic_json") or {},
            )
            db.add(question)
            db.flush()
            _upsert_question_options(db, question, tenant_id, normalized.get("options") or [])


# ---------------------------------------------------------------------------
# IMPORT
# ---------------------------------------------------------------------------


def import_survey(
    payload: Dict[str, Any],
    tenant_id: str,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Importa una encuesta desde un payload JSON exportado previamente.

    - ``type == "survey_template"`` → crea una SurveyTemplate en estado draft.
    - ``type == "survey_instance"`` → crea una SurveyTemplate + SurveyInstance en estado draft.

    Retorna un dict con ``type`` y los objetos creados.
    """
    export_type = str(payload.get("type") or "")
    if export_type not in _VALID_EXPORT_TYPES:
        raise ValueError(
            f"Tipo de exportación no reconocido: {export_type!r}. "
            f"Se esperaba uno de: {sorted(_VALID_EXPORT_TYPES)}."
        )

    if export_type == "survey_template":
        tpl_data = payload.get("template") or {}
        template = _import_template(tpl_data, tenant_id, created_by)
        return {"type": "survey_template", "template": template}

    inst_data = payload.get("instance") or {}
    template, instance = _import_instance(inst_data, tenant_id, created_by)
    return {"type": "survey_instance", "template": template, "instance": instance}


def _import_template(
    data: Dict[str, Any],
    tenant_id: str,
    created_by: Optional[str],
) -> Dict[str, Any]:
    db = get_db()
    try:
        nombre = str(data.get("nombre") or "Encuesta importada")
        base_slug = _slugify(str(data.get("slug") or nombre))
        slug = _unique_slug(db, tenant_id, base_slug)

        template = SurveyTemplate(
            tenant_id=tenant_id,
            nombre=nombre,
            slug=slug,
            descripcion=data.get("descripcion"),
            categoria=data.get("categoria"),
            survey_type=str(data.get("survey_type") or "general"),
            status="draft",
            version=1,
            scoring_mode=str(data.get("scoring_mode") or "none"),
            settings_json=data.get("settings_json") or {},
            validation_rules_json=data.get("validation_rules_json") or {},
            created_by=created_by,
        )
        db.add(template)
        db.flush()

        _import_sections(db, template.id, None, tenant_id, data.get("sections") or [])

        db.commit()
        db.refresh(template)
        return _template_dict(template)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _import_instance(
    data: Dict[str, Any],
    tenant_id: str,
    created_by: Optional[str],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    db = get_db()
    try:
        nombre = str(data.get("nombre") or "Encuesta importada")
        base_slug = _slugify(nombre)
        slug = _unique_slug(db, tenant_id, base_slug)
        codigo = _unique_codigo(db, tenant_id, slug)

        template = SurveyTemplate(
            tenant_id=tenant_id,
            nombre=nombre,
            slug=slug,
            descripcion=data.get("descripcion"),
            survey_type=str((data.get("settings_json") or {}).get("survey_type") or "general"),
            status="draft",
            version=1,
            scoring_mode=str((data.get("settings_json") or {}).get("scoring_mode") or "none"),
            settings_json=data.get("settings_json") or {},
            validation_rules_json={},
            created_by=created_by,
        )
        db.add(template)
        db.flush()

        instance = SurveyInstance(
            tenant_id=tenant_id,
            template_id=template.id,
            codigo=codigo,
            nombre=nombre,
            descripcion=data.get("descripcion"),
            status="draft",
            publication_mode=str(data.get("publication_mode") or "manual"),
            audience_mode=str(data.get("audience_mode") or "internal"),
            anonymity_mode=str(data.get("anonymity_mode") or "identified"),
            is_public_link_enabled=False,
            source_app=data.get("source_app"),
            external_entity_type=data.get("external_entity_type"),
            external_entity_id=data.get("external_entity_id"),
            settings_json=data.get("settings_json") or {},
            publication_rules_json=data.get("publication_rules_json") or {},
            created_by=created_by,
        )
        db.add(instance)
        db.flush()

        _import_sections(db, template.id, instance.id, tenant_id, data.get("sections") or [])

        db.commit()
        db.refresh(template)
        db.refresh(instance)
        return _template_dict(template), _instance_dict(instance)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
