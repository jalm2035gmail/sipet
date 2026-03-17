MANIFEST = {
    "name": "modulo_base",
    "summary": "Plantilla base reutilizable para modulos SIPET.",
    "description": (
        "Framework interno de modulos SIPET con contratos reutilizables para "
        "configuracion, rutas, servicios, repositorios, permisos, assets, "
        "respuestas y migraciones Alembic."
    ),
    "version": "1.0.0",
    "category": "Base",
    "author": "SIPET",
    "sequence": "200",
    "website": "https://avancoop.org",
    "route": "/modulo-base",
    "routes": [
        "/modulo-base",
        "/api/modulo-base/health",
        "/api/modulo-base/resumen",
        "/api/modulo-base/assets/modulo_base.css",
        "/api/modulo-base/assets/modulo_base.js",
    ],
    "api_prefix": "/api/modulo-base",
    "icon": "fa-solid fa-layer-group",
    "depends": ["main", "web"],
    "menu": {
        "label": "Modulo base",
        "icon": "fa-solid fa-layer-group",
        "sequence": 200,
        "route": "/modulo-base",
    },
    "submenus": [
        {
            "label": "Resumen",
            "route": "/modulo-base",
            "sequence": 1,
        }
    ],
    "permissions": [
        "modulo_base.ver",
        "modulo_base.crear",
        "modulo_base.editar",
        "modulo_base.eliminar",
        "modulo_base.exportar",
        "modulo_base.aprobar",
        "modulo_base.configurar",
        "modulo_base.administrar",
        "modulo_base.auditoria",
    ],
    "data": [
        "seguridad/permisos.json",
        "vistas/base_page.html",
        "vistas/navbar.html",
        "vistas/sidebar.html",
        "README.md",
    ],
    "assets": {
        "css": [
            "static/css/modulo_base.css",
        ],
        "js": [
            "static/js/modulo_base.js",
        ],
        "description": [
            "static/description/modulo_base.svg",
        ],
        "img": [],
    },
    "widgets": [],
    "structure": {
        "router": [
            "controladores/modulo_base.py",
            "controladores/pages.py",
            "controladores/api.py",
            "controladores/assets.py",
            "controladores/dependencies.py",
        ],
        "core": [
            "core/audit.py",
            "core/module.py",
            "core/ml_service.py",
            "core/router.py",
            "core/service.py",
            "core/repository.py",
            "core/permissions.py",
            "core/assets.py",
            "core/cache_service.py",
            "core/http_service.py",
            "core/lock_service.py",
            "core/media_service.py",
            "core/responses.py",
            "core/security.py",
            "core/visual_editor_service.py",
        ],
        "migrations": [
            "migrations/README.md",
            "migrations/versions/.gitkeep",
        ],
        "models": [
            "modelos/db_models.py",
            "modelos/schemas.py",
            "modelos/enums.py",
        ],
        "repositories": [
            "repositorios/base_repository.py",
            "repositorios/common.py",
        ],
        "services": [
            "servicios/base_service.py",
            "servicios/cache_service.py",
            "servicios/http_service.py",
            "servicios/lock_service.py",
            "servicios/media_service.py",
            "servicios/ml_service.py",
            "servicios/security_service.py",
            "servicios/task_queue_service.py",
            "servicios/visual_editor_service.py",
        ],
        "ml": [
            "ml/README.md",
            "ml/models/.gitkeep",
            "ml/pipelines/.gitkeep",
            "ml/artifacts/.gitkeep",
        ],
        "visual": [
            "visual/README.md",
            "visual/landing/.gitkeep",
            "visual/presentations/.gitkeep",
            "visual/widgets/.gitkeep",
            "visual/forms/.gitkeep",
        ],
        "tasks": [
            "tareas/__init__.py",
            "tareas/celery_app.py",
            "tareas/sync_tasks.py",
            "tareas/report_tasks.py",
        ],
        "security": [
            "seguridad/permisos.json",
            "core/security.py",
            "servicios/security_service.py",
        ],
        "tests": [
            "tests/test_modulo_base.py",
        ],
    },
    "events": [],
    "schema": {
        "uses_migrations": True,
        "alembic_required_in_production": True,
        "allow_create_all_in_dev": True,
        "requires_data_bootstrap": False,
        "requires_seeds": False,
    },
    "tasks": [
        "modulo_base.protocol_sync",
        "modulo_base.report_export",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

__all__ = ["MANIFEST"]
