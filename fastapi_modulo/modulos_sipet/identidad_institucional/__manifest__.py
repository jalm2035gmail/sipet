MANIFEST = {'name': 'identidad_institucional',
 'label': 'Personalización',
 'summary': 'Personalización institucional y estructura visual principal.',
 'description': 'Personalización institucional y estructura visual principal.',
 'version': '1.0.0',
 'category': 'Operaciones',
 'author': 'SIPET',
 'sequence': '400',
 'website': 'https://avancoop.org',
 'route': '/identidad-institucional',
 'icon': 'fa-solid fa-building',
 'fafa': 'fa-solid fa-building',
 'depends': ['web'],
 'data': [],
 'assets': {'css': ['static/css/identidad_institucional.css'],
            'js': [],
            'description': ['static/description/identidad.svg'],
            'img': []},
 'structure': {'router': ['controladores/__init__.py',
                          'controladores/identidad_institucional.py',
                          'controladores/branding.py',
                          'controladores/empresa_usuarios.py',
                          'controladores/empresa_accesos.py'],
               'services': ['servicios/__init__.py',
                            'servicios/identidad_service.py',
                            'servicios/usuarios_empresa_service.py',
                            'servicios/acceso_empresa_service.py'],
               'tests': ['tests/test_identidad_institucional_module_contract.py',
                         'tests/test_identidad_institucional_services.py']},
 'screen_access_levels': {
     'empresa': {
         'screen_key': 'empresa',
         'label': 'Empresa',
         'levels': {
             'full_access': {
                 'label': 'Administrador',
                 'description': 'Acceso total: branding, usuarios, datos y plantillas.',
             },
             'special_permissions': {
                 'label': 'Editor',
                 'description': 'Branding y plantillas sin gestión de usuarios.',
             },
             'department_only': {
                 'label': 'Gestor de usuarios',
                 'description': 'Gestión de usuarios sin acceso a branding.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta sin capacidad de edición.',
             },
         },
     },
     'empresa.usuarios': {
         'screen_key': 'empresa.usuarios',
         'label': 'Usuarios, roles y acceso',
         'levels': {
             'full_access': {
                 'label': 'Administrador de usuarios',
                 'description': 'Crear, editar y eliminar usuarios. Asignar roles y permisos. Ver roles y niveles de acceso.',
             },
             'special_permissions': {
                 'label': 'Editor de usuarios',
                 'description': 'Crear y editar usuarios sin gestión de roles avanzada.',
             },
             'department_only': {
                 'label': 'Gestor departamental',
                 'description': 'Gestionar usuarios de su propio departamento.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consultar el directorio de usuarios sin editar.',
             },
         },
     },
     'empresa.roles': {
         'screen_key': 'empresa.roles',
         'label': 'Roles',
         'levels': {
             'full_access': {
                 'label': 'Administrador de roles',
                 'description': 'Configurar perfiles base de roles y permisos.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Ver la configuración de roles sin modificarla.',
             },
         },
     },
     'empresa.acceso': {
         'screen_key': 'empresa.acceso',
         'label': 'Niveles de acceso',
         'levels': {
             'full_access': {
                 'label': 'Administrador de acceso',
                 'description': 'Configurar perfiles de rol y niveles de acceso por módulo.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Ver la configuración de acceso sin modificarla.',
             },
         },
     },
 },
 'installable': True,
 'application': True,
 'auto_install': False}

__all__ = ["MANIFEST"]
