MANIFEST = {
    'name': 'referidos',
    'label': 'Referidos',
    'summary': 'Programa integral de referidos y embajadores de marca.',
    'description': 'Gestión del ciclo de vida de referidos, incentivos y embajadores.',
    'version': '1.0.0',
    'category': 'Comercial',
    'author': 'SIPET',
    'sequence': '310',
    'website': 'https://avancoop.org',
    'route': '/referidos',
    'icon': 'fa-solid fa-users',
    'depends': ['web'],
    'data': ['vistas/referidos.html'],
    'assets': {
        'css': ['static/css/referidos.css'],
        'js': ['static/js/referidos.js'],
        'description': ['static/description/referidos.svg'],
        'img': []
    },
    'structure': {
        'router': ['controladores/referidos.py'],
        'models': [
            'modelos/db_models.py',
            'modelos/schemas.py',
            'modelos/store.py',
        ],
        'views': ['vistas/referidos.html']
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}

__all__ = ["MANIFEST"]
