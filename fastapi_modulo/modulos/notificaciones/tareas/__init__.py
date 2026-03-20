from fastapi_modulo.modulos.notificaciones.tareas.celery_tasks import (
    celery_app,
    send_notification,
)

__all__ = ["celery_app", "send_notification"]
