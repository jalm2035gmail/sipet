MANIFEST = {'name': 'frontend',
 'label': 'Web',
 'summary': 'Sitio web público y constructor.',
 'description': 'Sitio web público y constructor.',
 'version': '1.0.0',
 'category': 'Operaciones',
 'author': 'SIPET',
 'sequence': '200',
 'website': 'https://avancoop.org',
 'route': '/frontend/builder',
 'icon': 'fa-solid fa-globe',
 'fafa': 'fa-solid fa-globe',
 'depends': ['web'],
 'data': ['vistas/frontend.html'],
 'assets': {'css': [], 'js': [], 'description': ['static/description/web.svg'], 'img': []},
 'structure': {'router': ['controladores/frontend.py'],
               'models': ['modelos/frontend_db_models.py', 'modelos/frontend_store.py'],
               'views': ['vistas/frontend.html']},
 'screen_access_levels': {
     'Frontend': {
         'screen_key': 'Frontend',
         'label': 'Web',
         'levels': {
             'full_access': {
                 'label': 'Administrador',
                 'description': 'Acceso total al constructor, páginas, publicaciones y recursos del frontend.',
             },
             'special_permissions': {
                 'label': 'Editor',
                 'description': 'Puede diseñar, editar y publicar páginas del frontend.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Puede ver el módulo sin modificar contenido.',
             },
         },
     },
     'frontend.builder': {
         'screen_key': 'frontend.builder',
         'label': 'Constructor web',
         'levels': {
             'full_access': {
                 'label': 'Administrador',
                 'description': 'Gestiona páginas, versiones, publicaciones, marca y galería del constructor.',
             },
             'special_permissions': {
                 'label': 'Editor',
                 'description': 'Edita contenido y administra la publicación del frontend.',
             },
             'read_only': {
                 'label': 'Solo lectura',
                 'description': 'Consulta la configuración del constructor sin editarla.',
             },
         },
     },
 },
 'installable': True,
 'application': False,
 'auto_install': False}

__all__ = ["MANIFEST"]
