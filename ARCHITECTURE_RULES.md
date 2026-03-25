# Reglas De Arquitectura De Modulos

Estas reglas aplican a modulos nuevos y a refactorizaciones relevantes de modulos existentes.

## 1. Base de datos

- Un modulo tenant debe usar la BD resuelta por request.
- El acceso normal a datos debe hacerse con `core_db.SessionLocal()`, `core_db.get_session_factory_for_host()` o helpers/repositorios que ya usen esa ruta.
- No se permite crear engines o sesiones SQLAlchemy ad hoc dentro del modulo con `create_engine()` o `sessionmaker()` salvo en tests aislados.
- No se permite usar `get_session_factory_for_host("")`, `get_engine_for_host("")` ni `get_current_database_info("")` dentro de flujo tenant.
- Si un modulo necesita datos globales o administrativos, debe usar la API explicita de admin: `get_admin_engine()`, `get_admin_session_factory()` o `AdminSessionLocal()`.
- Si un modulo define tablas propias, su bootstrap debe ser idempotente y depender de la BD efectiva del sitio.

## 2. Manifest y estructura

- Cada modulo debe tener `__manifest__.py` con un `MANIFEST` valido.
- Claves requeridas: `name`, `label`, `summary`, `version`, `depends`, `route`, `installable`, `application`.
- Las rutas declaradas en `structure` y `assets` deben existir.
- El modulo debe declarar dependencias minimas reales en `depends`.

## 3. Frontend y estilos

- No usar `https://cdn.tailwindcss.com` ni otras inyecciones runtime de Tailwind.
- Las clases Tailwind en templates deben ser estaticas; no usar patrones tipo `text-{{ tone }}`, `bg-{{ color }}`, `alert-{{ kind }}`.
- Los assets CSS y JS del modulo deben declararse en el `MANIFEST` cuando correspondan.
- Si el modulo vive dentro del backend comun, debe respetar tokens y componentes compartidos antes de introducir CSS paralelo.

## 4. Calidad minima

- El modulo debe tener al menos una ruta de prueba automatizada o tests propios.
- No debe depender de rutas o archivos legacy fuera de su directorio sin una razon explicita.
- Debe usar imports absolutos del proyecto y evitar duplicar infraestructura ya presente en `fastapi_modulo.core`.

## 5. Regla operativa

- Antes de integrar un modulo nuevo, ejecutar:

```bash
python3 scripts/validate_module_architecture.py /ruta/al/modulo
```

- Si el validador reporta `ERROR`, el modulo no debe darse de alta.
- Los `WARN` deben revisarse manualmente y justificarse si se aceptan.
