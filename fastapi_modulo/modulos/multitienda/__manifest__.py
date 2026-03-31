MANIFEST = {'name': 'multitienda',
 'label': 'Multitienda',
 'fafa': 'fa-solid fa-store',
 'summary': 'Marketplace multitienda integrable al runtime de SIPET.',
 'description': 'Marketplace multitienda integrado como módulo independiente que reutiliza autenticación, runtime y base de datos de SIPET.',
 'version': '1.0.0',
 'category': 'Operaciones',
 'author': 'SIPET',
 'sequence': '300',
 'website': 'https://avancoop.org',
 'route': '/multitienda',
 'icon': 'fa-solid fa-store',
 'screen_access_levels': {
     'multitienda': {
         'screen_key': 'multitienda',
         'label': 'Multitienda',
         'levels': {
             'full_access': {
                 'label': 'Administrador',
                 'description': 'Administra por completo el marketplace, configuración, catálogos y operación comercial.',
             },
             'special_permissions': {
                 'label': 'Gestor comercial',
                 'description': 'Opera el marketplace y gestiona tiendas, productos y pedidos sin administrar accesos globales.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta tiendas, pedidos y métricas del marketplace sin editar información.',
             },
         },
     },
     'multitienda.gestion': {
         'screen_key': 'multitienda.gestion',
         'label': 'Gestión del marketplace',
         'levels': {
             'full_access': {
                 'label': 'Gestión completa',
                 'description': 'Accede a panel administrativo, configuración, vendedores y operación del marketplace.',
             },
             'special_permissions': {
                 'label': 'Operador',
                 'description': 'Gestiona operación comercial y seguimiento de tiendas sin administrar seguridad global.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta el panel y la operación del marketplace sin realizar cambios.',
             },
         },
     },
 },
 'depends': ['web', 'identidad_institucional', 'aplicaciones'],
 'data': [],
 'assets': {'css': ['marketplace/static/templates/fields-template.css'],
            'js': ['marketplace/static/js/backend-navbar.js',
                   'marketplace/static/js/backend-sidebar-core.js',
                   'marketplace/static/js/sidebar-theme-editor.js'],
            'description': ['marketplace/static/description/marketplace.svg'],
            'img': []},
 'structure': {'router': ['controladores/multitienda.py', 'controladores/marketplace_backend.py'],
               'backend': ['marketplace/backend/apps/', 'marketplace/backend/core/']},
 'installable': True,
 'application': True,
 'auto_install': False}
MANIFEST['sidebar'] = {'icon': 'fa-solid fa-store', 'label': 'Multitienda', 'route': '/multitienda'}

__all__ = ["MANIFEST"]
