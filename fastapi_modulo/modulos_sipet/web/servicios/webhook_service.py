"""
Servicio de webhooks y notificaciones salientes.

Usa httpx (ya instalado) para enviar notificaciones HTTP a endpoints
externos cuando ocurren eventos de seguridad relevantes:
- Acceso sospechoso detectado por el modelo ML
- Umbral de intentos fallidos superado
- Usuario sin MFA detectado en reporte de cumplimiento
- Snapshot de cumplimiento con score bajo

Configuración via variables de entorno:
  WEB_WEBHOOK_URL          URL destino (ej. Slack, Teams, endpoint propio)
  WEB_WEBHOOK_SECRET       Token Bearer para autenticar el webhook
  WEB_WEBHOOK_ENABLED      "true" / "false" (default: true si WEB_WEBHOOK_URL está definida)
  WEB_WEBHOOK_TIMEOUT      Segundos de timeout (default: 5)
  WEB_WEBHOOK_COMPLIANCE_THRESHOLD  Score mínimo antes de notificar (default: 60)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# ── Configuración ─────────────────────────────────────────────────────────────
_WEBHOOK_URL = (os.environ.get("WEB_WEBHOOK_URL") or "").strip()
_WEBHOOK_SECRET = (os.environ.get("WEB_WEBHOOK_SECRET") or "").strip()
_WEBHOOK_TIMEOUT = float((os.environ.get("WEB_WEBHOOK_TIMEOUT") or "5").strip() or "5")
_COMPLIANCE_THRESHOLD = int((os.environ.get("WEB_WEBHOOK_COMPLIANCE_THRESHOLD") or "60").strip() or "60")
_WEBHOOK_ENABLED = (
    os.environ.get("WEB_WEBHOOK_ENABLED", "true" if _WEBHOOK_URL else "false")
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)


def webhook_available() -> bool:
    """Devuelve True si httpx está instalado, hay URL configurada y el webhook está habilitado."""
    return bool(httpx is not None and _WEBHOOK_URL and _WEBHOOK_ENABLED)


def _build_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if _WEBHOOK_SECRET:
        headers["Authorization"] = f"Bearer {_WEBHOOK_SECRET}"
    return headers


def _utcnow_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _send(payload: dict[str, Any]) -> bool:
    """
    Envía el payload al webhook configurado de forma síncrona.
    Devuelve True si el servidor respondió 2xx, False en cualquier otro caso.
    Nunca lanza excepciones — falla silenciosamente para no interrumpir
    el flujo de la aplicación.
    """
    if not webhook_available():
        return False
    try:
        with httpx.Client(timeout=_WEBHOOK_TIMEOUT) as client:
            response = client.post(_WEBHOOK_URL, json=payload, headers=_build_headers())
            if response.is_success:
                return True
            logger.warning(
                "webhook_service: respuesta no exitosa status=%s url=%s",
                response.status_code,
                _WEBHOOK_URL,
            )
            return False
    except httpx.TimeoutException:
        logger.warning("webhook_service: timeout enviando a %s", _WEBHOOK_URL)
        return False
    except Exception as exc:
        logger.warning("webhook_service: error inesperado — %s", exc)
        return False


# ── Notificaciones públicas ───────────────────────────────────────────────────

def notify_suspicious_access(
    username: str,
    ip: str,
    risk_score: float,
    risk_label: str,
    model_status: str = "trained",
    extra: dict[str, Any] | None = None,
) -> bool:
    """
    Notifica cuando el modelo ML clasifica un intento de acceso como sospechoso.
    Solo envía si risk_label == "sospechoso" para evitar ruido.
    """
    if risk_label != "sospechoso":
        return False
    payload: dict[str, Any] = {
        "event": "suspicious_access",
        "timestamp": _utcnow_iso(),
        "username": username,
        "ip": ip,
        "risk_score": round(float(risk_score), 4),
        "risk_label": risk_label,
        "model_status": model_status,
    }
    if isinstance(extra, dict):
        payload["extra"] = extra
    logger.info(
        "webhook_service: notificando acceso sospechoso username=%s ip=%s score=%s",
        username, ip, risk_score,
    )
    return _send(payload)


def notify_failed_login_threshold(
    tenant_id: str,
    failed_count: int,
    window_hours: int,
    top_ips: list[dict[str, Any]] | None = None,
) -> bool:
    """
    Notifica cuando el número de intentos fallidos supera el umbral
    en la ventana de tiempo analizada.
    """
    payload: dict[str, Any] = {
        "event": "failed_login_threshold_exceeded",
        "timestamp": _utcnow_iso(),
        "tenant_id": tenant_id,
        "failed_count": int(failed_count),
        "window_hours": int(window_hours),
        "top_ips": top_ips or [],
    }
    logger.info(
        "webhook_service: umbral de intentos fallidos superado tenant=%s count=%s",
        tenant_id, failed_count,
    )
    return _send(payload)


def notify_mfa_disabled_users(
    users: list[dict[str, Any]],
    tenant_id: str = "",
) -> bool:
    """
    Notifica la lista de usuarios sin MFA configurado.
    Solo envía si hay al menos un usuario afectado.
    """
    if not users:
        return False
    payload: dict[str, Any] = {
        "event": "mfa_disabled_users_detected",
        "timestamp": _utcnow_iso(),
        "tenant_id": tenant_id,
        "affected_count": len(users),
        "users": [
            {
                "user_id": u.get("user_id"),
                "username": u.get("username"),
                "role_id": u.get("role_id"),
            }
            for u in users
        ],
    }
    logger.info(
        "webhook_service: %s usuarios sin MFA detectados tenant=%s",
        len(users), tenant_id,
    )
    return _send(payload)


def notify_compliance_score(
    score: int,
    report: dict[str, Any],
    tenant_id: str = "",
) -> bool:
    """
    Notifica cuando el score de cumplimiento cae por debajo del umbral configurado
    (WEB_WEBHOOK_COMPLIANCE_THRESHOLD, default 60).
    """
    if score >= _COMPLIANCE_THRESHOLD:
        return False
    payload: dict[str, Any] = {
        "event": "compliance_score_below_threshold",
        "timestamp": _utcnow_iso(),
        "tenant_id": tenant_id,
        "compliance_score": int(score),
        "threshold": _COMPLIANCE_THRESHOLD,
        "window_hours": report.get("window_hours"),
        "active_sessions_users": report.get("active_sessions_users"),
        "failed_login_attempts": report.get("failed_login_attempts"),
        "users_with_mfa_disabled": report.get("users_with_mfa_disabled"),
        "credential_change_events": report.get("credential_change_events"),
    }
    logger.warning(
        "webhook_service: score de cumplimiento bajo score=%s threshold=%s tenant=%s",
        score, _COMPLIANCE_THRESHOLD, tenant_id,
    )
    return _send(payload)


def notify_security_event(
    event_type: str,
    username: str = "",
    tenant_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> bool:
    """
    Notificación genérica para cualquier evento de seguridad.
    Útil para extender sin modificar este servicio.
    """
    payload: dict[str, Any] = {
        "event": event_type,
        "timestamp": _utcnow_iso(),
        "username": username,
        "tenant_id": tenant_id,
        "metadata": metadata or {},
    }
    return _send(payload)
