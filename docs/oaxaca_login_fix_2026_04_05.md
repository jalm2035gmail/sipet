# Oaxaca Login Fix 2026-04-05

Incidente observado en `oaxaca.tunegociovale.com` despues de deploy:

- `POST /backend/login` con `0konomiyaki` respondia `303` a `/base_datos/inicializar`
- el journal mostraba `UndefinedColumn: column users.app_access does not exist`

## Causa

La base `sipet_oaxaca` no tenia aplicadas las columnas nuevas del modulo web en `users`:

- `app_access`
- `menu_blocks`
- `conversation_access`
- `is_employee`

El arbol de migraciones Alembic del servidor tambien estaba desalineado con esa base:

- multiples heads
- `alembic/env.py` requiere escapar `%` en `DATAMAIN_URL`
- una rama de migraciones intentaba aplicar FKs contra `departments`, tabla inexistente en esta base

## Fix operativo aplicado en produccion

Se agregaron manualmente las columnas faltantes:

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS app_access TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS menu_blocks TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS conversation_access TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_employee BOOLEAN NOT NULL DEFAULT FALSE;
```

Despues del reinicio del servicio, el login tecnico respondio correctamente:

- `HTTP/1.1 303 See Other`
- `Location: /inicio`

## Ajuste en repositorio

La migracion `fastapi_modulo/modulos_sipet/web/alembic/versions/20260402_0004_web_users_empresa_access_fields.py`
se dejo idempotente para tolerar bases donde las columnas ya fueron creadas manualmente.

## Recomendaciones

- No ejecutar `alembic upgrade heads` en produccion sin revisar primero la rama de migraciones activa.
- Si se necesita correr Alembic con password URL-encoded, exportar `DATAMAIN_URL` con `%%` en lugar de `%`.
- Antes de un deploy productivo, validar que `users` tenga las columnas esperadas por el codigo web actual.
