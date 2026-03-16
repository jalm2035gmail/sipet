MANIFEST = {
    "name": "crm",
    "summary": "Gestion de relaciones con clientes, oportunidades, actividades y campanias.",
    "description": (
        "Modulo CRM con vista principal, endpoints API, modelos de dominio y "
        "recursos frontend para la gestion de contactos, oportunidades, "
        "actividades, notas y campanias."
    ),
    "version": "1.0.0",
    "category": "Operaciones",
    "author": "SIPET",
    "sequence": "",
    "website": "https://avancoop.org",
    "depends": ["main", "web"],
    "data": [
        "vistas/crm.html",
    ],
    "assets": {
        "css": [
            "static/css/crm.css",
        ],
        "js": [
            "static/js/crm.js",
            "static/js/crm/api.js",
            "static/js/crm/ui.js",
            "static/js/crm/contactos.js",
            "static/js/crm/oportunidades.js",
            "static/js/crm/actividades.js",
            "static/js/crm/notas.js",
            "static/js/crm/campanias.js",
            "static/js/crm/main.js",
        ],
        "description": [],
        "img": [
            "static/description/crm.svg",
        ],
    },
    "structure": {
        "router": [
            "controladores/crm.py",
            "controladores/pages.py",
            "controladores/api_contactos.py",
            "controladores/api_oportunidades.py",
            "controladores/api_actividades.py",
            "controladores/api_notas.py",
            "controladores/api_campanias.py",
            "controladores/dependencies.py",
            "controladores/utils.py",
        ],
        "schemas": [
            "modelos/crm_models.py",
            "modelos/schemas.py",
            "modelos/enums.py",
        ],
        "models": [
            "modelos/crm_db_models.py",
            "modelos/db_models.py",
        ],
        "repositories": [
            "repositorios/common.py",
            "repositorios/contacto_repository.py",
            "repositorios/oportunidad_repository.py",
            "repositorios/actividad_repository.py",
            "repositorios/nota_repository.py",
            "repositorios/campania_repository.py",
        ],
        "mappers": [
            "mappers/contacto_mapper.py",
            "mappers/oportunidad_mapper.py",
            "mappers/actividad_mapper.py",
            "mappers/nota_mapper.py",
            "mappers/campania_mapper.py",
            "mappers/contacto_campania_mapper.py",
        ],
        "service": [
            "modelos/crm_store.py",
            "servicios/contacto_service.py",
            "servicios/oportunidad_service.py",
            "servicios/actividad_service.py",
            "servicios/nota_service.py",
            "servicios/campania_service.py",
            "servicios/dashboard_service.py",
            "bootstrap.py",
        ],
        "tests": [
            "test_crm_phase6.py",
        ],
        "docs": [
            "README.md",
            "fase_2_arquitectura_modelo_datos.md",
        ],
        "frontend": [
            "static/css/crm.css",
            "static/js/crm.js",
            "static/js/crm/api.js",
            "static/js/crm/ui.js",
            "static/js/crm/contactos.js",
            "static/js/crm/oportunidades.js",
            "static/js/crm/actividades.js",
            "static/js/crm/notas.js",
            "static/js/crm/campanias.js",
            "static/js/crm/main.js",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}

__all__ = ["MANIFEST"]
