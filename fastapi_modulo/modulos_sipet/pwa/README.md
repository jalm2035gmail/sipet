# SIPET PWA — módulo real base

Esta versión deja de ser solo un cascarón PWA y ya incluye una base funcional de SIPET:

- Autenticación JWT
- PWA instalable
- Planes estratégicos
- Objetivos estratégicos
- KPIs
- Actividades y presupuesto
- Evidencias por actividad
- Dashboard resumido
- Reportes PDF/Excel

## Endpoints nuevos de SIPET

- `GET /api/v1/sipet/dashboard`
- `POST /api/v1/sipet/plans`
- `GET /api/v1/sipet/plans`
- `POST /api/v1/sipet/objectives`
- `GET /api/v1/sipet/plans/{plan_id}/objectives`
- `POST /api/v1/sipet/kpis`
- `GET /api/v1/sipet/objectives/{objective_id}/kpis`
- `POST /api/v1/sipet/activities`
- `GET /api/v1/sipet/objectives/{objective_id}/activities`
- `POST /api/v1/sipet/activities/{activity_id}/evidence`
- `GET /api/v1/sipet/activities/{activity_id}/evidence`

## Lo siguiente recomendado

1. Catálogos: áreas, responsables, sucursales, ejes, hitos.
2. Permisos por rol: director, gerente, analista, supervisor, auditor.
3. POA mensual y presupuesto por partida.
4. Comentarios, bitácora y aprobaciones.
5. Cola offline para capturar evidencias y sincronizar luego.
6. Notificaciones push y recordatorios.
7. Dashboard visual real en frontend.
