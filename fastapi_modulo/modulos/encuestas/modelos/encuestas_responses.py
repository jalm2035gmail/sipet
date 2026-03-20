from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session, object_session

from fastapi_modulo.modulos.encuestas.modelos.encuestas_models import (
    SurveyAssignment,
    SurveyAttempt,
    SurveyEvaluation360,
    SurveyInstance,
    SurveyOption,
    SurveyQuestion,
    SurveyResponse,
    SurveyResponseItem,
    SurveyResult,
)
from fastapi_modulo.modulos.encuestas.modelos.encuestas_question_catalog import (
    QUESTION_TYPE_CATALOG,
    get_question_type_definition,
)
from fastapi_modulo.modulos.encuestas.modelos.encuestas_store import (
    _assignment_dict,
    _dt,
    _evaluation_360_dict,
    _is_360_payload,
    _resolve_integration_context,
    _response_dict,
    _response_item_dict,
    _section_dict,
    get_db,
)


def _ensure_instance_available_for_response(instance: SurveyInstance, access_mode: str) -> None:
    now = datetime.utcnow()
    if instance.status in {"draft", "archived"}:
        raise ValueError("La encuesta aún no está publicada.")
    if instance.status == "scheduled" and instance.schedule_start_at and instance.schedule_start_at > now:
        raise ValueError("La encuesta aún no está disponible.")
    if instance.status == "closed":
        raise ValueError("La encuesta ya fue cerrada.")
    if access_mode == "public" and _is_360_instance(instance):
        raise ValueError("Las evaluaciones 360 requieren acceso autenticado interno.")
    if access_mode == "public" and (not instance.is_public_link_enabled or not instance.public_link_token):
        raise ValueError("El enlace público no está habilitado para esta encuesta.")


def _find_existing_response(
    db: Session,
    instance_id: int,
    tenant_id: str,
    assignment_id: Optional[int] = None,
    respondent_key: str = "",
    external_entity_type: str = "",
    external_entity_id: str = "",
) -> Optional[SurveyResponse]:
    query = (
        db.query(SurveyResponse)
        .filter(SurveyResponse.instance_id == instance_id, SurveyResponse.tenant_id == tenant_id)
        .order_by(SurveyResponse.updated_at.desc(), SurveyResponse.id.desc())
    )
    entity_type = str(external_entity_type or "").strip()
    entity_id = str(external_entity_id or "").strip()
    if entity_type and entity_id:
        query = query.filter(
            SurveyResponse.external_entity_type == entity_type,
            SurveyResponse.external_entity_id == entity_id,
        )
    if assignment_id is not None:
        response = query.filter(SurveyResponse.assignment_id == assignment_id).first()
        if response:
            return response
    if respondent_key:
        return query.filter(SurveyResponse.respondent_key == respondent_key).first()
    return None


def _find_or_create_attempt(
    db: Session,
    tenant_id: str,
    instance_id: int,
    assignment_id: Optional[int],
    response_id: int,
    attempt_number: Optional[int] = None,
) -> Optional[SurveyAttempt]:
    if not assignment_id:
        return None
    query = (
        db.query(SurveyAttempt)
        .filter(
            SurveyAttempt.tenant_id == tenant_id,
            SurveyAttempt.instance_id == instance_id,
            SurveyAttempt.assignment_id == assignment_id,
        )
        .order_by(SurveyAttempt.attempt_number.desc(), SurveyAttempt.id.desc())
    )
    attempt = query.first()
    if attempt_number is not None:
        attempt = query.filter(SurveyAttempt.attempt_number == attempt_number).first()
    if attempt:
        if attempt.response_id is None:
            attempt.response_id = response_id
        if attempt.started_at is None:
            attempt.started_at = datetime.utcnow()
        return attempt
    attempt = SurveyAttempt(
        tenant_id=tenant_id,
        instance_id=instance_id,
        assignment_id=assignment_id,
        response_id=response_id,
        attempt_number=attempt_number or 1,
        status="in_progress",
        started_at=datetime.utcnow(),
    )
    db.add(attempt)
    return attempt


def _quiz_settings(instance: SurveyInstance) -> Dict[str, Any]:
    instance_settings = instance.settings_json or {}
    template_settings = instance.template.settings_json if instance.template and instance.template.settings_json else {}
    scoring_mode = str(
        instance_settings.get("scoring_mode")
        or template_settings.get("scoring_mode")
        or (instance.template.scoring_mode if instance.template else "")
        or "none"
    ).strip().lower()
    is_quiz = scoring_mode == "quiz" or "quiz" in str(instance.external_entity_type or "").strip().lower()
    max_attempts = int(instance_settings.get("max_attempts") or template_settings.get("max_attempts") or 1)
    timer_seconds = int(instance_settings.get("timer_seconds") or template_settings.get("timer_seconds") or 0)
    attempt_strategy = str(instance_settings.get("attempt_strategy") or template_settings.get("attempt_strategy") or "best").strip().lower()
    passing_score = instance_settings.get("passing_score")
    if passing_score is None:
        passing_score = template_settings.get("passing_score")
    if passing_score is None:
        integration = _resolve_integration_context(
            source_app=instance.source_app,
            external_entity_type=instance.external_entity_type,
            external_entity_id=instance.external_entity_id,
        )
        course = integration.get("course") or {}
        if course.get("puntaje_aprobacion") is not None:
            passing_score = float(course["puntaje_aprobacion"])
    return {
        "is_quiz": is_quiz,
        "max_attempts": max(1, max_attempts),
        "timer_seconds": max(0, timer_seconds),
        "attempt_strategy": attempt_strategy if attempt_strategy in {"best", "last"} else "best",
        "passing_score": float(passing_score) if passing_score is not None else None,
    }


def _assignment_attempts(db: Session, tenant_id: str, instance_id: int, assignment_id: Optional[int]) -> List[SurveyAttempt]:
    if not assignment_id:
        return []
    return (
        db.query(SurveyAttempt)
        .filter(
            SurveyAttempt.tenant_id == tenant_id,
            SurveyAttempt.instance_id == instance_id,
            SurveyAttempt.assignment_id == assignment_id,
        )
        .order_by(SurveyAttempt.attempt_number.asc(), SurveyAttempt.id.asc())
        .all()
    )


