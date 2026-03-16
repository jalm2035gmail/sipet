MANIFEST = {
    "name": "mi_tablero",
    "fafa": "fa-solid fa-rectangle-list",
    "label": "Mi tablero",
    "summary": "Vista personal y accesos rapidos del usuario.",
    "description": "Modulo independiente para la portada operativa y accesos directos del usuario.",
    "version": "1.0.0",
    "category": "Base",
    "author": "SIPET",
    "sequence": "001",
    "website": "https://avancoop.org",
    "route": "/mi-tablero",
    "icon": "fa-solid fa-rectangle-list",
    "depends": ["main", "web"],
    "data": [
        "vistas/mi_tablero.html",
    ],
    "assets": {
        "css": [
            "static/css",
        ],
        "js": [
            "static/js",
        ],
        "description": [],
        "img": [
            "static/widgets",
        ],
    },
    "structure": {
        "router": [
            "controladores/__init__.py",
            "controladores/dashboard_pages.py",
            "controladores/dashboard_api.py",
            "controladores/dashboard_security.py",
            "controladores/mi_tablero.py",
        ],
        "services": [
            "servicios/__init__.py",
            "servicios/dashboard_service.py",
            "servicios/preference_service.py",
            "servicios/analytics_service.py",
            "servicios/integration_service.py",
            "servicios/widget_service.py",
        ],
        "repositories": [
            "repositorios/dashboard_repository.py",
            "repositorios/preference_repository.py",
        ],
        "models": [
            "modelos/db_models.py",
            "modelos/schemas.py",
            "modelos/enums.py",
        ],
        "tasks": [
            "tareas/dashboard_tasks.py",
        ],
        "ml": [
            "ml/recommender_model.py",
        ],
        "reports": [
            "reports/dashboard_report.py",
        ],
        "views": [
            "vistas/mi_tablero.html",
            "vistas/widgets",
        ],
        "static": [
            "static/css",
            "static/js",
            "static/widgets",
        ],
        "tests": [
            "tests/test_mi_tablero.py",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}

__all__ = ["MANIFEST"]
