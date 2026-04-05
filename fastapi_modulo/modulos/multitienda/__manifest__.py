MANIFEST = {'name': 'multitienda',
 'label': 'Multitienda',
 'fafa': 'fa-solid fa-store',
 'summary': 'Marketplace multitienda integrable al runtime de SIPET.',
 'description': 'Marketplace multitienda integrado como módulo independiente que reutiliza autenticación, runtime y base de datos de SIPET.',
 'version': '1.1.0',
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
     'multitienda.tienda': {
         'screen_key': 'multitienda.tienda',
         'label': 'Tienda',
         'levels': {
             'full_access': {
                 'label': 'Administrador de tienda',
                 'description': 'Gestiona su tienda completa: perfil, productos, pedidos y configuración.',
             },
             'special_permissions': {
                 'label': 'Vendedor de tienda',
                 'description': 'Opera productos, pedidos e inventario de su tienda.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta la información de la tienda sin editar.',
             },
         },
     },
     'multitienda.productos': {
         'screen_key': 'multitienda.productos',
         'label': 'Productos',
         'levels': {
             'full_access': {
                 'label': 'Gestión de catálogo',
                 'description': 'Crea, edita y elimina productos, categorías, variantes e imágenes.',
             },
             'special_permissions': {
                 'label': 'Operativo de productos',
                 'description': 'Actualiza precios, inventario y estatus de productos.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta el catálogo sin editar.',
             },
         },
     },
     'multitienda.empleados': {
         'screen_key': 'multitienda.empleados',
         'label': 'Empleados',
         'levels': {
             'full_access': {
                 'label': 'Gestión de equipo',
                 'description': 'Agrega, edita y desactiva miembros del equipo de la tienda.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta el equipo sin editar.',
             },
         },
     },
     'multitienda.repartidores': {
         'screen_key': 'multitienda.repartidores',
         'label': 'Repartidores',
         'levels': {
             'full_access': {
                 'label': 'Gestión logística',
                 'description': 'Administra repartidores, asigna entregas y consulta métricas logísticas.',
             },
             'special_permissions': {
                 'label': 'Repartidor',
                 'description': 'Accede a las entregas asignadas, actualiza estado y registra evidencia.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta el panel logístico sin editar.',
             },
         },
     },
     'multitienda.configuracion': {
         'screen_key': 'multitienda.configuracion',
         'label': 'Configuración de tienda',
         'levels': {
             'full_access': {
                 'label': 'Configuración completa',
                 'description': 'Edita todos los parámetros de la tienda: horario, landing, fiscal, políticas y visibilidad.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta la configuración sin editar.',
             },
         },
     },
     'multitienda.crm': {
         'screen_key': 'multitienda.crm',
         'label': 'CRM',
         'levels': {
             'full_access': {
                 'label': 'CRM completo',
                 'description': 'Accede al CRM integrado de la tienda para contactos, oportunidades, campañas y seguimiento comercial.',
             },
             'special_permissions': {
                 'label': 'Operación CRM',
                 'description': 'Opera contactos, oportunidades y campañas sin administrar accesos globales.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta información comercial del CRM sin editar.',
             },
         },
     },
 },
 'depends': ['web', 'identidad_institucional', 'aplicaciones'],
 'integration_points': [
     {
         'section_id': 'referidos',
         'module_key': 'referidos',
         'required': False,
         'scope_query_param': 'business_slug',
     },
     {
         'section_id': 'reservaciones',
         'module_key': 'reservaciones',
         'required': False,
     },
     {
         'section_id': 'institucion_financiera',
         'module_key': 'intelicoop',
         'required': False,
     },
     {
         'section_id': 'notificaciones_pwa',
         'module_key': 'pwa',
         'required': False,
         'scope_query_param': 'business_slug',
         'target_route': '/pwa/notificaciones-tienda',
     },
     {
         'section_id': 'repartidores',
         'module_key': 'repartidores',
         'required': False,
     },
     {
         'section_id': 'subastas',
         'module_key': 'subastas',
         'required': False,
     },
     {
         'section_id': 'crm',
         'module_key': 'crm',
         'required': False,
         'target_route': '/crm',
         'scope_query_param': 'business_slug',
     },
 ],
 'data': [],
 'assets': {'css': ['marketplace/static/templates/fields-template.css'],
            'js': ['marketplace/static/js/backend-navbar.js',
                   'marketplace/static/js/backend-sidebar-core.js',
                   'marketplace/static/js/sidebar-theme-editor.js'],
            'description': ['marketplace/static/description/marketplace.svg'],
            'img': []},
 'structure': {
     'router': ['controladores/multitienda.py', 'controladores/marketplace_backend.py'],
     'backend': ['marketplace/backend/apps/', 'marketplace/backend/core/'],
     'vistas': ['vistas/'],
     'servicios': ['servicios/'],
     'tests': ['tests/'],
 },
 'installable': True,
 'application': True,
 'auto_install': False}
MANIFEST['sidebar'] = {'icon': 'fa-solid fa-store', 'label': 'Multitienda', 'route': '/multitienda'}

__all__ = ["MANIFEST"]
