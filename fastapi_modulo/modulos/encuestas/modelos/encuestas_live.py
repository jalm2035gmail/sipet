"""
Servicio de sesiones en vivo para encuestas interactivas.

Permite al presentador controlar en tiempo real qué contenido se muestra
al público. El estado de la sesión se almacena en settings_json de
SurveyInstance para evitar migraciones de base de datos.
"""
from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from fastapi_modulo.modulos.encuestas.modelos.encuestas_models import (
    SurveyInstance,
    SurveyQuestion,
    SurveyResponse,
    SurveyResponseItem,
)
from fastapi_modulo.modulos.encuestas.modelos.encuestas_store import get_db


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _get_instance(db: Session, instance_id: int, tenant_id: str) -> Optional[SurveyInstance]:
    return (
        db.query(SurveyInstance)
        .filter(
            SurveyInstance.id == instance_id,
            SurveyInstance.tenant_id == tenant_id,
        )
        .first()
    )


def _flat_question_ids(instance: SurveyInstance) -> List[int]:
    """Devuelve los IDs de preguntas en orden (sección → pregunta)."""
    ids: List[int] = []
    for section in sorted(instance.sections or [], key=lambda s: s.orden or 0):
        for q in sorted(section.questions or [], key=lambda q: q.orden or 0):
            ids.append(q.id)
    return ids


def _question_dict(q: SurveyQuestion) -> Dict[str, Any]:
    return {
        "id": q.id,
        "titulo": q.titulo,
        "descripcion": q.descripcion,
        "question_type": q.question_type,
        "is_required": q.is_required,
        "orden": q.orden,
        "options": [
            {
                "id": opt.id,
                "label": opt.label,
                "value": opt.value,
                "orden": opt.orden,
            }
            for opt in sorted(q.options or [], key=lambda o: o.orden or 0)
        ],
    }


def _first_question_id_in_page(page: Dict[str, Any]) -> Optional[int]:
    for section in page.get("layout_sections") or []:
        if str(section.get("type") or "") != "question":
            continue
        question_ids = section.get("question_ids") or []
        if isinstance(question_ids, list):
            for question_id in question_ids:
                try:
                    return int(question_id)
                except (TypeError, ValueError):
                    continue
        question_id = section.get("question_id")
        try:
            return int(question_id)
        except (TypeError, ValueError):
            continue
    for block in page.get("blocks") or []:
        if str(block.get("type") or "") != "question":
            continue
        question_id = block.get("question_id")
        try:
            return int(question_id)
        except (TypeError, ValueError):
            continue
    return None


def _question_ids_in_page(page: Dict[str, Any]) -> List[int]:
    ids: List[int] = []
    for section in page.get("layout_sections") or []:
        if str(section.get("type") or "") != "question":
            continue
        for question_id in section.get("question_ids") or []:
            try:
                ids.append(int(question_id))
            except (TypeError, ValueError):
                continue
        if not ids and section.get("question_id") is not None:
            try:
                ids.append(int(section.get("question_id")))
            except (TypeError, ValueError):
                pass
    for block in page.get("blocks") or []:
        if str(block.get("type") or "") != "question":
            continue
        try:
            ids.append(int(block.get("question_id")))
        except (TypeError, ValueError):
            continue
    # dedupe preserving order
    return list(dict.fromkeys(ids))


