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
 'pwa': {'features': [{'key': 'sitio_publico',
                       'label': 'Sitio público',
                       'description': 'Entrada al frontend publicado desde la app instalada.',
                       'route': '/web/inicio',
                       'offline_capable': False}],
         'shortcuts': [{'name': 'Abrir sitio',
                        'short_name': 'Sitio',
                        'url': '/web/inicio'}],
         'precache_urls': ['/web/inicio']},
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
 'auto_install': False,

 # ── Arquitectura de datos (fuente única de verdad) ─────────────────────────────
 # Todas las entidades del módulo usan SQLAlchemy (MAIN) como fuente activa.
 # Los archivos JSON del directorio raíz son exclusivamente datos legacy:
 #   pages_store.json, versions_store.json, tasas_store.json
 # Se leen UNA SOLA VEZ durante _migrate_all_legacy_files() (DB vacía → import).
 # Después de esa migración los JSON no se modifican ni se consultan.
 # contact_store.json y brand_store.json NUNCA existieron como fuente activa;
 # esas entidades fueron DB desde el inicio.
 #
 # Entidad         Fuente activa   Archivo JSON legacy
 # ─────────────── ─────────────── ────────────────────────────
 # páginas         DB              pages_store.json
 # versiones       DB              versions_store.json
 # tasas           DB              tasas_store.json
 # brand           DB              (ninguno)
 # contactos       DB              (ninguno)
 'storage': 'database_primary',
}

__all__ = ["MANIFEST"]
