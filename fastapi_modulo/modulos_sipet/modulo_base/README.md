# Modulo Base

Plantilla base para crear modulos SIPET con estructura inspirada en Odoo.

## Objetivo

- Estandarizar la estructura de nuevos modulos.
- Reducir dependencias implícitas con `main.py`.
- Servir como referencia técnica para manifests, routers, modelos, servicios, vistas y pruebas.

## Estructura

- `__manifest__.py`
- `bootstrap.py`
- `controladores/`
- `modelos/`
- `repositorios/`
- `servicios/`
- `seguridad/`
- `static/`
- `vistas/`
- `tests/`

## Uso recomendado

1. Copiar `modulo_base` a un nuevo directorio de modulo.
2. Renombrar rutas, manifest, permiso y assets.
3. Sustituir `ModuloBaseRegistro` por modelos del dominio real.
4. Registrar el router nuevo en `module_registry.py`.

## Contrato FastAPI

- `APIRouter` raiz con `lifespan` y dependencia global de acceso en `controladores/modulo_base.py`.
- `Depends` reutilizables para contexto y `tenant_id` en `controladores/dependencies.py`.
- `response_model` y sobres JSON tipados en `modelos/schemas.py`.
- Manejo uniforme de errores y validaciones en `core/exceptions.py`.
- `BackgroundTasks` para trabajo no bloqueante cuando la ruta lo necesite.
