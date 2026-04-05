MANIFEST = {
    'name': 'tortas',
    'label': 'Restaurante',
    'fafa': 'fa-solid fa-utensils',
    'summary': 'Sistema de gestión integral de restaurante y comida.',
    'description': 'Gestión de pedidos, menú, modificadores, bases del producto, canales de venta, cupones, corte de caja y preórdenes. Adaptable a tortas, pizzas, sushi, hamburguesas, ensaladas y cualquier concepto gastronómico.',
    'version': '2.0.0',
    'category': 'Operaciones',
    'author': 'SIPET',
    'sequence': '330',
    'website': 'https://avancoop.org',
    'route': '/tortas',
    'icon': 'fa-solid fa-utensils',
    'screen_access_levels': {
        'tortas': {
            'screen_key': 'tortas',
            'label': 'Restaurante',
            'levels': {
                'full_access': {'label': 'Administrador', 'description': 'Acceso completo al módulo de restaurante.'},
                'special_permissions': {'label': 'Cajero / Operador', 'description': 'Gestiona pedidos y pagos.'},
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
