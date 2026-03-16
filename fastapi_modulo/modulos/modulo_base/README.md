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
