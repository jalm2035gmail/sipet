from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from fastapi import Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.planificacion.modelos.kpis_service import (
    _ensure_kpi_mediciones_table,
    _kpi_evaluate_status,
)
from fastapi_modulo.modulos_sipet.modulo_base.runtime_app import (
    DocumentoEvidencia,
    POAActivity,
    POADeliverableApproval,
    POASubactivity,
    PublicQuizSubmission,
    SessionLocal,
    StrategicObjectiveConfig,
    UserNotificationRead,
    _activity_status,
    _current_user_record,
    _is_user_process_owner,
    _normalize_tenant_id,
    _notification_user_key,
    _user_aliases,
    get_current_tenant,
)
from fastapi_modulo.modulos_sipet.web.servicios.access_service import is_superadmin


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class NotificationItem(BaseModel):
    id: str
    kind: str
    title: str
    message: str
    created_at: str
    href: str
    read: bool = False
    deadline_state: Optional[str] = None
    severity: Optional[str] = None


class NotificationCounts(BaseModel):
    poa_aprobacion: int = 0
    documento_autorizacion: int = 0
    actividad_fecha: int = 0
    actividad_atrasada: int = 0
    actividad_por_vencer: int = 0
    quiz_descuento: int = 0
    ia_riesgo_poa: int = 0
    kpi_alerta: int = 0
    kpi_advertencia: int = 0


class NotificationsSummaryResponse(BaseModel):
    success: bool
    total: int
    unread: int
    counts: NotificationCounts
    items: List[NotificationItem]


class MarkReadRequest(BaseModel):
    id: str = Field(..., min_length=1, description="ID de la notificación a marcar como leída")


class MarkAllReadRequest(BaseModel):
    ids: List[str] = Field(default_factory=list, max_length=200)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _get_document_tenant(request: Request) -> str:
    return _normalize_tenant_id(get_current_tenant(request))


def _severity_label_es(severity: str) -> str:
    return {"high": "alto", "medium": "medio", "low": "bajo"}.get(severity.lower(), "bajo")


def _safe_isoformat(dt: Any, fallback: datetime) -> str:
    """Devuelve ISO string de forma segura ante valores None o inesperados."""
    if dt is None:
        return fallback.isoformat()
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


# ---------------------------------------------------------------------------
# Recolectores de notificaciones (separados para claridad y testabilidad)
# ---------------------------------------------------------------------------

