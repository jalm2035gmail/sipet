MANIFEST = {'name': 'mkt',
 'label': 'MKT',
 'fafa': 'fa-solid fa-bullhorn',
 'summary': 'Marketing y comunicación.',
 'description': 'Marketing y comunicación.',
 'version': '1.0.0',
 'category': 'Operaciones',
 'author': 'SIPET',
 'sequence': '',
 'website': 'https://avancoop.org',
 'route': '/mkt/digital',
 'icon': 'fa-solid fa-bullhorn',
 'screen_access_levels': {
     'mkt': {
         'screen_key': 'mkt',
         'label': 'MKT',
         'levels': {
             'full_access': {
                 'label': 'Administrador de MKT',
                 'description': 'Acceso completo al módulo de marketing y sus pantallas.',
             },
             'special_permissions': {
                 'label': 'Editor de MKT',
                 'description': 'Gestiona contenido y campañas sin control administrativo total.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta tableros y configuraciones sin editar.',
             },
         },
     },
     'mkt.digital': {
         'screen_key': 'mkt.digital',
         'label': 'MKT digital',
         'levels': {
             'full_access': {
                 'label': 'Gestión completa',
                 'description': 'Emailing, automatización y seguimiento de campañas digitales.',
             },
             'special_permissions': {
                 'label': 'Editor',
                 'description': 'Edita piezas y campañas sin administrar accesos globales.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta campañas y métricas sin cambios.',
             },
         },
     },
     'mkt.whatsapp_business': {
         'screen_key': 'mkt.whatsapp_business',
         'label': 'WhatsApp Business',
         'levels': {
             'full_access': {
                 'label': 'Gestión completa',
                 'description': 'Administra atención, plantillas y campañas conversacionales.',
             },
             'special_permissions': {
                 'label': 'Editor',
                 'description': 'Gestiona mensajes y catálogos sin administrar accesos globales.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta conversaciones y plantillas sin editar.',
             },
         },
     },
     'mkt.redes_sociales': {
         'screen_key': 'mkt.redes_sociales',
         'label': 'Redes sociales',
         'levels': {
             'full_access': {
                 'label': 'Gestión completa',
                 'description': 'Administra contenidos, calendario y campañas de redes sociales.',
             },
             'special_permissions': {
                 'label': 'Editor',
                 'description': 'Edita publicaciones y programación sin administrar accesos globales.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta publicaciones, agenda y métricas sin cambios.',
             },
         },
     },
 },
 'depends': ['main'],
 'data': ['vistas/mkt_digital.html', 'vistas/redes_sociales.html', 'vistas/whatsapp_business.html'],
 'assets': {'css': [], 'js': [], 'description': ['static/description/mkt.svg'], 'img': []},
 'structure': {'router': ['controladores/mkt.py'],
               'views': ['vistas/mkt_digital.html',
                         'vistas/redes_sociales.html',
                         'vistas/whatsapp_business.html']},
 'installable': True,
 'application': True,
 'auto_install': False}

__all__ = ["MANIFEST"]