def _best_attempt_payload(attempts: List[SurveyAttempt], strategy: str = "best") -> Optional[Dict[str, Any]]:
    submitted = [attempt for attempt in attempts if attempt.status == "submitted"]
    if not submitted:
        return None
    if strategy == "last":
        selected = submitted[-1]
    else:
        selected = max(submitted, key=lambda item: (float(item.score_value or 0), -(int(item.attempt_number or 0))))
    return {
        "attempt_number": int(selected.attempt_number or 1),
        "score_value": float(selected.score_value or 0),
        "elapsed_seconds": selected.elapsed_seconds,
        "submitted_at": _dt(selected.submitted_at),
        "status": selected.status,
        "result_json": selected.result_json or {},
    }


def _evaluation_status(total_score: Optional[float], passing_score: Optional[float]) -> Optional[str]:
    if total_score is None or passing_score is None:
        return None
    return "aprobado" if float(total_score) >= float(passing_score) else "reprobado"


def _response_attempt_context(db: Session, instance: SurveyInstance, response: SurveyResponse) -> Dict[str, Any]:
    quiz = _quiz_settings(instance)
    attempts = _assignment_attempts(db, instance.tenant_id, instance.id, response.assignment_id)
    current_attempt = next((attempt for attempt in attempts if attempt.response_id == response.id), None)
    attempts_used = len([attempt for attempt in attempts if attempt.status == "submitted"])
    remaining_attempts = max(0, quiz["max_attempts"] - attempts_used)
    if current_attempt and current_attempt.status != "submitted" and remaining_attempts > 0:
        remaining_attempts -= 1
    return {
        "is_quiz": quiz["is_quiz"],
        "current_attempt_number": int(current_attempt.attempt_number or 1) if current_attempt else 1,
        "attempts_used": attempts_used,
        "max_attempts": quiz["max_attempts"],
        "remaining_attempts": max(0, remaining_attempts),
        "attempt_strategy": quiz["attempt_strategy"],
        "timer_seconds": quiz["timer_seconds"],
        "passing_score": quiz["passing_score"],
        "best_attempt": _best_attempt_payload(attempts, quiz["attempt_strategy"]),
        "can_retry": bool(
            quiz["is_quiz"]
            and response.assignment_id
            and response.status == "submitted"
            and attempts_used < quiz["max_attempts"]
        ),
    }


def _is_360_instance(instance: SurveyInstance) -> bool:
    return _is_360_payload(instance.template.survey_type if instance.template else "", instance.external_entity_type or "")


def _response_evaluation_context(db: Session, instance: SurveyInstance, response: SurveyResponse) -> Dict[str, Any]:
    if not _is_360_instance(instance):
        return {"is_360": False, "current": None, "pending": [], "completed": 0, "total": 0}
    rows = (
        db.query(SurveyEvaluation360)
        .filter(
            SurveyEvaluation360.instance_id == instance.id,
            SurveyEvaluation360.tenant_id == instance.tenant_id,
            SurveyEvaluation360.assignment_id == response.assignment_id,
        )
        .order_by(SurveyEvaluation360.id.asc())
        .all()
    )
    current = None
    current_id = str(response.external_entity_id or "").strip()
    for row in rows:
        if current_id and str(row.id) == current_id:
            current = row
            break
    pending = [_evaluation_360_dict(row) for row in rows if row.status != "completed"]
    completed = len([row for row in rows if row.status == "completed"])
    return {
        "is_360": True,
        "current": _evaluation_360_dict(current) if current else None,
        "pending": pending,
        "completed": completed,
        "total": len(rows),
    }


def _response_summary(instance: SurveyInstance, response: SurveyResponse, access_mode: str) -> Dict[str, Any]:
    normalized_access_mode = "public" if access_mode in {"public", "public_link"} else "internal"
    sections = [_section_dict(section) for section in (instance.sections or [])]
    db = object_session(response) or object_session(instance)
    attempt_context = _response_attempt_context(db, instance, response) if db else {
        "is_quiz": False,
        "current_attempt_number": 1,
        "attempts_used": 0,
        "max_attempts": 1,
        "remaining_attempts": 0,
        "attempt_strategy": "best",
        "timer_seconds": 0,
        "passing_score": None,
        "best_attempt": None,
        "can_retry": False,
    }
    evaluation_context = _response_evaluation_context(db, instance, response) if db else {
        "is_360": False,
        "current": None,
        "pending": [],
        "completed": 0,
        "total": 0,
    }
    return {
        "instance": {
            "id": instance.id,
            "nombre": instance.nombre,
            "descripcion": instance.descripcion,
            "status": instance.status,
            "schedule_start_at": _dt(instance.schedule_start_at),
            "schedule_end_at": _dt(instance.schedule_end_at),
            "anonymity_mode": instance.anonymity_mode,
            "audience_mode": instance.audience_mode,
        },
        "response": _response_dict(response),
        "assignment": _assignment_dict(response.assignment) if response.assignment else None,
        "access_mode": normalized_access_mode,
        "draft_exists": response.status == "draft" and bool(response.answers_json),
        "quiz": attempt_context,
        "evaluation_360": evaluation_context,
        "sections": sections,
        "question_types": [{"key": key, **value} for key, value in QUESTION_TYPE_CATALOG.items()],
    }


def _is_answer_present(value: Any) -> bool:
    if isinstance(value, list):
        return any(_is_answer_present(item) for item in value)
    if isinstance(value, dict):
        return bool(value)
    if value is None:
        return False
    return bool(str(value).strip())


def _coerce_answer(question: SurveyQuestion, raw_value: Any) -> Dict[str, Any]:
    definition = get_question_type_definition(question.question_type)
    shape = definition.get("answer_shape")
    options = {str(option.value): option for option in (question.options or [])}
    if shape == "array":
        values = raw_value if isinstance(raw_value, list) else ([] if raw_value is None else [raw_value])
        normalized = [str(item).strip() for item in values if str(item).strip()]
        return {"value": normalized, "items": normalized}
    if shape == "number":
        if raw_value is None or str(raw_value).strip() == "":
            return {"value": None, "items": []}
        text = str(raw_value).strip()
        option = options.get(text)
        return {"value": text, "items": [option.value if option else text]}
    if shape == "json":
        if question.question_type in {"matrix", "likert_scale", "semantic_differential"}:
            rows = {str(option.value): option for option in (question.options or [])}
            columns = {
                str(column.get("value")): column
                for column in ((question.config_json or {}).get("columns") or [])
                if str(column.get("value") or "").strip()
            }
            payload = raw_value if isinstance(raw_value, dict) else {}
            normalized: Dict[str, str] = {}
            for row_key in rows:
                value = str(payload.get(row_key) or "").strip()
                if value and value in columns:
                    normalized[row_key] = value
            return {"value": normalized, "items": list(normalized.values())}
        if question.question_type == "file_upload":
            payload = raw_value if isinstance(raw_value, dict) else {}
            file_name = str(payload.get("name") or "").strip()
            if not file_name:
                return {"value": {}, "items": []}
            return {
                "value": {
                    "name": file_name,
                    "type": str(payload.get("type") or "").strip(),
                    "size": int(payload.get("size") or 0),
                    "data_url": str(payload.get("data_url") or "").strip(),
                },
                "items": [file_name],
            }
        if raw_value is None:
            return {"value": {}, "items": []}
        return {"value": raw_value if isinstance(raw_value, dict) else {}, "items": []}
    if shape == "string":
        if raw_value is None:
            return {"value": "", "items": []}
        text = str(raw_value).strip()
        return {"value": text, "items": [text] if text else []}
    return {"value": raw_value, "items": [raw_value] if raw_value is not None else []}


