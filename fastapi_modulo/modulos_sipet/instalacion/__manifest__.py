MANIFEST = {
    "name": "instalacion",
    "label": "Instalación",
    "summary": "Bootstrap inicial de SIPET para preparar sipet.conf y la base de datos.",
    "description": (
        "Módulo técnico para la primera ejecución de SIPET. "
        "Guía la preparación de sipet.conf, la base principal y el seed mínimo del sistema."
    ),
    "version": "1.0.0",
    "category": "Base",
    "author": "SIPET",
    "sequence": "1",
    "website": "https://avancoop.org",
    "route": "/instalacion",
    "icon": "fa-solid fa-screwdriver-wrench",
    "depends": ["web"],
    "data": [],
    "assets": {"css": [], "js": [], "description": [], "img": []},
    "structure": {
        "router": ["controladores/instalacion.py"],
        "services": ["servicios/installer_service.py"],
    },
    "installable": True,
    "application": False,
    "auto_install": True,
}

__all__ = ["MANIFEST"]
