MANIFEST = {
    'name': 'reservaciones',
    'label': 'Reservaciones',
    'fafa': 'fa-solid fa-calendar-check',
    'summary': 'Sistema de gestión de citas y reservaciones.',
    'description': 'Agenda citas con ejecutivos, gestiona disponibilidad y calendario de atención.',
    'version': '1.0.0',
    'category': 'Operaciones',
    'author': 'SIPET',
    'sequence': '320',
    'website': 'https://avancoop.org',
    'route': '/reservaciones',
    'icon': 'fa-solid fa-calendar-check',
    'screen_access_levels': {
        'reservaciones': {
            'screen_key': 'reservaciones',
            'label': 'Reservaciones',
            'levels': {
                'full_access': {'label': 'Administrador', 'description': 'Acceso completo al módulo de reservaciones.'},
                'special_permissions': {'label': 'Ejecutivo', 'description': 'Gestiona citas asignadas a su perfil.'},
                'read_only': {'label': 'Solo lectura', 'description': 'Solo puede consultar citas y ejecutivos.'},
            },
        },
    },
    'depends': ['web'],
    'data': ['vistas/reservaciones.html'],
    'assets': {
        'css': ['static/css/reservaciones.css'],
        'description': ['static/description/reservaciones.svg'],
        'img': [],
    },
    'structure': {
        'router': ['controladores/reservaciones.py'],
        'models': ['modelos/db_models.py', 'modelos/schemas.py', 'modelos/store.py'],
        'views': ['vistas/reservaciones.html'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}

__all__ = ["MANIFEST"]