def _validate_answers_payload(instance: SurveyInstance, answers: Dict[str, Any], require_all: bool) -> List[str]:
    errors: List[str] = []
    for section in instance.sections or []:
        for question in section.questions or []:
            key = str(question.id)
            raw_value = answers.get(key)
            coerced = _coerce_answer(question, raw_value)
            validation = question.validation_json or {}
            required = bool(question.is_required or validation.get("required"))
            if require_all and required and not _is_answer_present(coerced["value"]):
                errors.append(f"La pregunta '{question.titulo}' es obligatoria.")
                continue
            if not _is_answer_present(coerced["value"]):
                continue
            if question.question_type in {"single_choice", "live_poll_single_choice", "yes_no", "true_false", "quiz_single_choice", "scale_1_5", "live_scale_1_5", "nps_0_10", "dropdown", "image_choice"}:
                option_values = {str(option.value) for option in (question.options or [])}
                if str(coerced["value"]) not in option_values:
                    errors.append(f"La respuesta de '{question.titulo}' no es válida.")
            elif question.question_type in {"multiple_choice", "ranking"}:
                option_values = {str(option.value) for option in (question.options or [])}
                for item in coerced["value"]:
                    if str(item) not in option_values:
                        errors.append(f"La respuesta de '{question.titulo}' contiene opciones inválidas.")
                        break
                if question.question_type == "ranking" and len(set(coerced["value"])) != len(coerced["value"]):
                    errors.append(f"La respuesta de '{question.titulo}' contiene valores duplicados.")
                min_choices = validation.get("min_choices")
                max_choices = validation.get("max_choices")
                if min_choices is not None and len(coerced["value"]) < int(min_choices):
                    errors.append(f"La pregunta '{question.titulo}' requiere al menos {int(min_choices)} selección(es).")
                if max_choices is not None and len(coerced["value"]) > int(max_choices):
                    errors.append(f"La pregunta '{question.titulo}' permite máximo {int(max_choices)} selección(es).")
            elif question.question_type in {"short_text", "long_text", "word_cloud"}:
                max_length = validation.get("max_length")
                if max_length is not None and len(str(coerced["value"])) > int(max_length):
                    errors.append(f"La respuesta de '{question.titulo}' excede la longitud permitida.")
            elif question.question_type in {"matrix", "likert_scale", "semantic_differential"}:
                row_values = coerced["value"] if isinstance(coerced["value"], dict) else {}
                valid_rows = {str(option.value) for option in (question.options or [])}
                valid_cols = {
                    str(column.get("value"))
                    for column in ((question.config_json or {}).get("columns") or [])
                    if str(column.get("value") or "").strip()
                }
                for row_key, col_value in row_values.items():
                    if row_key not in valid_rows or str(col_value) not in valid_cols:
                        errors.append(f"La respuesta de '{question.titulo}' contiene valores inválidos.")
                        break
                if required and require_all and len(row_values) < len(valid_rows):
                    errors.append(f"La pregunta '{question.titulo}' requiere responder todas las filas.")
            elif question.question_type == "slider":
                try:
                    slider_value = float(coerced["value"])
                except (TypeError, ValueError):
                    errors.append(f"La respuesta de '{question.titulo}' no es numérica.")
                    continue
                min_value = validation.get("min_value")
                max_value = validation.get("max_value")
                if min_value is not None and slider_value < float(min_value):
                    errors.append(f"La respuesta de '{question.titulo}' es menor al mínimo permitido.")
                if max_value is not None and slider_value > float(max_value):
                    errors.append(f"La respuesta de '{question.titulo}' excede el máximo permitido.")
            elif question.question_type == "file_upload":
                payload = coerced["value"] if isinstance(coerced["value"], dict) else {}
                max_size_mb = validation.get("max_size_mb") or (question.config_json or {}).get("max_size_mb")
                size_bytes = int(payload.get("size") or 0)
                if max_size_mb is not None and size_bytes > int(float(max_size_mb) * 1024 * 1024):
                    errors.append(f"El archivo de '{question.titulo}' excede el tamaño permitido.")
    return errors