def _presentation_pages(instance: SurveyInstance) -> List[Dict[str, Any]]:
    rules = instance.publication_rules_json or {}
    pages = rules.get("presentation_pages") or []
    if not isinstance(pages, list):
        return []
    sanitized: List[Dict[str, Any]] = []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        try:
            section_count = int(page.get("section_count") or 1)
        except (TypeError, ValueError):
            section_count = 1
        if section_count not in {1, 2, 4}:
            section_count = 1
        blocks = []
        layout_sections = []
        for block in page.get("blocks") or []:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "html")
            item: Dict[str, Any] = {
                "id": block.get("id") or f"block_{index}_{len(blocks)}",
                "type": block_type,
                "width": "half" if str(block.get("width") or "") == "half" else "full",
            }
            if block_type == "question":
                try:
                    item["question_id"] = int(block.get("question_id"))
                except (TypeError, ValueError):
                    item["question_id"] = None
            elif block_type == "image":
                item["image_url"] = str(block.get("image_url") or "")
                item["image_alt"] = str(block.get("image_alt") or "")
                item["image_fit"] = "contain" if str(block.get("image_fit") or "").strip().lower() == "contain" else "cover"
            else:
                item["html"] = str(block.get("html") or "")
                item["css"] = str(block.get("css") or "")
                item["js_input"] = str(block.get("js_input") or "")
                item["js_highlight"] = str(block.get("js_highlight") or "")
                item["js_output"] = str(block.get("js_output") or "")
                item["js_input_effect"] = str(block.get("js_input_effect") or "none")
                item["js_highlight_effect"] = str(block.get("js_highlight_effect") or "none")
                item["js_output_effect"] = str(block.get("js_output_effect") or "none")
            blocks.append(item)
        for section in page.get("layout_sections") or []:
            if not isinstance(section, dict):
                continue
            section_type = str(section.get("type") or "html")
            section_item: Dict[str, Any] = {
                "id": section.get("id") or f"section_{index}_{len(layout_sections)}",
                "type": section_type,
            }
            if section_type == "question":
                question_ids: List[int] = []
                raw_question_ids = section.get("question_ids") or []
                if isinstance(raw_question_ids, list):
                    for raw_question_id in raw_question_ids:
                        try:
                            question_ids.append(int(raw_question_id))
                        except (TypeError, ValueError):
                            continue
                try:
                    question_id = int(section.get("question_id"))
                except (TypeError, ValueError):
                    question_id = None
                if question_id is not None and question_id not in question_ids:
                    question_ids.append(question_id)
                section_item["question_ids"] = question_ids
                section_item["question_id"] = question_ids[0] if question_ids else None
            elif section_type == "image":
                section_item["image_url"] = str(section.get("image_url") or "")
                section_item["image_alt"] = str(section.get("image_alt") or "")
                section_item["image_fit"] = "contain" if str(section.get("image_fit") or "").strip().lower() == "contain" else "cover"
            else:
                section_item["html"] = str(section.get("html") or "")
                section_item["css"] = str(section.get("css") or "")
                section_item["js_input"] = str(section.get("js_input") or "")
                section_item["js_highlight"] = str(section.get("js_highlight") or "")
                section_item["js_output"] = str(section.get("js_output") or "")
                section_item["js_input_effect"] = str(section.get("js_input_effect") or "none")
                section_item["js_highlight_effect"] = str(section.get("js_highlight_effect") or "none")
                section_item["js_output_effect"] = str(section.get("js_output_effect") or "none")
            layout_sections.append(section_item)
        sanitized.append({
            "id": page.get("id") or f"page_{index}",
            "title": str(page.get("title") or page.get("titulo") or f"Página {index + 1}"),
            "description": str(page.get("description") or page.get("descripcion") or ""),
            "bg_color": str(page.get("bg_color") or "#ffffff"),
            "bg_image_url": str(page.get("bg_image_url") or ""),
            "section_count": section_count,
            "layout_sections": layout_sections,
            "footer_text": str(page.get("footer_text") or ""),
            "footer_color": str(page.get("footer_color") or "#0f172a"),
            "blocks": blocks,
        })
    return sanitized


def _live_state(instance: SurveyInstance) -> Dict[str, Any]:
    s = instance.settings_json or {}
    live_pages = s.get("live_pages") or []
    if not live_pages:
        live_pages = _presentation_pages(instance)
    live_mode = s.get("live_mode", "questions")
    if live_pages and live_mode != "presentation":
        live_mode = "presentation"
    return {
        "live_status": s.get("live_status", "idle"),
        "live_mode": live_mode,
        "live_current_question_id": s.get("live_current_question_id"),
        "live_current_question_index": s.get("live_current_question_index", 0),
        "live_current_page_index": s.get("live_current_page_index", 0),
        "live_show_results": s.get("live_show_results", True),
        "live_started_at": s.get("live_started_at"),
        "live_ended_at": s.get("live_ended_at"),
        "live_question_ids": s.get("live_question_ids", []),
        "live_pages": live_pages,
    }


