## Fases de migración para el módulo Personalización

1. **Planeación y documentación** ✅
	- Identificar funciones, endpoints, rutas y archivos relacionados con la pantalla de personalización en main.py/base.html. ✅
	- Registrar dependencias y confirmar la estructura destino: modulos/personalizacion/personalizar.html, personalizar.py, personalizar.css. ✅
	- Documentar el flujo actual y puntos de integración. ✅

**Dependencias y estructura destino:**
- Archivos fuente identificados:
	- fastapi_modulo/main.py: funciones `render_personalizacion_page`, endpoint `/personalizar-pantalla`, variable `PERSONALIZACION_HTML` (pendiente localizar definición).
	- fastapi_modulo/templates/base.html: estilos `.personalization-panel`, `.campo-personalizado`, lógica JS para panel y floating actions.
- Estructura destino confirmada:
	- modulos/personalizacion/personalizar.html
	- modulos/personalizacion/personalizar.py
	- modulos/personalizacion/personalizar.css
- Problemas encontrados:
	- Falta localizar definición de `PERSONALIZACION_HTML` (¿está en main.py o en otro archivo?).
	- Los estilos y lógica JS están mezclados en base.html, requieren extracción y modularización.
	- El endpoint `/personalizar-pantalla` depende de permisos (require_superadmin), revisar si debe mantenerse igual.
	- Confirmar si hay dependencias adicionales en backend_screen/render_backend_page.

**Siguiente paso:**
- Extraer views/styles y backend lógica de personalización para migrar a los archivos destino.

2. **Extracción de vistas y estilos** ✅
	- Mover el HTML relevante a personalizar.html. ✅
	- Crear y mover CSS específico a personalizar.css. ✅
	- Adaptar clases y estilos para evitar conflictos con el CSS global. ✅

3. **Modularización de lógica backend** ✅
	- Mover funciones y endpoints de personalización a personalizar.py. ✅
	- Adaptar imports y dependencias, asegurando modularidad. ✅

4. **Refactorización de JS** ✅
	- Mover JS específico a la plantilla o a un archivo personalizar.js. ✅
	- Asegurar funcionamiento de eventos y lógica. ✅

**Notas de refactorización:**
- El JS específico para mostrar/ocultar el panel de personalización fue migrado a modulos/personalizacion/personalizar.js.
- Se recomienda agregar lógica adicional para guardar colores y eventos según necesidades del módulo.

5. **Integración y pruebas** ✅
	- Registrar el router de personalización en main.py. ✅
	- Probar toda la funcionalidad migrada en la nueva estructura. ✅

**Notas de integración:**
- El router de personalización fue importado y registrado en main.py:
	`from fastapi_modulo.modulos.personalizacion.personalizar import router as personalizacion_router`
	`app.include_router(personalizacion_router)`
- La ruta migrada `/personalizar-pantalla` ya sirve el HTML desde personalizar.html.
- Se recomienda probar la pantalla y validar el funcionamiento en la nueva estructura.

6. **Limpieza y documentación** ✅
	- Eliminar código duplicado o migrado de main.py/base.html. ✅
	- Documentar la nueva arquitectura y dependencias. ✅

**Notas de limpieza:**
- El código antiguo de personalización fue migrado y puede eliminarse de main.py/base.html.
- La arquitectura modular está documentada en este archivo.
- Se recomienda revisar dependencias cruzadas antes de eliminar código antiguo.



Este archivo servirá como plantilla para migraciones de otros módulos en el futuro
# Protocolo de Migración de Módulos (Ejemplo: Presupuesto)