def _upsert_response_items(db: Session, response: SurveyResponse, instance: SurveyInstance, answers: Dict[str, Any]) -> Dict[str, Any]:
    db.query(SurveyResponseItem).filter(SurveyResponseItem.response_id == response.id).delete(synchronize_session=False)
    normalized_answers: Dict[str, Any] = {}
    total_questions = 0
    answered_questions = 0
    total_score = 0.0
    score_has_value = False
    question_scores: Dict[str, Dict[str, Any]] = {}
    section_scores: Dict[str, Dict[str, Any]] = {}
    competency_scores: Dict[str, Dict[str, Any]] = {}
    nps_values: List[float] = []
    csat_values: List[float] = []
    ces_values: List[float] = []
    survey_scoring_mode = str((instance.settings_json or {}).get("scoring_mode") or "").strip().lower()

    for section in instance.sections or []:
        section_total = 0.0
        section_scored_questions = 0
        section_answered_questions = 0
        for question in section.questions or []:
            total_questions += 1
            key = str(question.id)
            raw_value = answers.get(key)
            coerced = _coerce_answer(question, raw_value)
            value = coerced["value"]
            normalized_answers[key] = value
            if not _is_answer_present(value):
                continue
            answered_questions += 1
            section_answered_questions += 1
            question_score_total = 0.0
            question_score_has_value = False
            correct_count = 0
            answer_count = 0
            if question.question_type in {"multiple_choice", "ranking"}:
                selected_values = [str(item) for item in value]
                options_map = {str(option.value): option for option in (question.options or [])}
                for index, item in enumerate(selected_values):
                    option = options_map.get(item)
                    score_value = option.score_value if option and option.score_value is not None else None
                    is_correct = option.is_correct if option else None
                    db.add(
                        SurveyResponseItem(
                            tenant_id=response.tenant_id,
                            response_id=response.id,
                            question_id=question.id,
                            option_id=option.id if option else None,
                            item_index=index,
                            answer_text=option.label if option else item,
                            answer_value=item,
                            answer_json={"value": item},
                            score_value=score_value,
                            is_correct=is_correct,
                        )
                    )
                    if score_value is not None:
                        total_score += float(score_value)
                        question_score_total += float(score_value)
                        score_has_value = True
                        question_score_has_value = True
                    if is_correct:
                        correct_count += 1
                    answer_count += 1
            elif question.question_type in {"matrix", "likert_scale", "semantic_differential"}:
                selected_map = value if isinstance(value, dict) else {}
                row_map = {str(option.value): option for option in (question.options or [])}
                column_map = {
                    str(column.get("value")): column
                    for column in ((question.config_json or {}).get("columns") or [])
                    if str(column.get("value") or "").strip()
                }
                for index, (row_key, col_value) in enumerate(selected_map.items()):
                    row_option = row_map.get(str(row_key))
                    column = column_map.get(str(col_value))
                    score_value = column.get("score_value") if column and column.get("score_value") is not None else None
                    answer_text = f"{row_option.label if row_option else row_key}: {column.get('label') if column else col_value}"
                    db.add(
                        SurveyResponseItem(
                            tenant_id=response.tenant_id,
                            response_id=response.id,
                            question_id=question.id,
                            option_id=row_option.id if row_option else None,
                            item_index=index,
                            answer_text=answer_text,
                            answer_value=str(col_value),
                            answer_json={"row": row_key, "value": str(col_value)},
                            score_value=score_value,
                            is_correct=None,
                        )
                    )
                    if score_value is not None:
                        total_score += float(score_value)
                        question_score_total += float(score_value)
                        score_has_value = True
                        question_score_has_value = True
                    answer_count += 1
            elif question.question_type == "file_upload":
                file_payload = value if isinstance(value, dict) else {}
                file_name = str(file_payload.get("name") or "").strip()
                db.add(
                    SurveyResponseItem(
                        tenant_id=response.tenant_id,
                        response_id=response.id,
                        question_id=question.id,
                        option_id=None,
                        item_index=0,
                        answer_text=file_name,
                        answer_value=file_name,
                        answer_json=file_payload,
                        score_value=None,
                        is_correct=None,
                    )
                )
                answer_count = 1
            else:
                text_value = str(value).strip() if value is not None else ""
                option = None
                if question.question_type in {"single_choice", "live_poll_single_choice", "yes_no", "true_false", "quiz_single_choice", "scale_1_5", "live_scale_1_5", "nps_0_10", "dropdown", "image_choice"}:
                    for candidate in question.options or []:
                        if str(candidate.value) == text_value:
                            option = candidate
                            break
                score_value = option.score_value if option and option.score_value is not None else None
                is_correct = option.is_correct if option else None
                answer_text = option.label if option else text_value
                answer_json = {"value": value}
                db.add(
                    SurveyResponseItem(
                        tenant_id=response.tenant_id,
                        response_id=response.id,
                        question_id=question.id,
                        option_id=option.id if option else None,
                        item_index=0,
                        answer_text=answer_text,
                        answer_value=text_value,
                        answer_json=answer_json,
                        score_value=score_value,
                        is_correct=is_correct,
                    )
                )
                if score_value is not None:
                    total_score += float(score_value)
                    question_score_total += float(score_value)
                    score_has_value = True
                    question_score_has_value = True
                if is_correct:
                    correct_count = 1
                answer_count = 1

            metric_kind = str((question.config_json or {}).get("metric_kind") or "").strip().lower()
            if question.question_type == "nps_0_10" and value is not None:
                try:
                    nps_values.append(float(value))
                except (TypeError, ValueError):
                    pass
            if question.question_type in {"scale_1_5", "live_scale_1_5", "slider"}:
                try:
                    scale_value = float(value)
                except (TypeError, ValueError):
                    scale_value = None
                if scale_value is not None:
                    if survey_scoring_mode == "ces" or metric_kind == "ces":
                        ces_values.append(scale_value)
                    if survey_scoring_mode in {"", "csat"} and metric_kind != "ces":
                        csat_values.append(scale_value)

            question_score = question_score_total if question_score_has_value else None
            if question_score is not None:
                section_total += question_score
                section_scored_questions += 1
            question_scores[key] = {
                "question_id": question.id,
                "question_type": question.question_type,
                "score": question_score,
                "max_score": question.max_score,
                "min_score": question.min_score,
                "is_correct": bool(correct_count) if question.question_type == "quiz_single_choice" else None,
                "correct_answers": correct_count if question.question_type == "quiz_single_choice" else None,
                "answer_count": answer_count,
            }
            competency_meta = section.settings_json or {}
            question_meta = question.config_json or {}
            competency_key = str(
                question_meta.get("competency_key")
                or competency_meta.get("competency_key")
                or section.id
            )
            competency_label = str(
                question_meta.get("competency_label")
                or competency_meta.get("competency_label")
                or section.titulo
            )
            bucket = competency_scores.setdefault(
                competency_key,
                {
                    "competency_key": competency_key,
                    "competency_label": competency_label,
                    "question_scores": [],
                    "answered_questions": 0,
                    "total_questions": 0,
                },
            )
            bucket["total_questions"] += 1
            if _is_answer_present(value):
                bucket["answered_questions"] += 1
            if question_score is not None:
                bucket["question_scores"].append(float(question_score))

        section_key = str(section.id)
        section_scores[section_key] = {
            "section_id": section.id,
            "titulo": section.titulo,
            "answered_questions": section_answered_questions,
            "total_questions": len(section.questions or []),
            "score_total": section_total if section_scored_questions else None,
            "score_avg": round(section_total / section_scored_questions, 2) if section_scored_questions else None,
        }

    completion_pct = round((answered_questions / total_questions) * 100, 2) if total_questions else 0.0
    quiz_questions = [
        payload for payload in question_scores.values() if payload.get("question_type") == "quiz_single_choice"
    ]
    quiz_answered = [payload for payload in quiz_questions if payload.get("is_correct") is not None]
    quiz_correct = sum(1 for payload in quiz_answered if payload.get("is_correct"))
    quiz_approval_pct = round((quiz_correct / len(quiz_answered)) * 100, 2) if quiz_answered else None
    nps_score = None
    if nps_values:
        promoters = sum(1 for value in nps_values if value >= 9)
        detractors = sum(1 for value in nps_values if value <= 6)
        nps_score = round(((promoters / len(nps_values)) * 100) - ((detractors / len(nps_values)) * 100), 2)
    csat_score = round((sum(1 for value in csat_values if value >= 4) / len(csat_values)) * 100, 2) if csat_values else None
    ces_score = round(sum(ces_values) / len(ces_values), 2) if ces_values else None
    return {
        "answers_json": normalized_answers,
        "completion_pct": completion_pct,
        "total_score": total_score if score_has_value else None,
        "answered_questions": answered_questions,
        "total_questions": total_questions,
        "question_scores": question_scores,
        "section_scores": section_scores,
        "competency_scores": {
            key: {
                "competency_key": payload["competency_key"],
                "competency_label": payload["competency_label"],
                "score_avg": round(sum(payload["question_scores"]) / len(payload["question_scores"]), 2) if payload["question_scores"] else None,
                "answered_questions": payload["answered_questions"],
                "total_questions": payload["total_questions"],
            }
            for key, payload in competency_scores.items()
        },
        "quiz_approval_pct": quiz_approval_pct,
        "nps_score": nps_score,
        "csat_score": csat_score,
        "ces_score": ces_score,
    }