def _has_presenter_token(instance: SurveyInstance, token: str) -> bool:
    stored = (instance.settings_json or {}).get("live_presenter_token") or ""
    return secrets.compare_digest(str(stored), str(token))


def _set_live_settings(instance: SurveyInstance, updates: Dict[str, Any]) -> None:
    current = dict(instance.settings_json or {})
    current.update(updates)
    instance.settings_json = current


# ---------------------------------------------------------------------------
# Operaciones públicas del servicio
# ---------------------------------------------------------------------------


def start_live_session(instance_id: int, tenant_id: str) -> Dict[str, Any]:
    """
    Inicia una sesión en vivo para la instancia. Genera un presenter_token.
    Retorna el estado completo incluyendo el presenter_token (solo en esta llamada).
    """
    db = get_db()
    try:
        instance = _get_instance(db, instance_id, tenant_id)
        if instance is None:
            raise ValueError("Encuesta no encontrada.")
        if instance.status == "draft":
            raise ValueError("La encuesta debe estar publicada para iniciar una sesión en vivo.")

        presentation_pages = _presentation_pages(instance)
        response_mode = str((instance.publication_rules_json or {}).get("response_mode") or "standard").strip().lower()
        is_presentation_mode = len(presentation_pages) > 0 and (
            response_mode == "presentation" or response_mode == "standard"
        )

        question_ids = _flat_question_ids(instance)
        if not is_presentation_mode and not question_ids:
            raise ValueError("La encuesta no tiene preguntas configuradas.")

        presenter_token = secrets.token_urlsafe(32)
        first_page = presentation_pages[0] if presentation_pages else {}
        first_question_id = _first_question_id_in_page(first_page) if first_page else (question_ids[0] if question_ids else None)
        first_question_index = question_ids.index(first_question_id) if first_question_id in question_ids else 0

        _set_live_settings(instance, {
            "live_status": "running",
            "live_mode": "presentation" if is_presentation_mode else "questions",
            "live_current_question_id": first_question_id,
            "live_current_question_index": first_question_index,
            "live_current_page_index": 0,
            "live_show_results": True,
            "live_started_at": _now_iso(),
            "live_ended_at": None,
            "live_question_ids": question_ids,
            "live_pages": presentation_pages if is_presentation_mode else [],
            "live_presenter_token": presenter_token,
        })
        db.commit()
        db.refresh(instance)

        state = _live_state(instance)
        state["presenter_token"] = presenter_token
        state["instance_id"] = instance_id
        state["total_questions"] = len(question_ids)
        state["total_pages"] = len(presentation_pages)
        return state
    finally:
        db.close()


def stop_live_session(instance_id: int, tenant_id: str) -> Dict[str, Any]:
    """Finaliza la sesión en vivo."""
    db = get_db()
    try:
        instance = _get_instance(db, instance_id, tenant_id)
        if instance is None:
            raise ValueError("Encuesta no encontrada.")

        _set_live_settings(instance, {
            "live_status": "ended",
            "live_mode": (instance.settings_json or {}).get("live_mode", "questions"),
            "live_current_question_id": None,
            "live_ended_at": _now_iso(),
            "live_presenter_token": "",
        })
        db.commit()
        db.refresh(instance)
        return _live_state(instance)
    finally:
        db.close()


