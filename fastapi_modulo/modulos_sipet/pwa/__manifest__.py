MANIFEST = {
    "name": "pwa",
    "label": "Progressive Web App",
    "summary": "Módulo PWA para SIPET construido con FastAPI y Python.",
    "description": (
        "Módulo que transforma SIPET en una Progressive Web App (PWA) con soporte "
        "offline, service worker, manifest web, instalación nativa y caché avanzado."
    ),
    "version": "1.0.0",
    "category": "Web",
    "author": "SIPET",
    "sequence": "900",
    "website": "https://avancoop.org",
    "route": "/",
    "routes": [
        "/",
        "/login",
        "/register",
        "/offline",
        "/manifest.webmanifest",
        "/sw.js",
        "/favicon.ico",
        "/api/v1/auth",
        "/api/v1/users",
        "/api/v1/ml",
        "/api/v1/reports",
        "/api/v1/sipet",
    ],
    "api_prefix": "/api/v1",
    "icon": "fa-solid fa-mobile-screen",
    "depends": ["web"],
    "external_dependencies": {
        "python": ["fastapi", "sqlalchemy", "alembic"],
    },
    "data": [
        "README.md",
        "app/templates/pages/index.html",
        "app/templates/pages/login.html",
        "app/templates/pages/register.html",
        "app/templates/pages/offline.html",
    ],
    "assets": {
        "css": [
            "static/css/main.css",
        ],
        "js": [
            "static/js/app.js",
            "static/js/sw.js",
        ],
        "description": [],
        "img": [
            "static/icons/icon-192x192.png",
            "static/icons/icon-512x512.png",
        ],
    },
    "pwa": {
        "manifest": "static/manifest.json",
        "service_worker": "static/js/sw.js",
        "icons_dir": "static/icons",
    },
    "structure": {
        "router": [
            "app/api/v1/routers/auth.py",
            "app/api/v1/routers/users.py",
            "app/api/v1/routers/ml.py",
            "app/api/v1/routers/reports.py",
            "app/api/v1/routers/sipet.py",
        ],
        "models": [
            "models/",
        ],
        "migrations": [
            "migrations/",
        ],
        "services": [
            "app/services/",
        ],
        "repositories": [
            "app/repositories/",
        ],
        "tests": [
            "tests/",
        ],
    },
    "schema": {
        "uses_migrations": True,
        "alembic_required_in_production": True,
        "allow_create_all_in_dev": True,
        "requires_data_bootstrap": False,
        "requires_seeds": False,
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}

__all__ = ["MANIFEST"]
