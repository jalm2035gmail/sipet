from __future__ import annotations

from fastapi_modulo.modulos_sipet.web.servicios import access_risk_ml_service


def test_predict_access_risk_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        access_risk_ml_service,
        "_recent_login_stats",
        lambda username, ip, created_at, lookback_minutes=60: {
            "recent_failed_attempts": 8,
            "recent_attempts": 10,
            "recent_distinct_ips": 4,
            "recent_ip_attempts": 3,
        },
    )
    monkeypatch.setattr(access_risk_ml_service, "load_model", lambda output_path=access_risk_ml_service.MODEL_PATH: None)
    payload = access_risk_ml_service.predict_access_risk(
        {
            "created_at": "2026-03-15T02:10:00",
            "username": "autoridad",
            "ip": "10.1.1.50",
            "user_agent": "Unknown Agent",
            "success": False,
            "metadata": {"role": "autoridades"},
        }
    )
    assert payload["model_status"] == "fallback"
    assert payload["label"] in {"inusual", "sospechoso"}


def test_train_access_risk_model_fallback_without_sklearn(monkeypatch) -> None:
    monkeypatch.setattr(
        access_risk_ml_service,
        "build_training_dataset",
        lambda hours=24 * 30: [
            {
                "hour": 10,
                "weekday": 1,
                "ip_octet_bucket": 22,
                "user_agent_family": "chrome",
                "role": "usuario",
                "success": 1,
                "recent_failed_attempts": 0,
                "recent_attempts": 2,
                "recent_distinct_ips": 1,
                "recent_ip_attempts": 2,
                "label": "normal",
            }
        ],
    )
    monkeypatch.setattr(access_risk_ml_service, "sklearn_available", lambda: False)
    payload = access_risk_ml_service.train_access_risk_model()
    assert payload["status"] == "fallback"
    assert payload["samples"] == 1


def test_batch_predict_recent_logins(monkeypatch) -> None:
    class _Row:
        def __init__(self, created_at, username, ip, user_agent, success) -> None:
            self.created_at = created_at
            self.username = username
            self.ip = ip
            self.user_agent = user_agent
            self.success = success

    class _Query:
        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

        def all(self):
            from datetime import datetime

            return [_Row(datetime(2026, 3, 15, 10, 0, 0), "admin", "1.1.1.1", "pytest", True)]

    class _Session:
        def query(self, *args, **kwargs):
            return _Query()

        def close(self):
            return None

    monkeypatch.setattr(access_risk_ml_service, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(
        access_risk_ml_service,
        "predict_access_risk",
        lambda event, model_path=access_risk_ml_service.MODEL_PATH: {
            "label": "normal",
            "risk_score": 0.12,
            "model_status": "fallback",
        },
    )
    rows = access_risk_ml_service.batch_predict_recent_logins()
    assert rows[0]["label"] == "normal"
    assert rows[0]["risk_score"] == 0.12