def _upsert_result_metric(
    db: Session,
    tenant_id: str,
    instance_id: int,
    segment_type: str,
    segment_key: str,
    metric_key: str,
    metric_label: str,
    value_numeric: Optional[float],
    sample_size: int,
    result_json: Optional[Dict[str, Any]] = None,
) -> None:
    row = (
        db.query(SurveyResult)
        .filter(
            SurveyResult.tenant_id == tenant_id,
            SurveyResult.instance_id == instance_id,
            SurveyResult.segment_key == segment_key,
            SurveyResult.metric_key == metric_key,
        )
        .first()
    )
    if not row:
        row = SurveyResult(
            tenant_id=tenant_id,
            instance_id=instance_id,
            segment_type=segment_type,
            segment_key=segment_key,
            metric_key=metric_key,
        )
        db.add(row)
    row.segment_type = segment_type
    row.metric_label = metric_label
    row.value_numeric = value_numeric
    row.value_text = None if value_numeric is not None else ""
    row.sample_size = sample_size
    row.result_json = result_json or {}
    row.computed_at = datetime.utcnow()


def _refresh_instance_results(db: Session, instance: SurveyInstance) -> None:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_analytics import _report_360

    responses = [response for response in (instance.responses or []) if response.status == "submitted"]
    tenant_id = instance.tenant_id
    instance_id = instance.id
    db.query(SurveyResult).filter(
        SurveyResult.tenant_id == tenant_id,
        SurveyResult.instance_id == instance_id,
    ).delete(synchronize_session=False)
    if not responses:
        return
    quiz = _quiz_settings(instance)
    if quiz["is_quiz"]:
        responses_by_id = {response.id: response for response in responses}
        selected_responses: List[SurveyResponse] = []
        for assignment in instance.assignments or []:
            attempts = [attempt for attempt in (assignment.attempts or []) if attempt.status == "submitted" and attempt.response_id in responses_by_id]
            if not attempts:
                continue
            best_attempt = _best_attempt_payload(attempts, quiz["attempt_strategy"])
            if not best_attempt:
                continue
            selected = next(
                (attempt for attempt in attempts if int(attempt.attempt_number or 1) == int(best_attempt["attempt_number"])),
                None,
            )
            if selected and selected.response_id in responses_by_id:
                selected_responses.append(responses_by_id[selected.response_id])
        if selected_responses:
            responses = selected_responses

    total_scores = [float(response.total_score) for response in responses if response.total_score is not None]
    completion_values = [float(response.completion_pct or 0) for response in responses]
    nps_values: List[float] = []
    csat_values: List[float] = []
    ces_values: List[float] = []
    quiz_values: List[float] = []
    evaluation_statuses: List[str] = []
    section_buckets: Dict[str, Dict[str, Any]] = {}

    for response in responses:
        metrics = response.metrics_json or {}
        if metrics.get("nps_score") is not None:
            nps_values.append(float(metrics["nps_score"]))
        if metrics.get("csat_score") is not None:
            csat_values.append(float(metrics["csat_score"]))
        if metrics.get("ces_score") is not None:
            ces_values.append(float(metrics["ces_score"]))
        if metrics.get("quiz_approval_pct") is not None:
            quiz_values.append(float(metrics["quiz_approval_pct"]))
        if metrics.get("evaluation_status"):
            evaluation_statuses.append(str(metrics["evaluation_status"]))
        for section_id, payload in (metrics.get("section_scores") or {}).items():
            bucket = section_buckets.setdefault(
                str(section_id),
                {"score_values": [], "completion_values": [], "titulo": payload.get("titulo") or f"Sección {section_id}"},
            )
            if payload.get("score_avg") is not None:
                bucket["score_values"].append(float(payload["score_avg"]))
            total_questions = int(payload.get("total_questions") or 0)
            answered_questions = int(payload.get("answered_questions") or 0)
            if total_questions:
                bucket["completion_values"].append(round((answered_questions / total_questions) * 100, 2))

    _upsert_result_metric(
        db, tenant_id, instance_id, "general", "general", "responses_count", "Respuestas enviadas",
        float(len(responses)), len(responses), {"responses_count": len(responses)}
    )
    _upsert_result_metric(
        db, tenant_id, instance_id, "general", "general", "completion_pct_avg", "Promedio de finalización",
        round(sum(completion_values) / len(completion_values), 2) if completion_values else None,
        len(responses),
        {"values": completion_values},
    )
    if total_scores:
        _upsert_result_metric(
            db, tenant_id, instance_id, "general", "general", "total_score_avg", "Score promedio total",
            round(sum(total_scores) / len(total_scores), 2),
            len(total_scores),
            {"values": total_scores},
        )
    if quiz_values:
        _upsert_result_metric(
            db, tenant_id, instance_id, "general", "general", "quiz_approval_pct", "Aprobación de quiz",
            round(sum(quiz_values) / len(quiz_values), 2),
            len(quiz_values),
            {"values": quiz_values},
        )
    if evaluation_statuses:
        approved = len([item for item in evaluation_statuses if item == "aprobado"])
        failed = len([item for item in evaluation_statuses if item == "reprobado"])
        _upsert_result_metric(
            db, tenant_id, instance_id, "general", "general", "approved_count", "Aprobados",
            float(approved),
            len(evaluation_statuses),
            {"approved_count": approved},
        )
        _upsert_result_metric(
            db, tenant_id, instance_id, "general", "general", "failed_count", "Reprobados",
            float(failed),
            len(evaluation_statuses),
            {"failed_count": failed},
        )
    if nps_values:
        _upsert_result_metric(
            db, tenant_id, instance_id, "general", "general", "nps_score", "NPS",
            round(sum(nps_values) / len(nps_values), 2),
            len(nps_values),
            {"values": nps_values},
        )
    if csat_values:
        _upsert_result_metric(
            db, tenant_id, instance_id, "general", "general", "csat_score", "CSAT",
            round(sum(csat_values) / len(csat_values), 2),
            len(csat_values),
            {"values": csat_values},
        )
    if ces_values:
        _upsert_result_metric(
            db, tenant_id, instance_id, "general", "general", "ces_score", "CES",
            round(sum(ces_values) / len(ces_values), 2),
            len(ces_values),
            {"values": ces_values},
        )
    for section_id, bucket in section_buckets.items():
        if bucket["score_values"]:
            _upsert_result_metric(
                db,
                tenant_id,
                instance_id,
                "section",
                section_id,
                "section_score_avg",
                f"Score promedio · {bucket['titulo']}",
                round(sum(bucket["score_values"]) / len(bucket["score_values"]), 2),
                len(bucket["score_values"]),
                {"values": bucket["score_values"], "titulo": bucket["titulo"]},
            )
        if bucket["completion_values"]:
            _upsert_result_metric(
                db,
                tenant_id,
                instance_id,
                "section",
                section_id,
                "section_completion_pct",
                f"Finalización · {bucket['titulo']}",
                round(sum(bucket["completion_values"]) / len(bucket["completion_values"]), 2),
                len(bucket["completion_values"]),
                {"values": bucket["completion_values"], "titulo": bucket["titulo"]},
            )
    if _is_360_instance(instance):
        report_360 = _report_360(instance)
        for row in report_360.get("by_relationship") or []:
            _upsert_result_metric(
                db,
                tenant_id,
                instance_id,
                "evaluation_360_relationship",
                str(row["relationship_type"]),
                "score_avg",
                f"Promedio 360 · {row['relationship_type']}",
                row.get("score_avg"),
                int(row.get("responses") or 0),
                row,
            )
        for row in report_360.get("by_competency") or []:
            _upsert_result_metric(
                db,
                tenant_id,
                instance_id,
                "evaluation_360_competency",
                str(row["competency_key"]),
                "score_avg",
                f"Competencia 360 · {row['competency_label']}",
                row.get("score_avg"),
                int(row.get("responses") or 0),
                row,
            )