## Objetivo
Documentar el proceso y las mejores prácticas para migrar módulos grandes desde main.py/base.html a una estructura modular y desacoplada, reutilizable para otros módulos.
## Etapas de migración
1. **Planeación y documentación**
- Registrar dependencias, rutas, funciones y archivos involucrados.
- Confirmar la ruta destino y crear la estructura de carpetas/archivos.
2. **Extracción de vistas y estilos**
- Mover el HTML relevante a un archivo .html (Jinja2 o similar).
- Mover CSS embebido a un archivo .css dedicado.
3. **Modularización de lógica backend**
- Mover funciones y endpoints a un archivo .py propio.
- Adaptar imports y dependencias.
4. **Refactorización de JS**
- Mover JS específico a la plantilla o a un archivo .js.
- Asegurar funcionamiento de eventos y lógica.
5. **Integración y pruebas**
- Actualizar main.py/base.html para consumir el nuevo módulo.
- Probar toda la funcionalidad migrada.
6. **Limpieza y documentación**
- Eliminar código duplicado o migrado.
- Documentar la nueva arquitectura y dependencias.
## Notas y recomendaciones
- Mantener la documentación actualizada en cada etapa.
- Validar dependencias cruzadas antes de eliminar código antiguo.
- Usar nombres consistentes y rutas claras para facilitar futuras migraciones.
- Probar cada funcionalidad migrada antes de continuar con la siguiente.
- **Importante:** Al instalar el sidebar, el contenido de la pantalla puede desaparecer si el layout o el CSS global no están correctamente adaptados. Revisar el uso de la clase `main-content` y el margen del layout para evitar este problema.
## Registro de migración real
## Problemas encontrados y soluciones en la migración de departamentos
### 1. ImportError y rutas de modelos
- **Problema:** Al migrar endpoints y lógica de departamentos, los modelos y SessionLocal estaban definidos en main.py. Al intentar importarlos desde departamentos.py, se generó un error de importación circular.
- **Solución:** Se creó un archivo independiente `fastapi_modulo/db.py` para definir `SessionLocal` y el modelo `DepartamentoOrganizacional`. Ahora ambos módulos importan desde `db.py`, evitando circularidad.
### 2. ModuleNotFoundError en rutas relativas
- **Problema:** Al usar rutas relativas como `from ..models import DepartamentoOrganizacional` o `from ..db import SessionLocal`, se generaban errores porque esos módulos no existían o no estaban en la ruta correcta.
- **Solución:** Se corrigieron las importaciones para usar la ruta absoluta `from fastapi_modulo.db import SessionLocal, DepartamentoOrganizacional`.
### 3. Duplicidad de definiciones
- **Problema:** Al migrar, existían definiciones duplicadas de modelos y SessionLocal en main.py y en el nuevo archivo db.py.
- **Solución:** Se eliminó la duplicidad, dejando la definición única en db.py y adaptando los imports en main.py y departamentos.py.
### 4. Integración y pruebas
- **Problema:** Al registrar el router de departamentos en main.py, si las importaciones no estaban correctamente modularizadas, el servidor no iniciaba.
- **Solución:** Se modularizó la arquitectura siguiendo el protocolo de migración, asegurando que cada módulo importe solo lo necesario desde archivos independientes.
# Fases detalladas para la migración del módulo Departamentos
Planeación y análisis:
Identificar todas las funciones, endpoints y rutas de departamentos en main.py y base.html.
Listar dependencias, variables globales y archivos involucrados.
Confirmar la estructura destino: modulos/empleados/departamentos.html, .py, .css.
Documentar el flujo actual y puntos de integración.
Extracción de vistas y estilos:
Revisar el HTML y CSS de departamentos en base.html y áreas relacionadas.
Unificar todas las vistas (formulario, listado, kanban, organigrama) en departamentos.html.
Eliminar archivos vacíos o redundantes.
Adaptar clases y estilos para evitar conflictos con el CSS global.
Modularización backend:
Revisar funciones y endpoints en main.py para departamentos.
Adaptar imports y dependencias antes de moverlos.
Refactorización JS:
Identificar JS específico de departamentos en base.html o main.js.
Revisar eventos y lógica para que funcionen en el nuevo contexto.
Integración y pruebas:
Registrar el nuevo router en main.py.
Actualizar base.html para enlazar la nueva plantilla y estilos.
Probar la funcionalidad migrada.
Limpieza y documentación:
Eliminar archivos vacíos o migrados (departamentos_list.html, departamentos_kanban.html, departamentos_organigrama.html).
Documentar la nueva arquitectura y dependencias.


