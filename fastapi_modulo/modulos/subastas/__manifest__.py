MANIFEST = {
    "name": "subastas",
    "label": "Subastas",
    "summary": "Módulo de subastas con lotes, postores, pujas, adjudicación y pagos.",
    "description": "Gestión integral de subastas alineada al runtime de SIPET, manteniendo su lógica y datos independientes.",
    "version": "1.0.0",
    "category": "Comercial / Operaciones",
    "author": "SIPET",
    "sequence": "330",
    "website": "https://avancoop.org",
    "route": "/subastas",
    "icon": "fa-solid fa-gavel",
    "screen_access_levels": {
        "subastas": {
            "screen_key": "subastas",
            "label": "Subastas",
            "levels": {
                "full_access": {
                    "label": "Administrador",
                    "description": "Administra subastas, lotes, postores, adjudicaciones y pagos.",
                },
                "special_permissions": {
                    "label": "Operador",
                    "description": "Opera subastas y seguimiento operativo sin administrar accesos globales.",
                },
                "read_only": {
                    "label": "Solo lectura",
                    "description": "Consulta subastas, pujas y entregas sin editar información.",
                },
            },
        },
    },
    "depends": ["web"],
    "data": ["vistas/subastas.html"],
    "assets": {
        "css": ["static/css/subastas.css"],
        "js": ["static/js/subastas.js"],
        "description": [],
        "img": [],
    },
    "structure": {
        "router": ["controladores/subastas.py"],
        "models": [
            "modelos/db_models.py",
            "modelos/schemas.py",
            "modelos/store.py",
            "modelos/scheduler.py",
        ],
        "views": ["vistas/subastas.html"],
        "tests": ["tests/"],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}

__all__ = ["MANIFEST"]
