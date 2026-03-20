from __future__ import annotations

import os
from io import BytesIO, StringIO
from datetime import datetime
from uuid import uuid4
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
import redis as redis_lib
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.orm import Session, object_session
from openpyxl.utils import get_column_letter

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos.encuestas.modelos.encuestas_question_catalog import (
    QUESTION_TYPE_CATALOG,
    get_question_type_definition,
    normalize_question_payload,
)
from fastapi_modulo.modulos.encuestas.modelos.encuestas_models import (
    SurveyAssignment,
    SurveyAttempt,
    SurveyAudienceGroup,
    SurveyAudienceGroupMember,
    SurveyDispatchLog,
    SurveyEvaluation360,
    SurveyInstance,
    SurveyOption,
    SurveyQuestion,
    SurveyResponse,
    SurveyResponseItem,
    SurveyResult,
    SurveySection,
    SurveyTemplate,
)

_SURVEY_TABLES = [
    SurveyTemplate.__table__,
    SurveyInstance.__table__,
    SurveySection.__table__,
    SurveyQuestion.__table__,
    SurveyOption.__table__,
    SurveyAudienceGroup.__table__,
    SurveyAudienceGroupMember.__table__,
    SurveyAssignment.__table__,
    SurveyResponse.__table__,
    SurveyResponseItem.__table__,
    SurveyResult.__table__,
    SurveyAttempt.__table__,
    SurveyEvaluation360.__table__,
    SurveyDispatchLog.__table__,
]

_SURVEY_SCHEMA_READY = False
_NOTIFICATION_SCHEMA_READY = False

DEFAULT_SURVEY_TEMPLATES: List[Dict[str, Any]] = [
    {
        "nombre": "Encuesta general",
        "slug": "encuesta-general",
        "descripcion": "Plantilla MAIN para levantar percepciones generales.",
        "categoria": "general",
        "survey_type": "general",
        "scoring_mode": "none",
        "settings_json": {},
        "sections": [
            {
                "titulo": "Datos generales",
                "descripcion": "Preguntas abiertas y valoración general.",
                "questions": [
                    {"titulo": "¿Cómo calificarías tu experiencia general?", "question_type": "scale_1_5", "is_required": True},
                    {"titulo": "¿Qué fue lo mejor de la experiencia?", "question_type": "long_text"},
                    {"titulo": "¿Qué deberíamos mejorar?", "question_type": "long_text"},
                ],
            }
        ],
    },
    {
        "nombre": "Satisfacción del cliente",
        "slug": "satisfaccion-del-cliente",
        "descripcion": "Mide satisfacción de servicio y atención recibida.",
        "categoria": "clientes",
        "survey_type": "customer_satisfaction",
        "scoring_mode": "csat",
        "settings_json": {"scoring_mode": "csat"},
        "sections": [
            {
                "titulo": "Atención",
                "questions": [
                    {"titulo": "La atención fue rápida", "question_type": "scale_1_5", "is_required": True},
                    {"titulo": "El trato recibido fue amable", "question_type": "scale_1_5", "is_required": True},
                    {"titulo": "¿Volverías a utilizar el servicio?", "question_type": "yes_no", "is_required": True},
                ],
            }
        ],
    },
    {
        "nombre": "NPS",
        "slug": "nps",
        "descripcion": "Plantilla corta para medir recomendación.",
        "categoria": "clientes",
        "survey_type": "nps",
        "scoring_mode": "nps",
        "settings_json": {"scoring_mode": "nps"},
        "sections": [
            {
                "titulo": "Lealtad",
                "questions": [
                    {"titulo": "¿Qué tan probable es que recomiendes la organización?", "question_type": "nps_0_10", "is_required": True},
                    {"titulo": "¿Cuál es el principal motivo de tu calificación?", "question_type": "long_text"},
                ],
            }
        ],
    },
    {
        "nombre": "Clima laboral corto",
        "slug": "clima-laboral-corto",
        "descripcion": "Pulso rápido de clima laboral interno.",
        "categoria": "talento",
        "survey_type": "employee_climate",
        "scoring_mode": "csat",
        "settings_json": {"scoring_mode": "csat"},
        "sections": [
            {
                "titulo": "Ambiente",
                "questions": [
                    {"titulo": "Me siento motivado en mi trabajo", "question_type": "scale_1_5", "is_required": True},
                    {"titulo": "Tengo claridad sobre mis responsabilidades", "question_type": "scale_1_5", "is_required": True},
                    {"titulo": "Recomendaría esta organización para trabajar", "question_type": "nps_0_10", "is_required": True},
                ],
            }
        ],
    },
    {
        "nombre": "Evaluación 360 básica",
        "slug": "evaluacion-360-basica",
        "descripcion": "Plantilla MAIN para evaluación 360 con anonimato restringido.",
        "categoria": "talento",
        "survey_type": "evaluation_360",
        "scoring_mode": "csat",
        "settings_json": {"scoring_mode": "csat"},
        "anonymity_mode": "restricted",
        "external_entity_type": "evaluation_360",
        "sections": [
            {
                "titulo": "Competencias",
                "questions": [
                    {"titulo": "Demuestra liderazgo en su área", "question_type": "scale_1_5", "is_required": True},
                    {"titulo": "Colabora con el equipo", "question_type": "scale_1_5", "is_required": True},
                    {"titulo": "Comentario cualitativo", "question_type": "long_text"},
                ],
            }
        ],
    },
    {
        "nombre": "Quiz de capacitación",
        "slug": "quiz-de-capacitacion",
        "descripcion": "Evaluación corta de conocimiento posterior a capacitación.",
        "categoria": "capacitacion",
        "survey_type": "quiz",
        "scoring_mode": "quiz",
        "settings_json": {"scoring_mode": "quiz"},
        "sections": [
            {
                "titulo": "Conocimiento",
                "questions": [
                    {
                        "titulo": "¿Cuál es el objetivo principal del curso?",
                        "question_type": "quiz_single_choice",
                        "is_required": True,
                        "options": [
                            {"label": "Actualizar conocimientos", "value": "actualizar", "is_correct": True},
                            {"label": "Realizar una auditoría", "value": "auditoria"},
                            {"label": "Solicitar vacaciones", "value": "vacaciones"},
                        ],
                    },
                    {
                        "titulo": "Selecciona los temas vistos",
                        "question_type": "multiple_choice",
                        "options": [
                            {"label": "Proceso", "value": "proceso", "score_value": 1},
                            {"label": "Políticas", "value": "politicas", "score_value": 1},
                            {"label": "Cafetería", "value": "cafeteria", "score_value": 0},
                        ],
                    },
                ],
            }
        ],
    },
    {
        "nombre": "Mentimeter para capacitación",
        "slug": "mentimeter-capacitacion",
        "descripcion": "Dinámica en vivo para sesiones de capacitación con poll, nube de palabras y escala rápida.",
        "categoria": "capacitacion",
        "survey_type": "live_poll",
        "scoring_mode": "none",
        "settings_json": {"presentation_mode": "mentimeter", "live_session_enabled": True},
        "sections": [
            {
                "titulo": "Participación en vivo",
                "descripcion": "Usa una pregunta por dinámica o duplica la plantilla.",
                "questions": [
                    {
                        "titulo": "¿Qué concepto te resultó más claro?",
                        "question_type": "word_cloud",
                        "is_required": True,
                    },
                    {
                        "titulo": "¿Qué tan claro fue el tema de hoy?",
                        "question_type": "live_scale_1_5",
                        "is_required": True,
                    },
                    {
                        "titulo": "¿Qué actividad quieres reforzar?",
                        "question_type": "live_poll_single_choice",
                        "is_required": True,
                        "options": [
                            {"label": "Ejemplo guiado", "value": "ejemplo_guiado", "orden": 1},
                            {"label": "Práctica", "value": "practica", "orden": 2},
                            {"label": "Preguntas y respuestas", "value": "preguntas_respuestas", "orden": 3},
                        ],
                    },
                ],
            }
        ],
    },
    {
        "nombre": "Encuesta post evento",
        "slug": "encuesta-post-evento",
        "descripcion": "Recoge satisfacción, logística e impacto de un evento.",
        "categoria": "eventos",
        "survey_type": "post_event",
        "scoring_mode": "csat",
        "settings_json": {"scoring_mode": "csat"},
        "sections": [
            {
                "titulo": "Experiencia",
                "questions": [
                    {"titulo": "El evento cumplió tus expectativas", "question_type": "scale_1_5", "is_required": True},
                    {"titulo": "La logística fue adecuada", "question_type": "scale_1_5", "is_required": True},
                    {"titulo": "Comentario final", "question_type": "long_text"},
                ],
            }
        ],
    },
]


