MANIFEST = {
    "name": "aplicaciones",
    "label": "Gobierno de Aplicaciones",
    "summary": "Catalogo institucional, operacion de modulos, paquetes y auditoria del protocolo.",
    "description": (
        "Modulo de gobierno de aplicaciones para catalogar modulos, controlar su estado, "
        "administrar paquetes instalables y auditar el protocolo __init__.py y __manifest__.py."
    ),
    "version": "1.2.0",
    "category": "Base",
    "author": "SIPET",
    "sequence": "",
    "website": "https://avancoop.org",
    "route": "/aplicaciones",
    "icon": "fa-solid fa-cubes",
    "depends": ["main", "web"],
    "data": [
        "README.md",
        "vistas/aplicaciones.html",
    ],
    "assets": {
        "css": ["static/css/aplicaciones.css"],
        "js": ["static/js/aplicaciones.js"],
        "description": [],
        "img": [],
    },
    "structure": {
        "router": [
            "controladores/aplicaciones.py",
            "controladores/pages.py",
            "controladores/api_protocol.py",
            "controladores/api_packages.py",
            "controladores/api_security.py",
            "controladores/api_state.py",
            "controladores/dependencies.py",
        ],
        "models": [
            "modelos/db_models.py",
            "modelos/schemas.py",
            "modelos/enums.py",
        ],
        "repositories": [
            "repositorios/app_repository.py",
            "repositorios/audit_repository.py",
            "repositorios/package_repository.py",
            "repositorios/persistence_repository.py",
        ],
        "services": [
            "servicios/catalog_service.py",
            "servicios/protocol_service.py",
            "servicios/package_service.py",
            "servicios/audit_service.py",
            "servicios/state_service.py",
            "servicios/security_service.py",
        ],
        "views": [
            "vistas/aplicaciones.html",
        ],
        "tests": [
            "tests/test_protocol_service.py",
            "tests/test_persistence_repository.py",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}

__all__ = ["MANIFEST"]
