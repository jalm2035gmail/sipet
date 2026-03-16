MANIFEST = {
    "name": "web",
    "summary": "Servicios web compartidos para modulos SIPET.",
    "description": (
        "Modulo tecnico inspirado en Odoo para centralizar logica compartida "
        "de acceso, render backend y entrega de assets entre modulos SIPET."
    ),
    "version": "1.0.0",
    "category": "Base",
    "author": "SIPET",
    "sequence": "100",
    "website": "https://avancoop.org",
    "depends": ["main"],
    "data": [
        "README.md",
        "vistas/backend_nav_catalog.html",
        "vistas/backend_shell_script.html",
        "vistas/navbar.html",
        "vistas/sidebar.html",
        "vistas/sidebar_icons.html",
        "vistas/partials/floating_actions.html",
        "vistas/partials/navbar.html",
        "vistas/partials/page_shell.html",
        "vistas/partials/sidebar.html",
    ],
    "assets": {
        "css": ["static/css/backend_shell.css"],
        "js": [],
        "description": [],
        "img": [],
    },
    "structure": {
        "router": [
            "controladores/__init__.py",
            "controladores/backend_auth.py",
            "controladores/backend_shell.py",
        ],
        "views": [
            "vistas/backend_nav_catalog.html",
            "vistas/backend_shell_script.html",
            "vistas/navbar.html",
            "vistas/sidebar.html",
            "vistas/sidebar_icons.html",
            "vistas/partials/floating_actions.html",
            "vistas/partials/navbar.html",
            "vistas/partials/page_shell.html",
            "vistas/partials/sidebar.html",
        ],
        "services": [
            "servicios/module_tools.py",
        ],
        "tests": [
            "tests/test_module_tools.py",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}

__all__ = ["MANIFEST"]