def ensure_survey_schema() -> None:
    global _SURVEY_SCHEMA_READY
    if _SURVEY_SCHEMA_READY:
        return
    engine = core_db.get_engine_for_host(core_db.get_request_host())
    MAIN.metadata.create_all(bind=engine, tables=_SURVEY_TABLES, checkfirst=True)
    _SURVEY_SCHEMA_READY = True


def get_db() -> Session:
    session_factory = core_db.get_session_factory_for_host(core_db.get_request_host())
    return session_factory()


ensure_survey_schema()


def _dt(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _is_360_payload(survey_type: str = "", external_entity_type: str = "") -> bool:
    survey_value = str(survey_type or "").strip().lower()
    entity_value = str(external_entity_type or "").strip().lower()
    return survey_value in {"360", "evaluation_360", "evaluacion_360"} or "360" in entity_value


def _notification_timestamp() -> str:
    return datetime.utcnow().isoformat()


def _background_runtime_status() -> Dict[str, Any]:
    broker_url = (
        os.environ.get("ENCUESTAS_CELERY_BROKER_URL")
        or os.environ.get("CELERY_BROKER_URL")
        or os.environ.get("REDIS_URL")
        or ""
    ).strip()
    result_backend = (
        os.environ.get("ENCUESTAS_CELERY_RESULT_BACKEND")
        or os.environ.get("CELERY_RESULT_BACKEND")
        or broker_url
    ).strip()
    queue_name = (os.environ.get("ENCUESTAS_CELERY_QUEUE") or "encuestas_automation").strip() or "encuestas_automation"
    configured = bool(broker_url)
    redis_ready = False
    redis_error = ""
    if configured and broker_url.startswith(("redis://", "rediss://")):
        try:
            redis_lib.from_url(broker_url, socket_connect_timeout=0.5, socket_timeout=0.5).ping()
            redis_ready = True
        except Exception as exc:
            redis_error = str(exc)
    return {
        "configured": configured,
        "broker_url": broker_url,
        "result_backend": result_backend,
        "queue_name": queue_name,
        "engine": "celery" if configured else "manual_scheduler",
        "celery_ready": configured,
        "redis_ready": redis_ready,
        "redis_error": redis_error,
    }


def _load_capacitacion_enrollments(curso_id: int) -> List[Dict[str, Any]]:
    try:
        from fastapi_modulo.modulos.capacitacion.modelos.cap_inscripcion_service import list_inscripciones

        return list_inscripciones(curso_id=curso_id)
    except Exception:
        return []


def _load_crm_campaign_contacts(campaign_id: int) -> List[Dict[str, Any]]:
    try:
        from fastapi_modulo.modulos.crm.modelos.crm_store import list_contactos, list_contactos_campania

        links = list_contactos_campania(campaign_id)
        contact_ids = {int(item["contacto_id"]) for item in links if item.get("contacto_id")}
        contacts = {int(item["id"]): item for item in list_contactos()}
        return [contacts[contact_id] for contact_id in sorted(contact_ids) if contact_id in contacts]
    except Exception:
        return []


def _resolve_integration_context(source_app: str = "", external_entity_type: str = "", external_entity_id: str = "") -> Dict[str, Any]:
    source_value = str(source_app or "").strip().lower()
    entity_type = str(external_entity_type or "").strip().lower()
    entity_id = str(external_entity_id or "").strip()
    if not source_value or not entity_type or not entity_id:
        return {}
    if source_value == "capacitacion" and entity_type in {"curso", "course"} and entity_id.isdigit():
        courses = {str(item["id"]): item for item in _load_capacitacion_courses()}
        course = courses.get(entity_id)
        return {"course": course} if course else {}
    if source_value == "crm":
        if entity_type in {"contacto", "contact", "crm_contact"} and entity_id.isdigit():
            contacts = {str(item["id"]): item for item in _load_crm_contacts()}
            contact = contacts.get(entity_id)
            return {"contact": contact} if contact else {}
        if entity_type in {"campania", "campaign", "crm_campaign"} and entity_id.isdigit():
            contacts = _load_crm_campaign_contacts(int(entity_id))
            return {
                "campaign_contacts": contacts,
                "campaign_contacts_count": len(contacts),
            }
    return {}


def _automation_settings(instance: SurveyInstance) -> Dict[str, Any]:
    settings = instance.settings_json or {}
    rules = instance.publication_rules_json or {}
    background = _background_runtime_status()
    return {
        "enabled": bool(rules.get("automation_enabled", True)),
        "reminder_interval_hours": int(rules.get("reminder_interval_hours") or settings.get("reminder_interval_hours") or 24),
        "closing_notice_hours": int(rules.get("closing_notice_hours") or settings.get("closing_notice_hours") or 24),
        "engine": background["engine"],
        "future": {
            "celery_ready": background["celery_ready"],
            "redis_ready": background["redis_ready"],
            "redis_error": background["redis_error"],
            "broker_configured": background["configured"],
            "queue_name": background["queue_name"],
        },
    }


def _assignment_dict(obj: SurveyAssignment) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "instance_id": obj.instance_id,
        "audience_group_id": obj.audience_group_id,
        "assignee_key": obj.assignee_key,
        "assignee_name_snapshot": obj.assignee_name_snapshot,
        "assignee_role_snapshot": obj.assignee_role_snapshot,
        "assignee_area_snapshot": obj.assignee_area_snapshot,
        "assignee_position_snapshot": obj.assignee_position_snapshot,
        "assignee_company_snapshot": obj.assignee_company_snapshot,
        "source_app": obj.source_app,
        "external_entity_type": obj.external_entity_type,
        "external_entity_id": obj.external_entity_id,
        "assignment_type": obj.assignment_type,
        "channel": obj.channel,
        "status": obj.status,
        "due_at": _dt(obj.due_at),
        "first_sent_at": _dt(obj.first_sent_at),
        "last_sent_at": _dt(obj.last_sent_at),
        "response_count": obj.response_count,
        "created_at": _dt(obj.created_at),
        "updated_at": _dt(obj.updated_at),
    }


