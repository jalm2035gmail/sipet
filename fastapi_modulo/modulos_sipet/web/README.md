# Web

Modulo tecnico para centralizar utilidades compartidas entre modulos SIPET.

## Incluye

- validacion estandar de acceso por `app_access`
- render comun de paginas backend
- render comun de pagina sin acceso
- lectura segura de assets y archivos de texto
- entrega de assets con validacion de path
- modelos SQLAlchemy propios para seguridad, sesiones, desafios MFA y preferencias
- estructura base en `modelos/`, `repositorios/` y `servicios/` con capas separadas para auth, sesiones, auditoria, preferencias y branding
- base Alembic local en [alembic.ini](/Users/jalm/Dropbox/Apps/SIPET/fastapi_modulo/modulos/web/alembic.ini) y [alembic/](/Users/jalm/Dropbox/Apps/SIPET/fastapi_modulo/modulos/web/alembic)
- tareas Celery para limpieza, auditoria y seguridad en [tareas/](/Users/jalm/Dropbox/Apps/SIPET/fastapi_modulo/modulos/web/tareas)
- analitica de accesos y uso de pantallas con `pandas`, `openpyxl` y `numpy` en [analytics_service.py](/Users/jalm/Dropbox/Apps/SIPET/fastapi_modulo/modulos/web/servicios/analytics_service.py)
- scoring de riesgo de acceso y entrenamiento persistente con `scikit-learn` y `joblib` en [access_risk_ml_service.py](/Users/jalm/Dropbox/Apps/SIPET/fastapi_modulo/modulos/web/servicios/access_risk_ml_service.py)
- validacion fuerte de cargas `multipart/form-data` para branding en [branding_upload_service.py](/Users/jalm/Dropbox/Apps/SIPET/fastapi_modulo/modulos/web/servicios/branding_upload_service.py)
- reportes PDF de auditoria de seguridad con `reportlab` en [audit_report_service.py](/Users/jalm/Dropbox/Apps/SIPET/fastapi_modulo/modulos/web/servicios/audit_report_service.py)
