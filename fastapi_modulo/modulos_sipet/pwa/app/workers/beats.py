from app.workers.celery_app import celery_app

# Evita tareas de ejemplo rotas en producción.
# Configura aquí sólo tareas realmente existentes.
celery_app.conf.beat_schedule = {}
