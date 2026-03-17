from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta
from typing import Any

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover
    letter = None
    canvas = None

from sqlalchemy import func

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.modelos.db_models import WebLoginAttempt, WebSecurityEvent, WebUserSession
from fastapi_modulo.modulos_sipet.web.repositorios.core_repository import list_users_basic


def reportlab_enabled() -> bool:
    return canvas is not None and letter is not None


def _hours_since(hours: int) -> datetime:
    return datetime.utcnow() - timedelta(hours=max(1, int(hours)))


def active_sessions_by_user(limit: int = 100) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = (
            db.query(
                WebUserSession.user_id.label("user_id"),
                WebUserSession.tenant_id.label("tenant_id"),
                func.count(WebUserSession.id).label("active_sessions"),
            )
            .filter(
                WebUserSession.revoked_at.is_(None),
                WebUserSession.expires_at >= datetime.utcnow(),
            )
            .group_by(WebUserSession.user_id, WebUserSession.tenant_id)
            .order_by(func.count(WebUserSession.id).desc(), WebUserSession.user_id.asc())
            .limit(max(1, int(limit)))
            .all()
        )
        return [
            {
                "user_id": int(row.user_id or 0),
                "tenant_id": str(row.tenant_id or ""),
                "active_sessions": int(row.active_sessions or 0),
            }
            for row in rows
        ]
    finally:
        db.close()


def failed_login_attempts(hours: int = 24, limit: int = 100) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = (
            db.query(WebLoginAttempt)
            .filter(
                WebLoginAttempt.created_at >= _hours_since(hours),
                WebLoginAttempt.success.is_(False),
            )
            .order_by(WebLoginAttempt.created_at.desc())
            .limit(max(1, int(limit)))
            .all()
        )
        return [
            {
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "tenant_id": str(row.tenant_id or ""),
                "username": str(row.username or ""),
                "ip": str(row.ip or ""),
                "user_agent": str(row.user_agent or ""),
            }
            for row in rows
        ]
    finally:
        db.close()


def access_events_by_role(hours: int = 24) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = (
            db.query(
                WebSecurityEvent.event_type.label("event_type"),
                func.count(WebSecurityEvent.id).label("events"),
            )
            .filter(
                WebSecurityEvent.created_at >= _hours_since(hours),
                WebSecurityEvent.event_type.in_(("login_success", "login_failed", "screen_view")),
            )
            .group_by(WebSecurityEvent.event_type)
            .order_by(func.count(WebSecurityEvent.id).desc())
            .all()
        )
        return [{"event_type": str(row.event_type or ""), "events": int(row.events or 0)} for row in rows]
    finally:
        db.close()


def users_with_mfa_disabled(limit: int = 100) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        disabled: list[dict[str, Any]] = []
        for row in list_users_basic(db, limit=limit):
            has_totp = bool(row.get("totp_enabled") and row.get("totp_secret"))
            has_passkey = bool(row.get("backendauthn_credential_id") and row.get("backendauthn_public_key"))
            if has_totp or has_passkey:
                continue
            disabled.append(
                {
                    "user_id": int(row.get("id", 0) or 0),
                    "username": str(row.get("usuario", "") or ""),
                    "role_id": int(row.get("rol_id", 0) or 0),
                }
            )
        return disabled
    except Exception:
        return []
    finally:
        db.close()


def credential_change_events(hours: int = 24, limit: int = 100) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = (
            db.query(WebSecurityEvent)
            .filter(
                WebSecurityEvent.created_at >= _hours_since(hours),
                WebSecurityEvent.event_type.in_(("passkey_registered", "passkey_revoked", "password_changed")),
            )
            .order_by(WebSecurityEvent.created_at.desc())
            .limit(max(1, int(limit)))
            .all()
        )
        return [
            {
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "event_type": str(row.event_type or ""),
                "username": str(row.username or ""),
                "success": bool(row.success),
            }
            for row in rows
        ]
    finally:
        db.close()


def build_security_compliance_report(hours: int = 24) -> dict[str, Any]:
    active_sessions = active_sessions_by_user()
    failed_attempts = failed_login_attempts(hours)
    disabled_mfa = users_with_mfa_disabled()
    credential_events = credential_change_events(hours)
    return {
        "window_hours": int(hours),
        "active_sessions_users": len(active_sessions),
        "failed_login_attempts": len(failed_attempts),
        "users_with_mfa_disabled": len(disabled_mfa),
        "credential_change_events": len(credential_events),
        "compliance_score": max(
            0,
            100 - min(40, len(disabled_mfa) * 2) - min(30, len(failed_attempts)) - min(20, len(active_sessions)),
        ),
    }


def export_security_audit_pdf(hours: int = 24, output_path: str = "") -> str:
    if not reportlab_enabled():
        return ""
    resolved_path = output_path or os.path.join(
        tempfile.gettempdir(),
        f"web_security_audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf",
    )
    report = build_security_compliance_report(hours)
    session_rows = active_sessions_by_user(limit=12)
    failed_rows = failed_login_attempts(hours, limit=12)
    credential_rows = credential_change_events(hours, limit=12)
    role_rows = access_events_by_role(hours)

    pdf = canvas.Canvas(resolved_path, pagesize=letter)
    width, height = letter
    y = height - 48
    pdf.setTitle("Reporte de Auditoria de Seguridad")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, "Reporte de Auditoria de Seguridad")
    y -= 24
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, f"Generado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    y -= 22

    def draw_section(title: str, rows: list[str]) -> None:
        nonlocal y
        if y < 100:
            pdf.showPage()
            y = height - 48
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, title)
        y -= 16
        pdf.setFont("Helvetica", 10)
        for line in rows:
            if y < 60:
                pdf.showPage()
                y = height - 48
                pdf.setFont("Helvetica", 10)
            pdf.drawString(50, y, line[:110])
            y -= 13
        y -= 8

    draw_section(
        "Cumplimiento",
        [
            f"Ventana analizada: {report['window_hours']} horas",
            f"Usuarios con sesiones activas: {report['active_sessions_users']}",
            f"Intentos fallidos: {report['failed_login_attempts']}",
            f"Usuarios con MFA deshabilitado: {report['users_with_mfa_disabled']}",
            f"Eventos de credenciales: {report['credential_change_events']}",
            f"Puntaje de cumplimiento: {report['compliance_score']}/100",
        ],
    )
    draw_section(
        "Sesiones Activas por Usuario",
        [
            f"user_id={item['user_id']} tenant={item['tenant_id']} sesiones={item['active_sessions']}"
            for item in session_rows
        ]
        or ["Sin sesiones activas."],
    )
    draw_section(
        "Intentos Fallidos de Login",
        [
            f"{item['created_at']} usuario={item['username']} ip={item['ip']}"
            for item in failed_rows
        ]
        or ["Sin intentos fallidos."],
    )
    draw_section(
        "Eventos de Credenciales",
        [
            f"{item['created_at']} {item['event_type']} usuario={item['username']}"
            for item in credential_rows
        ]
        or ["Sin cambios de credenciales."],
    )
    draw_section(
        "Eventos de Acceso por Tipo",
        [
            f"{item['event_type']}: {item['events']}"
            for item in role_rows
        ]
        or ["Sin eventos."],
    )
    pdf.save()
    return resolved_path