def _apply_response_anonymity(instance: SurveyInstance, response: SurveyResponse) -> None:
    mode = str(instance.anonymity_mode or "identified").strip().lower()
    if mode == "anonymous":
        response.respondent_key = None
        response.respondent_name_snapshot = "Anónimo"
        response.respondent_role_snapshot = None
        response.respondent_area_snapshot = None
        response.respondent_position_snapshot = None
        response.respondent_company_snapshot = None
        response.external_entity_id = None
    elif mode == "restricted":
        response.respondent_name_snapshot = response.respondent_name_snapshot or "Restringido"


def _active_attempt_for_response(db: Session, tenant_id: str, response: SurveyResponse) -> Optional[SurveyAttempt]:
    return (
        db.query(SurveyAttempt)
        .filter(SurveyAttempt.tenant_id == tenant_id, SurveyAttempt.response_id == response.id)
        .order_by(SurveyAttempt.attempt_number.desc(), SurveyAttempt.id.desc())
        .first()
    )


def _enforce_quiz_attempt_constraints(db: Session, response: SurveyResponse) -> Dict[str, Any]:
    instance = response.instance
    quiz = _quiz_settings(instance)
    if not quiz["is_quiz"] or not response.assignment_id:
        return quiz
    attempt = _active_attempt_for_response(db, response.tenant_id, response)
    if not attempt:
        return quiz
    if attempt.status == "submitted":
        raise ValueError("El intento actual ya fue enviado.")
    if quiz["timer_seconds"] and attempt.started_at:
        elapsed = max(0, int((datetime.utcnow() - attempt.started_at).total_seconds()))
        if elapsed > quiz["timer_seconds"]:
            raise ValueError("El tiempo del intento ya expiró.")
    return quiz


