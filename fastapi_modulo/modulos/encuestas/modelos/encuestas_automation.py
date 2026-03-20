from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import redis as redis_lib
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.encuestas.modelos.encuestas_models import (
    SurveyAssignment,
    SurveyDispatchLog,
    SurveyEvaluation360,
    SurveyInstance,
)
from fastapi_modulo.modulos.encuestas.modelos.encuestas_store import (
    _automation_settings,
    _background_runtime_status,
    _dt,
    _is_360_payload,
    _load_capacitacion_enrollments,
    _load_crm_campaign_contacts,
    _load_crm_contacts,
    _load_user_directory,
    _notification_timestamp,
    _refresh_instance_lifecycle,
    get_db,
    list_assignments,
)

_NOTIFICATION_SCHEMA_READY = False


def _ensure_notification_schema(db: Session) -> None:
    global _NOTIFICATION_SCHEMA_READY
    if _NOTIFICATION_SCHEMA_READY:
        return
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS conversation_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_username TEXT NOT NULL,
                to_usernames TEXT NOT NULL DEFAULT '[]',
                message_text TEXT NOT NULL DEFAULT '',
                scope TEXT NOT NULL DEFAULT 'conversation',
                conversation_id TEXT NOT NULL DEFAULT '',
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
    )
    _NOTIFICATION_SCHEMA_READY = True
    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_cn_to_read
            ON conversation_notifications(to_usernames, is_read, created_at)
            """
        )
    )


def _record_dispatch_log(
    db: Session,
    instance: SurveyInstance,
    dispatch_type: str,
    dispatch_status: str,
    assignment: Optional[SurveyAssignment] = None,
    message_text: str = "",
    metadata_json: Optional[Dict[str, Any]] = None,
) -> None:
    db.add(
        SurveyDispatchLog(
            tenant_id=instance.tenant_id,
            instance_id=instance.id,
            assignment_id=assignment.id if assignment else None,
            dispatch_type=dispatch_type,
            dispatch_status=dispatch_status,
            channel=str((assignment.channel if assignment else "system") or "system"),
            recipient_key=assignment.assignee_key if assignment else None,
            recipient_name_snapshot=assignment.assignee_name_snapshot if assignment else None,
            message_text=message_text,
            metadata_json=metadata_json or {},
            dispatched_at=datetime.utcnow(),
        )
    )


def _survey_backendhook_settings(instance: SurveyInstance) -> Dict[str, Any]:
    settings = instance.settings_json or {}
    rules = instance.publication_rules_json or {}
    backendhook_url = str(rules.get("backendhook_url") or settings.get("backendhook_url") or "").strip()
    events = rules.get("backendhook_events") or settings.get("backendhook_events") or ["response_submitted"]
    if not isinstance(events, list):
        events = [str(events)]
    timeout = float(rules.get("backendhook_timeout_seconds") or settings.get("backendhook_timeout_seconds") or 5)
    return {
        "enabled": bool(backendhook_url),
        "url": backendhook_url,
        "events": [str(event).strip() for event in events if str(event).strip()],
        "timeout_seconds": max(1.0, min(timeout, 15.0)),
    }


def _dispatch_survey_backendhook(
    db: Session,
    instance: SurveyInstance,
    event_name: str,
    payload: Dict[str, Any],
    assignment: Optional[SurveyAssignment] = None,
) -> None:
    config = _survey_backendhook_settings(instance)
    if not config["enabled"] or event_name not in config["events"]:
        return
    metadata = {
        "event": event_name,
        "backendhook_url": config["url"],
    }
    try:
        with httpx.Client(timeout=config["timeout_seconds"], follow_redirects=True) as client:
            response = client.post(
                config["url"],
                json={
                    "event": event_name,
                    "instance": {
                        "id": instance.id,
                        "nombre": instance.nombre,
                        "tenant_id": instance.tenant_id,
                    },
                    "payload": payload,
                    "sent_at": _dt(datetime.utcnow()),
                },
            )
        metadata["status_code"] = response.status_code
        metadata["response_text"] = (response.text or "")[:500]
        _record_dispatch_log(
            db,
            instance,
            dispatch_type=f"backendhook:{event_name}",
            dispatch_status="sent" if response.is_success else "failed",
            assignment=assignment,
            message_text=f"backendhook {event_name} enviado a {config['url']}.",
            metadata_json=metadata,
        )
        db.commit()
    except Exception as exc:
        metadata["error"] = str(exc)
        _record_dispatch_log(
            db,
            instance,
            dispatch_type=f"backendhook:{event_name}",
            dispatch_status="error",
            assignment=assignment,
            message_text=f"backendhook {event_name} falló para {config['url']}.",
            metadata_json=metadata,
        )
        db.commit()


def dispatch_backendhook_event(
    tenant_id: str,
    instance_id: int,
    event_name: str,
    payload: Dict[str, Any],
    assignment_id: Optional[int] = None,
) -> Dict[str, Any]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_models import SurveyInstance

    db = get_db()
    try:
        instance = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not instance:
            raise ValueError("Encuesta no encontrada.")
        assignment = None
        if assignment_id is not None:
            assignment = (
                db.query(SurveyAssignment)
                .filter(
                    SurveyAssignment.id == assignment_id,
                    SurveyAssignment.instance_id == instance_id,
                    SurveyAssignment.tenant_id == tenant_id,
                )
                .first()
            )
        _dispatch_survey_backendhook(db, instance, event_name, payload, assignment=assignment)
        return {
            "queued": False,
            "processed": True,
            "event": event_name,
            "instance_id": instance_id,
        }
    finally:
        db.close()


def _enqueue_celery_task(task_name: str, kwargs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    runtime = _background_runtime_status()
    if not runtime["configured"]:
        return None
    try:
        from fastapi_modulo.modulos.encuestas.modelos.encuestas_tasks import get_celery_app

        task = get_celery_app().send_task(task_name, kwargs=kwargs, queue=runtime["queue_name"])
        return {
            "queued": True,
            "task_id": task.id,
            "queue_name": runtime["queue_name"],
            "engine": "celery",
        }
    except Exception:
        return None


def queue_automation_job(tenant_id: str, instance_id: Optional[int] = None) -> Dict[str, Any]:
    queued = _enqueue_celery_task(
        "encuestas.run_automation_jobs",
        {"tenant_id": tenant_id, "instance_id": instance_id},
    )
    if queued:
        return {
            **queued,
            "processed": False,
            "summary": None,
        }
    return {
        "queued": False,
        "processed": True,
        "engine": "manual_scheduler",
        "summary": run_automation_jobs(tenant_id, instance_id=instance_id),
    }


def queue_backendhook_event(
    tenant_id: str,
    instance_id: int,
    event_name: str,
    payload: Dict[str, Any],
    assignment_id: Optional[int] = None,
) -> Dict[str, Any]:
    queued = _enqueue_celery_task(
        "encuestas.dispatch_backendhook",
        {
            "tenant_id": tenant_id,
            "instance_id": instance_id,
            "event_name": event_name,
            "payload": payload,
            "assignment_id": assignment_id,
        },
    )
    if queued:
        return {
            **queued,
            "processed": False,
            "event": event_name,
            "instance_id": instance_id,
        }
    return dispatch_backendhook_event(
        tenant_id=tenant_id,
        instance_id=instance_id,
        event_name=event_name,
        payload=payload,
        assignment_id=assignment_id,
    )


def _send_assignment_notifications(
    db: Session,
    instance: SurveyInstance,
    assignments: List[SurveyAssignment],
    notification_kind: str = "invitation",
) -> int:
    internal_assignments = [
        assignment
        for assignment in assignments
        if str(assignment.channel or "").strip().lower() == "internal" and assignment.assignee_key
    ]
    if not internal_assignments:
        return 0
    _ensure_notification_schema(db)
    sent = 0
    ts = _notification_timestamp()
    for assignment in internal_assignments:
        if assignment.status == "completed":
            continue
        message = (
            f"Aviso de cierre: la encuesta '{instance.nombre}' está por cerrar. Responde cuanto antes."
            if notification_kind == "closing_soon"
            else
            f"Recordatorio: tienes pendiente responder la encuesta '{instance.nombre}'."
            if notification_kind == "reminder"
            else f"Tienes una nueva invitacion para responder la encuesta '{instance.nombre}'."
        )
        db.execute(
            text(
                """
                INSERT INTO conversation_notifications
                (from_username, to_usernames, message_text, scope, conversation_id, is_read, created_at)
                VALUES (:from_u, :to_u, :msg, :scope, :conv, 0, :ts)
                """
            ),
            {
                "from_u": str(instance.created_by or "sistema").strip().lower(),
                "to_u": f"[\"{str(assignment.assignee_key).strip().lower()}\"]",
                "msg": message,
                "scope": "survey",
                "conv": f"survey:{instance.id}",
                "ts": ts,
            },
        )
        now = datetime.utcnow()
        if not assignment.first_sent_at:
            assignment.first_sent_at = now
        assignment.last_sent_at = now
        _record_dispatch_log(
            db,
            instance,
            dispatch_type=notification_kind,
            dispatch_status="sent",
            assignment=assignment,
            message_text=message,
            metadata_json={
                "scope": "survey",
                "conversation_id": f"survey:{instance.id}",
            },
        )
        sent += 1
    return sent


def _should_send_closing_notice(instance: SurveyInstance, now: datetime) -> bool:
    if not instance.schedule_end_at:
        return False
    automation = _automation_settings(instance)
    hours = max(1, int(automation["closing_notice_hours"]))
    remaining_seconds = (instance.schedule_end_at - now).total_seconds()
    if remaining_seconds <= 0 or remaining_seconds > hours * 3600:
        return False
    return True


def _last_dispatch_for_type(
    db: Session,
    instance_id: int,
    tenant_id: str,
    dispatch_type: str,
) -> Optional[SurveyDispatchLog]:
    return (
        db.query(SurveyDispatchLog)
        .filter(
            SurveyDispatchLog.instance_id == instance_id,
            SurveyDispatchLog.tenant_id == tenant_id,
            SurveyDispatchLog.dispatch_type == dispatch_type,
        )
        .order_by(SurveyDispatchLog.dispatched_at.desc(), SurveyDispatchLog.id.desc())
        .first()
    )


def run_automation_jobs(tenant_id: str, instance_id: Optional[int] = None) -> Dict[str, Any]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_models import SurveyInstance

    db = get_db()
    try:
        now = datetime.utcnow()
        background = _background_runtime_status()
        query = db.query(SurveyInstance).filter(SurveyInstance.tenant_id == tenant_id)
        if instance_id is not None:
            query = query.filter(SurveyInstance.id == instance_id)
        instances = query.all()
        summary = {
            "processed_instances": 0,
            "invitations_sent": 0,
            "reminders_sent": 0,
            "closing_notices_sent": 0,
            "auto_closed": 0,
            "engine": background["engine"],
            "future": {
                "celery_ready": background["celery_ready"],
                "redis_ready": background["redis_ready"],
                "redis_error": background["redis_error"],
                "broker_configured": background["configured"],
                "queue_name": background["queue_name"],
            },
        }
        for instance in instances:
            automation = _automation_settings(instance)
            if not automation["enabled"]:
                continue
            summary["processed_instances"] += 1
            if instance.status in {"published", "scheduled"} and instance.schedule_end_at and instance.schedule_end_at <= now:
                if instance.status != "closed":
                    instance.status = "closed"
                    instance.closed_at = instance.closed_at or now
                    instance.updated_at = now
                    _record_dispatch_log(
                        db,
                        instance,
                        dispatch_type="auto_close",
                        dispatch_status="applied",
                        message_text=f"Cierre automático ejecutado para la encuesta '{instance.nombre}'.",
                        metadata_json={"schedule_end_at": _dt(instance.schedule_end_at)},
                    )
                    summary["auto_closed"] += 1
                continue
            if instance.status not in {"published", "scheduled"}:
                continue
            assignments = list(instance.assignments or [])
            pending_assignments = [assignment for assignment in assignments if assignment.status != "completed"]
            if pending_assignments and not any(assignment.first_sent_at for assignment in pending_assignments):
                summary["invitations_sent"] += _send_assignment_notifications(
                    db,
                    instance,
                    pending_assignments,
                    notification_kind="invitation",
                )
            reminder_due = []
            for assignment in pending_assignments:
                if assignment.first_sent_at and assignment.status in {"pending", "in_progress"}:
                    last_touch = assignment.last_sent_at or assignment.first_sent_at
                    elapsed_hours = (now - last_touch).total_seconds() / 3600 if last_touch else 0
                    if elapsed_hours >= max(1, int(automation["reminder_interval_hours"])):
                        reminder_due.append(assignment)
            if reminder_due:
                summary["reminders_sent"] += _send_assignment_notifications(
                    db,
                    instance,
                    reminder_due,
                    notification_kind="reminder",
                )
            if pending_assignments and _should_send_closing_notice(instance, now):
                last_notice = _last_dispatch_for_type(db, instance.id, tenant_id, "closing_soon")
                notice_recent = False
                if last_notice and last_notice.dispatched_at:
                    notice_recent = (now - last_notice.dispatched_at).total_seconds() < max(1, int(automation["closing_notice_hours"])) * 3600
                if not notice_recent:
                    summary["closing_notices_sent"] += _send_assignment_notifications(
                        db,
                        instance,
                        pending_assignments,
                        notification_kind="closing_soon",
                    )
        db.commit()
        return summary
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def _sync_evaluations_360(
    db: Session,
    instance: SurveyInstance,
    assignments: List[SurveyAssignment],
    users_by_id: Dict[str, Dict[str, Any]],
) -> None:
    if not _is_360_payload(instance.template.survey_type if instance.template else "", instance.external_entity_type or ""):
        return
    db.query(SurveyEvaluation360).filter(
        SurveyEvaluation360.instance_id == instance.id,
        SurveyEvaluation360.tenant_id == instance.tenant_id,
    ).delete(synchronize_session=False)

    assignments_by_key = {str(item.assignee_key): item for item in assignments if item.assignee_key}
    subordinates_by_manager: Dict[str, List[Dict[str, Any]]] = {}
    for user in users_by_id.values():
        manager_key = str(user.get("jefe_inmediato_id") or "").strip()
        if manager_key:
            subordinates_by_manager.setdefault(manager_key, []).append(user)

    links: set[tuple[str, str, str]] = set()

    def add_link(evaluator_key: str, evaluatee_key: str, relationship_type: str) -> None:
        evaluator = users_by_id.get(evaluator_key)
        evaluatee = users_by_id.get(evaluatee_key)
        assignment = assignments_by_key.get(evaluator_key)
        if not evaluator or not evaluatee or not assignment:
            return
        link_key = (evaluatee_key, evaluator_key, relationship_type)
        if link_key in links:
            return
        links.add(link_key)
        db.add(
            SurveyEvaluation360(
                tenant_id=instance.tenant_id,
                instance_id=instance.id,
                assignment_id=assignment.id,
                evaluatee_key=evaluatee_key,
                evaluator_key=evaluator_key,
                relationship_type=relationship_type,
                evaluatee_name_snapshot=evaluatee.get("nombre"),
                evaluatee_role_snapshot=evaluatee.get("role"),
                evaluatee_area_snapshot=evaluatee.get("departamento"),
                evaluatee_position_snapshot=evaluatee.get("puesto"),
                evaluatee_company_snapshot=evaluatee.get("empresa"),
                evaluator_name_snapshot=evaluator.get("nombre"),
                evaluator_role_snapshot=evaluator.get("role"),
                evaluator_area_snapshot=evaluator.get("departamento"),
                evaluator_position_snapshot=evaluator.get("puesto"),
                evaluator_company_snapshot=evaluator.get("empresa"),
                status="pending",
                source_app="empleados",
                external_entity_type="hierarchy_360",
                external_entity_id=f"{instance.id}:{relationship_type}:{evaluatee_key}:{evaluator_key}",
            )
        )

    for evaluator_key in assignments_by_key:
        add_link(evaluator_key, evaluator_key, "self")
        manager_key = str((users_by_id.get(evaluator_key) or {}).get("jefe_inmediato_id") or "").strip()
        if manager_key:
            add_link(evaluator_key, manager_key, "subordinate")
        for subordinate in subordinates_by_manager.get(evaluator_key, []):
            subordinate_key = str(subordinate.get("user_id") or "").strip()
            if subordinate_key:
                add_link(evaluator_key, subordinate_key, "manager")


def sync_assignments(instance_id: int, tenant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_models import (
        SurveyAssignment,
        SurveyAudienceGroup,
        SurveyAudienceGroupMember,
        SurveyInstance,
    )
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_store import _group_members_payload

    db = get_db()
    try:
        instance = (
            db.query(SurveyInstance)
            .filter(SurveyInstance.id == instance_id, SurveyInstance.tenant_id == tenant_id)
            .first()
        )
        if not instance:
            raise ValueError("Encuesta no encontrada.")
        user_directory = _load_user_directory()
        crm_contacts = _load_crm_contacts()
        users_by_id = {str(item["user_id"]): item for item in user_directory}
        crm_contacts_by_id = {str(item["id"]): item for item in crm_contacts}
        users_by_role: Dict[str, List[Dict[str, Any]]] = {}
        users_by_department: Dict[str, List[Dict[str, Any]]] = {}
        users_by_position: Dict[str, List[Dict[str, Any]]] = {}
        for item in user_directory:
            if item["role"]:
                users_by_role.setdefault(item["role"].lower(), []).append(item)
            if item["departamento"]:
                users_by_department.setdefault(item["departamento"].lower(), []).append(item)
            if item["puesto"]:
                users_by_position.setdefault(item["puesto"].lower(), []).append(item)

        due_at = payload.get("due_at")
        due_at_value = due_at if isinstance(due_at, datetime) else None
        rules = payload.get("assignment_rules") or {}
        entries = list(payload.get("assignments") or [])
        if (
            str(instance.source_app or "").strip().lower() == "capacitacion"
            and str(instance.external_entity_type or "").strip().lower() in {"curso", "course"}
            and str(instance.external_entity_id or "").strip().isdigit()
            and not entries
        ):
            enrollments = _load_capacitacion_enrollments(int(str(instance.external_entity_id)))
            enrolled_keys = [str(item.get("colaborador_key") or "").strip() for item in enrollments if item.get("colaborador_key")]
            if enrolled_keys:
                entries.append({"type": "user", "values": enrolled_keys})
        if (
            str(instance.source_app or "").strip().lower() == "crm"
            and str(instance.external_entity_type or "").strip().lower() in {"campania", "campaign", "crm_campaign"}
            and str(instance.external_entity_id or "").strip().isdigit()
            and not entries
        ):
            contacts = _load_crm_campaign_contacts(int(str(instance.external_entity_id)))
            contact_ids = [str(item["id"]) for item in contacts if item.get("id")]
            if contact_ids:
                entries.append({"type": "crm_contact", "values": contact_ids})
        if (
            str(instance.source_app or "").strip().lower() == "crm"
            and str(instance.external_entity_type or "").strip().lower() in {"contacto", "contact", "crm_contact"}
            and str(instance.external_entity_id or "").strip()
            and not entries
        ):
            entries.append({"type": "crm_contact", "values": [str(instance.external_entity_id)]})
        db.query(SurveyAssignment).filter(
            SurveyAssignment.instance_id == instance_id,
            SurveyAssignment.tenant_id == tenant_id,
        ).delete(synchronize_session=False)

        manual_groups = rules.get("manual_groups") or []
        groups_created: List[Dict[str, Any]] = []
        for group in manual_groups:
            group_name = str(group.get("name") or "").strip()
            members = _group_members_payload(group.get("members") or [])
            if not group_name or not members:
                continue
            audience_group = SurveyAudienceGroup(
                tenant_id=tenant_id,
                nombre=group_name,
                descripcion=str(group.get("description") or "").strip() or "Grupo manual de encuesta",
                source_app="encuestas",
                external_entity_type="manual_group",
                external_entity_id=f"{instance_id}:{group_name.lower().replace(' ', '-')}",
                filters_json={"source": "manual_group", "instance_id": instance_id},
                is_dynamic=False,
                created_by=instance.created_by,
            )
            db.add(audience_group)
            db.flush()
            groups_created.append({"group_id": audience_group.id, "members": members})
            for member in members:
                db.add(
                    SurveyAudienceGroupMember(
                        tenant_id=tenant_id,
                        group_id=audience_group.id,
                        member_key=str(member["user_id"]),
                        member_name_snapshot=member["nombre"],
                        member_role_snapshot=member["role"],
                        member_area_snapshot=member["departamento"],
                        member_position_snapshot=member["puesto"],
                        member_company_snapshot=member["empresa"],
                        source_app="encuestas",
                        external_entity_type="manual_group",
                        external_entity_id=str(audience_group.id),
                    )
                )

        materialized: Dict[str, Dict[str, Any]] = {}

        def add_candidate(
            candidate_payload: Dict[str, Any],
            assignment_type: str,
            audience_group_id: Optional[int] = None,
            source_app: str = "encuestas",
            external_entity_type: str = "user",
            external_entity_id: Optional[str] = None,
            channel: Optional[str] = None,
        ):
            key = str(candidate_payload.get("user_id") or candidate_payload.get("assignee_key") or candidate_payload.get("id") or "").strip()
            if not key:
                return
            materialized[key] = {
                "audience_group_id": audience_group_id,
                "assignee_key": key,
                "assignee_name_snapshot": candidate_payload.get("nombre") or candidate_payload.get("assignee_name_snapshot") or key,
                "assignee_role_snapshot": candidate_payload.get("role") or candidate_payload.get("assignee_role_snapshot") or "",
                "assignee_area_snapshot": candidate_payload.get("departamento") or candidate_payload.get("assignee_area_snapshot") or "",
                "assignee_position_snapshot": candidate_payload.get("puesto") or candidate_payload.get("assignee_position_snapshot") or "",
                "assignee_company_snapshot": candidate_payload.get("empresa") or candidate_payload.get("assignee_company_snapshot") or "",
                "assignment_type": assignment_type,
                "source_app": source_app,
                "external_entity_type": external_entity_type,
                "external_entity_id": external_entity_id or key,
                "channel": channel or ("public_link" if instance.audience_mode == "public_link" else "internal"),
            }

        for entry in entries:
            entry_type = str(entry.get("type") or "").strip().lower()
            values = entry.get("values") or []
            if entry_type == "user":
                for value in values:
                    user = users_by_id.get(str(value))
                    if user:
                        add_candidate(user, "user")
            elif entry_type == "role":
                for value in values:
                    for user in users_by_role.get(str(value).lower(), []):
                        add_candidate(user, "role")
            elif entry_type == "department":
                for value in values:
                    for user in users_by_department.get(str(value).lower(), []):
                        add_candidate(user, "department")
            elif entry_type == "position":
                for value in values:
                    for user in users_by_position.get(str(value).lower(), []):
                        add_candidate(user, "position")
            elif entry_type == "crm_contact":
                for value in values:
                    contact = crm_contacts_by_id.get(str(value))
                    if not contact:
                        continue
                    add_candidate(
                        {
                            "user_id": f"crm:{contact['id']}",
                            "nombre": contact.get("nombre") or f"Contacto {contact['id']}",
                            "puesto": contact.get("puesto") or "",
                            "empresa": contact.get("empresa") or "",
                        },
                        "crm_contact",
                        source_app="crm",
                        external_entity_type="crm_contact",
                        external_entity_id=str(contact["id"]),
                        channel="public_link",
                    )
            elif entry_type == "crm_campaign":
                for value in values:
                    if not str(value).isdigit():
                        continue
                    for contact in _load_crm_campaign_contacts(int(str(value))):
                        add_candidate(
                            {
                                "user_id": f"crm:{contact['id']}",
                                "nombre": contact.get("nombre") or f"Contacto {contact['id']}",
                                "puesto": contact.get("puesto") or "",
                                "empresa": contact.get("empresa") or "",
                            },
                            "crm_campaign",
                            source_app="crm",
                            external_entity_type="crm_campaign",
                            external_entity_id=str(value),
                            channel="public_link",
                        )

        for group in groups_created:
            for member in group["members"]:
                user = users_by_id.get(str(member["user_id"]))
                if user:
                    add_candidate(user, "manual_group", audience_group_id=group["group_id"])
                else:
                    add_candidate(member, "manual_group", audience_group_id=group["group_id"])

        persisted_assignments: List[SurveyAssignment] = []
        for candidate in materialized.values():
            assignment = SurveyAssignment(
                tenant_id=tenant_id,
                instance_id=instance_id,
                audience_group_id=candidate["audience_group_id"],
                assignee_key=candidate["assignee_key"],
                assignee_name_snapshot=candidate["assignee_name_snapshot"],
                assignee_role_snapshot=candidate["assignee_role_snapshot"],
                assignee_area_snapshot=candidate["assignee_area_snapshot"],
                assignee_position_snapshot=candidate["assignee_position_snapshot"],
                assignee_company_snapshot=candidate["assignee_company_snapshot"],
                source_app=candidate["source_app"],
                external_entity_type=candidate["external_entity_type"],
                external_entity_id=candidate["external_entity_id"],
                assignment_type=candidate["assignment_type"],
                channel=candidate["channel"],
                status="pending",
                due_at=due_at_value or instance.schedule_end_at,
            )
            db.add(assignment)
            persisted_assignments.append(assignment)

        db.flush()
        _sync_evaluations_360(db, instance, persisted_assignments, users_by_id)
        notifications_sent = 0
        if instance.status in {"published", "scheduled"}:
            notifications_sent = _send_assignment_notifications(
                db,
                instance,
                persisted_assignments,
                notification_kind="invitation",
            )
        instance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(instance)
        return {
            "count": len(materialized),
            "notifications_sent": notifications_sent,
            "assignments": list_assignments(instance_id, tenant_id),
        }
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
