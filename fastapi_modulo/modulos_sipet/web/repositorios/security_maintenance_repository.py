from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.modelos.db_models import WebLoginAttempt, WebMfaChallenge, WebUserSession
from fastapi_modulo.modulos_sipet.web.servicios.access_risk_ml_service import batch_predict_recent_logins, train_access_risk_model
from fastapi_modulo.modulos_sipet.web.servicios.analytics_service import build_backend_analytics, export_access_history_excel
from fastapi_modulo.modulos_sipet.web.servicios.audit_report_service import (
    build_security_compliance_report,
    export_security_audit_pdf,
)


def cleanup_expired_sessions() -> int:
    db = SessionLocal()
    try:
        deleted = (
            db.query(WebUserSession)
            .filter(
                (WebUserSession.expires_at < datetime.utcnow())
                | (WebUserSession.revoked_at.is_not(None))
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return int(deleted or 0)
    except (OperationalError, SQLAlchemyError):
        db.rollback()
        return 0
    finally:
        db.close()


def cleanup_expired_mfa_challenges() -> int:
    db = SessionLocal()
    try:
        deleted = (
            db.query(WebMfaChallenge)
            .filter(
                (WebMfaChallenge.expires_at < datetime.utcnow())
                | (WebMfaChallenge.used_at.is_not(None))
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return int(deleted or 0)
    except (OperationalError, SQLAlchemyError):
        db.rollback()
        return 0
    finally:
        db.close()


def detect_suspicious_login_patterns(window_minutes: int = 15, threshold: int = 5) -> list[dict]:
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(minutes=max(1, int(window_minutes)))
        rows = (
            db.query(
                WebLoginAttempt.ip.label("ip"),
                WebLoginAttempt.username.label("username"),
                func.count(WebLoginAttempt.id).label("attempts"),
            )
            .filter(
                WebLoginAttempt.created_at >= since,
                WebLoginAttempt.success.is_(False),
            )
            .group_by(WebLoginAttempt.ip, WebLoginAttempt.username)
            .having(func.count(WebLoginAttempt.id) >= threshold)
            .all()
        )
        return [
            {"ip": str(row.ip or ""), "username": str(row.username or ""), "attempts": int(row.attempts or 0)}
            for row in rows
        ]
    except (OperationalError, SQLAlchemyError):
        return []
    finally:
        db.close()


def summarize_active_sessions() -> dict:
    db = SessionLocal()
    try:
        active_count = (
            db.query(func.count(WebUserSession.id))
            .filter(
                WebUserSession.revoked_at.is_(None),
                WebUserSession.expires_at >= datetime.utcnow(),
            )
            .scalar()
            or 0
        )
        active_users = (
            db.query(WebUserSession.user_id)
            .filter(
                WebUserSession.revoked_at.is_(None),
                WebUserSession.expires_at >= datetime.utcnow(),
            )
            .distinct()
            .count()
        )
        return {"active_sessions": int(active_count), "active_users": int(active_users)}
    except (OperationalError, SQLAlchemyError):
        return {"active_sessions": 0, "active_users": 0}
    finally:
        db.close()


def build_access_report(hours: int = 24) -> dict:
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(hours=max(1, int(hours)))
        successful_logins = (
            db.query(func.count(WebLoginAttempt.id))
            .filter(WebLoginAttempt.created_at >= since, WebLoginAttempt.success.is_(True))
            .scalar()
            or 0
        )
        failed_logins = (
            db.query(func.count(WebLoginAttempt.id))
            .filter(WebLoginAttempt.created_at >= since, WebLoginAttempt.success.is_(False))
            .scalar()
            or 0
        )
        return {
            "window_hours": int(hours),
            "successful_logins": int(successful_logins),
            "failed_logins": int(failed_logins),
        }
    except (OperationalError, SQLAlchemyError):
        return {"window_hours": int(hours), "successful_logins": 0, "failed_logins": 0}
    finally:
        db.close()


def build_backend_analytics_report(hours: int = 24) -> dict:
    return build_backend_analytics(hours)


def export_backend_access_history_excel(hours: int = 24, output_path: str = "") -> str:
    return export_access_history_excel(hours, output_path=output_path)


def build_security_compliance_snapshot(hours: int = 24) -> dict:
    return build_security_compliance_report(hours)


def export_security_audit_report_pdf(hours: int = 24, output_path: str = "") -> str:
    return export_security_audit_pdf(hours, output_path=output_path)


def train_backend_access_risk_model(hours: int = 24 * 30) -> dict:
    return train_access_risk_model(hours)


def build_access_risk_report(hours: int = 24, limit: int = 100) -> dict:
    predictions = batch_predict_recent_logins(hours=hours, limit=limit)
    suspicious = [item for item in predictions if item.get("label") == "sospechoso"]
    unusual = [item for item in predictions if item.get("label") == "inusual"]
    return {
        "window_hours": int(hours),
        "evaluated_events": len(predictions),
        "suspicious_events": suspicious,
        "unusual_events": unusual,
        "high_risk_count": len(suspicious),
        "medium_risk_count": len(unusual),
    }


def build_security_alerts() -> list[dict]:
    alerts = [
        {
            "type": "suspicious_login_pattern",
            "severity": "high" if item.get("attempts", 0) >= 10 else "medium",
            **item,
        }
        for item in detect_suspicious_login_patterns()
    ]
    for item in build_access_risk_report().get("suspicious_events", []):
        alerts.append(
            {
                "type": "access_risk_ml",
                "severity": "high",
                "username": item.get("username", ""),
                "ip": item.get("ip", ""),
                "risk_score": item.get("risk_score", 0.0),
            }
        )
    return alerts