def _dispatch_log_dict(obj: SurveyDispatchLog) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "instance_id": obj.instance_id,
        "assignment_id": obj.assignment_id,
        "dispatch_type": obj.dispatch_type,
        "dispatch_status": obj.dispatch_status,
        "channel": obj.channel,
        "recipient_key": obj.recipient_key,
        "recipient_name_snapshot": obj.recipient_name_snapshot,
        "message_text": obj.message_text,
        "metadata_json": obj.metadata_json or {},
        "dispatched_at": _dt(obj.dispatched_at),
        "created_at": _dt(obj.created_at),
    }


def _evaluation_360_dict(obj: SurveyEvaluation360) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "instance_id": obj.instance_id,
        "assignment_id": obj.assignment_id,
        "evaluatee_key": obj.evaluatee_key,
        "evaluator_key": obj.evaluator_key,
        "relationship_type": obj.relationship_type,
        "evaluatee_name_snapshot": obj.evaluatee_name_snapshot,
        "evaluatee_role_snapshot": obj.evaluatee_role_snapshot,
        "evaluatee_area_snapshot": obj.evaluatee_area_snapshot,
        "evaluatee_position_snapshot": obj.evaluatee_position_snapshot,
        "evaluatee_company_snapshot": obj.evaluatee_company_snapshot,
        "evaluator_name_snapshot": obj.evaluator_name_snapshot,
        "evaluator_role_snapshot": obj.evaluator_role_snapshot,
        "evaluator_area_snapshot": obj.evaluator_area_snapshot,
        "evaluator_position_snapshot": obj.evaluator_position_snapshot,
        "evaluator_company_snapshot": obj.evaluator_company_snapshot,
        "status": obj.status,
        "source_app": obj.source_app,
        "external_entity_type": obj.external_entity_type,
        "external_entity_id": obj.external_entity_id,
        "created_at": _dt(obj.created_at),
        "updated_at": _dt(obj.updated_at),
    }


def _response_item_dict(obj: SurveyResponseItem) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "question_id": obj.question_id,
        "option_id": obj.option_id,
        "item_index": obj.item_index,
        "answer_text": obj.answer_text,
        "answer_value": obj.answer_value,
        "answer_json": obj.answer_json or {},
        "score_value": obj.score_value,
        "is_correct": obj.is_correct,
    }


def _response_dict(obj: SurveyResponse) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "instance_id": obj.instance_id,
        "assignment_id": obj.assignment_id,
        "respondent_key": obj.respondent_key,
        "respondent_name_snapshot": obj.respondent_name_snapshot,
        "respondent_role_snapshot": obj.respondent_role_snapshot,
        "respondent_area_snapshot": obj.respondent_area_snapshot,
        "respondent_position_snapshot": obj.respondent_position_snapshot,
        "respondent_company_snapshot": obj.respondent_company_snapshot,
        "source_app": obj.source_app,
        "external_entity_type": obj.external_entity_type,
        "external_entity_id": obj.external_entity_id,
        "status": obj.status,
        "submission_channel": obj.submission_channel,
        "evaluation_360_id": int(obj.external_entity_id) if str(obj.external_entity_type or "") == "evaluation_360" and str(obj.external_entity_id or "").isdigit() else None,
        "started_at": _dt(obj.started_at),
        "submitted_at": _dt(obj.submitted_at),
        "last_saved_at": _dt(obj.last_saved_at),
        "completion_pct": obj.completion_pct,
        "total_score": obj.total_score,
        "metrics_json": obj.metrics_json or {},
        "answers_json": obj.answers_json or {},
        "created_at": _dt(obj.created_at),
        "updated_at": _dt(obj.updated_at),
        "items": [_response_item_dict(item) for item in (obj.items or [])],
    }


def _template_dict(obj: SurveyTemplate) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "nombre": obj.nombre,
        "slug": obj.slug,
        "descripcion": obj.descripcion,
        "categoria": obj.categoria,
        "survey_type": obj.survey_type,
        "status": obj.status,
        "version": obj.version,
        "source_app": obj.source_app,
        "external_entity_type": obj.external_entity_type,
        "external_entity_id": obj.external_entity_id,
        "scoring_mode": obj.scoring_mode,
        "settings_json": obj.settings_json or {},
        "validation_rules_json": obj.validation_rules_json or {},
        "created_by": obj.created_by,
        "created_at": _dt(obj.created_at),
        "updated_at": _dt(obj.updated_at),
        "published_at": _dt(obj.published_at),
        "sections_count": len(obj.sections or []),
    }


def _instance_dict(obj: SurveyInstance) -> Dict[str, Any]:
    integration_context = _resolve_integration_context(
        source_app=obj.source_app,
        external_entity_type=obj.external_entity_type,
        external_entity_id=obj.external_entity_id,
    )
    automation_settings = _automation_settings(obj)
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "template_id": obj.template_id,
        "template_nombre": obj.template.nombre if obj.template else None,
        "codigo": obj.codigo,
        "nombre": obj.nombre,
        "descripcion": obj.descripcion,
        "status": obj.status,
        "publication_mode": obj.publication_mode,
        "audience_mode": obj.audience_mode,
        "anonymity_mode": obj.anonymity_mode,
        "schedule_start_at": _dt(obj.schedule_start_at),
        "schedule_end_at": _dt(obj.schedule_end_at),
        "is_public_link_enabled": obj.is_public_link_enabled,
        "public_link_token": obj.public_link_token,
        "source_app": obj.source_app,
        "external_entity_type": obj.external_entity_type,
        "external_entity_id": obj.external_entity_id,
        "integration_context": integration_context,
        "automation_settings": automation_settings,
        "settings_json": obj.settings_json or {},
        "publication_rules_json": obj.publication_rules_json or {},
        "created_by": obj.created_by,
        "created_at": _dt(obj.created_at),
        "updated_at": _dt(obj.updated_at),
        "published_at": _dt(obj.published_at),
        "closed_at": _dt(obj.closed_at),
        "assignments_count": len(obj.assignments or []),
        "responses_count": len(obj.responses or []),
    }


def _option_dict(obj: SurveyOption) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "label": obj.label,
        "value": obj.value,
        "orden": obj.orden,
        "score_value": obj.score_value,
        "is_correct": obj.is_correct,
        "config_json": obj.config_json or {},
    }


def _question_dict(obj: SurveyQuestion) -> Dict[str, Any]:
    definition = get_question_type_definition(obj.question_type)
    return {
        "id": obj.id,
        "template_id": obj.template_id,
        "section_id": obj.section_id,
        "question_key": obj.question_key,
        "titulo": obj.titulo,
        "descripcion": obj.descripcion,
        "question_type": obj.question_type,
        "question_type_label": definition.get("label"),
        "input_kind": definition.get("input_kind"),
        "orden": obj.orden,
        "is_required": obj.is_required,
        "is_scored": obj.is_scored,
        "max_score": obj.max_score,
        "min_score": obj.min_score,
        "config_json": obj.config_json or {},
        "validation_json": obj.validation_json or {},
        "logic_json": obj.logic_json or {},
        "options": [_option_dict(option) for option in (obj.options or [])],
    }


