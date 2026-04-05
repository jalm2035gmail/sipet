MANIFEST = {
    'name': 'repartidores',
    'label': 'Repartidores',
    'summary': 'Gestión logística de repartidores, entregas, incidencias y liquidaciones.',
    'description': 'Módulo SIPET para administrar repartidores, zonas, vehículos, entregas y control operativo de última milla.',
    'version': '1.0.0',
    'category': 'Operaciones',
    'author': 'SIPET',
    'sequence': '330',
    'website': 'https://avancoop.org',
    'route': '/repartidores',
    'icon': 'fa-solid fa-truck-fast',
    'screen_access_levels': {
        'repartidores': {
            'screen_key': 'repartidores',
            'label': 'Repartidores',
            'levels': {
                'full_access': {'label': 'Administrador', 'description': 'Acceso completo al módulo de repartidores.'},
                'special_permissions': {'label': 'Supervisor logístico', 'description': 'Puede gestionar repartidores, asignar entregas y generar liquidaciones.'},
                'delivery_access': {'label': 'Repartidor', 'description': 'Puede consultar sus entregas y actualizar estatus operativos.'},
                'read_only': {'label': 'Solo lectura', 'description': 'Consulta tableros, entregas y repartidores sin editar.'},
            },
        },
    },
    'depends': ['web'],
    'data': ['vistas/repartidores.html'],
    'assets': {
        'css': ['static/css/repartidores.css'],
        'js': ['static/js/repartidores.js'],
        'description': ['static/description/repartidores.svg'],
        'img': [],
    },
    'structure': {
        'router': ['controladores/repartidores.py'],
        'models': ['modelos/db_models.py', 'modelos/schemas.py', 'modelos/store.py'],
        'views': ['vistas/repartidores.html'],
    },
    'sipet_relation': {
        'ecosystem': 'sipet',
        'integrates_with': ['web', 'usuarios', 'sucursales', 'clientes', 'pedidos', 'analitica'],
        'module_type': 'operacion_logistica',
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}

__all__ = ['MANIFEST']