def start_internal_response(instance_id: int, tenant_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_store import _refresh_instance_lifecycle

    db = get_db()
    try:
        _refresh_instance_lifecycle(db, instance_id=instance_id, tenant_id=tenant_id)
        instance = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not instance:
            raise ValueError("Encuesta no encontrada.")
        _ensure_instance_available_for_response(instance, "internal")
        user_id = str(user.get("user_id") or user.get("user_key") or "").strip()
        assignment = None
        if user_id:
            assignment = (
                db.query(SurveyAssignment)
                .filter(
                    SurveyAssignment.instance_id == instance_id,
                    SurveyAssignment.tenant_id == tenant_id,
                    SurveyAssignment.assignee_key == user_id,
                )
                .first()
            )
        if not assignment and instance.audience_mode != "public_link":
            raise ValueError("No tienes una asignación activa para esta encuesta.")
        now = datetime.utcnow()
        quiz = _quiz_settings(instance)
        evaluation_row = None
        if assignment and _is_360_instance(instance):
            evaluation_rows = (
                db.query(SurveyEvaluation360)
                .filter(
                    SurveyEvaluation360.instance_id == instance.id,
                    SurveyEvaluation360.tenant_id == tenant_id,
                    SurveyEvaluation360.assignment_id == assignment.id,
                )
                .order_by(SurveyEvaluation360.status.asc(), SurveyEvaluation360.id.asc())
                .all()
            )
            for row in evaluation_rows:
                response_for_row = _find_existing_response(
                    db,
                    instance_id=instance_id,
                    tenant_id=tenant_id,
                    assignment_id=assignment.id,
                    respondent_key=user_id,
                    external_entity_type="evaluation_360",
                    external_entity_id=str(row.id),
                )
                if response_for_row and response_for_row.status != "submitted":
                    evaluation_row = row
                    break
            if evaluation_row is None:
                evaluation_row = next((row for row in evaluation_rows if row.status != "completed"), None)
            if evaluation_row is None and evaluation_rows:
                evaluation_row = evaluation_rows[0]
        response = None
        if assignment:
            attempts = _assignment_attempts(db, tenant_id, instance.id, assignment.id)
            current_attempt = attempts[-1] if attempts else None
            if current_attempt and current_attempt.status != "submitted" and current_attempt.response_id and not evaluation_row:
                response = (
                    db.query(SurveyResponse)
                    .filter(SurveyResponse.id == current_attempt.response_id, SurveyResponse.tenant_id == tenant_id)
                    .first()
                )
            elif quiz["is_quiz"] and current_attempt and current_attempt.status == "submitted":
                submitted_attempts = len([attempt for attempt in attempts if attempt.status == "submitted"])
                if submitted_attempts < quiz["max_attempts"]:
                    response = SurveyResponse(
                        tenant_id=tenant_id,
                        instance_id=instance.id,
                        assignment_id=assignment.id,
                        respondent_key=user_id or None,
                        respondent_name_snapshot=user.get("nombre"),
                        respondent_role_snapshot=user.get("role"),
                        respondent_area_snapshot=user.get("departamento"),
                        respondent_position_snapshot=user.get("puesto"),
                        respondent_company_snapshot=user.get("empresa"),
                        source_app="encuestas",
                        external_entity_type="internal_user",
                        external_entity_id=user_id or None,
                        status="draft",
                        submission_channel="internal",
                        started_at=now,
                        last_saved_at=now,
                        answers_json={},
                        metrics_json={},
                    )
                    db.add(response)
                    db.flush()
                    _find_or_create_attempt(
                        db,
                        tenant_id,
                        instance.id,
                        assignment.id,
                        response.id,
                        attempt_number=submitted_attempts + 1,
                    )
                elif current_attempt.response_id:
                    response = (
                        db.query(SurveyResponse)
                        .filter(SurveyResponse.id == current_attempt.response_id, SurveyResponse.tenant_id == tenant_id)
                        .first()
                    )
            if response is None:
                response = _find_existing_response(
                    db,
                    instance_id=instance_id,
                    tenant_id=tenant_id,
                    assignment_id=assignment.id if assignment else None,
                    respondent_key=user_id,
                    external_entity_type="evaluation_360" if evaluation_row else "",
                    external_entity_id=str(evaluation_row.id) if evaluation_row else "",
                )
        else:
            response = _find_existing_response(
                db,
                instance_id=instance_id,
                tenant_id=tenant_id,
                assignment_id=None,
                respondent_key=user_id,
            )
        if not response:
            response = SurveyResponse(
                tenant_id=tenant_id,
                instance_id=instance.id,
                assignment_id=assignment.id if assignment else None,
                respondent_key=user_id or None,
                respondent_name_snapshot=user.get("nombre"),
                respondent_role_snapshot=user.get("role"),
                respondent_area_snapshot=user.get("departamento"),
                respondent_position_snapshot=user.get("puesto"),
                respondent_company_snapshot=user.get("empresa"),
                source_app="encuestas",
                external_entity_type="evaluation_360" if evaluation_row else "internal_user",
                external_entity_id=str(evaluation_row.id) if evaluation_row else (user_id or None),
                status="draft",
                submission_channel="internal",
                started_at=now,
                last_saved_at=now,
                answers_json={},
                metrics_json={},
            )
            db.add(response)
            db.flush()
        if evaluation_row:
            response.external_entity_type = "evaluation_360"
            response.external_entity_id = str(evaluation_row.id)
            response.metrics_json = {
                **(response.metrics_json or {}),
                "evaluation_360": {
                    "evaluation_id": evaluation_row.id,
                    "evaluatee_key": evaluation_row.evaluatee_key,
                    "evaluatee_name_snapshot": evaluation_row.evaluatee_name_snapshot,
                    "relationship_type": evaluation_row.relationship_type,
                },
            }
        if assignment:
            assignment.status = "in_progress" if response.status == "draft" else assignment.status
            assignment.updated_at = now
        if assignment:
            existing_attempt = (
                db.query(SurveyAttempt)
                .filter(SurveyAttempt.tenant_id == tenant_id, SurveyAttempt.response_id == response.id)
                .first()
            )
            if not existing_attempt:
                _find_or_create_attempt(db, tenant_id, instance.id, assignment.id if assignment else None, response.id)
        db.commit()
        db.refresh(response)
        return _response_summary(instance, response, "internal")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def start_public_response(public_token: str, tenant_id: str, response_key: str = "") -> Dict[str, Any]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_store import _refresh_instance_lifecycle

    db = get_db()
    try:
        token = str(public_token or "").strip()
        _refresh_instance_lifecycle(db, tenant_id=tenant_id)
        instance = (
            db.query(SurveyInstance)
            .filter(
                SurveyInstance.tenant_id == tenant_id,
                SurveyInstance.public_link_token == token,
            )
            .first()
        )
        if not instance:
            raise ValueError("Encuesta no encontrada.")
        _ensure_instance_available_for_response(instance, "public")
        respondent_key = str(response_key or "").strip()
        if not respondent_key:
            respondent_key = f"public:{instance.id}:{uuid4().hex}"
        response = _find_existing_response(
            db,
            instance_id=instance.id,
            tenant_id=tenant_id,
            respondent_key=respondent_key,
        )
        now = datetime.utcnow()
        if not response:
            response = SurveyResponse(
                tenant_id=tenant_id,
                instance_id=instance.id,
                assignment_id=None,
                respondent_key=respondent_key,
                respondent_name_snapshot="Participante externo",
                source_app="encuestas",
                external_entity_type="public_link",
                external_entity_id=token,
                status="draft",
                submission_channel="public_link",
                started_at=now,
                last_saved_at=now,
                answers_json={},
                metrics_json={},
            )
            db.add(response)
            db.flush()
        db.commit()
        db.refresh(response)
        payload = _response_summary(instance, response, "public")
        payload["response_key"] = respondent_key
        return payload
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_response_session(response_id: int, tenant_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        response = (
            db.query(SurveyResponse)
            .join(SurveyInstance, SurveyResponse.instance_id == SurveyInstance.id)
            .filter(SurveyResponse.id == response_id, SurveyResponse.tenant_id == tenant_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not response:
            return None
        return _response_summary(response.instance, response, response.submission_channel or "internal")
    finally:
        db.close()


def save_response_draft(response_id: int, tenant_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        response = (
            db.query(SurveyResponse)
            .join(SurveyInstance, SurveyResponse.instance_id == SurveyInstance.id)
            .filter(SurveyResponse.id == response_id, SurveyResponse.tenant_id == tenant_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not response:
            raise ValueError("Respuesta no encontrada.")
        if response.status == "submitted":
            raise ValueError("La respuesta ya fue enviada.")
        instance = response.instance
        _ensure_instance_available_for_response(instance, "public" if response.submission_channel == "public_link" else "internal")
        quiz = _enforce_quiz_attempt_constraints(db, response)
        merged_answers = dict(response.answers_json or {})
        for key, value in (answers or {}).items():
            merged_answers[str(key)] = value
        errors = _validate_answers_payload(instance, merged_answers, require_all=False)
        if errors:
            raise ValueError(errors[0])
        stats = _upsert_response_items(db, response, instance, merged_answers)
        now = datetime.utcnow()
        attempt = _active_attempt_for_response(db, tenant_id, response)
        response.answers_json = stats["answers_json"]
        response.completion_pct = stats["completion_pct"]
        response.total_score = stats["total_score"]
        response.metrics_json = {
            **({"evaluation_360": (response.metrics_json or {}).get("evaluation_360")} if (response.metrics_json or {}).get("evaluation_360") else {}),
            "answered_questions": stats["answered_questions"],
            "total_questions": stats["total_questions"],
            "question_scores": stats["question_scores"],
            "section_scores": stats["section_scores"],
            "competency_scores": stats["competency_scores"],
            "quiz_approval_pct": stats["quiz_approval_pct"],
            "nps_score": stats["nps_score"],
            "csat_score": stats["csat_score"],
            "ces_score": stats["ces_score"],
            "attempt_number": int(attempt.attempt_number or 1) if attempt else 1,
            "attempt_strategy": quiz["attempt_strategy"],
            "max_attempts": quiz["max_attempts"],
            "timer_seconds": quiz["timer_seconds"],
            "passing_score": quiz["passing_score"],
            "evaluation_status": _evaluation_status(stats["total_score"], quiz["passing_score"]),
        }
        response.last_saved_at = now
        response.updated_at = now
        if response.assignment:
            response.assignment.status = "in_progress"
            response.assignment.updated_at = now
        db.commit()
        db.refresh(response)
        return _response_summary(instance, response, response.submission_channel or "internal")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def submit_response(response_id: int, tenant_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_automation import queue_backendhook_event

    db = get_db()
    try:
        response = (
            db.query(SurveyResponse)
            .join(SurveyInstance, SurveyResponse.instance_id == SurveyInstance.id)
            .filter(SurveyResponse.id == response_id, SurveyResponse.tenant_id == tenant_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not response:
            raise ValueError("Respuesta no encontrada.")
        if response.status == "submitted":
            return _response_summary(response.instance, response, response.submission_channel or "internal")
        instance = response.instance
        _ensure_instance_available_for_response(instance, "public" if response.submission_channel == "public_link" else "internal")
        quiz = _enforce_quiz_attempt_constraints(db, response)
        merged_answers = dict(response.answers_json or {})
        for key, value in (answers or {}).items():
            merged_answers[str(key)] = value
        errors = _validate_answers_payload(instance, merged_answers, require_all=True)
        if errors:
            raise ValueError(errors[0])
        stats = _upsert_response_items(db, response, instance, merged_answers)
        now = datetime.utcnow()
        attempt = _active_attempt_for_response(db, tenant_id, response)
        evaluation_status = _evaluation_status(stats["total_score"], quiz["passing_score"])
        response.answers_json = stats["answers_json"]
        response.completion_pct = 100.0 if stats["total_questions"] else 0.0
        response.total_score = stats["total_score"]
        response.metrics_json = {
            **({"evaluation_360": (response.metrics_json or {}).get("evaluation_360")} if (response.metrics_json or {}).get("evaluation_360") else {}),
            "answered_questions": stats["answered_questions"],
            "total_questions": stats["total_questions"],
            "submitted": True,
            "question_scores": stats["question_scores"],
            "section_scores": stats["section_scores"],
            "competency_scores": stats["competency_scores"],
            "quiz_approval_pct": stats["quiz_approval_pct"],
            "nps_score": stats["nps_score"],
            "csat_score": stats["csat_score"],
            "ces_score": stats["ces_score"],
            "attempt_number": int(attempt.attempt_number or 1) if attempt else 1,
            "attempt_strategy": quiz["attempt_strategy"],
            "max_attempts": quiz["max_attempts"],
            "timer_seconds": quiz["timer_seconds"],
            "passing_score": quiz["passing_score"],
            "evaluation_status": evaluation_status,
        }
        response.status = "submitted"
        response.last_saved_at = now
        response.submitted_at = now
        response.updated_at = now
        _apply_response_anonymity(instance, response)
        evaluation_row = None
        if str(response.external_entity_type or "") == "evaluation_360" and str(response.external_entity_id or "").isdigit():
            evaluation_row = (
                db.query(SurveyEvaluation360)
                .filter(
                    SurveyEvaluation360.id == int(str(response.external_entity_id)),
                    SurveyEvaluation360.tenant_id == tenant_id,
                )
                .first()
            )
            if evaluation_row:
                evaluation_row.status = "completed"
                evaluation_row.updated_at = now
        if response.assignment:
            response.assignment.response_count = (
                db.query(SurveyResponse)
                .filter(
                    SurveyResponse.assignment_id == response.assignment.id,
                    SurveyResponse.tenant_id == tenant_id,
                    SurveyResponse.status == "submitted",
                )
                .count()
            )
            if evaluation_row:
                pending_links = (
                    db.query(SurveyEvaluation360)
                    .filter(
                        SurveyEvaluation360.assignment_id == response.assignment.id,
                        SurveyEvaluation360.tenant_id == tenant_id,
                        SurveyEvaluation360.status != "completed",
                    )
                    .count()
                )
                response.assignment.status = "completed" if pending_links == 0 else "in_progress"
            else:
                response.assignment.status = "completed"
            response.assignment.updated_at = now
            if attempt:
                attempt.response_id = response.id
                attempt.status = "submitted"
                attempt.submitted_at = now
                if attempt.started_at:
                    attempt.elapsed_seconds = max(0, int((now - attempt.started_at).total_seconds()))
                attempt.score_value = response.total_score
                attempt.result_json = {
                    "question_scores": stats["question_scores"],
                    "section_scores": stats["section_scores"],
                    "quiz_approval_pct": stats["quiz_approval_pct"],
                    "nps_score": stats["nps_score"],
                    "csat_score": stats["csat_score"],
                    "ces_score": stats["ces_score"],
                    "evaluation_status": evaluation_status,
                    "passing_score": quiz["passing_score"],
                }
                attempt.updated_at = now
        _refresh_instance_results(db, instance)
        db.commit()
        db.refresh(response)
        summary = _response_summary(instance, response, response.submission_channel or "internal")
        queue_backendhook_event(
            tenant_id=tenant_id,
            instance_id=instance.id,
            event_name="response_submitted",
            payload={
                "response": summary,
                "metrics": response.metrics_json or {},
            },
            assignment_id=response.assignment.id if response.assignment else None,
        )
        return summary
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