def _section_dict(obj: SurveySection) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "template_id": obj.template_id,
        "instance_id": obj.instance_id,
        "titulo": obj.titulo,
        "descripcion": obj.descripcion,
        "orden": obj.orden,
        "is_required": obj.is_required,
        "settings_json": obj.settings_json or {},
        "questions": [_question_dict(question) for question in (obj.questions or [])],
    }


def list_templates(tenant_id: str, status: str = "") -> List[Dict[str, Any]]:
    db = get_db()
    try:
        query = (
            db.query(SurveyTemplate)
            .filter(SurveyTemplate.tenant_id == tenant_id)
            .order_by(SurveyTemplate.updated_at.desc(), SurveyTemplate.id.desc())
        )
        if status:
            query = query.filter(SurveyTemplate.status == status)
        return [_template_dict(row) for row in query.all()]
    finally:
        db.close()


def create_template(data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = SurveyTemplate(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return _template_dict(obj)
    except IntegrityError:
        db.rollback()
        raise
    finally:
        db.close()


def _create_template_with_structure(db: Session, data: Dict[str, Any]) -> SurveyTemplate:
    payload = dict(data or {})
    sections = payload.pop("sections", [])
    template = SurveyTemplate(**payload)
    db.add(template)
    db.flush()
    for section_index, section_data in enumerate(sections, start=1):
        section = SurveySection(
            tenant_id=template.tenant_id,
            template_id=template.id,
            instance_id=None,
            titulo=str(section_data.get("titulo") or f"Sección {section_index}"),
            descripcion=section_data.get("descripcion"),
            orden=section_index,
            is_required=bool(section_data.get("is_required", False)),
            settings_json=section_data.get("settings_json") or {},
        )
        db.add(section)
        db.flush()
        for question_index, question_data in enumerate(section_data.get("questions") or [], start=1):
            normalized = normalize_question_payload(question_data)
            question = SurveyQuestion(
                tenant_id=template.tenant_id,
                template_id=template.id,
                section_id=section.id,
                question_key=normalized.get("question_key"),
                titulo=str(normalized.get("titulo") or f"Pregunta {question_index}"),
                descripcion=normalized.get("descripcion"),
                question_type=str(normalized.get("question_type") or "short_text"),
                orden=question_index,
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
            _upsert_question_options(db, question, template.tenant_id, normalized.get("options") or [])
    return template


def ensure_default_templates(tenant_id: str, created_by: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        existing = {
            row.slug: row
            for row in db.query(SurveyTemplate).filter(SurveyTemplate.tenant_id == tenant_id).all()
        }
        for item in DEFAULT_SURVEY_TEMPLATES:
            slug = str(item["slug"])
            if slug in existing:
                continue
            template = _create_template_with_structure(
                db,
                {
                    "tenant_id": tenant_id,
                    "nombre": item["nombre"],
                    "slug": slug,
                    "descripcion": item.get("descripcion"),
                    "categoria": item.get("categoria"),
                    "survey_type": item.get("survey_type") or "general",
                    "status": "published",
                    "version": 1,
                    "source_app": "encuestas",
                    "external_entity_type": item.get("external_entity_type"),
                    "external_entity_id": slug,
                    "scoring_mode": item.get("scoring_mode") or "none",
                    "settings_json": item.get("settings_json") or {},
                    "validation_rules_json": {},
                    "created_by": created_by,
                    "published_at": datetime.utcnow(),
                    "sections": item.get("sections") or [],
                },
            )
            template.status = "published"
            template.published_at = datetime.utcnow()
        db.commit()
        rows = (
            db.query(SurveyTemplate)
            .filter(SurveyTemplate.tenant_id == tenant_id)
            .order_by(SurveyTemplate.updated_at.desc(), SurveyTemplate.id.desc())
            .all()
        )
        return [_template_dict(row) for row in rows]
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def list_instances(tenant_id: str, status: str = "") -> List[Dict[str, Any]]:
    db = get_db()
    try:
        _refresh_instance_lifecycle(db, tenant_id=tenant_id)
        query = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.tenant_id == tenant_id)
            .order_by(SurveyInstance.updated_at.desc(), SurveyInstance.id.desc())
        )
        if status:
            query = query.filter(SurveyInstance.status == status)
        return [_instance_dict(row) for row in query.all()]
    finally:
        db.close()


def create_instance(data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        template_id = data.get("template_id")
        if not template_id:
            template = SurveyTemplate(
                tenant_id=str(data.get("tenant_id") or "default"),
                nombre=str(data.get("nombre") or "Nueva encuesta"),
                slug=str(data.get("codigo") or data.get("nombre") or "encuesta").lower(),
                descripcion=data.get("descripcion"),
                categoria=data.get("categoria"),
                survey_type=str(data.get("survey_type") or "general"),
                status="draft",
                source_app=data.get("source_app"),
                external_entity_type=data.get("external_entity_type"),
                external_entity_id=data.get("external_entity_id"),
                scoring_mode=str((data.get("settings_json") or {}).get("scoring_mode") or "none"),
                settings_json=data.get("settings_json") or {},
                validation_rules_json={},
                created_by=data.get("created_by"),
            )
            db.add(template)
            db.flush()
            template_id = template.id
        obj = SurveyInstance(**{**data, "template_id": template_id})
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return _instance_dict(obj)
    except IntegrityError:
        db.rollback()
        raise
    finally:
        db.close()


def create_instance_from_template(
    tenant_id: str,
    template_id: int,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    db = get_db()
    try:
        template = (
            db.query(SurveyTemplate)
            .filter(SurveyTemplate.id == template_id, SurveyTemplate.tenant_id == tenant_id)
            .first()
        )
        if not template:
            raise ValueError("Plantilla no encontrada.")
        payload = dict(data or {})
        payload["tenant_id"] = tenant_id
        payload["template_id"] = template.id
        payload.setdefault("nombre", template.nombre)
        payload.setdefault("descripcion", template.descripcion)
        payload.setdefault("source_app", template.source_app)
        payload.setdefault("external_entity_type", template.external_entity_type)
        payload.setdefault("external_entity_id", template.external_entity_id)
        payload.setdefault("settings_json", template.settings_json or {})
        payload.setdefault("publication_rules_json", {})
        payload.setdefault(
            "anonymity_mode",
            "restricted" if str(template.survey_type or "").strip().lower() in {"360", "evaluation_360", "evaluacion_360"} else "identified",
        )
        instance = SurveyInstance(**payload)
        db.add(instance)
        db.flush()
        for section in template.sections or []:
            new_section = SurveySection(
                tenant_id=tenant_id,
                template_id=template.id,
                instance_id=instance.id,
                titulo=section.titulo,
                descripcion=section.descripcion,
                orden=section.orden,
                is_required=section.is_required,
                settings_json=section.settings_json or {},
            )
            db.add(new_section)
            db.flush()
            for question in section.questions or []:
                cloned = SurveyQuestion(
                    tenant_id=tenant_id,
                    template_id=template.id,
                    section_id=new_section.id,
                    question_key=question.question_key,
                    titulo=question.titulo,
                    descripcion=question.descripcion,
                    question_type=question.question_type,
                    orden=question.orden,
                    is_required=question.is_required,
                    is_scored=question.is_scored,
                    max_score=question.max_score,
                    min_score=question.min_score,
                    config_json=question.config_json or {},
                    validation_json=question.validation_json or {},
                    logic_json=question.logic_json or {},
                )
                db.add(cloned)
                db.flush()
                _upsert_question_options(
                    db,
                    cloned,
                    tenant_id,
                    [
                        {
                            "label": option.label,
                            "value": option.value,
                            "orden": option.orden,
                            "score_value": option.score_value,
                            "is_correct": option.is_correct,
                            "config_json": option.config_json or {},
                        }
                        for option in (question.options or [])
                    ],
                )
        db.commit()
        db.refresh(instance)
        return _instance_dict(instance)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def save_instance_as_template(instance_id: int, tenant_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        instance = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not instance:
            raise ValueError("Encuesta no encontrada.")
        slug = str(data.get("slug") or "").strip()
        if not slug:
            raise ValueError("La plantilla requiere slug.")
        existing = (
            db.query(SurveyTemplate)
            .filter(SurveyTemplate.tenant_id == tenant_id, SurveyTemplate.slug == slug)
            .first()
        )
        if existing:
            raise ValueError("Ya existe una plantilla con ese slug.")
        template = SurveyTemplate(
            tenant_id=tenant_id,
            nombre=str(data.get("nombre") or instance.nombre),
            slug=slug,
            descripcion=data.get("descripcion") or instance.descripcion,
            categoria=data.get("categoria"),
            survey_type=str(data.get("survey_type") or (instance.template.survey_type if instance.template else "general")),
            status="published",
            version=1,
            source_app=instance.source_app or "encuestas",
            external_entity_type=data.get("external_entity_type"),
            external_entity_id=data.get("external_entity_id") or f"saved_template:{instance.id}",
            scoring_mode=str((instance.settings_json or {}).get("scoring_mode") or "none"),
            settings_json=instance.settings_json or {},
            validation_rules_json=instance.publication_rules_json or {},
            created_by=data.get("created_by"),
            published_at=datetime.utcnow(),
        )
        db.add(template)
        db.flush()
        for section in instance.sections or []:
            new_section = SurveySection(
                tenant_id=tenant_id,
                template_id=template.id,
                instance_id=None,
                titulo=section.titulo,
                descripcion=section.descripcion,
                orden=section.orden,
                is_required=section.is_required,
                settings_json=section.settings_json or {},
            )
            db.add(new_section)
            db.flush()
            for question in section.questions or []:
                cloned = SurveyQuestion(
                    tenant_id=tenant_id,
                    template_id=template.id,
                    section_id=new_section.id,
                    question_key=question.question_key,
                    titulo=question.titulo,
                    descripcion=question.descripcion,
                    question_type=question.question_type,
                    orden=question.orden,
                    is_required=question.is_required,
                    is_scored=question.is_scored,
                    max_score=question.max_score,
                    min_score=question.min_score,
                    config_json=question.config_json or {},
                    validation_json=question.validation_json or {},
                    logic_json=question.logic_json or {},
                )
                db.add(cloned)
                db.flush()
                _upsert_question_options(
                    db,
                    cloned,
                    tenant_id,
                    [
                        {
                            "label": option.label,
                            "value": option.value,
                            "orden": option.orden,
                            "score_value": option.score_value,
                            "is_correct": option.is_correct,
                            "config_json": option.config_json or {},
                        }
                        for option in (question.options or [])
                    ],
                )
        db.commit()
        db.refresh(template)
        return _template_dict(template)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def get_instance(instance_id: int, tenant_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        _refresh_instance_lifecycle(db, instance_id=instance_id, tenant_id=tenant_id)
        obj = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        return _instance_dict(obj) if obj else None
    finally:
        db.close()


def get_instance_builder(instance_id: int, tenant_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        _refresh_instance_lifecycle(db, instance_id=instance_id, tenant_id=tenant_id)
        obj = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not obj:
            return None
        payload = _instance_dict(obj)
        payload["sections"] = [_section_dict(section) for section in (obj.sections or [])]
        payload["publish_validation"] = validate_instance_for_publish_db(obj)
        payload["assignments"] = [_assignment_dict(assignment) for assignment in (obj.assignments or [])]
        return payload
    finally:
        db.close()


def update_instance_draft(instance_id: int, tenant_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not obj:
            return None
        if obj.status not in {"draft", "archived"}:
            raise ValueError("Solo se puede editar una encuesta en borrador o archivada.")
        if not obj.template_id:
            template = SurveyTemplate(
                tenant_id=tenant_id,
                nombre=str(data.get("nombre") or obj.nombre or "Nueva encuesta"),
                slug=str(obj.codigo or obj.nombre or f"encuesta_{obj.id}").lower(),
                descripcion=data.get("descripcion") if "descripcion" in data else obj.descripcion,
                survey_type="general",
                status="draft",
                source_app=data.get("source_app") if "source_app" in data else obj.source_app,
                external_entity_type=data.get("external_entity_type") if "external_entity_type" in data else obj.external_entity_type,
                external_entity_id=data.get("external_entity_id") if "external_entity_id" in data else obj.external_entity_id,
                scoring_mode=str((data.get("settings_json") or obj.settings_json or {}).get("scoring_mode") or "none"),
                settings_json=data.get("settings_json") if "settings_json" in data else (obj.settings_json or {}),
                validation_rules_json={},
                created_by=obj.created_by,
            )
            db.add(template)
            db.flush()
            obj.template_id = template.id
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        if obj.template:
            template = obj.template
            template.nombre = obj.nombre
            template.descripcion = obj.descripcion
            template.source_app = obj.source_app
            template.external_entity_type = obj.external_entity_type
            template.external_entity_id = obj.external_entity_id
            template.scoring_mode = str((obj.settings_json or {}).get("scoring_mode") or template.scoring_mode or "none")
            template.settings_json = obj.settings_json or {}
            template.updated_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(obj)
        return _instance_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def publish_instance(instance_id: int, tenant_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not obj:
            return None
        if obj.status == "closed":
            raise ValueError("No se puede publicar una encuesta cerrada.")
        now = datetime.utcnow()
        if obj.schedule_start_at and obj.schedule_start_at > now:
            obj.status = "scheduled"
        else:
            obj.status = "published"
            obj.published_at = now
        if obj.template:
            obj.template.status = obj.status
            obj.template.published_at = obj.published_at
            obj.template.updated_at = now
        if obj.status in {"published", "scheduled"} and obj.assignments:
            has_sent_notifications = any(assignment.first_sent_at for assignment in (obj.assignments or []))
            _send_assignment_notifications(
                db,
                obj,
                list(obj.assignments or []),
                notification_kind="reminder" if has_sent_notifications else "invitation",
            )
        obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(obj)
        return _instance_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def close_instance(instance_id: int, tenant_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not obj:
            return None
        obj.status = "closed"
        obj.closed_at = datetime.utcnow()
        if obj.template:
            obj.template.status = "closed"
            obj.template.updated_at = datetime.utcnow()
        obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(obj)
        return _instance_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def archive_or_delete_instance(instance_id: int, tenant_id: str, hard_delete: bool = False) -> bool:
    db = get_db()
    try:
        obj = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not obj:
            return False
        if hard_delete:
            if obj.template and len(obj.template.instances or []) <= 1:
                db.delete(obj.template)
            db.delete(obj)
        else:
            obj.status = "archived"
            if obj.template:
                obj.template.status = "archived"
                obj.template.updated_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def _next_section_order(db: Session, template_id: int) -> int:
    section = (
        db.query(SurveySection)
        .filter(SurveySection.template_id == template_id)
        .order_by(SurveySection.orden.desc(), SurveySection.id.desc())
        .first()
    )
    return int(section.orden or 0) + 1 if section else 1


def _next_question_order(db: Session, section_id: int) -> int:
    question = (
        db.query(SurveyQuestion)
        .filter(SurveyQuestion.section_id == section_id)
        .order_by(SurveyQuestion.orden.desc(), SurveyQuestion.id.desc())
        .first()
    )
    return int(question.orden or 0) + 1 if question else 1


def _upsert_question_options(
    db: Session,
    question: SurveyQuestion,
    tenant_id: str,
    options: List[Dict[str, Any]],
) -> None:
    db.query(SurveyOption).filter(SurveyOption.question_id == question.id).delete(synchronize_session=False)
    for index, option in enumerate(options, start=1):
        db.add(
            SurveyOption(
                tenant_id=tenant_id,
                question_id=question.id,
                label=str(option.get("label") or f"Opcion {index}"),
                value=str(option.get("value") or option.get("label") or f"option_{index}"),
                orden=int(option.get("orden") or index),
                score_value=option.get("score_value"),
                is_correct=bool(option.get("is_correct", False)),
                config_json=option.get("config_json") or {},
            )
        )


def create_section(instance_id: int, tenant_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        instance = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not instance:
            return None
        if instance.status not in {"draft", "archived"}:
            raise ValueError("Solo se pueden agregar secciones en encuestas editables.")
        section = SurveySection(
            tenant_id=tenant_id,
            template_id=instance.template_id,
            instance_id=instance.id,
            titulo=str(data.get("titulo") or "Nueva seccion"),
            descripcion=data.get("descripcion"),
            orden=int(data.get("orden") or _next_section_order(db, instance.template_id)),
            is_required=bool(data.get("is_required", False)),
            settings_json=data.get("settings_json") or {},
        )
        db.add(section)
        instance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(section)
        return _section_dict(section)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_section(instance_id: int, section_id: int, tenant_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        section = (
            db.query(SurveySection)
            .join(SurveyInstance, SurveySection.instance_id == SurveyInstance.id)
            .filter(
                SurveySection.id == section_id,
                SurveySection.instance_id == instance_id,
                SurveySection.tenant_id == tenant_id,
                SurveyInstance.tenant_id == tenant_id,
            )
            .first()
        )
        if not section:
            return None
        if section.instance and section.instance.status not in {"draft", "archived"}:
            raise ValueError("Solo se pueden editar secciones en encuestas editables.")
        for key, value in data.items():
            if value is not None:
                setattr(section, key, value)
        section.updated_at = datetime.utcnow()
        if section.instance:
            section.instance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(section)
        return _section_dict(section)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def reorder_sections(instance_id: int, tenant_id: str, section_ids: List[int]) -> bool:
    db = get_db()
    try:
        total = (
            db.query(SurveySection.id)
            .filter(
                SurveySection.instance_id == instance_id,
                SurveySection.tenant_id == tenant_id,
                SurveySection.id.in_(section_ids),
            )
            .count()
        )
        if total != len(section_ids):
            return False
        temp_offset = len(section_ids) + 1000
        for index, section_id in enumerate(section_ids, start=1):
            db.query(SurveySection).filter(SurveySection.id == section_id).update(
                {"orden": temp_offset + index, "updated_at": datetime.utcnow()},
                synchronize_session=False,
            )
        db.commit()
        for index, section_id in enumerate(section_ids, start=1):
            db.query(SurveySection).filter(SurveySection.id == section_id).update(
                {"orden": index, "updated_at": datetime.utcnow()},
                synchronize_session=False,
            )
        instance = db.query(SurveyInstance).filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id).first()
        if instance:
            instance.updated_at = datetime.utcnow()
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def create_question(instance_id: int, section_id: int, tenant_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        section = (
            db.query(SurveySection)
            .join(SurveyInstance, SurveySection.instance_id == SurveyInstance.id)
            .filter(
                SurveySection.id == section_id,
                SurveySection.instance_id == instance_id,
                SurveySection.tenant_id == tenant_id,
                SurveyInstance.tenant_id == tenant_id,
            )
            .first()
        )
        if not section:
            return None
        if section.instance and section.instance.status not in {"draft", "archived"}:
            raise ValueError("Solo se pueden agregar preguntas en encuestas editables.")
        payload = normalize_question_payload(data)
        question = SurveyQuestion(
            tenant_id=tenant_id,
            template_id=section.template_id,
            section_id=section.id,
            question_key=payload.get("question_key"),
            titulo=str(payload.get("titulo") or "Nueva pregunta"),
            descripcion=payload.get("descripcion"),
            question_type=str(payload.get("question_type") or "short_text"),
            orden=int(payload.get("orden") or _next_question_order(db, section.id)),
            is_required=bool(payload.get("is_required", False)),
            is_scored=bool(payload.get("is_scored", False)),
            max_score=payload.get("max_score"),
            min_score=payload.get("min_score"),
            config_json=payload.get("config_json") or {},
            validation_json=payload.get("validation_json") or {},
            logic_json=payload.get("logic_json") or {},
        )
        db.add(question)
        db.flush()
        _upsert_question_options(db, question, tenant_id, payload.get("options") or [])
        if section.instance:
            section.instance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(question)
        return _question_dict(question)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_question(instance_id: int, question_id: int, tenant_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        question = (
            db.query(SurveyQuestion)
            .join(SurveySection, SurveyQuestion.section_id == SurveySection.id)
            .join(SurveyInstance, SurveySection.instance_id == SurveyInstance.id)
            .filter(
                SurveyQuestion.id == question_id,
                SurveySection.instance_id == instance_id,
                SurveyQuestion.tenant_id == tenant_id,
                SurveyInstance.tenant_id == tenant_id,
            )
            .first()
        )
        if not question:
            return None
        if question.section and question.section.instance and question.section.instance.status not in {"draft", "archived"}:
            raise ValueError("Solo se pueden editar preguntas en encuestas editables.")
        merged_payload = {
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
            "options": [
                {
                    "label": option.label,
                    "value": option.value,
                    "orden": option.orden,
                    "score_value": option.score_value,
                    "is_correct": option.is_correct,
                    "config_json": option.config_json or {},
                }
                for option in (question.options or [])
            ],
        }
        merged_payload.update(data)
        payload = normalize_question_payload(merged_payload)
        options = payload.pop("options", None)
        for key, value in payload.items():
            if value is not None:
                setattr(question, key, value)
        question.updated_at = datetime.utcnow()
        if options is not None:
            _upsert_question_options(db, question, tenant_id, options)
        if question.section and question.section.instance:
            question.section.instance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(question)
        return _question_dict(question)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def duplicate_question(instance_id: int, question_id: int, tenant_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        question = (
            db.query(SurveyQuestion)
            .join(SurveySection, SurveyQuestion.section_id == SurveySection.id)
            .join(SurveyInstance, SurveySection.instance_id == SurveyInstance.id)
            .filter(
                SurveyQuestion.id == question_id,
                SurveySection.instance_id == instance_id,
                SurveyQuestion.tenant_id == tenant_id,
                SurveyInstance.tenant_id == tenant_id,
            )
            .first()
        )
        if not question:
            return None
        cloned = SurveyQuestion(
            tenant_id=tenant_id,
            template_id=question.template_id,
            section_id=question.section_id,
            question_key=(f"{question.question_key}_copy" if question.question_key else None),
            titulo=f"{question.titulo} (copia)",
            descripcion=question.descripcion,
            question_type=question.question_type,
            orden=_next_question_order(db, question.section_id),
            is_required=question.is_required,
            is_scored=question.is_scored,
            max_score=question.max_score,
            min_score=question.min_score,
            config_json=question.config_json or {},
            validation_json=question.validation_json or {},
            logic_json=question.logic_json or {},
        )
        db.add(cloned)
        db.flush()
        _upsert_question_options(
            db,
            cloned,
            tenant_id,
            [
                {
                    "label": option.label,
                    "value": option.value,
                    "orden": option.orden,
                    "score_value": option.score_value,
                    "is_correct": option.is_correct,
                    "config_json": option.config_json or {},
                }
                for option in (question.options or [])
            ],
        )
        if question.section and question.section.instance:
            question.section.instance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cloned)
        return _question_dict(cloned)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def reorder_questions(instance_id: int, section_id: int, tenant_id: str, question_ids: List[int]) -> bool:
    db = get_db()
    try:
        total = (
            db.query(SurveyQuestion.id)
            .join(SurveySection, SurveyQuestion.section_id == SurveySection.id)
            .filter(
                SurveySection.instance_id == instance_id,
                SurveySection.id == section_id,
                SurveyQuestion.tenant_id == tenant_id,
                SurveyQuestion.id.in_(question_ids),
            )
            .count()
        )
        if total != len(question_ids):
            return False
        temp_offset = len(question_ids) + 1000
        for index, question_id in enumerate(question_ids, start=1):
            db.query(SurveyQuestion).filter(SurveyQuestion.id == question_id).update(
                {"orden": temp_offset + index, "updated_at": datetime.utcnow()},
                synchronize_session=False,
            )
        db.commit()
        for index, question_id in enumerate(question_ids, start=1):
            db.query(SurveyQuestion).filter(SurveyQuestion.id == question_id).update(
                {"orden": index, "updated_at": datetime.utcnow()},
                synchronize_session=False,
            )
        instance = db.query(SurveyInstance).filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id).first()
        if instance:
            instance.updated_at = datetime.utcnow()
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def validate_instance_for_publish(instance_id: int, tenant_id: str) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not obj:
            return {"ok": False, "errors": ["Encuesta no encontrada."]}
        return validate_instance_for_publish_db(obj)
    finally:
        db.close()


def validate_instance_for_publish_db(obj: SurveyInstance) -> Dict[str, Any]:
    errors: List[str] = []
    sections = obj.sections or []
    if not str(obj.nombre or "").strip():
        errors.append("La encuesta requiere nombre.")
    if not sections:
        errors.append("La encuesta debe tener al menos una sección.")
    if sections and not any((section.questions or []) for section in sections):
        errors.append("La encuesta debe tener al menos una pregunta.")
    if obj.audience_mode != "public_link" and len(obj.assignments or []) == 0:
        errors.append("La encuesta requiere al menos una asignación materializada o enlace público.")
    for section in sections:
        if not str(section.titulo or "").strip():
            errors.append("Todas las secciones deben tener título.")
        for question in section.questions or []:
            if not str(question.titulo or "").strip():
                errors.append("Todas las preguntas deben tener enunciado.")
            definition = get_question_type_definition(question.question_type)
            if definition.get("requires_options") and len(question.options or []) == 0:
                errors.append(f"La pregunta '{question.titulo}' requiere opciones.")
            if question.question_type == "quiz_single_choice":
                correct_count = sum(1 for option in (question.options or []) if option.is_correct)
                if correct_count != 1:
                    errors.append(f"La pregunta '{question.titulo}' requiere exactamente una opción correcta.")
    return {"ok": len(errors) == 0, "errors": errors}


def _refresh_instance_lifecycle(
    db: Session,
    instance_id: Optional[int] = None,
    tenant_id: Optional[str] = None,
) -> None:
    now = datetime.utcnow()
    query = db.query(SurveyInstance)
    if tenant_id:
        query = query.filter(SurveyInstance.tenant_id == tenant_id)
    if instance_id is not None:
        query = query.filter(SurveyInstance.id == instance_id)
    changed = False
    for obj in query.all():
        next_status = obj.status
        published_at = obj.published_at
        closed_at = obj.closed_at
        if obj.status in {"draft", "scheduled"} and obj.schedule_start_at and obj.schedule_start_at > now:
            next_status = "scheduled"
        elif obj.status == "scheduled" and obj.schedule_start_at and obj.schedule_start_at <= now:
            next_status = "published"
            published_at = published_at or now
        if obj.status in {"published", "scheduled"} and obj.schedule_end_at and obj.schedule_end_at <= now:
            if obj.status != "closed":
                _record_dispatch_log(
                    db,
                    obj,
                    dispatch_type="auto_close",
                    dispatch_status="applied",
                    message_text=f"Cierre automático ejecutado para la encuesta '{obj.nombre}'.",
                    metadata_json={"schedule_end_at": _dt(obj.schedule_end_at)},
                )
            next_status = "closed"
            closed_at = closed_at or now
        if next_status != obj.status or published_at != obj.published_at or closed_at != obj.closed_at:
            obj.status = next_status
            obj.published_at = published_at
            obj.closed_at = closed_at
            obj.updated_at = now
            changed = True
    if changed:
        db.commit()


def _load_user_directory() -> List[Dict[str, Any]]:
    db = get_db()
    try:
        rows = db.execute(
            text(
                """
                SELECT
                    id,
                    full_name AS nombre,
                    username AS usuario,
                    role,
                    departamento,
                    puesto,
                    jefe_inmediato_id,
                    jefe
                FROM users
                WHERE is_active = 1
                ORDER BY full_name ASC, username ASC, id ASC
                """
            )
        ).mappings().all()
        names_by_id = {int(row["id"]): (str(row["nombre"] or row["usuario"] or "")).strip() for row in rows}
        payload = []
        for user in rows:
            payload.append(
                {
                    "user_id": int(user["id"]),
                    "user_key": str(user["id"]),
                    "nombre": (str(user["nombre"] or user["usuario"] or "")).strip(),
                    "usuario": (str(user["usuario"] or "")).strip(),
                    "role": (str(user["role"] or "")).strip(),
                    "departamento": (str(user["departamento"] or "")).strip(),
                    "puesto": (str(user["puesto"] or "")).strip(),
                    "jefe_inmediato_id": user["jefe_inmediato_id"],
                    "jefe": names_by_id.get(user["jefe_inmediato_id"], "") or (str(user["jefe"] or "")).strip(),
                    "empresa": "default",
                }
            )
        return payload
    finally:
        db.close()


def _load_capacitacion_courses() -> List[Dict[str, Any]]:
    try:
        from fastapi_modulo.modulos.capacitacion.cap_store import list_cursos

        rows = list_cursos()
        return [
            {
                "course_id": item.get("id"),
                "nombre": item.get("nombre"),
                "categoria": item.get("categoria_nombre") or item.get("categoria"),
                "nivel": item.get("nivel"),
                "estado": item.get("estado"),
            }
            for item in (rows or [])
        ]
    except Exception:
        return []


def _load_crm_contacts() -> List[Dict[str, Any]]:
    try:
        from fastapi_modulo.modulos.crm.modelos.crm_store import list_contactos

        rows = list_contactos()
        return [
            {
                "contact_id": item.get("id"),
                "nombre": item.get("nombre"),
                "email": item.get("email"),
                "telefono": item.get("telefono"),
                "empresa": item.get("empresa") or "",
                "puesto": item.get("puesto") or "",
                "tipo": item.get("tipo") or "prospecto",
            }
            for item in (rows or [])
        ]
    except Exception:
        return []


def list_integration_sources() -> Dict[str, Any]:
    users = _load_user_directory()
    departments = sorted({item["departamento"] for item in users if item.get("departamento")})
    positions = sorted({item["puesto"] for item in users if item.get("puesto")})
    roles = sorted({item["role"] for item in users if item.get("role")})
    managers = [item for item in users if item.get("jefe_inmediato_id")]
    return {
        "empleados": {
            "users": users,
            "departments": departments,
            "positions": positions,
            "roles": roles,
            "hierarchy_ready": bool(managers),
        },
        "capacitacion": {
            "courses": _load_capacitacion_courses(),
        },
        "crm": {
            "contacts": _load_crm_contacts(),
        },
    }


def _group_members_payload(members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    seen = set()
    for member in members:
        key = str(member.get("user_id") or member.get("user_key") or member.get("value") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "user_id": key,
                "nombre": str(member.get("nombre") or member.get("label") or key).strip(),
                "role": str(member.get("role") or "").strip(),
                "departamento": str(member.get("departamento") or "").strip(),
                "puesto": str(member.get("puesto") or "").strip(),
                "empresa": str(member.get("empresa") or "default").strip(),
            }
        )
    return normalized


def list_assignable_users() -> List[Dict[str, Any]]:
    return _load_user_directory()


def list_assignments(instance_id: int, tenant_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        rows = (
            db.query(SurveyAssignment)
            .filter(SurveyAssignment.instance_id == instance_id, SurveyAssignment.tenant_id == tenant_id)
            .order_by(SurveyAssignment.assignment_type.asc(), SurveyAssignment.assignee_name_snapshot.asc())
            .all()
        )
        return [_assignment_dict(row) for row in rows]
    finally:
        db.close()


def list_results(instance_id: int, tenant_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        rows = (
            db.query(SurveyResult)
            .filter(SurveyResult.instance_id == instance_id, SurveyResult.tenant_id == tenant_id)
            .order_by(SurveyResult.segment_type.asc(), SurveyResult.segment_key.asc(), SurveyResult.metric_key.asc())
            .all()
        )
        return [
            {
                "id": row.id,
                "instance_id": row.instance_id,
                "segment_type": row.segment_type,
                "segment_key": row.segment_key,
                "metric_key": row.metric_key,
                "metric_label": row.metric_label,
                "value_numeric": row.value_numeric,
                "value_text": row.value_text,
                "sample_size": row.sample_size,
                "result_json": row.result_json or {},
                "computed_at": _dt(row.computed_at),
            }
            for row in rows
        ]
    finally:
        db.close()


def list_dispatch_logs(instance_id: int, tenant_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        rows = (
            db.query(SurveyDispatchLog)
            .filter(SurveyDispatchLog.instance_id == instance_id, SurveyDispatchLog.tenant_id == tenant_id)
            .order_by(SurveyDispatchLog.dispatched_at.desc(), SurveyDispatchLog.id.desc())
            .all()
        )
        return [_dispatch_log_dict(row) for row in rows]
    finally:
        db.close()


def list_live_course_surveys(curso_id: int, tenant_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        rows = (
            db.query(SurveyInstance)
            .filter(
                SurveyInstance.tenant_id == tenant_id,
                SurveyInstance.source_app == "capacitacion",
                SurveyInstance.external_entity_type.in_(["curso", "course"]),
                SurveyInstance.external_entity_id == str(curso_id),
                SurveyInstance.status.in_(["published", "scheduled"]),
            )
            .order_by(SurveyInstance.updated_at.desc(), SurveyInstance.id.desc())
            .all()
        )
        payload = []
        for row in rows:
            instance_payload = _instance_dict(row)
            settings = instance_payload.get("settings_json") or {}
            payload.append(
                {
                    **instance_payload,
                    "is_live": bool(
                        settings.get("presentation_mode") == "mentimeter"
                        or settings.get("live_session_enabled")
                        or str(row.survey_type if row.template else "").strip().lower() in {"live", "live_poll", "mentimeter"}
                    ),
                }
            )
        return payload
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Re-exports for backward compatibility (lazy to avoid circular imports)
# ---------------------------------------------------------------------------
# These allow existing code that imports from encuestas_store to keep working
# without changes. New code should import from the specialized modules directly.

def __getattr__(name: str):  # noqa: N807
    _automation_exports = {
        "dispatch_backendhook_event",
        "queue_automation_job",
        "queue_backendhook_event",
        "run_automation_jobs",
        "sync_assignments",
    }
    _responses_exports = {
        "get_response_session",
        "save_response_draft",
        "start_internal_response",
        "start_public_response",
        "submit_response",
    }
    _analytics_exports = {"get_results_dashboard"}
    _exports_exports = {"export_results_csv", "export_results_excel", "export_results_pdf"}

    if name in _automation_exports:
        from fastapi_modulo.modulos.encuestas.modelos import encuestas_automation as _mod
        return getattr(_mod, name)
    if name in _responses_exports:
        from fastapi_modulo.modulos.encuestas.modelos import encuestas_responses as _mod
        return getattr(_mod, name)
    if name in _analytics_exports:
        from fastapi_modulo.modulos.encuestas.modelos import encuestas_analytics as _mod
        return getattr(_mod, name)
    if name in _exports_exports:
        from fastapi_modulo.modulos.encuestas.modelos import encuestas_exports as _mod
        return getattr(_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