def set_live_question(
    instance_id: int,
    tenant_id: str,
    question_id: int,
    presenter_token: str,
    show_results: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Cambia la pregunta activa en la sesión en vivo.
    Requiere presenter_token válido.
    """
    db = get_db()
    try:
        instance = _get_instance(db, instance_id, tenant_id)
        if instance is None:
            raise ValueError("Encuesta no encontrada.")
        if not _has_presenter_token(instance, presenter_token):
            raise PermissionError("Token de presentador inválido.")

        settings = instance.settings_json or {}
        if settings.get("live_status") != "running":
            raise ValueError("La sesión en vivo no está activa.")

        question_ids: List[int] = settings.get("live_question_ids") or []
        if question_id not in question_ids:
            raise ValueError("La pregunta no pertenece a esta encuesta.")

        idx = question_ids.index(question_id)
        updates: Dict[str, Any] = {
            "live_current_question_id": question_id,
            "live_current_question_index": idx,
        }
        if show_results is not None:
            updates["live_show_results"] = show_results

        _set_live_settings(instance, updates)
        db.commit()
        db.refresh(instance)

        state = _live_state(instance)
        state["instance_id"] = instance_id
        state["total_questions"] = len(question_ids)
        return state
    finally:
        db.close()


def set_live_page(
    instance_id: int,
    tenant_id: str,
    page_index: int,
    presenter_token: str,
    show_results: Optional[bool] = None,
) -> Dict[str, Any]:
    db = get_db()
    try:
        instance = _get_instance(db, instance_id, tenant_id)
        if instance is None:
            raise ValueError("Encuesta no encontrada.")
        if not _has_presenter_token(instance, presenter_token):
            raise PermissionError("Token de presentador inválido.")

        settings = instance.settings_json or {}
        if settings.get("live_status") != "running":
            raise ValueError("La sesión en vivo no está activa.")
        if settings.get("live_mode") != "presentation":
            raise ValueError("La sesión no está en modo presentación.")

        pages: List[Dict[str, Any]] = settings.get("live_pages") or []
        if page_index < 0 or page_index >= len(pages):
            raise ValueError("La página no existe en esta presentación.")

        question_ids: List[int] = settings.get("live_question_ids") or []
        question_id = _first_question_id_in_page(pages[page_index])
        question_index = question_ids.index(question_id) if question_id in question_ids else 0
        updates: Dict[str, Any] = {
            "live_current_page_index": page_index,
            "live_current_question_id": question_id,
            "live_current_question_index": question_index,
        }
        if show_results is not None:
            updates["live_show_results"] = show_results

        _set_live_settings(instance, updates)
        db.commit()
        db.refresh(instance)

        state = _live_state(instance)
        state["instance_id"] = instance_id
        state["total_questions"] = len(question_ids)
        state["total_pages"] = len(pages)
        return state
    finally:
        db.close()


def get_live_status_presenter(
    instance_id: int,
    tenant_id: str,
) -> Dict[str, Any]:
    """
    Retorna el estado completo de la sesión en vivo para el presentador,
    incluyendo resultados de la pregunta actual.
    """
    db = get_db()
    try:
        instance = (
            db.query(SurveyInstance)
            .options(joinedload(SurveyInstance.sections))
            .filter(
                SurveyInstance.id == instance_id,
                SurveyInstance.tenant_id == tenant_id,
            )
            .first()
        )
        if instance is None:
            raise ValueError("Encuesta no encontrada.")

        state = _live_state(instance)
        state["instance_id"] = instance_id
        state["instance_nombre"] = instance.nombre

        question_ids: List[int] = state["live_question_ids"]
        state["total_questions"] = len(question_ids)

        # Build ordered questions list
        questions_map: Dict[int, SurveyQuestion] = {}
        for section in instance.sections or []:
            for q in section.questions or []:
                questions_map[q.id] = q

        state["questions"] = [
            _question_dict(questions_map[qid])
            for qid in question_ids
            if qid in questions_map
        ]
        state["pages"] = state.get("live_pages") or []
        current_page_index = state.get("live_current_page_index", 0)
        state["current_page"] = state["pages"][current_page_index] if 0 <= current_page_index < len(state["pages"]) else None

        # Results for current question
        current_qid = state.get("live_current_question_id")
        state["current_results"] = _get_question_results(db, instance_id, tenant_id, current_qid) if current_qid else {}
        state["current_page_results"] = {}
        if state["current_page"]:
            for question_id in _question_ids_in_page(state["current_page"]):
                state["current_page_results"][str(question_id)] = _get_question_results(db, instance_id, tenant_id, question_id)
        state["presentation_mode"] = state.get("live_mode") == "presentation"
        state["total_pages"] = len(state["pages"])
        return state
    finally:
        db.close()


def get_live_status_audience(
    instance_id: int,
    tenant_id: str,
    public_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retorna el estado de la sesión en vivo para la audiencia (sin datos privados).
    Se usa para el polling desde la página de respuesta.
    """
    db = get_db()
    try:
        instance = (
            db.query(SurveyInstance)
            .options(joinedload(SurveyInstance.sections))
            .filter(
                SurveyInstance.id == instance_id,
                SurveyInstance.tenant_id == tenant_id,
            )
            .first()
        )
        if instance is None:
            raise ValueError("Encuesta no encontrada.")

        # Validate public token if instance requires it
        if public_token:
            if instance.public_link_token != public_token:
                raise PermissionError("Token público inválido.")

        settings = instance.settings_json or {}
        live_status = settings.get("live_status", "idle")
        current_qid = settings.get("live_current_question_id")
        show_results = settings.get("live_show_results", True)

        payload: Dict[str, Any] = {
            "instance_id": instance_id,
            "live_status": live_status,
            "live_mode": settings.get("live_mode", "questions"),
            "live_current_question_id": current_qid,
            "live_current_question_index": settings.get("live_current_question_index", 0),
            "live_current_page_index": settings.get("live_current_page_index", 0),
            "total_questions": len(settings.get("live_question_ids", [])),
            "total_pages": len(settings.get("live_pages", [])),
            "pages": settings.get("live_pages", []),
            "show_results": show_results,
            "current_question": None,
            "current_page": None,
            "current_results": None,
        }

        pages = settings.get("live_pages") or []
        current_page_index = settings.get("live_current_page_index", 0)
        if 0 <= current_page_index < len(pages):
            payload["current_page"] = pages[current_page_index]

        if current_qid:
            # Find the question object
            for section in instance.sections or []:
                for q in section.questions or []:
                    if q.id == current_qid:
                        payload["current_question"] = _question_dict(q)
                        break

            if show_results:
                payload["current_results"] = _get_question_results(db, instance_id, tenant_id, current_qid)

        payload["current_page_results"] = {}
        if payload["current_page"]:
          for question_id in _question_ids_in_page(payload["current_page"]):
              payload["current_page_results"][str(question_id)] = _get_question_results(db, instance_id, tenant_id, question_id)

        payload["presentation_mode"] = settings.get("live_mode") == "presentation"

        return payload
    finally:
        db.close()


def _get_question_results(
    db: Session,
    instance_id: int,
    tenant_id: str,
    question_id: int,
) -> Dict[str, Any]:
    """Agrega las respuestas para una pregunta específica."""
    items = (
        db.query(SurveyResponseItem)
        .join(SurveyResponse, SurveyResponseItem.response_id == SurveyResponse.id)
        .filter(
            SurveyResponse.instance_id == instance_id,
            SurveyResponse.tenant_id == tenant_id,
            SurveyResponse.status == "submitted",
            SurveyResponseItem.question_id == question_id,
        )
        .all()
    )

    total = len(set(item.response_id for item in items))
    counts: Dict[str, int] = {}
    texts: List[str] = []

    for item in items:
        val = str(item.answer_value or "").strip()
        text = str(item.answer_text or "").strip()
        if val:
            counts[val] = counts.get(val, 0) + 1
        if text and len(texts) < 20:
            texts.append(text)

    return {
        "question_id": question_id,
        "total_responses": total,
        "counts": counts,
        "texts": texts,
    }
