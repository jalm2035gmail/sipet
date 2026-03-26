MANIFEST = {
    'name': 'tortas',
    'label': 'Tortas',
    'fafa': 'fa-solid fa-bread-slice',
    'summary': 'Sistema de gestión integral de negocio de tortas.',
    'description': 'Gestión de pedidos, menú, toppings, tipos de pan, cupones, corte de caja y preordenes.',
    'version': '1.0.0',
    'category': 'Operaciones',
    'author': 'SIPET',
    'sequence': '330',
    'website': 'https://avancoop.org',
    'route': '/tortas',
    'icon': 'fa-solid fa-bread-slice',
    'screen_access_levels': {
        'tortas': {
            'screen_key': 'tortas',
            'label': 'Tortas',
            'levels': {
                'full_access': {'label': 'Administrador', 'description': 'Acceso completo al módulo de tortas.'},
                'special_permissions': {'label': 'Cajero', 'description': 'Gestiona pedidos y pagos.'},
                'read_only': {'label': 'Solo lectura', 'description': 'Solo puede consultar información.'},
            },
        },
    },
    'depends': ['web'],
    'data': ['vistas/tortas.html'],
    'assets': {
        'css': ['static/css/tortas.css'],
        'description': ['static/description/tortas.svg'],
        'img': [],
    },
    'structure': {
        'router': ['controladores/tortas.py'],
        'models': ['modelos/db_models.py', 'modelos/schemas.py', 'modelos/store.py'],
        'views': ['vistas/tortas.html'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}

__all__ = ["MANIFEST"]