def _collect_poa_approvals(
    request: Request,
    db: Session,
    now: datetime,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    pending = (
        db.query(POADeliverableApproval)
        .filter(POADeliverableApproval.status == "pendiente")
        .order_by(POADeliverableApproval.created_at.desc())
        .all()
    )
    for approval in pending:
        if not _is_user_process_owner(request, db, approval.process_owner):
            continue
        activity = (
            db.query(POAActivity)
            .filter(POAActivity.id == approval.activity_id)
            .first()
        )
        objective = (
            db.query(StrategicObjectiveConfig)
            .filter(StrategicObjectiveConfig.id == approval.objective_id)
            .first()
        )
        items.append(
            {
                "id": f"poa-approval-{approval.id}",
                "kind": "poa_aprobacion",
                "title": "Aprobación de entregable pendiente",
                "message": (
                    f"Actividad {activity.nombre if activity else 'sin nombre'} "
                    f"({activity.codigo if activity else ''}) - "
                    f"Objetivo {objective.nombre if objective else ''}"
                ).strip(),
                "created_at": _safe_isoformat(approval.created_at, now),
                "href": "/poa/crear",
            }
        )
    return items


def _collect_document_approvals(
    request: Request,
    db: Session,
    now: datetime,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    try:
        document_tenant = _get_document_tenant(request)
        docs_query = db.query(DocumentoEvidencia).filter(
            DocumentoEvidencia.estado.in_(["enviado", "actualizado"])
        )
        if is_superadmin(request):
            header_tenant = request.headers.get("x-tenant-id")
            if header_tenant and _normalize_tenant_id(header_tenant) != "all":
                docs_query = docs_query.filter(
                    func.lower(DocumentoEvidencia.tenant_id)
                    == _normalize_tenant_id(header_tenant).lower()
                )
            elif not header_tenant:
                docs_query = docs_query.filter(
                    func.lower(DocumentoEvidencia.tenant_id) == document_tenant.lower()
                )
        else:
            docs_query = docs_query.filter(
                func.lower(DocumentoEvidencia.tenant_id) == document_tenant.lower()
            )
        for doc in docs_query.order_by(DocumentoEvidencia.updated_at.desc()).limit(20):
            items.append(
                {
                    "id": f"doc-approval-{doc.id}",
                    "kind": "documento_autorizacion",
                    "title": "Documento pendiente de autorización",
                    "message": (
                        f"{(doc.titulo or '').strip()} · Estado: {(doc.estado or '').strip()}"
                    ),
                    "created_at": _safe_isoformat(
                        doc.updated_at or doc.enviado_at or doc.creado_at, now
                    ),
                    "href": "/reportes/documentos",
                }
            )
    except Exception:
        db.rollback()
    return items


def _collect_quiz_submissions(
    db: Session,
    now: datetime,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for quiz in (
        db.query(PublicQuizSubmission)
        .order_by(PublicQuizSubmission.created_at.desc(), PublicQuizSubmission.id.desc())
        .limit(20)
    ):
        items.append(
            {
                "id": f"quiz-submission-{quiz.id}",
                "kind": "quiz_descuento",
                "title": "Nuevo cuestionario de descuento",
                "message": (
                    f"{(quiz.nombre or '').strip()} · {(quiz.cooperativa or '').strip()} · "
                    f"{int(quiz.correctas or 0)}/10 correctas · "
                    f"{int(quiz.descuento or 0)}% de descuento"
                ),
                "created_at": _safe_isoformat(quiz.created_at, now),
                "href": "/usuarios",
            }
        )
    return items


def _collect_activity_deadlines(
    request: Request,
    db: Session,
    now: datetime,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    today = now.date()
    session_username = (
        getattr(request.state, "user_name", None)
        or request.cookies.get("user_name")
        or ""
    ).strip()
    user = _current_user_record(request, db)
    aliases = sorted(_user_aliases(user, session_username))
    if not aliases:
        return items

    lookahead = today + timedelta(days=2)

    # Actividades propias
    own_activities = (
        db.query(POAActivity)
        .filter(func.lower(POAActivity.responsable).in_(aliases))
        .order_by(POAActivity.fecha_final.asc(), POAActivity.id.asc())
        .all()
    )
    for activity in own_activities:
        if not activity.fecha_final:
            continue
        if (activity.entrega_estado or "").strip().lower() == "aprobada":
            continue
        if activity.fecha_final > lookahead:
            continue
        delta = (activity.fecha_final - today).days
        if delta < 0:
            title, msg, state = (
                "Tarea atrasada",
                f"{activity.nombre} está atrasada desde {activity.fecha_final.isoformat()}",
                "atrasada",
            )
        elif delta == 0:
            title, msg, state = "Actividad vence hoy", f"{activity.nombre} vence hoy", "por_vencer"
        else:
            title, msg, state = (
                "Actividad por vencer",
                f"{activity.nombre} vence el {activity.fecha_final.isoformat()}",
                "por_vencer",
            )
        items.append(
            {
                "id": f"activity-deadline-{activity.id}",
                "kind": "actividad_fecha",
                "title": title,
                "message": msg,
                "deadline_state": state,
                "created_at": datetime.combine(activity.fecha_final, datetime.min.time()).isoformat(),
                "href": "/poa/crear",
            }
        )

    # Subactividades propias
    own_subactivities = (
        db.query(POASubactivity, POAActivity)
        .join(POAActivity, POAActivity.id == POASubactivity.activity_id)
        .filter(func.lower(POASubactivity.responsable).in_(aliases))
        .order_by(POASubactivity.fecha_final.asc(), POASubactivity.id.asc())
        .all()
    )
    for subactivity, parent in own_subactivities:
        if not subactivity.fecha_final:
            continue
        if _activity_status(parent, today=today) == "Terminada":
            continue
        if subactivity.fecha_final > lookahead:
            continue
        delta = (subactivity.fecha_final - today).days
        if delta < 0:
            title, msg, state = (
                "Tarea atrasada",
                (
                    f"{subactivity.nombre} (subtarea de {parent.nombre}) "
                    f"está atrasada desde {subactivity.fecha_final.isoformat()}"
                ),
                "atrasada",
            )
        elif delta == 0:
            title, msg, state = "Subtarea vence hoy", f"{subactivity.nombre} vence hoy", "por_vencer"
        else:
            title, msg, state = (
                "Subtarea por vencer",
                f"{subactivity.nombre} vence el {subactivity.fecha_final.isoformat()}",
                "por_vencer",
            )
        items.append(
            {
                "id": f"subactivity-deadline-{subactivity.id}",
                "kind": "actividad_fecha",
                "title": title,
                "message": msg,
                "deadline_state": state,
                "created_at": datetime.combine(
                    subactivity.fecha_final, datetime.min.time()
                ).isoformat(),
                "href": (
                    f"/poa/crear"
                    f"?activity_id={int(parent.id or 0)}"
                    f"&subactivity_id={int(subactivity.id or 0)}"
                ),
            }
        )
    return items


def _collect_ia_risk_alerts(db: Session, now: datetime) -> List[Dict[str, Any]]:
    """
    Lee alertas activas del motor de riesgo IA.
    La tabla se crea via Alembic; aquí solo se consulta.
    Si la tabla aún no existe (entorno recién inicializado) se captura
    la excepción y se devuelve lista vacía sin romper el flujo general.
    """
    items: List[Dict[str, Any]] = []
    try:
        rows = db.execute(
            text(
                """
                SELECT id, created_at, updated_at, severity, risk_score,
                       title, message, recommendation
                FROM ia_poa_risk_alerts
                WHERE source = 'ia_risk_engine' AND status = 'active'
                ORDER BY
                    CASE severity
                        WHEN 'high'   THEN 3
                        WHEN 'medium' THEN 2
                        WHEN 'low'    THEN 1
                        ELSE 0
                    END DESC,
                    risk_score DESC,
                    updated_at DESC
                LIMIT 20
                """
            )
        ).fetchall()
        for row in rows:
            severity = str(row.severity or "").strip().lower()
            items.append(
                {
                    "id": f"ia-poa-risk-{int(row.id or 0)}",
                    "kind": "ia_riesgo_poa",
                    "title": str(row.title or "Alerta IA de riesgo POA").strip(),
                    "message": (
                        f"{str(row.message or '').strip()} "
                        f"· Riesgo {_severity_label_es(severity)} "
                        f"· Recomendación: {str(row.recommendation or '').strip()}"
                    ).strip(" ·"),
                    "created_at": str(
                        row.updated_at or row.created_at or now.isoformat()
                    ).strip() or now.isoformat(),
                    "href": "/poa/crear",
                }
            )
    except Exception:
        db.rollback()
    return items


def _collect_kpi_alerts(db: Session, now: datetime) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    try:
        _ensure_kpi_mediciones_table(db)
        rows = db.execute(
            text(
                """
                SELECT k.id, k.nombre, k.estandar, k.referencia,
                       m.valor, m.periodo, m.created_at
                FROM strategic_objective_kpis k
                INNER JOIN kpi_mediciones m ON m.id = (
                    SELECT id FROM kpi_mediciones
                    WHERE kpi_id = k.id
                    ORDER BY created_at DESC
                    LIMIT 1
                )
                WHERE k.estandar != '' AND k.referencia != ''
                """
            )
        ).fetchall()
        for row in rows:
            kpi_status = _kpi_evaluate_status(
                float(row[4] or 0), str(row[2] or ""), str(row[3] or "")
            )
            if kpi_status not in ("alert", "warning"):
                continue
            sev_label = "Alerta" if kpi_status == "alert" else "Advertencia"
            periodo = str(row[5] or "")
            items.append(
                {
                    "id": f"kpi-alerta-{int(row[0])}",
                    "kind": "kpi_alerta",
                    "severity": kpi_status,
                    "title": f"{sev_label} KPI: {str(row[1] or '')}",
                    "message": (
                        f"Valor: {float(row[4] or 0)} · Meta ({str(row[2] or '')}): {str(row[3] or '')}"
                        + (f" · Período: {periodo}" if periodo else "")
                    ),
                    "created_at": str(row[6] or "") or now.isoformat(),
                    "href": "/inicio/kpis",
                }
            )
    except Exception:
        db.rollback()
    return items


# ---------------------------------------------------------------------------
# Conteo de no leídos
# ---------------------------------------------------------------------------

def _build_counts(items: List[Dict[str, Any]]) -> NotificationCounts:
    counts = NotificationCounts()
    for item in items:
        if item.get("read"):
            continue
        kind = str(item.get("kind") or "")
        if kind == "poa_aprobacion":
            counts.poa_aprobacion += 1
        elif kind == "documento_autorizacion":
            counts.documento_autorizacion += 1
        elif kind == "actividad_fecha":
            counts.actividad_fecha += 1
            state = str(item.get("deadline_state") or "").lower()
            if state == "atrasada":
                counts.actividad_atrasada += 1
            elif state == "por_vencer":
                counts.actividad_por_vencer += 1
        elif kind == "quiz_descuento":
            counts.quiz_descuento += 1
        elif kind == "ia_riesgo_poa":
            counts.ia_riesgo_poa += 1
        elif kind == "kpi_alerta":
            severity = str(item.get("severity") or "").lower()
            if severity == "alert":
                counts.kpi_alerta += 1
            elif severity == "warning":
                counts.kpi_advertencia += 1
    return counts


# ---------------------------------------------------------------------------
# Endpoints públicos
# ---------------------------------------------------------------------------

def notifications_summary(request: Request) -> JSONResponse:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        tenant_id = _normalize_tenant_id(get_current_tenant(request))
        user_key = _notification_user_key(request, db)

        # Recolectar todas las fuentes de notificaciones
        items: List[Dict[str, Any]] = []
        items.extend(_collect_poa_approvals(request, db, now))
        items.extend(_collect_document_approvals(request, db, now))
        if is_superadmin(request):
            items.extend(_collect_quiz_submissions(db, now))
        items.extend(_collect_activity_deadlines(request, db, now))
        items.extend(_collect_ia_risk_alerts(db, now))
        items.extend(_collect_kpi_alerts(db, now))

        # Ordenar y limitar
        items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        limited_items = items[:25]

        # Marcar leídas
        notification_ids = [
            str(item.get("id") or "").strip()
            for item in limited_items
            if str(item.get("id") or "").strip()
        ]
        read_ids: Set[str] = set()
        if user_key and notification_ids:
            read_rows = (
                db.query(UserNotificationRead.notification_id)
                .filter(
                    UserNotificationRead.tenant_id == tenant_id,
                    UserNotificationRead.user_key == user_key,
                    UserNotificationRead.notification_id.in_(notification_ids),
                )
                .all()
            )
            read_ids = {str(row[0]) for row in read_rows}

        for item in limited_items:
            item["read"] = str(item.get("id") or "") in read_ids

        counts = _build_counts(limited_items)
        unread = sum(1 for item in limited_items if not item.get("read"))

        return JSONResponse(
            {
                "success": True,
                "total": len(limited_items),
                "unread": unread,
                "counts": counts.model_dump(),
                "items": limited_items,
            }
        )
    finally:
        db.close()


def mark_notification_read(
    request: Request,
    data: MarkReadRequest = Body(...),
) -> JSONResponse:
    db = SessionLocal()
    try:
        tenant_id = _normalize_tenant_id(get_current_tenant(request))
        user_key = _notification_user_key(request, db)
        if not user_key:
            return JSONResponse(
                {"success": False, "error": "Usuario no autenticado"}, status_code=401
            )

        row = (
            db.query(UserNotificationRead)
            .filter(
                UserNotificationRead.tenant_id == tenant_id,
                UserNotificationRead.user_key == user_key,
                UserNotificationRead.notification_id == data.id,
            )
            .first()
        )
        now = datetime.utcnow()
        if row:
            row.read_at = now
            db.add(row)
        else:
            db.add(
                UserNotificationRead(
                    tenant_id=tenant_id,
                    user_key=user_key,
                    notification_id=data.id,
                    read_at=now,
                )
            )
        db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()


def mark_all_notifications_read(
    request: Request,
    data: MarkAllReadRequest = Body(default_factory=MarkAllReadRequest),
) -> JSONResponse:
    ids = [v.strip() for v in data.ids if v.strip()]
    if not ids:
        return JSONResponse({"success": True, "updated": 0})

    db = SessionLocal()
    try:
        tenant_id = _normalize_tenant_id(get_current_tenant(request))
        user_key = _notification_user_key(request, db)
        if not user_key:
            return JSONResponse(
                {"success": False, "error": "Usuario no autenticado"}, status_code=401
            )

        existing = (
            db.query(UserNotificationRead)
            .filter(
                UserNotificationRead.tenant_id == tenant_id,
                UserNotificationRead.user_key == user_key,
                UserNotificationRead.notification_id.in_(ids),
            )
            .all()
        )
        existing_by_id = {row.notification_id: row for row in existing}
        now = datetime.utcnow()

        for notif_id in ids:
            row = existing_by_id.get(notif_id)
            if row:
                row.read_at = now
                db.add(row)
            else:
                db.add(
                    UserNotificationRead(
                        tenant_id=tenant_id,
                        user_key=user_key,
                        notification_id=notif_id,
                        read_at=now,
                    )
                )
        db.commit()
        return JSONResponse({"success": True, "updated": len(ids)})
    finally:
        db.close()
        